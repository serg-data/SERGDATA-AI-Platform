import asyncio
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock


def _install_optional_import_stubs():
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
        mcp_stdio_stub.stdio_client = lambda *a, **k: None
        sys.modules.update({
            'mcp': mcp_stub,
            'mcp.client': mcp_client_stub,
            'mcp.client.stdio': mcp_stdio_stub,
        })


def _agent_with_summary():
    _install_optional_import_stubs()
    from workbench.agent import Agent

    agent = object.__new__(Agent)
    agent.effective_context_limit = AsyncMock(return_value=(8192, None, None))
    agent.prompt_metrics = lambda *args: {'estimated_prompt_tokens': 100000}
    async def summarize(model, old_messages, previous_memory, bid=None, turn_message_id=None):
        # Preserve evidence that the tool results reached compaction.
        roles = [m.get('role') for m in old_messages]
        contents = [m.get('content', '') for m in old_messages]
        assert 'tool' in roles
        assert any('tool-result' in str(value) for value in contents)
        return 'Сводка: инструмент вернул tool-result.', 11, 7
    agent._summarize = summarize
    return agent


def test_compaction_keeps_user_query_when_tool_messages_are_last():
    agent = _agent_with_summary()
    messages = [
        {'role': 'system', 'content': 'system prompt'},
        {'role': 'user', 'content': 'Исследуй проект и продолжай до результата.'},
        {'role': 'assistant', 'content': '', 'tool_calls': [
            {'id': 'call-1', 'type': 'function',
             'function': {'name': 'read_project_file', 'arguments': '{"path":"a.py"}'}}
        ]},
        {'role': 'tool', 'tool_call_id': 'call-1', 'content': 'tool-result: file contents'},
    ]

    compacted, memory, prompt_tokens, completion_tokens = asyncio.run(
        agent._compact_runtime(messages, [], 'test-model', 42, '', 100)
    )

    assert any(m.get('role') == 'user' and
               m.get('content') == 'Исследуй проект и продолжай до результата.'
               for m in compacted)
    assert compacted[-1]['role'] == 'user'
    assert 'Сводка:' in memory
    assert prompt_tokens == 11
    assert completion_tokens == 7


def test_compaction_preserves_latest_synthetic_user_instruction_after_tools():
    agent = _agent_with_summary()
    messages = [
        {'role': 'system', 'content': 'system prompt'},
        {'role': 'user', 'content': 'Исходная задача пользователя.'},
        {'role': 'assistant', 'content': 'Выполняю поиск.'},
        {'role': 'tool', 'tool_call_id': 'call-1', 'content': 'tool-result: результаты поиска'},
        {'role': 'user', 'content': '[WORKBENCH] Продолжи с недостающим диапазоном.'},
    ]

    compacted, memory, _, _ = asyncio.run(
        agent._compact_runtime(messages, [], 'test-model', 42, '', 100)
    )

    assert compacted[-1] == messages[-1]
    assert any(m.get('role') == 'user' and
               m.get('content') == '[WORKBENCH] Продолжи с недостающим диапазоном.'
               for m in compacted)
    assert 'Сводка:' in memory


def test_compaction_without_user_message_does_not_send_a_malformed_rebuilt_context():
    agent = _agent_with_summary()
    messages = [
        {'role': 'system', 'content': 'system prompt'},
        {'role': 'assistant', 'content': 'only assistant'},
        {'role': 'tool', 'tool_call_id': 'call-1', 'content': 'tool-result'},
    ]

    compacted, memory, prompt_tokens, completion_tokens = asyncio.run(
        agent._compact_runtime(messages, [], 'test-model', 42, '', 100)
    )

    # Fail closed: no lossy compaction is attempted when there is no user
    # turn to preserve. The caller receives the original context unchanged.
    assert compacted is messages
    assert memory == ''
    assert prompt_tokens == completion_tokens == 0
