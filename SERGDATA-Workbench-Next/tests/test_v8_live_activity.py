from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_chat_status_exposes_live_agent_activity():
    source = (ROOT / 'main.py').read_text(encoding='utf-8')
    assert 'CHAT_ACTIVITY={}' in source
    assert "'activity':get_chat_activity(branch_id)" in source
    assert 'agent.activity_callback=set_chat_activity' in source


def test_agent_marks_model_tool_and_wait_states():
    source = (ROOT / 'workbench' / 'agent.py').read_text(encoding='utf-8')
    for stage in ('model_generation', 'tool_running', 'waiting_input', 'waiting_approval'):
        assert stage in source


def test_pending_user_gates_do_not_trigger_an_extra_model_generation():
    source = (ROOT / 'workbench' / 'agent.py').read_text(encoding='utf-8')
    assert 'Waiting for user approval/input is a workflow state' in source
    assert 'Ожидается ответ в панели защищённого ввода' in source
    assert 'Команда подготовлена и ожидает подтверждения' in source


def test_frontend_polls_transcript_while_agent_request_is_active():
    source = (ROOT / 'static' / 'app.js').read_text(encoding='utf-8')
    assert 'function pollChatActivity(branch)' in source
    assert 'setInterval(()=>pollChatActivity(Number(branch)),1200)' in source
    assert 'if(state.active)await loadMessages()' in source


def test_process_stop_reports_actual_terminal_state():
    source = (ROOT / 'workbench' / 'processes.py').read_text(encoding='utf-8')
    assert 'thread.join(timeout=5)' in source
    assert "current.get('status') in ('completed','failed','stopped')" in source
    main = (ROOT / 'main.py').read_text(encoding='utf-8')
    assert "'active':current.get('status') not in ('completed','failed','stopped')" in main
