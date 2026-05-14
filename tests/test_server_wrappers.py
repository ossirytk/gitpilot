"""Wrapper behavior tests for gitpilot server tools."""

from __future__ import annotations

import json

from gitpilot import server


def test_git_wrappers_with_mocked_runner(monkeypatch) -> None:
    sep = "\x1f"
    status_out = (
        "# branch.head main\n"
        "# branch.upstream origin/main\n"
        "# branch.ab +2 -1\n"
        "1 M. N... 100644 100644 100644 a b src/file.py\n"
        "2 R. N... 100644 100644 100644 a b R100 src/new.py\tsrc/old.py\n"
        "? untracked.txt\n"
        "u UU N... 100644 100644 100644 100644 a b c conflicted.txt\n"
    )
    show_meta = f"abcdef123456{sep}Test User{sep}t@example.com{sep}2026-01-01T00:00:00+00:00{sep}Subject{sep}Body"

    responses: dict[tuple[str, ...], tuple[int, str, str]] = {
        ("git", "status", "--porcelain=v2", "--branch"): (0, status_out, ""),
        ("git", "diff", "--staged", "--", "src/file.py"): (0, "diff --git a/src/file.py b/src/file.py\n+line\n", ""),
        ("git", "diff", "--staged", "--stat", "--", "src/file.py"): (
            0,
            " src/file.py | 1 +\n 1 file changed, 1 insertion(+)\n",
            "",
        ),
        ("git", "add", "-A"): (0, "", ""),
        ("git", "commit", "-m", "commit msg"): (0, "[main abc1234] commit msg\n 1 file changed\n", ""),
        ("git", "show", "--stat", "--format=", "abc1234"): (0, " src/file.py | 1 +\n", ""),
        ("git", "show", "--no-patch", "--pretty=tformat:%H\x1f%an\x1f%ae\x1f%aI\x1f%s\x1f%b", "HEAD"): (
            0,
            show_meta,
            "",
        ),
        ("git", "show", "--stat", "--patch", "--format=", "HEAD"): (
            0,
            " src/file.py | 1 +\ndiff --git a/src/file.py b/src/file.py\n+line\n",
            "",
        ),
        ("git", "checkout", "-b", "feature"): (0, "", ""),
        ("git", "checkout", "main"): (0, "", ""),
        ("git", "branch", "-d", "feature"): (0, "", ""),
        ("git", "branch", "--format=%(refname:short)\t%(HEAD)\t%(symref)", "-a"): (0, "main\t*\t\nfeature\t\t\n", ""),
        ("git", "merge", "--no-ff", "-m", "merge msg", "main"): (0, "Already up to date.\n", ""),
        ("git", "stash", "push", "-m", "save"): (0, "Saved working directory and index state\n", ""),
        ("git", "stash", "pop"): (0, "Dropped refs/stash@{0}\n", ""),
        ("git", "stash", "list"): (0, "stash@{0}: WIP on main: abc1234 test\n", ""),
        ("git", "reset", "HEAD", "--", "src/file.py"): (0, "", ""),
        ("git", "tag", "-a", "v1.0.0", "-m", "annotated"): (0, "", ""),
        ("git", "tag", "-d", "v0.9.0"): (0, "", ""),
        ("git", "tag", "--sort=-creatordate"): (0, "v1.0.0\nv0.9.0\n", ""),
        ("git", "remote", "add", "origin2", "https://example.com/other.git"): (0, "", ""),
        ("git", "remote", "remove", "origin2"): (0, "", ""),
        ("git", "remote", "-v"): (
            0,
            "origin\thttps://example.com/repo.git (fetch)\norigin\thttps://example.com/repo.git (push)\n",
            "",
        ),
        ("git", "fetch", "origin", "--prune"): (0, "Fetched\n", ""),
        ("git", "pull", "--rebase", "origin", "main"): (0, "Pulled\n", ""),
        ("git", "push", "--force-with-lease", "-u", "--tags", "origin", "main"): (0, "Pushed\n", ""),
    }

    def fake_run(args: list[str], cwd: str) -> tuple[int, str, str]:
        del cwd
        return responses.get(tuple(args), (0, "", ""))

    monkeypatch.setattr(server, "_run", fake_run)

    status = server.git_status()
    assert status["branch"] == "main"
    assert status["upstream"] == "origin/main"
    assert status["ahead"] == 2
    assert status["behind"] == 1
    assert status["untracked"] == ["untracked.txt"]
    assert status["unmerged"] == ["conflicted.txt"]
    assert status["clean"] is False

    diff = server.git_diff(staged=True, file="src/file.py")
    assert diff["staged"] is True
    assert "diff --git" in diff["diff"]
    assert diff["stats"]

    commit = server.git_commit("commit msg", add_all=True)
    assert commit["sha"] == "abc1234"

    shown = server.git_show("HEAD")
    assert shown["subject"] == "Subject"
    assert "diff --git" in shown["diff"]

    branches = server.git_branch(create="feature", switch="main", delete="feature", remote=True)
    assert branches["current"] == "main"
    assert "feature" in branches["branches"]

    assert server.git_merge("main", no_ff=True, message="merge msg")["merged"] == "main"
    assert server.git_stash(message="save")["action"] == "push"
    assert server.git_stash(pop=True)["action"] == "pop"
    assert "error" in server.git_reset(mode="broken")
    assert server.git_reset(files=["src/file.py"])["mode"] == "unstage"
    assert server.git_tag(create="v1.0.0", delete="v0.9.0", message="annotated")["tags"] == ["v1.0.0", "v0.9.0"]
    assert (
        "origin"
        in server.git_remote(add_name="origin2", add_url="https://example.com/other.git", remove="origin2")["remotes"]
    )
    assert server.git_fetch(prune=True)["remote"] == "origin"
    assert server.git_pull(branch="main", rebase=True)["branch"] == "main"
    assert server.git_push(branch="main", force=True, set_upstream=True, tags=True)["branch"] == "main"


