# Исправленный комплект Runtime Context Preservation Fix

## Важно
Этот комплект заменяет **два согласованных файла**: `workbench/agent.py` и `workbench/tool_call_adapter.py`.
Первый предыдущий архив содержал только `agent.py`, что привело к ImportError на установке. Этот комплект исправляет упаковку и устанавливает согласованную пару.

## Установка
1. Останови Workbench.
2. Распакуй архив во временную папку.
3. Открой PowerShell в распакованной папке.
4. Запусти:
   ```powershell
   .\install-runtime-context-fix.ps1 -Root 'F:\SERGDATA-Workbench-Next'
   ```
5. Скрипт сначала проверит SHA-256 обоих текущих файлов. Если хотя бы один отличается, остановится **до изменения файлов**.
6. При совпадении создаст резервные копии обоих файлов и заменит их. При ошибке копирования восстановит обе копии.

## Откат
Останови Workbench и восстанови оба файла из резервных копий с одинаковой меткой времени, которую показал установщик:
```powershell
Copy-Item 'F:\SERGDATA-Workbench-Next\workbench\agent.py.bak-YYYYMMDD-HHMMSS' 'F:\SERGDATA-Workbench-Next\workbench\agent.py' -Force
Copy-Item 'F:\SERGDATA-Workbench-Next\workbench\tool_call_adapter.py.bak-YYYYMMDD-HHMMSS' 'F:\SERGDATA-Workbench-Next\workbench\tool_call_adapter.py' -Force
```

## Не затрагивается
`.env`, `.workbench`, SQLite, credentials, uploads, SSH-профили, Approval Queue, frontend, настройки проекта.

## SHA-256
- исходный agent.py: `6e0d59d3bf94e112b4d0d1bbc73db870f2a4b0584349ca327e660df80b5b8c36`
- исправленный agent.py: `fea660aa8f32c41384856c26c5fec9fb667e108937cd82aaf4052131e2368c4f`
- исходный tool_call_adapter.py: `824faed016fc7061f585483bc8fb817128087e67e1a893c8b6c924aaafed72a2` (адаптер согласован с импортами исправленного agent.py)

## Проверки
Этот архив исправляет обнаруженную несовместимость комплекта и включает регрессионные тесты для компактизации контекста. Перед установкой обязательно дождись успешного SHA-256 preflight. Полный живой тест LM Studio должен быть выполнен отдельно после запуска.
