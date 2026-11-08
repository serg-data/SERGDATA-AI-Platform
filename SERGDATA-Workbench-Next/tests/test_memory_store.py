from pathlib import Path
from tempfile import TemporaryDirectory
from workbench.db import Store


def test_branch_memory_inheritance():
    with TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / 'test.sqlite3')
        project = store.ensure_project('test', tmp)
        task_id, branch_id = store.create_task(project['id'], 'task')
        message_id = store.add_message(branch_id, 'user', 'first message')
        store.save_memory(branch_id, 'compact project memory', message_id)
        child_id = store.create_branch(branch_id, 'experiment')
        memory = store.get_memory(child_id)
        assert memory is not None
        assert memory['summary'] == 'compact project memory'
        assert memory['through_message_id'] == message_id
        assert [m['content'] for m in store.messages(child_id)] == ['first message']


def test_context_compaction_without_network():
    import asyncio
    async def run_test():
        from types import SimpleNamespace, ModuleType
        import sys
        # Stub network SDK imports: this test exercises local context compaction only.
        openai = ModuleType('openai'); openai.AsyncOpenAI = object; sys.modules.setdefault('openai', openai)
        mcp = ModuleType('mcp'); mcp.ClientSession = object; mcp.StdioServerParameters = object; sys.modules.setdefault('mcp', mcp)
        mcp_client = ModuleType('mcp.client'); sys.modules.setdefault('mcp.client', mcp_client)
        mcp_stdio = ModuleType('mcp.client.stdio'); mcp_stdio.stdio_client = object; sys.modules.setdefault('mcp.client.stdio', mcp_stdio)
        from workbench.agent import Agent
        with TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / 'test.sqlite3')
            project = store.ensure_project('test', tmp)
            _, branch_id = store.create_task(project['id'], 'long task')
            history = []
            for i in range(34):
                role = 'user' if i % 2 == 0 else 'assistant'
                mid = store.add_message(branch_id, role, (f'message {i} ' + 'details ' * 80))
                history.append({'id': mid, 'role': role, 'content': f'message {i} ' + 'details ' * 80})
            agent = Agent.__new__(Agent)
            agent.cfg = SimpleNamespace(context_limit=4096)
            agent.store = store
            agent.project = SimpleNamespace(root=Path(tmp))
            async def fake_summary(model, old, previous, bid=None, turn_message_id=None):
                return ((previous + '\n' if previous else '') + f'Сводка {len(old)} старых сообщений', 20, 10)
            agent._summarize = fake_summary
            messages, info = await agent._prepare_context(branch_id, history, 'fake-model', [])
            assert store.get_memory(branch_id) is not None
            assert info['memory_active'] is True
            assert len(messages) < len(history) + 2
            print('context compaction test: OK', info)
    
    
    asyncio.run(run_test())
if __name__ == '__main__':
    import asyncio
    test_branch_memory_inheritance()
    asyncio.run(test_context_compaction_without_network())
    print('all memory tests: OK')
