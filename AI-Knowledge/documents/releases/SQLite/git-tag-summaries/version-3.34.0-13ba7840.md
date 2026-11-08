# SQLite — Git tag version-3.34.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.34.0
Сравнение с предыдущим тегом: version-3.33.0

## Коммиты в диапазоне

```text
384f5c26f 2020-12-01 Version 3.34.0
aeb4e6eeb 2020-11-30 Update the tea/win/makefile.vc file that ships as part of the autoconf package to use "sqlite3" instead of "tclsqlite3" for the installed dll filename.
56a5747e6 2020-11-30 Do not reuse the obsolete SQLITE_TESTCTRL_PRNG_RESET value for SQLITE_TESTCTRL_SEEK_COUNT.  Give SEEK_COUNT its own unique value. This avoids incompatibility with legacy test code.
cad760d16 2020-11-27 Fix a compiler warning in fts5_aux.c.
6d19bf946 2020-11-27 Add missing cast to fts5 bm25() code.
318170689 2020-11-27 Remove a redundant "if( rc==SQLITE_OK )" from the fts5 bm25() code.
66efc393c 2020-11-27 Move an "if( rc==SQLITE_OK )" to outside a loop body in the fts5 bm25() code.
1c5b23f17 2020-11-27 Fix a case in the FTS5 integrity check where a corrupt database could cause a buffer overread.
ec8962869 2020-11-26 Update mkunicode.tcl to match the change erroneously made to machine generated file fts5_unicode2.c in [b7b7bde9].
68b403445 2020-11-25 Update a requirement mark in the e_expr.test script.
d36f588f3 2020-11-25 Fix harmless compiler warnings about unused function parameters.
3ef2cb599 2020-11-25 Fix a potential NULL pointer dereference in the geopoly_overlap() routine of the GeoPoly extension.
f82d78e9c 2020-11-25 Fix the shell1.test test script so that it works on windows.
b7c46aa8c 2020-11-25 Change the -init option to the command-line shell to honor the -bail option. Also change it to report an error if the filename mentioned cannot be opened.
f862b55a5 2020-11-24 Fix a typo in the sqlite3_txn_state() documentation.
4989a530a 2020-11-24 Add the new sqlite3_txn_state() interface to the set of routines accessible by run-time loadables extensions.
a7fc1686e 2020-11-24 Fix a harmless typo in a comment.
f5c3a75b6 2020-11-24 Fix a bug in OOM handling code introduced by [6a28713d].
2e3cb1382 2020-11-24 Ensure that super-journal and other journal filenames passed by SQLite to an sqlite3_vfs.xOpen() implementation may be safely passed to sqlite3_uri_parameter() and similar functions.
ef5b2d27b 2020-11-24 Remove the VERSION_NUMBER macro from configure.ac as it has been unused since 2009 check-in [7f4810747b086498].  See also [forum:/forumpost/bb2c634fcd|forum post bb2c634fcd].
de9873bb0 2020-11-23 Syntactic changes to work around a bug in gcov 9.3.0.  No changes to the generated code for release builds.
d46beb06a 2020-11-23 In os_unix.c, put ALWAYS() on unreachable branches associated with pathname normalization.
39acaec16 2020-11-23 Fix a test script problem causing crash8.test to fail when run with leak-sanitizer.
1335ec7df 2020-11-23 Allow "substring()" as an alias for "substr()" for compatibility with other SQL engines.
6a5e21149 2020-11-20 Add file doc/vdbesort-memory.md, containing notes on the way vdbesort.c uses heap memory.
e5dc4a209 2020-11-19 More test case changes so that shared-cache mode tests all work with normalized database names.
f4097026e 2020-11-19 Fix the tkt3793 test case so that work even when filenames are normalized.
f56a4bfcd 2020-11-18 Improvements to the mechanism that attempts to report SQLITE_CORRUPT if pread() says that the underlying filesystem is corrupt.
8ea11095c 2020-11-18 Update cksumvfs.c so that if SQLITE_AMALGAMATION is defined, SQLITE_CKSUMVFS_STATIC is implied.
c30b78f6f 2020-11-18 Add test infrastructure for cksumvfs. And update cksumvfs so that it works in concert with version 2 VFSs. No changes to core SQLite.
8bb3961d4 2020-11-18 Fix a problem causing sqlite3_carray_bind() to return an undefined value.
5011bb8dd 2020-11-18 Update test code to fix a problem with SQLITE_OMIT_VIRTUAL_TABLE builds.
5a07d10fd 2020-11-18 On unix, for certain error codes of read()/pread() return SQLITE_IOERR_CORRUPTFS instead of SQLITE_IOERR_READ.  And then convert this error into SQLITE_CORRUPT prior to returning back to the application.
32881bebb 2020-11-17 Claw back most of the performance lost in the previous commit.
aff1a57f4 2020-11-17 Fix trivial memory leaks in the shell and sqldiff programs.
12c999465 2020-11-17 Fix test file busy2.test so that it works with the "inmemory_journal" permutation.
ea847f1b9 2020-11-17 Add a single-argument form to the CARRAY table-valued function, with content bound using the sqlite3_carray_bind() interface that is included with the extension.
7f42dcd90 2020-11-16 Enhance the unix VFS so that it removes extra "/", "/./" and "/../" from the database filename.
ea2487200 2020-11-14 Modify UPDATE so that two-pass updates on a rowid table use an ephemeral table to store rowids rather than a RowSet.  This uses less memory, though it is slower.
b035b87ef 2020-11-12 Improved diagnostics output with ".wheretrace 0x800".  No changes to non-debug builds.
75e6bbbec 2020-11-11 Fix a typo in a comment.  No changes to code.
235667a85 2020-11-08 Use NEVER and ALWAYS macros to confirm that the return value from sqlite3ExprSkipCollateAndLikely() is never NULL in some of its use cases.
78043e891 2020-11-06 Add ALWAYS() to conditionals associated with SHM locking that are always true.
4e451aad5 2020-11-05 Suppress errors associated with TEMP triggers that reference objects in non-TEMP databases.  This is a continuation of the fix for ticket #3810 shown in check-in [ba1afc040171810d] from [/timeline?c=trunk:200908061743|2009-08-06], based on a bug report in [forum:/forumpost/157dc791df|forum post 157dc791df]
114cb0179 2020-11-05 Remove unused variable from speedtest1.c
6d5ab2a1d 2020-11-02 Fix an another OSS-Fuzz discovered assertion fault due to ALTER TABLE and strange triggers.
2fa781857 2020-10-31 Add the -tabs command-line option to the CLI.
7a39faecc 2020-10-31 Update the ALTER TABLE command to correctly handle UPDATE ... FROM statements within trigger programs.
ed7974dee 2020-10-26 Always create a statement journal when using the OP_ParseSchema opcode, as you never know when it might fail.  See the discussion on [forum:/forumpost/daa2c728cc|forum post daa2c728cc].
19f7bd3b0 2020-10-26 Ensure that the table argument passed to Tcl_GetIndexFromObjStruct() in the sessions module test code is declared "static".
d1d43efa4 2020-10-26 Prevent fts5 tokenizer unicode61 from considering '\0' to be a token characters, even if other characters of class "Cc" are.
461ff3594 2020-10-22 Test case updates.
403869680 2020-10-22 Sometimes it makes sense to do a full table scan rather than try to use an index when most of the rows will be selected.  This branch is trying to tune the query planner to make that happen more often.
672f07c64 2020-10-20 Fix the sqlite3_hard_heap_limit() so that it works with sqlite3_realloc64() in addition to sqlite3_malloc64().  Improvements to OOM processing and debugging aids in the fuzzcheck utility.
1a56fce61 2020-10-20 Fix an assert() inside of debug-only code that can fail following an OOM.
94d6f3f83 2020-10-19 Fix an incorrect table ref-count in the new recursive CTE logic that might result in a reference to freed memory following a syntax error.
07d7a8dca 2020-10-19 New test cases for recursive CTEs with multiple recursive terms.
340558540 2020-10-19 Allow multiple recursive terms in the compound SELECT of a recursive CTE. This facilitates writing a query to find find the connected components of an undirected graph.
a00a01674 2020-10-18 Fix harmless compiler warnings.
ff01ee34c 2020-10-17 Fix the SQLITE_DESERIALIZE_FREEONCLOSE flag so that it works as it is documented to work. See [forum:/forumpost/ba1dff667a|forum post ba1dff667a]
e93986a93 2020-10-17 Fix an incorrect printf() in debugging logic in where.c. Problem reported [forum:/info/80a9c47769772207|by forum post 80a9c47769772207].
71cb42205 2020-10-15 Minor fixes to the cksumvfs documentation in the header comment of the source file.  Enhance speedtest1.c so that it can more easily do performance comparisons of cksumvfs.
f8c4c3a09 2020-10-15 The windows VFS accepts query parameter "exclusive=true" to cause it to take a mandatory file lock, preventing other applications from even reading the file.
d5157e01b 2020-10-14 Enhancements to TclKit batch tool for MSVC.
05881886a 2020-10-14 Fix typo in a documentation comment.
7207be402 2020-10-14 Enhanced documentation for sqlite3_vtab_nochange() to make it clear that it is an optimization and that virtual table implementations should be prepared for it to always return false.
f6b0464e3 2020-10-12 Fix some fts5 problems with signed integer overflow causing segfaults in -ftrapv builds.
c6712647c 2020-10-12 Improved quoting of the table name argument for the ".import" command of the CLI.  See [forum:34591fefbe|forum post 34591fefbe].
c196219dd 2020-10-12 Add options --data-only and --nosys to the ".dump" command in the CLI.
936a30598 2020-10-12 Fix ALTER TABLE so that it can run even if the schema contains unknown collation sequences.
bbb29ecfb 2020-10-12 Add the --nosys option to the .schema command in the CLI.
4d906f1b5 2020-10-12 Fix UPDATE FROM statements on virtual tables that are declared WITHOUT ROWID.
1ca037f41 2020-10-12 Fix BEGIN IMMEDIATE and BEGIN EXCLUSIVE so that they work even if one or more of the database files in the connection are read-only.  Test cases for this are in TH3.
0897c3c05 2020-10-07 In the CSV extension, use SQLITE_TRANSIENT rather than SQLITE_STATIC on return values that can in fact change.
f46be6a1b 2020-10-05 Allow fts5 trigram tables created with detail=column or detail=none to optimize LIKE and GLOB queries. Allow case-insensitive tables to optimize GLOB as well as LIKE.
a344ad47f 2020-10-03 Do not apply affinities when creating entries for automatic indexes on views. Fix for [95302bdb].
12a6a1eaf 2020-10-03 Fix a segfault caused by running "column LIKE NULL" against an fts5 table using the trigram tokenizer. Fix for [e33ee62575fc22].
95dca8d0c 2020-10-03 FTS5 does not handle tokens that contain embedded nul characters. Prevent the trigram tokenizer from returning such tokens. Fix for [2ba5930b2].
7093a3be0 2020-10-02 Fix some test code so that testfixture can build with SQLITE_OMIT_WAL defined.
7d14ffe4e 2020-10-02 Additional corner-case fixes for the in-scan-vs-index or OP_SeekScan optimization.
64208b50c 2020-10-02 Remove an incorrect assert() from the OP_SeekScan opcode.
9bb612f2c 2020-10-02 Fix a faulty assert() statement.  Add new test cases.
04e70ce07 2020-10-02 For the OP_SeekScan optimization, the OP_IdxGT does not necessarily come right after the OP_SeekGE.   So use the P2 operand of OP_SeekScan to point to the first instruction after OP_IdxGT.  Problem found by dbsqlfuzz.
4ad1a1c74 2020-10-02 Disable the OP_SeekScan opcode of the in-scan-vs-index optimization when in PRAGMA reverse_unordered_selects mode, as the OP_SeekScan only works with forwards scans.  Thanks to OSSFuzz for pointing out the problem to us.
a22c1c84c 2020-10-01 Add the -trigram option to the fts5txt2db.tcl script.
ccf578d43 2020-10-01 Add tests for the trigram tokenizer. Fix minor issues.
deaa61072 2020-10-01 Fix the OP_SeekScan opcode so that its variable names do not cause problems for the test/vdbe-compress.tcl script.
644f43c0f 2020-10-01 Remove a debugging printf() accidentally left in the previous check-in.
67306cb3b 2020-10-01 The IN-early-out optimization does not work for virtual tables.  Do not try to use it there.  Fix for ticket [2d5a3163563d559f].  Test cases in TH3.
33a99fad0 2020-09-30 Add experimental unicode-aware trigram tokenizer to fts5. And support for LIKE and GLOB optimizations for fts5 tables that use said tokenizer.
4f65b3bbf 2020-09-30 For the OP_SeekScan opcode, adjust the number of steps run before giving up based on the estimated number of comparisons needed to perform a seek.
395a60dad 2020-09-30 Back out the incorrect optimization of check-in [e51ecadcbdef5ce6] as ticket [5c4e7aa793943803] reports a case where the optimization does not work.
af3711536 2020-09-30 In the query flattener when substituting expression Y in place of expression X, if X is marked has having come from an ON or USING clause of a LEFT JOIN, then be sure that all subexpressions of Y, not just the root node of Y, are similarly marked.  Otherwise, if Y is an AND operator, it will be split up during WHERE clause analysis and the subexpressions will not get the special treatment needed by LEFT JOIN ON/USING clauses. Fix for ticket [66e4b0e271c47145].
1e6c58dee 2020-09-30 Better understanding of savepoint code
a957e22fa 2020-09-30 Add an sqlite3FaultSim() call to btreeNext() to make it easier to simulate I/O errors in calls to sqlite3BtreeNext(), and in OP_SeekScan.
f287d0010 2020-09-30 In the OP_SeekScan opcode, changes to pOp must occur after the call to VdbeBranchTaken() so that the VdbeBranchTaken() attributes the branch to the correct opcode.
a54e1b1fc 2020-09-29 The OP_SeekScan opcode is a no-op if the cursor is not pointing to a valid row upon entry.
0b2949c36 2020-09-29 Coverage testing of the OP_SeekScan opcode.  Fix a problem that comes up when OP_SeekScan reaches the end of the table.
dfbaae757 2020-09-29 Improved comments on the new OP_SeekScan opcode.
c40076a8c 2020-09-29 Improved performance by manually in-lining the sqlite3VdbeIdxKeyCompare() routine for the OP_IdxGT opcode and its kin.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
