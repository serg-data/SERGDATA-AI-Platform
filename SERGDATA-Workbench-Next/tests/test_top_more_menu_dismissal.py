from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_top_more_menu_dismisses_on_outside_click_and_escape():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "$('topMoreMenu')" in js
    assert "details.contains(event.target)" in js
    assert "event.key==='Escape'&&!inFocusMode()&&details.open" in js
    assert "panel.addEventListener('click'" in js


def test_top_more_menu_does_not_break_focus_mode_toolbar():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "const inFocusMode=()=>!!app?.classList.contains('focus-mode')" in js
    assert "details.open&&!inFocusMode()" in js


def test_frontend_cache_version_is_bumped_for_patch():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert "style.css?v=20261106-top-more-dismiss1" in html
    assert "app.js?v=20261106-dom-code-render-v1" in html
