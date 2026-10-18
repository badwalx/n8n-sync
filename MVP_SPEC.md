# n8n-sync — Workflow CI/CD for n8n Community Edition

## Problem
n8n Enterprise Source Control costs €667/mo. Community Edition has zero version control.
Users manually export JSON, email it, import on other instances, fix credentials by hand.

## Solution
CLI tool that:
1. Pulls workflows from any n8n instance (via REST API)
2. Stores them in Git with normalized JSON (readable diffs)
3. Pushes workflows to any n8n instance (with credential mapping)
4. Detects drift between instances
5. Works as GitHub Action for CI/CD

## MVP Scope (Phase 1 — 2 weeks)

### Core Commands
```
n8n-sync pull    # Export all workflows from instance → local JSON files
n8n-sync push    # Import local JSON files → instance (with credential mapping)
n8n-sync diff    # Compare local files vs instance (drift detection)
n8n-sync status  # Which workflows are active, last edited, drift status
```

### Config File (.n8n-sync.yml)
```yaml
instances:
  staging:
    url: https://n8n-staging.b7co.cloud
    api_key: ${N8N_STAGING_KEY}
  production:
    url: https://n8n.b7co.cloud
    api_key: ${N8N_PRODUCTION_KEY}

credentials_map:
  # Map credential names between instances
  staging:
    "Postgres - Staging": "Postgres - Production"
  production:
    "Postgres - Production": "Postgres - Staging"

workflow_dir: ./workflows  # Where JSON files are stored
```

### Workflow JSON Normalization
- Strip instance-specific IDs (workflowId, nodeId)
- Strip credential IDs (keep names only — IDs are instance-specific)
- Sort nodes, connections alphabetically for consistent diffs
- Add YAML frontmatter with metadata (name, active, tags, lastModified)

### Output Structure
```
workflows/
  daily-email-summary.json
  slack-notifications.json
  webhook-handler.json
.n8n-sync.yml
```

## Phase 2 (weeks 3-4) — Paid Features
- Multi-instance promotion (staging → production with one command)
- Credential mapping UI (web dashboard)
- Git-based change log (who changed what, when)
- Team collaboration (shared credential maps)
- Scheduled sync (auto-pull on cron)

## Phase 3 (weeks 5-8) — Growth
- GitHub Action for CI/CD pipeline
- Web dashboard for multi-instance management
- Slack/Discord notifications on drift
- Workflow testing framework (run workflows in dry-run mode)
- n8n community template publishing

## Tech Stack
- CLI: Python (click/typer) — user already has Python
- API client: httpx (async)
- JSON normalization: custom logic
- Config: pydantic-settings + YAML
- Git integration: subprocess git calls
- Package: pip-installable, also Docker image

## Pricing
- Phase 1 CLI: FREE + open-source (builds trust, dogfooding, community)
- Phase 2 SaaS: $15/mo individual, $30/mo team (credential mapping UI, multi-instance)
- Phase 3: $30/mo professional (GitHub Action, dashboard, testing)

## Distribution
- GitHub repo with good README
- n8n community forum post
- Reddit r/n8n
- n8n Discord
- Product Hunt launch
- Blog posts: "n8n CI/CD without Enterprise"

## Revenue Projections
- Conservative: 100 paid users × $20 avg = $2K MRR (Year 1)
- Moderate: 300 paid users × $20 avg = $6K MRR (Year 1)
- Optimistic: 500 paid users × $25 avg = $12.5K MRR (Year 1)

## Risks
1. n8n GmbH open-sources Source Control → unlikely (Enterprise cash cow, 2+ years unchanged)
2. Market too small → mitigated by free tier (any n8n user can try it)
3. n8n API changes → pin to API v1, add version detection
4. Credential handling security → never store API keys in Git, use env vars only
