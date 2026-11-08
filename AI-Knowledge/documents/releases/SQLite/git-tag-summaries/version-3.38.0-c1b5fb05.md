# SQLite — Git tag version-3.38.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.38.0
Сравнение с предыдущим тегом: version-3.37.0

## Коммиты в диапазоне

```text
98095e394 2022-02-22 Version 3.38.0
60f3657b4 2022-02-22 Fix an undersized memory allocation in the test harness for RTREE.  This error was in test logic only, not in the SQLite library itself. [forum:/forumpost/35470a0a72a005e1|forum post 35470a0a72a005e1]
16f56e841 2022-02-21 Fix compiler warnings for older compilers (ex: gcc 4.0.1 powerpc-apple-darwin).
a12500005 2022-02-21 Remove stray tab characters from auxiliary source code files.
91260dcf8 2022-02-21 Add SQLITE_OMIT_JSON to the compile-time option test sequence.
d01a1bd94 2022-02-21 Do not allow error messages from sqlite3NestedParse() to leak up into the main parse.
a7919add6 2022-02-19 Improve .backup and .save help text
1ff855b22 2022-02-19 Add a NEVER() to a branch that is unreachable for STAT4.
b15a3940d 2022-02-17 Enhance the documentation on sqlite3_stmt_readonly() to explain that EXPLAIN and EXPLAIN QUERY PLAN do not affect the return value.  Add test cases to verify this.  Add new test cases and requirements marks for complete requirements test coverage on this interface.
dedd51aed 2022-02-17 Remove references to the now-defunct SQLITE_ENABLE_JSON1 compile-time option.
24ea5fb3e 2022-02-17 Fix a testing error on Windows that was recently added to shell5.test.
be4e3c88f 2022-02-16 Make the sqlite3_error_offset() interface accessible from TCL using the new "erroroffset" method on the sqlite3 object.
537a6bf18 2022-02-15 Improved rendering of floating point numbers without a fractional part in ".dump" output from the CLI. [forum:/forumpost/550d877659f37cb2|Forum post 550d877659f37cb2].
0ca098835 2022-02-15 New assert() statements to help prove correctness of memjournal.c.
e63b7bdac 2022-02-14 Generalize the in-memory journal so that it is able to accept writes that begin at any offset less than or equal to the current file size.
9a4e88604 2022-02-14 Minor correction to the early corruption detection added by [a6fda39e81d0da98|check-in a6fda39e81d0da98] so that it works even if the page being cleared in page 1 of the database.
0aa094511 2022-02-14 Fix a bad assert() (it needs an "||CORRUPT_DB" term) in b-tree, discovered by dbsqlfuzz.
336338614 2022-02-14 CLI's .import column rename made more minimal, and reports renames.
dfcb11de1 2022-02-12 Do not run merge1.test with SQLITE_OMIT_VIRTUALTABLE builds.
02ede43da 2022-02-12 Fix a possible user-after-free in ALTER TABLE found by asan.
8443505dc 2022-02-12 Update fuzz.test to account for a change in error message made in the core.
af7b8dcb5 2022-02-12 Avoid dropping SQLITE_TOOBIG errors in the quote() function.
43a196a3b 2022-02-12 For .import auto-column, aid build-time override of rename decoration.
0a704c314 2022-02-12 Fix auto-column bug noted by post https://sqlite.org/forum/forumpost/d102c15d63
f17f60755 2022-02-11 Fix a test in without_rowid1.test so that it is disabled without ALTER TABLE support, as it uses ALTER TABLE.
7b57aa3da 2022-02-11 Update some OOM tests of the ALTER TABLE command to account for an error message which may be returned if opening the temp db fails.
eba21cd4b 2022-02-11 Load recent dbsqlfuzz finds into test/fuzzdata8.db.
11fc3c0fa 2022-02-11 Reference the wayback machine for the dead hyperlink to the MS support page in the comments about why the extra typedef for va_arg().  No code changes.
4ba1c5cc4 2022-02-11 Fix an assert() in the pager by adding "|| CORRUPT_DB", in as much as the assert() is not necessarily true if the database size in the header is wrong.  dbsqlfuzz f2f996065b90988aa9b0ae425b66dbb296546a08.
63a47336a 2022-02-11 Fix a problem in [c006515ae6faff65] causing an assert() to fail with some build configurations.
85548fac8 2022-02-11 Use the enhanced SQLITE_TESTCTRL_LOCALTIME_FAULT (2) capability to do better testing of the 'localtime' and 'utc' modifiers to date/time functions.
a03372745 2022-02-11 Upon .import column renaming, issue message saying so. Test this.
fa3ee3b10 2022-02-11 Fix the bind2.test test script so that it works even if SQLITE_ENABLE_PREUPDATE_HOOK is not defined. Fix for test-case breakage from check-in [c006515ae6faff65].
0d58ae010 2022-02-11 Work around the MSVC bug that prevents the use of function pointer types in the second argument of va_arg() by adding a typedef.
4c5c6214b 2022-02-11 CLI auto-column rename revamped after forum discussion.
b30af022d 2022-02-10 Fix SQLITE_TESTCTRL_LOCALTIME_FAULT so that it works even if mutexes are enabled.
d7e185ce5 2022-02-10 Enhance SQLITE_TESTCTRL_LOCALTIME_FAULT so that is able to install an alternative localtime() interface so that the localtime logic an be better tested.
eadccaa92 2022-02-10 Performance improve to the 'localtime' and 'utc' modifiers for date/time functions.
522608d3a 2022-02-10 Faster implementation of the date(), time(), and datetime() functions.
ddd3fe6fc 2022-02-10 Fix the test harness so that it builds without SQLITE_ENABLE_PREUPDATE_HOOK. Has been broken since [c006515ae6faff65].
58a53d6e7 2022-02-10 A CLI feature. auto .import (new table) columns. WIP
208b7141d 2022-02-10 Create new branch named "auto-column"
0d3636860 2022-02-10 Fix a typo in documentation.  No code changes.
e2adc0eea 2022-02-09 When process first moves a database into WAL mode and then tries to run sqlite3_wal_checkpoint() without first performing a transaction, first try to run a synthesized transaction to get the Pager caught up before attemptingn the checkpoint. [forum:/forumpost/fd0f19d229156939|forum post fd0f19d229156939].
252fe67bd 2022-02-09 Fix a problem with using sqlite3_bind_value() with sqlite3_value objects obtained from sqlite3_preupdate_new() when an integer value is written to a column with real affinity.
9f4ce3b19 2022-02-08 Writes to the subjournal should be all-or-nothing.  Fix for dbsqlfuzz fe3c397fb90029313446c4e0f4a6cd0c81dd9621.
4e532958c 2022-02-08 Provide sqlite3_error_offset() data for some new errors.
07fc85a2b 2022-02-08 comment-only change to sqlite3.h
633c79828 2022-02-08 Do not show the error code number of CLI error messages unless the error is something other than 1 (SQLITE_ERROR).
3e46db21d 2022-02-08 Improved error message formatting in the shell.  Distinguish between "Parse errors" and "Runtime errors".
e1c474312 2022-02-07 Disable the sqlite3_error_offset() when the error occurs in a trigger or view or some other bit of text that is not part of the original statement.
6e85b27cb 2022-02-07 When create table/view fails due to name taken, say which took it.
5d20a2181 2022-02-06 Fix unreachable branches in the sqlite3_error_offset() logic.
51896e6fd 2022-02-06 The sqlite3_vtab_in() interface should return false for a vector IN constraint.
89e9baa2c 2022-02-06 With the new ALTER TABLE under PRAGMA writable_schema=ON processing, do not ignore non-parser errors such as OOMs.
2ef111168 2022-02-06 Faster computation of Expr.nHeight.
17a93ae1b 2022-02-06 Record the error offset on INTEGER tokens.
62fc069eb 2022-02-06 Further improvements to localization of errors in input SQL.
4f77c9208 2022-02-05 Enhance sqlite3_error_offset() to report the position of unresolved identifiers.
796588ae0 2022-02-05 Record the position of many identifiers in the parse using the new Expr.w.iOfst field.  This is done with the idea of providing offset results for sqlite3_error_offset() for a more kinds of errors, though that part is not yet implemented.
4734b3f9b 2022-02-05 Update stale evidence marks on sqlite3_vtab_rhs_value() test cases.
569c10566 2022-02-05 Fix a NULL pointer dereference that can occur after OOM.  Problem introduced by check-in [197cbabf1767d060].
6c758900c 2022-02-05 Fix documentation typo.
d515ea5b5 2022-02-05 Typo fixes in documentation.
bcd60d20a 2022-02-04 Test case for permissive ALTER TABLE RENAME when writable_schema=ON.
10d29c7a9 2022-02-04 One more case of disabling errors for ALTER TABLE RENAME when writable_schema=ON.
0fab10991 2022-02-04 Add a compile-time option to include vt02.c in fuzzcheck.
5a80050dd 2022-02-04 Allow ALTER TABLE RENAME COLUMN to proceed even if there are errors in the schema, as long as PRAGMA writable_schema=ON is active.
69b0ce33f 2022-02-04 Fix various harmless compiler warnings.
02e3e0413 2022-02-04 For the MULTI-INDEX-OR optimization, when pushing down WHERE clause terms from the main query into the various OR-term subqueries, do not push down slices of a vector comparison, since the right-hand operand of the comparison might have only been initialized in a different OR branch that was not taken. dbsqlfuzz 80a9fade844b4fb43564efc972bcb2c68270f5d1.
7f1c11194 2022-02-03 Minor typo fix in comment. No code changes.
697c50b94 2022-02-03 Do not allow the vdbe-compress.tcl script to generate structures named "do" or "if".
3832c3c10 2022-02-03 Prohibit schema changes within xBestIndex callbacks.
19eef9af6 2022-02-02 Improvement to the sqlite3_vtab_in_first() documentation.
cc0db6136 2022-02-02 Additional test cases.
d96ab9958 2022-02-02 Test cases for sqlite3_vtab_in() and sqlite3_vtab_distinct().
2725db836 2022-02-02 Improved documentation for sqlite3_vtab_in().  No code changes.
3d7a69e5e 2022-02-02 Relax the restriction that the RHS of the IN operator must be a list in order for sqlite3_vtab_in() to work.  Change an unreachable branch into an assert().
38d1e4435 2022-02-02 Be sure that sqlite3_vtab_in_first() and _next() set the correct encoding.
30e314e4c 2022-02-02 Refactor sqlite3_vtab_in() to make use of the existing sqlite3_value_pointer() mechanism for passing the list of IN operator RHS values into xFilter, for improved memory safety.
9ede896ac 2022-02-02 Fix a harmless code indentation issue.
b30298d3e 2022-02-01 Tweaks to the sqlite3_vtab_in() interface.
a9f18f017 2022-02-01 Index in 2nd argument to sqlite3_vtab_in() should be on the aConstraint[] array, not the internal array of all constraints.
0fe7e7d92 2022-02-01 Add new interfaces to enable virtual table to process IN operator constraints all at once, rather than one element at a time.
e66532a63 2022-02-01 CLI: Take extra care to not split a multi-byte unicode character when doing wordwrap.
ca1776b5f 2022-02-01 CLI: Add the --ww option as an alias for --wordwrap.  Improve the wordwrap algorithm so that it breaks at punctuation if it cannot find space.  Always wordwrap with --ww even if there is a .width setting for the column.
cc4d55c9c 2022-02-01 Add "--wordwrap on/off" option for CLI columnar modes, qwbox shortcut
5aabdaebd 2022-02-01 CLI: In ".mode column" output, if any row contains a newline or wraps, then put a single blank line in between each pair of rows to provide additional visual separately.
47741b8de 2022-01-31 CLI: for columnar output modes, make sure the header is not too big. Also, improve the help text.
376950123 2022-01-31 CLI: Fix a problem with tabs in the new qbox mode.
5dce6f96d 2022-01-31 Fix harmless compiler warnings in MSVC.
87fb37efc 2022-01-31 Do not attempt to limit the number of columns used in a table to a prefix if the table will be used to construct an automatic index or bloom filter. dbsqlfuzz 787d9bd73164c6f0c85469e2e48b2aff19af6938.
e40f28618 2022-01-31 CLI: Enhancements to columnar output modes.  (See [forum/forumpost/5b53cd851f66441f9|forum post 5b53cd851] for discussion.) New output mode "qbox".  New output options "--quote" and "--wrap N".
92ecf306e 2022-01-31 Fix an obscure problem in sqlite3_backup_init() caused by [6a45d8fe8bfbc11a|check-in 6a45d8fe8bfbc11a].  See [forum:/forumpost/8b39fbf3e7b5c278|forum post 8b39fbf3e7] for the original bug report.
b617219ba 2022-01-31 CLI: Fix the new ".mode box" output so that it works with unicode characters.
09a39ed52 2022-01-30 CLI: For columnar modes ("box", "column", "table", "markdown") the ".width" is now both the minimum and maximum width of the column.  Text that spans multiple lines or that contains tabs is properly formatted.  If any part of the output contains multi-line text, then extra separators are provided between each row.
e229ca030 2022-01-30 Always enable all JSON tests, now that JSON is included by default.
ddd166a35 2022-01-30 Remove a faulty NEVER().  Fix for dbsqlfuzz 4678cf825d27f87c9b8343720121e12cf944b71a
86c756015 2022-01-29 Documentation enhancements.  No code changes.
f6f788862 2022-01-28 Add a NEVER() on an unreachable branch.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
