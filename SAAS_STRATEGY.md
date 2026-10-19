# n8n-sync SaaS — Competitive Intel & Feature Priority

## The Gap
n8n Enterprise Source Control = €667/mo, still can't merge, detect conflicts, or do per-version revert.
Free CLI tools exist but lack: auto-sync, credential mapping, fleet management, semantic diffs, CI/CD hooks.
**Price gap: $0 → €667 with nothing in between.** n8n-sync fills it.

## Top 5 Features by Demand Signal

| Priority | Feature | Willingness | Key Evidence |
|----------|---------|-------------|--------------|
| 1 | Auto-sync + drift detection + notifications | $10-20/mo | Every lost-workflow incident traces to "we forgot to push" or "we didn't notice it changed." Forum posts 257648, 42099, 22503. |
| 2 | Environment promotion (dev→staging→prod) + credential mapping | $15-25/mo | Forum 295660 (versioning across envs), 303592 (credential syncing). "The part everyone underestimates." |
| 3 | Multi-instance fleet dashboard | $20-30/mo | Agency scaling pain at 8-12 clients. No single-pane tool exists. Maintain Flow is adjacent (monitoring) but not sync. |
| 4 | Semantic workflow diffs (node-level) | $10-15/mo | GitHub issue #26707. JSON diffs bury reviewers in "thousands of lines." |
| 5 | CI/CD webhook triggers | $15-25/mo | Forum 3056 (years of engagement). n8n has no migration API for CD step. |

## Competitors

| Tool | Price | Gap They Leave |
|------|-------|---------------|
| n8n Business Source Control | €667/mo | No merge, no conflict detection, pull overwrites, no auto-push, Community excluded |
| ParsedVentures GitHub-n8n-sync | ~$49-99 one-time | No multi-instance, no credential mapping, no CI/CD hooks, no SaaS dashboard |
| Maintain Flow | Pre-launch | Monitoring only, not sync/versioning — complementary not competing |
| Open-source CLIs (n8nc, @egose/n8n-sync) | Free | No dashboard, no fleet view, no semantic diffs, no scheduled auto-sync |
| Aisle.sh | Per-seat | Replaces n8n entirely (code-first Python), different paradigm |

## Updated Tier Structure

### Free — $0 forever
- CLI: init, pull, push, diff, status, list + --filter
- Single instance sync to one Git repo
- YAML frontmatter + sorted JSON diffs
- `diff --check` CI exit codes
- Dry-run push
- GitHub community support

### Pro — $15/mo
- Everything in Free
- **Auto-sync scheduling** (managed cron — set and forget)
- **Drift detection** with Slack/Discord/email alerts
- **Environment promotion** with credential mapping
- **Semantic workflow diffs** (node-level change view)
- **CI/CD webhook triggers** (GitHub Actions, GitLab CI)
- 3 connected n8n instances
- 30-day change history + one-click restore

### Team — $29/mo
- Everything in Pro
- **Fleet dashboard** (unlimited instances)
- Per-instance health + last-sync tracking
- Team members (5) with shared sync configs
- Audit log of all sync operations
- Client/workflow tagging across instances
- Monthly fleet health report (PDF/email)
- Priority support

## Conversion Trigger
Auto-sync + drift detection. This feature alone justifies the subscription — 
it prevents the "silent production breakage" that every forum thread about 
lost workflows traces back to. The first incident it prevents pays for years of subscription.
