"""Shared path and secret-name policy used by every project-file tool."""
from __future__ import annotations
from pathlib import Path
import re

_SECRET_DIRS = {
    '.git', '.ssh', '.aws', '.azure', '.gnupg', '.config', '.docker', '.kube',
    '.terraform', '.terraform.d', '.pulumi', '.npm', '.pki', 'keyrings', 'gcloud', 'secrets',
    'credentials', 'private', 'tokens', 'certs', 'certificates', 'passwords', 'passphrases',
    'sessions', 'cookies', 'vault', 'authinfo',
}
_SECRET_NAMES = {
    '.env', '.env.local', '.env.production', '.env.development', '.env.test',
    '.env.staging', '.envrc', '.npmrc', '.pypirc', '.netrc', '.git-credentials',
    '.pgpass', '.my.cnf', '.htpasswd', '.authinfo', 'id_rsa', 'id_ed25519', 'id_ecdsa',
    'id_dsa', 'authorized_keys', 'shadow', 'gshadow', 'passwd', 'password', 'passwords',
    'passphrase', 'passphrases', 'cookies.txt', 'cookies.sqlite', 'session.json',
    'sessions.json', 'auth.json', 'auth.yaml', 'auth.yml', 'credentials.json',
    'secrets.json', 'service-account.json', 'service_account.json',
    'application_default_credentials.json', 'login data', 'web data', 'local state',
}
_SECRET_SUFFIXES = {'.pem', '.key', '.p12', '.pfx', '.p7b', '.p7c', '.jks', '.kdbx', '.keystore', '.ppk', '.ovpn'}
_SAFE_ENV_EXAMPLES = {'.env.example', '.env.sample', '.env.template'}
_SECRET_NAME_PATTERN = re.compile(
    r'(^|[._-])(secret|secrets|credential|credentials|token|tokens|api[_-]?key|private[_-]?key|'
    r'password|passwords|passwd|passphrase|passphrases|pwd)([._-]|$)', re.I
)


def is_sensitive_path(path: str | Path) -> bool:
    p = Path(str(path or '').replace('\\', '/'))
    parts = [x.casefold() for x in p.parts if x not in ('/', '\\', '')]
    if any(part in _SECRET_DIRS or _SECRET_NAME_PATTERN.search(part) for part in parts):
        return True
    name = p.name.casefold()
    if name in _SAFE_ENV_EXAMPLES:
        return False
    if name in _SECRET_NAMES or (name.startswith('.env.') and name not in _SAFE_ENV_EXAMPLES):
        return True
    # Environment files are commonly named prod.env / staging.env as well as .env.*.
    if name.endswith('.env') and name not in _SAFE_ENV_EXAMPLES:
        return True
    if re.match(r'^id_(?:rsa|ed25519|ecdsa|dsa)(?:[._-]|$)', name):
        return True
    if p.suffix.casefold() in _SECRET_SUFFIXES:
        return True
    if _SECRET_NAME_PATTERN.search(name) or name == 'kubeconfig':
        return True
    if name.endswith(('.tfstate', '.tfstate.backup', '.mobileprovision')):
        return True
    if name.endswith(('.secret', '.secrets', '.credential', '.credentials', '.token', '.tokens')):
        return True
    return False
