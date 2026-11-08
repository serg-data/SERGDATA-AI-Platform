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
