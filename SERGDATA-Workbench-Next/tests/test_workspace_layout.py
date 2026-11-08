from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_focus_mode_overrides_hidden_inspector_grid():
    css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
    assert ".app.focus-mode.hide-inspector" in css
    assert ".app.focus-mode.hide-sidebar" in css
    assert ".app.hide-inspector.hide-sidebar" in css
    assert "grid-template-columns:minmax(0,1fr)!important" in css


def test_panel_widths_are_persisted_and_restored():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "localStorage.getItem('sergdata-layout')" in js
    assert "localStorage.setItem('sergdata-layout'" in js
    assert "--wb-left-width" in js
    assert "--wb-right-width" in js


def test_workspace_preferences_are_persisted():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "sergdata-workspace-prefs" in js
    assert "prefs.focus" in js
    assert "prefs.hideInspector" in js
    assert "prefs.executionCollapsed" in js


def test_vertical_layout_is_persisted():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "sergdata-layout-vertical" in js
    assert "localStorage.setItem('sergdata-layout-vertical'" in js
