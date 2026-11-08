from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_highlighter_builds_tokens_with_dom_apis_not_html_strings():
    source = (ROOT / 'static' / 'app.js').read_text(encoding='utf-8')
    assert 'function highlightCodeFragment(code,lang){' in source
    assert "document.createElement('span')" in source
    assert 'span.textContent=text;' in source
    assert 'codeElement.replaceChildren(highlightCodeFragment(source,language));' in source
    assert 'rawCodeSources.get(codeElement)' in source
    # The Markdown fence contains escaped plain source; syntax spans are added only
    # after insertion into the live DOM.
    assert 'data-code-language=\"${esc(lang)}\">${esc(code.join' in source
    assert 'highlightCode(code.join' not in source


def test_chat_polling_fetches_final_messages_before_stopping():
    source = (ROOT / 'static' / 'app.js').read_text(encoding='utf-8')
    start = source.index('async function pollChatActivity(branch){')
    end = source.index('\nfunction setChatUiActive', start)
    poll = source[start:end]
    final_fetch = poll.rfind('await loadMessages();')
    stop = poll.rfind('stopChatPolling();')
    assert final_fetch != -1 and stop != -1 and final_fetch < stop
    assert 'else{\n   // The server may have committed the final assistant message' in poll
