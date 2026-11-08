from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_chat_send_refreshes_execution_queue_after_agent_response():
    source = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    send_start = source.index("async function send(){")
    send_end = source.index("\n}\nfunction renderAttachmentChips", send_start)
    send_body = source[send_start:send_end]
    assert "await loadPending();await loadExecutionQueue();" in send_body


def test_agent_never_treats_chat_confirmation_as_execution_approval():
    source = (ROOT / "workbench" / "agent.py").read_text(encoding="utf-8")
    assert "текст пользователя в чате вроде" in source
    assert "сообщение «подтверждаю» в чате само по себе не запускает команду" in source.lower()


def test_execution_queue_is_project_scoped_and_includes_origin_labels():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    db_source = (ROOT / "workbench" / "db.py").read_text(encoding="utf-8")
    assert "pending_executions_for_project(int(branch['id']))" in source
    assert "JOIN branches b ON b.id=pe.branch_id" in db_source
    assert "p.name AS project_name" in db_source
    assert "t.title AS task_title" in db_source


def test_queue_refresh_reports_empty_success_and_api_failure_separately():
    source = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "Очередь обновлена · ожидающих команд нет" in source
    assert "Не удалось обновить очередь подтверждений" in source
    assert "Последнее успешное состояние не считается актуальным." in source

def test_queue_polling_refreshes_button_state_while_chat_is_idle():
    source = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "executionQueuePollTimer=setInterval(()=>{if(activeBranch)loadExecutionQueue({silent:true})},2000)" in source
    assert "renderChatComputeButton(false);" in source[source.index("async function loadExecutionQueue"):source.index("function startExecutionQueuePolling")]

def test_queue_refresh_button_shows_user_feedback():
    source = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "addEventListener('click',()=>loadExecutionQueue({silent:false}))" in source


def test_pending_execution_queue_finds_sibling_branch_requests(tmp_path):
    from workbench.db import Store

    store = Store(tmp_path / 'queue.sqlite3')
    project_id = store.ensure_project('Approval project', str(tmp_path))['id']
    task_id, branch_a = store.create_task(project_id, 'Task A')
    task_id_b, branch_b = store.create_task(project_id, 'Task B')
    pending_id = store.add_pending_execution(branch_b, '__SERGDATA_PROFILE_EXEC_V1__{}')

    # The active UI branch may differ from the branch that owns the pending call.
    assert store.pending_executions(branch_a) == []
    rows = store.pending_executions_for_project(project_id)
    assert [row['id'] for row in rows] == [pending_id]
    assert rows[0]['branch_id'] == branch_b
    assert rows[0]['task_title'] == 'Task B'
    assert rows[0]['project_name'] == 'Approval project'


def test_manual_queue_refresh_does_not_fail_silently_when_poll_is_in_flight():
    source = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "if(executionQueuePollBusy){if(!silent)toast('Обновление очереди уже выполняется; дождись результата.');return null;}" in source
