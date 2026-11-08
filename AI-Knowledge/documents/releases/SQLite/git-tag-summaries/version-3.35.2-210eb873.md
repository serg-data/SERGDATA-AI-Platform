# SQLite — Git tag version-3.35.2

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.35.2
Сравнение с предыдущим тегом: version-3.35.1

## Коммиты в диапазоне

```text
176b04c47 2021-03-17 Version 3.35.2
8b04094c4 2021-03-17 Fix a harmless compiler warning in the appendvfs.c extension.
51ddfef74 2021-03-17 If there are already 500 or more simple SELECTs in a query, do not add more by flattening UNION ALL sub-queries into parent join queries.
42470513b 2021-03-17 Fix a problem in sqldiff virtual table hanlding to do with tab and other non-space whitespace characters in the CREATE VIRTUAL TABLE statement.
a7d8d4a07 2021-03-16 Date/time functions with no arguments (ex: date() or time()) should be non-deterministic.  Fix for ticket [2c6c8689fb5f3d2f].
0d3485f01 2021-03-16 Increase the version number to 3.35.2.
3fee67533 2021-03-16 Comment and stylistic changes to the appendvfs.c implementation.
776a578c2 2021-03-16 Fix a problem with ALTER TABLE RENAME COLUMN when used on a schema that features generated columns.
67d4bbf6c 2021-03-16 Fix assert typo.
5cad178b8 2021-03-16 Fix appendvfs bug exposed with bigger files, and add tests for such conditions.
21f0f694f 2021-03-16 Create new branch named "appendvfs_fix"
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
