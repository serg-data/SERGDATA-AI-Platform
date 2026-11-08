from workbench.db import Store
from workbench.handoff import collect_handoff_scope


def test_branch_scope_includes_only_selected_branch_and_its_lineage(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('P', str(tmp_path))
    tid, root = store.create_task(pid, 'Task A')
    store.add_message(root, 'user', 'root history')
    child = store.create_branch(root, 'Child')
    store.add_message(child, 'user', 'child history')
    sibling = store.create_branch(root, 'Sibling')
    store.add_message(sibling, 'user', 'sibling history')
    project = store.project(pid)
    task = next(x for x in store.tasks(pid) if x['id'] == tid)

    data = collect_handoff_scope(store, project, task, child, 'branch')
    assert [b['id'] for _, b in data['selected_branches']] == [child]
    assert data['total_source_messages'] == 2
    assert 'root history' in data['evidence_messages'][0]['content']
    assert 'child history' in data['evidence_messages'][0]['content']
    assert 'sibling history' not in data['evidence_messages'][0]['content']


def test_task_scope_includes_all_branches_but_not_other_tasks(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('P', str(tmp_path))
    tid, root = store.create_task(pid, 'Task A')
    store.add_message(root, 'user', 'task A root')
    branch = store.create_branch(root, 'Second')
    store.add_message(branch, 'user', 'task A second')
    other_tid, other = store.create_task(pid, 'Task B')
    store.add_message(other, 'user', 'task B excluded')
    project = store.project(pid)
    task = next(x for x in store.tasks(pid) if x['id'] == tid)

    data = collect_handoff_scope(store, project, task, root, 'task')
    assert {b['id'] for _, b in data['selected_branches']} == {root, branch}
    assert data['total_source_messages'] == 2
    combined = '\n'.join(x['content'] for x in data['evidence_messages'])
    assert 'task A root' in combined and 'task A second' in combined
    assert 'task B excluded' not in combined


def test_project_scope_includes_other_tasks_in_same_project_only(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('P', str(tmp_path))
    tid, root = store.create_task(pid, 'Task A')
    store.add_message(root, 'user', 'task A')
    other_tid, other = store.create_task(pid, 'Task B')
    store.add_message(other, 'user', 'task B')
    other_pid = store.create_project('Other', str(tmp_path / 'other'))
    _, external = store.create_task(other_pid, 'External')
    store.add_message(external, 'user', 'external excluded')
    project = store.project(pid)
    task = next(x for x in store.tasks(pid) if x['id'] == tid)

    data = collect_handoff_scope(store, project, task, root, 'project')
    combined = '\n'.join(x['content'] for x in data['evidence_messages'])
    assert 'task A' in combined and 'task B' in combined
    assert 'external excluded' not in combined


def test_invalid_handoff_scope_is_rejected(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('P', str(tmp_path))
    tid, bid = store.create_task(pid, 'Task')
    project = store.project(pid)
    task = next(x for x in store.tasks(pid) if x['id'] == tid)
    try:
        collect_handoff_scope(store, project, task, bid, 'everything')
    except ValueError as exc:
        assert 'Недопустимый' in str(exc)
    else:
        raise AssertionError('invalid scope must be rejected')


def test_create_task_with_handoff_memory_is_atomic_and_complete(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('P', str(tmp_path))
    tid, bid = store.create_task_with_memory(pid, 'Continuation', '# Handoff')
    task = next(x for x in store.tasks(pid) if x['id'] == tid)
    assert task['summary'] == '# Handoff'
    assert store.branches(tid)[0]['id'] == bid
    assert store.messages(bid) == []
