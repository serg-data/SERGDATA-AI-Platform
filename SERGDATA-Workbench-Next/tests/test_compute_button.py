from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_compute_button_renders_real_busy_state_and_stop_action():
    source = (ROOT / 'static' / 'app.js').read_text(encoding='utf-8')
    assert 'function renderChatComputeButton(stopping=false)' in source
    assert "stageLabel==='tool_running'?'Tool'" in source or 'stageLabel' in source
    assert 'Остановить генерацию модели' in source
    assert "if(busy){await stopChat();return}" in source
    assert "renderChatComputeButton(true)" in source


def test_compute_button_elapsed_timer_is_cleaned_up():
    source = (ROOT / 'static' / 'app.js').read_text(encoding='utf-8')
    assert 'chatBusySince=Date.now()' in source
    assert 'chatElapsedTimer=setInterval' in source
    assert 'clearInterval(chatElapsedTimer)' in source


def test_compute_spinner_has_accessible_reduced_motion_support():
    css = (ROOT / 'static' / 'style.css').read_text(encoding='utf-8')
    assert '.compute-spinner' in css
    assert '@keyframes sergdata-compute-spin' in css
    assert '@media(prefers-reduced-motion:reduce)' in css
    assert '.composer-send.is-computing.is-stopping' in css
