import pytest
from workbench import ssh


def test_ssh_argv_uses_strict_key_and_batch_auth(monkeypatch):
    monkeypatch.setattr(ssh.shutil, 'which', lambda name: '/usr/bin/ssh' if name == 'ssh' else None)
    args = ssh.ssh_argv('fin.sergdata.top', 'root', 2222, 'hostname')
    assert args[0] == '/usr/bin/ssh'
    assert 'StrictHostKeyChecking=yes' in args
    assert 'BatchMode=yes' in args
    assert 'PasswordAuthentication=no' in args
    assert args[-1] == 'hostname'


@pytest.mark.parametrize('host,user,port', [('../host','root',22), ('host','bad user',22), ('host','root',0), ('host','root',65536)])
def test_rejects_invalid_targets(monkeypatch, host, user, port):
    monkeypatch.setattr(ssh.shutil, 'which', lambda name: '/usr/bin/ssh')
    with pytest.raises(ssh.SSHError):
        ssh.validate_target(host, user, port)


def test_read_file_requires_absolute_path(monkeypatch):
    with pytest.raises(ssh.SSHError):
        ssh.read_remote_file('host', 'root', 22, 'relative.txt')


def test_read_file_quotes_path(monkeypatch):
    monkeypatch.setattr(ssh.shutil, 'which', lambda name: '/usr/bin/ssh')
    captured = {}
    def fake_run(args, **kwargs):
        captured['args'] = args
        class Result:
            returncode = 0
            stdout = 'hello'
            stderr = ''
        return Result()
    monkeypatch.setattr(ssh.subprocess, 'run', fake_run)
    result = ssh.read_remote_file('fin.sergdata.top', 'root', 2222, "/tmp/a file.txt")
    assert result['exit_code'] == 0
    assert captured['args'][-1] == "cat -- '/tmp/a file.txt'"

@pytest.mark.parametrize('path', ['/etc/shadow', '/root/.ssh/id_ed25519', '/opt/app/.env', '/tmp/private.pem'])
def test_read_file_blocks_secrets(path):
    with pytest.raises(ssh.SSHError):
        ssh.read_remote_file('host', 'root', 22, path)
