from workbench.db import Store


def _seed_attachment(store, project_id, task_id, branch_id):
    return store.add_attachment(
        project_id=project_id, task_id=task_id, branch_id=branch_id,
        original_name='design.md', stored_name='shared-design.md',
        media_type='text/markdown', kind='text', size=28, sha256='a' * 64,
        note='Техническая спецификация',
        chunks=[{'source_path':'design.md','chunk_index':0,'content':'handoff attachment content'}],
    )


def test_handoff_grants_new_task_scoped_attachment_access_without_copying(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('P', str(tmp_path))
    source_tid, source_bid = store.create_task(pid, 'Source')
    aid = _seed_attachment(store, pid, source_tid, source_bid)

    new_tid, new_bid = store.create_task_with_memory(pid, 'Continuation', '# handoff', [aid])

    visible = store.attachments(pid, new_tid, new_bid)
    assert [x['id'] for x in visible] == [aid]
    assert store.attachment(aid)['stored_name'] == 'shared-design.md'
    assert store.read_attachment_chunks(aid, pid, new_tid, new_bid)['chunks'][0]['content'] == 'handoff attachment content'
    allowed, payload = store.attachment_payload([aid], pid, new_tid, new_bid)
    assert allowed == [aid]
    assert 'handoff attachment content' in payload
    assert store.search_attachments(pid, 'handoff attachment', new_tid, new_bid)


def test_handoff_attachment_grant_does_not_leak_to_other_tasks_or_projects(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('P', str(tmp_path))
    source_tid, source_bid = store.create_task(pid, 'Source')
    aid = _seed_attachment(store, pid, source_tid, source_bid)
    new_tid, new_bid = store.create_task_with_memory(pid, 'Continuation', '# handoff', [aid])
    unrelated_tid, unrelated_bid = store.create_task(pid, 'Unrelated')

    assert not store.attachments(pid, unrelated_tid, unrelated_bid)
    try:
        store.read_attachment_chunks(aid, pid, unrelated_tid, unrelated_bid)
    except ValueError as exc:
        assert 'другой задаче' in str(exc) or 'другой ветке' in str(exc)
    else:
        raise AssertionError('attachment access must remain task-scoped')

    other_pid = store.create_project('Other', str(tmp_path / 'other'))
    other_tid, other_bid = store.create_task(other_pid, 'Other task')
    try:
        store.attachment_payload([aid], other_pid, other_tid, other_bid)
    except ValueError as exc:
        assert 'другому проекту' in str(exc)
    else:
        raise AssertionError('attachment access must not cross projects')
