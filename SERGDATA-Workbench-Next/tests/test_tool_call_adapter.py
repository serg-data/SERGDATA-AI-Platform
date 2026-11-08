from types import SimpleNamespace

from workbench.tool_call_adapter import extract_tool_calls, parse_text_tool_calls


def _tools():
    return [{"type": "function", "function": {
        "name": "sandbox_run_check",
        "parameters": {"type": "object", "properties": {
            "sandbox_id": {"type": "string"},
            "command": {"type": "string", "enum": ["pytest", "compile"]},
            "args": {"type": "array", "items": {"type": "string"}},
        }, "required": ["sandbox_id", "command"]},
    }}]


def test_parse_neohorse_xml_tool_call_and_alias_mode_to_command():
    content = '''<tool_call>
<function=sandbox_run_check>
<parameter=sandbox_id>
abc123
</parameter>
<parameter=mode>
pytest
</parameter>
<parameter=args>
["test_app.py", "-v"]
</parameter>
</function>
</tool_call>'''
    calls, detected, error = parse_text_tool_calls(content, _tools())
    assert detected is True
    assert error is None
    assert len(calls) == 1
    assert calls[0].function.name == "sandbox_run_check"
    assert calls[0].function.arguments == '{"sandbox_id": "abc123", "args": ["test_app.py", "-v"], "command": "pytest"}'


def test_parse_qwen_json_tool_call():
    content = '<tool_call>{"name":"sandbox_run_check","arguments":{"sandbox_id":"abc123","command":"compile"}}</tool_call>'
    calls, detected, error = parse_text_tool_calls(content, _tools())
    assert detected and error is None
    assert calls[0].function.name == "sandbox_run_check"


def test_reject_unknown_tool_and_unknown_parameters():
    unknown = '<tool_call><function=not_a_tool><parameter=x>1</parameter></function></tool_call>'
    calls, detected, error = parse_text_tool_calls(unknown, _tools())
    assert detected and not calls and "Неизвестный инструмент" in error
    bad_args = '<tool_call><function=sandbox_run_check><parameter=sandbox_id>x</parameter><parameter=mode>pytest</parameter><parameter=arbitrary>oops</parameter></function></tool_call>'
    calls, detected, error = parse_text_tool_calls(bad_args, _tools())
    assert detected and not calls and "Неизвестные параметры" in error


def test_native_tool_calls_take_precedence_over_text():
    native = [SimpleNamespace(id="native", function=SimpleNamespace(name="sandbox_run_check", arguments='{}'))]
    message = SimpleNamespace(tool_calls=native, content="<tool_call>bad</tool_call>")
    calls, detected, error = extract_tool_calls(message, _tools())
    assert calls == native
    assert not detected and error is None


