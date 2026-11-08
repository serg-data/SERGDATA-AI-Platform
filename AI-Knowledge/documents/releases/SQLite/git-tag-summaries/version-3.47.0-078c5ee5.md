# SQLite — Git tag version-3.47.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.47.0
Сравнение с предыдущим тегом: version-3.46.0

## Коммиты в диапазоне

```text
f5fb820c0 2024-10-21 Version 3.47.0
e2f294a1e 2024-10-21 Add a case to testrunner.tcl so that mdevtest can run on openbsd.
32d255851 2024-10-21 Avoid using LIKE in sqlite3expert.c, in case "PRAGMA case_sensitive_like" has been used or the "like" UDF replaced by something unexpected.
b74c7880d 2024-10-20 Fix another problem with ".expert" and virtual tables. [forum:/forumpost/49d6a19ec|Forum post 49d6a19ec].
72c5b9bf0 2024-10-19 Add sqlite3_rsync to the docs at the top of mktoolzip.tcl. No code changes.
885fad890 2024-10-19 Add missing $(TEXE) suffixes in the tool-zip makefile target.
4da761773 2024-10-19 Move the #include of hwtime.h from the bottom of util.c to the top of vdbe.c so that it will be available when needed, even for non-amalgamation builds.
624cb96f5 2024-10-19 An assortment of comment typo fixes discovered by aspell. Add several new words to tool/custom.txt. No code changes.
afb88c529 2024-10-19 Remove unnecessary VACUUMs from the previous check-in to sqlite3_rsync.
78b6c17fa 2024-10-19 Fix the sqlite3_rsync utility so that it is able to synchronize a database using a UTF16 text encoding. [forum:/forumpost/e055d50821|Forum post e055d50821].
a525d635a 2024-10-18 Minor doc cleanups in SQLTester.mjs and confirm that the tests pass with both OPFS VFSes.
23caead6c 2024-10-18 Fix three bugs in SQLTester.mjs which caused --tableresult tests, escaping of SQL values to incorrectly fail, and the --column-names setting to not be reset between tests.
b94228a11 2024-10-18 Fix a var reference typo in SQLTester.mjs.
d11a3fd91 2024-10-18 Remove the unused dbfuzz2-asan/msan makefile targets. Fix a comment typo in a makefile.
90675da34 2024-10-18 Remove a not-strictly-necessary 'undefine' invocation from ext/wasm/GNUmakefile, as it is not compatible with too-old versions of gmake. Resolves the problem reported in [forum:e57932e3ccdc2c9c | forum post e57932e3ccdc2c9c].
f9a02e166 2024-10-18 Minor enhancements to the compile-for-windows.md document.
d8712c6c2 2024-10-18 Fix typo in the README.txt for the amalgamation autoconf tarball.
c2e400af0 2024-10-18 New assert() statements to validate OP_OpenEphemeral logic.
dd719bebf 2024-10-17 Fix obsolete M4 macro in the configure script for the TEA extension within the autoconf tarball.
fe15ed434 2024-10-17 Fixes from code inspection: (1) Extra paranoid defense against integer overflow. (2) Remove a stray blank line in an FTS5 comment.
a9e4ebc51 2024-10-17 Fix a typo in compile-for-unix.md.  Simplify hyperlinks in the compile-for-* documents.
bcdb28b8f 2024-10-17 Improved README.txt file in the amalgamation-autoconf tarball.
4f5eba199 2024-10-17 Attempt to get the TEA builder in the amalgamation-autoconf tarball working using hints from Jan Nijtmans.
cab957466 2024-10-17 Ensure that the OPFS VFS's xOpen() writes back the read-only flag to the output flags. Resolves the problem reported in [forum:cf37d5ff1182c31081 | forum post cf37d5ff1182c31081].
6031de92c 2024-10-17 When calling OpfsSAHPoolUtil.removeVfs(), ensure that the cached result the VFS init is also removed so that the VFS may later be registered again with the same name. Set up test code for the regression reported in [forum:cf37d5ff11 | forum post cf37d5ff11] (which uncovered the removeVfs() shortcoming) but that test is currently only known to fail with the "opfs" VFS and is not currently set up to fail.
88282af52 2024-10-16 Add has_tclconfig to the tidy makefile target.
f578ce102 2024-10-16 Change the name of the new utility program from sqlite3-rsync to sqlite3_rsync - dash changed to underscore - for consistency with the preexisting sqlite3_analyzer.
9c5fb63d3 2024-10-16 In the unix Makefile, strip compiled binaries prior to adding them to the tool ZIP archive.
87cb97b0e 2024-10-15 Fix harmless compiler warning in flockCheckReservedLock().
45b4dca60 2024-10-15 Fix the "tool-zip" makefile target so that it includes sqlite3-rsync.
1b59f37c0 2024-10-15 Fix a typo in a comment used to generate document.  No code changes.
dcaae8fd4 2024-10-15 Cross-reference the sqlite3_backup_init() function to the documentation for VACUUM INTO and sqlite3-rsync.  Comment changes only.  No changes to code.
4924847cb 2024-10-14 Avoid the possibility of buffer overrun in the READ_UTF8 macro by using an less-than operator rather than not-equal-to.
5899d9c08 2024-10-14 There is no need to DELETE the content of sqlite_sequence in the output of the CLI ".dump" command because that table will initially be empty if it exists at all.  [forum:/forumpost/2e31f49d00472cec|Forum post 2e31f49d004]
39b924956 2024-10-14 The CLI now default to ".crlf ON" in Windows.  CSV output always uses CRLF on all platforms.
863fcdc11 2024-10-14 Be consistent about using "CRLF" instead of "CRNL".
72fea1180 2024-10-14 Fix a harmless compiler warning in the CLI.
629e1bfa6 2024-10-12 Ensure that test file ext/expert/expert1.test works with non-fts5 builds.
d5a780fdd 2024-10-12 Allow the ".expert" command to analyze statements that use built-in virtual tables.
589ce93e9 2024-10-11 Additional clarification in the comments to sqlite3_stdio.c.  No changes to code.
4859bc9a9 2024-10-11 Update comments in ext/misc/sqlite3_stdio.c to reflect the latest enhancements. No changes to code.
4dfc4dc2d 2024-10-11 Add the doc/compile-for-unix.md document.
ea7ea76a5 2024-10-11 Avoid a segfault when calling src-verify without any arguments.
c85c102ef 2024-10-11 Add two missing $(BEXE) suffixes, as reported in [forum:9ad28680d394afda | forum post 9ad28680d3]. Problem introduced by [1218a203483cecdc] being incomplete in where it added that suffix.
2623a19ab 2024-10-11 Improved instructions in the TEA readme for building the TCL extension.
b8d18f321 2024-10-11 Update the README for the TEA extension in the amalgamation tarball.
472353963 2024-10-11 Avoid running some new tests in lock5.test with the inmemory_journal permutation.
ed3cf6ef3 2024-10-11 Update the autoconf Makefile.msc
17408fbbd 2024-10-11 An improved method for statically linking sqlite3_analyzer.exe using Tcl9. Enable wildcard expansion of arguments to testfiture on Windows.
b23cce9a1 2024-10-11 Fix the CSV output mode in the CLI such that the line ending is NL by default but goes to CRLF if ".crnl on" is set.  Make the .crnl command available on non-Windows builds.  Update the .crnl command such that if it has no arguments it shows the current setting.
0b453b3b3 2024-10-11 Avoid undesirable NL to CRLF translation when doing binary output to the Windows console.
7b179a309 2024-10-10 For compatibility, allow the TCL interfact to continue working with TCL 8.5.
f553588c7 2024-10-10 Adjustments to the Makefile.msc to get static builds of sqlite3_analyzer.exe working with TCL9.  Update the compile-for-windows.md document for TCL9.
50ec92f7c 2024-10-09 Improvements to Makefile.msc: (1) Attempt to find sane values for key variables based on the value of TCLDIR.  (2) Default to TCLVERSION 90 instead of 86.  (3) Add the "tcl-env" target that shows the values of key variables associated with TCL.
94fe1ad1c 2024-10-09 Add quotes around $(CC) in tclextension-related targets so that a CC of "ccache cc" works.
da1bf77cc 2024-10-09 Fix a problem in the generate_series() extension introduced by [d50b784807333c54].
48dd75df7 2024-10-09 Fix the xCheckReservedLock() method of the flock VFS to avoid dropping the file-lock.
492925a8f 2024-10-09 Change the makefile to prefer the use of tclsh9.0 if it is available.
97b061060 2024-10-09 Make it so that the TCL extension installed using "make install" has the same name as the one installed by "make tclextension-install".
50bb0aaa2 2024-10-09 Changes to the TCL extension and how it is built, suggested by Jan Nijtmans.
4b0a2e010 2024-10-09 Improved handling of unicode characters in the LIKE optimization. Follow-up to [bce52ce2a6e7f3d3].
48d11044b 2024-10-09 Add a few missing $(BEXE) suffixes on makefile targets which are apparently never run on platforms where that var is non-empty.
7f5a10e4b 2024-10-08 Enable the ".crnl" command on Windows builds of the CLI even if the SQLITE_U8TEXT_ONLY or SQLITE_U8TEST_STDIO compile-time options are used.
ab85d9abd 2024-10-08 Additional improvements to the behavior of ".crnl" in the CLI.  The default output mode is O_BINARY so that results are identical on Windows and non-Windows systems.  On Windows you can optionally do ".crnl on" to enable NL-to-CRLF conversion on output.  Output to Windows console is always O_U8TEXT and so is unaffected by the .crnl setting.
dd2deecbb 2024-10-08 Fix the .crnl command in the shell so that it does not get undone by calls to print a quoted string or CSV output.
7998b889e 2024-10-08 Add an ALWAYS() on a branch in the new indexed-subtype logic.
ddc764b27 2024-10-07 Add a NEVER() to an unreachable branch in the new indexed-subtype logic. Mark the pi() function as deterministic.
f7f78a624 2024-10-07 The (undocumented) subtype() SQL function should have the SQLITE_SUBTYPE flag.
ce527f2e9 2024-10-07 Fix handling of U+fffd in the LIKE optimization. dbsqlfuzz eee57fb9eea1dfa5aa40dfa87865cf8c84d12f96.
29f976432 2024-10-07 Fix an assert() failure in "PRAGMA integrity_check" that could occur when checking a corrupt database.
fba24d352 2024-10-06 Origin should not send content for the lock-byte page to the replica, in sqlite3-rsync. [forum:/forumpost/d14b55e5fa19c25f|Forum post d14b55e5fa19c25f].
74672acd9 2024-10-06 New SQL function for testing/debugging use only: parseuri().
2c72c55dc 2024-10-05 Back out [2f7eab381e16] because the stderr output on systems without gmake causes grief in the testing tools.
d564bdb05 2024-10-05 Allow expressions with subtypes to be read from indexes unless they are being used as direct or indirect parameters to SQLITE_SUBTYPE functions.
c857b9eb5 2024-10-05 Experimental change to allow expressions with subtypes to be read from indexes in situations where they are not used as function parameters.
706fdeebb 2024-10-05 Add ext/wasm to the top-level clean/distclean rules in such a way that any error due to a lack of gmake are ignored.
c8c95f514 2024-10-04 Fix typo in documentation for SQLITE_SUBTYPE. No code changes.
51bbf0c7b 2024-10-03 Unconditionally include &lt;ctype.h&gt; in sqliteInt.h, even in builds where it is not needed.
1e2834dd4 2024-10-03 Fix to the previous:  The dbpageRollbackTo() method should return SQLITE_OK.
c51dccbd8 2024-10-03 Fix missing return value from the new dbpageRollbackTo() callback.
46a62afba 2024-10-02 Modify the behavior of sqlite_dbpage so that the null-INSERT that truncates a database must be the very last INSERT operation within a transaction in order to be effective.  This simplifies the code and also makes the behavior easier to document and understand.
44b8c3701 2024-10-02 Fix a typo in fts5delete.test.
3b3f230d9 2024-10-02 Adjust the new truncation behavior of sqlite_dbpage(N,null) such that it causes the database to be truncated to N-1 pages.  This makes more since.  An error is raised if N is less than 2.
010f9f870 2024-10-02 Remove a few more traces of long double from the code.
f9d1141a3 2024-10-02 Update docs for sqlite3_snapshot_get().
e8b2c9224 2024-10-01 Remove all code that makes use of the C-language "long double" datatype.
715101091 2024-10-01 New #ifdefs to omit code that is unused when SQLITE_USE_LONG DOUBLE is defined.
1f2faa647 2024-10-01 Another comment about the LONGDOUBLE wasm topic. No code changes.
c9c1b6569 2024-10-01 Use the new SQLITE_USE_LONG_DOUBLE to disable long-double support in WASM builds, as they cannot be represented in JS and this saves approximately 5.5kb in the resulting wasm file.
dac22f656 2024-10-01 Add compile-time option -DSQLITE_USE_LONG_DOUBLE=0 to omit all attempts to use "long double".  Or =1 to omit attempts to use the Dekker algorithms to achieve high-resolution floating point.
ed94e0e67 2024-10-01 Add an #if'd-out block to sqlite3-wasm.c mentioning the LONGDOUBLE_TYPE, as brought up in [forum:cbfb0d0ac0a4e349 | forum post cbfb0d0ac]. No functional changes.
cacef2308 2024-09-30 Fix the character width tables for the CLI such that all unicode code-points less than 0x300 have a width of 1.  This is in fact the case for Mac, Ubuntu, and Windows.
d5838eaa4 2024-09-30 In fts5, avoid starting a new merge of level L if there exists already an ongoing merge of a level less than L.
54fd01c4a 2024-09-28 Fix the CLI so that the --bom option only outputs a single BOM, not two.
33669ef28 2024-09-28 Add another missing mkdir to the wasm build process.
54e35b543 2024-09-28 Add tests for DELETE on contentless, contentless-delete and contentless-unindexed fts5 tables.
5ec9ed7fe 2024-09-28 Complete a line of documentation which was interrupted mid-sentence.
6a8336987 2024-09-28 wasm: move the makefile-eval-generated fiddle rules into mkwasmbuilds.c. Squelch some warnings from grep when running 'make clean' on a clean tree.
d4c735d49 2024-09-28 Ensure that the temporary build dir is mkdir'd by wasm deps which depend on it.
51fb37db6 2024-09-28 For wasm builds: automatically use higher optimization (but slower build) levels when a target related to deliverables (as opposed to dev mode) is explicitly invoked.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
