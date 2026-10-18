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
def status(
    config: ConfigOption = Path(".n8n-sync.yml"),
    instance: InstanceOption = None,
    check: Annotated[bool, typer.Option("--check", help="Exit 1 if drift exists")] = False,
):
    """List activation, modification time, and drift for every workflow."""
    run("status", config, instance, check=check)
