import copy
import json

import httpx
import pytest
from typer.testing import CliRunner

from n8n_sync.cli import app
from n8n_sync.client import N8nClient
from n8n_sync.config import Config, load_config
from n8n_sync.errors import SyncError
from n8n_sync.normalize import dumps, loads, read_directory
from n8n_sync.sync import detect_drift, index_workflows, push, write_pull


def workflow(name="Daily Email", credential=True):
    return {
        "id": "source-id",
        "name": name,
        "active": True,
        "updatedAt": "2026-01-01",
        "tags": [{"id": "tag-source", "name": "daily"}],
        "nodes": [
            {
                "id": "node-source",
                "name": "Z",
                "type": "test",
                "parameters": {"id": "keep", "workflowId": "keep-too"},
                "credentials": {"postgres": {"id": "cred-source", "name": "Source"}}
                if credential
                else {},
            },
            {"id": "other", "name": "A", "type": "test"},
        ],
        "connections": {"Z": {"main": [[{"node": "A", "index": 1}, {"node": "Z", "index": 0}]]}},
        "settings": {},
    }


def test_normalization_and_roundtrip():
    original = workflow()
    before = copy.deepcopy(original)
    doc = loads(dumps(original))
    assert original == before
    assert [n["name"] for n in doc["nodes"]] == ["A", "Z"]
    assert "id" not in doc["nodes"][1]
    assert doc["nodes"][1]["credentials"] == {"postgres": {"name": "Source"}}
    assert doc["nodes"][1]["parameters"]["workflowId"] == "keep-too"
    assert doc["connections"] == original["connections"]
    assert dumps(doc) == dumps(original)
    assert loads(json.dumps(original)) == doc


def test_drift_metadata_mapping_and_arrays():
    local = workflow()
    remote = workflow()
    remote["updatedAt"] = "new"
    remote["nodes"].reverse()
    remote["nodes"][1]["credentials"]["postgres"]["name"] = "Target"
    assert (
        detect_drift({local["name"]: local}, {remote["name"]: remote}, {"Source": "Target"})[
            0
        ].state
        == "in-sync"
    )
    remote["connections"]["Z"]["main"][0].reverse()
    assert detect_drift({local["name"]: local}, {remote["name"]: remote})[0].patch
    assert detect_drift({"x": local}, {})[0].state == "local-only"
    assert detect_drift({}, {"x": remote})[0].state == "remote-only"


def test_config_env_and_relative_paths(tmp_path, monkeypatch):
    path = tmp_path / ".n8n-sync.yml"
    path.write_text("instances:\n  stage:\n    url: https://test\n    api_key: ${TEST_KEY}\n")
    monkeypatch.delenv("TEST_KEY", raising=False)
    with pytest.raises(SyncError, match="missing"):
        load_config(path)
    monkeypatch.setenv("TEST_KEY", "secret")
    config = load_config(path)
    assert config.workflow_dir == tmp_path / "workflows"
    assert config.instance(None)[0] == "stage"
    assert "secret" not in repr(config)
    path.write_text("instances:\n  stage:\n    url: https://test\n    api_key: literal-secret\n")
    with pytest.raises(SyncError, match="ENV_VAR"):
        load_config(path)


def test_pull_collision_preservation_and_reuse(tmp_path):
    remote = index_workflows([workflow("A B"), workflow("A-B"), workflow("../../")])
    assert write_pull(tmp_path, remote) == 3
    paths = sorted(tmp_path.glob("*.json"))
    assert len(paths) == 3
    assert all(p.parent == tmp_path for p in paths)
    assert write_pull(tmp_path, remote) == 3
    assert sorted(tmp_path.glob("*.json")) == paths
    write_pull(tmp_path, index_workflows([workflow("A B")]))
    assert len(read_directory(tmp_path)) == 3


