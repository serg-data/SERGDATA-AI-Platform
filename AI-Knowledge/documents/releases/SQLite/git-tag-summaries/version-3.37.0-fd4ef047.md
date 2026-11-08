# SQLite — Git tag version-3.37.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.37.0
Сравнение с предыдущим тегом: version-3.36.0

## Коммиты в диапазоне

```text
315e3122c 2021-11-27 Version 3.37.0
14851b9a1 2021-11-27 Fix a harmless comment typo.
855a165fe 2021-11-26 Add platform "Darwin-arm64" to test/releasetest_data.tcl.
913306a53 2021-11-26 Improved defenses against integer overflow when computing the size of a memory allocations.  No bugs were fixed here.  But perhaps future bugs will be prevented.
e574a9233 2021-11-26 Fixes to internal comments.  No changes to code or documentation.
2df026a54 2021-11-24 Avoid splitting Failure-Detection test cases in wapptest.tcl.
622bd63c3 2021-11-24 Update Makefile.msc to support target "tcltest" in the same way as the autoconf build system.
b0906b608 2021-11-23 Changes a test pattern for RBU so that it works regardless of whether newer TCL versions are used.
7907d372b 2021-11-23 Fix a compiler warning in the dbserialize method of the TCL interface.
619a5f557 2021-11-23 Exclude two recently added tests in where.test from valgrind runs. They fail due to the subtly different handling of real numbers under valgrind.
70a05e916 2021-11-22 Omit wal mode tests in memdb1.test for builds and configurations that do not support wal mode.
b127d0fd2 2021-11-22 Omit wal mode tests in vacuum-into.test for builds and configurations that do not support wal mode.
c7b29b0ce 2021-11-22 Do not attempt to run the tests in alterfault.est with SQLITE_OMIT_ALTERTABLE builds.
42ac4c2e5 2021-11-22 Fix a typo in memdb1.test preventing tests from passing with -DSQLITE_DEFAULT_AUTOVACUUM=1 builds.
b670fd554 2021-11-22 There are two possible error messages from stat-9.1, depending on compile-time options.  Adjust the test case to accept either one.
81258cc91 2021-11-22 In fuzzcheck, improve the defense against long delays due to rogue busy_timeout macros in fuzzer-generated scripts.
9f9bdf934 2021-11-22 Fix the build for SQLITE_OMIT_CTE.
156d44104 2021-11-22 In the previous check-in, do not overwrite the SQLITE_CORRUPT signal with an SQLITE_OK before exiting fts3auxNextMethod().
bb0c54283 2021-11-22 Fix a crash in the fts3aux code that could occur handling corrupt records.
6f991147b 2021-11-20 New test cases for STRICT and NOT NULL in PRIMARY KEY.
a51e60079 2021-11-19 Small performance increase and size reduction for sqlite3ExprCompare(). This change also handles some corner cases without the need for ALWAYS().
d9137e3be 2021-11-19 Fix a benign data race in os_unix.c that might trouble tsan and similar tools.
5e90794b6 2021-11-18 Minor tweaks to the way auxiliary tools are built, to make it easier to customize the builds without having to alter the code.
826ec6013 2021-11-18 Fix a performance regression in rtree introduced by the previous commit.
895c807a6 2021-11-18 Fix a problem slowing down the handling of == constraints in the rtree module.
9cd0c3d4c 2021-11-18 Improve CSV quoting in the CLI using the strstr() function.
e41d30ffd 2021-11-18 Fix an obscure problem associated with quoting of CSV output in the CLI.
488b55856 2021-11-16 Fix a problem causing an OOM within an ALTER TABLE ADD COLUMN command that adds a column with a CHECK constraint to go unreported.
9dc718856 2021-11-15 Strengthen the sticky-CORRUPT idea of check-in [3feb0f1c3840904d] by automatically changing the first COMMIT after an SQLITE_CORRUPT error into a ROLLBACK.
3ce76a0bb 2021-11-15 Small performance optimization in sqlite3VdbeHalt().
8745f8a3c 2021-11-15 Fix a problem causing the count(*) optimization to be misapplied in some cases where an aggregate sub-query uses a count() expression that is aggregated against the outer query.
5b001cc25 2021-11-15 Improved context shown for the "ABORT-due-to-error" output line when using "PRAGMA vdbe_debug=on" in an SQLITE_DEBUG build.
a2852ac4d 2021-11-15 Fix a faulty JSON assert() added 30 days ago by check-in [7b8ea2298927fd34]. dbsqlfuzz f30366e7b02562398a387ddcc681422fd4251190.
146121f5c 2021-11-12 Improved handling of OOM while reallocating a column name to add type information.  dbsqlfuzz 5a195b4233649e49e0aa34f1b743ca192d85b198
9135ebb7d 2021-11-11 Make sure the rowid value returned by the VUpdate opcode is always initialized.
f9241a5fd 2021-11-11 Remove a NEVER() that was add yesterday.  The fuzzer found a new test case to make it happen.
3ab4ffce1 2021-11-11 New assert() statements to help prove correct usage of VdbeCursor objects.
34e71830d 2021-11-10 Load new test cases into test/fuzzdata8.db
46c425b4d 2021-11-10 Make SQLITE_CORRUPT sticky:  If a CORRUPT error is returned, all subsequent write statements within the same transaction also fail early with SQLITE_CORRUPT.
995d33ae0 2021-11-09 Change test case error message text to match the current implementation.
4e86aa86e 2021-11-09 Fix lempar.c so that Lemon can compile with NDEBUG defined. [forum:/forumpost/f331adca0b|Forum post f331adca0b]
90cf38be6 2021-11-08 Refactor the code that figures out which SELECT in a cascade of nested queries a particular aggregate function belongs to.  This fixes the problem reported by [forum:/forumpost/c7cc2aa3546e39c1|forum post c7cc2aa3546e39c1]. New test cases in dbsqlfuzz and th3.
a32536b49 2021-11-08 Fix the zeroblob() function and related APIs so that they work with SQLITE_OMIT_INCRBLOB builds.
1a39e4561 2021-11-08 Fix an assert() in memdbTruncate() that could fail when processing a corrupt database.
6d64b4a02 2021-11-07 Ensure that the window function rewrite does not leave the parse tree in an invalid state that might cause problems downstream before the error is recognized and unwinds the stack.  Also take steps such that an invalid parse tree does not cause problems even if it goes unrecognized. [forum:/forumpost/398e9d5aa9|Forum post 398e9d5aa9].
7b108e4cf 2021-11-06 Add ALWAYS() to a branch made unreachable by the previous check-in.
35c7312ff 2021-11-06 Return an error if an attempt is made to drop an eponymous virtual table.
62561b82f 2021-11-06 Avoid accessing the sqlite3_module.xShadowName field if (sqlite3_module.iVersion<3).
64d5b1ca2 2021-11-05 New test cases for rbu_exclusive_checkpoint query parameter.
c18e022f1 2021-11-05 Update an assert() statement to conform to the changes of the previous check-in.
91acf7d35 2021-11-05 Add the SQLITE_OPEN_EXRESCODE flag for sqlite3_open_v2().
1182e2ac7 2021-11-05 If the target database URI passed to sqlite3rbu_open() is contains the option "rbu_exclusive_checkpoint=1", hold an exclusive lock for the duration of any incremental checkpoint operation.
695c87f67 2021-11-05 Update sqllimits1.test to account for recent changes to SQL function strftime().
608af68ad 2021-11-05 Use the FTS_CORRUPT_VTAB macro rather than a direct call to sqlite3Fts3Corrupt() in [2fad2a89527757b3] so that the build works in all cases.
a1c4c3c18 2021-11-05 Remove an incorrect NEVER() reported at [forum:/forumpost/5bbabfb7ce|forum post 5bbabfb7ce].  Also use this opportunity to improve the isSimpleCount() function with better formatting, an expanded header comment, and some extra assert() and textcase() macros.
11e29677a 2021-11-05 Fix vacuum3.test so that it works with SQLITE_OMIT_ALTERTABLE builds.
06ee28418 2021-11-05   Update a test case in sqllimits1.test to account for the updated implementation of SQL function strftime().
2841abedd 2021-11-05 Fix a couple of problems with test scripts and SQLITE_OMIT_ALTERTABLE builds.
355527441 2021-11-04 Fix a crash that could occur in fts3 when processing a corrupt database.
de3fd373a 2021-11-04 Fix corruptN.test so that it works with SQLITE_DEFAULT_AUTOVACUUM=1 builds.
715e002d0 2021-11-04 Update a test case in corruptN.test to account for the fact that if writable_schema=1 is set, no error is raised if a DELETE statement finds that an index entry is missing ([19e56291a7344c7a]).
a4adaa37f 2021-11-04 Have wapptest.tcl avoid attempting to build fuzztest for SQLITE_OMIT_VIRTUALTABLE configurations.
a1d35da5f 2021-11-04 Fix typo in the sqlite3ext.h file. [forum:/forumpost/63802db4ce|forum post 63802db4ce]
a4a871c28 2021-11-04 Show the preferred schema table names in the output of "PRAGMA table_list".
06b7281c9 2021-11-04 Change a branch made unreachable by the previous check-in into an assert().
ddfec00de 2021-11-04 First the shadow table mechanism so that it works even if the shadow table comes before the virtual table in the sqlite_schema table, as can happen after a VACUUM.
0b97189c4 2021-11-03 Remove two incorrect assert() statements added by a check-in from earlier today.
ac894af85 2021-11-03 Improved the error message that results when a schema parse fails after ALTER TABLE ADD COLUMN.
926aac51b 2021-11-03 Fix INSERT into STRICT table with STATIC generated columns.
80b957b75 2021-11-03 Add the --strict option to speedtest1.c
5c9290423 2021-11-03 Fix an issue in PRAGMA integrity_check associated reporting NULL values in a NOT NULL column of type ANY in a STRICT table.
5d742e39d 2021-11-02 Proposed fix for a problem associated with OP_SeekScan that results in an incorrect answer.  See ticket [5981a8c041a3c2f3].
61a8ad7cf 2021-11-02 Ensure that ALTER TABLE RENAME recognizes OOM errors while parsing dependent triggers and handles them appropriately. dbsqlfuzz 53e245eee15d3f19639d773048aa955c30708785.
07ed9c110 2021-11-02 Fix a minor memory leak in the shell tool. Omit running fuzztest as part of the Device-One release test configuration, as it is now incompatible with SQLITE_OMIT_VIRTUALTABLE.
a12a40c3f 2021-11-02 Add #ifdef logic to os_unix.c so that it builds with SQLITE_OMIT_WAL defined.
0c0fb9cf8 2021-11-02 Fix a minor typo in a comment.
1cd6042f9 2021-11-02 Add recent dbsqlfuzz cases to test/fuzzdata8.db.
76c3ae684 2021-11-02 Fix a broken assert() in fts5 that could fail if the snippet() function were used with a query phrase containing 0 tokens on a detail=none or detail=col table.
8f09f4b26 2021-11-02 Add globbing option to shell's .archive command.
719506f9a 2021-11-01 zap trailing whitespace
7774fc010 2021-11-01 Add a test for .ar -r and fix a use-of-uninitialized-variable bug
47061b9d5 2021-11-01 Add --remove subcommand to shell's .archive command
16fc5e67a 2021-11-01 The VVA() macro in json1.c must be active during SQLITE_COVERAGE_TEST because it affects the outcome of testcase() macros.
362c18191 2021-10-30 Fix an incorrect assert() statement in sqlite3GenerateConstraintChecks(). dbsqlfuzz 4190cff310aeab359a55f354e560db95d3a6f47d
21b1c6dda 2021-10-30 Fix a memory leak in test code on this branch.
e4e1af5ef 2021-10-29 Reorder a test add earlier today to OP_Transaction for easier testing.
cfb524962 2021-10-29 Allow "VACUUM INTO" to change the page_size of a database even if the original database is in WAL mode.  Enhancement suggested by [forum:/forumpost/033f2c9d1f|forum post 033f2c9d1f].
37bbcb48a 2021-10-29 Add pragmas "multiplex_enabled", "multiplex_chunksize", and "multiplex_filecount" to the multiplexer implementation.
8cb63f5a5 2021-10-29 Fix the OP_Transaction opcode so that if an error other than SQLITE_SCHEMA occurs first, the original error is not overwritten by SQLITE_SCHEMA. dbsqlfuzz 85bf7e262017c6c7bddb03ff6d8541511985d36c.
6ac9a5cf5 2021-10-28 Fix .import -skip issue reported at https://sqlite.org/forum/forumpost/4c0816c24fc9d16f?t=h
33d28ab4c 2021-10-28 Minor changes to make it easier for static analyzers to reason about the code.
eaad533e5 2021-10-27 Ensure that all possible outcomes for walIndexPage() are accounted for by callers.
71c3ea752 2021-10-27 Avoid the 1-based indexing on the WalHashLoc.aPgno[] array.  Make it 0-indexed instead.
5f25627a1 2021-10-27 Improve the comment on walIndexPage() to more accurately describe the post-conditions.
9b2adcc3d 2021-10-27 New assert()s to help prove correctness in sqlite3VdbeMemExpandBlob().
f76d28774 2021-10-27 Fix the build for various the OMIT-everything compile-time option.  No impact on regular builds.
90385ddcf 2021-10-27 Fix a harmless compiler warning in memdb.c.
be2d6fdd7 2021-10-27 Fix a harmless compiler warning in fuzzcheck.
662bebb6b 2021-10-27 Change fuzzcheck so that it accepts binary dbsql files.
075201e50 2021-10-27 Add the --script option to fuzzcheck.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
