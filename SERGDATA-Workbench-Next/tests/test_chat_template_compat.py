import sys
from types import ModuleType

# Workbench runtime dependencies are intentionally stubbed here: these tests
# exercise the pure message-normalization method and do not open network/MCP.
if 'openai' not in sys.modules:
    openai_stub = ModuleType('openai')
    openai_stub.AsyncOpenAI = object
    sys.modules['openai'] = openai_stub
if 'mcp' not in sys.modules:
    mcp_stub = ModuleType('mcp')
    mcp_stub.ClientSession = object
    mcp_stub.StdioServerParameters = object
    mcp_client_stub = ModuleType('mcp.client')
    mcp_stdio_stub = ModuleType('mcp.client.stdio')
    mcp_stdio_stub.stdio_client = lambda *args, **kwargs: None
    sys.modules['mcp'] = mcp_stub
    sys.modules['mcp.client'] = mcp_client_stub
    sys.modules['mcp.client.stdio'] = mcp_stdio_stub

from workbench.agent import Agent


def test_context_builder_emits_one_leading_system_message_and_keeps_tool_results_in_order():
    agent = object.__new__(Agent)
    history = [
        {'role': 'user', 'content': 'Найди настройку'},
        {'role': 'assistant', 'content': 'Сейчас проверю.'},
        {'role': 'tool', 'content': 'search_knowledge:\nНайден файл config.py'},
        {'role': 'assistant', 'content': 'Нашёл config.py.'},
    ]

    messages = agent._context_messages(
        history,
        memory='Сохранённая память ветки',
        project_root='F:/AI-Projects/demo',
        project_memory='Архитектура проекта',
        task_memory='Проверить настройки',
    )

    system_positions = [i for i, message in enumerate(messages) if message['role'] == 'system']
    assert system_positions == [0]
    assert messages[0]['content'].count('PROJECT_ROOT:') == 1
    assert 'Архитектура проекта' in messages[0]['content']
    assert 'Проверить настройки' in messages[0]['content']
    assert 'Сохранённая память ветки' in messages[0]['content']
    assert messages[3]['role'] == 'user'
    assert messages[3]['content'].startswith('[ПОДТВЕРЖДЁННЫЙ РЕЗУЛЬТАТ ИНСТРУМЕНТА')
    assert messages[-1] == {'role': 'assistant', 'content': 'Нашёл config.py.'}


def test_context_builder_never_creates_system_messages_from_stored_tool_results():
    agent = object.__new__(Agent)
    messages = agent._context_messages(
        [{'role': 'tool', 'content': 'list_project_files:\na.py'}],
        memory='', project_root='F:/project',
    )
    assert [m['role'] for m in messages] == ['system', 'user']


def test_agent_has_full_attachment_reader_and_evidence_protocol():
    agent = object.__new__(Agent)
    agent.kbtools = {}
    names = [item['function']['name'] for item in agent.specs()]
    assert 'read_uploaded_file' in names
    assert 'полностью' in Agent.__dict__.get('SYSTEM', '').lower() or 'ПРОТОКОЛ ДОКАЗАТЕЛЬСТВ' in __import__('workbench.agent', fromlist=['SYSTEM']).SYSTEM


def test_mcp_tool_text_is_joined_with_real_newlines():
    import asyncio
    from types import SimpleNamespace

    class FakeKB:
        async def call_tool(self, name, args):
            return SimpleNamespace(content=[SimpleNamespace(text='first'), SimpleNamespace(text='second')], isError=False)

    agent = object.__new__(Agent)
    agent.kbtools = {'search_knowledge': object()}
    agent.kb = FakeKB()
    from pathlib import Path
    agent.store = SimpleNamespace(project_for_branch=lambda bid: {'root': str(Path.cwd())})
    result = asyncio.run(agent.tool('search_knowledge', {'query': 'x'}, 1))
    assert result == 'first\nsecond'


def test_read_uploaded_file_tool_exposes_partial_then_complete_state(tmp_path):
    import asyncio
    from pathlib import Path
    from workbench.db import Store

    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('p', str(tmp_path))
    tid, bid = store.create_task(pid, 'task')
    aid = store.add_attachment(
        project_id=pid, task_id=tid, branch_id=bid, original_name='continuum.md',
        stored_name='continuum.md', media_type='text/markdown', kind='text', size=10,
        sha256='abc', note='', chunks=[
            {'source_path':'continuum.md','chunk_index':0,'content':'first section'},
            {'source_path':'continuum.md','chunk_index':1,'content':'last section'},
        ]
    )
    agent = object.__new__(Agent)
    agent.store = store
    partial = asyncio.run(agent.tool('read_uploaded_file', {'attachment_id': aid, 'start_chunk': 0, 'max_chunks': 1}, bid))
    assert 'ЧАСТИЧНО ПРОЧИТАН' in partial
    assert 'СЛЕДУЮЩАЯ ЧАСТЬ: 2' in partial
    complete = asyncio.run(agent.tool('read_uploaded_file', {'attachment_id': aid, 'start_chunk': 1, 'max_chunks': 1}, bid))
    assert 'ПОЛНОСТЬЮ ПРОЧИТАН' in complete
    assert 'last section' in complete


def test_write_tool_does_not_queue_duplicate_pending_change(tmp_path):
    import asyncio
    from workbench.db import Store

    store = Store(tmp_path / 'db.sqlite3')
    pid = store.create_project('p', str(tmp_path))
    tid, bid = store.create_task(pid, 'task')
    agent = object.__new__(Agent)
    agent.store = store
    store.add_pending(bid, 'README.md', '# Existing')
    same = asyncio.run(agent.tool('write_project_file', {'path': 'README.md', 'content': '# Existing'}, bid))
    conflict = asyncio.run(agent.tool('write_project_file', {'path': 'README.md', 'content': '# New'}, bid))
    assert 'ДУБЛЬ ПРЕДОТВРАЩЁН' in same
    assert 'КОНФЛИКТ ОЖИДАЮЩЕГО ИЗМЕНЕНИЯ' in conflict
    assert len(store.pending(bid)) == 1


def test_system_prompt_requires_relevant_knowledge_search_for_new_local_project_tasks_without_repeating_followups():
    from workbench.agent import SYSTEM

    assert 'Для каждой НОВОЙ технической задачи по зарегистрированному локальному проекту' in SYSTEM
    assert 'не запускай поиск механически на каждое сообщение' in SYSTEM
    assert 'Если инструменты Knowledge не подключены' in SYSTEM
    assert 'актуальная реализация и конфигурация подтверждают текущее поведение' in SYSTEM
