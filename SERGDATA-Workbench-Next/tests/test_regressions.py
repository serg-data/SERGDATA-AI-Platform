from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
from workbench.db import Store


def test_legacy_import_is_not_replayed_after_user_deletes_imported_task():
    with TemporaryDirectory() as tmp:
        root=Path(tmp)
        legacy=root/'legacy.sqlite3'
        c=sqlite3.connect(legacy)
        c.executescript("""
        CREATE TABLE tasks(id INTEGER PRIMARY KEY,title TEXT,status TEXT,summary TEXT,created_at TEXT,updated_at TEXT);
        CREATE TABLE events(id INTEGER PRIMARY KEY,task_id INTEGER,kind TEXT,payload TEXT,created_at TEXT);
        INSERT INTO tasks VALUES(1,'Imported task','active','', '2020-01-01','2020-01-01');
        """)
        c.commit(); c.close()
        store=Store(root/'main.sqlite3',legacy)
        imported=[x for x in store.tasks() if x['title']=='Imported task']
        assert len(imported)==1
        store.delete_task(imported[0]['id'])
        # Simulate another application startup against the same DB.
        store2=Store(root/'main.sqlite3',legacy)
        assert not [x for x in store2.tasks() if x['title']=='Imported task']


def test_delete_parent_branch_removes_descendants_and_messages():
    with TemporaryDirectory() as tmp:
        root=Path(tmp); store=Store(root/'db.sqlite3')
        p=store.ensure_project('P',str(root))
        tid,b1=store.create_task(p['id'],'T')
        store.add_message(b1,'user','hello')
        b2=store.create_branch(b1,'child')
        b3=store.create_branch(b2,'grandchild')
        store.add_message(b3,'user','descendant')
        # create a sibling so deleting the tree is allowed
        store.create_branch(b1,'sibling')
        store.delete_branch(b2)
        assert [b['name'] for b in store.branches(tid)]==['Основная','sibling']
        assert store.messages(b1)[0]['content']=='hello'


def test_delete_task_with_nested_branches_succeeds():
    with TemporaryDirectory() as tmp:
        root=Path(tmp); store=Store(root/'db.sqlite3')
        p=store.ensure_project('P',str(root))
        tid,b1=store.create_task(p['id'],'T')
        b2=store.create_branch(b1,'child')
        store.create_branch(b2,'grandchild')
        store.delete_task(tid)
        assert store.tasks(p['id'])==[]


def test_pending_change_lookup_prevents_duplicate_path_queue(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('p', str(tmp_path))
    tid, bid = store.create_task(pid, 'task')
    pending_id = store.add_pending(bid, 'README.md', '# Draft')
    found = store.pending_for_path(bid, 'README.md')
    assert found['id'] == pending_id
    assert found['content'] == '# Draft'
    assert store.pending_for_path(bid, 'pyproject.toml') is None
