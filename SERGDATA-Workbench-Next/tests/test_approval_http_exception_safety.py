from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_approval_http_conflicts_bypass_startup_failure_recovery():
    source = (ROOT / 'main.py').read_text(encoding='utf-8')
    start = source.index("@app.post('/api/execution/{eid}/approve')")
    end = source.index("@app.get('/api/processes/{jid}')", start)
    block = source[start:end]

    http_handler = block.index('    except HTTPException:')
    generic_handler = block.index('    except Exception as e:', http_handler)
    assert http_handler < generic_handler
    http_branch = block[http_handler:generic_handler]
    assert 'raise' in http_branch
    assert 'store.finish_execution' not in http_branch
    assert 'run_tracked_agent_task' not in http_branch

    generic_branch = block[generic_handler:]
    assert "store.finish_execution(eid,'failed'" in generic_branch
    assert 'agent.resume_execution(eid' in generic_branch
