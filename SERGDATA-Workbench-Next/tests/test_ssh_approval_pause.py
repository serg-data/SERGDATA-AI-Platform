from pathlib import Path


def test_agent_stops_after_ssh_command_is_queued():
    source = (Path(__file__).resolve().parents[1] / "workbench" / "agent.py").read_text(encoding="utf-8")
    marker = "if name in {'ssh_run_command', 'ssh_run_profile_command', 'execute_powershell'} and queued_match:"
    assert marker in source
    block = source[source.index(marker):source.index("if stop_reason:", source.index(marker))]
    assert "stop_reason =" in block
    assert "Не создавай обход" in block
    assert "break" not in block


def test_agent_stops_after_local_powershell_command_is_queued():
    source = (Path(__file__).resolve().parents[1] / "workbench" / "agent.py").read_text(encoding="utf-8")
    marker = "if name in {'ssh_run_command', 'ssh_run_profile_command', 'execute_powershell'} and queued_match:"
    assert marker in source
    block = source[source.index(marker):source.index("if stop_reason:", source.index(marker))]
    assert "if name == 'execute_powershell':" in block
    assert "Не выполняй её другим способом" in block
    assert "явного подтверждения пользователя" in block