def test_agent_chat_executes_text_call_then_continues_to_final_answer(monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    import sys
    from types import ModuleType
    if 'openai' not in sys.modules:
        openai_stub = ModuleType('openai'); openai_stub.AsyncOpenAI = object; sys.modules['openai'] = openai_stub
    if 'mcp' not in sys.modules:
        mcp_stub = ModuleType('mcp'); mcp_stub.ClientSession = object; mcp_stub.StdioServerParameters = object
        mcp_client_stub = ModuleType('mcp.client'); mcp_stdio_stub = ModuleType('mcp.client.stdio')
        mcp_stdio_stub.stdio_client = lambda *a, **k: None
        sys.modules.update({'mcp': mcp_stub, 'mcp.client': mcp_client_stub, 'mcp.client.stdio': mcp_stdio_stub})
    from workbench.agent import Agent

    first = SimpleNamespace(content='''<tool_call>
<function=sandbox_run_check>
<parameter=sandbox_id>abc123</parameter>
<parameter=mode>pytest</parameter>
<parameter=args>["test_app.py", "-v"]</parameter>
</function>
</tool_call>''', tool_calls=None)
    second = SimpleNamespace(content=first.content, tool_calls=None)
    third = SimpleNamespace(content='Проверка завершена успешно.', tool_calls=None)
    responses = [SimpleNamespace(choices=[SimpleNamespace(message=first)], usage=None),
                 SimpleNamespace(choices=[SimpleNamespace(message=second)], usage=None),
                 SimpleNamespace(choices=[SimpleNamespace(message=third)], usage=None)]

    class FakeCompletions:
        async def create(self, **kwargs):
            return responses.pop(0)

    class FakeLLM:
        chat = SimpleNamespace(completions=FakeCompletions())
        def with_options(self, **kwargs):
            return self

    class FakeStore:
        def get_app_settings(self):
            return {'max_tool_rounds': 4, 'max_tool_calls': 8, 'request_timeout': 30, 'temperature': 0}
        def project_for_branch(self, bid):
            return {'id': 1}
        def task_for_branch(self, bid):
            return {'id': 1}
        def attachment_payload(self, *args):
            return [], ''
        def add_message(self, *args, **kwargs):
            return 1
        def record_llm_call(self, *args, **kwargs):
            pass
        def pending(self, bid):
            return []

    agent = object.__new__(Agent)
    agent.store = FakeStore()
    agent.cfg = SimpleNamespace(lm_model='test-model', max_tool_rounds=4)
    agent.llm = FakeLLM()
    agent.kbtools = {}
    agent.runtime_settings = {}
    agent.last_model = 'test-model'
    agent._prepare_context = AsyncMock(return_value=([{'role': 'system', 'content': 'test'}],
        {'summary_prompt_tokens': 0, 'summary_completion_tokens': 0}))
    agent._compact_runtime = AsyncMock(side_effect=lambda msgs, *a: (msgs, {}, 0, 0))
    agent.prompt_metrics = lambda *args: {}
    executed = []
    async def fake_tool(name, args, bid):
        executed.append((name, args, bid))
        return {'status': 'completed', 'exit_code': 0}
    agent.tool = fake_tool

    result = asyncio.run(agent.chat(7, 'Запусти тесты', []))
    assert executed == [('sandbox_run_check', {
        'sandbox_id': 'abc123', 'args': ['test_app.py', '-v'], 'command': 'pytest'
    }, 7)]
    assert result['answer'] == 'Проверка завершена успешно.'
    assert result['tool_calls'] == 2
    assert result['tool_rounds'] == 2


def test_incomplete_text_tool_call_is_not_mistaken_for_a_final_answer():
    calls, detected, error = parse_text_tool_calls('<tool_call><function=sandbox_run_check>', _tools())
    assert detected and not calls
    assert 'незавершённый' in error


def test_reasoning_content_is_never_used_as_user_visible_answer():
    from workbench.tool_call_adapter import visible_response_text, empty_response_notice
    message = SimpleNamespace(content='', reasoning_content='Внутренний текст с возможными рассуждениями', tool_calls=None)
    assert visible_response_text(message, '') == ''
    notice = empty_response_notice(message, 'основного ответа')
    assert 'reasoning_content' in notice
    assert 'Внутренний текст' not in notice
    assert 'не был показан' in notice


def test_regular_content_wins_even_when_reasoning_is_present():
    from workbench.tool_call_adapter import visible_response_text
    message = SimpleNamespace(content='Готово.', reasoning_content='private reasoning')
    assert visible_response_text(message, 'fallback') == 'Готово.'


def test_empty_response_without_reasoning_gets_clear_notice():
    from workbench.tool_call_adapter import empty_response_notice
    message = SimpleNamespace(content='', reasoning_content=None)
    notice = empty_response_notice(message, 'основного ответа')
    assert 'без пользовательского текста' in notice


def test_agent_retries_once_when_model_returns_only_reasoning_content():
    import asyncio
    import sys
    from types import ModuleType, SimpleNamespace
    from unittest.mock import AsyncMock
    if 'openai' not in sys.modules:
        openai_stub = ModuleType('openai'); openai_stub.AsyncOpenAI = object; sys.modules['openai'] = openai_stub
    if 'mcp' not in sys.modules:
        mcp_stub = ModuleType('mcp'); mcp_stub.ClientSession = object; mcp_stub.StdioServerParameters = object
        mcp_client_stub = ModuleType('mcp.client'); mcp_stdio_stub = ModuleType('mcp.client.stdio')
        mcp_stdio_stub.stdio_client = lambda *a, **k: None
        sys.modules.update({'mcp': mcp_stub, 'mcp.client': mcp_client_stub, 'mcp.client.stdio': mcp_stdio_stub})
    from workbench.agent import Agent

    responses = [
        SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='', reasoning_content='private reasoning', tool_calls=None))], usage=None),
        SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='Файл изучен полностью.', tool_calls=None))], usage=None),
    ]
    calls = []
    class FakeCompletions:
        async def create(self, **kwargs):
            calls.append(kwargs)
            return responses.pop(0)
    class FakeLLM:
        chat = SimpleNamespace(completions=FakeCompletions())
        def with_options(self, **kwargs): return self
    class FakeStore:
        def get_app_settings(self):
            return {'max_tool_rounds': 4, 'max_tool_calls': 8, 'request_timeout': 30, 'temperature': 0}
        def project_for_branch(self, bid): return {'id': 1}
        def task_for_branch(self, bid): return {'id': 1}
        def attachment_payload(self, *args): return [], ''
        def add_message(self, *args, **kwargs): return 1
        def record_llm_call(self, *args, **kwargs): pass
        def pending(self, bid): return []

    agent = object.__new__(Agent)
    agent.store = FakeStore(); agent.cfg = SimpleNamespace(lm_model='test-model', max_tool_rounds=4)
    agent.llm = FakeLLM(); agent.kbtools = {}; agent.runtime_settings = {}; agent.last_model = 'test-model'
    agent._prepare_context = AsyncMock(return_value=([{'role': 'system', 'content': 'test'}], {'summary_prompt_tokens': 0, 'summary_completion_tokens': 0}))
    agent._compact_runtime = AsyncMock(side_effect=lambda msgs, *a: (msgs, {}, 0, 0))
    agent.prompt_metrics = lambda *args: {}
    agent._set_activity = lambda *args: None
    result = asyncio.run(agent.chat(7, 'Изучи файл', []))
    assert result['answer'] == 'Файл изучен полностью.'
    assert len(calls) == 2
    assert any('ПУСТОЙ ВИДИМЫЙ ОТВЕТ' in m.get('content', '') for m in calls[1]['messages'])


