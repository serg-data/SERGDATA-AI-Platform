from pathlib import Path
import pytest
from workbench.release_manager import ReleaseManager


def make_pair(tmp_path):
    source = tmp_path / "next"
    target = tmp_path / "stable"
    source.mkdir(); target.mkdir()
    return source, target


def test_compare_classifies_changes_and_excludes_private_files(tmp_path):
    source, target = make_pair(tmp_path)
    (source / "new.py").write_text("new", encoding="utf-8")
    (source / "same.py").write_text("same", encoding="utf-8")
    (target / "same.py").write_text("old", encoding="utf-8")
    (target / "stable-only.py").write_text("keep", encoding="utf-8")
    (source / ".env").write_text("SECRET=1", encoding="utf-8")
    result = ReleaseManager(source, target).compare()
    assert result["counts"] == {"added": 1, "modified": 1, "deleted": 1}
    assert {x["path"] for x in result["files"]} == {"new.py", "same.py", "stable-only.py"}
    assert ".env" not in {x["path"] for x in result["files"]}


def test_prepare_does_not_modify_target_and_apply_has_backup(tmp_path):
    source, target = make_pair(tmp_path)
    (source / "app.py").write_text("new version", encoding="utf-8")
    (target / "app.py").write_text("stable version", encoding="utf-8")
    manager = ReleaseManager(source, target)
    plan = manager.prepare(["app.py"])
    assert (target / "app.py").read_text(encoding="utf-8") == "stable version"
    applied = manager.apply(plan["plan_id"])
    assert (target / "app.py").read_text(encoding="utf-8") == "new version"
    assert (Path(applied["backup"]) / "app.py").read_text(encoding="utf-8") == "stable version"


def test_apply_rejects_target_changed_after_prepare(tmp_path):
    source, target = make_pair(tmp_path)
    (source / "app.py").write_text("new", encoding="utf-8")
    (target / "app.py").write_text("old", encoding="utf-8")
    manager = ReleaseManager(source, target)
    plan = manager.prepare(["app.py"])
    (target / "app.py").write_text("changed after plan", encoding="utf-8")
    with pytest.raises(ValueError, match="изменился после подготовки"):
        manager.apply(plan["plan_id"])
    assert (target / "app.py").read_text(encoding="utf-8") == "changed after plan"


def test_apply_rejects_symlink_parent_escape_after_prepare(tmp_path):
    source, target = make_pair(tmp_path)
    (source / "dir").mkdir()
    (source / "dir" / "app.py").write_text("new", encoding="utf-8")
    (target / "dir").mkdir()
    (target / "dir" / "app.py").write_text("old", encoding="utf-8")
    manager = ReleaseManager(source, target)
    plan = manager.prepare(["dir/app.py"])
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "app.py").write_text("do not touch", encoding="utf-8")
    (source / "dir" / "app.py").unlink()
    (source / "dir").rmdir()
    (source / "dir").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="Символическая ссылка"):
        manager.apply(plan["plan_id"])
    assert (outside / "app.py").read_text(encoding="utf-8") == "do not touch"
    assert (target / "dir" / "app.py").read_text(encoding="utf-8") == "old"


def test_prepare_tracks_each_selected_path_independently(tmp_path):
    source, target = make_pair(tmp_path)
    (source / "one.py").write_text("new one", encoding="utf-8")
    (source / "two.py").write_text("new two", encoding="utf-8")
    (target / "one.py").write_text("old one", encoding="utf-8")
    (target / "two.py").write_text("old two", encoding="utf-8")

    manager = ReleaseManager(source, target)
    plan = manager.prepare(["one.py", "two.py"])

    assert [item["path"] for item in plan["files"]] == ["one.py", "two.py"]
    applied = manager.apply(plan["plan_id"])
    assert {Path(item).as_posix() for item in applied["applied"]} == {"one.py", "two.py"}
    assert (target / "one.py").read_text(encoding="utf-8") == "new one"
    assert (target / "two.py").read_text(encoding="utf-8") == "new two"
    assert (Path(applied["backup"]) / "one.py").read_text(encoding="utf-8") == "old one"
    assert (Path(applied["backup"]) / "two.py").read_text(encoding="utf-8") == "old two"


def test_compare_ignores_accidental_console_transcript_files(tmp_path):
    source, target = make_pair(tmp_path)
    (source / "real.py").write_text("source", encoding="utf-8")
    (source / "t_cache __pycache__ .workbench").write_text("terminal help", encoding="utf-8")
    (source / "t \uf022`n=== GIT IGNORE CHECK ===\uf022").write_text("git config output", encoding="utf-8")
    result = ReleaseManager(source, target).compare()
    assert {item["path"] for item in result["files"]} == {"real.py"}
