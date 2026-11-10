from workbench.db import Store


def make_store(tmp_path):
    store = Store(tmp_path / "workbench.sqlite3")
    now = store.now()
    with store.conn() as c:
        project_id = c.execute(
            "INSERT INTO projects(name,root,created_at) VALUES(?,?,?)",
            ("Test project", str(tmp_path / "project"), now),
        ).lastrowid
        task_id = c.execute(
            "INSERT INTO tasks(project_id,title,status,summary,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            (project_id, "Checkpoint task", "active", "", now, now),
        ).lastrowid
        branch_id = c.execute(
            "INSERT INTO branches(task_id,name,created_at,updated_at) VALUES(?,?,?,?)",
            (task_id, "main", now, now),
        ).lastrowid
    return store, branch_id


def test_checkpoint_versions_are_preserved_and_latest_is_resumable(tmp_path):
    store, bid = make_store(tmp_path)
    source_id = store.add_message(bid, "user", "Проверь проект")
    first = store.save_execution_checkpoint(
        bid,
        {"version": 1, "summary": "Первый этап", "next_step": "Проверить тесты"},
        status="paused", reason="tool_event", source_message_id=source_id,
    )
    second = store.save_execution_checkpoint(
        bid,
        {"version": 1, "summary": "Второй этап", "next_step": "Проверить diff"},
        status="paused", reason="user_cancel", source_message_id=source_id,
    )
    assert second["sequence"] == first["sequence"] + 1
    latest = store.get_latest_execution_checkpoint(bid)
    assert latest["id"] == second["id"]
    assert latest["payload"]["next_step"] == "Проверить diff"
    with store.conn() as c:
        rows = c.execute(
            "SELECT id,status FROM execution_checkpoints WHERE branch_id=? ORDER BY id", (bid,)
        ).fetchall()
    assert [(r["id"], r["status"]) for r in rows] == [
        (first["id"], "superseded"), (second["id"], "paused")
    ]


def test_completed_checkpoint_is_not_resumable(tmp_path):
    store, bid = make_store(tmp_path)
    item = store.save_execution_checkpoint(
        bid, {"version": 1, "summary": "Готово", "next_step": "Нет"},
        status="paused", reason="model_checkpoint",
    )
    assert store.transition_execution_checkpoint(item["id"], "completed") is True
    assert store.get_latest_execution_checkpoint(bid, resumable_only=True) is None
    assert store.get_latest_execution_checkpoint(bid, resumable_only=False)["status"] == "completed"


def test_checkpoint_does_not_change_branch_memory_cursor(tmp_path):
    store, bid = make_store(tmp_path)
    with store.conn() as c:
        c.execute(
            "INSERT INTO branch_memory(branch_id,summary,through_message_id,updated_at) VALUES(?,?,?,?)",
            (bid, "Existing memory", 17, store.now()),
        )
    store.save_execution_checkpoint(
        bid, {"version": 1, "summary": "Paused", "next_step": "Continue"},
        status="paused", reason="user_cancel",
    )
    memory = store.get_memory(bid)
    assert memory["through_message_id"] == 17
    assert memory["summary"] == "Existing memory"
