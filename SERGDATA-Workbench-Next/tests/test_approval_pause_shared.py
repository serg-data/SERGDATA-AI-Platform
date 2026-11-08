from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_all_approval_gated_command_tools_stop_the_agent_turn():
    source = (ROOT / "workbench" / "agent.py").read_text(encoding="utf-8")
    marker = "if name in {'ssh_run_command', 'ssh_run_profile_command', 'execute_powershell'} and queued_match:"
    assert marker in source
    block = source[source.index(marker):source.index("if stop_reason:", source.index(marker))]
    assert "stop_reason =" in block
    assert "execute_powershell" in block
    assert "ssh_run_command" in block
    assert "явного подтверждения пользователя" in block
    assert "Не выполняй её другим способом" in block
    assert "Не создавай обход" in block
    assert "break" not in block


def test_waiting_approval_state_is_preserved_after_agent_turn():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "if get_chat_activity(data.branch_id).get('stage') not in {'waiting_input','waiting_approval'}:" in source
    assert "return {'ok':True,'branch_id':branch_id,'active':active,'activity':get_chat_activity(branch_id)}" in source
