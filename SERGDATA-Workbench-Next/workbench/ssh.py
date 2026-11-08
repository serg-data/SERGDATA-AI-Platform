"""Safe OpenSSH adapter: strict host-key checking, batch auth, bounded output."""
from __future__ import annotations
import os, re, shutil, subprocess, time, shlex
from pathlib import Path
from .security import is_sensitive_path

MAX_COMMAND = 12000
MAX_OUTPUT = 30000
_HOST = re.compile(r"^(?=.{1,253}$)[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$|^(?:\d{1,3}\.){3}\d{1,3}$")
_USER = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,31}$")

class SSHError(ValueError):
    pass

def validate_fields(host: str, user: str, port: int):
    host, user = str(host or '').strip(), str(user or '').strip()
    if not _HOST.fullmatch(host) or '..' in host:
        raise SSHError('Некорректное имя SSH-хоста')
    if not _USER.fullmatch(user):
        raise SSHError('Некорректное имя SSH-пользователя')
    port = int(port)
    if not 1 <= port <= 65535:
        raise SSHError('Порт должен быть в диапазоне 1–65535')
    if re.fullmatch(r'(?:\d{1,3}\.){3}\d{1,3}', host):
        if any(int(part) > 255 for part in host.split('.')):
            raise SSHError('Некорректный IPv4-адрес')
    return host, user, port


def find_matching_profile(profiles, host: str, user: str, port: int):
    """Return the unique saved profile matching an SSH target, if one exists."""
    host, user, port = validate_fields(host, user, port)
    matches = [
        p for p in (profiles or [])
        if str(p.get("host", "")).strip().lower() == host.lower()
        and str(p.get("username", "")).strip().lower() == user.lower()
        and int(p.get("port", 0)) == port
    ]
    if len(matches) > 1:
        raise SSHError("Для SSH-адреса найдено несколько профилей. Выбери профиль явно через ssh_run_profile_command.")
    return matches[0] if matches else None


def validate_target(host: str, user: str, port: int):
    host, user, port = validate_fields(host, user, port)
    exe = shutil.which('ssh')
    if not exe:
        raise SSHError('OpenSSH client (ssh) не найден в PATH')
    return exe, host, user, port

def ssh_argv(host: str, user: str, port: int, remote_command: str, timeout: int = 30):
    exe, host, user, port = validate_target(host, user, port)
    if not remote_command or len(remote_command) > MAX_COMMAND or any(ord(c) < 32 and c not in '\t\n' for c in remote_command):
        raise SSHError('Удалённая команда пуста, слишком длинная или содержит управляющие символы')
    return [exe, '-T', '-p', str(port), '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
            '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2',
            '-o', 'StrictHostKeyChecking=yes', '-o', 'PasswordAuthentication=no',
            f'{user}@{host}', remote_command]

def run_ssh(host: str, user: str, port: int, remote_command: str, timeout: int = 30):
    argv = ssh_argv(host, user, port, remote_command, timeout)
    started = time.monotonic()
    try:
        p = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=max(1, min(int(timeout), 180)), shell=False)
        return {'status': 'completed' if p.returncode == 0 else 'failed', 'exit_code': p.returncode,
                'duration_sec': round(time.monotonic()-started, 2),
                'stdout': (p.stdout or '')[-MAX_OUTPUT:], 'stderr': (p.stderr or '')[-MAX_OUTPUT:]}
    except subprocess.TimeoutExpired as e:
        def dec(v): return v.decode('utf-8','replace') if isinstance(v, bytes) else (v or '')
        return {'status':'timed_out','exit_code':None,'duration_sec':round(time.monotonic()-started,2),
                'stdout':dec(e.stdout)[-MAX_OUTPUT:],'stderr':(dec(e.stderr)+'\n[Workbench: SSH timeout]')[-MAX_OUTPUT:]}

def read_remote_file(host: str, user: str, port: int, path: str, timeout: int = 30):
    path = str(path or '').strip()
    if not path.startswith('/') or '\x00' in path or '\n' in path or '\r' in path:
        raise SSHError('Для чтения укажи абсолютный путь без переводов строк')
    if is_sensitive_path(path):
        raise SSHError('Чтение потенциально секретного файла запрещено')
    # Quote the path as one POSIX shell argument; this is a fixed read-only command.
    result = run_ssh(host, user, port, 'cat -- ' + shlex.quote(path), timeout)
    if len(result['stdout']) >= MAX_OUTPUT:
        result['stdout'] += '\n[Вывод обрезан лимитом Workbench]'
    return result


