"""Sync planning and drift detection without implicit deletions."""

import copy
import difflib
import json
import os
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from .client import N8nClient
from .config import Config
from .errors import SyncError
from .normalize import comparable, dumps, normalize, read_directory, slug


def index_workflows(workflows: list[dict]) -> dict[str, dict]:
    result = {}
    for workflow in workflows:
        name = normalize(workflow)["name"]
        if name in result:
            raise SyncError(f"Ambiguous remote workflow name: {name}")
        result[name] = workflow
    return result


def mapped(workflow: dict, mapping: dict[str, str]) -> dict:
    result = copy.deepcopy(workflow)
    for node in result.get("nodes", []):
        for ref in node.get("credentials", {}).values():
            ref["name"] = mapping.get(ref["name"], ref["name"])
    return result


@dataclass
class Drift:
    name: str
    state: str
    patch: str = ""


def detect_drift(
    local: dict[str, dict], remote: dict[str, dict], mapping: dict[str, str] | None = None
) -> list[Drift]:
    result = []
    for name in sorted(local.keys() | remote.keys()):
        if name not in remote:
            result.append(Drift(name, "local-only"))
        elif name not in local:
            result.append(Drift(name, "remote-only"))
        else:
            left = comparable(mapped(local[name], mapping or {}))
            right = comparable(remote[name])
            patch = "".join(
                difflib.unified_diff(
                    (json.dumps(left, indent=2, sort_keys=True) + "\n").splitlines(True),
                    (json.dumps(right, indent=2, sort_keys=True) + "\n").splitlines(True),
                    fromfile=f"local/{name}",
                    tofile=f"remote/{name}",
                )
            )
            result.append(Drift(name, "changed" if patch else "in-sync", patch))
    return result


def write_pull(directory: Path, remote: dict[str, dict]) -> int:
    directory.mkdir(parents=True, exist_ok=True)
    existing = {}
    for path in directory.glob("*.json"):
        from .normalize import loads

        name = loads(path.read_text(encoding="utf-8"))["name"]
        if name in existing:
            raise SyncError(f"Duplicate local workflow name: {name}")
        existing[name] = path
    planned, used = [], set(existing.values())
    for name, workflow in sorted(remote.items()):
        target = existing.get(name, directory / (slug(name) + ".json"))
        if name not in existing and target in used:
            suffix = uuid.uuid5(uuid.NAMESPACE_URL, name).hex[:12]
            target = directory / f"{slug(name)}-{suffix}.json"
        if name not in existing and (target in used or target.exists()):
            raise SyncError(f"Filename collision: {target}")
        used.add(target)
        planned.append((target, dumps(workflow)))
    for target, content in planned:
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=directory, delete=False
            ) as handle:
                temporary = Path(handle.name)
                handle.write(content)
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return len(planned)


def credential_registry(remote: dict[str, dict], explicit: dict) -> dict:
    registry = {}
    for workflow in remote.values():
        for node in workflow.get("nodes", []):
            for kind, ref in node.get("credentials", {}).items():
                if ref.get("name") and ref.get("id"):
                    key = (kind, ref["name"])
                    registry.setdefault(key, set()).add(str(ref["id"]))
    for kind, names in explicit.items():
        for name, credential_id in names.items():
            registry[(kind, name)] = {credential_id}
    return registry


async def push(
    client: N8nClient, config: Config, instance: str, dry_run: bool = False, filter_pattern: str | None = None
) -> list[str]:
    local = read_directory(config.workflow_dir)
    if filter_pattern:
        import fnmatch
        local = {k: v for k, v in local.items() if fnmatch.fnmatch(k, filter_pattern)}
    remote = index_workflows(await client.workflows())
    registry = credential_registry(remote, config.credential_ids.get(instance, {}))
    mapping = config.credentials_map.get(instance, {})
    drift = {item.name: item.state for item in detect_drift(local, remote, mapping)}
    plans = []
    for name, source in sorted(local.items()):
        if drift[name] == "in-sync":
            continue
        workflow = normalize(mapped(source, mapping))
        payload = {
            key: copy.deepcopy(workflow[key])
            for key in ("name", "nodes", "connections", "settings")
        }
        for node in payload["nodes"]:
            node["id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, name + "/" + node["name"]))
            for kind, ref in node.get("credentials", {}).items():
                ids = registry.get((kind, ref["name"]), set())
                if len(ids) != 1:
                    raise SyncError(
                        f"{name}: cannot uniquely resolve credential {kind}/{ref['name']}; "
                        f"set credential_ids.{instance}.{kind} in config"
                    )
                ref["id"] = next(iter(ids))
        target = remote.get(name)
        if target and not target.get("id"):
            raise SyncError(f"{name}: target workflow is missing its ID")
        plans.append((workflow, payload, target))
    # Resolve all tags before the first write as well.
    tag_ids = {}
    if any(workflow["tags"] for workflow, _, _ in plans):
        for tag in await client.list_all("tags"):
            if tag.get("name") in tag_ids:
                raise SyncError(f"Ambiguous target tag: {tag['name']}")
            tag_ids[tag.get("name")] = tag.get("id")
        missing = {
            tag for workflow, _, _ in plans for tag in workflow["tags"] if not tag_ids.get(tag)
        }
        if missing:
            raise SyncError(
                "Create these tags on the target before pushing: " + ", ".join(sorted(missing))
            )
    messages = []
    for workflow, payload, target in plans:
        action = "update" if target else "create"
        if not dry_run:
            try:
                saved = await client.save(payload, target["id"] if target else None)
                if workflow["tags"] or (target and target.get("tags")):
                    await client.set_tags(
                        saved["id"], [{"id": tag_ids[t]} for t in workflow["tags"]]
                    )
                if workflow["active"] != saved.get("active", False):
                    await client.set_active(saved["id"], workflow["active"])
            except SyncError as exc:
                raise SyncError(
                    f"Push stopped at {workflow['name']}: {exc}. "
                    "Earlier operations may have completed; run diff before retrying."
                ) from exc
        messages.append(f"{'Would ' if dry_run else ''}{action}: {workflow['name']}")
    return messages
