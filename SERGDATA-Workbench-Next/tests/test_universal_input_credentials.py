import asyncio
import json
from types import SimpleNamespace

from workbench.credential_broker import CredentialBroker
from workbench.db import Store
from workbench.agent import Agent


class FakeProtector:
    def protect(self, value: bytes) -> bytes:
        return b'protected:' + value[::-1]

    def unprotect(self, value: bytes) -> bytes:
        assert value.startswith(b'protected:')
        return value[len(b'protected:'):][::-1]


def make_branch(store, root):
    with store.conn() as c:
        c.execute("INSERT INTO projects(name,root,created_at) VALUES('p',?,?)", (str(root), 'now'))
        pid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO tasks(project_id,title,created_at,updated_at) VALUES(?,?,?,?)", (pid, 't', 'now', 'now'))
        tid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("INSERT INTO branches(task_id,name,created_at,updated_at) VALUES(?,?,?,?)", (tid, 'b', 'now', 'now'))
        return c.execute('SELECT last_insert_rowid()').fetchone()[0]


def test_credential_broker_persistent_values_are_encrypted_and_reload(tmp_path):
    path = tmp_path / 'credentials.dpapi'
    protector = FakeProtector()
    broker = CredentialBroker(path, protector=protector)
    ref = broker.put('not-a-real-password-123', persist=True)
    raw = path.read_text('utf-8')
    assert 'not-a-real-password-123' not in raw
    assert ref in raw
    reopened = CredentialBroker(path, protector=protector)
    assert reopened.resolve(ref) == 'not-a-real-password-123'


def test_credential_broker_ephemeral_secret_does_not_survive_restart(tmp_path):
    path = tmp_path / 'credentials.dpapi'
    broker = CredentialBroker(path, protector=FakeProtector())
    ref = broker.put('temporary-secret', persist=False)
    assert broker.resolve(ref) == 'temporary-secret'
    reopened = CredentialBroker(path, protector=FakeProtector())
    try:
        reopened.resolve(ref)
    except Exception as exc:
        assert 'отсутствует' in str(exc)
    else:
        raise AssertionError('ephemeral secret unexpectedly survived restart')


def test_input_request_secret_is_not_written_to_sqlite_and_resumes_original_tool_call(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    bid = make_branch(store, tmp_path)
    request_id = store.add_input_request(bid, 'SSH пароль', 'Введи пароль сервера', 'secret')
    snapshot = [
        {'role': 'user', 'content': 'Подключись к серверу'},
        {'role': 'assistant', 'content': '', 'tool_calls': [
            {'id': 'call_before', 'type': 'function', 'function': {'name':'list_server_profiles','arguments':'{}'}},
            {'id': 'call_secret_1', 'type': 'function', 'function': {
                'name': 'request_user_secret', 'arguments': '{"title":"SSH пароль"}'}},
            {'id': 'call_after', 'type': 'function', 'function': {'name':'ssh_run_profile_command','arguments':'{}'}},
        ]},
        {'role':'tool','tool_call_id':'call_before','content':'Профилей пока нет'},
    ]
    store.set_input_request_context(request_id, snapshot, 'call_secret_1', 'test-model', None)
    broker = CredentialBroker(tmp_path / 'credentials.dpapi', protector=FakeProtector())
    ref = broker.put('ultra-secret-value', persist=False)
    assert store.complete_input_request(request_id, '', ref)
    row = store.input_request(request_id)
    assert row['result_text'] == ''
    assert row['credential_ref'] == ref
    assert 'ultra-secret-value' not in json.dumps(row)

    captured = {}
    class FakeCompletions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            msg = SimpleNamespace(content='Получил защищённую ссылку и продолжу.', tool_calls=None)
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
                                   usage=SimpleNamespace(prompt_tokens=4, completion_tokens=5))
    class FakeLLM:
        chat = SimpleNamespace(completions=FakeCompletions())
        def with_options(self, **kwargs):
            return self

    agent = object.__new__(Agent)
    agent.store = store
    agent.credentials = broker
    agent.cfg = SimpleNamespace(lm_model='test-model')
    agent.llm = FakeLLM()
    agent.specs = lambda: []
    async def compact(msgs, tools, model, branch_id, memory, turn_id):
        return msgs, '', 0, 0
    agent._compact_runtime = compact

    result = asyncio.run(agent.resume_input_request(request_id))
    assert result['resumed'] is True
    tool_messages = [m for m in captured['messages'] if m.get('role') == 'tool']
    by_id = {m['tool_call_id']:m for m in tool_messages}
    assert set(by_id) == {'call_before','call_secret_1','call_after'}
    assert by_id['call_before']['content'] == 'Профилей пока нет'
    assert ref in by_id['call_secret_1']['content']
    assert 'ultra-secret-value' not in by_id['call_secret_1']['content']
    assert 'ожидает пользователя' in by_id['call_after']['content']
    assert store.input_request(request_id)['resume_status'] == 'completed'
    assert all('ultra-secret-value' not in m['content'] for m in store.messages(bid))


