from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_knowledge_stop_endpoint_uses_shared_process_registry():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "@app.post('/api/knowledge/stop')" in source
    assert "from workbench.processes import processes" in source
    assert "processes.start(command, Path(cwd), timeout=900)" in source
    assert "processes.stop(jid)" in source
    assert '"stop_requested": False' in source


def test_knowledge_close_stops_first_and_closes_afterwards():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert 'id="knowledgeClose" type="button"' in html
    assert "fetch('/api/knowledge/stop'" in js
    assert "sd.job?.running" in js
    assert "dialog.close();" in js
