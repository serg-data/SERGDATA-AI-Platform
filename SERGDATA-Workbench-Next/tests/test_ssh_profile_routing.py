from workbench import ssh


def test_find_matching_profile_routes_exact_saved_target():
    profiles = [
        {"id": 2, "name": "SUB", "host": "sub.sergdata.top", "username": "root",
         "port": 2222, "auth_method": "password", "credential_ref": "opaque-ref"}
    ]
    match = ssh.find_matching_profile(profiles, "SUB.SERGDATA.TOP", "root", 2222)
    assert match["id"] == 2
    assert match["auth_method"] == "password"
    assert match["credential_ref"] == "opaque-ref"


def test_find_matching_profile_returns_none_for_unregistered_target():
    assert ssh.find_matching_profile([], "fin.sergdata.top", "root", 2222) is None


def test_find_matching_profile_rejects_ambiguous_profiles():
    profiles = [
        {"id": 1, "host": "sub.sergdata.top", "username": "root", "port": 2222},
        {"id": 2, "host": "SUB.sergdata.top", "username": "ROOT", "port": 2222},
    ]
    try:
        ssh.find_matching_profile(profiles, "sub.sergdata.top", "root", 2222)
    except ssh.SSHError as exc:
        assert "несколько профилей" in str(exc)
    else:
        raise AssertionError("Expected ambiguous profile match to be rejected")



def test_agent_generic_ssh_path_routes_matching_profiles():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "workbench" / "agent.py").read_text(encoding="utf-8")
    assert "find_matching_profile(" in source
    assert "__SERGDATA_PROFILE_EXEC_V1__" in source
    assert "PasswordAuthentication=no" not in source[source.find("if name == 'ssh_run_command'"):source.find("if name == 'execute_powershell'")]
