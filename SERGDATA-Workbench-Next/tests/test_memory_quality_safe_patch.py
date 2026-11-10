import asyncio
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock


def _stub_imports():
    if 'openai' not in sys.modules:
        m = ModuleType('openai'); m.AsyncOpenAI = object; sys.modules['openai'] = m
    if 'mcp' not in sys.modules:
        m = ModuleType('mcp'); m.ClientSession = object; m.StdioServerParameters = object
        c = ModuleType('mcp.client'); st = ModuleType('mcp.client.stdio'); st.stdio_client = lambda *a, **k: None
        sys.modules.update({'mcp': m, 'mcp.client': c, 'mcp.client.stdio': st})


def test_summary_message_length_setting_persists_and_is_bounded():
    from workbench.db import Store
    with TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / 'settings.sqlite3')
        assert store.get_app_settings()['summary_message_max_chars'] == 15000
        saved = store.set_app_settings({'summary_message_max_chars': 30000})
        assert saved['summary_message_max_chars'] == 30000
        assert Store(Path(tmp) / 'settings.sqlite3').get_app_settings()['summary_message_max_chars'] == 30000
        for invalid in (999, 50001):
            try:
                store.set_app_settings({'summary_message_max_chars': invalid})
            except ValueError:
                pass
            else:
                raise AssertionError('out-of-range summary_message_max_chars was accepted')


def test_summarizer_respects_configured_limit_and_keeps_message_tail():
    _stub_imports()
    from workbench.agent import Agent
    agent = object.__new__(Agent)
    agent.runtime_settings = {'summary_message_max_chars': 1000}
    agent.store = SimpleNamespace(record_llm_call=lambda *args: None)
    captured = {}
    async def create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='Сводка'))], usage=None)
    agent.llm = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    result = asyncio.run(agent._summarize('model', [{'role': 'tool', 'content': 'START-' + ('x' * 2000) + '-IMPORTANT-END'}], '', 1, 2))
    payload = captured['messages'][1]['content']
    assert result[0] == 'Сводка'
    assert 'START-' in payload
    assert '-IMPORTANT-END' in payload
    assert 'СРЕДНЯЯ ЧАСТЬ СООБЩЕНИЯ ПРОПУЩЕНА' in payload
    assert len(payload) < 1200


def test_repeated_runtime_compaction_replaces_summary_and_keeps_one_system_message():
    _stub_imports()
    from workbench.agent import Agent
    agent = object.__new__(Agent)
    agent.effective_context_limit = AsyncMock(return_value=(8192, None, None))
    agent.prompt_metrics = lambda *args: {'estimated_prompt_tokens': 100000}
    summaries = iter(['Первая runtime-сводка', 'Вторая runtime-сводка'])
    async def summarize(*args, **kwargs):
        return next(summaries), 1, 1
    agent._summarize = summarize

    initial = [
        {'role': 'system', 'content': 'Основные системные инструкции.'},
        {'role': 'user', 'content': 'Исходный запрос.'},
        {'role': 'assistant', 'content': 'Старый шаг.'},
        {'role': 'tool', 'content': 'Результат старого инструмента.'},
        {'role': 'user', 'content': 'Продолжи.'},
    ]
    first, memory, _, _ = asyncio.run(agent._compact_runtime(initial, [], 'model', 1, '', 10))
    second_input = [
        first[0], first[1],
        {'role': 'assistant', 'content': 'Ещё один шаг.'},
        {'role': 'tool', 'content': 'Ещё один результат.'},
        {'role': 'user', 'content': 'Продолжай дальше.'},
    ]
    second, memory2, _, _ = asyncio.run(agent._compact_runtime(second_input, [], 'model', 1, memory, 11))
    system_messages = [m for m in second if m.get('role') == 'system']
    system_text = system_messages[0]['content']
    assert len(system_messages) == 1
    assert 'Основные системные инструкции.' in system_text
    assert 'Первая runtime-сводка' not in system_text
    assert system_text.count('[WORKBENCH_RUNTIME_MEMORY_BEGIN]') == 1
    assert 'Вторая runtime-сводка' in system_text
    assert second[-1]['content'] == 'Продолжай дальше.'
    assert memory2 == 'Вторая runtime-сводка'
