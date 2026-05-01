"""Tests for git_log tool."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from gitpilot.server import git_log


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository with two commits."""
    env = {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@example.com",
           "HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}

    def run(*args: str) -> None:
        subprocess.run(list(args), cwd=tmp_path, env=env, check=True, capture_output=True)

    run("git", "init")
    run("git", "config", "user.email", "t@example.com")
    run("git", "config", "user.name", "Test")

    (tmp_path / "README.md").write_text("hello\n")
    run("git", "add", "README.md")
    run("git", "commit", "-m", "first commit")

    (tmp_path / "main.py").write_text("print('hi')\n")
    run("git", "add", "main.py")
    run("git", "commit", "-m", "add main.py")

    return tmp_path


def test_git_log_returns_commits(git_repo: Path) -> None:
    result = git_log(path=str(git_repo))
    assert "commits" in result
    commits = result["commits"]
    assert len(commits) == 2
    assert commits[0]["subject"] == "add main.py"
    assert commits[1]["subject"] == "first commit"


def test_git_log_sha_format(git_repo: Path) -> None:
    result = git_log(path=str(git_repo))
    commit = result["commits"][0]
    assert len(commit["sha"]) == 12
    assert len(commit["sha_full"]) == 40


def test_git_log_truncated_flag(git_repo: Path) -> None:
    result = git_log(path=str(git_repo), limit=1)
    assert result["truncated"] is True
    assert len(result["commits"]) == 1


def test_git_log_not_truncated_when_within_limit(git_repo: Path) -> None:
    result = git_log(path=str(git_repo), limit=10)
    assert result["truncated"] is False
    assert result["count"] == 2


def test_git_log_include_diff_stat(git_repo: Path) -> None:
    result = git_log(path=str(git_repo), include_diff_stat=True)
    commits = result["commits"]
    # Most recent commit added main.py
    assert "files_changed" in commits[0]
    assert "main.py" in commits[0]["files_changed"]
    # First commit added README.md
    assert "README.md" in commits[1]["files_changed"]


def test_git_log_file_filter(git_repo: Path) -> None:
    result = git_log(path=str(git_repo), file="main.py")
    assert result["count"] == 1
    assert result["commits"][0]["subject"] == "add main.py"


def test_git_log_invalid_repo(tmp_path: Path) -> None:
    result = git_log(path=str(tmp_path))
    assert "error" in result
