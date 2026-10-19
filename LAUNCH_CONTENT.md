# n8n-sync Launch Content

## Reddit r/n8n Post

**Title:** I built a free CLI to put n8n workflows under Git version control

**Body:**
Hey r/n8n,

I kept losing track of workflow changes — someone edits in the UI, breaks something, and there's no history to roll back to. Enterprise has versioning, but Community Edition doesn't.

So I built n8n-sync: a CLI that backs up your n8n workflows to Git.

```
pip install n8n-sync
n8n-sync init   # point it at your instance
n8n-sync pull   # exports all workflows as readable JSON
git commit      # now you have history, diffs, rollback
```

What it does:
- **pull**: Export workflows to normalized JSON (YAML frontmatter + sorted JSON = meaningful git diffs)
- **push**: Create/update workflows on remote (with dry-run)
- **diff**: Semantic comparison between local and remote
- **status**: Drift detection — know if someone changed a workflow in the UI
- **list**: Show remote workflows with IDs, tags, active state
- **--filter**: Select workflows by glob pattern (e.g., `--filter "prod-*"`)

Use cases I've found:
1. **Backup**: `n8n-sync pull && git commit` gives you audit trail
2. **CI/CD**: `n8n-sync diff --check` exits 1 on drift — run it in GitHub Actions
3. **Staging→Prod**: Push with automatic credential mapping
4. **Multi-instance**: Manage multiple n8n instances from one repo

Free, open source (MIT), works with any n8n Community Edition instance.

GitHub: https://github.com/badwalx/n8n-sync
PyPI: https://pypi.org/project/n8n-sync/
Docs: https://n8n-sync.b7co.cloud/

Would love feedback — what features would make this useful for your setup?

---

## Hacker News Show HN

**Title:** Show HN: n8n-sync – Free CLI for Git version control of n8n workflows

**Body:**
I built n8n-sync because n8n Community Edition has no built-in version control for workflows. Enterprise gets it, but if you're self-hosting CE, you're out of luck.

The CLI exports workflows to normalized JSON files (YAML frontmatter + sorted JSON) so `git diff` actually shows meaningful changes instead of random key reordering.

Key features:
- Pull/push workflows with dry-run
- Semantic diff between local and remote
- Drift detection (someone edited in the UI?)
- Credential mapping for staging→prod
- CI-ready: `diff --check` exits 1 on drift
- Filter by glob pattern for multi-instance setups

Install: `pip install n8n-sync`

https://github.com/badwalx/n8n-sync

---

## Product Hunt Draft

**Tagline:** Git version control for n8n workflows — free and open source

**Description:**
n8n-sync is a CLI tool that brings Git version control to n8n Community Edition workflows. Backup, diff, sync, and detect drift — without needing Enterprise.

Perfect for: self-hosted n8n users who want audit trails, CI/CD for automations, or staging-to-production sync.

**Topics:** Developer Tools, Open Source, Productivity

---

## Twitter/X Thread

1/ I built n8n-sync — a free CLI that puts your n8n workflows under Git version control 🔄

No more losing track of workflow changes. No more "who broke the automation?"

pip install n8n-sync

2/ How it works:
• n8n-sync pull → exports workflows as readable JSON
• git commit → now you have history & diffs
• n8n-sync diff → compare local vs remote
• n8n-sync status → detect drift

3/ Use cases:
✅ Backup to Git (audit trail)
✅ CI/CD (diff --check exits 1 on drift)
✅ Staging → Production sync
✅ Multi-instance management

4/ Why this matters:
n8n Enterprise has version control. Community Edition doesn't. 

If you're self-hosting n8n CE, n8n-sync fills that gap for free.

5/ It's open source (MIT), works with any n8n instance, and takes 30 seconds to set up.

GitHub: github.com/badwalx/n8n-sync
PyPI: pypi.org/project/n8n-sync
