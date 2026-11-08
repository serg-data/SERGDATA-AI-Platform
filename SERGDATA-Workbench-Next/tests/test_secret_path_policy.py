import pytest
from workbench.tools import ProjectTools
from workbench.execution import ExecutionEngine
from workbench.security import is_sensitive_path


@pytest.mark.parametrize('name', [
    '.env', '.env.development', '.env.test', '.env.staging', '.netrc', '.npmrc',
    '.pypirc', '.git-credentials', 'id_ed25519', 'secrets.toml', 'access.token',
    'private/server.conf', '.ssh/config', 'certs/client.p12', 'api_key.json', 'my-secret-config.yaml', 'kubeconfig', 'terraform.tfstate', r'.ssh\id_rsa', r'private\server.conf',
    'password.txt', 'db.passphrase', 'passwd', '.pgpass', '.my.cnf', '.htpasswd',
    'auth.json', 'cookies.txt', 'session.json', 'passwords/prod.txt', 'vault/prod.yml',
    'production.env', 'id_ed25519_work', 'private.ppk', 'vpn-profile.ovpn'
])
def test_central_policy_blocks_common_secret_paths(name):
    assert is_sensitive_path(name)


def test_project_tools_hide_and_refuse_secret_files_consistently(tmp_path):
    (tmp_path / 'src').mkdir()
    (tmp_path / '.env.development').write_text('PASSWORD=do-not-read', encoding='utf-8')
    (tmp_path / '.env.example').write_text('PASSWORD=placeholder', encoding='utf-8')
    (tmp_path / '.netrc').write_text('machine test login x password y', encoding='utf-8')
    (tmp_path / 'src' / 'app.py').write_text('print("ok")', encoding='utf-8')
    tools = ProjectTools(tmp_path)
    listing = tools.listing()
    assert '.env.development' not in listing
    assert '.netrc' not in listing
    assert '.env.example' in listing
    assert 'src/app.py' in listing
    with pytest.raises(ValueError):
        tools.read('.env.development')
    with pytest.raises(ValueError):
        tools.read('.netrc')
    engine = ExecutionEngine(tmp_path)
    with pytest.raises(ValueError):
        engine.read_file('.env.development')
    assert '.env.development' not in engine.search('password')
