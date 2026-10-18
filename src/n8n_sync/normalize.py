"""Deterministic portable documents; preserve semantic array ordering."""

import copy
import json
import re
from pathlib import Path

import yaml

from .errors import SyncError


def normalize(workflow: dict) -> dict:
    if not isinstance(workflow, dict):
        raise SyncError("Workflow must be an object")
    name = workflow.get("name")
    if not isinstance(name, str) or not name.strip():
        raise SyncError("Workflow requires a non-empty name")
    nodes = copy.deepcopy(workflow.get("nodes", []))
    connections = copy.deepcopy(workflow.get("connections", {}))
    if not isinstance(nodes, list) or not isinstance(connections, dict):
        raise SyncError(f"{name}: nodes must be a list and connections an object")
    names = set()
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("name"), str):
            raise SyncError(f"{name}: each node requires a name")
        if node["name"] in names:
            raise SyncError(f"{name}: duplicate node name {node['name']}")
        names.add(node["name"])
        for key in ("id", "nodeId", "workflowId"):
            node.pop(key, None)
        credentials = node.get("credentials", {})
        if not isinstance(credentials, dict):
            raise SyncError(f"{name}: invalid node credentials")
        for kind, ref in credentials.items():
            if not isinstance(ref, dict) or not isinstance(ref.get("name"), str):
                raise SyncError(f"{name}: credential {kind} requires a name")
            credentials[kind] = {"name": ref["name"]}
    tags = workflow.get("tags", [])
    if not isinstance(tags, list):
        raise SyncError(f"{name}: tags must be a list")
    tag_names = [tag.get("name") if isinstance(tag, dict) else tag for tag in tags]
    if any(not isinstance(tag, str) or not tag for tag in tag_names):
        raise SyncError(f"{name}: tags require names")
    settings = copy.deepcopy(workflow.get("settings", {}))
    if not isinstance(settings, dict):
        raise SyncError(f"{name}: settings must be an object")
    active = workflow.get("active", False)
    if not isinstance(active, bool):
        raise SyncError(f"{name}: active must be boolean")
    try:
        json.dumps(
            {"nodes": nodes, "connections": connections, "settings": settings}, allow_nan=False
        )
    except (ValueError, TypeError) as exc:
        raise SyncError(f"{name}: workflow contains values that are not valid JSON") from exc
    return {
        "name": name,
        "active": active,
        "tags": sorted(set(tag_names)),
        "lastModified": workflow.get("updatedAt", workflow.get("lastModified")),
        "nodes": sorted(nodes, key=lambda n: n["name"]),
        "connections": connections,
        "settings": settings,
    }


def comparable(workflow: dict) -> dict:
    result = normalize(workflow)
    result.pop("lastModified", None)
    return result


def dumps(workflow: dict) -> str:
    doc = normalize(workflow)
    metadata = {key: doc.pop(key) for key in ("name", "active", "tags", "lastModified")}
    return (
        "---\n"
        + yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
        + "---\n"
        + json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    )


def loads(text: str) -> dict:
    try:
        if text.startswith("---\n"):
            parts = text.split("\n---\n", 1)
            if len(parts) != 2:
                raise SyncError("Unterminated YAML frontmatter")
            metadata = yaml.safe_load(parts[0][4:])
            body = json.loads(parts[1])
            if not isinstance(metadata, dict) or not isinstance(body, dict):
                raise SyncError("Frontmatter and workflow must be objects")
            body.update(metadata)
        else:
            body = json.loads(text)
        return normalize(body)
    except (ValueError, yaml.YAMLError) as exc:
        raise SyncError(f"Invalid workflow document ({type(exc).__name__})") from exc


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:120] or "workflow"


def read_directory(directory: Path) -> dict[str, dict]:
    if not directory.is_dir():
        raise SyncError(f"Workflow directory does not exist: {directory}; run pull first")
    result = {}
    for path in sorted(directory.glob("*.json")):
        try:
            workflow = loads(path.read_text(encoding="utf-8"))
        except (SyncError, OSError, UnicodeError) as exc:
            raise SyncError(f"{path}: {exc}") from exc
        if workflow["name"] in result:
            raise SyncError(f"Duplicate workflow name: {workflow['name']}")
        result[workflow["name"]] = workflow
    return result
