from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_prepare_context_does_not_summarize_by_message_count_alone():
    source = (ROOT / "workbench" / "agent.py").read_text(encoding="utf-8")
    start = source.index("async def _prepare_context(")
    end = source.index("async def _compact_runtime(", start)
    block = source[start:end]
    assert "len(fresh) >= 14" not in block
    assert "if prepare_tokens > budget:" in block


def test_runtime_compaction_has_distinct_activity_and_replaces_old_summary():
    source = (ROOT / "workbench" / "agent.py").read_text(encoding="utf-8")
    start = source.index("async def _compact_runtime(")
    end = source.index("async def chat(", start)
    block = source[start:end]
    assert '"Сжатие контекста текущего запроса"' in block
    assert '"phase": "compacting"' in block
    assert '"phase": "compacted"' in block
    assert '"after_tokens": int(after_tokens)' in block
    assert "[WORKBENCH_RUNTIME_MEMORY_BEGIN]" in block
    assert "[WORKBENCH_RUNTIME_MEMORY_END]" in block
    assert "RUNTIME_COMPACTION" in block


def test_model_generation_status_is_set_after_runtime_compaction():
    source = (ROOT / "workbench" / "agent.py").read_text(encoding="utf-8")
    compact = source.index("msgs, runtime_memory, cp, cc = await self._compact_runtime(")
    generation = source.index('self._set_activity(bid, "model_generation"', compact)
    assert generation > compact


def test_activity_exposes_runtime_context_without_replacing_history_stats():
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    app_source = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "'context': dict(context) if isinstance(context, dict) else previous.get('context')" in main_source
    assert "renderRuntimeContextStatus(chatActivity)" in app_source
    assert "Текущий запрос:" in app_source
    assert "after_tokens" in app_source


def test_runtime_context_is_measured_after_compaction_before_llm_request():
    source = (ROOT / "workbench" / "agent.py").read_text(encoding="utf-8")
    compact = source.index("msgs, runtime_memory, cp, cc = await self._compact_runtime(")
    preflight = source.index("preflight = await asyncio.to_thread(self.prompt_metrics, msgs, tools, model)", compact)
    activity = source.index('"phase": "ready"', preflight)
    request = source.index("response = await llm.chat.completions.create(", activity)
    assert compact < preflight < activity < request


def test_frontend_cache_version_is_bumped_for_runtime_context_patch():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert "app.js?v=20261109-runtime-context-live-v1" in html
