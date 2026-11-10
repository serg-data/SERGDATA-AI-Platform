import asyncio
import sys
from pathlib import Path
from types import ModuleType

# Lightweight stubs for optional runtime packages not needed by these unit tests.
if "openai" not in sys.modules:
    openai = ModuleType("openai")
    openai.AsyncOpenAI = object
    sys.modules["openai"] = openai
if "mcp" not in sys.modules:
    mcp = ModuleType("mcp")
    mcp.ClientSession = object
    mcp.StdioServerParameters = object
    client = ModuleType("mcp.client")
    stdio = ModuleType("mcp.client.stdio")
    stdio.stdio_client = lambda *args, **kwargs: None
    sys.modules.update({"mcp": mcp, "mcp.client": client, "mcp.client.stdio": stdio})

from workbench.agent import Agent, ToolAccessDeniedResult
from workbench.db import Store


def make_agent(tmp_path, contents):
    store = Store(Path(tmp_path) / "test.sqlite3")
    pid = store.create_project("test", str(tmp_path))
    tid, bid = store.create_task(pid, "task")
    aid = store.add_attachment(
        project_id=pid, task_id=tid, branch_id=bid,
        original_name="agent.py", stored_name="agent.py",
        media_type="text/plain", kind="text",
        size=sum(map(len, contents)), sha256="test", note="",
        chunks=[{"source_path":"agent.py", "chunk_index":i, "content":x}
                for i, x in enumerate(contents)],
    )
    agent = object.__new__(Agent)
    agent.store = store
    return agent, aid, bid


def test_all_23_chunks_read_without_gaps_or_duplicates(tmp_path):
    source = [f"CHUNK-{i:02d}-" + "x" * 100 for i in range(23)]
    agent, aid, bid = make_agent(tmp_path, source)
    cursor = 0
    seen = []
    while True:
        text = asyncio.run(agent.tool("read_uploaded_file", {
            "attachment_id": aid, "start_chunk": cursor, "max_chunks": 6
        }, bid))
        seen.extend(line.split(";", 1)[0] for line in text.splitlines() if line.startswith("[ЧАСТЬ "))
        if "ПОЛНОСТЬЮ ПРОЧИТАН" in text:
            break
        marker = "ТОЧНОЕ ЗНАЧЕНИЕ start_chunk ДЛЯ СЛЕДУЮЩЕГО ВЫЗОВА (с нуля): "
        cursor = int(text.split(marker, 1)[1].splitlines()[0])
    assert seen == [f"[ЧАСТЬ {i}" for i in range(1, 24)]


def test_out_of_range_empty_result_does_not_raise_typeerror(tmp_path):
    agent, aid, bid = make_agent(tmp_path, ["one", "two"])
    text = asyncio.run(agent.tool("read_uploaded_file", {
        "attachment_id": aid, "start_chunk": 99, "max_chunks": 6
    }, bid))
    assert ("Не удалось прочитать диапазон" in text or "уже достиг конца" in text)
    assert "TypeError" not in text


def test_document_with_denial_phrases_is_plain_content(tmp_path):
    payload = "Файл не найден или путь находится вне разрешённых папок\nЗапрещён выход за пределы\nДоступ к потенциально секретному файлу запрещён\nДоступ к другому проекту не разрешён\nне зарегистрирован как активный проект Workbench"
    agent, aid, bid = make_agent(tmp_path, [payload])
    result = asyncio.run(agent.tool("read_uploaded_file", {"attachment_id": aid}, bid))
    assert not isinstance(result, ToolAccessDeniedResult)
    assert payload in result


def test_reader_result_is_allowed_over_generic_7000_limit(tmp_path):
    chunks = [f"PART-{i}-" + "z" * 4990 for i in range(6)]
    agent, aid, bid = make_agent(tmp_path, chunks)
    result = asyncio.run(agent.tool("read_uploaded_file", {
        "attachment_id": aid, "start_chunk": 0, "max_chunks": 6
    }, bid))
    assert len(result) > 7000
    assert all(f"PART-{i}-" in result for i in range(6))


