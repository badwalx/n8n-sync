"""Typer command entry points with rich, script-friendly exit codes."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from . import __version__
from .client import N8nClient
from .config import load_config
from .errors import SyncError
from .normalize import read_directory
from .sync import detect_drift, index_workflows, write_pull
from .sync import push as push_workflows

app = typer.Typer(no_args_is_help=True, help="Version and synchronize n8n workflows.")
console = Console()
errors = Console(stderr=True)
ConfigOption = Annotated[Path, typer.Option("--config", "-c", help="YAML configuration path")]
InstanceOption = Annotated[str | None, typer.Option("--instance", "-i", help="Instance name")]


def version_callback(value: bool):
    if value:
        console.print(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool, typer.Option("--version", callback=version_callback, is_eager=True)
    ] = False,
):
    pass


async def execute(
    command: str, path: Path, instance: str | None, dry_run: bool = False, check: bool = False
):
    config = load_config(path)
    name, target = config.instance(instance)
    async with N8nClient(target.url, target.api_key.get_secret_value(), config.timeout) as client:
        if command == "push":
            messages = await push_workflows(client, config, name, dry_run)
            for message in messages:
                console.print(message, markup=False)
            console.print(f"{len(messages)} workflow(s) {'planned' if dry_run else 'pushed'}.")
            return
        remote = index_workflows(await client.workflows())
        if command == "pull":
            count = write_pull(config.workflow_dir, remote)
            console.print(f"Pulled {count} workflow(s) into {config.workflow_dir}", markup=False)
            return
        local = read_directory(config.workflow_dir) if config.workflow_dir.is_dir() else {}
        drift = detect_drift(local, remote, config.credentials_map.get(name, {}))
        table = Table(title=f"{name}: workflow {command}")
        for heading in ("Workflow", "Active", "Last edited", "Drift"):
            table.add_column(heading)
        for item in drift:
            workflow = remote.get(item.name, local.get(item.name, {}))
            table.add_row(
                item.name,
                "yes" if workflow.get("active") else "no",
                str(workflow.get("updatedAt", workflow.get("lastModified")) or "—"),
                item.state,
            )
        console.print(table)
        if command == "diff":
            for item in drift:
                if item.patch:
                    console.print(Syntax(item.patch, "diff", word_wrap=True))
        if check and any(item.state != "in-sync" for item in drift):
            raise typer.Exit(1)


def run(*args, **kwargs):
    try:
        asyncio.run(execute(*args, **kwargs))
    except (SyncError, OSError, UnicodeError) as exc:
        errors.print(f"Error: {exc}", style="red", markup=False)
        raise typer.Exit(2) from exc
    except KeyboardInterrupt:
        errors.print("Interrupted; run diff to check for partially completed changes.")
        raise typer.Exit(130)


@app.command()
def pull(config: ConfigOption = Path(".n8n-sync.yml"), instance: InstanceOption = None):
    """Export workflows to portable files, preserving local-only files."""
    run("pull", config, instance)


@app.command()
def push(
    config: ConfigOption = Path(".n8n-sync.yml"),
    instance: InstanceOption = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Validate without writing")] = False,
):
    """Create or update workflows by exact name and synchronize activation and tags."""
    run("push", config, instance, dry_run=dry_run)


@app.command()
def diff(
    config: ConfigOption = Path(".n8n-sync.yml"),
    instance: InstanceOption = None,
    check: Annotated[bool, typer.Option("--check", help="Exit 1 if drift exists")] = False,
):
    """Show semantic local-versus-remote differences."""
    run("diff", config, instance, check=check)


@app.command()
def init(
    config: ConfigOption = Path(".n8n-sync.yml"),
):
    """Interactively create a .n8n-sync.yml configuration file."""
    if config.exists():
        overwrite = typer.confirm(f"{config} already exists. Overwrite?", default=False)
        if not overwrite:
            raise typer.Exit(0)

    console.print("[bold]n8n-sync setup[/bold]\n")

    instances = {}
    while True:
        name = typer.prompt("Instance name", default="production" if not instances else "")
        if not name:
            break
        url = typer.prompt("  n8n URL (e.g. https://n8n.example.com)")
        env_var = typer.prompt("  API key env var name", default=f"N8N_{name.upper()}_KEY")
        instances[name] = {"url": url.rstrip("/"), "api_key": f"${{{env_var}}}"}

        if not typer.confirm("Add another instance?", default=False):
            break

    if not instances:
        errors.print("No instances configured.", style="red")
        raise typer.Exit(2)

    config_data = {"instances": instances, "workflows_dir": "workflows"}

    # Add credential mapping if multiple instances
    names = list(instances.keys())
    if len(names) >= 2:
        console.print(f"\nCredential mapping: {names[0]} → {names[1]}")
        cred_map = {}
        while True:
            source = typer.prompt("  Source credential name (empty to skip)", default="")
            if not source:
                break
            target = typer.prompt("  Target credential name", default=source)
            cred_map[source] = target
        if cred_map:
            config_data["credentials_map"] = {names[1]: cred_map}

    import yaml
    config.write_text(yaml.safe_dump(config_data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    console.print(f"\n✓ Config written to {config}")
    console.print("Next steps:")
    console.print(f"  1. Set your API key: export {list(instances.values())[0]['api_key'].strip('${}')}='your-key'")
    console.print(f"  2. Pull workflows:    n8n-sync pull")
    console.print(f"  3. Commit to git:     git add workflows && git commit -m 'initial'")


@app.command(name="list")
def list_workflows(
    config: ConfigOption = Path(".n8n-sync.yml"),
    instance: InstanceOption = None,
):
    """List remote workflow names and IDs."""
    config_obj = load_config(config)
    name, target = config_obj.instance(instance)

    async def _list():
        async with N8nClient(target.url, target.api_key.get_secret_value(), config_obj.timeout) as client:
            workflows = await client.workflows()
            if not workflows:
                console.print("No workflows found.")
                return
            table = Table(title=f"{name}: remote workflows")
            table.add_column("ID")
            table.add_column("Name")
            table.add_column("Active")
            table.add_column("Tags")
            for wf in workflows:
                tags = ", ".join(sorted(t.get("name", "") for t in wf.get("tags", [])))
                table.add_row(str(wf.get("id", "")), wf.get("name", ""), "✓" if wf.get("active") else "✗", tags)
            console.print(table)

    try:
        asyncio.run(_list())
    except (SyncError, OSError) as exc:
        errors.print(f"Error: {exc}", style="red", markup=False)
        raise typer.Exit(2) from exc


@app.command()
def status(
    config: ConfigOption = Path(".n8n-sync.yml"),
    instance: InstanceOption = None,
    check: Annotated[bool, typer.Option("--check", help="Exit 1 if drift exists")] = False,
):
    """List activation, modification time, and drift for every workflow."""
    run("status", config, instance, check=check)
