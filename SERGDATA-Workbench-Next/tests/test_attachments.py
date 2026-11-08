import io
import zipfile
from pathlib import Path

from workbench.db import Store
from workbench.attachments import extract_document


def test_attachment_metadata_chunks_and_message_link(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('p', str(tmp_path))
    tid, bid = store.create_task(pid, 'task')
    aid = store.add_attachment(
        project_id=pid, task_id=tid, branch_id=bid, original_name='notes.md',
        stored_name='abc.md', media_type='text/markdown', kind='text', size=5,
        sha256='hash', note='indexed', chunks=[{'source_path':'notes.md','chunk_index':0,'content':'important alpha'}]
    )
    mid = store.add_message(bid, 'user', 'check this')
    store.link_message_attachments(mid, [aid])
    messages = store.messages(bid)
    assert messages[-1]['attachments'][0]['original_name'] == 'notes.md'
    assert store.attachment_payload([aid], pid, tid, bid)[0] == [aid]
    assert 'important alpha' in store.attachment_payload([aid], pid, tid, bid)[1]
    assert store.search_attachments(pid, 'alpha', tid)[0]['attachment_id'] == aid


def test_text_and_zip_indexing_without_extraction(tmp_path):
    kind, chunks, note = extract_document('readme.md', b'# Title\n\nHello SERGDATA')
    assert kind == 'text'
    assert 'SERGDATA' in chunks[0]['content']

    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as zf:
        zf.writestr('src/app.py', 'print("safe")')
        zf.writestr('../outside.txt', 'must not be indexed')
    kind, chunks, note = extract_document('project.zip', data.getvalue())
    assert kind == 'zip'
    assert any(x['source_path'] == 'src/app.py' for x in chunks)
    assert not any('outside' in x['source_path'] for x in chunks)
    assert 'не распаковывались' in note


def test_branch_attachments_follow_fork_lineage_not_siblings(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('p', str(tmp_path))
    tid, parent = store.create_task(pid, 'task')
    parent_aid = store.add_attachment(
        project_id=pid, task_id=tid, branch_id=parent, original_name='parent.md',
        stored_name='parent.md', media_type='text/markdown', kind='text', size=4,
        sha256='1', note='', chunks=[{'source_path':'parent.md','chunk_index':0,'content':'parent marker'}]
    )
    child = store.create_branch(parent, 'child')
    sibling = store.create_branch(parent, 'sibling')
    sibling_aid = store.add_attachment(
        project_id=pid, task_id=tid, branch_id=sibling, original_name='sibling.md',
        stored_name='sibling.md', media_type='text/markdown', kind='text', size=4,
        sha256='2', note='', chunks=[{'source_path':'sibling.md','chunk_index':0,'content':'sibling marker'}]
    )
    assert parent_aid in [x['id'] for x in store.attachments(pid, tid, child)]
    assert sibling_aid not in [x['id'] for x in store.attachments(pid, tid, child)]
    assert 'parent marker' in store.attachment_payload([parent_aid], pid, tid, child)[1]
    assert store.search_attachments(pid, 'sibling', tid, child) == []


def test_secret_files_are_rejected(tmp_path):
    import pytest
    with pytest.raises(ValueError, match='секретных файлов'):
        extract_document('.env', b'API_KEY=do-not-store')
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as zf:
        zf.writestr('project/.env', 'SECRET=value')
    with pytest.raises(ValueError, match='секретный файл'):
        extract_document('project.zip', data.getvalue())


def test_read_uploaded_file_reports_complete_coverage_across_pages(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('p', str(tmp_path))
    tid, bid = store.create_task(pid, 'task')
    aid = store.add_attachment(
        project_id=pid, task_id=tid, branch_id=bid, original_name='continuum.md',
        stored_name='continuum.md', media_type='text/markdown', kind='text', size=20,
        sha256='abc', note='', chunks=[
            {'source_path':'continuum.md','chunk_index':0,'content':'section one'},
            {'source_path':'continuum.md','chunk_index':1,'content':'section two'},
            {'source_path':'continuum.md','chunk_index':2,'content':'section three'},
            {'source_path':'continuum.md','chunk_index':3,'content':'section four'},
        ]
    )
    first = store.read_attachment_chunks(aid, pid, tid, bid, start_chunk=0, max_chunks=3)
    assert first['complete'] is False
    assert first['next_chunk'] == 3
    assert [x['content'] for x in first['chunks']] == ['section one','section two','section three']
    last = store.read_attachment_chunks(aid, pid, tid, bid, start_chunk=first['next_chunk'], max_chunks=3)
    assert last['complete'] is True
    assert last['next_chunk'] is None
    assert last['chunks'][0]['content'] == 'section four'


def test_read_uploaded_file_rejects_other_branch_attachment(tmp_path):
    import pytest
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('p', str(tmp_path))
    tid, bid = store.create_task(pid, 'task')
    sibling = store.create_branch(bid, 'sibling')
    aid = store.add_attachment(
        project_id=pid, task_id=tid, branch_id=sibling, original_name='private.md',
        stored_name='private.md', media_type='text/markdown', kind='text', size=4,
        sha256='abc', note='', chunks=[{'source_path':'private.md','chunk_index':0,'content':'private'}]
    )
    with pytest.raises(ValueError, match='другой ветке'):
        store.read_attachment_chunks(aid, pid, tid, bid)


def test_upload_blocks_secret_env_variants_and_secret_files_in_zip():
    import io
    import zipfile
    import pytest
    from workbench.attachments import extract_document

    with pytest.raises(ValueError):
        extract_document('.env.development', b'PASSWORD=secret')
    with pytest.raises(ValueError):
        extract_document('secrets.toml', b'password = "secret"')

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('src/app.py', 'print(1)')
        archive.writestr('.git/config', '[remote]\nurl=https://token@example.invalid/repo')
    with pytest.raises(ValueError):
        extract_document('source.zip', buffer.getvalue())