def run_profile_command(profile: dict, command: str, credential_broker=None, timeout: int = 180, cancel_event=None):
    """Run an approved command through a saved profile; password never enters argv/logs."""
    host = profile.get('host')
    user = profile.get('username')
    port = profile.get('port')
    host, user, port = validate_fields(host, user, port)
    command = str(command or '').strip()
    if not command or len(command) > MAX_COMMAND or any(ord(c) < 32 and c not in '\t\n' for c in command):
        raise SSHError('Удалённая команда пуста, слишком длинная или содержит управляющие символы')
    timeout = max(1, min(int(timeout), 180))
    if cancel_event is not None and cancel_event.is_set():
        return {'status':'stopped','exit_code':130,'duration_sec':0.0,'stdout':'','stderr':'Остановлено пользователем до подключения'}
    if profile.get('auth_method') == 'key':
        return run_ssh(host, user, port, command, timeout)
    if profile.get('auth_method') != 'password':
        raise SSHError('Неизвестный способ SSH-аутентификации')
    if not credential_broker:
        raise SSHError('Защищённое хранилище учётных данных не подключено')
    try:
        import paramiko
    except ImportError as exc:
        raise SSHError('Для парольной SSH-аутентификации установи зависимость paramiko из requirements.txt') from exc

    known_hosts = Path.home() / '.ssh' / 'known_hosts'
    if not known_hosts.is_file():
        raise SSHError(f'Файл проверенных SSH host keys не найден: {known_hosts}. Сначала проверь fingerprint и добавь ключ вручную.')
    # Do not even resolve the secret until the trusted host-key database is present.
    secret = credential_broker.resolve(profile.get('credential_ref', ''))
    client = paramiko.SSHClient()
    if cancel_event is not None and hasattr(cancel_event, 'register'):
        cancel_event.register(client.close)
    client.load_system_host_keys()
    client.load_host_keys(str(known_hosts))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    started = time.monotonic()
    stdout_data = bytearray()
    stderr_data = bytearray()
    exit_code = None
    status = 'failed'
    try:
        try:
            client.connect(hostname=host, port=int(port), username=user, password=secret,
                           timeout=10, banner_timeout=10, auth_timeout=15,
                           allow_agent=False, look_for_keys=False)
        except Exception as exc:
            if cancel_event is not None and cancel_event.is_set():
                return {'status':'stopped','exit_code':130,'duration_sec':round(time.monotonic()-started,2),
                        'stdout':'','stderr':'Остановлено пользователем во время SSH-подключения'}
            if isinstance(exc, getattr(paramiko, 'AuthenticationException', ())):
                raise SSHError('SSH-сервер отклонил пароль профиля. Проверь правильность пароля и разрешена ли парольная авторизация для root на сервере. Секрет присутствует в CredentialBroker; это не ошибка отсутствующей ссылки.') from exc
            raise
        if cancel_event is not None and cancel_event.is_set():
            return {'status':'stopped','exit_code':130,'duration_sec':round(time.monotonic()-started,2),
                    'stdout':'','stderr':'Остановлено пользователем после SSH-подключения'}
        transport = client.get_transport()
        if not transport or not transport.is_active():
            raise SSHError('SSH-транспорт не активен после авторизации')
        channel = transport.open_session(timeout=10)
        if cancel_event is not None and hasattr(cancel_event, 'register'):
            cancel_event.register(channel.close)
        channel.settimeout(0.2)
        channel.exec_command(command)
        deadline = time.monotonic() + timeout
        while True:
            if cancel_event is not None and cancel_event.is_set():
                channel.close()
                status, exit_code = 'stopped', 130
                break
            if channel.recv_ready():
                chunk = channel.recv(8192)
                if chunk:
                    stdout_data.extend(chunk)
                    if len(stdout_data) > MAX_OUTPUT:
                        del stdout_data[:-MAX_OUTPUT]
            if channel.recv_stderr_ready():
                chunk = channel.recv_stderr(8192)
                if chunk:
                    stderr_data.extend(chunk)
                    if len(stderr_data) > MAX_OUTPUT:
                        del stderr_data[:-MAX_OUTPUT]
            if channel.exit_status_ready() and not channel.recv_ready() and not channel.recv_stderr_ready():
                exit_code = channel.recv_exit_status()
                status = 'completed' if exit_code == 0 else 'failed'
                break
            if time.monotonic() >= deadline:
                channel.close()
                status, exit_code = 'timed_out', None
                stderr_data.extend(b'\n[Workbench: SSH timeout]')
                break
            time.sleep(0.03)
        return {'status': status, 'exit_code': exit_code,
                'duration_sec': round(time.monotonic() - started, 2),
                'stdout': bytes(stdout_data).decode('utf-8', 'replace'),
                'stderr': bytes(stderr_data).decode('utf-8', 'replace')}
    finally:
        client.close()
        secret = None
