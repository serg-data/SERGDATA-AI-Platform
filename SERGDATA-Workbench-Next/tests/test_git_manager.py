import subprocess
from pathlib import Path
import pytest
from workbench.git_manager import GitManager

def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)

def test_init_and_status(tmp_path):
    gm=GitManager(tmp_path)
    assert gm.status()["initialized"] is False
    result=gm.init()
    assert result["initialized"] is True
    assert (tmp_path/".git").is_dir()

def test_stage_commit_and_history(tmp_path):
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    (tmp_path/"hello.txt").write_text("hello", encoding="utf-8")
    gm=GitManager(tmp_path)
    gm.stage(["hello.txt"])
    assert gm.commit("first commit")["ok"] is True
    assert "first commit" in gm.history()

def test_stage_blocks_secret_paths(tmp_path):
    git(tmp_path, "init")
    gm=GitManager(tmp_path)
    (tmp_path/".env").write_text("SECRET=x", encoding="utf-8")
    with pytest.raises(ValueError):
        gm.stage([".env"])

def test_stage_blocks_parent_traversal(tmp_path):
    git(tmp_path, "init")
    gm=GitManager(tmp_path)
    with pytest.raises(ValueError):
        gm.stage(["../outside.txt"])

def test_project_nested_in_parent_repo_is_not_misreported(tmp_path):
    git(tmp_path, "init")
    child=tmp_path/"child"
    child.mkdir()
    gm=GitManager(child)
    assert gm.is_repo() is False

def test_git_doctor_reports_clean_repository(tmp_path):
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    (tmp_path / "tracked.txt").write_text("stable\n", encoding="utf-8")
    git(tmp_path, "add", "tracked.txt")
    git(tmp_path, "commit", "-m", "initial")
    result = GitManager(tmp_path).doctor()
    assert result["ok"] is True
    assert result["issues"] == []


def test_git_doctor_does_not_modify_worktree(tmp_path):
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    (tmp_path / "tracked.txt").write_text("stable\n", encoding="utf-8")
    git(tmp_path, "add", "tracked.txt")
    git(tmp_path, "commit", "-m", "initial")
    before = (tmp_path / "tracked.txt").read_bytes()
    GitManager(tmp_path).doctor()
    assert (tmp_path / "tracked.txt").read_bytes() == before


def configure_identity(root):
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")


def test_unstage_before_first_commit_preserves_working_file(tmp_path):
    git(tmp_path, "init", "-b", "main")
    file_path = tmp_path / "new.txt"
    file_path.write_text("important content\n", encoding="utf-8")
    gm = GitManager(tmp_path)
    gm.stage(["new.txt"])

    result = gm.unstage(["new.txt"])

    assert result["ok"] is True
    assert file_path.read_text(encoding="utf-8") == "important content\n"
    assert git(tmp_path, "status", "--porcelain").stdout.strip() == "?? new.txt"


def test_unstage_after_first_commit_keeps_file_and_moves_change_to_worktree(tmp_path):
    git(tmp_path, "init", "-b", "main")
    configure_identity(tmp_path)
    file_path = tmp_path / "tracked.txt"
    file_path.write_text("before\n", encoding="utf-8")
    git(tmp_path, "add", "tracked.txt")
    git(tmp_path, "commit", "-m", "initial")
    file_path.write_text("after\n", encoding="utf-8")
    gm = GitManager(tmp_path)
    gm.stage(["tracked.txt"])

    gm.unstage(["tracked.txt"])

    assert file_path.read_text(encoding="utf-8") == "after\n"
    assert git(tmp_path, "status", "--porcelain").stdout.strip() == "M tracked.txt"


def test_first_push_sets_upstream_to_origin(tmp_path):
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    remote.mkdir()
    work.mkdir()
    git(remote, "init", "--bare", "-b", "main")
    git(work, "init", "-b", "main")
    configure_identity(work)
    (work / "tracked.txt").write_text("ready\n", encoding="utf-8")
    git(work, "add", "tracked.txt")
    git(work, "commit", "-m", "initial")
    git(work, "remote", "add", "origin", str(remote))

    result = GitManager(work).sync("push")

    assert result["ok"] is True
    upstream = git(work, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    assert upstream.stdout.strip() == "origin/main"
    assert git(remote, "rev-parse", "refs/heads/main").stdout.strip() == git(work, "rev-parse", "HEAD").stdout.strip()


def test_first_push_without_origin_fails_without_changing_commit(tmp_path):
    git(tmp_path, "init", "-b", "main")
    configure_identity(tmp_path)
    (tmp_path / "tracked.txt").write_text("ready\n", encoding="utf-8")
    git(tmp_path, "add", "tracked.txt")
    git(tmp_path, "commit", "-m", "initial")
    before = git(tmp_path, "rev-parse", "HEAD").stdout.strip()

    with pytest.raises(ValueError, match="origin"):
        GitManager(tmp_path).sync("push")

    assert git(tmp_path, "rev-parse", "HEAD").stdout.strip() == before
