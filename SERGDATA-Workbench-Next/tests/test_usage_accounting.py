from pathlib import Path
from tempfile import TemporaryDirectory

from workbench.db import Store


def test_branch_usage_includes_only_inherited_history_before_fork():
    with TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / 'workbench.sqlite3')
        project = store.ensure_project('P', tmp)
        task_id, parent = store.create_task(project['id'], 'T')

        first_user = store.add_message(parent, 'user', 'first question')
        store.record_llm_call(parent, first_user, 'model-a', 'chat', 100, 10)
        store.add_message(parent, 'assistant', 'first answer', 100, 10, usage_message_id=first_user)

        child = store.create_branch(parent, 'Child')

        # This API usage happened in the parent after the fork; it must not
        # appear in the child's inherited-history totals.
        later_user = store.add_message(parent, 'user', 'parent-only question')
        store.record_llm_call(parent, later_user, 'model-a', 'chat', 300, 30)
        store.add_message(parent, 'assistant', 'parent-only answer', 300, 30, usage_message_id=later_user)

        child_user = store.add_message(child, 'user', 'child question')
        store.record_llm_call(child, child_user, 'model-a', 'chat', 50, 5)
        store.add_message(child, 'assistant', 'child answer', 50, 5, usage_message_id=child_user)

        result = store.usage_lineage(child)
        assert result['direct'] == {'p': 50, 'c': 5, 't': 55}
        assert result['inherited'] == {'p': 100, 'c': 10, 't': 110}
        assert result['history'] == {'p': 150, 'c': 15, 't': 165}

        calls = store.llm_call_history(child)
        assert len(calls) == 2
        assert [x['prompt_tokens'] for x in calls] == [100, 50]


def test_call_without_usage_is_recorded_as_unreported():
    with TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / 'workbench.sqlite3')
        project = store.ensure_project('P', tmp)
        _, branch = store.create_task(project['id'], 'T')
        user_message = store.add_message(branch, 'user', 'question')
        store.record_llm_call(branch, user_message, 'model-a', 'chat', None, None)
        call = store.llm_call_history(branch)[0]
        assert call['usage_reported'] == 0
        assert call['prompt_tokens'] is None
        assert call['completion_tokens'] is None


def test_last_turn_usage_sums_tool_rounds_and_inherited_parent_turn():
    with TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / 'workbench.sqlite3')
        project = store.ensure_project('P', tmp)
        task_id, parent = store.create_task(project['id'], 'T')

        first_user = store.add_message(parent, 'user', 'parent question')
        store.record_llm_call(parent, first_user, 'model-a', 'tool_call', 100, 5)
        store.record_llm_call(parent, first_user, 'model-a', 'chat', 130, 12)
        store.add_message(parent, 'assistant', 'parent answer', 230, 17, usage_message_id=first_user)
        child = store.create_branch(parent, 'Child')

        inherited_turn = store.last_llm_turn(child)
        assert inherited_turn['message_id'] == first_user
        assert inherited_turn['call_count'] == 2
        assert inherited_turn['prompt_tokens'] == 230
        assert inherited_turn['completion_tokens'] == 17
        assert inherited_turn['complete'] is True

        child_user = store.add_message(child, 'user', 'child question')
        store.record_llm_call(child, child_user, 'model-a', 'tool_call', 70, 4)
        store.record_llm_call(child, child_user, 'model-a', 'chat', None, None)
        latest = store.last_llm_turn(child)
        assert latest['message_id'] == child_user
        assert latest['call_count'] == 2
        assert latest['reported_calls'] == 1
        assert latest['unreported_calls'] == 1
        assert latest['prompt_tokens'] == 70
        assert latest['complete'] is False


def test_legacy_usage_totals_are_preserved_alongside_new_detailed_calls():
    import sqlite3
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'workbench.sqlite3'
        store = Store(path)
        project = store.ensure_project('P', tmp)
        _, branch = store.create_task(project['id'], 'T')
        with sqlite3.connect(path) as conn:
            conn.execute(
                "INSERT INTO usage(branch_id,model,prompt_tokens,completion_tokens,total_tokens,created_at) VALUES(?,?,?,?,?,?)",
                (branch, 'old-model', 400, 100, 500, '2026-01-01T00:00:00+00:00')
            )
        user_message = store.add_message(branch, 'user', 'new question')
        store.record_llm_call(branch, user_message, 'new-model', 'chat', 120, 20)
        store.add_message(branch, 'assistant', 'answer', 120, 20, usage_message_id=user_message)

        totals = store.usage_lineage(branch)
        assert totals['direct'] == {'p': 520, 'c': 120, 't': 640}
        assert totals['history'] == {'p': 520, 'c': 120, 't': 640}


def test_delete_message_removes_only_its_turn_usage_and_rejects_inherited(tmp_path):
    store = Store(tmp_path / 'db.sqlite3')
    project = store.ensure_project('P', str(tmp_path))
    _, parent = store.create_task(project['id'], 'T')
    mid = store.add_message(parent, 'user', 'question')
    store.record_llm_call(parent, mid, 'model', 'chat', 100, 20)
    child = store.create_branch(parent, 'Child')
    try:
        store.delete_message(child, mid)
        assert False, 'inherited message must not be deleted from child branch'
    except ValueError:
        pass
    assert store.delete_message(parent, mid) is True
    assert store.usage_lineage(parent)['history']['t'] == 0
    assert store.messages(parent) == []
