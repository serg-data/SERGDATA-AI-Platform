"""Normalize native OpenAI tool calls and strict LM Studio text-form calls.

Only complete, explicitly delimited calls for registered Workbench tools are
accepted. This is a compatibility adapter, not a general command interpreter.
"""
from __future__ import annotations

import json
import re
import uuid
from types import SimpleNamespace

_TOOL_BLOCK = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL | re.IGNORECASE)
_FUNCTION = re.compile(r"<function=([A-Za-z_][A-Za-z0-9_]*)>\s*(.*?)\s*</function>", re.DOTALL | re.IGNORECASE)
_PARAMETER = re.compile(r"<parameter=([A-Za-z_][A-Za-z0-9_]*)>\s*(.*?)\s*</parameter>", re.DOTALL | re.IGNORECASE)
# Some local chat templates serialize control tags with a literal backslash
# immediately before the opening angle bracket and after the closing bracket,
# e.g. \<tool_call>\ or \<function=search_knowledge>\. Normalize only
# recognized tool-call delimiters; never rewrite arbitrary code or user text.
_CONTROL_TAG = re.compile(
    r"(\\*)(</?(?:tool_call|function(?:=[A-Za-z_][A-Za-z0-9_]*)?|"
    r"parameter(?:=[A-Za-z_][A-Za-z0-9_]*)?)>)(\\*)",
    re.IGNORECASE,
)


def _normalize_control_tag_escaping(content: str) -> str:
    text = str(content or "")
    return _CONTROL_TAG.sub(lambda match: match.group(2), text)


def _value(raw: str):
    value = raw.strip()
    if not value:
        return ""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def _schemas(tools):
    result = {}
    for item in tools or []:
        function = item.get("function", {})
        if function.get("name"):
            result[function["name"]] = function.get("parameters", {})
    return result


def _validate(name, args, schema):
    if not isinstance(args, dict):
        raise ValueError("Аргументы инструмента должны быть объектом")
    properties = schema.get("properties", {})
    unknown = set(args) - set(properties)
    if unknown:
        raise ValueError(f"Неизвестные параметры {name}: {', '.join(sorted(unknown))}")
    missing = set(schema.get("required", [])) - set(args)
    if missing:
        raise ValueError(f"Не хватает параметров {name}: {', '.join(sorted(missing))}")
    for key, value in args.items():
        spec = properties[key]
        expected = spec.get("type")
        valid = {
            "string": lambda x: isinstance(x, str),
            "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
            "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
            "boolean": lambda x: isinstance(x, bool),
            "array": lambda x: isinstance(x, list),
            "object": lambda x: isinstance(x, dict),
        }.get(expected)
        if valid and not valid(value):
            raise ValueError(f"Параметр {key} должен иметь тип {expected}")
        if "enum" in spec and value not in spec["enum"]:
            raise ValueError(f"Недопустимое значение {key}: {value}")
    return args


def _normalize_argument_aliases(name: str, args: dict) -> dict:
    """Normalize narrowly-scoped aliases emitted by local model templates."""
    args = dict(args)
    if name == "read_uploaded_file" and "file_id" in args:
        if "attachment_id" in args and args["attachment_id"] != args["file_id"]:
            raise ValueError("Одновременно переданы конфликтующие file_id и attachment_id")
        args["attachment_id"] = args.pop("file_id")
    return args


def parse_text_tool_calls(content: str, tools):
    """Normalize text-form calls, retaining valid calls when a sibling is bad.

    Some local templates emit multiple <tool_call> blocks in one assistant
    response. One malformed block must not discard unrelated valid calls.
    The returned error describes only rejected blocks; the caller can execute
    accepted calls and ask the model to repair the remainder.
    """
    text = _normalize_control_tag_escaping(content)
    blocks = list(_TOOL_BLOCK.finditer(text))
    open_count = len(re.findall(r"<tool_call\s*>", text, re.IGNORECASE))
    if not blocks and open_count:
        return [], True, "Обнаружен незавершённый блок <tool_call>: отсутствует закрывающий тег."
    if open_count != len(blocks):
        return [], True, "Количество открывающих и закрывающих блоков <tool_call> не совпадает."
    if not blocks:
        return [], False, None

    schemas = _schemas(tools)
    calls = []
    errors = []
    for index, block in enumerate(blocks, 1):
        try:
            body = block.group(1).strip()
            # Qwen-style: <tool_call>{"name":"...","arguments":{...}}</tool_call>
            if body.startswith("{"):
                payload = json.loads(body)
                name = payload.get("name")
                args = payload.get("arguments", {})
            else:
                function = _FUNCTION.fullmatch(body)
                if not function:
                    raise ValueError("Неполный или неизвестный формат function-call")
                name, body = function.groups()
                args = {key: _value(value) for key, value in _PARAMETER.findall(body)}
                if name == "sandbox_run_check" and "mode" in args and "command" not in args:
                    args["command"] = args.pop("mode")
            if name not in schemas:
                raise ValueError(f"Неизвестный инструмент: {name}")
            args = _normalize_argument_aliases(name, args)
            args = _validate(name, args, schemas[name])
            calls.append(SimpleNamespace(
                id=f"textcall_{uuid.uuid4().hex}",
                type="function",
                function=SimpleNamespace(name=name, arguments=json.dumps(args, ensure_ascii=False)),
            ))
        except Exception as exc:
            errors.append(f"Вызов #{index}: {type(exc).__name__}: {exc}")

    error = "Не удалось принять часть текстовых вызовов инструмента: " + "; ".join(errors) if errors else None
    return calls, True, error


def contains_tool_call_markup(content: str) -> bool:
    """Return True when content contains a tool-call transport block, complete or partial.

    This is used only on final, tool-disabled model responses. Such a response
    must never expose pseudo tool calls as if they were executed commands.
    """
    text = _normalize_control_tag_escaping(content)
    return bool(re.search(r"<tool_call\b|<function\s*=", text, re.IGNORECASE))


def strip_text_tool_call_markup(content: str) -> str:
    """Remove transport markup before assistant content is fed back as prose."""
    text = _normalize_control_tag_escaping(content)
    text = _TOOL_BLOCK.sub("", text)
    # Do not carry an incomplete transport block into later model context.
    text = re.sub(r"<tool_call\b.*$", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()


def extract_tool_calls(message, tools):
    """Prefer native API calls; adapt a supported text format only if needed."""
    native = getattr(message, "tool_calls", None)
    if native:
        return list(native), False, None
    return parse_text_tool_calls(getattr(message, "content", "") or "", tools)


def visible_response_text(message, fallback=""):
    """Return only user-visible assistant content, never private reasoning.

    Some local OpenAI-compatible servers can finish with an empty `content`
    while populating `reasoning_content`. Reasoning is deliberately NOT used
    as a substitute: callers receive an explicit, safe fallback instead.
    """
    content = getattr(message, "content", None)
    if isinstance(content, str) and content.strip():
        return content
    return fallback


def empty_response_notice(message, stage="ответа"):
    """Explain an empty visible response without exposing reasoning tokens."""
    reasoning = getattr(message, "reasoning_content", None)
    if isinstance(reasoning, str) and reasoning.strip():
        return (
            f"Модель завершила генерацию, но не вернула пользовательский текст ({stage}). "
            "Текст присутствует только во внутреннем поле reasoning_content и не был "
            "показан во избежание раскрытия внутренних рассуждений. Повтори запрос "
            "или проверь формат ответа/шаблон модели в LM Studio."
        )
    return f"Модель завершила генерацию без пользовательского текста ({stage}). Повтори запрос."
