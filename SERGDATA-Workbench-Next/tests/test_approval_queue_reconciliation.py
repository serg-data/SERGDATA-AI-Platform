from pathlib import Path

from workbench.db import Store

ROOT = Path(__file__).resolve().parents[1]


def _branch(store, tmp_path):
    with store.conn() as c:
        c.execute("INSERT INTO projects(name,root,created_at) VALUES('p',?,?)", (str(tmp_path), 'now'))
        project_id = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO tasks(project_id,title,created_at,updated_at) VALUES(?,?,?,?)",
                  (project_id, 't', 'now', 'now'))
        task_id = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO branches(task_id,name,created_at,updated_at) VALUES(?,?,?,?)",
                  (task_id, 'main', 'now', 'now'))
        return c.execute('SELECT last_insert_rowid()').fetchone()[0]


def test_execution_approval_is_atomically_recorded_and_cannot_be_claimed_twice(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    branch_id = _branch(store, tmp_path)
    execution_id = store.add_pending_execution(branch_id, 'Get-Date')

    assert store.claim_execution_approval(execution_id, 'workbench_ui') is True
    row = store.execution_by_id(execution_id)
    assert row['status'] == 'running'
    assert row['approved_at']
    assert row['approved_via'] == 'workbench_ui'
    assert store.claim_execution_approval(execution_id, 'workbench_ui') is False
    assert store.reject_execution_by_user(execution_id, 'workbench_ui') is False


def test_rejection_is_atomically_recorded_and_cannot_be_applied_after_approval(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    branch_id = _branch(store, tmp_path)
    execution_id = store.add_pending_execution(branch_id, 'Get-Date')
    assert store.reject_execution_by_user(execution_id, 'workbench_ui') is True
    row = store.execution_by_id(execution_id)
    assert row['status'] == 'rejected'
    assert row['rejected_at']
    assert row['rejected_via'] == 'workbench_ui'
    assert store.claim_execution_approval(execution_id, 'workbench_ui') is False


def test_pending_queue_and_approval_button_are_refreshed_during_chat_poll():
    source = (ROOT / 'static' / 'app.js').read_text(encoding='utf-8')
    poll_start = source.index('async function pollChatActivity(branch){')
    poll_end = source.index('\nfunction setChatUiActive', poll_start)
    poll_body = source[poll_start:poll_end]
    assert 'await refreshExecutionQueueState(branch)' in poll_body
    assert 'function refreshExecutionQueueState(branch=activeBranch)' in source
    assert 'renderChatComputeButton(false)' in source[source.index('async function refreshExecutionQueueState'):source.index('async function loadExecutionQueue')]


def test_chat_status_reconciles_waiting_state_with_persistent_approval_queue():
    source = (ROOT / 'main.py').read_text(encoding='utf-8')
    start = source.index("@app.get('/api/chat/status')")
    end = source.index("@app.post('/api/chat/cancel')", start)
    block = source[start:end]
    assert 'store.pending_executions(branch_id)' in block
    assert "set_chat_activity(branch_id,'idle','')" in block
    assert "'waiting_approval'" in block
