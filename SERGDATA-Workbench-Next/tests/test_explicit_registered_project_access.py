from pathlib import Path
import pytest
import sys
from types import ModuleType

if 'openai' not in sys.modules:
    openai_stub = ModuleType('openai'); openai_stub.AsyncOpenAI = object; sys.modules['openai'] = openai_stub
if 'mcp' not in sys.modules:
    mcp_stub = ModuleType('mcp'); mcp_stub.ClientSession = object; mcp_stub.StdioServerParameters = object
    mcp_client_stub = ModuleType('mcp.client'); mcp_stdio_stub = ModuleType('mcp.client.stdio')
    mcp_stdio_stub.stdio_client = lambda *a, **k: None
    sys.modules.update({'mcp': mcp_stub, 'mcp.client': mcp_client_stub, 'mcp.client.stdio': mcp_stdio_stub})

from workbench.agent import _explicit_external_project_roots, Agent
from workbench.db import Store


def test_external_folder_requires_explicit_read_consent_and_preserves_full_path(tmp_path):
    external = r'E:\SERGDATA — копия\SERGDATA AI Platform test\SERGDATA-Workbench-Next'
    projects = [{'id': 1, 'root': r'E:\SERGDATA — копия\SERGDATA AI Platform test'}]

    assert _explicit_external_project_roots(
        f'Путь {external} тут находится тестовая папка.', projects, 1
    ) == ()
    assert _explicit_external_project_roots(
        f'Путь {external}. Не даю разрешение на чтение.', projects, 1
    ) == ()
    granted = _explicit_external_project_roots(
        f'Путь {external} тут находится тестовая папка. Даю разрешение на доступ к папке и чтению необходимых файлов.',
        projects,
        1,
    )
    assert granted == (external,)


def test_external_folder_read_is_read_only_confined_and_does_not_require_registration(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    active_root = tmp_path / 'active'
    external_root = tmp_path / 'external folder — copy'
    active_root.mkdir(); external_root.mkdir()
    (external_root / 'src').mkdir()
    (external_root / 'src' / 'app.py').write_text('print("safe")\n', encoding='utf-8')
    (tmp_path / 'outside.txt').write_text('secret outside', encoding='utf-8')
    store.ensure_project('Active', str(active_root))

    agent = object.__new__(Agent)
    agent.store = store
    bid = 1
    no_consent = __import__('asyncio').run(agent.tool(
        'read_registered_project_file', {'root': str(external_root), 'path': 'src/app.py'}, bid))
    assert 'не подтверждён' in no_consent

    # The model's malformed/truncated root is replaced by the sole exact path
    # authorized in the current user message.
    listing = __import__('asyncio').run(agent.tool(
        'list_registered_project_files', {'root': r'E:\SERGDATA', 'path': 'src'}, bid,
        authorized_external_roots=(str(external_root),)))
    assert 'src/app.py' in listing
    allowed = __import__('asyncio').run(agent.tool(
        'read_registered_project_file', {'root': r'E:\SERGDATA', 'path': 'src/app.py'}, bid,
        authorized_external_roots=(str(external_root),)))
    assert 'print("safe")' in allowed
    with pytest.raises(ValueError, match='Запрещён выход за пределы папки проекта'):
        __import__('asyncio').run(agent.tool(
            'read_registered_project_file', {'root': str(external_root), 'path': '../outside.txt'}, bid,
            authorized_external_roots=(str(external_root),)))


def test_multiple_authorized_paths_require_exact_tool_root(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    active_root = tmp_path / 'active'; active_root.mkdir()
    a = tmp_path / 'a'; b = tmp_path / 'b'; a.mkdir(); b.mkdir()
    store.ensure_project('Active', str(active_root))
    agent = object.__new__(Agent); agent.store = store
    denied = __import__('asyncio').run(agent.tool(
        'list_registered_project_files', {'root': str(tmp_path), 'path': '.'}, 1,
        authorized_external_roots=(str(a), str(b))))
    assert 'несколько разрешённых папок' in denied


def test_external_file_tools_remain_read_only_capabilities():
    agent = object.__new__(Agent)
    agent.kbtools = {}
    names = {item['function']['name'] for item in agent.specs()}
    assert 'list_registered_project_files' in names
    assert 'read_registered_project_file' in names
    assert 'write_registered_project_file' not in names
    assert 'execute_registered_project_command' not in names


def test_model_instructions_and_tool_descriptions_allow_unregistered_explicit_folder():
    agent = object.__new__(Agent)
    agent.kbtools = {}
    source = Path(__import__('workbench.agent', fromlist=['__file__']).__file__).read_text(encoding='utf-8')
    assert 'Регистрация в Workbench НЕ требуется' in source
    assert 'Если путь не зарегистрирован или не указан пользователем' not in source
    descriptions = {
        item['function']['name']: item['function']['description']
        for item in agent.specs()
        if item['function']['name'] in {'list_registered_project_files', 'read_registered_project_file'}
    }
    assert 'Регистрация в Workbench не требуется' in descriptions['list_registered_project_files']
    assert 'Регистрация не требуется' in descriptions['read_registered_project_file']
    assert all('только' in value.lower() and 'read-only' in value.lower() for value in descriptions.values())
