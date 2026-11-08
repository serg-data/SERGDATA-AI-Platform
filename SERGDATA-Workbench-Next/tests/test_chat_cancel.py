from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_backend_exposes_branch_scoped_chat_cancellation():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "@app.post('/api/chat/cancel')" in source
    assert "task.cancel()" in source
    assert "except asyncio.CancelledError:" in source
    assert "Генерация остановлена пользователем." in source


def test_cancelled_chat_task_is_removed_from_registry():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "CHAT_TASKS[data.branch_id]=task" in source
    assert "if CHAT_TASKS.get(data.branch_id) is task:" in source
    assert "CHAT_TASKS.pop(data.branch_id,None)" in source


def test_frontend_button_switches_to_stop_and_calls_cancel_endpoint():
    source = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "if(busy){await stopChat();return}" in source
    assert 'function renderChatComputeButton(stopping=false)' in source
    assert 'stageLabel' in source
    assert 'Остановить генерацию модели' in source
    assert "/api/chat/cancel?branch_id=" in source
    assert "await loadExecutionQueue()" in source


def test_backend_exposes_active_chat_status_for_reloaded_browser():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "@app.get('/api/chat/status')" in source
    assert "'active':active" in source
    assert "task and not task.done()" in source


def test_cancel_waits_for_chat_handler_to_release_branch_lock():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    cancel = source[source.index("@app.post('/api/chat/cancel')"):source.index("@app.get('/api/branches/{bid}/memory')")]
    assert "await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), timeout=8)" in cancel
    assert "'active':active" in cancel


def test_frontend_restores_stop_button_from_server_state():
    source = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "async function syncChatStatus" in source
    assert "'/api/chat/status?branch_id='" in source or "`/api/chat/status?branch_id=" in source
    assert "await syncChatStatus(activeBranch)" in source
    assert "if(stillActive){" in source and "preserveActive=true" in source
    assert "setChatUiActive(true,branch)" in source
