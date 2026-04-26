# gitpilot

Git workflow MCP server — wraps `git` and `gh` CLI as structured tool calls.

> **Status:** 🚧 Work in progress

gitpilot exposes common Git operations as MCP tools, letting AI assistants inspect repository state, make commits, manage branches, and open pull requests without leaving the conversation.

---

## Tools

| Tool | Description |
|------|-------------|
| `git_status` | Inspect the working tree — branch, staged, unstaged, and untracked files |
| `git_diff` | Show unified diff of working-tree or staged changes |
| `git_commit` | Stage files and create a commit |
| `git_branch` | List, create, or switch branches |
| `git_stash` | Push or pop uncommitted changes to/from the stash |
| `git_log` | View recent commit history |
| `gh_pr_create` | Open a pull request via the `gh` CLI |

---

## Installation

> Coming soon.

---

## Development

```sh
# Install dependencies
uv sync

# Run the server
uv run gitpilot

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Run tests
uv run pytest
```