def test_server_profiles_store_only_opaque_credential_reference(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    profile_id = store.save_server_profile(None, 'SUB', 'sub.example.test', 2222, 'root',
                                           'password', 'cred_test_reference')
    profile = store.server_profile(profile_id)
    assert profile['name'] == 'SUB'
    assert profile['credential_ref'] == 'cred_test_reference'
    assert 'password' not in profile
    assert store.delete_server_profile(profile_id)
    assert store.server_profile(profile_id) is None


def test_password_ssh_profile_uses_strict_known_hosts_and_never_puts_password_in_command(monkeypatch, tmp_path):
    import sys
    from pathlib import Path
    from workbench import ssh

    ssh_dir = tmp_path / '.ssh'
    ssh_dir.mkdir()
    (ssh_dir / 'known_hosts').write_text('verified-host-key', encoding='utf-8')
    monkeypatch.setattr(ssh.Path, 'home', lambda: tmp_path)
    captured = {}

    class FakeChannel:
        def settimeout(self, value): pass
        def exec_command(self, command): captured['command'] = command
        def recv_ready(self): return False
        def recv_stderr_ready(self): return False
        def exit_status_ready(self): return True
        def recv_exit_status(self): return 0

    class FakeTransport:
        def is_active(self): return True
        def open_session(self, timeout=None): return FakeChannel()

    class FakeClient:
        def load_system_host_keys(self): captured['system_keys'] = True
        def load_host_keys(self, path): captured['known_hosts'] = path
        def set_missing_host_key_policy(self, policy): captured['policy'] = type(policy).__name__
        def connect(self, **kwargs): captured['connect'] = kwargs
        def get_transport(self): return FakeTransport()
        def close(self): captured['closed'] = True

    class FakeParamiko:
        SSHClient = FakeClient
        class RejectPolicy: pass

    monkeypatch.setitem(sys.modules, 'paramiko', FakeParamiko)
    class Broker:
        def resolve(self, ref):
            captured['resolved_ref'] = ref
            return 'top-secret-password'

    profile = {'host':'sub.example.test', 'username':'root', 'port':2222,
               'auth_method':'password', 'credential_ref':'cred_test_1'}
    result = ssh.run_profile_command(profile, 'hostname && id', Broker())
    assert result['status'] == 'completed'
    assert captured['policy'] == 'RejectPolicy'
    assert captured['known_hosts'] == str(ssh_dir / 'known_hosts')
    assert captured['connect']['password'] == 'top-secret-password'
    assert captured['connect']['allow_agent'] is False
    assert captured['connect']['look_for_keys'] is False
    assert captured['command'] == 'hostname && id'
    assert 'top-secret-password' not in captured['command']
    assert captured['closed'] is True


def test_input_resume_claim_is_atomic_and_only_once(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    bid = make_branch(store, tmp_path)
    request_id = store.add_input_request(bid, 'Continue', 'Enter value', 'text')
    snapshot = [{'role':'assistant','content':'','tool_calls':[{'id':'call_once','type':'function','function':{'name':'request_user_input','arguments':'{}'}}]}]
    store.set_input_request_context(request_id, snapshot, 'call_once', 'model', None)
    assert store.complete_input_request(request_id, 'value', '')
    assert store.claim_input_request_resume(request_id) is True
    assert store.claim_input_request_resume(request_id) is False
    store.mark_input_request_resumed(request_id, 'completed')
    assert store.input_requests_waiting_resume() == []


def test_restart_recovery_marks_unknown_execution_without_retry(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    bid = make_branch(store, tmp_path)
    execution_id = store.add_pending_execution(bid, 'hostname')
    with store.conn() as c:
        c.execute("UPDATE pending_execution SET status='running',resume_status='waiting' WHERE id=?", (execution_id,))
    recovered = store.recover_interrupted_executions()
    assert [x['id'] for x in recovered] == [execution_id]
    row = store.execution_by_id(execution_id)
    assert row['status'] == 'failed'
    assert row['resume_status'] == 'failed'
    assert 'неизвестен' in row['result'].lower()
    assert store.recover_interrupted_executions() == []


def test_shared_credential_reference_survives_until_last_profile_is_removed(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    first = store.save_server_profile(None, 'FIN', 'fin.example.test', 2222, 'root', 'password', 'cred_shared')
    second = store.save_server_profile(None, 'FIN backup', 'fin2.example.test', 2222, 'root', 'password', 'cred_shared')
    assert store.credential_ref_used_by_profile('cred_shared') is True
    store.delete_server_profile(first)
    assert store.credential_ref_used_by_profile('cred_shared') is True
    store.delete_server_profile(second)
    assert store.credential_ref_used_by_profile('cred_shared') is False


def test_secret_reference_is_detached_from_input_request_after_profile_binding(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    bid = make_branch(store, tmp_path)
    request_id = store.add_input_request(bid, 'Password', 'Enter password', 'secret')
    store.complete_input_request(request_id, '', 'cred_bound')
    assert store.input_request(request_id)['credential_ref'] == 'cred_bound'
    assert store.detach_credential_ref_from_input_requests('cred_bound') == 1
    assert store.input_request(request_id)['credential_ref'] == ''


def test_credential_broker_prunes_unreferenced_persistent_secrets(tmp_path):
    path = tmp_path / 'credentials.dpapi'
    protector = FakeProtector()
    broker = CredentialBroker(path, protector=protector)
    keep = broker.put('keep-me', persist=True)
    drop = broker.put('drop-me', persist=True)
    broker.prune({keep})
    reopened = CredentialBroker(path, protector=protector)
    assert reopened.resolve(keep) == 'keep-me'
    try:
        reopened.resolve(drop)
    except Exception:
        pass
    else:
        raise AssertionError('orphan credential was not pruned')


def test_persistent_secret_requires_platform_protector(tmp_path):
    from workbench.credential_broker import CredentialError
    broker = CredentialBroker(tmp_path / 'credentials.dpapi')
    if __import__('os').name != 'nt':
        try:
            broker.put('secret', persist=True)
        except CredentialError as exc:
            assert 'Windows DPAPI' in str(exc) or 'безопасно сохранить' in str(exc)
        else:
            raise AssertionError('persistent secret storage must fail closed without DPAPI')


def test_resume_snapshot_preserves_prior_tool_results_and_blocks_siblings(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    snapshot = [
        {'role':'user','content':'start'},
        {'role':'assistant','content':'','tool_calls':[
            {'id':'first','type':'function','function':{'name':'read','arguments':'{}'}},
            {'id':'awaited','type':'function','function':{'name':'request_user_secret','arguments':'{}'}},
            {'id':'not_run','type':'function','function':{'name':'ssh_run_profile_command','arguments':'{}'}},
        ]},
        {'role':'tool','tool_call_id':'first','content':'previous result'},
    ]
    normalized = store._resume_context_snapshot(snapshot, 'awaited')
    results = [m for m in normalized if m.get('role') == 'tool']
    assert [m['tool_call_id'] for m in results] == ['first','awaited','not_run']
    assert results[0]['content'] == 'previous result'
    assert results[1]['content'] == Store.PENDING_TOOL_RESULT
    assert 'ожидает пользователя' in results[2]['content']


def test_agent_can_create_and_update_profile_using_only_opaque_credential_refs(tmp_path):
    from workbench.agent import Agent
    store = Store(tmp_path / 'workbench.sqlite3')
    broker = CredentialBroker(tmp_path / 'credentials.dpapi', protector=FakeProtector())
    first_ref = broker.put('first-password')
    second_ref = broker.put('second-password')
    agent = object.__new__(Agent)
    agent.store = store
    agent.credentials = broker

    created = asyncio.run(agent.tool('create_server_profile', {
        'name':'SUB','host':'sub.example.test','port':2222,'username':'root',
        'auth_method':'password','credential_ref':first_ref
    }, 1))
    assert 'создан' in created
    profile = store.server_profiles()[0]
    assert profile['credential_ref'] == first_ref
    assert 'first-password' not in created

    updated = asyncio.run(agent.tool('update_server_profile', {
        'profile_id':profile['id'],'credential_ref':second_ref
    }, 1))
    assert 'обновлён' in updated
    assert store.server_profile(profile['id'])['credential_ref'] == second_ref
    assert broker.exists(second_ref)
    assert not broker.exists(first_ref)


def test_execution_result_is_persisted_once_for_process_callback_and_poll_race(tmp_path):
    store = Store(tmp_path / 'workbench.sqlite3')
    bid = make_branch(store, tmp_path)
    execution_id = store.add_pending_execution(bid, 'hostname')
    with store.conn() as c:
        c.execute("UPDATE pending_execution SET status='running',resume_status='waiting' WHERE id=?", (execution_id,))
    first, rendered = store.finish_execution_once(execution_id, 'completed', 0, 'host', '')
    second, rendered_again = store.finish_execution_once(execution_id, 'completed', 0, 'host', '')
    assert first is True and second is False
    assert rendered == rendered_again
    assert store.execution_by_id(execution_id)['status'] == 'completed'
