SERGDATA Workbench — Git Doctor v3 (read-only)

Установка: остановить Workbench, сделать резервную копию, распаковать содержимое архива поверх корня F:\SERGDATA-Workbench-Next с сохранением путей, запустить Workbench и открыть «База знаний».

Кнопка «Git Doctor · диагностика» находится рядом с «Git-репозитории». Инструмент использует только repositories.json и локальные клоны AI-Knowledge/code. Проверка читает HEAD, ветку и git status --porcelain=v2. Команды восстановления, reset, add, restore, checkout, pull и fetch не выполняются. Индекс базы знаний и внешние источники не меняются. Правая Git-панель не изменяется.

Файлы патча: main.py, static/index.html, static/app.js, static/style.css.
