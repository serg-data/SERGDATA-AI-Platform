from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_checkpoint_resume_is_explicit_startup_briefing_and_contains_original_request():
    source = (ROOT / 'workbench' / 'agent.py').read_text(encoding='utf-8')
    assert '[WORKBENCH EXECUTION CHECKPOINT — ОБЯЗАТЕЛЬНАЯ СТАРТОВАЯ СВОДКА ПРЕДЫДУЩЕЙ РАБОТЫ]' in source
    assert 'last_user_request' in source
    assert 'Перед выполнением нового запроса сначала прочитай эту сводку целиком' in source
    assert 'recent_tool_events' in source
    assert 'продолжай с next_step' in source.lower()
    assert 'completed_work_reference' in source
    assert 'не возобновляй её шаги автоматически' in source.lower()


def test_lm_studio_bad_request_diagnostic_logs_only_structured_error_fields():
    source = (ROOT / 'main.py').read_text(encoding='utf-8')
    assert 'upstream_error=%s' in source
    assert "('code', 'type', 'message')" in source
    assert 'submitted prompt, tool arguments, request headers' in source
    assert '[:800]' in source


def test_checkpoint_briefing_is_merged_into_single_leading_system_message():
    source = (ROOT / 'workbench' / 'agent.py').read_text(encoding='utf-8')
    assert 'msgs[0]["content"] = str(msgs[0].get("content") or "") + "\\n\\n" + checkpoint_briefing' in source
    assert 'msgs.insert(0, {"role": "system", "content": checkpoint_briefing})' in source
    assert 'msgs.append({"role": "system", "content": (' not in source
    assert 'causes HTTP 400 on affected templates' in source


def test_lm_studio_diagnostic_falls_back_to_exception_message_when_body_is_empty():
    source = (ROOT / 'main.py').read_text(encoding='utf-8')
    assert 'getattr(e, "message", None) or str(e)' in source
    assert 'never log the submitted request' in source
