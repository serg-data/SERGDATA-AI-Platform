# SQLite — Git tag version-3.31.1

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.31.1
Сравнение с предыдущим тегом: version-3.31.0

## Коммиты в диапазоне

```text
562fd18b9 2020-01-27 Version 3.31.1
f54f10544 2020-01-27 Update the version number to 3.31.1.
532b0d23f 2020-01-27 Revise the layout of filenames in the Pager object so that it is unchanged from prior versions.  It turns out that some important 3rd-party software does questionable pointer manipulations on those filenames that depend on that legacy layout.  Technical this is a misuse of SQLite by the 3rd-party software, but we want to avoid unnecessary breakage.
9a3bdeba3 2020-01-23 Fix typos in the sqlite3ext.h header file that prevent some newer APIs from being accessed from loadable extensions.
8122c6e9b 2020-01-23 Fix variable declaration issue seen with MSVC.
78b522032 2020-01-22 Fix a NEVER() macro that can be true if compiled with SQLITE_ENABLE_UNKNOWN_SQL_FUNCTION. Ticket [b985f0bd1636d9bc]
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
