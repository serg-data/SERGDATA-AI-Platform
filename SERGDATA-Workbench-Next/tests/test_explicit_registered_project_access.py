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


def test_only_exactly_named_registered_external_root_is_granted(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    active_root = tmp_path / 'active'
    target_root = tmp_path / 'target project'
    active_root.mkdir()
    target_root.mkdir()
    active_id = store.ensure_project('Active', str(active_root))['id']
    target_id = store.ensure_project('Target', str(target_root))['id']
    projects = store.projects()

    explicit = _explicit_external_project_roots(
        f'Проверь исходники в `{target_root}`', projects, active_id)
    assert explicit == (str(target_root),)
    assert _explicit_external_project_roots('Проверь другой проект', projects, active_id) == ()
    assert _explicit_external_project_roots(f'Путь похож: {target_root}ish', projects, active_id) == ()
    assert _explicit_external_project_roots(f'Проверь только папку {target_root / "src"}', projects, active_id) == ()


def test_registered_project_read_is_read_only_and_confined(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    active_root = tmp_path / 'active'
    target_root = tmp_path / 'target'
    active_root.mkdir(); target_root.mkdir()
    (target_root / 'src').mkdir()
    (target_root / 'src' / 'app.py').write_text('print("safe")\n', encoding='utf-8')
    (tmp_path / 'outside.txt').write_text('secret outside', encoding='utf-8')
    store.ensure_project('Active', str(active_root))
    store.ensure_project('Target', str(target_root))

    agent = object.__new__(Agent)
    agent.store = store
    bid = 1
    denied = __import__('asyncio').run(agent.tool(
        'read_registered_project_file', {'root': str(target_root), 'path': 'src/app.py'}, bid))
    assert 'не разрешён' in denied

    listing = __import__('asyncio').run(agent.tool(
        'list_registered_project_files', {'root': str(target_root), 'path': 'src'}, bid,
        authorized_external_roots=(str(target_root),)))
    assert 'src/app.py' in listing
    allowed = __import__('asyncio').run(agent.tool(
        'read_registered_project_file', {'root': str(target_root), 'path': 'src/app.py'}, bid,
        authorized_external_roots=(str(target_root),)))
    assert 'print("safe")' in allowed
    with pytest.raises(ValueError, match='Запрещён выход за пределы папки проекта'):
        __import__('asyncio').run(agent.tool(
            'read_registered_project_file', {'root': str(target_root), 'path': '../outside.txt'}, bid,
            authorized_external_roots=(str(target_root),)))


def test_registered_project_file_tool_is_not_a_write_or_execution_capability():
    agent = object.__new__(Agent)
    agent.kbtools = {}
    names = {item['function']['name'] for item in agent.specs()}
    assert 'list_registered_project_files' in names
    assert 'read_registered_project_file' in names
    assert 'write_registered_project_file' not in names
    assert 'execute_registered_project_command' not in names
