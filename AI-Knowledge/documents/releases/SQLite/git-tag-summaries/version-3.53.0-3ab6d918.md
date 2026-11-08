# SQLite — Git tag version-3.53.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.53.0
Сравнение с предыдущим тегом: version-3.52.0

## Коммиты в диапазоне

```text
4ebc7fdcf 2026-04-09 Version 3.53.0
df3e20750 2026-04-09 When generating make.sh for testrunner, correctly quote the value of any options passed via environment variable OPTS.
535b1f287 2026-04-09 Fix some buffer overreads that might occur in the session module when handling corrupt changesets.
a7200804e 2026-04-08 Fix a buffer overflow bug in a recent check-in, reported by unsolicted email from OpenAI/Codex.
0d979c217 2026-04-07 Fix a few doc typos and inconsistencies. No code changes.
e9af8caac 2026-04-07 Fix incorrect datatype on the auto_ext_leak_tester() function in the CLI.
606c64a54 2026-04-07 Fix redundant typedef in qrf.c when that file is amalgamated into tclsqlite3.c.
eefe3aa9a 2026-04-07 Replace a doc reference to a renamed file, as reported by [forum:5d9d70c618|forum post 5d9d70c618]. No code changes.
fcef193a8 2026-04-06 Add a dummy auto-extension to the shell in SQLITE_DEBUG builds to validate that [9d56df17b4ab49] does the right thing.
8e7ffc09f 2026-04-06 Add a call to sqlite3_reset_auto_extension() near the end of shell.c.in:main() to squelch a leak message when SQLITE_EXTRA_INIT adds auto-extensions, as reported in [forum:310cb231b07c80d1|forum post 310cb231b07c80d1].
9ad63c0f4 2026-04-04 Appease static analyzers by masking the index to the WalHashLoc.aPgno array to make it easy to prove that there is never OOB read or write.
d4b74b9fa 2026-04-04 Add some comments to the OPFS async proxy about potential future experimentation. No code changes.
7ff8b558e 2026-04-03 Enhance testrunner.tcl so that a PATTERN argument that begins with "~" is an "anti-pattern".  Only run tests that match one or more patterns if there are any patterns *and* do not match any anti-pattern.
bb6d2a5f0 2026-04-03 configure script: replace two 'file normalize' calls with file-normalize (a tcl/jimsh compatibility issue) to fix --with-linenoise. Problem reported in [forum:ce688d13793bd78f|forum post ce688d13793bd78f].
217c59068 2026-04-03 Fix Tcl9 compatibility issues in test_session.c.
fc19b2ca8 2026-04-02 Minor patch to test/json/json-speed-check.sh.  That script is not maintained, but this fix at least gets it working for now.
62f315020 2026-04-01 Fix a potential 4-byte overread in the sessions module when processing a corrupt changeset.
34e139d3a 2026-04-01 Always use sqlite3_malloc64() in extensions, where possible.
6e6598c8f 2026-04-01 Fix a problem in the sessions module allowing a NULL pointer to be passed to memcpy().
e230de2cb 2026-04-01 Minor improvements to the documentation on how to compile for Unix. No changes to code.
eb8edc0ba 2026-04-01 Doc cleanups in opfs-wl. No code changes.
d6226a9c2 2026-03-31 Add appropriate headers to ext/session/sqlite3session.h so that the documentation generator will pick up the API documentation for the new one-at-a-time changegroup APIs.
60b829e0d 2026-03-31 Turn an incorrect assert() into a testcase().  Fix over-length code lines in the sqlite.h.in source file.  Fix the documentation on OOM conditions in the sqlite3_value_text() family of APIs.
f92d10724 2026-03-30 Move some build docs around for clarity. Move the TARGET_DEBUG flags from the end of T.cc to the beginning so that -Ox flags can be passed to make for specific binaries without having to reconfigure.
b060cecb2 2026-03-30 Remove an unused variable in sqlite3Reindex().  Minor enhancements to the header comment on sqlite3AtoF().
0cb576f30 2026-03-29 Fix harmless compiler warnings about unused variable assignments.
03f13d77a 2026-03-29 Avoid using unsigned 64-bit integer division on platforms that do not support it in hardware.
445fbc61c 2026-03-29 The _umulh() intrinsic function is not available on 32-bit windows.  So don't use it there.
eb0cb3f53 2026-03-28 In sqlite3_str_vappendf(), write floating-point renderings directly into the output buffer, saving a memcpy().
5239e69fb 2026-03-28 Remove a harmless unused variable from the fp-speed-2.c benchmark.
20d93e16d 2026-03-28 Enhancements to the fp-speed-N.c programs, suggested by Andreas Kupries.
c409eaaf1 2026-03-28 Reduce the compiled size of the quote() SQL function.
2e0141676 2026-03-28 Turn an sqlite3VMPrintf() into an sqlite3DbStrDup().
ff8a0895d 2026-03-27 Fix up the floating-point speed tests so that they only need to be run once to get a performance comparision.  Provide the fp-speed-test makefile target to build and run them both.
a2f78f665 2026-03-27 Add a comment to test/fptest01.sql to remind us that failures in that script might not be the fault of SQLite.
c4cedd7ff 2026-03-27 New test cases for text&rarr;float conversions.
00c6eca32 2026-03-27 Enable the use of intrinsic high-precision multiplies on Windows ARM. Make the SQLITE_DISABLE_INTRINSIC option effective on high-precision multiple subroutines, for testing purposes.
be2242d2e 2026-03-27 Change the print resolution the fp-speed-1.c test to 17 digits.
2dd3b4a64 2026-03-27 Update fp-speed-1.c and fp-speed-2.c to include its own timers, so that it works on platforms that lack the "time" command.
4570aeb7b 2026-03-27 Add the fp-speed-2.c performance test program.
1283969f2 2026-03-27 Add a comment showing reserved file-control numbers to sqlite3.h
772ea2f01 2026-03-26 Add SQLITE_STRICT_SUBTYPE to PRAGMA compile_options, an omission reported in [forum:3906a71526|forum post 3906a71526].
d4af925e3 2026-03-26 Enhance the return value from sqlite3AtoF() so that it reports if the input includes more than 19.25 significant digits.
61d3bc8dd 2026-03-26 Revamp the return code from sqlite3AtoF() for additional information and for small speed improvement and size reduction.
f9a3b7856 2026-03-26 Improvements to the sqlite3AtoF() interface.  Add a test-control for direct testing of sqlite3AtoF().
f855727e4 2026-03-26 Back out the sqlite3_atof() API, for now.
3d58f022a 2026-03-25 Fix an off-by-one error that cause a loop to (harmlessly) run more times than necessary.  Performance optimization, not a bug fix.
7e9eaf3c1 2026-03-25 Performance optimization when zero-padding in printf().
0944b3efa 2026-03-25 Small size reduction and performance increase in sqlite3Atoi64().
f3f194c38 2026-03-25 Signification optimizations to layout of text for floating point conversions in sqlite3_str_vappendf().
183a73c35 2026-03-25 Handle the case where the compile-time default page-size is greater than 8192 bytes.
53197b794 2026-03-24 Prevent overly long JSON paths from using too much stack space.
f1f1784f4 2026-03-24 Limit JSONB recursion depth in the json_patch() function.
814f592cf 2026-03-24 Improved error messages for JSONB nested too deep.
9b805c624 2026-03-24 Remove a stale reference to the long-removed SQLITE_MUTEX_APPDEF, as pointed out in [forum:348453389b|forum post 348453389b].
3c2ccd290 2026-03-24 Minor simplification to JSON path error reporting.
7bf4d708d 2026-03-24 Recognize artifical JSONB blobs with deep recursion as being ill-formed.
5239e821e 2026-03-23 Move datatype and structure definitions up near the top in the CLI source code, to facilitate future changes.  No changes to the actual logic (yet).
a217a4af0 2026-03-23 Require a button click to start the OPFS concurrency tester, rather than simply launching all N workers immediately on page load.
3e3c31ff0 2026-03-23 Use sqlite3_atof() instead of atof() in the CLI.  Dogfooding.
dc32016ee 2026-03-23 Move the definition of the new sqlite3_atof() function in sqlite3.h so that it is adjacent to sqlite3_mprintf().
80b88b248 2026-03-22 Proposed new API routine: sqlite3_atof().
dfd31e158 2026-03-22 Additional performance improvements in sqlite3AtoF().  Also update the header comments.
cc19c1daf 2026-03-22 Further simplification and performance improvement
99571bf3c 2026-03-22 Performance improvements in the floating-point number parser.
3c1f72760 2026-03-21 Because version 3.52.0 was withdrawn, that means QRF has never been officially released.  Hence the new nMultiInsert field of the spec can be moved out of the extensions area and into the main part of the spec, and the version number can drop back from 2 to 1.
d9e70f2b9 2026-03-21 Try to fix harmless compiler warnings from legacy C compilers in the CLI.
958b6a52e 2026-03-21 Undo "indices"&rarr;"indexes" changes in comments, to avoid diff clutter. Fix a couple of unreachable branches.
f62cff6a9 2026-03-20 Fix harmless compiler warnings in the csv.c.
f163bfba4 2026-03-20 If the argument to REINDEX is EXPRESSIONS (with no schema prefix) then it updates both expression indexes, and any indexes named "expressions" or all indexes of any tables name "expressions".
b0a4b69b9 2026-03-20 If there are not collating sequences, tables, or indexes named "EXPRESSIONS" then the "REINDEX EXPRESSIONS" command rebuilds all expression indexes.
bd580270a 2026-03-20 Ensure that collation sequences on non-PK columns of a WITHOUT ROWID table are used correctly when they are part of a row value comparison. Fix for forum post [forum:7a308e933d | 7a308e933d].
de4ef2dc7 2026-03-19 Ensure that sqlite3RCStr values returned by json_group_array() and json_group_object() are zero-terminated.
0cb7603d4 2026-03-19 Update fts5 scan costs to take into account that a prefix query combined with a rowid equality constraint is still quite expensive.
28cfb1e4a 2026-03-19 Restructure some internal subroutine signatures for improved performance of affinity type conversions.
915a55444 2026-03-19 Use compiler intrinsics to improve the performance of sqlite3Multiply160().
a2d80200b 2026-03-19 Reverse the if() condition added by this branch.
08eb5e9e5 2026-03-18 Continue enforcing the legacy declaration-before-statement C-language rule, since some downstream still uses it.
ac53ce155 2026-03-18 Minor optimization to error message generation in integrity_check.
5a6772eaa 2026-03-18 Comment improvements.  Ensure that tests in shellB.test that require virtual tables do not run when compiling without virtual table support.
acc213b42 2026-03-18 Improve the integrity-check error message when floating point index values are off by one or two ULPs.  Change the name of the eiib1.test test module to expridx1.test.
345bc9167 2026-03-18 Do not assume that a recursive CTE emits rows in ORDER BY order. Forum [forum:deb1eadf4d677bd5 | deb1eadf4d677bd5].
1539575e0 2026-03-18 Take care not to overread the record header when decoding the record in vdbeIsMatchingIndexKey().
f0648f692 2026-03-18 Pad the allocation in vdbeIsMatchingKey() a little to avoid undefined behaviour if the record is corrupt and getVarint32() reads past the end of it.
15a3b2d4e 2026-03-18 Adjust the fix at [f7389cdb129d3386] so that integrity_check output still appears prior to the SQLITE_CORRUPT return.
765ff2189 2026-03-18 Simplification to the logic that decides whether or not an index field matches when floating point values are close but not exact.
3ca448dee 2026-03-18 Fix harmless signed/unsigned compiler warnings.
3f2d7d4aa 2026-03-18 Fix some cases where integrity-check would fail to identify real values in indexed expressions that are with 2 ULPs of each other.
00989bcd9 2026-03-18 Fix harmless "unused variable" compiler warning.
362b9cecd 2026-03-17 Modify integrity-check so that it is only tolerant of very small distortions of real values in indexed expression fields.
f4e6483cd 2026-03-17 Improved error handling in OP_IFindKey and in vdbeIsMatchingIndexKey().
ae2820ab2 2026-03-17 When integrity-check finds a missing index entry, search a small range (currently 10) of entries around the missing key for an entry that matches all non-virtual and non-expression fields.
bdbad43f3 2026-03-17 Do not run index healing on an invalid cursor.
ccf2babd4 2026-03-17 Fix an assertion fault that could occur in RTree when given a corrupt database.
2953e950c 2026-03-17 Fix display of P4_INDEX values in EXPLAIN output.
8736da94b 2026-03-17 Fix compiler warning an inefficiency introduced by previous commit.
b302c4d39 2026-03-17 Typo fix in sqlite3Multiply128():  The datatype should be *unsigned*.
022f2f96b 2026-03-17 Change the sqlite3VdbeFindDeleteKey() routine so that all index fields that are not expressions or virtual columns must match the table for the delete to succeed.
5a7338651 2026-03-17 Fix a harmless compiler warning.
b50ce0859 2026-03-17 Include the float-point table generator utility in the tools directory.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
