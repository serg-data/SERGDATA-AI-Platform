# Обновление интерфейса: читаемость и сохранение размеров

## Исправления
- В светлой теме повышен контраст карточки статистики токенов: фон, подписи, значения и индикатор.
- В светлой теме исправлены цвета заголовка, пояснений, поля ввода и результатов локального PowerShell.
- Сохранение высоты поля основного сообщения и поля команды PowerShell в `localStorage`.
- Существующее сохранение размеров областей сообщений и PowerShell через разделитель оставлено без изменения.

## Проверки
- `PYTHONPATH=. pytest -q --ignore=tests/test_autonomy_processes.py`: 53 passed.
- `PYTHONPATH=. pytest -q tests/test_autonomy_processes.py -k 'not process_registry_streams_and_stops'`: 2 passed, 1 deselected (известный нестабильный тест исключён).
- `node --check static/app.js`: успешно.
- `python -m compileall -q .`: успешно.
- Полноценная проверка в браузере Windows/LM Studio не выполнялась.
