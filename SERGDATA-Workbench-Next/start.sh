#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$(readlink -f "$0")")"

PYTHON=""
for candidate in python3.12 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'; then
    PYTHON="$candidate"
    break
  fi
done
if [[ -z "$PYTHON" ]]; then
  echo "Не найден Python 3.12+. Установи Python 3.12 или новее и повтори запуск." >&2
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  "$PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo
echo "Проверка окружения:"
.venv/bin/python -m workbench.doctor

echo
if [[ ! -f .env && -f .env.example ]]; then
  cp .env.example .env
  echo "Создан .env из шаблона. Отредактируй пути Knowledge MCP и PROJECT_ROOT в .env."
fi
exec .venv/bin/python main.py
