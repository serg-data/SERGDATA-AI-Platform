SERGDATA Workbench — Git Doctor v5 (только исправление ширины окна)

Установка:
1. Остановить Workbench.
2. Сделать резервную копию static\index.html и static\style.css.
3. Распаковать архив в F:\SERGDATA-Workbench-Next с заменой файлов.
4. Запустить Workbench и открыть «База знаний».

В архиве только static\index.html и static\style.css.
В index.html обновлена версия CSS в URL, чтобы браузер гарантированно загрузил новые стили.
В style.css окно #knowledgeDialog расширено до 1040 px (с учётом ширины экрана),
кнопки переносятся, длинные строки не расширяют окно.

Не заменяются main.py, static\app.js, скрипты индексации, база данных и repositories.json.
Полная индексация и правая Git-панель не затрагиваются.
