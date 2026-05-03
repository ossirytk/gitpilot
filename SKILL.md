---
name: gitpilot
description: Git workflow and GitHub CLI tools. Use this skill when the user wants to inspect the working tree, stage or commit changes, view history, manage branches, push/pull, or interact with GitHub pull requests and issues. Invoke for prompts like "commit these changes", "show me recent commits", "create a PR", "what's staged?", "switch to branch X", or "list open issues".
---

## Overview

gitpilot wraps `git` and `gh` CLI as structured MCP tool calls. All tools return JSON. Use gitpilot for the full git workflow loop — from inspecting changes through committing, branching, and opening pull requests.

## Available Tools

### Git

| Tool | When to use |
|------|-------------|
| `gitpilot-git_status` | Inspect the working tree — branch, staged, unstaged, and untracked files. Use before committing. |
| `gitpilot-git_diff` | Show raw unified diff of working-tree or staged changes. Optional `file` to scope to one path. For structured JSON hunks, use diffpilot instead. |
| `gitpilot-git_commit` | Stage files and create a commit. Required: `path`, `message`. Optional: `add_all` (bool — run `git add -A` before committing). |
| `gitpilot-git_log` | View recent commit history. Optional: `branch`, `author`, `file`, `limit`. Set `include_diff_stat: true` to get `files_changed` per commit. Output includes `truncated: true` when capped by `limit`. |
| `gitpilot-git_show` | Inspect metadata and diff for a specific commit or ref. |
| `gitpilot-git_branch` | List, create, switch, or delete branches. |
| `gitpilot-git_merge` | Merge a branch into the current branch. |
| `gitpilot-git_stash` | Push or pop uncommitted changes to/from the stash. |
| `gitpilot-git_reset` | Unstage files or reset HEAD (soft / mixed / hard). |
| `gitpilot-git_tag` | List, create, or delete tags. |
| `gitpilot-git_remote` | List or manage remotes. |
| `gitpilot-git_fetch` | Download objects and refs from a remote. |
| `gitpilot-git_pull` | Fetch and integrate remote changes. |
| `gitpilot-git_push` | Push commits to a remote. |

### GitHub CLI (`gh`)

| Tool | When to use |
|------|-------------|
| `gitpilot-gh_pr_create` | Open a pull request. Required: `path`, `title`. Optional: `body`, `base`, `draft`. |
| `gitpilot-gh_pr_list` | List pull requests. Filters: `state`, `base`, `author`, `label`. |
| `gitpilot-gh_pr_view` | Read PR details, body, and reviews. |
| `gitpilot-gh_issue_create` | Open a new issue. Required: `path`, `title`. Optional: `body`, `labels`. |
| `gitpilot-gh_issue_list` | List issues. Filters: `state`, `label`, `assignee`, `author`. |

## Guidance

- **Workflow order**: `git_status` → `git_diff` → `git_commit` → `git_push` → `gh_pr_create`
- **History**: use `git_log` with `include_diff_stat: true` when you need to know which files a commit touched. For structured JSON hunks on staged changes use diffpilot's `diff_staged`.
- **Unstaged diffs**: `git_diff` (with `staged=False`) returns raw unified diff text for working-tree changes — diffpilot does not cover that case.
- **Requires**: `git` and (for `gh_*` tools) `gh` on `PATH` and authenticated.
