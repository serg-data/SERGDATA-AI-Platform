from pathlib import Path
import pytest
from workbench.sandbox import SandboxManager


def test_sandbox_copy_edit_and_diff_are_isolated(tmp_path):
    root=tmp_path/'project'; root.mkdir()
    (root/'app.py').write_text('print("old")\n',encoding='utf-8')
    (root/'.env').write_text('SECRET=value',encoding='utf-8')
    (root/'state.sqlite3').write_bytes(b'database')
    sm=SandboxManager(root)
    created=sm.create('test')
    sid=created['id']
    assert 'app.py' in sm.list_files(sid)
    assert '.env' not in sm.list_files(sid)
    assert 'state.sqlite3' not in sm.list_files(sid)
    sm.write(sid,'app.py','print("new")\n')
    assert (root/'app.py').read_text(encoding='utf-8')=='print("old")\n'
    assert sm.diff(sid)['changes']==[{'path':'app.py','change':'modified'}]


def test_sandbox_rejects_traversal_and_sensitive_paths(tmp_path):
    root=tmp_path/'project'; root.mkdir(); (root/'a.py').write_text('x')
    sm=SandboxManager(root); sid=sm.create()['id']
    with pytest.raises(ValueError): sm.read(sid,'../outside.txt')
    with pytest.raises(ValueError): sm.write(sid,'.env','secret')


def test_sandbox_check_uses_workspace(tmp_path):
    root=tmp_path/'project'; root.mkdir(); (root/'a.py').write_text('x = 1\n')
    sm=SandboxManager(root); sid=sm.create()['id']
    result=sm.run_check(sid,'compile')
    assert result['status']=='completed'


def test_sandbox_shell_syntax_check_runs_only_parser(tmp_path):
    import shutil
    if not shutil.which("sh"):
        pytest.skip("sh is not installed")
    root=tmp_path/'project'; root.mkdir()
    script=root/'check.sh'
    script.write_text('#!/bin/sh\\necho "this must not execute"\\n',encoding='utf-8')
    sm=SandboxManager(root); sid=sm.create()['id']
    result=sm.run_check(sid,'sh_syntax',path='check.sh')
    assert result['status']=='completed'
    assert result['exit_code']==0
    assert 'this must not execute' not in result['stdout']


def test_sandbox_shell_syntax_reports_invalid_script(tmp_path):
    import shutil
    if not shutil.which("sh"):
        pytest.skip("sh is not installed")
    root=tmp_path/'project'; root.mkdir()
    (root/'broken.sh').write_text('if then\\n',encoding='utf-8')
    sm=SandboxManager(root); sid=sm.create()['id']
    result=sm.run_check(sid,'sh_syntax',path='broken.sh')
    assert result['status']=='failed'
    assert result['exit_code'] != 0


def test_sandbox_shell_check_rejects_missing_or_unsafe_path(tmp_path):
    root=tmp_path/'project'; root.mkdir()
    (root/'script.sh').write_text('true\\n',encoding='utf-8')
    sm=SandboxManager(root); sid=sm.create()['id']
    with pytest.raises(ValueError):
        sm.run_check(sid,'sh_syntax')
    with pytest.raises(ValueError):
        sm.run_check(sid,'sh_syntax',path='../script.sh')
    with pytest.raises(ValueError):
        sm.run_check(sid,'sh_syntax',path='script.py')
