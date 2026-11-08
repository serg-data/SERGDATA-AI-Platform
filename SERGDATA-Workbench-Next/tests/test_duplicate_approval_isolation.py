"""Regression: duplicate approval must not terminate the first running job."""
import ast
from pathlib import Path
from workbench.db import Store


def test_duplicate_claim_preserves_running_execution(tmp_path):
    store = Store(tmp_path / 'test.sqlite3')
    with store.conn() as c:
        c.execute("INSERT INTO projects(name,root,created_at) VALUES('p',?,?)", (str(tmp_path), 'now'))
        pid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO tasks(project_id,title,created_at,updated_at) VALUES(?,?,?,?)", (pid, 't', 'now', 'now'))
        tid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO branches(task_id,name,created_at,updated_at) VALUES(?,?,?,?)", (tid, 'b', 'now', 'now'))
        bid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
    eid = store.add_pending_execution(bid, 'Write-Output test')
    assert store.claim_execution_approval(eid)
    assert not store.claim_execution_approval(eid)
    assert store.execution_by_id(eid)['status'] == 'running'


def test_approve_http_conflict_does_not_enter_failure_handler():
    source = (Path(__file__).resolve().parents[1] / 'main.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    endpoint = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'approve_execution')
    outer_try = next(n for n in endpoint.body if isinstance(n, ast.Try))
    assert len(outer_try.handlers) >= 2
    first, second = outer_try.handlers[:2]
    assert isinstance(first.type, ast.Name) and first.type.id == 'HTTPException'
    assert len(first.body) == 1 and isinstance(first.body[0], ast.Raise) and first.body[0].exc is None
    assert isinstance(second.type, ast.Name) and second.type.id == 'Exception'
    assert 'store.finish_execution' not in ast.get_source_segment(source, first)
    assert 'run_tracked_agent_task' not in ast.get_source_segment(source, first)
