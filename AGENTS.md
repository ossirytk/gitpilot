# AGENTS.md — Project Rules for AI Assistants (Python)

gitpilot is a Git workflow MCP server that wraps the `git` and `gh` CLI tools, exposing common operations — status, diff, commit, branch management, stash, log, and PR creation — as structured MCP tool calls.

---

## Tech Stack

- **Language:** Python 3.12+
- **MCP Framework:** FastMCP
- **Build / env:** uv + hatchling
- **Linter / formatter:** ruff
- **Tests:** pytest + pytest-cov

---

## Development Commands

```sh
# Install all dependencies (including dev)
uv sync

# Run the server
uv run gitpilot

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Fix auto-fixable lint issues
uv run ruff check --fix .

# Run tests
uv run pytest
```

---

## Project Structure

```
gitpilot/
├── src/
│   └── gitpilot/
│       ├── __init__.py      # Package marker
│       ├── __main__.py      # python -m gitpilot entry point
│       └── server.py        # FastMCP server + all tool definitions
├── pyproject.toml           # Project metadata, deps, ruff config
├── .python-version          # Pinned Python version (3.12)
├── AGENTS.md                # This file
└── README.md                # User-facing documentation
```

---

## Key Conventions

- All tool logic lives in `src/gitpilot/server.py` initially; extract helpers into sibling modules as they grow.
- Add dependencies with `uv add <package>`; add dev dependencies with `uv add --dev <package>`.
- ruff is the sole formatter and linter — never use black, isort, or other tools.
- `pyproject.toml` is the single source of truth for all ruff settings.
- Run `uv run ruff check --fix . && uv run ruff format .` before every commit.
