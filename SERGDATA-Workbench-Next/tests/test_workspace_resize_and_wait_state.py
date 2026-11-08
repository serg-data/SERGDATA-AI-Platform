from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vertical_resize_handles_are_visible_and_resizable():
    css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert ".v-resize{" in css
    assert "display:flex!important" in css
    assert "data-vresize" in js
    assert "window.addEventListener('pointermove',move" in js
    assert "localStorage.setItem('sergdata-layout-vertical'" in js
    assert "height*.72" in js


def test_waiting_for_secret_is_not_shown_as_compute():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "waitingForUserInput" in js
    assert "Ожидается защищённый ввод" in js
    assert "Ответ передан модели; секрет не добавлен в историю" in js
