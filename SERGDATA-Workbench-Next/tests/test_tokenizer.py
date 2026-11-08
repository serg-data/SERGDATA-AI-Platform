import sys
from types import ModuleType, SimpleNamespace

from workbench.tokenizer import LMStudioTokenCounter


def test_lmstudio_token_counter_uses_model_template_and_tokenizer(monkeypatch):
    calls = {}

    class FakeModel:
        def apply_prompt_template(self, chat):
            calls['chat'] = chat
            return '<prompt> ' + ' '.join(m['content'] for m in chat['messages'])

        def tokenize(self, text):
            return text.split()

        def get_context_length(self):
            return 32768

    class FakeChat:
        @staticmethod
        def from_history(payload):
            return payload

    fake = ModuleType('lmstudio')
    fake.Chat = FakeChat
    fake.configure_default_client = lambda *args, **kwargs: calls.update(host=args[0], auth=kwargs)
    fake.set_sync_api_timeout = lambda value: calls.update(timeout=value)
    fake.llm = lambda model_id: calls.update(model=model_id) or FakeModel()
    monkeypatch.setitem(sys.modules, 'lmstudio', fake)

    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b'{"data":[{"id":"qwen-test","state":"loaded"}]}'

    monkeypatch.setattr('workbench.tokenizer.urlopen', lambda request, timeout=0: FakeResponse())
    counter = LMStudioTokenCounter('http://127.0.0.1:1234/v1', 'lm-studio')
    result = counter.count('qwen-test', [{'role': 'user', 'content': 'hello world'}],
                           [{'type': 'function', 'function': {'name': 'search'}}])

    assert result['model_context_limit'] == 32768
    assert result['messages_tokens'] > 0
    assert result['tools_tokens_estimate'] > 0
    assert result['tokenizer_status'] == 'model_tokenizer'
    assert calls['host'] == '127.0.0.1:1234'
    assert calls['model'] == 'qwen-test'


def test_legacy_usage_table_gets_additive_column():
    import sqlite3
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from workbench.db import Store

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'old.sqlite3'
        conn = sqlite3.connect(path)
        conn.execute('CREATE TABLE usage(id INTEGER PRIMARY KEY AUTOINCREMENT,branch_id INTEGER NOT NULL,model TEXT,prompt_tokens INTEGER,completion_tokens INTEGER,total_tokens INTEGER,created_at TEXT NOT NULL)')
        conn.execute("INSERT INTO usage(branch_id,model,prompt_tokens,completion_tokens,total_tokens,created_at) VALUES(1,'m',9,3,12,'2026-01-01T00:00:00+00:00')")
        conn.commit(); conn.close()

        Store(path)
        conn = sqlite3.connect(path)
        columns = {r[1] for r in conn.execute('PRAGMA table_info(usage)')}
        row = conn.execute('SELECT prompt_tokens,completion_tokens,total_tokens FROM usage').fetchone()
        conn.close()
        assert 'turn_message_id' in columns
        assert row == (9, 3, 12)


def test_token_counter_does_not_jit_load_unloaded_model(monkeypatch):
    calls = {'llm': 0}

    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b'{"data":[{"id":"qwen-test","state":"not-loaded"}]}'

    fake = ModuleType('lmstudio')
    fake.configure_default_client = lambda *args, **kwargs: None
    fake.llm = lambda model_id: calls.update(llm=calls['llm'] + 1)
    monkeypatch.setitem(sys.modules, 'lmstudio', fake)
    monkeypatch.setattr('workbench.tokenizer.urlopen', lambda request, timeout=0: FakeResponse())

    counter = LMStudioTokenCounter('http://127.0.0.1:1234/v1')
    try:
        counter.context_length('qwen-test')
        assert False, 'Ожидалось безопасное прекращение для незагруженной модели'
    except RuntimeError as exc:
        assert 'не загружена' in str(exc)
    assert calls['llm'] == 0
