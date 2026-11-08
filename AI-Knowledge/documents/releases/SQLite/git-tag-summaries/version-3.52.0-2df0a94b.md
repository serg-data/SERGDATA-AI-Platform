# SQLite — Git tag version-3.52.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.52.0
Сравнение с предыдущим тегом: version-3.51.0

## Коммиты в диапазоне

```text
257fdf849 2026-03-06 Version 3.52.0
93353c0bc 2026-03-06 Add the new realpath() extension function to the list of functions prohibited in --safe mode of the CLI.
ea595494e 2026-03-06 Uninstall faultsim at the end of the walrestart.test script.
7a125b97d 2026-03-05 Fix the build for -DSQLITE_OMIT_FLOATING_POINT.
21bdb75ac 2026-03-05 Ensure xMutexInit() is called in SQLITE_THREAD_MISUSE_WARNINGS builds.
bef2a1e33 2026-03-05 Add a little flexibility to checkpoint sizes in the walrestart.test script.
0f7f9ab00 2026-03-04 Remove dead (commented-out) code that came to my attention because it ws nearby the fix of the previous check-in.
76e562e22 2026-03-04 Fix a code-generator bug introduced by the UNION/INTERSECT/EXISTS optimization of check-in [132ba781b031972c] and reported in [forum:/forumpost/2026-03-04T05:06:26Z|forum post 2026-03-04T05:06:26Z].
8ba2a3836 2026-03-03 Do not run test script walrestart.test with the "memsubsys1" permutation.
bb80d688a 2026-03-03 Minor tweaks to the previous, for testability.
fe57e14b4 2026-03-03 Avoid an obscure race condition between a checkpointer and a writer wrapping around to the start of the wal file.
f6c8adf3a 2026-03-02 Omit explain_i calls from TCL test scripts.
72afb50a6 2026-03-02 Fix TEMP INSTEAD OF triggers so that they work on TEMP views. [forum:/forumpost/2026-02-28T23:33:04z|Forum post 2026-02-28T23:33:04z].
7fa89ea90 2026-03-02 Change some sqlite3_realloc() calls into sqlite3_realloc64().
c1454ee83 2026-03-02 Remove the experimental and incomplete ext/repair extension,  to prevent AIs from scanning the (incomplete) code and reporting bugs against it.
ea6b2a87d 2026-03-02 Disable test shell1-5.0 as it is causing a use of initialized deep inside of TCL.
f27046036 2026-03-02 Use only 64-bit memory allocation in FTS5.  Fix for UAF reported by Zijie Zhao.
33478099c 2026-03-02 Fix a possible 9-byte buffer overread in the zipfile extension hit when processing a corrupt zip file. Forum post [forum:/forumpost/721a05d2c5 | 721a05d2c5].
93ad2e083 2026-03-02 The intck01.sql test should only be run if virtual tables work.
ffaf9110f 2026-03-01 More floating point conversion test cases.
7e4e866ba 2026-03-01 New floating-point test case.
e293b2d83 2026-03-01 Fix an OOB read in the incremental integrity-check extension.
83de60bd7 2026-03-01 Simplified rounding logic in sqlite3Fp10Convert2().
a000db975 2026-02-28 Code changes in sqlite3Fp10Convert2() for easier maintenance.  Does not affect the generated machine code.
7ac310d0c 2026-02-27 Improvements to power-of-ten computations used for text &harr; binary64 conversions.
afaf7ea2e 2026-02-27 Minor simplification to the text&rarr;binary64 conversion algorithm.
f707e2ec5 2026-02-27 Two code comment typo fixes reported in the forum. No code changes.
7d9fbe647 2026-02-27 Fix an off-by-one error in the indentation of multi-line outputs in QRF_STYLE_Line mode.
c67a53816 2026-02-27 Add an assert() to sqlite3RegisterLikeFunctions() to hopefully prevent future false-positive bug reports coming out of CodeQL.
57d7a20ce 2026-02-27 Another nano-optimization in kvvfs v2.
d22d0edc4 2026-02-27 JS: slight performance improvements in KVVfsStorage.
5dfccfb0b 2026-02-26 Fix typos in the SQLITE_PREPARE_FROM_DDL documentation.
5a6eef2fb 2026-02-26 Improvements to the SQLITE_PREPARE_FROM_DDL documentation.
8bc78bebf 2026-02-26 Fix an inconsequential typo in the output of the datedebug() SQL function.
a86c6017e 2026-02-26 Fix a problem where the wrong collation could be used as part of a row-value comparison between columns with different collation sequences. [forum:/forumpost/6ceca07fc3 | Forum post 6ceca07fc3].
1a152ea92 2026-02-25 The GCC bug is fixed in GCC-15.
f45c69547 2026-02-25 Reinstant the work-around for [https://gcc.gnu.org/bugzilla/show_bug.cgi?id=96270|GCC compiler bug 96270] which is apparently still an issue as of gcc 13.3.0 with -m32 on Mint Linux. The test case in the bug report is fixed, but the vdbeMemRenderNum() routine in SQLite still shows the problem.
46bf39e39 2026-02-25 Use a 64-bit hash for the testing option SQLITE_CHECK_PAGES to maintain page alignment.
b1a73ba34 2026-02-24 Adjust the changes to shell8.test from [5da9bf09cc00faf9] so that they work with older versions of TCL.
9d6529020 2026-02-24 Rename SQLITE_ENABLE_MULTITHREADED_CHECKS to SQLITE_THREAD_MISUSE_WARNINGS. Run test cases with that option. Also add the SQLITE_THREAD_MISUSE_ABORT option.
da67225f0 2026-02-23 Fix an assert() that is incorrect when the SQLITE_DBCONFIG_FP_DIGITS setting is on a non-default value.
d2e27e5d5 2026-02-23 Add test cases for the symlink defenses of the previous check-in.
ffd9892a0 2026-02-23 Change the SQLAR archive extraction algorithm in the CLI so that it uses the newly enhanced realpath() SQL function to guard against attacks that use symlinks to try to write files outside of the destination directory. [forum:/forumpost/641b09daa17d9086|Forum post 641b09daa17d9086].
9235f9b04 2026-02-23 Enhance the realpath() SQL function in the fileio.c extension so that it works ever for pathnames that do not exist.
9dac613f0 2026-02-23 When doing an SQLAR archive extraction in the CLI, postpone creating symlinks until after all files and directories have been created.  This prevents a hostile archive from creating a symlink through which it can subsequently write content outside of the target directory.  [forum:forumpost/9e176adfef91c207|Forum post 9e176adfef91c207].
95fe5b9c3 2026-02-23 Improved implementation of realpath() in the fileio.c extension that does not require the last element of the path to actually exist.
9bc017423 2026-02-22 Add the realpath() SQL function to the fileio.c extension.  And clean up the UTF8 handling on the Windows side of that extension while we are at it.
60f132bf1 2026-02-21 Fix typos and include wording in the documentation for SQLITE_DBCONFIG_FP_DIGITS.
f8681fb63 2026-02-21 Fix a harmless warning in the decimal extension.
8642ca202 2026-02-21 New sqlite3_db_config(SQLITE_DBCONFIG_FP_DIGITS) that let's the application specify the number of significant digits that double&rarr;text conversions will attempt to preserve.
699959ff2 2026-02-21 New test cases for floating-point conversions.
7aba85859 2026-02-21 Remove an unreachable branch.
4428aa842 2026-02-21 Increase the precision of double &rarr; text conversions that happen in sqlite3_column_text(), or sqlite3_value_text(), or in the CAST() operator, or similar, so that round-tripping the value back to double results in exactly the same value.
24ef9fbb1 2026-02-21 Further simplification, performance gain, and size reduction in sqlite3FpDecode().
aec283385 2026-02-21 Small performance increase and size reduction in sqlite3FpDecode() by using local variables instead of structure elements.
ac5ee556e 2026-02-20 Inconsequential changes to floating-point conversion, amounting to mere code cleanup to aid comprehension.
62546d4b1 2026-02-20 In the decimal extension, an optional second argument to the decimal() and decimal_exp() functions rounds the value to the number of significant digits specified by that argument.
9e395efec 2026-02-20 Fix a cse in the fiddle.debug build where it could not overwrite its read-only/generated index.html.
d447df420 2026-02-20 Add new functions ieee754_to_int() and ieee754_from_int() to the ieee754 extension.  No changes to the core SQLite.
20c65785c 2026-02-20 Improved rounding of floating-point conversions in some corner cases.
e8750019c 2026-02-19 In the CLI, the ".quit" command in a --cmd argument causes an immediate exit.  [forum:/forumpost/f057122b68|Forum post f057122b68].
cac09127e 2026-02-19 Improvements to rounding behavior in the new floating-point conversion logic.
37ee141d2 2026-02-17 Restore the CLI function dtostr() back to its original purpose of converting floating point values to decimal using the host computer's C-library.
7549e784a 2026-02-17 Minor fixes to tmstmpvfs.c.
8c3e8dce4 2026-02-17 Increase the number of floating-point precision test cases by 9x, and increase the require precision to 16 digits.
31d4e56b2 2026-02-17 Fix a harmless compiler warning from MSVC.
530f536ce 2026-02-17 New assert()s for the return value from sqlite3SchemaToIndex().
0b5e94448 2026-02-17 Faster conversion of integers to text, by converting two digits at a time.
63338e3ba 2026-02-16 Simplifications to sqlite3AtoF(), resulting in slightly faster performance and slightly smaller size.
6315919ba 2026-02-16 Fix a bad assert() in the previous check-in.
5c977eaa0 2026-02-16 Refactor the sqlite3AtoF() routine so that it requires a zero-terminated UTF-8 input.  When the need arises to convert UTF16 or non-terminated strings, wrapper functions are used.  Together, this makes the code slightly smaller and faster.
1105c3390 2026-02-16 Fix another case where SQLite might fail to identify an ON clause on a RIGHT or FULL join that refers to FROM-clause elements to its right.
7b93f1a38 2026-02-16 Fix a problem with identifying ON clauses attached to RIGHT or FULL JOINs (which is an error) if the join appeared in a flattened sub-query.
adbb75615 2026-02-15 Avoid the big power-of-ten lookup table.
658908a32 2026-02-14 Fix to [9d3a12d3926d55ef] to force the static const string literal to have two-byte alignment.  Necessary to get that patch to work in Mac-ARM.
b3b2695d4 2026-02-14 Add the "LLU" suffix to 64-bit integer constants, for portability to older compilers.
775e4b707 2026-02-14 Fix to the generic version of the 128-bit multiple subroutine.
4bee65dcb 2026-02-14 Another minor performance refinement.
4d0611c1e 2026-02-14 Minor corrections.
10fb1e307 2026-02-14 Improved comment.  No code changes.
db84cdb74 2026-02-14 Use a precomputed table of 696 powers of 10 to improve the performance of floating-point to decimal and decimal to floating-point conversions.
990d86103 2026-02-13 Add new assert() statements to demonstrate that the complaint given in [forum:/forumpost/56ad8b632c|forum post 56ad8b632c] is not a real bug.
23e57bc7c 2026-02-13 Use only a single bit, rather than a whole byte, to store infrequently accessed boolean values in the Parse object.
7d49eb1df 2026-02-13 Add a "const" to avoid a harmless false-positive compiler warning.
df59c5da7 2026-02-12 Respect "const" strings in the sqlite3ShadowTableName() function. Patch moved to trunk, where it was intended.
643fb6cf4 2026-02-11 Minor performance enhancement to floating-point rendering.
c652e3431 2026-02-10 Correction to date/time computations associated with the timestamp-vfs.
c94f97fac 2026-02-10 Minor tweaks to the star-query optimization in the query planner.
1f9ae1f78 2026-02-09 Immediately reset all pending prepared statements on any call to sqlite3_set_authorizer(), even if the authorizer is being disabled.
612bee531 2026-02-09 Do not allow table-function argument expressions on the RHS of an OUTER join to refer to FROM clause elements to their right.
de702aebb 2026-02-08 Fix a method name typo in test-only code which could hide the triggering error condition.
e45418c5f 2026-02-08 JS doc touchups.
a0857f321 2026-02-07 Improved output from calls to sqlite3ShowSrcList() made from a symbolic debugger.
450a90097 2026-02-05 Do a better job of not generating unnecessary Bloom filters associated with IN operators.
e58c1a987 2026-02-05 Fix harmless compiler warning when the CLI is compiled with SQLITE_OMIT_PROGRESS_CALLBACK.
d0c4a5853 2026-02-04 Display scanstatus results in neat columns.
c9ccd2704 2026-02-04 Improved display of scan-status estimates.
5e842d0ec 2026-02-04 Render scan-status values with 3 or 4 significant digits only, for improved readability.
3fab5d2a4 2026-02-04 Fix scanstatus output in QRF so that it shows the total number of cycles on the "QUERY PLAN" line.
e54142009 2026-02-03 Minor change to test/dotcmd01.test so that it works with STAT4.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
