# n8n-sync Launch Posts

## n8n Community Forum

**Category:** Community Showcase
**Title:** n8n-sync — Git-based version control for Community Edition workflows

**Body:**

Hey everyone 👋

If you're self-hosting n8n Community Edition, you already know the pain: no built-in version control. Enterprise has Source Control at €667/mo, but for Community users, there's nothing.

I got tired of manually exporting workflow JSON, committing it, and fixing credentials by hand when promoting from staging to production. So I built **n8n-sync** — a CLI that gives you Git-friendly version control for your n8n workflows.

**What it does:**
- `n8n-sync pull` — exports all workflows to normalized JSON files (readable diffs!)
- `n8n-sync push` — creates/updates workflows with credential mapping + dry-run
- `n8n-sync diff` — shows semantic differences between local files and your instance
- `n8n-sync status` — lists all workflows with drift detection

**Why it's useful:**
- `diff --check` exits 1 on drift — perfect for CI pipelines
- Credential mapping between staging/production without manual fixes
- YAML frontmatter + sorted JSON = actually readable Git diffs
- No n8n Enterprise required

It's open source: https://github.com/badwalx/n8n-sync

Would love feedback from other self-hosters. What's missing? What would make this useful for your workflow?

---

## Reddit r/n8n

**Title:** Built a CLI for n8n Community Edition version control (since Enterprise Source Control is €667/mo)

**Body:**

Self-hosting n8n and tired of manually exporting/importing workflow JSON? 

I built n8n-sync — a Python CLI that gives you git-friendly version control for Community Edition workflows:

- Pull/push workflows with credential mapping
- Drift detection with CI-friendly exit codes
- Normalized JSON for readable Git diffs
- Dry-run push for safe promotions

Free + open source. Would appreciate feedback from other self-hosters.

https://github.com/badwalx/n8n-sync
