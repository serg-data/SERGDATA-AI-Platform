# SERGDATA Workbench — Agent Tool-call / external read patch v2

Дата: 07.11.2026

## Почему предыдущий патч не устранил остановку

В тесте от 07.11 модель вывела управляющие XML-теги с обратными слешами вокруг delimiters: `\<tool_call>\`, `\<function=...>\`, `\<parameter=...>\` и закрывающие варианты. Предыдущий адаптер распознавал только обычные теги `<tool_call>`. Из-за этого `text_call_detected=False`, адаптер не просил исправить формат, а непустой текст возвращался как обычный ответ. Агентный цикл штатно завершался.

## Что изменено в v2

- Перед разбором нормализуются только известные управляющие теги `tool_call`, `function`, `parameter`; снятие обратных слешей не применяется к произвольному тексту/коду.
- Нормализация выполняется также перед удалением служебной разметки из истории модели.
- Сохранены частичные пакеты: допустимые вызовы выполняются, только отклонённые отправляются модели на исправление.
- Сохранён узкий алиас `read_uploaded_file.file_id` → `attachment_id`.
- Сохранено явное read-only разрешение на внешний зарегистрированный проект: только при точном корневом пути в текущем запросе. Запись/запуск внешних команд не разрешены.

## Установка

1. Останови Workbench через `Ctrl+C`.
2. Создай резервные копии:

```powershell
$root = 'F:\SERGDATA-Workbench-Next'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item "$root\workbench\agent.py" "$root\workbench\agent.py.bak-$stamp"
Copy-Item "$root\workbench\tool_call_adapter.py" "$root\workbench\tool_call_adapter.py.bak-$stamp"
```

3. Распакуй архив поверх `F:\SERGDATA-Workbench-Next`, заменив файлы.
4. Не заменяй `.env`, `.workbench`, базу SQLite, `credentials.dpapi`, SSH-ключи и пользовательские данные.
5. Запусти Workbench обычным способом.

## Проверка

В новой задаче напиши полный точный корень зарегистрированного внешнего проекта прямо в тексте запроса, например:

```text
Проведи read-only аудит исходников SERGDATA Workbench в F:\SERGDATA-Workbench-Next.
Перечисли файлы, затем прочитай main.py и workbench/agent.py. Ничего не изменяй и не запускай.
```

Ожидаемые журнальные маркеры: `TOOL_CALL_ADAPTER_OK ... accepted=N` либо `TOOL_CALL_ADAPTER_REJECTED ... accepted=N`. Для последнего теста модель должна выполнить оба вызова инструмента, а не показывать XML-разметку как ответ.

Проверки после распаковки:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q workbench tests
```

## Откат

Останови Workbench и восстанови две резервные копии, используя фактический `$stamp`:

```powershell
Copy-Item "$root\workbench\agent.py.bak-$stamp" "$root\workbench\agent.py" -Force
Copy-Item "$root\workbench\tool_call_adapter.py.bak-$stamp" "$root\workbench\tool_call_adapter.py" -Force
```

Патч не содержит миграций БД и не меняет `.env`, Approval Queue, движок выполнения или SSH-профили. Живой тест LM Studio ещё не выполнен.