def test_model_display_part_number_is_corrected_to_zero_based_cursor():
    from workbench.agent import _correct_uploaded_read_cursor, _remember_uploaded_read_cursor

    cursors = {}
    _remember_uploaded_read_cursor(
        "СТАТУС ПОКРЫТИЯ: ЧАСТИЧНО ПРОЧИТАН\\n"
        "ТОЧНОЕ ЗНАЧЕНИЕ start_chunk ДЛЯ СЛЕДУЮЩЕГО ВЫЗОВА (с нуля): 6",
        8,
        cursors,
    )
    corrected, notice = _correct_uploaded_read_cursor(
        {"attachment_id": 8, "start_chunk": 7, "max_chunks": 6}, cursors
    )
    assert corrected["start_chunk"] == 6
    assert "скорректирован с 7 на 6" in notice


def test_cursor_guard_does_not_change_unrelated_or_initial_reads():
    from workbench.agent import _correct_uploaded_read_cursor

    cursors = {8: 6}
    initial, initial_notice = _correct_uploaded_read_cursor(
        {"attachment_id": 9, "start_chunk": 0}, cursors
    )
    assert initial["start_chunk"] == 0
    assert initial_notice == ""
    correct, correct_notice = _correct_uploaded_read_cursor(
        {"attachment_id": 8, "start_chunk": 6}, cursors
    )
    assert correct["start_chunk"] == 6
    assert correct_notice == ""



def test_runtime_compaction_keeps_single_system_message_and_replaces_memory():
    import sys
    from types import ModuleType
    from unittest.mock import AsyncMock

    if "openai" not in sys.modules:
        m = ModuleType("openai"); m.AsyncOpenAI = object; sys.modules["openai"] = m
    if "mcp" not in sys.modules:
        m = ModuleType("mcp"); m.ClientSession = object; m.StdioServerParameters = object
        c = ModuleType("mcp.client"); st = ModuleType("mcp.client.stdio"); st.stdio_client = lambda *a, **k: None
        sys.modules.update({"mcp": m, "mcp.client": c, "mcp.client.stdio": st})
    from workbench.agent import Agent

    agent = object.__new__(Agent)
    agent.effective_context_limit = AsyncMock(return_value=(8192, None, None))
    agent.prompt_metrics = lambda *args: {"estimated_prompt_tokens": 100000}
    summaries = iter(["Старая сводка", "Новая сводка"])
    async def summarize(*args, **kwargs):
        return next(summaries), 1, 1
    agent._summarize = summarize

    messages = [
        {"role": "system", "content": "Исходные системные инструкции."},
        {"role": "user", "content": "Запрос пользователя."},
        {"role": "assistant", "content": "Шаг."},
        {"role": "tool", "content": "Результат инструмента."},
        {"role": "user", "content": "Продолжай."},
    ]
    first, memory, _, _ = asyncio.run(agent._compact_runtime(messages, [], "model", 1, "", 1))
    second_input = [
        first[0], first[1],
        {"role": "assistant", "content": "Ещё шаг."},
        {"role": "tool", "content": "Ещё результат."},
        {"role": "user", "content": "Продолжай дальше."},
    ]
    second, memory2, _, _ = asyncio.run(
        agent._compact_runtime(second_input, [], "model", 1, memory, 2)
    )
    systems = [m for m in second if m.get("role") == "system"]
    assert len(systems) == 1
    assert systems[0]["content"].startswith("Исходные системные инструкции.")
    assert "Старая сводка" not in systems[0]["content"]
    assert "Новая сводка" in systems[0]["content"]
    assert systems[0]["content"].count("[WORKBENCH_RUNTIME_MEMORY_BEGIN]") == 1
    assert second[-1] == {"role": "user", "content": "Продолжай дальше."}
    assert memory2 == "Новая сводка"
