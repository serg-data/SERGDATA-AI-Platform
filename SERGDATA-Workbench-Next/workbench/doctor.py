"""Cross-platform environment diagnostics for SERGDATA Workbench."""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_MODULES = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "openai": "openai",
    "mcp": "mcp",
    "python-dotenv": "dotenv",
    "tiktoken": "tiktoken",
    "python-multipart": "multipart",
    "pypdf": "pypdf",
    "python-docx": "docx",
    "lmstudio": "lmstudio",
    "paramiko": "paramiko",
}
OPTIONAL_MODULES = {
    "pytest": "pytest",
    "ruff": "ruff",
    "beautifulsoup4": "bs4",
    "html5lib": "html5lib",
}
TOOLS = ("git", "node", "npm", "ssh", "bash", "pwsh", "powershell")


def _module_available(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        # A dependency may already be imported/mocked without a module spec.
        return module in sys.modules and sys.modules[module] is not None


def _version(name: str, executable: str) -> str:
    candidates = {
        "git": ["--version"], "node": ["--version"], "npm": ["--version"],
        "ssh": ["-V"], "bash": ["--version"], "pwsh": ["--version"],
        "powershell": ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
    }
    try:
        result = subprocess.run(
            [executable, *candidates[name]], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=4, check=False,
        )
        value = (result.stdout or result.stderr).strip().splitlines()
        return value[0][:160] if value else "версия не определена"
    except (OSError, subprocess.TimeoutExpired):
        return "версия не определена"


def inspect_environment() -> dict:
    required = {}
    for package, module in REQUIRED_MODULES.items():
        required[package] = _module_available(module)

    optional = {}
    for package, module in OPTIONAL_MODULES.items():
        present = _module_available(module)
        version = None
        if present:
            try:
                version = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                pass
        optional[package] = {"installed": present, "version": version}

    commands = {}
    for name in TOOLS:
        path = shutil.which(name)
        commands[name] = {"installed": path is not None, "path": path,
                          "version": _version(name, path) if path else None}

    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "python_supported": sys.version_info >= (3, 12),
        "venv": sys.prefix != getattr(sys, "base_prefix", sys.prefix),
        "required_packages": required,
        "optional_packages": optional,
        "commands": commands,
        "project_directory": str(Path.cwd()),
        "missing_required": [name for name, ok in required.items() if not ok],
    }


def print_report(report: dict) -> None:
    print("SERGDATA Workbench — проверка окружения")
    print(f"ОС: {report['system']} ({report['platform']})")
    print(f"Python: {report['python_version']} — {'OK' if report['python_supported'] else 'нужен Python 3.12+'}")
    print(f"Интерпретатор: {report['python_executable']}")
    print(f"Виртуальное окружение: {'да' if report['venv'] else 'нет (рекомендуется .venv)'}")
    print("\nОбязательные Python-пакеты:")
    for name, installed in report["required_packages"].items():
        print(f"  [{'OK' if installed else 'НЕТ'}] {name}")
    print("\nДополнительные Python-пакеты (не обязательны для запуска):")
    for name, info in report["optional_packages"].items():
        suffix = f" ({info['version']})" if info["version"] else ""
        print(f"  [{'есть' if info['installed'] else 'нет'}] {name}{suffix}")
    print("\nВнешние инструменты (обнаружение, не установка):")
    for name, info in report["commands"].items():
        detail = f" — {info['version']}" if info["version"] else ""
        print(f"  [{'есть' if info['installed'] else 'нет'}] {name}{detail}")
    if report["missing_required"]:
        print("\nНе хватает обязательных пакетов. Выполни: python -m pip install -r requirements.txt")
    if not report["python_supported"]:
        print("Требуется Python версии 3.12 или новее.")
    print("\nОтсутствие Node.js/Git/SSH не мешает запуску Workbench, но отключает связанные проверки или возможности.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверка зависимостей и системных инструментов Workbench")
    parser.add_argument("--json", action="store_true", help="вывести машинно-читаемый JSON")
    args = parser.parse_args()
    report = inspect_environment()
    if args.json:
        import json
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)
    return 1 if report["missing_required"] or not report["python_supported"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
