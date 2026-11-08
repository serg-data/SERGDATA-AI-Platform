# SQLite — Git tag version-3.31.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.31.0
Сравнение с предыдущим тегом: version-3.30.0

## Коммиты в диапазоне

```text
1a3220ace 2020-01-22 Version 3.31.0
d0add948e 2020-01-21 Update test file exclusive.test so that it works with the "journaltest" permutation.
8c812f98a 2020-01-21 Fix a problem with using views in SQLITE_OMIT_VIRTUAL_TABLE builds. Also some test case fixes required for the same builds.
7d2a1be84 2020-01-21 Fix a case in fts3auto.test that fails for SQLITE_DISABLE_FTS4_DEFERRED builds.
70a32703a 2020-01-21 Fix an assert() that could fail in SQLITE_MUTATION_TEST builds following an error in a query that uses CTEs.
39ef8b31f 2020-01-21 Fix a problem in the userauth extension causing it to occasionally set "PRAGMA count_changes" (and some others) to true.
988af251d 2020-01-21 Fix the series.c and spellfix.c extensions to use SQLITE_VTAB_INNOCUOUS correctly.  Fix the documentation on sqlite3_vtab_config() to take into account SQLITE_VTAB_INNOCUOUS and SQLITE_VTAB_DIRECTONLY.
cbf1c8c25 2020-01-21 Improvements to the autoconf TEA Makefile for MSVC.
be03cc9fc 2020-01-20 In the fuzzcheck test program, reduce the default expression depth limit from 1000 to 500 to avoid stack-overflow problems when running stress tests using clang ASAN.
4b86e2048 2020-01-19 Enhancement to the CLI to allow the ".parameter init" command to work even if defensive mode is turned on.
38e14fbd5 2020-01-18 Documentation improvements.
76a1fce53 2020-01-18 In the TCL interface, add the ability to change the SQLITE_DBCONFIG_TRUSTED_SCHEMA setting using the "db config" method.
fe7046044 2020-01-18 Allow non-deterministic function in CHECK constraints.  It turns out that PostgreSQL, MySQL, and SQLServer all allow this.  We should be the the exception.  Ticket [830277d9db6c3ba1]
f71eb2091 2020-01-18 Do not use memcpy() of zero bytes when initializing a pager.  This avoids a warning.
a01fda711 2020-01-18 Disable a redundant test case that uses a very large stack, and hence is unable to run with -fsanitize=undefined,address.
591711751 2020-01-18 Fix harmless compiler warning seen with MSVC.
cea7b5d57 2020-01-18 Add extra front margin to the fake empty filename returned by sqlite3PagerFilename() for an in-memory or TEMP database.
1ee02a1ce 2020-01-18 Fix the VDBE so that it correctly handles the sequence of operations OP_OpenEphemeral, OP_OpenDup, OP_OpenEphemeral, and OP_OpenDup in that order on the same cursor.
2d58b7f40 2020-01-17 Fix a typo in a comment.  No code changes.
929a94067 2020-01-17 The compress() function should not be deterministic since the same input can have multiple possible compressed outputs.  The uncompress() function, on the other hand, is deterministic.
ef9f719d0 2020-01-17 Fix #ifdefs so it compiles cleanly with all SQLITE_OMIT compile-time options. Update compile-time option testing.
915530dcc 2020-01-17 Improved rounding in the 'unixepoch' feature of the date and time functions.
a369d98b9 2020-01-17 Update test script instrfault.test to account for the fact that bound blob values cast to text values are now intepreted using the text encoding of the database, instead of always as utf-8.
d1eb23cd2 2020-01-17 Fix a case in "fuzz.test" that could fail, as non-deterministic functions may no longer appear in CHECK constraints.
be0330e85 2020-01-16 New testcase() macros in select.c, for coverage of the change from two check-ins ago.
1d7d8c8f7 2020-01-16 Add the SQLITE_FCNTL_CKPT_DONE file-control for the use of custom VFSs.
39df24a3f 2020-01-16 Do not allow the constant-propagation optimization to apple to ON/USING clause terms as it does not help and it might cause downstream problems.
7db212a70 2020-01-16 Fix an SQL syntax error in the comment on the omit-left-join optimization. No changes to code.
7d07a5f4e 2020-01-16 Clean up the definitions of the TERM_ constants in the code generator. Formatting only - no logic changes.
b5f0e4057 2020-01-15 Do not allow the "PRAGMA encoding" statement to change the database encoding if TEMP content exists, or content in any other attached database.  Formerly, encoding changes were allowed if just the main database file was empty.  Ticket [a08879a4a476eea9].
be22a8540 2020-01-14 Fix the urifuncs.c extension (used for testing and debugging only) so that the sqlite3_filename_database() SQL function and its siblings correctly handle an invalid schema name passed in as the argument.
05e8c5407 2020-01-14 Remove an ALWAYS on a branch for improved database corruption detection in btree.c:freeSpace().  Test case found by dbsqlfuzz.
299b102b9 2020-01-14 Add the new noop_nd() debugging function to the noop.c extension.
c1f73e29b 2020-01-14 For the showdb utility program, more accurate detection of when the database is in autovacuum mode for the "pgidx" subcommand.
76c120684 2020-01-14 Fix a minor typo on a comment in the CLI implementation.
a14de9136 2020-01-14 Improvements to sqlite3_open_v2() documentation.
c6b2f9e32 2020-01-13 More documentation updates.  No code changes.
3c867026c 2020-01-13 Documentation updates.  No changes to code.
3b8eb08b1 2020-01-12 Better than removing the incorrect assert() is to change it into a testcase() together with a comment indicating where an appropriate test case can be found, and the ticket that provoked the change. Ticket [614b25314c766238]
d8df36bd4 2020-01-12 Change the zipfile virtual table so that the xBestIndex method gives a reasonable cost estimate even if no filename is specified.  The missing filename error continues to be raised in the xFilter method.  Meanwhile, the more reasonable cost estimate avoids unnecessary wierdness in the query planner.
ca7d3e1d4 2020-01-12 Remove an incorrect assert().  Fix for ticket [614b25314c766238]
cdfadc794 2020-01-11 Minor changes for consistency between sqlite3_filename_wal() and sqlite3_filename_journal().
8080403e4 2020-01-11 Redesign for better legacy compatibility.  Add the sqlite3_uri_key() interface.
8875b9e7b 2020-01-10 Rearchitect the way in which filenames are stored in the Pager object so that the sqlite3_uri_parameter() interface will work from journal and WAL filenames too.  This check-in implements the central idea, and compile and runs somewhat, but crashes on an extended test.
b2fe5a7c3 2020-01-10 Fix to the register validity tracking logic in debug builds.  No impact on release builds.
e5f880104 2020-01-10 Documentation updates on newer APIs.  No changes to code.
2e22579de 2020-01-09 Fix the fossildelta.c extension so that it will compile on mingw.
32d184e04 2020-01-09 Only register the fts3_tokenizer() function using a single text encoding.
7be5e3dd4 2020-01-09 Fix a harmless compiler warning.
fbb6e9ff4 2020-01-09 Fix an assert() in window.c that could fail with some obscure SELECT statements that use window functions.
b84fda37e 2020-01-09 Fix a problem in the encoding display in the updated PRAGMA function_list.
51ebd5fa1 2020-01-09 Fix minor typos in the trusted-schema.md document.
3858be3e5 2020-01-09 Minor formatting changes in the trusted-schema.md document.
b0c4ef711 2020-01-09 Design notes for the new-security-options branch.
32266a107 2020-01-09 Simplified error message for the unsafe use of a virtual table.
05b32ee3c 2020-01-09 Fix a problem that restricted edgy functions in TEMP tables. New test cases added.
014fff20a 2020-01-08 Block edgy functions used in DEFAULT constraints.
2eeca2046 2020-01-08 Performance improvements and test cases added. Allow "PRAGMA trusted_schema=ON"
0dfa5255b 2020-01-08 Check for whether or not it is safe to use non-innocuous functions as the function is being coded, not when its name is resolved.
15f3eacfc 2020-01-08 Provide the -innocuous option to the "db func" method in the TCL interface.
6d35956c8 2020-01-08 Fix the rot13.c extension to be deterministic.  Add the noop.c extension.
b7e519956 2020-01-08 In the TreeView debugging output, show a "DDL" mark on SrcList and Expr nodes that derive from a non-TEMP schema.
87969b2a1 2020-01-08 When doing a test-to-double conversion on a BLOB with an odd number of bytes and assuming a UTF16 encoding, ignore the last byte. Ticket [9eda2697f5cc1aba].
ded33ccea 2020-01-08 Fix a minor formatting error in the display of BLOB values during VDBE tracing.
4a62581b3 2020-01-08 Improvements to the documentation of sqlite3_create_collation().
f8f76d672 2020-01-08 Simplification of the logic in the constant-propagation optimization.
c9301e6e7 2020-01-08 Fix the constant propagation optimization so that it does not try to propagate constant expressions that have affinity.  Ticket [82ac75ba0093e5dc]
97bffe674 2020-01-08 Fix a misworded comment.  No code changes.
2b1c2aad9 2020-01-07 Create the "trusted_schema" pragma.  Add sqlite3_vtab_config() calls to set the risk rank for many virtual tables.
3f68142b8 2020-01-07 Enforce SQLITE_VTABRISK restrictions.
406dfcb84 2020-01-07 Fix a performance regression caused by the previous check-in.
b77da374a 2020-01-07 Invert the UNTRUSTED_SCHEMA setting to be TRUSTED_SCHEMA.
42925d1f1 2020-01-07 Add an "|| CORRUPT_DB" term to an assert() statement inside of btree.
262efe4a4 2020-01-07 Fix an instance of an undefined behaviour (a left-shift of a 64-bit unsigned integer by a value greater than 64) that could occur in fts3.
cbae3f8c7 2020-01-06 In the typeof() optimization in OP_Column, expand the size of the bogus buffer provided for data so that it is big enough to cover the increased number of bytes displayed during register tracing from check-in [54553bf16fabd72d]. This is the correct fix for ticket [bbd55a97e66ff50d], though the earlier one does not hurt and is useful to retain.
5ca06329c 2020-01-06 Rewrite the (debugging use only) sqlite3VdbeMemPrettyPrint() function to use the safer StrAccum interface rather than writing directly into a static string buffer.  Perhaps this will address ticket [bbd55a97e66ff50d], which we are unable to reproduce.
2e26a602a 2020-01-06 Backout change [4d0b9109f7a5312d4e1] because the conditional it added is no longer reachable due to check-in [1409758f72c0206c].
65cdae00e 2020-01-06 Move variable declaration to start-of-block for MSVC.
b592d47a8 2020-01-06 Do not attempt to use the skip-scan optimization if prior terms of the index are already used for non-equality constraints. Ticket [304017f5f04a0035]
9e10f9ab0 2020-01-06 Ensure the SF_Aggregate flag on a SELECT statement is set if a DISTINCT is transformed to a GROUP BY. Ticket [9c944882].
2928a15b3 2020-01-06 Refactor names of flags for improved legibility.
628b1a3f9 2020-01-05 Remove a NEVER in btree due to a new test case from dbsqlfuzz.
67c826536 2020-01-04 Refactor the names of the new controls for restricting what actions the schema can take behind the application's back.
337ca519e 2020-01-04 Enhance PRAGMA function_list to show internal functions if the direct use of internal functions is enabled via the SQLITE_TESTCTRL_INTERNAL_FUNCTIONS test control.
2e5beddb3 2020-01-04 Fix DBSTAT so that it returns now rows, rather than an error when the WHERE clause is "schema=NULL".
17aceebab 2020-01-04 Fix harmless compiler warnings.
664d80bbf 2020-01-04 Omit the omit flat from eq constraints on column "name" of dbstat virtual tables. Fix for [74a4c386].
56ea69bf0 2020-01-04 Record when the OP_IfNotOpen branch is and is not taken.
64f7ee021 2020-01-04 Remove another NEVER added by check-in [7b62555e285f32d3]. Dbsqlfuzz found another test case.
6f2180d21 2020-01-04 New test cases in test/in4.test require rtree, so disable those tests on builds that lack the rtree extension.
74ebaadcd 2020-01-04 Fix a problem where the loop for the RHS of a LEFT JOIN uses values from an IN() clause as the second or subsequent field of an index.
f6ea97ea3 2020-01-04 Fix a false-positive in the register validity tracking logic by moving the temporary register release call before the jump that uses that temporary register.
4549a3b8c 2020-01-04 Improve a testcase in test/fuzzdata8.db to make it more resilient.
b2b61bb61 2020-01-04 Back out another NEVER added by check-in [7b62555e285f32d3] - the test case was already in test/fuzzdata3.db, but it only occurs if compiled without SQLITE_ENABLE_PREUPDATE_HOOK.
6fe63b4ee 2020-01-04 Omit the omit flag from eq constraints on column "aggregate" of dbstat virtual tables. Fix for [727074e2].
e5cf3e990 2020-01-04 Restore a NEVER and an assert in btree that was removed by check-in [7b62555e285f32d3].  Dbsqlfuzz found test cases.
79d5bc80c 2020-01-04 Enhance PRAGMA function_list so that it shows all instances of each FuncDef, the number of arguments, the encoding, the type, and the flags.  Use this capability to locate and fix incorrect function flags in the standard build.
4be621e1b 2020-01-03 Invert the SQLITE_FUNC_SAFE bit to be SQLITE_FUNC_UNSAFE.  The external bit is still SQLITE_INNOCUOUS.  It gets inverted as the appdef function is registered.
c4ad84992 2020-01-03 When UNSAFE_IN_VIEW is disabled, only allow functions in views that are tagged with SQLITE_INNOCUOUS.
e455e3acf 2020-01-03 In fts3, avoid making a very large memory allocation if the merge-hint record is corrupt.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
