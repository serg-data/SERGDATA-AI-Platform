from workbench.tool_guard import tool_call_fingerprint


def test_sandbox_read_and_check_can_repeat_after_workspace_mutation():
    args = {'sandbox_id': 'a' * 32, 'path': 'storage.py'}
    before = tool_call_fingerprint('sandbox_read_file', args, 0)
    after = tool_call_fingerprint('sandbox_read_file', args, 1)
    assert before != after

    check_args = {'sandbox_id': 'a' * 32, 'command': 'pytest'}
    assert tool_call_fingerprint('sandbox_run_check', check_args, 0) != tool_call_fingerprint(
        'sandbox_run_check', check_args, 1
    )


def test_identical_sandbox_call_without_mutation_is_still_detectable():
    args = {'sandbox_id': 'a' * 32, 'path': 'storage.py'}
    assert tool_call_fingerprint('sandbox_read_file', args, 2) == tool_call_fingerprint(
        'sandbox_read_file', args, 2
    )


def test_non_sandbox_repeat_guard_does_not_depend_on_sandbox_revision():
    args = {'command': 'hostname'}
    assert tool_call_fingerprint('ssh_run_command', args, 0) == tool_call_fingerprint(
        'ssh_run_command', args, 99
    )


def test_sandbox_revision_advances_after_write(tmp_path):
    from workbench.sandbox import SandboxManager
    manager = SandboxManager(tmp_path)
    created = manager.create('revision-test')
    sid = created['id']
    assert manager.revision(sid) == 0
    manager.write(sid, 'sample.txt', 'one')
    assert manager.revision(sid) == 1
    manager.write(sid, 'sample.txt', 'two')
    assert manager.revision(sid) == 2
