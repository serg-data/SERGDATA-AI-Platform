import pytest
from workbench.db import Store


def test_agent_settings_persist_and_validate(tmp_path):
    store = Store(tmp_path / "settings.sqlite3")
    defaults = store.get_app_settings()
    assert defaults["context_limit"] == 50000
    assert defaults["summary_message_max_chars"] == 15000
    saved = store.set_app_settings({
        "context_limit": 65536,
        "max_tool_rounds": 12,
        "max_tool_calls": 32,
        "temperature": 0.1,
        "request_timeout": 300,
        "summary_message_max_chars": 30000,
    })
    assert saved["context_limit"] == 65536
    assert saved["max_tool_rounds"] == 12
    assert saved["max_tool_calls"] == 32
    assert saved["temperature"] == 0.1
    assert saved["request_timeout"] == 300
    assert saved["summary_message_max_chars"] == 30000
    # A new Store instance simulates an application/server restart.
    reopened = Store(tmp_path / "settings.sqlite3")
    assert reopened.get_app_settings() == saved


def test_agent_settings_reject_unsafe_ranges(tmp_path):
    store = Store(tmp_path / "settings.sqlite3")
    with pytest.raises(ValueError):
        store.set_app_settings({"context_limit": 1000})
    with pytest.raises(ValueError):
        store.set_app_settings({"max_tool_calls": 1000})
    with pytest.raises(ValueError):
        store.set_app_settings({"temperature": 1.5})
    with pytest.raises(ValueError):
        store.set_app_settings({"request_timeout": 1})
    with pytest.raises(ValueError):
        store.set_app_settings({"summary_message_max_chars": 999})
    with pytest.raises(ValueError):
        store.set_app_settings({"summary_message_max_chars": 50001})
