# Product Hunt Launch Draft: n8n-sync CLI

## Tagline
Git version control for n8n workflows — free and open source

## Full Description
n8n-sync is the first CLI that brings Git-like version control to n8n Community Edition workflows. It lets you backup, sync, diff, and detect drift across your n8n instances — all without needing Enterprise Source Control (€667/mo).

**Core Features:**
- **Pull/Push Workflows**: Export workflows as normalized JSON files (YAML frontmatter + sorted JSON) for readable Git diffs
- **Drift Detection**: Know instantly if someone changed a workflow in the UI with `n8n-sync status`
- **Semantic Diffs**: Compare local and remote workflows with meaningful node‑level differences
- **Credential Mapping**: Automatically map credentials between staging and production instances
- **CI/CD Ready**: `n8n-sync diff --check` exits 1 on drift — perfect for GitHub Actions pipelines
- **Multi‑Instance Support**: Manage multiple n8n instances from a single repository
- **Dry‑Run Push**: Preview changes before applying them to your live instance
- **Filtered Operations**: Select workflows by glob pattern (e.g., `--filter "prod-*"`)

**Why it matters:**
n8n Enterprise includes Source Control for €667/month. Community Edition users get nothing. If you’re self‑hosting n8n CE, n8n‑sync fills that gap — for free.

**Use Cases:**
1. **Audit Trail**: `n8n-sync pull && git commit` gives you version history and rollback capability
2. **CI/CD for Automations**: Run `diff --check` in your pipeline to catch unexpected workflow changes
3. **Environment Promotion**: Push workflows from staging to production with automatic credential mapping
4. **Fleet Management**: Keep dozens of client n8n instances in sync from one central repository

**Quick Start:**
```bash
pip install n8n-sync
n8n-sync init   # point it at your n8n instance
n8n-sync pull   # export all workflows to readable JSON files
git commit      # now you have full version history
```

**Open Source**: MIT licensed, available on PyPI and GitHub.

## Maker Comment
Hi Product Hunt! I’m Satwinder Badwal, the creator of n8n‑sync.

I built this tool because I kept losing track of workflow changes in my self‑hosted n8n instances — someone would edit a workflow in the UI, break something, and there was no history to roll back to. Enterprise has version control, but Community Edition didn’t have anything. So I created a CLI that makes n8n workflows first‑class Git citizens.

n8n‑sync solves three painful problems:
1. **No audit trail** — now every change is tracked in Git
2. **Manual promotion** — staging→prod sync with automatic credential mapping
3. **Silent drift** — CI‑ready drift detection catches unexpected changes before they cause outages

It’s free, open source, and works with any n8n Community Edition instance. I’d love to hear how you’re using n8n and what features would make n8n‑sync even more useful for your workflow.

## First Comment Strategy
- **Thank early upvoters** and ask about their n8n setup (self‑hosted? cloud?)
- **Highlight the €667/mo gap** — compare with n8n Enterprise Source Control
- **Share a quick demo GIF** (terminal showing `pull`, `diff`, `push`)
- **Ask for feedback** on planned Pro SaaS features (auto‑sync, dashboard, alerts)
- **Offer help** with setup — point to docs and examples

## Maker Names
Satwinder Badwal / @badwalx

## Pricing Note
**Free CLI**: The core CLI is and will remain free forever (MIT licensed). It includes all version‑control features: pull, push, diff, status, drift detection, credential mapping, CI integration, and multi‑instance support.

**Pro SaaS Coming**: Later this year we’ll launch a hosted Pro tier ($15‑29/month) with:
- Scheduled auto‑sync and drift alerts (Slack/Discord/email)
- Fleet dashboard for unlimited n8n instances
- Node‑level semantic diffs
- Environment promotion with credential mapping
- 30‑day change history and one‑click restore
- Team collaboration features

The Pro tier is for teams who want “set‑and‑forget” sync and a centralized dashboard — the free CLI remains fully functional for individual users and small teams.

## Gallery Image Descriptions (5 Shots)

1. **Terminal Demo** – Screenshot of `n8n-sync pull` output showing workflows being exported, followed by `git diff` highlighting clean, readable changes in a workflow JSON file.

2. **Drift Detection** – Side‑by‑side view: left panel shows `n8n-sync status` indicating “DRIFT” for a modified workflow, right panel shows the CI pipeline (`diff --check`) failing with exit code 1.

3. **Credential Mapping** – Diagram illustrating staging→production promotion: workflow JSON with placeholder credentials on the left, mapped production credentials on the right, arrow labeled “automatic mapping.”

4. **Multi‑Instance Dashboard** – Mockup of the upcoming Pro SaaS dashboard listing three n8n instances, each with sync status, last backup time, and drift alerts.

5. **GitHub Integration** – Screenshot of a GitHub Actions workflow file using `n8n-sync diff --check`, with green “✓ no drift” status next to a commit history showing regular automated backups.

## Launch Day Checklist

### Pre‑Launch (Week Before)
- [ ] Finalize all launch content (this document)
- [ ] Prepare demo GIF/video (terminal recording)
- [ ] Schedule social posts (Twitter, LinkedIn, Reddit r/n8n, n8n Forum)
- [ ] Notify email list (if any)
- [ ] Ensure documentation site (n8n-sync.b7co.cloud) is polished
- [ ] Double‑check PyPI package page and GitHub README

### Launch Day (Morning)
- [ ] **9:00 AM** – Post on Product Hunt (with optimized tagline, description, gallery images)
- [ ] **9:05 AM** – Maker comment posted
- [ ] **9:10 AM** – Share launch link on Twitter/X (thread), LinkedIn, and personal network
- [ ] **9:30 AM** – Post on n8n Community Forum (Community Showcase category)
- [ ] **10:00 AM** – Post on Reddit r/n8n (respect subreddit rules)

### Launch Day (Throughout Day)
- [ ] Monitor Product Hunt comments and respond promptly
- [ ] Engage with upvoters (thank them, ask about their use case)
- [ ] Share updates/achievements (“100 upvotes!”, “Featured on front page”)
- [ ] Post demo GIF/video as reply on Product Hunt
- [ ] Monitor GitHub for new stars/issues

### Post‑Launch (Next 48h)
- [ ] Collect feedback from comments and GitHub issues
- [ ] Write “Launch Results” blog post
- [ ] Follow up with interested users (offer setup help)
- [ ] Update roadmap based on feedback
- [ ] Begin planning Pro SaaS beta

---

**Additional Notes:**
- **Hashtags**: #DevTools #OpenSource #n8n #Automation #VersionControl #CLI
- **Links**: 
  - GitHub: https://github.com/badwalx/n8n-sync
  - PyPI: https://pypi.org/project/n8n-sync/
  - Docs: https://n8n-sync.b7co.cloud/
  - Forum Post: https://community.n8n.io/t/322533
- **Differentiator**: Only CLI for n8n workflow version control; Enterprise gap: €667/mo for source control features that n8n-sync provides free.