def test_duplicates_and_malformed_documents(tmp_path):
    with pytest.raises(SyncError, match="Ambiguous"):
        index_workflows([workflow(), workflow()])
    with pytest.raises(SyncError):
        loads("---\nname: A\n---\n[]")
    with pytest.raises(SyncError):
        loads("[]")
    with pytest.raises(SyncError):
        loads('{"name":"A","active":"false"}')
    (tmp_path / "one.json").write_text(dumps(workflow()))
    (tmp_path / "two.json").write_text(dumps(workflow()))
    with pytest.raises(SyncError, match="Duplicate"):
        read_directory(tmp_path)


async def test_api_pagination_and_error_redaction():
    requests = []

    def handler(request):
        requests.append(request)
        assert request.headers["X-N8N-API-KEY"] == "secret"
        if request.url.params.get("cursor"):
            return httpx.Response(200, json={"data": [{"id": "2"}]})
        return httpx.Response(200, json={"data": [{"id": "1"}], "nextCursor": "next"})

    async with N8nClient(
        "https://test/subpath", "secret", transport=httpx.MockTransport(handler)
    ) as c:
        assert len(await c.workflows()) == 2
    assert requests[0].url.path == "/subpath/api/v1/workflows"
    async with N8nClient(
        "https://test",
        "secret",
        transport=httpx.MockTransport(lambda r: httpx.Response(401, text="secret")),
    ) as c:
        with pytest.raises(SyncError) as error:
            await c.workflows()
        assert "secret" not in str(error.value)
        assert "401" in str(error.value)


async def test_repeated_cursor_and_invalid_json():
    async with N8nClient(
        "https://test/api/v1",
        "key",
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"data": [], "nextCursor": "same"})
        ),
    ) as c:
        with pytest.raises(SyncError, match="cursor"):
            await c.workflows()
    async with N8nClient(
        "https://test",
        "key",
        transport=httpx.MockTransport(lambda r: httpx.Response(200, text="<html>")),
    ) as c:
        with pytest.raises(SyncError, match="JSON"):
            await c.workflows()


def config_for(tmp_path):
    return Config(
        instances={"prod": {"url": "https://test", "api_key": "secret"}},
        workflow_dir=tmp_path,
        credentials_map={"prod": {"Source": "Target"}},
        credential_ids={"prod": {"postgres": {"Target": "target-cred"}}},
    )


async def test_push_create_tags_activation_and_idempotence(tmp_path):
    local = workflow()
    write_pull(tmp_path, index_workflows([local]))
    config = config_for(tmp_path)
    remote = []
    writes = []

    def handler(request):
        path = request.url.path
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "data": remote
                    if path.endswith("workflows")
                    else [{"id": "target-tag", "name": "daily"}]
                },
            )
        writes.append(
            (request.method, path, json.loads(request.content) if request.content else None)
        )
        if path.endswith("/workflows"):
            body = json.loads(request.content)
            assert body["nodes"][1]["credentials"]["postgres"] == {
                "id": "target-cred",
                "name": "Target",
            }
            assert set(body) == {"name", "nodes", "connections", "settings"}
            remote.append({**body, "id": "target-workflow", "active": False, "tags": []})
            return httpx.Response(200, json=remote[0])
        if path.endswith("/tags"):
            remote[0]["tags"] = [{"id": "target-tag", "name": "daily"}]
            return httpx.Response(200, json=remote[0]["tags"])
        if path.endswith("/activate"):
            remote[0]["active"] = True
            return httpx.Response(200, json=remote[0])
        raise AssertionError(path)

    async with N8nClient("https://test", "secret", transport=httpx.MockTransport(handler)) as c:
        assert len(await push(c, config, "prod", dry_run=True)) == 1
        assert not writes
        assert len(await push(c, config, "prod")) == 1
        assert len(writes) == 3
        assert await push(c, config, "prod") == []
        assert len(writes) == 3


