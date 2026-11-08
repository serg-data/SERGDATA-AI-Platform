from pathlib import Path
import pytest
from workbench.execution import ExecutionEngine


def test_execution_engine_lists_reads_and_searches_inside_project(tmp_path):
    (tmp_path/'src').mkdir()
    (tmp_path/'src'/'app.py').write_text('VALUE = 42\n', encoding='utf-8')
    engine=ExecutionEngine(tmp_path)
    assert 'src/app.py' in engine.list_files()
    assert 'VALUE = 42' in engine.read_file('src/app.py')
    assert 'src/app.py:1' in engine.search('value')


def test_execution_engine_blocks_traversal_and_secrets(tmp_path):
    outside=tmp_path.parent/'outside-secret.txt'
    outside.write_text('secret',encoding='utf-8')
    engine=ExecutionEngine(tmp_path)
    with pytest.raises(ValueError): engine.safe_path('../outside-secret.txt')
    with pytest.raises(ValueError): engine.safe_path('.env')
    with pytest.raises(ValueError): engine.safe_path('id_rsa.pem')


def test_execution_engine_blocks_symlink_escape(tmp_path):
    outside=tmp_path.parent/'outside-dir'
    outside.mkdir(exist_ok=True)
    link=tmp_path/'escape'
    try: link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError): pytest.skip('Symlinks unavailable')
    engine=ExecutionEngine(tmp_path)
    with pytest.raises(ValueError): engine.safe_path('escape/file.txt')


def test_execution_engine_check_allowlist(tmp_path):
    engine=ExecutionEngine(tmp_path)
    with pytest.raises(ValueError): engine.run_check('format-c-drive')


def test_pending_execution_queue_persists_and_finishes(tmp_path):
    from workbench.db import Store
    store=Store(tmp_path/'workbench.sqlite3')
    with store.conn() as c:
        c.execute("INSERT INTO projects(name,root,created_at) VALUES('p',?,?)",(str(tmp_path),'now'))
        project_id=c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO tasks(project_id,title,created_at,updated_at) VALUES(?,?,?,?)",(project_id,'t','now','now'))
        task_id=c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO branches(task_id,name,created_at,updated_at) VALUES(?,?,?,?)",(task_id,'b','now','now'))
        branch_id=c.execute('SELECT last_insert_rowid()').fetchone()[0]
    eid=store.add_pending_execution(branch_id,'Get-Location')
    assert store.pending_executions(branch_id)[0]['id']==eid
    store.finish_execution(eid,'rejected','declined')
    assert store.pending_executions(branch_id)==[]
    assert store.execution_by_id(eid)['result']=='declined'


def test_pending_execution_context_survives_store_reopen(tmp_path):
    from workbench.db import Store
    path = tmp_path / 'workbench.sqlite3'
    store = Store(path)
    with store.conn() as c:
        c.execute("INSERT INTO projects(name,root,created_at) VALUES('p',?,?)", (str(tmp_path), 'now'))
        pid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO tasks(project_id,title,created_at,updated_at) VALUES(?,?,?,?)", (pid, 't', 'now', 'now'))
        tid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO branches(task_id,name,created_at,updated_at) VALUES(?,?,?,?)", (tid, 'b', 'now', 'now'))
        bid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
    eid = store.add_pending_execution(bid, '__SERGDATA_EXEC_V1__{}')
    snapshot = [
        {'role': 'user', 'content': 'диагностика'},
        {'role': 'assistant', 'content': '', 'tool_calls': [
            {'id': 'call_123', 'type': 'function', 'function': {'name': 'ssh_run_command', 'arguments': '{}'}}
        ]},
    ]
    store.set_execution_context(eid, snapshot, 'call_123', 'local-model', 42)
    reopened = Store(path).execution_by_id(eid)
    import json
    saved_snapshot = json.loads(reopened['context_json'])
    assert saved_snapshot[:-1] == snapshot
    assert saved_snapshot[-1]['tool_call_id'] == 'call_123'
    assert saved_snapshot[-1]['content'] == Store.PENDING_TOOL_RESULT
    assert reopened['tool_call_id'] == 'call_123'
    assert reopened['model'] == 'local-model'
    assert reopened['user_message_id'] == 42
    assert reopened['resume_status'] == 'waiting'


def test_execution_context_has_size_limit(tmp_path):
    from workbench.db import Store
    store = Store(tmp_path / 'workbench.sqlite3')
    with store.conn() as c:
        c.execute("INSERT INTO projects(name,root,created_at) VALUES('p',?,?)", (str(tmp_path), 'now'))
        pid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO tasks(project_id,title,created_at,updated_at) VALUES(?,?,?,?)", (pid, 't', 'now', 'now'))
        tid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO branches(task_id,name,created_at,updated_at) VALUES(?,?,?,?)", (tid, 'b', 'now', 'now'))
        bid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
    eid = store.add_pending_execution(bid, 'cmd')
    import pytest
    with pytest.raises(ValueError, match='8 МБ'):
        store.set_execution_context(eid, [{'role': 'user', 'content': 'x' * (8 * 1024 * 1024)}], 'call', 'model', 1)
