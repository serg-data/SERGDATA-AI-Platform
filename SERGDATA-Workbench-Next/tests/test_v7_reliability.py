from pathlib import Path
import threading
import time

from workbench.credential_broker import CredentialBroker


class FakeProtector:
    def protect(self, data):
        return b"wrapped:" + data
    def unprotect(self, data):
        return data[len(b"wrapped:"):]


def test_credential_status_distinguishes_session_and_persistent(tmp_path):
    broker = CredentialBroker(tmp_path / "credentials.dpapi", protector=FakeProtector())
    session_ref = broker.put("session-secret")
    persistent_ref = broker.put("persistent-secret", persist=True)
    assert broker.status(session_ref) == "session"
    assert broker.status(persistent_ref) == "persistent"
    assert broker.status("cred_missing") == "missing"
    broker._persistent[persistent_ref] = "not-valid-base64"
    assert broker.status(persistent_ref) == "session"


def test_cancellation_token_invokes_registered_resource_closer():
    from workbench.processes import CancellationToken
    token = CancellationToken()
    called = []
    token.register(lambda: called.append("closed"))
    token.set()
    assert token.is_set()
    assert called == ["closed"]


def test_callable_process_stop_invokes_registered_close_callback(tmp_path):
    from workbench.processes import ProcessRegistry
    registry = ProcessRegistry()
    closed = threading.Event()

    def work(timeout=10, cancel_event=None):
        cancel_event.register(closed.set)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if cancel_event.is_set():
                return {"status": "stopped", "exit_code": 130, "stdout": "", "stderr": "stopped"}
            time.sleep(0.01)
        return {"status": "completed", "exit_code": 0, "stdout": "done", "stderr": ""}

    jid = registry.start_callable(work, (), Path(tmp_path), display="test cancel")
    time.sleep(0.05)
    assert registry.stop(jid) is True
    assert closed.wait(1)
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        item = registry.get(jid)
        if item and item["status"] == "stopped":
            break
        time.sleep(0.01)
    assert item["status"] == "stopped"


def test_process_stop_refuses_already_finished_job(tmp_path):
    from workbench.processes import ProcessRegistry
    registry = ProcessRegistry()
    jid = registry.start_callable(
        lambda timeout=10, cancel_event=None: {
            "status": "completed", "exit_code": 0, "stdout": "ok", "stderr": ""
        },
        (), Path(tmp_path)
    )
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        item = registry.get(jid)
        if item and item["status"] == "completed":
            break
        time.sleep(0.01)
    assert item["status"] == "completed"
    assert registry.stop(jid) is False


def test_ui_has_wide_vertical_splitter_and_credential_state_labels():
    root = Path(__file__).resolve().parents[1]
    css = (root / "static" / "style.css").read_text(encoding="utf-8")
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    assert "height:14px!important" in css
    assert "cursor:ns-resize!important" in css
    assert "пароль сохранён DPAPI" in js
    assert "пароль доступен до перезапуска" in js
    assert "Останавливаю…" in js


def test_paramiko_authentication_rejection_is_not_reported_as_missing_secret(monkeypatch, tmp_path):
    import sys
    from workbench import ssh
    from workbench.credential_broker import CredentialError

    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "known_hosts").write_text("known", encoding="utf-8")
    monkeypatch.setattr(ssh.Path, "home", lambda: tmp_path)

    class AuthError(Exception):
        pass

    class FakeClient:
        def load_system_host_keys(self): pass
        def load_host_keys(self, path): pass
        def set_missing_host_key_policy(self, policy): pass
        def connect(self, **kwargs):
            assert kwargs["password"] == "right-secret"
            raise AuthError("denied")
        def close(self): pass

    class FakeParamiko:
        SSHClient = FakeClient
        AuthenticationException = AuthError
        class RejectPolicy: pass

    monkeypatch.setitem(sys.modules, "paramiko", FakeParamiko)

    class Broker:
        def resolve(self, ref):
            return "right-secret"

    profile = {"host": "sub.example.test", "username": "root", "port": 2222,
               "auth_method": "password", "credential_ref": "cred_test"}
    try:
        ssh.run_profile_command(profile, "hostname", Broker())
    except ssh.SSHError as exc:
        assert "отклонил пароль" in str(exc)
        assert "CredentialBroker" in str(exc)
    else:
        raise AssertionError("Authentication rejection must be reported")


def test_paramiko_connection_can_be_cancelled_while_connecting(monkeypatch, tmp_path):
    import sys
    import threading
    from workbench import ssh
    from workbench.processes import CancellationToken

    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "known_hosts").write_text("known", encoding="utf-8")
    monkeypatch.setattr(ssh.Path, "home", lambda: tmp_path)
    entered = threading.Event()
    closed = threading.Event()

    class FakeClient:
        def load_system_host_keys(self): pass
        def load_host_keys(self, path): pass
        def set_missing_host_key_policy(self, policy): pass
        def connect(self, **kwargs):
            entered.set()
            if not closed.wait(2):
                raise TimeoutError("connect timeout")
            raise RuntimeError("socket closed")
        def close(self):
            closed.set()

    class FakeParamiko:
        SSHClient = FakeClient
        class RejectPolicy: pass

    monkeypatch.setitem(sys.modules, "paramiko", FakeParamiko)

    class Broker:
        def resolve(self, ref): return "secret"

    token = CancellationToken()
    result = {}
    worker = threading.Thread(target=lambda: result.update(ssh.run_profile_command(
        {"host":"sub.example.test","username":"root","port":2222,
         "auth_method":"password","credential_ref":"cred_test"},
        "sleep 100", Broker(), cancel_event=token)))
    worker.start()
    assert entered.wait(1)
    token.set()
    worker.join(2)
    assert not worker.is_alive()
    assert result["status"] == "stopped"
    assert closed.is_set()



def test_agent_generic_ssh_path_routes_registered_password_profiles():
    root = Path(__file__).resolve().parents[1]
    source = (root / "workbench" / "agent.py").read_text(encoding="utf-8")
    block = source[source.index("if name == 'ssh_run_command':"):source.index("if name == 'execute_powershell':")]
    assert "find_matching_profile(" in block
    assert "__SERGDATA_PROFILE_EXEC_V1__" in block
    assert "self.credentials.exists(profile.get('credential_ref', ''))" in block
    assert "credential_ref отсутствует" not in block


def test_agent_profile_listing_explains_session_and_missing_secret_states():
    root = Path(__file__).resolve().parents[1]
    source = (root / "workbench" / "agent.py").read_text(encoding="utf-8")
    assert "пароль доступен, сохранён через DPAPI" in source
    assert "пароль доступен только в текущем сеансе Workbench" in source
    assert "секрет недоступен в CredentialBroker" in source
