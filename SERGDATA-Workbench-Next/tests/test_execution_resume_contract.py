from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_agent_persists_original_tool_call_context_for_approval():
    source = (ROOT / 'workbench' / 'agent.py').read_text(encoding='utf-8')
    assert 'self.store.set_execution_context(int(queued_match.group(1)), msgs, tc.id, model, user_message_id)' in source
    assert 'async def resume_execution(self, execution_id: int, result_text: str):' in source
    assert "'tool_call_id': tool_call_id" in source


def test_powershell_cannot_be_used_as_ssh_bypass():
    source = (ROOT / 'workbench' / 'agent.py').read_text(encoding='utf-8')
    assert 'SSH-ОБХОД ЗАБЛОКИРОВАН' in source
    ssh_source = (ROOT / 'workbench' / 'ssh.py').read_text(encoding='utf-8')
    assert 'StrictHostKeyChecking=yes' in ssh_source


def test_terminal_process_result_triggers_agent_resume():
    source = (ROOT / 'main.py').read_text(encoding='utf-8')
    assert 'run_tracked_agent_task(' in source
    assert "run_execution_resume(\n                    int(link['branch_id']), link['execution_id'], rendered" in source
    assert "metadata={'kind':'execution_result'" in source


def test_approval_endpoint_blocks_legacy_powershell_ssh_bypass():
    source = (ROOT / 'main.py').read_text(encoding='utf-8')
    assert 'SSH нельзя запускать через PowerShell' in source
    assert 'SSH через PowerShell заблокирован' in source


def test_approval_endpoint_allows_specialized_ssh_profile_marker():
    source = (ROOT / 'main.py').read_text(encoding='utf-8')
    assert "raw_script.startswith(('__SERGDATA_EXEC_V1__', '__SERGDATA_PROFILE_EXEC_V1__'))" in source


def test_resume_execution_returns_actual_result_to_original_tool_call(tmp_path):
    import asyncio
    import json
    import pytest
    pytest.importorskip('openai')
    pytest.importorskip('mcp')
    from types import SimpleNamespace
    from workbench.agent import Agent
    from workbench.db import Store

    store = Store(tmp_path / 'workbench.sqlite3')
    with store.conn() as c:
        c.execute("INSERT INTO projects(name,root,created_at) VALUES('p',?,?)", (str(tmp_path), 'now'))
        pid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO tasks(project_id,title,created_at,updated_at) VALUES(?,?,?,?)", (pid, 't', 'now', 'now'))
        tid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO branches(task_id,name,created_at,updated_at) VALUES(?,?,?,?)", (tid, 'b', 'now', 'now'))
        bid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
    eid = store.add_pending_execution(bid, '__SERGDATA_EXEC_V1__{}')
    snapshot = [
        {'role': 'user', 'content': 'получи hostname'},
        {'role': 'assistant', 'content': '', 'tool_calls': [
            {'id': 'call_original_77', 'type': 'function', 'function': {'name': 'ssh_run_command', 'arguments': '{}'}}
        ]},
    ]
    store.set_execution_context(eid, snapshot, 'call_original_77', 'test-model', None)
    store.finish_execution(eid, 'completed', 'test execution')

    captured = {}
    class FakeCompletions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            msg = SimpleNamespace(content='Сервер ответил: fin-host', tool_calls=None)
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
                                   usage=SimpleNamespace(prompt_tokens=5, completion_tokens=3))
    class FakeLLM:
        chat = SimpleNamespace(completions=FakeCompletions())
        def with_options(self, **kwargs):
            return self

    agent = object.__new__(Agent)
    agent.store = store
    agent.cfg = SimpleNamespace(lm_model='test-model')
    agent.llm = FakeLLM()
    agent.specs = lambda: []
    async def compact(msgs, tools, model, branch_id, memory, turn_id):
        return msgs, '', 0, 0
    agent._compact_runtime = compact

    result = asyncio.run(agent.resume_execution(eid, 'STDOUT:\nfin-host\nexit_code=0'))
    assert result['resumed'] is True
    assert captured['messages'][-1]['role'] == 'tool'
    assert captured['messages'][-1]['tool_call_id'] == 'call_original_77'
    assert 'fin-host' in captured['messages'][-1]['content']
    saved = store.messages(bid)
    assert any(m['role'] == 'assistant' and 'Сервер ответил' in m['content'] for m in saved)
    assert store.execution_by_id(eid)['resume_status'] == 'completed'
    second = asyncio.run(agent.resume_execution(eid, 'must not replay'))
    assert second['resumed'] is False
    assert 'уже' in second['reason']


def test_execution_resume_waits_for_existing_branch_chat_without_losing_result():
    import asyncio
    import threading
    from workbench.execution_resume import run_after_branch_task

    async def scenario():
        tasks = {}
        lock = threading.RLock()
        entered = asyncio.Event()
        release = asyncio.Event()
        resumed = []

        async def existing_chat():
            entered.set()
            await release.wait()

        active = asyncio.create_task(existing_chat())
        with lock:
            tasks[7] = active
        await entered.wait()

        async def tracked_runner(branch_id, awaitable):
            current = asyncio.current_task()
            with lock:
                other = tasks.get(branch_id)
                assert other is None or other.done() or other is current
                tasks[branch_id] = current
            try:
                return await awaitable
            finally:
                with lock:
                    if tasks.get(branch_id) is current:
                        tasks.pop(branch_id, None)

        def make_resume():
            async def resume():
                resumed.append((7, 'original tool result'))
                return {'resumed': True}
            return resume()

        continuation = asyncio.create_task(run_after_branch_task(
            7, make_resume, tasks, lock, tracked_runner, lambda: False
        ))
        await asyncio.sleep(0)
        assert not continuation.done()
        assert resumed == []
        release.set()
        await active
        with lock:
            if tasks.get(7) is active:
                tasks.pop(7, None)
        result = await asyncio.wait_for(continuation, timeout=1)
        assert result == {'resumed': True}
        assert resumed == [(7, 'original tool result')]

    asyncio.run(scenario())


def test_execution_resume_on_another_branch_does_not_wait():
    import asyncio
    import threading
    from workbench.execution_resume import run_after_branch_task

    async def scenario():
        tasks = {1: asyncio.create_task(asyncio.sleep(0.2))}
        lock = threading.RLock()
        started = []

        async def tracked_runner(branch_id, awaitable):
            return await awaitable

        def make_resume():
            async def resume():
                started.append(2)
                return 'ok'
            return resume()

        result = await asyncio.wait_for(run_after_branch_task(
            2, make_resume, tasks, lock, tracked_runner, lambda: False
        ), timeout=0.05)
        assert result == 'ok'
        assert started == [2]
        await tasks[1]

    asyncio.run(scenario())


def test_execution_resume_path_uses_branch_waiter_and_logs_future_errors():
    source = (ROOT / 'main.py').read_text(encoding='utf-8')
    assert 'async def run_execution_resume(' in source
    assert 'run_after_branch_task(' in source
    assert 'future.add_done_callback(_log_resume_future)' in source
    assert "logger.exception(\"Не удалось запланировать продолжение выполнения #%s\", eid)" in source
