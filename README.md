# gitpilot

Git workflow MCP server — wraps `git` and `gh` CLI as structured tool calls, optimized for AI assistants.

---

## Tools

### Git

| Tool | Description |
|------|-------------|
| `git_status` | Inspect the working tree — branch, staged, unstaged, and untracked files |
| `git_diff` | Show unified diff of working-tree or staged changes |
| `git_commit` | Stage files and create a commit |
| `git_log` | View recent commit history with optional branch/author/file filters; set `include_diff_stat: true` to get `files_changed` per commit; output includes `truncated: true` when result was capped by `limit` |
| `git_show` | Inspect metadata and diff for a specific commit or ref |
| `git_branch` | List, create, switch, or delete branches |
| `git_merge` | Merge a branch into the current branch |
| `git_stash` | Push or pop uncommitted changes to/from the stash |
| `git_reset` | Unstage files or reset HEAD (soft / mixed / hard) |
| `git_tag` | List, create, or delete tags |
| `git_remote` | List or manage remotes |
| `git_fetch` | Download objects and refs from a remote |
| `git_pull` | Fetch and integrate remote changes |
| `git_push` | Push commits to a remote |

### GitHub CLI (`gh`)

| Tool | Description |
|------|-------------|
| `gh_pr_create` | Open a pull request |
| `gh_pr_list` | List pull requests (filter by state, base, author, label) |
| `gh_pr_view` | Read PR details, body, and reviews |
| `gh_issue_create` | Open a new issue |
| `gh_issue_list` | List issues (filter by state, label, assignee, author) |

---

## Installation

**Requires:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

> **Note:** `git` must be installed and available on your `PATH`. The `gh_*` tools additionally require the [GitHub CLI (`gh`)](https://cli.github.com/) on your `PATH` and authenticated (`gh auth login`).

### Option A — Install as a uv tool (recommended)

```sh
uv tool install git+https://github.com/ossirytk/gitpilot
```

Verify:

```sh
gitpilot --help
```

To update later:

```sh
uv tool upgrade gitpilot
```

### Option B — Clone and run from source

```sh
git clone https://github.com/ossirytk/gitpilot
cd gitpilot
uv sync
```

---

## Configuration

### GitHub Copilot CLI

Add to `~/.copilot/mcp-config.json`:

**Option A (installed tool):**

```json
{
  "mcpServers": {
    "gitpilot": {
      "type": "stdio",
      "command": "gitpilot"
    }
  }
}
```

**Option B (local clone):**

```json
{
  "mcpServers": {
    "gitpilot": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/path/to/gitpilot", "gitpilot"]
    }
  }
}
```

### VS Code Copilot

Add to your user-level MCP config file:
- **Linux:** `~/.config/Code/User/mcp.json`
- **macOS:** `~/Library/Application Support/Code/User/mcp.json`
- **Windows:** `%APPDATA%\Code\User\mcp.json`

**Option A:**

```json
{
  "servers": {
    "gitpilot": {
      "type": "stdio",
      "command": "gitpilot"
    }
  }
}
```

**Option B:**

```json
{
  "servers": {
    "gitpilot": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/path/to/gitpilot", "gitpilot"]
    }
  }
}
```

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

# Lint + format (pre-commit)
uv run ruff check --fix . && uv run ruff format .

# Run tests
uv run pytest
```
