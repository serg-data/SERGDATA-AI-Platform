# SQLite — Git tag version-3.32.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.32.0
Сравнение с предыдущим тегом: version-3.31.1

## Коммиты в диапазоне

```text
0b0274a90 2020-05-22 Version 3.32.0
f25f8d583 2020-05-21 Change a NEVER macro into a NO_TEST comment, as the conditional is reachable, but only when compiling for Windows 32-bit.
23e3c340b 2020-05-21 Avoid another potential OOB read in sqlite3expert.c.
4f1315a43 2020-05-20 Back out the change from [7fab1393c2b22b1f] that tries to convert invalid surrogate characters in UTF16 into the replacement character 0xfffd, as we find that this breaks some software.
5a8cd2e40 2020-05-19 Add compiler hints to disable TSAN for the routines that access the -shm file header in WAL mode using a double-read with memory barrier.
10757ed0c 2020-05-19 In os_win.c, avoid calling sqlite3_uri_boolean() on anything other than a main-db filename.
1a7feefac 2020-05-19 User-suggested improvement to the README.txt for the ICU extension.
f16cf653f 2020-05-19 In wal.c, improved comments on concurrency issues.  More use of AtomicLoad() and AtomicStore().
a5ee67d5b 2020-05-18 Add vdbevtab.lo to build of libsqlite3.lib in Makefile.msc.
c795e3df7 2020-05-17 Avoid harmless UB in memcpy() in the JSON extension.
d924e7bc7 2020-05-17 Use the sqlite3Realloc() interface internally, rather than the public sqlite3_realloc64() equivalent, to avoid unnecessary calls to sqlite3_initialize().
b2eb7e46e 2020-05-16 Performance optimization for the sqlite3FindTable() subroutine.
8c1febb2f 2020-05-16 The OP_RealAffinity opcode is not necessary after reading values from a virtual table (such as rtree).  It is harmless, but it does use CPU cycles.  Might as well leave it off.
becd68ba0 2020-05-16 Fix a use-after-free bug in the fts3 snippet() function.
c48428899 2020-05-16 Extra memory barrier during initialization.
62c94d0af 2020-05-16 Add sqlite3BeginBenignMalloc() and EndBenignMalloc() calls to debugging function sqlite3VdbePrintOp().
b2c6fe225 2020-05-15 Update code in sqlite3expert.c to account for the fact that "-- TRIGGER xyz" VM comments are now omitted for some builds.
d48eafb98 2020-05-15 Fix another build problem for SQLITE_OMIT_VIRTUALTABLE builds.
cc1d9109c 2020-05-15 Fix a documentation typo.  No changes to code.
bbf6d4328 2020-05-15 Adjust some requirement marks.  No changes to code.
2629adc7b 2020-05-15 Update test file e_fkey.test to account for the fact that new columns with REFERENCE clauses and non-NULL default values may now be added using ALTER TABLE if the table is empty.
34d156676 2020-05-15 Fix SQLITE_OMIT_VIRTUALTABLE testfixture builds.
a796de830 2020-05-15 Test script changes to account for the fact that the "p5" column in the EXPLAIN output is now an integer, not a text values containing a 2-digit hex value.
a8e41ecac 2020-05-15 Enhancements to long-path support in the Win32 VFS.
043c8f60a 2020-05-15 Move some new test cases from fts3snippet.test into fts3snippet2.test.
856408abf 2020-05-15 Add the SQLITE_ENABLE_FTS3_PARENTHESIS option to fuzzcheck.  Add a new test case that uses that option.
219b8e7e7 2020-05-14 Fix a null pointer deference that can occur on a strange matchinfo() query.
3d863b5e4 2020-05-14 Do not allow a virtual table to be renamed into the name of one of its shadows.
3c0e606bb 2020-05-13 Implement the IIF(x,y,z) SQL function that is short-hand for "CASE WHEN x THEN y ELSE z END".  For compatibility with SQL Server.
ffe421c76 2020-05-13 Remove unused constant SQLITE_FUNC_COALESCE.
8b4f231c4 2020-05-13 Use AtomicStore() and AtomicLoad() in a few more places to avoid a theoretically undefined behaviour. This is not actually problem on any known hardware.
2493dcdd0 2020-05-11 New test case in test/fuzzdata8.db.
efa78884a 2020-05-11 Fix a problem handling constant integer expressions with collation sequences in PARTITION BY clauses.
9e5fdc41c 2020-05-08 Release some restrictions on columns added by ALTER TABLE so that they only apply if the table contains one or more rows.
98aa1d735 2020-05-08 Fix the count-optimization so that it honors the NOT INDEXED clause.
91d4c374e 2020-05-08 New test cases added to test/fuzzdata8.db.
acc175215 2020-05-08 Do not retry on a failed realloc() unless SQLITE_ENABLE_MEMORY_MANAGEMENT is available, meaning that the retry has some possibility of success.
2d3ed22a3 2020-05-07 Fix a failing assert() in fts3 triggered by a corrupt database.
11a8182e5 2020-05-07 Fix an error that could occur if the first transaction executed by a connection configured to use blocking locks is a write-transaction for which the WRITER lock cannot be obtained.
e937df81f 2020-05-07 Fix the handling of reserve-bytes so that the maximum value of 255 can be used.
a8aae5239 2020-05-06 Avoid leaking a file-handle in test file walsetlk.test.
bc9fc18e4 2020-05-06 Fix an assert() failure that could follow an IO error.
783e159e4 2020-05-06 Fix harmless compiler warnings.
7a623e1d2 2020-05-06 Fix a problem preventing building without SQLITE_ENABLE_SETLK_TIMEOUT defined.
7bb8b8a4f 2020-05-06 Add error code SQLITE_BUSY_TIMEOUT, used internally by the OS layer to indicate that a call to xShmLock() has failed due to timeout of a blocking lock.
fc87ab8c4 2020-05-06 Fix compiler warnings in non-SQLITE_ENABLE_SETLK_TIMEOUT builds.
861fb1e9d 2020-05-06 Block on the WRITER lock when attempting to run recovery.
e0a8b712c 2020-05-06 Provide the SQLITE_DEFAULT_LEGACY_ALTER_TABLE compile-time option.
d0e6d1330 2020-05-06 Add tests for running recovery when opening a write transaction or performing a checkpoint with blocking locks enabled. Fix some failing assert() statements.
58021b237 2020-05-05 Unless upgrading an existing read transaction, have ENABLE_SETLK_TIMEOUT builds attempt to use a blocking lock when opening a write transaction on a wal mode database.
fde259250 2020-05-05 The only known path to a corruption detection branch was cut off by the previous commit implementing earlier index corruption.  So make the branch NEVER.  Maybe a fuzzer will find a new path.
85bd353ac 2020-05-05 Earlier detection of index corruption caused by missing index entries.
eb8305bbc 2020-05-05 Fix a compiler warning in cksumvfs.c.
3d42fb788 2020-05-04 Fix harmless compiler warnings.
8714de97c 2020-05-04 Changes to avoid deadlock in SQLITE_ENABLE_SETLK_TIMEOUT builds.
44a5c86c6 2020-05-04 Minor change to the sqlite_stmt virtual table, for test coverage.
20e34f911 2020-05-04 Simplify the initialization of built-in extensions.
995e1af9f 2020-05-04 Ensure that the master-journal name is in a form suitable to be passed into sqlite3_uri_parameter().
f72981f2d 2020-05-02 Add a missing VdbeCoverage() macro.
7e088a6c0 2020-05-02 Corner-case changes to the bytecode virtual table for testability and correctness.
fcf31b28f 2020-05-01 Add the SQLITE_FCNTL_CKPT_START file-control.  Use it to optimize the cksumvfs extension.
505119427 2020-05-01 Clarification to the sqlite3_uri() family of interfaces.  Documentation enhancement only - no changes to code.
8b2d8de3e 2020-05-01 Update documentation for sqlite3_close_v2() for clarity.  No functional changes.
cdb6ce980 2020-05-01 Add the new SQLITE_IOERR_DATA result code and use it in cksumvfs. Also enhance cksumvfs to emit an sqlite3_log() message whenever it finds an invalid checksum.
95063d8c9 2020-04-29 Do not allow page_size changes on an active cksumvfs database.
451f89a89 2020-04-28 Fix incorrect error message when something goes wrong with the sqlite3_dbpage() table-valued function in the .dbinfo command of the CLI.
065e4a8d2 2020-04-28 Add the cksumvfs extension.
23bef340b 2020-04-28 Use AtomicStore() when setting the mem0.nearlyFull boolean to avoid harmless TSAN warnings and to forestall doubts about threadsafety.
9f603fcef 2020-04-28 Use an AtomicLoad() macro in sqlite3HeapNearlyFull().
e238e3141 2020-04-26 Yet another attempt to enhance sqlite3_load_extension() so that it works with Window-style pathnames using a backslash separator character.
ec9a25c7c 2020-04-26 Fix an issue with check-in [bc3bf7c6681a96bc] when compiling on Windows.
7d9ad75a5 2020-04-25 Fix the sqlite3_load_extension() interface so that it tolerates backslashes in place of forward-slashes in pathnames on Windows.
07f9e8f4f 2020-04-25 Ensure affinity is not discarded from a view column if the view appears on the rhs of a LEFT JOIN. Fix for [45f4bf4e].
ab2172e69 2020-04-24 The new sqlite3_database_file_object() interface requires that the pager never invoke xOpen with SQLITE_OPEN_MAIN_JOURNAL unless it is using a pointer to the journal name found in the Pager structure itself.   Make this the case when processing a master-journal.
742efb674 2020-04-24 New test case for ticket [1dcb4d44964846ad].
5415ab49b 2020-04-23 Fix an uninitialized variable in the newly enhanced ".output" command of the CLI.
542bd6521 2020-04-22 Fix an off-by-one error in the "calculated" page count output from the sqlite3_analyzer utility for databases that are more than 1GB in size.
fc7f31742 2020-04-22 Fix an integer overflow in fts3 causing a usan error.
4d34766f4 2020-04-22 Clarify the comment on the sqlite3BtreeGetRequestedReserve() routine. No changes to code.
9a1bb3f61 2020-04-21 Add the sqlite3_database_file_object() interface to sqlite3ext.h.
480620c71 2020-04-21 Experimental API: sqlite3_database_file_object().
3b9f154bb 2020-04-20 Do not use O_NOFOLLOW when opening a directory just to call fsync() on that directory.
541ef2c36 2020-04-20 Enhance the ".filectrl" command in the CLI to support the --schema option.
45248de39 2020-04-20 The SQLITE_TESTCTRL_RESERVE operator is removed.  In its place is the more generate SQLITE_FCNTL_RESERVE_BYTES which is an API and which can operator on more than just the main schema.
871f45441 2020-04-20 Remove an obsolete comment.  No changes to code.
7a43100af 2020-04-18 Add the --bom option to the ".excel", ".once", and ".output" commands of the CLI.  Also fix the "--all" option on ".help" so that it works with two dashes in addition to just one.
1d9ea27f7 2020-04-17 Fix the ".excel" command and the ".open -x" and ".open -e" command so that they work better when running from an in-memory database and on Windows and when running from a script.
7576a68c8 2020-04-16 Improve corruption detection in fts3 shadow tables earlier in order to prevent an assert() from failing.
c39b121a9 2020-04-15 Clarification of the byte-order determination for UTF16 inputs to routines like sqlite3_bind_text16() and sqlite3_result_text16() and others that accept UTF16 input strings.
f05dd03a6 2020-04-14 Build the UINT collating sequence extension into the CLI.
e6a85962e 2020-04-14 Add the UINT collating sequence extension.  The implementation is copied out of the "natsort" branch.
43e862723 2020-04-09 When compiling the shell for WinRT, avoid using Win32 APIs that are unavailable.
4b3282d8a 2020-04-07 Limit LIKE/GLOB pattern length to 100 bytes (default is 50K) when running dbsql cases in the fuzzcheck utility.
aa0696ee9 2020-04-07 Add the --spinner option to the fuzzcheck test program.
2d99f9572 2020-04-07 The ALTER TABLE fix of check-in [7e5ad8e0ab7ee91a] is no longer needed due to the changes at check-in [4cf8721f5ceb1fda].  But, we keep the defense in place as an assert() for extra safety.
b3120fdf5 2020-04-07 Remove dead code that was added during initial development of RENAME COLUMN but never actually served a purpose.
4047bdfd2 2020-04-06 Performance improvement in sqlite3ResolveExprNameList().
d44390c8c 2020-04-06 Performance improvement for column name lookup.
85f2c76cf 2020-04-06 When running ALTER TABLE, avoid adding some internally generated tokens to the token map to improve performance on schemas with nested views.
47f8ef32a 2020-04-04 Remove a NEVER() that could be true in sqlite3MatchEName().
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