def test_gh_wrappers_with_mocked_runner(monkeypatch) -> None:
    responses: dict[tuple[str, ...], tuple[int, str, str]] = {
        ("gh", "pr", "create", "--title", "A PR", "--body", "Body", "--base", "main", "--draft"): (
            0,
            "https://github.com/org/repo/pull/42\n",
            "",
        ),
        (
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--limit",
            "10",
            "--json",
            "number,title,author,state,url,baseRefName,headRefName,isDraft,labels,createdAt",
            "--base",
            "main",
            "--author",
            "me",
            "--label",
            "bug",
        ): (0, json.dumps([{"number": 42, "title": "A PR"}]), ""),
        (
            "gh",
            "pr",
            "view",
            "42",
            "--json",
            "number,title,author,state,url,baseRefName,headRefName,isDraft,labels,body,reviews,commits,createdAt,mergedAt,closedAt",
        ): (0, json.dumps({"number": 42, "title": "A PR"}), ""),
        (
            "gh",
            "issue",
            "create",
            "--title",
            "Issue",
            "--body",
            "Body",
            "--label",
            "bug",
            "--label",
            "help",
            "--assignee",
            "me",
        ): (0, "https://github.com/org/repo/issues/7\n", ""),
        (
            "gh",
            "issue",
            "list",
            "--state",
            "open",
            "--limit",
            "10",
            "--json",
            "number,title,author,state,url,labels,assignees,createdAt",
            "--label",
            "bug",
            "--assignee",
            "me",
            "--author",
            "me",
        ): (0, json.dumps([{"number": 7, "title": "An issue"}]), ""),
    }

    def fake_run(args: list[str], cwd: str) -> tuple[int, str, str]:
        del cwd
        return responses.get(tuple(args), (0, "", ""))

    monkeypatch.setattr(server, "_run", fake_run)

    assert server.gh_pr_create("A PR", body="Body", base="main", draft=True)["number"] == "42"
    assert server.gh_pr_list(state="open", limit=10, base="main", author="me", label="bug")["count"] == 1
    assert server.gh_pr_view("42")["number"] == 42
    assert server.gh_issue_create("Issue", body="Body", label="bug,help", assignee="me")["number"] == "7"
    assert server.gh_issue_list(state="open", limit=10, label="bug", assignee="me", author="me")["count"] == 1
