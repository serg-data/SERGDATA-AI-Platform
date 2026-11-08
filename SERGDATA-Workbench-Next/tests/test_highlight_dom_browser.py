from pathlib import Path
import pytest
import shutil
import json

ROOT = Path(__file__).resolve().parents[1]


def test_highlight_and_copy_are_clean_in_real_chromium_dom():
    playwright = pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    source = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    def extract(start_marker: str, end_marker: str) -> str:
        start = source.index(start_marker)
        end = source.index(end_marker, start)
        return source[start:end]

    esc_fn = extract("function esc(s){", "async function init(){")
    inline_md = extract("function inlineMd(s){", "function appendCodeToken(")
    highlighter = extract("function appendCodeToken(", "function renderMarkdown(src){")
    markdown = extract("function renderMarkdown(src){", "function renderAssistant(text){")

    payloads = [
        ("sh", 'TCP_FALLBACK_HOST="premium.example"\n# reconnect\nRESTART_COOLDOWN=120'),
        ("python", 'def run():\n    return "ok"  # note'),
        ("json", '{"enabled": true, "count": 12}'),
        ("javascript", 'const endpoint = "https://example.test"; // note'),
        ("powershell", '$name = "node"\n# comment'),
        ("sh", 'echo "<tag attr=\'x\'> & text </script>"'),
    ]

    def fenced(lang: str, code: str) -> str:
        return f"```{lang}\n{code}\n```"

    content = "\n\n".join(fenced(lang, code) for lang, code in payloads)
    html = f"""<!doctype html><meta charset='utf-8'><div id='root'></div>
<script>
{esc_fn}
const rawCodeSources=new WeakMap();
{inline_md}
{highlighter}
{markdown}
const sourceText = {json.dumps(content, ensure_ascii=False).replace("</", "<\\/")};
const root = document.getElementById('root');
root.innerHTML = renderMarkdown(sourceText);
applyCodeHighlighting(root);
window.copyFromCode = (code) => rawCodeSources.get(code) ?? code.textContent ?? '';
</script>"""

    chromium = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    if not chromium:
        pytest.skip("No system Chromium executable is available")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox"])
        page = browser.new_page()
        page.set_content(html)
        page.evaluate("""() => {
            Object.defineProperty(navigator, 'clipboard', {value:{writeText: async text => {window.copiedCode = text;}}});
            document.querySelectorAll('.copy-code').forEach(btn => btn.addEventListener('click', () => {
                const codeElement=btn.closest('.code-card').querySelector('code');
                const code=rawCodeSources.get(codeElement)??codeElement.textContent??'';
                navigator.clipboard.writeText(code);
            }));
        }""")
        results = page.evaluate(
            """() => [...document.querySelectorAll('code[data-code-language]')].map(code => ({
                language: code.dataset.codeLanguage,
                innerText: code.innerText,
                textContent: code.textContent,
                copied: window.copyFromCode(code),
                hasStringToken: !!code.querySelector('.tok-string'),
                hasCommentToken: !!code.querySelector('.tok-comment'),
                textLeaksClass: /class="tok-(?:string|comment)">/.test(code.innerText)
            }))"""
        )
        copy_buttons = page.locator('.copy-code')
        clicked_copies = []
        for index in range(copy_buttons.count()):
            copy_buttons.nth(index).click()
            clicked_copies.append(page.evaluate('window.copiedCode'))
        browser.close()

    assert len(results) == len(payloads)
    assert clicked_copies == [code for _, code in payloads]
    for actual, (language, expected) in zip(results, payloads):
        assert actual["language"] == language
        assert actual["innerText"] == expected
        assert actual["textContent"] == expected
        assert actual["copied"] == expected
        assert not actual["textLeaksClass"]
    assert results[0]["hasStringToken"]
    assert results[0]["hasCommentToken"]
    assert results[1]["hasStringToken"] and results[1]["hasCommentToken"]
    assert results[2]["hasStringToken"]
    assert results[3]["hasStringToken"] and results[3]["hasCommentToken"]
    assert results[4]["hasStringToken"] and results[4]["hasCommentToken"]
