"""Git workflow MCP server wrapping git and gh CLI."""
from __future__ import annotations

from fastmcp import FastMCP

mcp: FastMCP = FastMCP(
    name="gitpilot",
    instructions=(
        "gitpilot is a Git workflow assistant. "
        "Use `git_status` to inspect the working tree. "
        "Use `git_diff` to show changes (staged or unstaged). "
        "Use `git_commit` to stage and commit changes. "
        "Use `git_branch` to list, create, or switch branches. "
        "Use `git_stash` to stash or pop uncommitted changes. "
        "Use `git_log` to view commit history. "
        "Use `gh_pr_create` to open a pull request via the gh CLI."
    ),
)


@mcp.tool()
def git_status(path: str = ".") -> dict[str, object]:
    """Return the working-tree status of a repository.

    Args:
        path: Path to the repository root. Defaults to the current directory.

    Returns:
        A dict with keys ``branch``, ``staged``, ``unstaged``, and ``untracked``.
    """
    raise NotImplementedError


@mcp.tool()
def git_diff(path: str = ".", staged: bool = False) -> dict[str, object]:
    """Show changes in the working tree or index.

    Args:
        path: Path to the repository root.
        staged: When True, show staged (index) changes instead of unstaged.

    Returns:
        A dict with keys ``diff`` (unified diff text) and ``stats``.
    """
    raise NotImplementedError


@mcp.tool()
def git_commit(message: str, path: str = ".", add_all: bool = False) -> dict[str, object]:
    """Stage files and create a commit.

    Args:
        message: The commit message.
        path: Path to the repository root.
        add_all: When True, run ``git add -A`` before committing.

    Returns:
        A dict with keys ``sha``, ``message``, and ``files_changed``.
    """
    raise NotImplementedError


@mcp.tool()
def git_branch(
    path: str = ".",
    create: str | None = None,
    switch: str | None = None,
) -> dict[str, object]:
    """List, create, or switch Git branches.

    Args:
        path: Path to the repository root.
        create: Name of a new branch to create (and switch to).
        switch: Name of an existing branch to switch to.

    Returns:
        A dict with keys ``current`` and ``branches``.
    """
    raise NotImplementedError


@mcp.tool()
def git_stash(path: str = ".", pop: bool = False, message: str = "") -> dict[str, object]:
    """Stash or restore uncommitted changes.

    Args:
        path: Path to the repository root.
        pop: When True, pop the most recent stash instead of pushing.
        message: Optional stash description (used when pushing).

    Returns:
        A dict with keys ``action`` and ``stash_list``.
    """
    raise NotImplementedError


@mcp.tool()
def git_log(path: str = ".", limit: int = 20, oneline: bool = True) -> dict[str, object]:
    """Return recent commit history.

    Args:
        path: Path to the repository root.
        limit: Maximum number of commits to return.
        oneline: When True, return abbreviated one-line entries.

    Returns:
        A dict with key ``commits`` containing a list of commit records.
    """
    raise NotImplementedError


@mcp.tool()
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

    Returns:
        A dict with keys ``url`` and ``number``.
    """
    raise NotImplementedError


def run() -> None:
    """Run the MCP server."""
    mcp.run()
