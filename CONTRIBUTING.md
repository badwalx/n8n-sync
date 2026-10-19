# Contributing

Thanks for your interest in n8n-sync! Here's how to contribute.

## Setup

```sh
git clone https://github.com/badwalx/n8n-sync.git
cd n8n-sync
pip install -e '.[dev]'
```

## Development

```sh
pytest                  # run tests
ruff check src tests    # lint
python -m n8n_sync      # run locally
```

## Making changes

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes + add tests
4. Ensure `pytest` and `ruff check` pass
5. Push and open a PR

## Commit style

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `refactor:` code restructure
- `chore:` maintenance

## Releasing

Maintainers only:

1. Bump version in `pyproject.toml`
2. `git commit -am "vX.Y.Z: description"`
3. `git tag vX.Y.Z && git push origin master --tags`
4. GitHub Actions auto-publishes to PyPI

## Ideas for contributions

- [ ] `n8n-sync pull --filter name:*report*` — selective pull by glob pattern
- [ ] `n8n-sync push --filter tag:production` — push only tagged workflows
- [ ] `n8n-sync export` — export as plain n8n JSON (for import in UI)
- [ ] `n8n-sync watch` — auto-pull on remote changes
- [ ] Config `ignore_patterns` — exclude workflows by name pattern
- [ ] Shell completions (bash, zsh, fish)
- [ ] Docker image on GitHub Container Registry
