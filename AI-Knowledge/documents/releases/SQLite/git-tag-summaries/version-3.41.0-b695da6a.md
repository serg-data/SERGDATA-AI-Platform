# SQLite — Git tag version-3.41.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.41.0
Сравнение с предыдущим тегом: version-3.40.0

## Коммиты в диапазоне

```text
3b832a1a2 2023-02-21 Version 3.41.0
b5726a76f 2023-02-21 Disable DQS by default in the MSVC makefile for the amalgamation tarball.
61f0a0349 2023-02-21 Yet another comment typo fix.  No changes to working code.
0c30eaec9 2023-02-21 Fix a minor typo in a comment.  No changes to working code.
6e2b2f307 2023-02-21 Fix formatting and improved documentation on the various sqlite3_file_control() opcodes.  Other minor documentation changes.  No changes to working code.
3eeace23f 2023-02-20 Update the TEA version number to 3.41.0
ffe9bfd8e 2023-02-20 Fix an incorrect #ifdef in the CLI.
e17cac189 2023-02-19 Fix a harmless compiler warning.
1603f7ede 2023-02-18 Fix stale requirement marks and fix a typo in the documentation for sqlite3_preupdate_hook().
3c7e90b89 2023-02-18 Fix a harmless UBSAN warning in debugging code of the new unhex() function.
16cdb4b63 2023-02-17 Fix a harmless typo in the test case added by [29fc06465efb948f].
ab31a5df9 2023-02-17 Do not allow the COUNTOFVIEW optimization to run if the count() contains a FILTER clause.  dbsqlfuzz 4f8e0de6e272bbbb3e1b41cb5aea31e0b47297e3
bdb2ec409 2023-02-14 Update testrunner.tcl to run zipvfs test scripts on unix.
d6ba4252b 2023-02-13 Ignore extra parentheses around a subquery on the RHS of an IN operator, because that is what PostgreSQL does.
b4dc263ec 2023-02-13 Do not allow WHERE clause terms to match constant string index terms, which can happen if DQS_DDL is enabled.  Follow-up to [44200596aa943963].  dbsqlfuzz 54c9db85ed4af7055f5fd0d50877875c82b11d46.
5c84aafd7 2023-02-13 Fix compile time option SQLITE_DEFAULT_SYNCHRONOUS so that it works consistently.
0c6993851 2023-02-13 Allow vector-IN expressions like "(a, b) IN ( (?,?), (?,?) )" to use an index.
9e463e878 2023-02-13 In the LIKE optimization, do not analyze the new virtual WHERE clause terms until both have been added, since they are expected to be consecutive and the analysis might add complementary terms. This fixes a problem caused by [44200596aa943963] and discovered by dbsqlfuzz and recorded as case 7e3b5983727d843b910b2d9ab556e4afcd777cfb.
0c55b5fd1 2023-02-11 Change a variable from 32 to 64-bits to avoid a harmless compiler warning in Xcode.  [forum:/forumpost/402d733c22|Forum post 402d733c22].
80e936aef 2023-02-10 Do a better job of detecting when a WHERE clause term might be useful to an expression index.  Fix for performance regression reported by [forum:/forumpost/e65800d8cb|forum thread e65800d8cb].
a3e619294 2023-02-10 Fix a problem with the fts5 trigram tokenizer and LIKE or GLOB patterns for which contain runs of 2 or fewer non-wildcard characters that are 3 or more bytes when encoded as utf-8.
74e6e3035 2023-02-10 Ensure that the valueFromFunction() routine does not clear a prior parser error.  dbsqlfuzz 6fa816f20cf5b62260d635d110b88f38e29d8fe1.
98094e2f4 2023-02-10 Minor text-only updates to wasm demo/test HTML and license header.
c9e3cbe87 2023-02-10 Fix ext/wasm/fiddle build, which was silently broken by recent build refactoring.
3f4795a39 2023-02-09 Disable the double-quoted string misfeature by default in CLI builds. DQS can be reenabled at run-time using the ".dbconfig dqs_dml" and ".dbconfig dqs_ddl" dot-commands.
5b56a1397 2023-02-09 Squelch two harmless signedness comparison warnings in shell.c.in.
9a8330b55 2023-02-09 New test cases added to fuzzdata8.db.
a0c8ec9ee 2023-02-09 The "flexnum" affinity that was added by [44135d6ea84f7ba6] needs to also be added to the output of the affinity() built-in function. dbsqlfuzz d309eaa5fe492c9606a8be876c2bc7dedb29d3d8
601e4d4a0 2023-02-08 Back out the 'txn' enhancement to date/time functions.  The duration of a "transaction" is confused and needs to be straightened out prior to moving forward with this change.
03b30b7ab 2023-02-08 Always use 64-bit integers for stats associated with STAT1 and STAT4.
0d12a7931 2023-02-08 Better fix the problem where optimizing an fts5 table too often causes it to become unreadable (first attempt was [35bed981]).
72ce57e67 2023-02-08 Cause gcc warning suppression in shell.c to be nice in other project(s).
8ae1d29b1 2023-02-08 Update an assert() in the stat4 code that is only true for a well-formed database.
0873d8842 2023-02-08 Fix an incorrect assert() in STAT4 logic added just a few days ago on [2023-02-01|/info/55a26c67ed4a3a93].
159cbfe1c 2023-02-08 Test cases to show that CURRENT_TIMESTAMP and similar hold the same value across a transaction.
ed092fc36 2023-02-08 Revert the behavior of date/time functions with no arguments so that they once again work like 'now', even while CURRENT_TIMESTAMP and similar work like 'txn'.
c1dab9ded 2023-02-08 Change the behavior of date-time functions without any arguments (and thus the CURRENT_TIME, CURRENT_DATE, and CURRENT_TIMESTAMP variables) so that they work like 'txn' instead of like 'now'.  This is an incompatibility with legacy, but brings SQLite into conformance with all other SQL systems.
3393ee7ff 2023-02-07 Simplify the code and add test cases.
d4af882a1 2023-02-07 Add support for the 'txn' argument to date/time functions that works like 'now' but keeps the same time for the entire transaction.
c3ea539dc 2023-02-07 Fix a test script problem causing "make test" to fail for non-RBU builds.
9d6725c65 2023-02-07 Fix a typo in example documentation code for sqlite3_vtab_in_next().
9f29998d2 2023-02-06 Roll back part of [c54f29d8] which attempted to use symbols which that worker does not have access to.
8057fe9ba 2023-02-06 Fix RBU test scripts to avoid attempting to copy or delete a locked file.
913ea7744 2023-02-06 Fix the build after the previous change
da3d655fd 2023-02-06 Remove the long obsolete "client/server" mode tests.
6896da42c 2023-02-06 Update test scripts speed1.test and speed1p.test so they may be run by testrunner.tcl.
634ed6431 2023-02-06 Shorten the status line for testrunner.tcl so that it fits on an 80-character terminal.
adc21bd43 2023-02-06 Fix error in the releasetest makefile target from the previous check-in.
4bce18250 2023-02-06 Update "releasetest" makefile targets to use testrunner.tcl.
3ff812aa9 2023-02-06 Add capability to override the JS's use of console.log/debug/warn/error() with client-provided versions via the bootstrap-time config object.
ee18659f6 2023-02-06 Fix a formatting problem in scanstatus2.test introduced by [81c118d9].
0bd0843eb 2023-02-06 Add the --fuzztest option to testrunner.tcl. Also, have it print whitespace over the top of the old report line before writing the new.
2288ecbb9 2023-02-06 Fix problems with test scripts preventing them from running with SQLITE_DEFAULT_MEMSTATUS=0 builds. Or builds without SQLITE_ENABLE_STAT4.
e734207a7 2023-02-06 Fix some test scripts that were failing with SQLITE_OMIT_VIRTUALTABLE builds.
072f48e55 2023-02-05 Do not use a Bloom filter if any outer loop lacks STAT1 data, since without STAT1 data, the query planner cannot make an accurate determination of whether or not a Bloom filter will be useful.  This fixes the problem reported by [forum:/forumpost/56de336385|forum post 56de336385].
9ce864367 2023-02-05 Add the "devtest" makefile target that runs both fuzztest and testrunner.
e88b20987 2023-02-05 In fuzzcheck, only show the description of each database if the -v option is specified.
8d07c3d49 2023-02-05 Restore a test for pBt NULL that was removed by [12a14711afa6cddb] but turned out to be necessary, as dbsqlfuzz quickly showed us.  Test case added to TH3.
fdde4042e 2023-02-05 Modify the status line output from testrunner so that each line overwrites the previous rather than scrolling.
2f9525b0f 2023-02-05 Changes to the sqlite_dbpage virtual table to tag or remove unreachable branches.
a3d4d7a0a 2023-02-04 Avoid running rbu tests under permutation "journaltest", which does not support wal. Fix some other test script problems.
111057cf6 2023-02-04 Add ALWAYS() and NEVER() macros to unreachable branchs in sqlite_dbpage.
5db5c122e 2023-02-04 Remove an ALWAYS() that can be false in some very rare cases. dbsqlfuzz 2274a23c85a93b870f7eb12fe686073da01abc33
b713d501f 2023-02-04 Changes so that wapptest.tcl still works.
0415dd9c5 2023-02-04 Update testrunner.tcl usage message.
4e5ff3b82 2023-02-04 Add testrunner.tcl "njob" and "status" commands.
ad1079e35 2023-02-04 Better error message when trying to do an INSERT on an sqlite_dbpage virtual table.
bd55d3dda 2023-02-03 Fixes for testrunner.tcl on windows.
d40a18350 2023-02-03 Fix a problem where optimizing an fts5 table too often might cause it to become unreadable.
33d355973 2023-02-03 Have testrunner.tcl run various builds as part of the 'release' command.
989d0cec5 2023-02-03 Attempt to fix harmless compiler warnings that reportedly appear in clang 15.
410a3bafe 2023-02-03 Improved detection of invalid command-line arguments to the showdb and showwal debugging utility programs.
60228cb3d 2023-02-03 Avoid using Tcl command [clock] in testrunner.tcl.
e18fdcd35 2023-02-02 Do not run test script pendingrace.test as part of the inmemory_journal permutation.
b0c8e2f90 2023-02-02 Add configuration data for osx and windows to testrunner_data.tcl
2dd3b645b 2023-02-02 Improved and simplified logic for resolving the various aliases of the schema table.
6f31eac7d 2023-02-02 Resolve all possible aliases and variations of the schema table names.
7667eedf9 2023-02-02 Remove automatic installation of JS-global S object for the sake of client libraries which embed this library, per [forum:9d4f722c6912799d|request in the forum].
71a933967 2023-02-01 Adjustments of assert() statement in STAT4 in order to give 100% MC/DC.
45ae9d6ba 2023-02-01 New assert() statements to verify that sqlite3DeleteIndexSamples() is always called with non-NULL parameters.
986c22a6d 2023-02-01 Update testrunner.tcl to use a separate process for each test script. And to run some extra tests too.
54725efd8 2023-02-01 Just because a CTE is used more than once, does not mean it should be tagged with M10d_Yes and thereby prohibited from participating in the query flattening optimization.  See [forum:/forumpost/1d571c02963355ed|forum thread 1d571c02963].
288409d73 2023-02-01 Fix a comment related to PENDING locks in os_unix.c. No code changes.
ca3aabdf5 2023-01-31 Fix a race condition during hot-journal rollback that could theoretically cause spurious corruption errors.
f7af9ba13 2023-01-30 Additional tweaks to the enhancement at [609fbb94b8f01d67] to further reduce the cost estimate for constructing an automatic index on an ephemeral table, in order to resolve the performance problem described by [forum:/forumpost/1d571c0296|forum post 1d571c0296].
26c7cff25 2023-01-29 Two JS file renames which got inadvertently undone while setting up [9062b31174618c0e]. Cosmetic cleanups in ext/wasm/dist.make.
2f5330036 2023-01-29 Correct the handling of the worker1 and promiser JS files in the face of the bundler-friendly changes. Those files require separate, bundler-friendly copies.
05a377fd4 2023-01-28 Do not assume that sub-queries that contain window functions are uncorrelated.
8cc8d36e4 2023-01-28 Show more details about the SrcItem.fg field in tree-trace output.
20438431c 2023-01-28 Fix a problem causing "PRAGMA quick_check" to return spurious corruption errors for a WITHOUT ROWID for which all columns are either virtual or part of the primary key, and for which the order of the columns in the primary key definition is different from the order in the table.
54c9250b0 2023-01-28 Update sqllimits1.test to account for the fact that if an odd value is specified as the length in bytes of a utf-16 string, it is truncated to the largest smaller even number.
c7170350d 2023-01-28 Makefile doc touchups - no code/build changes.
919fe5bac 2023-01-28 Overhaul ext/wasm/GNUmakefile to consolidate what amounts to much copy/paste/slightly-edit duplication into a single function, called once per distinctive build mode (vanilla, ESM, bundler-friendly).
e84454ff1 2023-01-28 Enhance oo1.DB.exec() to simplify returning whole result sets.
cfd01014d 2023-01-27 Fix compiler warning in base85.c.
69141f52b 2023-01-27 Update ext/wasm/README-dist.txt for the bundler-friendly build.
f92b006a6 2023-01-27 Add an assert() to help static analyzers.
844e7183a 2023-01-27 Do not try to run rbu tests with builds that do not support rbu.
6a3e2d377 2023-01-27 Add a feature idea note to DB.exec(), derived from a forum discussion.
cf73cb2fb 2023-01-27 Cherrypick [3773934e91c20ca243] into trunk.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
