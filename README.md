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
| `git_log` | View recent commit history with optional branch/author/file filters |
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

# Lint + format (pre-commit)
uv run ruff check --fix . && uv run ruff format .

# Run tests
uv run pytest
```
