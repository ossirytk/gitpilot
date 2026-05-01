"""Git workflow MCP server wrapping git and gh CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

mcp: FastMCP = FastMCP(
    name="gitpilot",
    instructions=(
        "gitpilot is a Git workflow MCP server optimized for AI assistants. "
        "Use `git_status` to inspect the working tree. "
        "Use `git_diff` to show changes (staged or unstaged). "
        "Use `git_commit` to stage and commit changes. "
        "Use `git_log` to view commit history. "
        "Use `git_show` to inspect a specific commit or ref. "
        "Use `git_branch` to list, create, switch, or delete branches. "
        "Use `git_merge` to merge a branch into the current branch. "
        "Use `git_stash` to stash or pop uncommitted changes. "
        "Use `git_reset` to unstage files or reset HEAD. "
        "Use `git_tag` to list, create, or delete tags. "
        "Use `git_remote` to list or manage remotes. "
        "Use `git_fetch` to download remote refs. "
        "Use `git_pull` to fetch and integrate remote changes. "
        "Use `git_push` to upload commits to a remote. "
        "Use `gh_pr_create` to open a pull request. "
        "Use `gh_pr_list` to list pull requests. "
        "Use `gh_pr_view` to read a pull request. "
        "Use `gh_issue_create` to open an issue. "
        "Use `gh_issue_list` to list issues."
    ),
)

_SEP = "\x1f"  # ASCII unit separator — safe as a git pretty-format delimiter


# ── Helpers ───────────────────────────────────────────────────────────────────


def _resolve(path: str) -> str:
    return str(Path(path).expanduser().resolve())


def _run(args: list[str], cwd: str) -> tuple[int, str, str]:
    try:
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as exc:
        cmd = " ".join(args)
        return 1, "", f"failed to run '{cmd}' in '{cwd}': {exc}"
    else:
        return result.returncode, result.stdout, result.stderr


def _err(msg: str) -> dict[str, Any]:
    return {"error": msg}


def _stash_list(cwd: str) -> list[str]:
    _, out, _ = _run(["git", "stash", "list"], cwd)
    return [line.strip() for line in out.splitlines() if line.strip()]


# ── git_status ────────────────────────────────────────────────────────────────


@mcp.tool
def git_status(path: str = ".") -> dict[str, object]:
    """Return the working-tree status of a repository.

    Args:
        path: Path to the repository root. Defaults to the current directory.
    """
    cwd = _resolve(path)
    rc, stdout, stderr = _run(["git", "status", "--porcelain=v2", "--branch"], cwd)
    if rc != 0:
        return _err(stderr.strip() or "git status failed")

    branch = "(unknown)"
    upstream: str | None = None
    ahead = 0
    behind = 0
    staged: list[dict[str, str]] = []
    unstaged: list[dict[str, str]] = []
    untracked: list[str] = []
    unmerged: list[str] = []

    for line in stdout.splitlines():
        if line.startswith("# branch.head "):
            branch = line[len("# branch.head ") :]
        elif line.startswith("# branch.upstream "):
            upstream = line[len("# branch.upstream ") :]
        elif line.startswith("# branch.ab "):
            for part in line.split():
                if part.startswith("+"):
                    ahead = int(part[1:])
                elif part.startswith("-"):
                    behind = int(part[1:])
        elif line.startswith("1 "):
            # porcelain v2 ordinary entry: 1 XY sub mH mI mW hH hI path
            parts = line.split(" ", maxsplit=8)
            if len(parts) < 9:
                continue
            xy = parts[1]
            name = parts[8].split("\t")[0]
        elif line.startswith("2 "):
            # porcelain v2 rename/copy entry: 2 XY sub mH mI mW hH hI Xscore path\torigPath
            parts = line.split(" ", maxsplit=9)
            if len(parts) < 10:
                continue
            xy = parts[1]
            name = parts[9].split("\t")[0]
        if line.startswith(("1 ", "2 ")):
            _status_labels = {
                "M": "modified",
                "A": "added",
                "D": "deleted",
                "R": "renamed",
                "C": "copied",
                "U": "unmerged",
            }
            if xy[0] != ".":
                staged.append({"status": _status_labels.get(xy[0], xy[0]), "file": name})
            if xy[1] != ".":
                unstaged.append({"status": _status_labels.get(xy[1], xy[1]), "file": name})
        elif line.startswith("u "):
            unmerged.append(line.split()[-1])
        elif line.startswith("? "):
            untracked.append(line[2:].strip())

    result: dict[str, Any] = {
        "branch": branch,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "clean": not (staged or unstaged or untracked or unmerged),
    }
    if upstream:
        result["upstream"] = upstream
        result["ahead"] = ahead
        result["behind"] = behind
    if unmerged:
        result["unmerged"] = unmerged
    return result


# ── git_diff ──────────────────────────────────────────────────────────────────


@mcp.tool
def git_diff(path: str = ".", staged: bool = False, file: str = "") -> dict[str, object]:
    """Show changes in the working tree or index.

    Args:
        path: Path to the repository root.
        staged: When True, show staged (index) changes instead of unstaged.
        file: Optional path to a specific file to diff.
    """
    cwd = _resolve(path)
    diff_args = ["git", "diff"]
    if staged:
        diff_args.append("--staged")
    stat_args = [*diff_args, "--stat"]
    if file:
        diff_args += ["--", file]
        stat_args += ["--", file]

    rc_diff, diff_out, diff_err = _run(diff_args, cwd)
    if rc_diff != 0:
        return _err(diff_err.strip() or "git diff failed")

    rc_stat, stat_out, _ = _run(stat_args, cwd)
    stats: list[str] = [line.strip() for line in stat_out.splitlines() if line.strip()] if rc_stat == 0 else []

    return {"diff": diff_out, "stats": stats, "staged": staged}


# ── git_commit ────────────────────────────────────────────────────────────────


@mcp.tool
def git_commit(message: str, path: str = ".", add_all: bool = False) -> dict[str, object]:
    """Stage files and create a commit.

    Args:
        message: The commit message.
        path: Path to the repository root.
        add_all: When True, run ``git add -A`` before committing.
    """
    cwd = _resolve(path)
    if add_all:
        rc, _, stderr = _run(["git", "add", "-A"], cwd)
        if rc != 0:
            return _err(stderr.strip() or "git add -A failed")

    rc, stdout, stderr = _run(["git", "commit", "-m", message], cwd)
    if rc != 0:
        return _err(stderr.strip() or stdout.strip() or "git commit failed")

    # Extract SHA from output like "[branch abc1234] message"
    sha = ""
    for line in stdout.splitlines():
        if line.startswith("["):
            parts = line.split()
            if len(parts) >= 2:
                sha = parts[1].rstrip("]")
            break

    rc_show, show_out, _ = _run(["git", "show", "--stat", "--format=", sha or "HEAD"], cwd)
    files_changed = [ln.strip() for ln in show_out.splitlines() if ln.strip() and "|" in ln] if rc_show == 0 else []

    return {"sha": sha, "message": message, "files_changed": files_changed}


# ── git_log ───────────────────────────────────────────────────────────────────


@mcp.tool
def git_log(
    path: str = ".",
    limit: int = 20,
    oneline: bool = True,
    branch: str = "",
    author: str = "",
    file: str = "",
) -> dict[str, object]:
    """Return recent commit history.

    Args:
        path: Path to the repository root.
        limit: Maximum number of commits to return (capped at 500).
        oneline: When True, return abbreviated one-line entries (sha + subject only).
        branch: Branch or ref to walk. Defaults to HEAD.
        author: Filter commits by author name or email substring.
        file: Restrict to commits touching this path.
    """
    cwd = _resolve(path)
    limit = min(max(1, limit), 500)
    fmt = f"%H{_SEP}%an{_SEP}%ae{_SEP}%aI{_SEP}%s" if oneline else f"%H{_SEP}%an{_SEP}%ae{_SEP}%aI{_SEP}%s{_SEP}%b"
    args = ["git", "log", f"--pretty=format:{fmt}%x00", f"-n{limit}"]
    if branch:
        args.append(branch)
    if author:
        args.append(f"--author={author}")
    if file:
        args += ["--", file]

    rc, stdout, stderr = _run(args, cwd)
    if rc != 0:
        return _err(stderr.strip() or "git log failed")

    commits: list[dict[str, str]] = []
    for raw_record in stdout.split("\x00"):
        record = raw_record.strip()
        if not record:
            continue
        # maxsplit=5 keeps any embedded _SEP chars in the body as part of parts[5]
        parts = record.split(_SEP, 5)
        if len(parts) < 5:
            continue
        entry: dict[str, str] = {
            "sha": parts[0][:12],
            "sha_full": parts[0],
            "author": parts[1],
            "email": parts[2],
            "date": parts[3],
            "subject": parts[4],
        }
        if not oneline and len(parts) > 5:
            entry["body"] = parts[5].strip()
        commits.append(entry)

    return {"commits": commits, "count": len(commits)}


# ── git_show ──────────────────────────────────────────────────────────────────


@mcp.tool
def git_show(ref: str = "HEAD", path: str = ".") -> dict[str, object]:
    """Show metadata and diff for a specific commit or ref.

    Args:
        ref: Git ref (SHA, branch, tag). Defaults to HEAD.
        path: Path to the repository root.
    """
    cwd = _resolve(path)

    # Fetch metadata separately to avoid multi-line bodies corrupting stat/diff parsing
    fmt = f"%H{_SEP}%an{_SEP}%ae{_SEP}%aI{_SEP}%s{_SEP}%b"
    rc, meta_out, stderr = _run(["git", "show", "--no-patch", f"--pretty=tformat:{fmt}", ref], cwd)
    if rc != 0:
        return _err(stderr.strip() or "git show failed")

    meta: dict[str, str] = {}
    parts = meta_out.strip().split(_SEP, 5)
    if len(parts) >= 5:
        meta = {
            "sha": parts[0][:12],
            "sha_full": parts[0],
            "author": parts[1],
            "email": parts[2],
            "date": parts[3],
            "subject": parts[4],
            "body": parts[5].strip() if len(parts) > 5 else "",
        }

    # Fetch stats + diff with an empty format to suppress the commit header
    rc2, show_out, _ = _run(["git", "show", "--stat", "--patch", "--format=", ref], cwd)
    stat_lines: list[str] = []
    diff_start = 0
    if rc2 == 0:
        lines = show_out.splitlines()
        for i, line in enumerate(lines):
            if line.strip() and "|" in line:
                stat_lines.append(line.strip())
            elif line.startswith("diff --git"):
                diff_start = i
                break

    return {
        **meta,
        "stats": stat_lines,
        "diff": "\n".join(show_out.splitlines()[diff_start:]) if rc2 == 0 else "",
    }


# ── git_branch ────────────────────────────────────────────────────────────────


@mcp.tool
def git_branch(
    path: str = ".",
    create: str | None = None,
    switch: str | None = None,
    delete: str | None = None,
    remote: bool = False,
) -> dict[str, object]:
    """List, create, switch, or delete Git branches.

    Args:
        path: Path to the repository root.
        create: Name of a new branch to create (and switch to).
        switch: Name of an existing branch to switch to.
        delete: Name of a branch to delete.
        remote: When True and listing, include remote-tracking branches.
    """
    cwd = _resolve(path)

    if create:
        rc, _, stderr = _run(["git", "checkout", "-b", create], cwd)
        if rc != 0:
            return _err(stderr.strip() or f"Failed to create branch '{create}'")

    if switch:
        rc, _, stderr = _run(["git", "checkout", switch], cwd)
        if rc != 0:
            return _err(stderr.strip() or f"Failed to switch to branch '{switch}'")

    if delete:
        rc, _, stderr = _run(["git", "branch", "-d", delete], cwd)
        if rc != 0:
            return _err(stderr.strip() or f"Failed to delete branch '{delete}'")

    list_args = ["git", "branch", "--format=%(refname:short)\t%(HEAD)\t%(symref)"]
    if remote:
        list_args.append("-a")
    rc, stdout, stderr = _run(list_args, cwd)
    if rc != 0:
        return _err(stderr.strip() or "git branch failed")

    current = ""
    branches: list[str] = []
    for raw_line in stdout.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        fields = stripped.split("\t")
        name = fields[0]
        is_current = len(fields) > 1 and fields[1] == "*"
        symref = fields[2] if len(fields) > 2 else ""
        if symref:  # skip symbolic refs like remotes/origin/HEAD
            continue
        branches.append(name)
        if is_current:
            current = name

    return {"current": current, "branches": branches}


# ── git_merge ────────────────────────────────────────────────────────────────


@mcp.tool
def git_merge(
    branch: str,
    path: str = ".",
    no_ff: bool = False,
    message: str = "",
) -> dict[str, object]:
    """Merge a branch into the current branch.

    Args:
        branch: Branch name (or ref) to merge.
        path: Path to the repository root.
        no_ff: When True, always create a merge commit (--no-ff).
        message: Optional merge commit message.
    """
    cwd = _resolve(path)
    args = ["git", "merge"]
    if no_ff:
        args.append("--no-ff")
    if message:
        args += ["-m", message]
    args.append(branch)

    rc, stdout, stderr = _run(args, cwd)
    out = (stdout + stderr).strip()
    if rc != 0:
        return _err(out or f"git merge {branch!r} failed")
    return {"merged": branch, "output": out}


# ── git_stash ─────────────────────────────────────────────────────────────────


@mcp.tool
def git_stash(path: str = ".", pop: bool = False, message: str = "") -> dict[str, object]:
    """Stash or restore uncommitted changes.

    Args:
        path: Path to the repository root.
        pop: When True, pop the most recent stash instead of pushing.
        message: Optional stash description (used when pushing).
    """
    cwd = _resolve(path)
    if pop:
        rc, stdout, stderr = _run(["git", "stash", "pop"], cwd)
        action = "pop"
    else:
        args = ["git", "stash", "push"]
        if message:
            args += ["-m", message]
        rc, stdout, stderr = _run(args, cwd)
        action = "push"

    if rc != 0:
        return _err(stderr.strip() or stdout.strip() or f"git stash {action} failed")

    return {"action": action, "output": stdout.strip(), "stash_list": _stash_list(cwd)}


# ── git_reset ────────────────────────────────────────────────────────────────


@mcp.tool
def git_reset(
    path: str = ".",
    ref: str = "HEAD",
    mode: str = "mixed",
    files: list[str] | None = None,
) -> dict[str, object]:
    """Reset the current HEAD or unstage specific files.

    Args:
        path: Path to the repository root.
        ref: Commit to reset to. Defaults to HEAD.
        mode: Reset mode — soft, mixed, or hard. Ignored when ``files`` is set.
        files: If provided, unstage only these files (``git reset HEAD <files>``).
    """
    cwd = _resolve(path)
    if files:
        args = ["git", "reset", "HEAD", "--", *files]
    else:
        if mode not in {"soft", "mixed", "hard"}:
            return _err(f"Invalid mode {mode!r}. Choose from: soft, mixed, hard.")
        args = ["git", "reset", f"--{mode}", ref]

    rc, stdout, stderr = _run(args, cwd)
    if rc != 0:
        return _err(stderr.strip() or "git reset failed")
    return {"ref": ref, "mode": mode if not files else "unstage", "output": (stdout + stderr).strip()}


# ── git_tag ───────────────────────────────────────────────────────────────────


@mcp.tool
def git_tag(
    path: str = ".",
    create: str = "",
    delete: str = "",
    ref: str = "HEAD",
    message: str = "",
) -> dict[str, object]:
    """List, create, or delete Git tags.

    Args:
        path: Path to the repository root.
        create: Name of a new tag to create.
        delete: Name of a tag to delete.
        ref: Commit or ref to tag (used with ``create``). Defaults to HEAD.
        message: If set, create an annotated tag with this message.
    """
    cwd = _resolve(path)
    if create:
        args = ["git", "tag"]
        if message:
            args += ["-a", create, "-m", message]
        else:
            args.append(create)
        if ref != "HEAD":
            args.append(ref)
        rc, _, stderr = _run(args, cwd)
        if rc != 0:
            return _err(stderr.strip() or f"Failed to create tag '{create}'")

    if delete:
        rc, _, stderr = _run(["git", "tag", "-d", delete], cwd)
        if rc != 0:
            return _err(stderr.strip() or f"Failed to delete tag '{delete}'")

    rc, stdout, stderr = _run(["git", "tag", "--sort=-creatordate"], cwd)
    if rc != 0:
        return _err(stderr.strip() or "git tag list failed")
    tags = [t.strip() for t in stdout.splitlines() if t.strip()]
    return {"tags": tags}


# ── git_remote ────────────────────────────────────────────────────────────────


@mcp.tool
def git_remote(
    path: str = ".",
    add_name: str = "",
    add_url: str = "",
    remove: str = "",
) -> dict[str, object]:
    """List or manage Git remotes.

    Args:
        path: Path to the repository root.
        add_name: Name for a new remote to add (requires ``add_url``).
        add_url: URL for the new remote.
        remove: Name of a remote to remove.
    """
    cwd = _resolve(path)
    if add_name and add_url:
        rc, _, stderr = _run(["git", "remote", "add", add_name, add_url], cwd)
        if rc != 0:
            return _err(stderr.strip() or "git remote add failed")

    if remove:
        rc, _, stderr = _run(["git", "remote", "remove", remove], cwd)
        if rc != 0:
            return _err(stderr.strip() or f"Failed to remove remote '{remove}'")

    rc, stdout, stderr = _run(["git", "remote", "-v"], cwd)
    if rc != 0:
        return _err(stderr.strip() or "git remote -v failed")

    remotes: dict[str, dict[str, list[str]]] = {}
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        name, url, kind = parts[0], parts[1], parts[2].strip("()")
        if name not in remotes:
            remotes[name] = {}
        if kind not in remotes[name]:
            remotes[name][kind] = []
        remotes[name][kind].append(url)

    return {"remotes": remotes}


# ── git_fetch ─────────────────────────────────────────────────────────────────


@mcp.tool
def git_fetch(path: str = ".", remote: str = "origin", prune: bool = False) -> dict[str, object]:
    """Download objects and refs from a remote.

    Args:
        path: Path to the repository root.
        remote: Remote name to fetch from. Defaults to ``origin``.
        prune: When True, remove remote-tracking refs that no longer exist on the remote.
    """
    cwd = _resolve(path)
    args = ["git", "fetch", remote]
    if prune:
        args.append("--prune")
    rc, stdout, stderr = _run(args, cwd)
    out = (stdout + stderr).strip()
    if rc != 0:
        return _err(out or f"git fetch {remote!r} failed")
    return {"remote": remote, "output": out}


# ── git_pull ──────────────────────────────────────────────────────────────────


@mcp.tool
def git_pull(
    path: str = ".",
    remote: str = "origin",
    branch: str = "",
    rebase: bool = False,
) -> dict[str, object]:
    """Fetch and integrate changes from a remote.

    Args:
        path: Path to the repository root.
        remote: Remote name. Defaults to ``origin``.
        branch: Remote branch to pull. Defaults to the tracked upstream.
        rebase: When True, rebase instead of merge.
    """
    cwd = _resolve(path)
    args = ["git", "pull"]
    if rebase:
        args.append("--rebase")
    if branch:
        args += [remote, branch]
    rc, stdout, stderr = _run(args, cwd)
    out = (stdout + stderr).strip()
    if rc != 0:
        return _err(out or "git pull failed")
    return {"remote": remote, "branch": branch or "(upstream)", "output": out}


# ── git_push ──────────────────────────────────────────────────────────────────


@mcp.tool
def git_push(
    path: str = ".",
    remote: str = "origin",
    branch: str = "",
    force: bool = False,
    set_upstream: bool = False,
    tags: bool = False,
) -> dict[str, object]:
    """Push commits to a remote.

    Args:
        path: Path to the repository root.
        remote: Remote name. Defaults to ``origin``.
        branch: Local branch to push. Defaults to the current branch.
        force: When True, force-push (--force-with-lease for safety).
        set_upstream: When True, set the upstream tracking ref (-u).
        tags: When True, push all tags.
    """
    cwd = _resolve(path)
    args = ["git", "push"]
    if force:
        args.append("--force-with-lease")
    if set_upstream:
        args.append("-u")
    if tags:
        args.append("--tags")
    args.append(remote)
    if branch:
        args.append(branch)
    rc, stdout, stderr = _run(args, cwd)
    out = (stdout + stderr).strip()
    if rc != 0:
        return _err(out or "git push failed")
    return {"remote": remote, "branch": branch or "(current)", "output": out}


# ── gh_pr_create ──────────────────────────────────────────────────────────────


@mcp.tool
def gh_pr_create(
    title: str,
    body: str = "",
    base: str = "main",
    draft: bool = False,
    path: str = ".",
) -> dict[str, object]:
    """Open a pull request via the gh CLI.

    Args:
        title: PR title.
        body: PR description body.
        base: Target branch for the PR.
        draft: When True, create a draft PR.
        path: Path to the repository root.
    """
    cwd = _resolve(path)
    args = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base]
    if draft:
        args.append("--draft")
    rc, stdout, stderr = _run(args, cwd)
    if rc != 0:
        return _err(stderr.strip() or "gh pr create failed")

    url = stdout.strip()
    number = ""
    for part in url.rstrip("/").split("/"):
        if part.isdigit():
            number = part
    return {"url": url, "number": number}


# ── gh_pr_list ────────────────────────────────────────────────────────────────


@mcp.tool
def gh_pr_list(
    path: str = ".",
    state: str = "open",
    limit: int = 30,
    base: str = "",
    author: str = "",
    label: str = "",
) -> dict[str, object]:
    """List pull requests in the current repository.

    Args:
        path: Path to the repository root.
        state: Filter by state — open, closed, or merged.
        limit: Maximum number of PRs to return.
        base: Filter PRs targeting this base branch.
        author: Filter by PR author.
        label: Filter by label.
    """
    cwd = _resolve(path)
    args = [
        "gh",
        "pr",
        "list",
        "--state",
        state,
        "--limit",
        str(limit),
        "--json",
        "number,title,author,state,url,baseRefName,headRefName,isDraft,labels,createdAt",
    ]
    if base:
        args += ["--base", base]
    if author:
        args += ["--author", author]
    if label:
        args += ["--label", label]

    rc, stdout, stderr = _run(args, cwd)
    if rc != 0:
        return _err(stderr.strip() or "gh pr list failed")

    try:
        prs = json.loads(stdout)
    except json.JSONDecodeError:
        return _err(f"Failed to parse gh output: {stdout[:200]}")
    return {"pull_requests": prs, "count": len(prs)}


# ── gh_pr_view ────────────────────────────────────────────────────────────────


@mcp.tool
def gh_pr_view(pr: str, path: str = ".") -> dict[str, object]:
    """View details and body of a pull request.

    Args:
        pr: PR number or URL.
        path: Path to the repository root.
    """
    cwd = _resolve(path)
    fields = (
        "number,title,author,state,url,baseRefName,headRefName,"
        "isDraft,labels,body,reviews,commits,createdAt,mergedAt,closedAt"
    )
    rc, stdout, stderr = _run(["gh", "pr", "view", pr, "--json", fields], cwd)
    if rc != 0:
        return _err(stderr.strip() or f"gh pr view {pr!r} failed")
    try:
        return dict(json.loads(stdout))
    except json.JSONDecodeError:
        return _err(f"Failed to parse gh output: {stdout[:200]}")


# ── gh_issue_create ───────────────────────────────────────────────────────────


@mcp.tool
def gh_issue_create(
    title: str,
    body: str = "",
    label: str = "",
    assignee: str = "",
    path: str = ".",
) -> dict[str, object]:
    """Create a new issue via the gh CLI.

    Args:
        title: Issue title.
        body: Issue body text.
        label: Comma-separated labels to apply.
        assignee: GitHub username to assign.
        path: Path to the repository root.
    """
    cwd = _resolve(path)
    args = ["gh", "issue", "create", "--title", title, "--body", body]
    if label:
        for lbl in label.split(","):
            normalized_label = lbl.strip()
            if normalized_label:
                args += ["--label", normalized_label]
    if assignee:
        args += ["--assignee", assignee]
    rc, stdout, stderr = _run(args, cwd)
    if rc != 0:
        return _err(stderr.strip() or "gh issue create failed")

    url = stdout.strip()
    number = ""
    for part in url.rstrip("/").split("/"):
        if part.isdigit():
            number = part
    return {"url": url, "number": number}


# ── gh_issue_list ─────────────────────────────────────────────────────────────


@mcp.tool
def gh_issue_list(
    path: str = ".",
    state: str = "open",
    limit: int = 30,
    label: str = "",
    assignee: str = "",
    author: str = "",
) -> dict[str, object]:
    """List issues in the current repository.

    Args:
        path: Path to the repository root.
        state: Filter by state — open, closed, or all.
        limit: Maximum number of issues to return.
        label: Filter by label.
        assignee: Filter by assignee.
        author: Filter by author.
    """
    cwd = _resolve(path)
    args = [
        "gh",
        "issue",
        "list",
        "--state",
        state,
        "--limit",
        str(limit),
        "--json",
        "number,title,author,state,url,labels,assignees,createdAt",
    ]
    if label:
        args += ["--label", label]
    if assignee:
        args += ["--assignee", assignee]
    if author:
        args += ["--author", author]

    rc, stdout, stderr = _run(args, cwd)
    if rc != 0:
        return _err(stderr.strip() or "gh issue list failed")

    try:
        issues = json.loads(stdout)
    except json.JSONDecodeError:
        return _err(f"Failed to parse gh output: {stdout[:200]}")
    return {"issues": issues, "count": len(issues)}


def run() -> None:
    """Run the MCP server."""
    mcp.run()
