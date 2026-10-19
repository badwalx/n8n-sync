# n8n-sync

[![PyPI version](https://img.shields.io/pypi/v/n8n-sync.svg)](https://pypi.org/project/n8n-sync/)
[![Python](https://img.shields.io/pypi/pyversions/n8n-sync.svg)](https://pypi.org/project/n8n-sync/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/badwalx/n8n-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/badwalx/n8n-sync/actions/workflows/ci.yml)

**Git-friendly version control for n8n Community Edition workflows.**

n8n Enterprise has Source Control at €667/mo. Community Edition has nothing.
**n8n-sync fills that gap** — a CLI that makes your n8n workflows first-class Git citizens.

## Quick start

```sh
pip install n8n-sync
n8n-sync init          # configure your n8n instance
n8n-sync pull          # export workflows to normalized files
git add workflows && git commit -m "snapshot"
n8n-sync diff --check  # CI-ready: exits 1 on drift, 0 if in-sync
n8n-sync push --dry-run  # preview changes before applying
n8n-sync push            # apply changes to remote
```

## Commands

| Command | Description |
|---------|-------------|
| `n8n-sync init` | Interactive setup — creates `.n8n-sync.yml` config |
| `n8n-sync pull` | Export all workflows to normalized JSON files |
| `n8n-sync push` | Create/update workflows on remote instance |
| `n8n-sync diff` | Show semantic differences between local and remote |
| `n8n-sync status` | List all workflows with drift detection |

### Key flags

- `--dry-run` — preview push without writing
- `--check` — exit 1 on drift (CI-friendly), 0 if in-sync, 2 on error
- `--instance <name>` — target a specific configured instance
- `--config <path>` — use a custom config file

## Why n8n-sync?

Without version control, self-hosted n8n workflows are a black box:

- ❌ No history of changes
- ❌ No way to review modifications before they go live
- ❌ No CI/CD integration
- ❌ Credentials break when copying between instances
- ❌ Cannot rollback a broken workflow

n8n-sync fixes all of this:

- ✅ **Readable Git diffs** — YAML frontmatter + sorted JSON
- ✅ **Credential mapping** — staging → production without manual fixes
- ✅ **CI integration** — `diff --check` exits 1 on drift
- ✅ **Drift detection** — know instantly if someone changed a workflow in the UI
- ✅ **Dry-run push** — preview before applying
- ✅ **No Enterprise required** — works with any Community Edition instance

## Configuration

Create `.n8n-sync.yml` in your project root:

```yaml
instances:
  staging:
    url: https://n8n-staging.example.com
    api_key: ${N8N_STAGING_KEY}
  production:
    url: https://n8n.example.com
    api_key: ${N8N_PRODUCTION_KEY}
    credentials:
      "Staging DB": "Production DB"
      "Staging API": "Production API"

workflows_dir: workflows
```

API keys use `${ENV_VAR}` placeholders — never commit literal keys. Set environment variables:

```sh
export N8N_STAGING_KEY='your-staging-api-key'
export N8N_PRODUCTION_KEY='your-production-api-key'
```

## CI/CD integration

Use `diff --check` in your pipeline to catch drift:

```yaml
# .github/workflows/n8n-drift.yml
name: n8n workflow drift check
on: [push, pull_request]
jobs:
  drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install n8n-sync
      - run: n8n-sync diff --instance production --check
        env:
          N8N_PRODUCTION_KEY: ${{ secrets.N8N_PRODUCTION_KEY }}
```

## Workflow file format

Files use YAML frontmatter + normalized JSON for readable diffs:

```yaml
---
name: Send Daily Report
active: true
tags: [reporting, daily]
lastModified: "2024-10-18T12:00:00.000Z"
---
{
  "nodes": [...],
  "connections": {...},
  "settings": {}
}
```

Node IDs, workflow IDs, and credential IDs are stripped. Credential names are preserved for mapping. JSON keys and nodes are sorted for stable diffs.

## Requirements

- Python 3.10+
- n8n Community Edition with API enabled
- n8n API key with workflow read/write permissions

## Install

```sh
pip install n8n-sync
```

For development:

```sh
git clone https://github.com/badwalx/n8n-sync.git
cd n8n-sync
pip install -e '.[dev]'
pytest
```

## License

MIT — see [LICENSE](LICENSE).
