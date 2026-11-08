SERGDATA Workbench — Git Doctor v1

Состав патча:
- workbench/git_manager.py — диагностика согласованности HEAD/index/worktree и безопасное адресное восстановление одной записи индекса.
- workbench/main.py — API GET /api/git/doctor и POST /api/git/doctor/repair.
- workbench/static/index.html — кнопки диагностики и исправления в панели Git.
- workbench/static/app.js — GUI-обработчики, повторная диагностика и подтверждение исправления.
- tests/test_git_manager.py — тесты Git Doctor.

Установка:
1. Остановить Workbench.
2. Сделать резервную копию текущей папки Workbench.
3. Распаковать содержимое архива поверх корня проекта, сохранив структуру папок.
4. Запустить Workbench и открыть нужный проект → Git → «Диагностика Git».
5. Кнопка «Исправить безопасно» появится только для подтверждённого случая, когда HEAD, индекс и файл содержат один и тот же blob, но Git сообщает staged deletion.

Безопасность:
- Диагностика ничего не меняет.
- Перед исправлением создаётся резервная копия .git/index с суффиксом .doctor-backup-<timestamp>.
- Исправляется только одна запись индекса; содержимое рабочего файла не перезаписывается.
- Перед исправлением доказательство повторно проверяется на сервере.
- При неудаче исходный индекс восстанавливается из резервной копии.
- Неизвестные untracked-файлы не удаляются.

Проверки в среде сборки:
- python -m compileall -q workbench — OK
- node --check workbench/static/app.js — OK
- pytest tests/test_git_manager.py — 7 passed
- Полный набор: 243 passed, 3 failed. Все три сбоя относятся к уже существовавшим несоответствиям в корневой папке static/ и не связаны с изменёнными файлами workbench/: test_frontend_cache_version_is_bumped_for_patch, test_frontend_polls_transcript_while_agent_request_is_active, test_vertical_resize_handles_are_visible_and_resizable.

Важно: патч собран на основе архива SERGDATA-Workbench-Next(20261107-143815).zip. Он не устанавливался на рабочий компьютер и не изменял рабочую базу AI-Knowledge.
