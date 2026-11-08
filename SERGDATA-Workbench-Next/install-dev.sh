#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$(readlink -f "$0")")"
if [[ ! -x .venv/bin/python ]]; then
  echo "Сначала запусти ./start.sh для создания .venv и установки основных зависимостей." >&2
  exit 1
fi
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m workbench.doctor
