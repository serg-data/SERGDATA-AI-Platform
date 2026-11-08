from workbench.processes import ProcessRegistry


def test_process_registry_keeps_only_recent_terminal_jobs_and_never_prunes_running():
    registry = ProcessRegistry()
    registry.jobs = {
        f'old-{i}': {'id': f'old-{i}', 'status': 'completed', 'started_at': float(i)}
        for i in range(150)
    }
    registry.jobs['active'] = {'id': 'active', 'status': 'running', 'started_at': 151.0}

    with registry.lock:
        registry._prune_locked()

    terminal = [job for job in registry.jobs.values()
                if job['status'] in ('completed', 'failed', 'stopped')]
    assert len(terminal) == registry.MAX_RETAINED_TERMINAL_JOBS
    assert 'active' in registry.jobs
    assert 'old-0' not in registry.jobs
    assert 'old-49' not in registry.jobs
    assert 'old-50' in registry.jobs
    assert 'old-149' in registry.jobs
