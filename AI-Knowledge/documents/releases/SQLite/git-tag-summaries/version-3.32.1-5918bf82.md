# SQLite — Git tag version-3.32.1

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.32.1
Сравнение с предыдущим тегом: version-3.32.0

## Коммиты в диапазоне

```text
d63c76fb3 2020-05-25 Version 3.32.1
b6907e299 2020-05-25 Extra assert() statements in the printf() logic.
0934d6404 2020-05-25 Defensive code that tries to prevent a recurrence of problems like the one described in ticket [7a5279a25c57adf1]
efc752b13 2020-05-25 Fix minor compile issues with optional extensions.
91960aa53 2020-05-25 Make sure variable declarations are at start of scope even when SQLITE_ENABLE_SNAPSHOT is used.
e859e43bb 2020-05-24 Version number to 3.32.1.
c37577bb2 2020-05-24 When rewriting a query for window functions, if the rewrite changes the depth of TK_AGG_FUNCTION nodes, be sure to adjust the Expr.op2 field appropriately.  Fix for ticket [7a5279a25c57adf1]
e40cc16b4 2020-05-24 Move some utility Walker callbacks into the walker.c source file, as they seem to belong there better.
ca74fbf6f 2020-05-24 Improvements to parse-tree tracing logic.  No changes in deliverable code.
16dc07f75 2020-05-24 Minor fix to a comment.  No code changes.
dd6c33d37 2020-05-23 Limit the "precision" of floating-point to text conversions in the printf() function to 100,000,000.  Fix for ticket [23439ea582241138].
8e50d65aa 2020-05-23 Improved bytecode comment.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
