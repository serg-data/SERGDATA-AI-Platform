import time
from pathlib import Path
from workbench.processes import ProcessRegistry


def wait_for(registry, job_id, terminal=('completed','failed','stopped'), timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        item = registry.get(job_id)
        if item and item['status'] in terminal:
            return item
        time.sleep(0.01)
    raise AssertionError('callable job did not finish in time')


def test_callable_execution_job_captures_bounded_result_without_secret_args(tmp_path):
    registry = ProcessRegistry()
    def execute(profile, command, broker, timeout=10, cancel_event=None):
        return {'status':'completed','exit_code':0,'stdout':f'ran {command}','stderr':''}
    job_id = registry.start_callable(execute, ({'name':'SUB'}, 'hostname', object()), Path(tmp_path), display='SSH SUB')
    item = wait_for(registry, job_id)
    assert item['status'] == 'completed'
    assert item['exit_code'] == 0
    assert item['stdout'] == 'ran hostname'
    assert 'broker' not in str(item).lower()


def test_callable_execution_job_can_be_cancelled(tmp_path):
    registry = ProcessRegistry()
    def execute(timeout=10, cancel_event=None):
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            if cancel_event.is_set():
                return {'status':'stopped','exit_code':130,'stdout':'','stderr':'stopped'}
            time.sleep(0.01)
        return {'status':'completed','exit_code':0,'stdout':'done','stderr':''}
    job_id = registry.start_callable(execute, (), Path(tmp_path), display='SSH cancellable')
    time.sleep(0.03)
    assert registry.stop(job_id) is True
    item = wait_for(registry, job_id)
    assert item['status'] == 'stopped'


def test_callable_completion_callback_runs_once_and_exposes_execution_link(tmp_path):
    registry = ProcessRegistry()
    seen = []
    def execute(timeout=10, cancel_event=None):
        return {'status':'completed','exit_code':0,'stdout':'done','stderr':''}
    job_id = registry.start_callable(execute, (), Path(tmp_path), display='callback job',
                                     execution_id=123, on_complete=lambda item: seen.append(item))
    item = wait_for(registry, job_id)
    deadline = time.monotonic() + 1
    while not seen and time.monotonic() < deadline:
        time.sleep(0.01)
    assert len(seen) == 1
    assert seen[0]['id'] == job_id
    assert seen[0]['execution_id'] == 123
    assert seen[0]['stdout'] == 'done'
    assert 'on_complete' not in seen[0]


def test_subprocess_completion_callback_runs_after_output_capture(tmp_path):
    import sys
    registry = ProcessRegistry()
    seen = []
    job_id = registry.start([sys.executable, '-c', 'print("hello-callback")'], Path(tmp_path),
                            timeout=10, on_complete=lambda item: seen.append(item), execution_id=321)
    item = wait_for(registry, job_id)
    deadline = time.monotonic() + 1
    while not seen and time.monotonic() < deadline:
        time.sleep(0.01)
    assert len(seen) == 1
    assert seen[0]['execution_id'] == 321
    assert 'hello-callback' in seen[0]['stdout']
