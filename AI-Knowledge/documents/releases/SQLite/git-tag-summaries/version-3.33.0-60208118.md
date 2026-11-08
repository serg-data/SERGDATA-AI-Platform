# SQLite — Git tag version-3.33.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.33.0
Сравнение с предыдущим тегом: version-3.32.1

## Коммиты в диапазоне

```text
ef215fbf3 2020-08-14 Version 3.33.0
96e337df6 2020-08-13 Fix "make test" handling of environment variable QUICKTEST_OMIT so that it can be used to exclude test files in other than the main test directory.
a3e649597 2020-08-12 Improvement on the previous fix.
b6a74caf9 2020-08-12 Fix an assertion() fault in ALTER TABLE found by OSSFuzz.  Test case in TH3.
c08716a31 2020-08-11 Fix harmless USAN warnings from gcc9.
4dfdb86c8 2020-08-11 New test cases for the use of the ieee754 and decimal extensions in the CLI.
91faeec8d 2020-08-11 Modify a test for corruption within the wal checkpoint code to account for the pending-byte page. And for the fact that test configurations might move the pending-byte page.
8c1fbe81d 2020-08-11 Minor comment fixes.  No changes to code.
24c22753f 2020-08-11 Remove an unused #define from sqliteInt.h.
47eb561c4 2020-08-10 Simplify #ifdefs associated with Parse.eParseMode.  Fix an #ifdef error associated with SQLITE_OMIT_AUTOVACUUM.
9f567eb9f 2020-08-10 Fix a problem causing test failures in corruptL.test for some permutations.
26c48d2aa 2020-08-10 Fix a problem building fts3 separately from the amalgamation.
12a4c4191 2020-08-10 Fix a shell tool build error caused by some combinations of options.
08b920866 2020-08-10 Fix harmless compiler warnings that surface in newer versions of GCC.
ed0af52cb 2020-08-10 Fix another test script problem in walvfs.test.
80aff0847 2020-08-10 Fix minor test script problems.
14d093f84 2020-08-09 Fix a harmless compiler warning.
8afc09dea 2020-08-08 Fix the check-in at [41474548ef3f7454] so that it computes the pointer in time for error checking at the end of the routine in the case of a non-OOM error.
07066d90f 2020-08-08 Fix test script busy2.test so that it works with the inmemory-journal permutation.
47d38e244 2020-08-08 Changes to busy2.test, corruptL.test and fkey5.test so that new test cases pass with all test permutations.
35a37c2a4 2020-08-08 Fix a test script problem causing an error for SQLITE_ENABLE_OVERSIZE_CELL_CHECK builds in corruptL.test.
c664355c0 2020-08-08 Move a pointer computation until after OOM checks to avoid a nuisance USAN warning.
a6c13b22b 2020-08-08 Change the name of sqlite3SelectTrace to sqlite3_unsupported_selecttrace.
d43c0cbed 2020-08-08 Update requirement marks due to wording improvements in the documentation.
7033ce4fd 2020-08-08 Reorder declarations in the decimal extension for C89.
799443b14 2020-08-07 Do the oversize-WAL corruption test before the size hint is issued.
26b9540fc 2020-08-07 Fix a file-descriptor leak in test script corruptL.test.
88819d587 2020-08-07 Return an SQLITE_CORRUPT error if the final expected size of the database when checkpointing is not reasonable - where reasonable is defined (basically) as the sum of the sizes of the database and wal files.
b19493434 2020-08-07 Add the --checkpoint option to speedtest1.
f82ce382f 2020-08-06 Fix the columnar output modes in the CLI so that they work with parameters. See [https://sqlite.org/forum/forumpost/17ba6aac24] for details of the problem fixed.
cec5f1d12 2020-08-04 Fix compilation issues with MSVC.
53218e2e2 2020-07-31 Back out a NEVER() that turns out to be reachable.
41af5b34b 2020-07-31 Remove an ALWAYS() that turns out to be reachable.
199188823 2020-07-30 Test for schema corruption is reachable after all.
e592c18c1 2020-07-30 Provide an alternative "guaranteed-safe" method for overwriting the WAL index on recovery, in case some platform is found for which memcpy() cannot do this safely.
013e7bb74 2020-07-30 Fix compiler warnings in MSVC.
48bf2d72b 2020-07-30 Fix unreachable branches.
8deae5ade 2020-07-29 Fix signed/unsigned compiler warnings.
1024822ba 2020-07-28 Earlier detection of out-of-range page numbers in the btree layer.
e7f3edcd4 2020-07-28 Add an sqlite3FaultSim() to make an OOM case more accessible and remove the ALWAYS() on the conditional that is false when the OOM actually occurs.
f31230af1 2020-07-27 On recovery, always overwrite the old with the new, even if they are the same. Add ALWAYS() macros on branches currently thought to be unreachable, pending additional testing.
cddfc3922 2020-07-27 Fix a couple of test scripts to match the new wal recovery behaviour on this branch.
8caebb26c 2020-07-27 Improved error reporting if walLockExclusive() fails.
d3e38b7c0 2020-07-25 Allow a wal mode recovery to proceed even if there are readers.
8adc8f1ec 2020-07-24 Remove a surplus space from a comment
0c52f5a2b 2020-07-24 Fix other potentiall pointer aliasing problems associated with subclassing of the sqlite3_file object for various VFS implementations.
d9059bdb5 2020-07-24 Fix pointer aliasing problem in the in-memory journal code. Ref: [https://sqlite.org/forum/forumpost/d44eb2fc44|forum post d44eb2fc44]
38f0ccc07 2020-07-23 Add the OMIT_ZLIB compile-time option to sessionfuzz.c.  (Originally checked into the wrong branch.)
b14034739 2020-07-23 Fix a typo in an error message.
2add24c0d 2020-07-23 An ORDER BY clause can slip into an SRT_Upfrom query via the query flattener, even without the SQLITE_ENABLE_UPDATE_DELETE_LIMIT compile-time option.  So always enable the code to deal with that case.
9d44327a8 2020-07-23 Fix another case where a corrupt record could cause an assert() to fail in fts3.
17d2d592f 2020-07-23 Add the ability to do a PRAGMA integrity_check (or quick_check) on a single table by specifying the table name as the argument.
ca439a496 2020-07-22 Disable rootpage bounds checking when the SQLITE_TESTCTRL_EXTRA_SCHEMA_CHECKS setting is off, to facilitate reaching obscure error states during testing.
69306bf43 2020-07-22 Improvements to rootpage bounds checking during schema parse.
3b3ddbae3 2020-07-22 When parsing the schema, detect out-of-bounds rootpage values and throw an error.
584e8b763 2020-07-22 All TCL tests now passing.
bb39ac777 2020-07-22 Most test cases now passing.
abc381586 2020-07-22 Continuing work toward supporting unsigned 32-bit page numbers.
55550b760 2020-07-22 Enhance showdb to be 32-bit clean.
2f04583f0 2020-07-21 Work-around for [https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96270|GCC bug 96270].
82b0f106c 2020-07-21 Add the sqlite3Int64ToText() routine and use it to convert integers to text, as it is much faster than the generic text formatter.
bbd620e22 2020-07-20 Fix the ".read" command so that it gives an error when its argument is a directory. See [https://sqlite.org/forum/forumpost/4c53c434ca|forum message 4c53c434ca].
09cf56929 2020-07-20 Fix a corner-case error in the new UPDATE FROM logic helpfully discovered by OSSFuzz.
4e6861d23 2020-07-20 Add the "enlargedb" utility program used to construct very large database files for testing.
a192807c1 2020-07-20 Faster column name lookup in the columnIndex() routine using hashing.
e9261dbd5 2020-07-20 Initial changes to allow database up to 281TB in size.
51da8daf8 2020-07-18 Fix test case result on a DELETE with an INDEXED BY clause due to improvements in the query planner at [d901837fea1ed54d]
a7c74006a 2020-07-18 More harmless compiler warning fixes.
aec7dc656 2020-07-18 Fix a harmless compiler warning.
387af48ed 2020-07-17 Add ALWAYS() around a conditional that is always true.
4c0086d7f 2020-07-17 Use #ifdef to omit code that is only reachable when the SQLITE_ENABLE_UPDATE_DELETE_LIMIT compile-time option is used.
07ca7d610 2020-07-17 Make it an error to repeat the target object/alias of an UPDATE statement in its FROM clause.
7e1d9512a 2020-07-17 Add a couple of "#ifdef SQLITE_ENABLE_UPDATE_DELETE_LIMIT" blocks missing from new code on this branch.
b1c993f68 2020-07-16 Relax pointless restrictions on allowing tables in the FROM clause from crossing over LEFT JOINs, as long as the table being moved is not the right table of the LEFT JOIN.
9a23d26cb 2020-07-16 Modifications to test code so that the sqlite3MemdebugHastype() assert() statements are enabled for Tcl tests.
369e758fd 2020-07-16 Small performance improvement and size reduction in sqlite3DbStrNDup().
01b2344b3 2020-07-16 Add OOM test for UPDATE...FROM statements inside triggers.
b866a65d4 2020-07-16 Fix a double-free of the FROM clause of an UPDATE inside of triggers.
6265c47a1 2020-07-16 Separate VdbeCoverage() macro for different jumps.
525326ef7 2020-07-15 Fix a problem in UPDATE FROM in which it tries to free using sqlite3_free() instead of sqlite3DbFree().
e7cf8fdd1 2020-07-15 Add tests for UPDATE...FROM and foreign keys.
576d5a863 2020-07-15 Fix problems that could occur if a table with the same name as the table being updated appeared in the FROM clause of an UPDATE statement.
243210b79 2020-07-15 Fix a problem in SQLITE_ENABLE_HIDDEN_COLUMN builds occuring when an UPDATE...FROM fired an INSTEAD OF trigger.
d8b3c1999 2020-07-15 New test cases for decimal and ieee754.
19543b9b7 2020-07-14 Now appears to work.  All legacy tests pass.  Need to add new tests, however.
e7877b2d6 2020-07-14 Support UPDATE...FROM statements in trigger programs.
c37b7680a 2020-07-14 Fix an obsolete header comment on the sqlite3WhereIsOrdered() routine.
bc2cf3b29 2020-07-14 Early detection of freelist size corruption in incremental vacuum.
751a44ed2 2020-07-14 Fix a crash.  Not all tests pass, but tests do at least run to completion now.
6e4b140e9 2020-07-14 Fix an obsolete assert().
f067ae8eb 2020-07-13 Add test for LEFT JOIN in UPDATE...FROM statement.
be952c11d 2020-07-13 Add test cases and fixes for UPDATE...FROM statements that modify primary key columns.
5b107654e 2020-07-13 Readd the ALWAYS() macro that was removed by [f7a74f89dbd58b47] as the condition is no longer reachable due to the previous check-in.
27da907f8 2020-07-13 Fix a problem causing queries containing window functions to ignore collation sequences under some circumstances.
bbc9e1908 2020-07-13 Fix an integer overflow bug in fts5 triggered by a corrupt record.
56215eaff 2020-07-11 Add second test case for the improvement in [30735432].
a1085f064 2020-07-11 Improved detection of a corrupt database schema. Fix for a problem discovered by dbsqlfuzz.
6af305de1 2020-07-10 Remove unnecessary code from the window functions implementation.
413b94af8 2020-07-10 An attempt to get the Min/Max optimization working with IN constraints. Not currently working.
b16425d05 2020-07-10 Fix a broken assert() in fts3 that could fail when handling corrupt records.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
