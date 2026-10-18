# n8n-sync

A Python CLI for versioning and synchronizing n8n Community Edition workflows using the public API v1. Requires Python 3.10+ and an n8n API key with workflow read/write permissions (and tag read/write permissions when synchronizing tags).

```sh
pip install .
cp .n8n-sync.example.yml .n8n-sync.yml
export N8N_STAGING_KEY='your-key'
export N8N_PRODUCTION_KEY='your-other-key'
n8n-sync pull --instance staging
git add workflows
git commit -m 'Snapshot workflows'
n8n-sync push --instance production --dry-run
n8n-sync push --instance production
n8n-sync diff --instance production --check
n8n-sync status --instance production
```

Use `--config PATH` on each command. A single configured instance is selected automatically; otherwise `--instance` is required. Relative workflow paths resolve against the configuration file, regardless of the working directory. API keys must use `${ENV_VAR}` placeholders; literal keys are rejected. Configure only the instances you need, as all configured key placeholders must resolve.

Workflow files use the spec's YAML frontmatter followed by formatted JSON, even though their extension is `.json`. They are not standalone JSON imports: use this CLI to push them. Plain n8n JSON exports can also be read. Frontmatter contains `name`, `active`, sorted tag names, and `lastModified`. The body contains nodes, connections, and settings. Node and workflow IDs and credential IDs are removed; credential names remain. JSON object keys and nodes are sorted, while connection arrays and parameter arrays preserve their meaningful order. Modification timestamps are informational and do not count as drift. n8n runtime data, execution history, pin data, and instance metadata are excluded.

Workflows match by exact, case-sensitive name. Duplicate names are rejected. Renaming a local workflow creates a new workflow on push. Pull reuses filenames for existing names and disambiguates slug collisions; it preserves local-only files and overwrites matching workflows. Neither push nor pull deletes workflows. Back up or commit local edits before pulling. Git operations are explicit, so the CLI never makes commits automatically.

Credential mappings are indexed by **target** instance: local name → target name. IDs resolve by credential type and target name using references in the target's existing workflows. For a credential not referenced there yet, set `credential_ids.<instance>.<credential-type>.<target-name>` to its ID (see example config). No private API or credential secret export is used. Missing or ambiguous references fail before any writes. Credentials themselves must already exist on the target. Mapping is also applied during drift detection.

Push validates every local workflow and resolves credentials and tags before writing. Tags must already exist on the target. It creates or updates changed workflows, assigns tags, and activates/deactivates to match the local document. An already matching workflow is skipped. Remote-only workflows remain untouched. Multiple API writes are not transactional; an error can leave partial changes. The error reports the failed workflow; run `diff` before retrying. Dry run performs reads and the same preflight but no writes. Workflow parameters are preserved verbatim, including embedded workflow references; instance-specific subworkflow IDs and hardcoded secrets in parameters must be reviewed before promotion. Workflow settings must be supported by the target n8n version.

`diff --check` and `status --check` exit 1 on drift, 0 when synchronized, and 2 on configuration/API/file errors. Drift states are `in-sync`, `changed`, `local-only`, and `remote-only`. Diff and status treat a missing workflow directory as empty; push requires an existing directory. This supports running checks in your own CI; a dedicated GitHub Action is outside the Phase 1 scope. Output may include sensitive workflow parameters, so protect CI logs and review exports before committing.

```sh
pip install -e '.[dev]'
pytest
ruff check src tests
python -m n8n_sync --help
# Optional container; mount config/workflows and pass environment variables:
docker build -t n8n-sync .
docker run --rm -v "$PWD:/workspace" -e N8N_STAGING_KEY -e N8N_PRODUCTION_KEY n8n-sync status -i staging
```

API documentation: [n8n public API](https://docs.n8n.io/api/). There is no automatic retry of writes, avoiding accidental duplicate creates after ambiguous network failures.
