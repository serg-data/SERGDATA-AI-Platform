import json
from pathlib import Path

from workbench.db import Store
from workbench.tools import ProjectTools


def test_message_metadata_round_trips_for_tool_activity(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('p', str(tmp_path))
    _, bid = store.create_task(pid, 't')
    event = {
        'version': 1,
        'name': 'read_project_file',
        'arguments': {'path': 'src/app.py'},
        'status': 'completed',
        'duration_ms': 12,
        'result_preview': 'VALUE = 42',
    }
    store.add_message(bid, 'tool', 'VALUE = 42', metadata=event)
    message = store.messages(bid)[0]
    assert message['content'] == 'VALUE = 42'
    assert message['metadata'] == event


def test_old_message_rows_receive_empty_metadata(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('p', str(tmp_path))
    _, bid = store.create_task(pid, 't')
    with store.conn() as conn:
        conn.execute(
            "INSERT INTO messages(branch_id,role,content,created_at) VALUES(?,?,?,?)",
            (bid, 'tool', 'old_tool:\nold result', store.now()),
        )
    assert store.messages(bid)[0]['metadata'] == {}


def test_project_listing_is_recursive_and_hides_backups_by_default(tmp_path):
    (tmp_path / 'backend' / 'api').mkdir(parents=True)
    (tmp_path / 'backend' / 'api' / 'main.py').write_text('VALUE = 1', encoding='utf-8')
    (tmp_path / 'README.md').write_text('# project', encoding='utf-8')
    (tmp_path / 'README.md.workbench.bak').write_text('# old', encoding='utf-8')
    tools = ProjectTools(tmp_path)
    listing = tools.listing(max_depth=4)
    assert 'backend/' in listing
    assert 'backend/api/' in listing
    assert 'backend/api/main.py' in listing
    assert 'README.md.workbench.bak' not in listing
    assert 'README.md.workbench.bak' in tools.listing(include_backups=True)


def test_project_tools_do_not_create_missing_project_roots(tmp_path):
    missing = tmp_path / 'does-not-exist'
    try:
        ProjectTools(missing)
    except ValueError as exc:
        assert 'Корень проекта не существует' in str(exc)
    else:
        raise AssertionError('Missing project root must be rejected')
    assert not missing.exists()


def test_search_and_file_listing_do_not_expose_secrets_or_backup_files(tmp_path):
    from workbench.execution import ExecutionEngine
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src' / 'safe.py').write_text('PUBLIC_MARKER = 1', encoding='utf-8')
    (tmp_path / '.env').write_text('PRIVATE_MARKER=secret', encoding='utf-8')
    (tmp_path / 'src' / 'old.py.workbench.bak').write_text('PRIVATE_MARKER=old', encoding='utf-8')
    engine = ExecutionEngine(tmp_path)
    listing = engine.list_files()
    search = engine.search('PRIVATE_MARKER')
    assert 'safe.py' in listing
    assert '.env' not in listing
    assert 'old.py.workbench.bak' not in listing
    assert 'PRIVATE_MARKER' not in search


def test_store_migrates_legacy_messages_table_with_metadata_column(tmp_path):
    import sqlite3
    db_path = tmp_path / 'legacy.sqlite3'
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE messages(id INTEGER PRIMARY KEY AUTOINCREMENT,branch_id INTEGER NOT NULL,role TEXT NOT NULL,content TEXT NOT NULL,created_at TEXT NOT NULL,prompt_tokens INTEGER DEFAULT 0,completion_tokens INTEGER DEFAULT 0)")
    conn.commit(); conn.close()
    store = Store(db_path)
    with store.conn() as conn:
        columns = {row[1] for row in conn.execute('PRAGMA table_info(messages)').fetchall()}
    assert 'metadata' in columns


def test_project_read_reports_complete_file_metadata_and_next_chunk(tmp_path):
    source = tmp_path / 'large.sh'
    source.write_text('\n'.join(f'echo line-{i}' for i in range(1, 1005)), encoding='utf-8')
    tools = ProjectTools(tmp_path)

    first = tools.read('large.sh')
    assert 'Всего строк: 1004' in first
    assert 'СТАТУС ЧТЕНИЯ: INCOMPLETE' in first
    assert 'NEXT_START_LINE=181' in first
    assert '180: echo line-180' in first
    assert len(first) < 7000

    second = tools.read('large.sh', start_line=181)
    assert '181: echo line-181' in second
    assert 'NEXT_START_LINE=361' in second
    assert len(second) < 7000

    last = tools.read('large.sh', start_line=901)
    assert '1004: echo line-1004' in last
    assert 'СТАТУС ФРАГМЕНТА: END_OF_FILE' in last
    assert 'NEXT_START_LINE' not in last


def test_project_read_respects_requested_end_but_caps_chunk(tmp_path):
    source = tmp_path / 'file.txt'
    source.write_text('\n'.join(f'line-{i}' for i in range(1, 501)), encoding='utf-8')
    result = ProjectTools(tmp_path).read('file.txt', start_line=220, end_line=400)
    assert '220: line-220' in result
    assert '399: line-399' in result
    assert '400: line-400' not in result
    assert 'NEXT_START_LINE=400' in result
