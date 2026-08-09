# Releasing `playerelo-mcp`

The MCP server ships two ways users find it: as a **PyPI package** (`uvx playerelo-mcp`)
and via the **MCP registry** (which the directories — PulseMCP, Glama, mcp.so — index
from). This is the runbook for both.

## 0. Version bump (when releasing a new version)

Keep three files in lock-step: `pyproject.toml` `version`, `playerelo_mcp/__init__.py`
`__version__`, and `server.json` (`version` + the package `version`).

## 1. Build + validate

```bash
python -m build            # -> dist/playerelo_mcp-<v>.tar.gz + .whl
python -m twine check dist/*
```

## 2. Publish to PyPI

Needs a PyPI account and an API token (create at <https://pypi.org/manage/account/token/>).
The token is a credential — keep it out of the shell history; prefer `~/.pypirc` or a
one-shot env:

```bash
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-XXXX python -m twine upload dist/*
```

Smoke-test the published package from a clean environment:

```bash
PLAYERELO_API_KEY=pe_live_... uvx playerelo-mcp    # should start and wait on stdio
```

## 3. Publish to the official MCP registry

The registry entry (`server.json`) points at the PyPI package, so do step 2 first.
Install the publisher CLI (Go binary) and authenticate as the GitHub namespace owner
(`io.github.mwolters-cmyk/*`), which is an interactive browser device-login:

```bash
# install mcp-publisher (see github.com/modelcontextprotocol/registry releases), then:
mcp-publisher login github        # opens a browser device-code flow
mcp-publisher publish             # reads ./server.json in this directory
```

The directories (PulseMCP, Glama, mcp.so) crawl the official registry, so a registry
publish gets you listed on them within a few days — no separate submission.

## 4. Smithery (optional, separate)

Smithery builds/hosts from a GitHub repo. Connect `mwolters-cmyk/playerelo-mcp` at
<https://smithery.ai/new> and follow its prompts (it may want a `smithery.yaml`; add one
if so).

## Notes

- The package is a thin HTTP client over the public API — no secrets in the repo. Safe to
  keep the source public.
- `server.json`'s `name` namespace (`io.github.mwolters-cmyk/*`) is proven by the
  `mcp-publisher login github` step; the `repository.url` must resolve to a real repo.
