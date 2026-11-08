from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_topbar_has_operation_logs_button_and_dialog():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert 'id="openLogs"' in html
    assert 'id="logsDialog"' in html
    assert 'id="logsOutput"' in html
    assert 'id="logsCopy"' in html


def test_operation_logs_viewer_reads_live_knowledge_job_and_polls():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "openLogs" in js
    assert "logsDialog" in js
    assert "fetch('/api/knowledge/status'" in js
    assert "setInterval(refresh,1200)" in js
    assert "navigator.clipboard.writeText(lastText)" in js
