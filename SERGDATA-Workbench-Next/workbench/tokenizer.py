"""LM Studio model-aware prompt token estimation.

The exact prompt count returned by LM Studio's OpenAI-compatible API remains
canonical after an inference request. This module provides a preflight count
using the loaded model's tokenizer and chat template; tool-schema serialization
is estimated separately because the OpenAI-compatible API does not expose a
standalone HTTP token-count endpoint.
"""
from __future__ import annotations

import json
import threading
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class LMStudioTokenCounter:
    def __init__(self, base_url: str, api_key: str = ""):
        self.base_url = base_url
        self.api_key = api_key or ""
        self._configured = False
        self._models = {}
        self._sdk = None
        self._lock = threading.RLock()
        self._loaded_verified_at = {}

    def _connect(self):
        if self._sdk is not None:
            return self._sdk
        import lmstudio as lms  # Optional at runtime; required in requirements.txt.

        parsed = urlsplit(self.base_url)
        if not parsed.hostname:
            raise RuntimeError("Некорректный LM_BASE_URL")
        host = f"{parsed.hostname}:{parsed.port or (443 if parsed.scheme == 'https' else 80)}"
        if not self._configured:
            # Configure before the first convenience-API call, as required by LM Studio SDK.
            if hasattr(lms, 'set_sync_api_timeout'):
                lms.set_sync_api_timeout(3)
            token = self.api_key if self.api_key and self.api_key != "lm-studio" else None
            if token:
                lms.configure_default_client(host, api_token=token)
            else:
                lms.configure_default_client(host)
            self._configured = True
        self._sdk = lms
        return lms

    def _assert_model_loaded(self, model_id: str) -> None:
        """Refuse SDK access to unloaded models: lms.llm() may JIT-load them."""
        now = time.monotonic()
        if now - self._loaded_verified_at.get(model_id, 0.0) < 3.0:
            return
        parsed = urlsplit(self.base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        headers = {}
        token = self.api_key if self.api_key and self.api_key != "lm-studio" else None
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(base + "/api/v0/models", headers=headers)
        try:
            with urlopen(request, timeout=1.5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise RuntimeError(f"Не удалось проверить состояние модели LM Studio: {type(exc).__name__}") from exc
        item = next((x for x in payload.get("data", []) if x.get("id") == model_id), None)
        if not item:
            raise RuntimeError(f"Модель {model_id} не найдена в /api/v0/models")
        if item.get("state") != "loaded":
            self._loaded_verified_at.pop(model_id, None)
            raise RuntimeError(f"Модель {model_id} не загружена в LM Studio; токенизатор не запускал её загрузку")
        self._loaded_verified_at[model_id] = now

    def _model(self, model_id: str):
        self._assert_model_loaded(model_id)
        lms = self._connect()
        model = self._models.get(model_id)
        if model is None:
            model = lms.llm(model_id)
            self._models[model_id] = model
        return lms, model

    def context_length(self, model_id: str) -> int:
        with self._lock:
            _, model = self._model(model_id)
            return int(model.get_context_length())

    def count(self, model_id: str, messages: list[dict], tools: list[dict] | None = None) -> dict:
        with self._lock:
            lms, model = self._model(model_id)

            # Match the actual chat formatting selected by the loaded GGUF/model template.
            chat = lms.Chat.from_history({"messages": messages})
            formatted = model.apply_prompt_template(chat)
            message_tokens = len(model.tokenize(formatted))

            # Tools travel outside the chat messages in /v1/chat/completions.
            # Count their JSON payload with the same tokenizer, but keep it clearly
            # identified as an estimate because LM Studio adds its own tool template.
            tool_tokens = 0
            if tools:
                tool_payload = json.dumps(tools, ensure_ascii=False, separators=(",", ":"))
                tool_tokens = len(model.tokenize(tool_payload))
            overhead_tokens = 64 if tools else 0
            context_length = int(model.get_context_length())
            return {
                "messages_tokens": message_tokens,
                "tools_tokens_estimate": tool_tokens,
                "format_overhead_estimate": overhead_tokens,
                "estimated_prompt_tokens": message_tokens + tool_tokens + overhead_tokens,
                "model_context_limit": context_length,
                "tokenizer_status": "model_tokenizer",
                "estimate_method": "LM Studio: шаблон чата и токенизатор загруженной модели; схема инструментов оценена отдельно",
            }