async def test_preflight_prevents_partial_push(tmp_path):
    first, second = workflow("A", False), workflow("Z")
    first["tags"] = []
    write_pull(tmp_path, index_workflows([first, second]))
    config = config_for(tmp_path)
    config.credential_ids = {}
    requests = []

    def handler(request):
        requests.append(request.method)
        return httpx.Response(200, json={"data": []})

    async with N8nClient("https://test", "secret", transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(SyncError, match="resolve credential"):
            await push(c, config, "prod")
    assert requests == ["GET"]


async def test_update_deactivate_remove_tags_and_inferred_credentials(tmp_path):
    local = workflow()
    local["active"], local["tags"] = False, []
    remote = workflow()
    remote["nodes"][0]["credentials"]["postgres"] = {"name": "Target", "id": "target-cred"}
    write_pull(tmp_path, index_workflows([local]))
    config = config_for(tmp_path)
    config.credential_ids = {}
    writes = []

    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, json={"data": [remote]})
        writes.append((request.method, request.url.path))
        return httpx.Response(200, json=remote)

    async with N8nClient("https://test", "secret", transport=httpx.MockTransport(handler)) as c:
        await push(c, config, "prod")
    assert writes == [
        ("PUT", "/api/v1/workflows/source-id"),
        ("PUT", "/api/v1/workflows/source-id/tags"),
        ("POST", "/api/v1/workflows/source-id/deactivate"),
    ]


def test_cli_help_version_errors_and_ci_exit(tmp_path, monkeypatch):
    runner = CliRunner()
    for command in [
        [],
        ["--help"],
        ["pull", "--help"],
        ["push", "--help"],
        ["diff", "--help"],
        ["status", "--help"],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code in (0, 2)
        assert "Usage" in result.output
    assert runner.invoke(app, ["--version"]).exit_code == 0
    result = runner.invoke(app, ["pull", "-c", str(tmp_path / "missing")])
    assert result.exit_code == 2
    assert "Error:" in result.output
    config = tmp_path / "config.yml"
    config.write_text("instances:\n  prod:\n    url: https://test\n    api_key: ${TEST_KEY}\n")
    monkeypatch.setenv("TEST_KEY", "secret")

    async def workflows(self):
        return [workflow()]

    monkeypatch.setattr(N8nClient, "workflows", workflows)
    result = runner.invoke(app, ["status", "-c", str(config), "--check"])
    assert result.exit_code == 1, result.output
    assert "remote-only" in result.output
    assert runner.invoke(app, ["pull", "-c", str(config)]).exit_code == 0
    assert runner.invoke(app, ["diff", "-c", str(config), "--check"]).exit_code == 0


async def test_missing_tags_and_timeout_are_actionable(tmp_path):
    write_pull(tmp_path, index_workflows([workflow(credential=False)]))
    calls = []

    def handler(request):
        calls.append(request.method)
        return httpx.Response(200, json={"data": []})

    async with N8nClient("https://test", "secret", transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(SyncError, match="Create these tags"):
            await push(c, config_for(tmp_path), "prod")
    assert calls == ["GET", "GET"]

    def timeout(request):
        raise httpx.ReadTimeout("secret", request=request)

    async with N8nClient("https://test", "secret", transport=httpx.MockTransport(timeout)) as c:
        with pytest.raises(SyncError, match="ReadTimeout") as error:
            await c.workflows()
        assert "secret" not in str(error.value)


def test_invalid_config_and_nonfinite_json(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_KEY", "super-secret")
    path = tmp_path / "config.yml"
    path.write_text("instances:\n  test:\n    url: invalid\n    api_key: ${TEST_KEY}\n")
    with pytest.raises(SyncError) as error:
        load_config(path)
    assert "super-secret" not in str(error.value)
    path.write_text("instances: {}")
    with pytest.raises(SyncError):
        load_config(path)
    with pytest.raises(SyncError, match="valid JSON"):
        loads('{"name":"bad", "settings":{"x":NaN}}')
