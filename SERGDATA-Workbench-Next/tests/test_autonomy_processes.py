import sys, time
from pathlib import Path
from workbench.db import Store
from workbench.processes import ProcessRegistry

def test_project_autonomy_defaults_and_persists(tmp_path):
    s=Store(tmp_path/'db.sqlite3')
    pid=s.create_project('p',str(tmp_path))
    assert s.get_project_settings(pid)['autonomy']=='analysis'
    s.set_project_autonomy(pid,'development')
    assert s.get_project_settings(pid)['autonomy']=='development'
    try:s.set_project_autonomy(pid,'unsafe')
    except ValueError:pass
    else:assert False

def test_process_registry_streams_and_stops(tmp_path):
    reg=ProcessRegistry()
    jid=reg.start([sys.executable,'-c',"import sys,time; print('OUT',flush=True); print('ERR',file=sys.stderr,flush=True); time.sleep(.2)"],tmp_path,timeout=5)
    deadline=time.time()+5
    while time.time()<deadline:
        item=reg.get(jid)
        if item and item['status'] in ('completed','failed'):break
        time.sleep(.03)
    assert item['status']=='completed'
    assert 'OUT' in item['stdout'] and 'ERR' in item['stderr']

def test_process_registry_stop(tmp_path):
    reg=ProcessRegistry()
    jid=reg.start([sys.executable,'-c','import time; time.sleep(20)'],tmp_path,timeout=30)
    time.sleep(.15); assert reg.stop(jid)
    deadline=time.time()+5
    while time.time()<deadline:
        item=reg.get(jid)
        if item['status']=='stopped':break
        time.sleep(.05)
    assert item['status']=='stopped'