def test_logged_neohorse_batch_accepts_file_id_alias_and_preserves_both_calls():
    tools = [
        {"type": "function", "function": {"name": "search_knowledge", "parameters": {
            "type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        }}},
        {"type": "function", "function": {"name": "read_uploaded_file", "parameters": {
            "type": "object", "properties": {"attachment_id": {"type": "integer"},
                "start_chunk": {"type": "integer"}, "max_chunks": {"type": "integer"}},
            "required": ["attachment_id"],
        }}},
    ]
    content = '''<tool_call>
<function=search_knowledge>
<parameter=query>
SERGDATA Workbench highlightCode function markdown render code block span tok-string dark theme CSS
</parameter>
<parameter=limit>
10
</parameter>
</function>
</tool_call>
<tool_call>
<function=read_uploaded_file>
<parameter=file_id>
5
</parameter>
</function>
</tool_call>'''
    calls, detected, error = parse_text_tool_calls(content, tools)
    assert detected is True
    assert error is None
    assert [call.function.name for call in calls] == ["search_knowledge", "read_uploaded_file"]
    assert calls[1].function.arguments == '{"attachment_id": 5}'


def test_invalid_sibling_does_not_discard_valid_neohorse_tool_call():
    tools = _tools() + [{"type": "function", "function": {"name": "search_knowledge", "parameters": {
        "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]
    }}}]
    content = '''<tool_call><function=search_knowledge><parameter=query>needle</parameter></function></tool_call>
<tool_call><function=missing_tool><parameter=x>1</parameter></function></tool_call>'''
    calls, detected, error = parse_text_tool_calls(content, tools)
    assert detected is True
    assert len(calls) == 1
    assert calls[0].function.name == "search_knowledge"
    assert "Вызов #2" in error and "Неизвестный инструмент" in error


def test_text_tool_transport_markup_is_removed_before_next_model_round():
    from workbench.tool_call_adapter import strip_text_tool_call_markup
    raw = 'Поиск выполняю. <tool_call><function=search_knowledge><parameter=query>x</parameter></function></tool_call>'
    assert strip_text_tool_call_markup(raw) == 'Поиск выполняю.'
    assert strip_text_tool_call_markup('<tool_call><function=search_knowledge>') == ''


def test_agent_executes_valid_call_from_partial_batch_then_finishes(monkeypatch):
    import asyncio
    import sys
    from types import ModuleType, SimpleNamespace
    from unittest.mock import AsyncMock
    if 'openai' not in sys.modules:
        openai_stub = ModuleType('openai'); openai_stub.AsyncOpenAI = object; sys.modules['openai'] = openai_stub
    if 'mcp' not in sys.modules:
        mcp_stub = ModuleType('mcp'); mcp_stub.ClientSession = object; mcp_stub.StdioServerParameters = object
        mcp_client_stub = ModuleType('mcp.client'); mcp_stdio_stub = ModuleType('mcp.client.stdio')
        mcp_stdio_stub.stdio_client = lambda *a, **k: None
        sys.modules.update({'mcp': mcp_stub, 'mcp.client': mcp_client_stub, 'mcp.client.stdio': mcp_stdio_stub})
    from workbench.agent import Agent

    first = SimpleNamespace(content='''<tool_call><function=list_uploaded_files></function></tool_call>
<tool_call><function=missing_tool><parameter=x>1</parameter></function></tool_call>''', tool_calls=None)
    second = SimpleNamespace(content='Результат найден, анализ завершён.', tool_calls=None)
    responses = [first, second]
    sent = []
    class FakeCompletions:
        async def create(self, **kwargs):
            sent.append(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=responses.pop(0))], usage=None)
    class FakeLLM:
        chat = SimpleNamespace(completions=FakeCompletions())
        def with_options(self, **kwargs): return self
    class FakeStore:
        def get_app_settings(self):
            return {'max_tool_rounds': 4, 'max_tool_calls': 8, 'request_timeout': 30, 'temperature': 0}
        def project_for_branch(self, bid): return {'id': 1, 'root': '/active'}
        def task_for_branch(self, bid): return {'id': 1}
        def projects(self): return [{'id': 1, 'root': '/active'}]
        def attachment_payload(self, *args): return [], ''
        def add_message(self, *args, **kwargs): return 1
        def record_llm_call(self, *args, **kwargs): pass
        def pending(self, bid): return []
    agent = object.__new__(Agent)
    agent.store = FakeStore(); agent.cfg = SimpleNamespace(lm_model='test-model', max_tool_rounds=4)
    agent.llm = FakeLLM(); agent.kbtools = {}; agent.runtime_settings = {}; agent.last_model = 'test-model'
    agent._prepare_context = AsyncMock(return_value=([{'role': 'system', 'content': 'test'}], {'summary_prompt_tokens': 0, 'summary_completion_tokens': 0}))
    agent._compact_runtime = AsyncMock(side_effect=lambda msgs, *a: (msgs, {}, 0, 0))
    agent.prompt_metrics = lambda *args: {}
    agent._set_activity = lambda *args: None
    executed = []
    async def fake_tool(name, args, bid):
        executed.append((name, args))
        return 'knowledge result'
    agent.tool = fake_tool
    result = asyncio.run(agent.chat(7, 'Проведи поиск', []))
    assert executed == [('list_uploaded_files', {})]
    assert result['answer'] == 'Результат найден, анализ завершён.'
    assert len(sent) == 2
    correction = '\n'.join(str(m.get('content', '')) for m in sent[1]['messages'])
    assert 'ЧАСТИЧНЫЙ РЕЗУЛЬТАТ TOOL-CALL ADAPTER' in correction
    assert 'missing_tool' in correction
    assert '<tool_call>' not in correction


def test_agent_executes_exact_two_call_batch_from_user_log(monkeypatch):
    import asyncio
    import sys
    from types import ModuleType, SimpleNamespace
    from unittest.mock import AsyncMock
    if 'openai' not in sys.modules:
        openai_stub = ModuleType('openai'); openai_stub.AsyncOpenAI = object; sys.modules['openai'] = openai_stub
    if 'mcp' not in sys.modules:
        mcp_stub = ModuleType('mcp'); mcp_stub.ClientSession = object; mcp_stub.StdioServerParameters = object
        mcp_client_stub = ModuleType('mcp.client'); mcp_stdio_stub = ModuleType('mcp.client.stdio')
        mcp_stdio_stub.stdio_client = lambda *a, **k: None
        sys.modules.update({'mcp': mcp_stub, 'mcp.client': mcp_client_stub, 'mcp.client.stdio': mcp_stdio_stub})
    from workbench.agent import Agent

    batch = '''<tool_call>
<function=search_knowledge>
<parameter=query>
SERGDATA Workbench highlightCode function markdown render code block span tok-string dark theme CSS
</parameter>
<parameter=limit>
10
</parameter>
</function>
</tool_call>
<tool_call>
<function=read_uploaded_file>
<parameter=file_id>
5
</parameter>
</function>
</tool_call>'''
    responses = [
        SimpleNamespace(content=batch, tool_calls=None),
        SimpleNamespace(content='Анализ завершён.', tool_calls=None),
    ]
    class FakeCompletions:
        async def create(self, **kwargs):
            return SimpleNamespace(choices=[SimpleNamespace(message=responses.pop(0))], usage=None)
    class FakeLLM:
        chat = SimpleNamespace(completions=FakeCompletions())
        def with_options(self, **kwargs): return self
    class FakeStore:
        def get_app_settings(self): return {'max_tool_rounds': 4, 'max_tool_calls': 8, 'request_timeout': 30, 'temperature': 0}
        def project_for_branch(self, bid): return {'id': 1, 'root': '/active'}
        def task_for_branch(self, bid): return {'id': 1}
        def projects(self): return [{'id': 1, 'root': '/active'}]
        def attachment_payload(self, *args): return [], ''
        def add_message(self, *args, **kwargs): return 1
        def record_llm_call(self, *args, **kwargs): pass
        def pending(self, bid): return []
    agent = object.__new__(Agent)
    agent.store = FakeStore(); agent.cfg = SimpleNamespace(lm_model='test-model', max_tool_rounds=4)
    agent.llm = FakeLLM(); agent.kbtools = {
        'search_knowledge': SimpleNamespace(input_schema={
            'type': 'object', 'properties': {'query': {'type': 'string'}, 'limit': {'type': 'integer'}},
            'required': ['query']}, description='Search knowledge')
    }
    agent.runtime_settings = {}; agent.last_model = 'test-model'
    agent._prepare_context = AsyncMock(return_value=([{'role': 'system', 'content': 'test'}], {'summary_prompt_tokens': 0, 'summary_completion_tokens': 0}))
    agent._compact_runtime = AsyncMock(side_effect=lambda msgs, *a: (msgs, {}, 0, 0))
    agent.prompt_metrics = lambda *args: {}
    agent._set_activity = lambda *args: None
    executed = []
    async def fake_tool(name, args, bid):
        executed.append((name, args))
        return f'{name}: OK'
    agent.tool = fake_tool

    result = asyncio.run(agent.chat(7, 'Проведи исследование', []))
    assert executed == [
        ('search_knowledge', {'query': 'SERGDATA Workbench highlightCode function markdown render code block span tok-string dark theme CSS', 'limit': 10}),
        ('read_uploaded_file', {'attachment_id': 5}),
    ]
    assert result['answer'] == 'Анализ завершён.'
    assert result['tool_calls'] == 2


def test_invalid_text_call_is_not_shown_as_final_transport_markup():
    import asyncio
    import sys
    from types import ModuleType, SimpleNamespace
    from unittest.mock import AsyncMock
    if 'openai' not in sys.modules:
        openai_stub = ModuleType('openai'); openai_stub.AsyncOpenAI = object; sys.modules['openai'] = openai_stub
    if 'mcp' not in sys.modules:
        mcp_stub = ModuleType('mcp'); mcp_stub.ClientSession = object; mcp_stub.StdioServerParameters = object
        mcp_client_stub = ModuleType('mcp.client'); mcp_stdio_stub = ModuleType('mcp.client.stdio')
        mcp_stdio_stub.stdio_client = lambda *a, **k: None
        sys.modules.update({'mcp': mcp_stub, 'mcp.client': mcp_client_stub, 'mcp.client.stdio': mcp_stdio_stub})
    from workbench.agent import Agent

    response = SimpleNamespace(content='<tool_call><function=not_registered><parameter=x>1</parameter></function></tool_call>', tool_calls=None)
    class FakeCompletions:
        async def create(self, **kwargs): return SimpleNamespace(choices=[SimpleNamespace(message=response)], usage=None)
    class FakeLLM:
        chat = SimpleNamespace(completions=FakeCompletions())
        def with_options(self, **kwargs): return self
    class FakeStore:
        def get_app_settings(self): return {'max_tool_rounds': 1, 'max_tool_calls': 8, 'request_timeout': 30, 'temperature': 0}
        def project_for_branch(self, bid): return {'id': 1, 'root': '/active'}
        def task_for_branch(self, bid): return {'id': 1}
        def projects(self): return [{'id': 1, 'root': '/active'}]
        def attachment_payload(self, *args): return [], ''
        def add_message(self, *args, **kwargs): return 1
        def record_llm_call(self, *args, **kwargs): pass
        def pending(self, bid): return []
    agent = object.__new__(Agent)
    agent.store = FakeStore(); agent.cfg = SimpleNamespace(lm_model='test-model', max_tool_rounds=1)
    agent.llm = FakeLLM(); agent.kbtools = {}; agent.runtime_settings = {}; agent.last_model = 'test-model'
    agent._prepare_context = AsyncMock(return_value=([{'role': 'system', 'content': 'test'}], {'summary_prompt_tokens': 0, 'summary_completion_tokens': 0}))
    agent._compact_runtime = AsyncMock(side_effect=lambda msgs, *a: (msgs, {}, 0, 0))
    agent.prompt_metrics = lambda *args: {}
    agent._set_activity = lambda *args: None
    result = asyncio.run(agent.chat(7, 'Проверь вызовы инструментов', []))
    assert result['tool_error'] is True
    assert 'Неизвестный инструмент' in result['answer']
    assert '<tool_call>' not in result['answer']



def test_parse_backslash_wrapped_neohorse_tags_from_latest_workbench_log():
    tools = [{"type": "function", "function": {"name": "search_knowledge", "parameters": {
        "type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
        "required": ["query"],
    }}}]
    # Literal delimiter form visible in the user's 08:55 Workbench output.
    content = "\\<tool_call>\\\n\\<function=search_knowledge>\\\n\\<parameter=query>\\\nSERGDATA Workbench highlightCode markdown render code block\n\\</parameter>\\\n\\<parameter=limit>\\\n10\n\\</parameter>\\\n\\</function>\\\n\\</tool_call>\\"
    calls, detected, error = parse_text_tool_calls(content, tools)
    assert detected is True
    assert error is None
    assert len(calls) == 1
    assert calls[0].function.name == "search_knowledge"
    assert calls[0].function.arguments == '{"query": "SERGDATA Workbench highlightCode markdown render code block", "limit": 10}'


def test_escaped_tool_call_markup_is_removed_before_model_context_reuse():
    from workbench.tool_call_adapter import strip_text_tool_call_markup
    content = "Начинаю поиск.\n\\<tool_call>\\\n\\<function=search_knowledge>\\\n\\<parameter=query>\\needle\\</parameter>\\\n\\</function>\\\n\\</tool_call>\\"
    assert strip_text_tool_call_markup(content) == "Начинаю поиск."


def test_escaped_incomplete_tool_call_is_detected_as_adapter_error():
    content = "\\<tool_call>\\\n\\<function=search_knowledge>\\"
    tools = [{"type": "function", "function": {"name": "search_knowledge", "parameters": {
        "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]
    }}}]
    calls, detected, error = parse_text_tool_calls(content, tools)
    assert calls == []
    assert detected is True
    assert error and "незавершённый" in error



def test_agent_executes_escaped_two_call_batch_and_continues_to_answer():
    import asyncio
    import re
    import sys
    from types import ModuleType, SimpleNamespace
    from unittest.mock import AsyncMock
    if 'openai' not in sys.modules:
        openai_stub = ModuleType('openai'); openai_stub.AsyncOpenAI = object; sys.modules['openai'] = openai_stub
    if 'mcp' not in sys.modules:
        mcp_stub = ModuleType('mcp'); mcp_stub.ClientSession = object; mcp_stub.StdioServerParameters = object
        mcp_client_stub = ModuleType('mcp.client'); mcp_stdio_stub = ModuleType('mcp.client.stdio')
        mcp_stdio_stub.stdio_client = lambda *a, **k: None
        sys.modules.update({'mcp': mcp_stub, 'mcp.client': mcp_client_stub, 'mcp.client.stdio': mcp_stdio_stub})
    from workbench.agent import Agent

    plain_batch = '''<tool_call>
<function=search_knowledge>
<parameter=query>
SERGDATA Workbench highlightCode function markdown render code block span tok-string dark theme CSS
</parameter>
<parameter=limit>
10
</parameter>
</function>
</tool_call>
<tool_call>
<function=read_uploaded_file>
<parameter=file_id>
5
</parameter>
</function>
</tool_call>'''
    # Reproduce the literal backslash-wrapped control tags shown in the user's screenshot.
    batch = re.sub(
        r"</?(?:tool_call|function(?:=[A-Za-z_][A-Za-z0-9_]*)?|parameter(?:=[A-Za-z_][A-Za-z0-9_]*)?)>",
        lambda match: "\\" + match.group(0) + "\\",
        plain_batch,
    )
    responses = [
        SimpleNamespace(content=batch, tool_calls=None),
        SimpleNamespace(content='Расследование продолжено после выполнения инструментов.', tool_calls=None),
    ]
    sent = []
    class FakeCompletions:
        async def create(self, **kwargs):
            sent.append(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=responses.pop(0))], usage=None)
    class FakeLLM:
        chat = SimpleNamespace(completions=FakeCompletions())
        def with_options(self, **kwargs): return self
    class FakeStore:
        def get_app_settings(self): return {'max_tool_rounds': 4, 'max_tool_calls': 8, 'request_timeout': 30, 'temperature': 0}
        def project_for_branch(self, bid): return {'id': 1, 'root': '/active'}
        def task_for_branch(self, bid): return {'id': 1}
        def projects(self): return [{'id': 1, 'root': '/active'}]
        def attachment_payload(self, *args): return [], ''
        def add_message(self, *args, **kwargs): return 1
        def record_llm_call(self, *args, **kwargs): pass
        def pending(self, bid): return []
    agent = object.__new__(Agent)
    agent.store = FakeStore(); agent.cfg = SimpleNamespace(lm_model='test-model', max_tool_rounds=4)
    agent.llm = FakeLLM(); agent.kbtools = {
        'search_knowledge': SimpleNamespace(input_schema={
            'type': 'object', 'properties': {'query': {'type': 'string'}, 'limit': {'type': 'integer'}},
            'required': ['query']}, description='Search knowledge')
    }
    agent.runtime_settings = {}; agent.last_model = 'test-model'
    agent._prepare_context = AsyncMock(return_value=([{'role': 'system', 'content': 'test'}], {'summary_prompt_tokens': 0, 'summary_completion_tokens': 0}))
    agent._compact_runtime = AsyncMock(side_effect=lambda msgs, *a: (msgs, {}, 0, 0))
    agent.prompt_metrics = lambda *args: {}
    agent._set_activity = lambda *args: None
    executed = []
    async def fake_tool(name, args, bid):
        executed.append((name, args))
        return f'{name}: OK'
    agent.tool = fake_tool

    result = asyncio.run(agent.chat(7, 'Проведи расследование', []))
    assert executed == [
        ('search_knowledge', {'query': 'SERGDATA Workbench highlightCode function markdown render code block span tok-string dark theme CSS', 'limit': 10}),
        ('read_uploaded_file', {'attachment_id': 5}),
    ]
    assert result['answer'] == 'Расследование продолжено после выполнения инструментов.'
    assert result['tool_calls'] == 2
    assert len(sent) == 2
    second_history = sent[1]['messages']
    assert not any('\\<tool_call>' in str(message.get('content', '')) for message in second_history)
    assert not any('<tool_call>' in str(message.get('content', '')) for message in second_history)
