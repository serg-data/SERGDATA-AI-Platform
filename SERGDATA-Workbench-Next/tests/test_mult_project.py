from pathlib import Path
from tempfile import TemporaryDirectory
from workbench.db import Store
from workbench.tools import ProjectTools


def test_tasks_are_isolated_by_project_and_branch_resolves_project():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        p1 = root / "one"; p1.mkdir()
        p2 = root / "two"; p2.mkdir()
        store = Store(root / "db.sqlite3")
        a = store.ensure_project("One", str(p1))
        b = store.create_project("Two", str(p2))
        task1, branch1 = store.create_task(a["id"], "Task A")
        task2, branch2 = store.create_task(b, "Task B")
        assert [x["title"] for x in store.tasks(a["id"])] == ["Task A"]
        assert [x["title"] for x in store.tasks(b)] == ["Task B"]
        assert store.project_for_branch(branch1)["root"] == str(p1)
        assert store.project_for_branch(branch2)["root"] == str(p2)
        store.save_task_memory(task1, "Task-specific decisions")
        assert store.task_for_branch(branch1)["summary"] == "Task-specific decisions"


def test_project_tools_reject_parent_traversal():
    with TemporaryDirectory() as tmp:
        root = Path(tmp) / "project"; root.mkdir()
        outside = Path(tmp) / "secret.txt"; outside.write_text("secret")
        tools = ProjectTools(root)
        try:
            tools.read("../secret.txt")
        except ValueError as exc:
            assert "Запрещён выход" in str(exc)
        else:
            raise AssertionError("Path traversal was not rejected")


def test_project_memory_is_persistent_and_separate():
    with TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / "db.sqlite3")
        project = store.ensure_project("Project", tmp)
        store.save_project_memory(project["id"], "Архитектура проекта")
        assert store.get_project_memory(project["id"])["summary"] == "Архитектура проекта"
