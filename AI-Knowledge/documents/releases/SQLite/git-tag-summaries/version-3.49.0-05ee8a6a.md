# SQLite — Git tag version-3.49.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.49.0
Сравнение с предыдущим тегом: version-3.48.0

## Коммиты в диапазоне

```text
659bafd05 2025-02-06 Version 3.49.0
31c3599ed 2025-02-05 Fix a harmless unused-parameter compiler warning introduced by [75f3d8744879].
6c074e5dc 2025-02-05 Summarize known incompatibilities/gotches between JimTCL and canonical TCL, and their workarounds. Doc changes only.
97af1346f 2025-02-05 Upstream JimTCL patch and minor tcl script tweaks to support (fconfigure -translation binary) for better cross-platform build portability.
b6859b6f2 2025-02-05 Attempted improvements to the SQLITE_DBCONFIG_... documentation.
802b042f6 2025-02-04 Detect and report signed integer overflow in the sumInverse() routine, used by window functions.
51dd67080 2025-02-03 Fix a potential UAF in FTS3.
31615637f 2025-02-03 New dbsqlfuzz case added to fuzzdata8.db.
0d9f2a15f 2025-02-03 The Parse.addrExplain field is never even if SQLITE_OMIT_EXPLAIN is defined.
589796cd8 2025-02-03 Fixes and improved documentation to the new --sqlid and --dbid range options in fuzzcheck.
dbe48d3c8 2025-02-03 Enhance fuzzcheck so that the --sqlid and --dbid options can specify a range of tests to be run.
6e5802fc7 2025-02-03 Improve the JS-side sqlite3_set_auxdata() test to also trigger the case that the aux data actually gets reused. Test changes only, no library code.
9e639d249 2025-02-03 Fix a use-after-free case in fts5 provoked by fuzzdata8.db. Tcl test case pending.
c6281e489 2025-02-03 New test case for test/fuzzdata8.db
3cd34ab98 2025-02-03 Rework [76c8435a] to eliminate automatic JS-to-WASM function conversions of sqlite3_set_auxdata() destructors because it can leads to leaks on every call of a UDF. This feature never worked before [76c8435a] but fixing it was ill-conceived because of the memory leakage it introduces. WASM function pointers can still be used as destructors in this context.
d98689f4d 2025-02-03 Add a more complete test for [76c8435a] and add some commentary about (A) the inability to automatically clean up automatically-generated WASM proxy functions for sqlite3_set_auxdata() destructors and (B) how to deal with (A) to avoid leaking WASM proxy functions.
77586831e 2025-02-03 Bring the autoconf-tarball Makefile.msc into alignment with the main Makefile.msc.
d256b5688 2025-02-03 Correct the FuncPtrAdapter signature for the JS binding of sqlite3_set_auxdata(). Reported in [https://github.com/sqlite/sqlite-wasm/issues/92|the npm subproject, ticket #92].
3cf467a3e 2025-02-03 Adjust the build process to avoid extra CR characters inserted by jimsh on Windows.
4170780a8 2025-02-03 The "clean" target on Makefile.msc should not delete the auto.def file.
f306ca528 2025-02-02 Add a header comment to test/speedtest1.c that outlines how to compile the program using historical amalgamation sources, for comparison testing.
c229f1181 2025-02-02 Update to the "--help" output from speedtest1.
14613b1b1 2025-02-02 URL typo fix in code comments. No code changes.
c49bfdbbe 2025-02-01 Add a missing "db2 close" to the ext/session/session_gen.test test module.
4b99ec0b8 2025-02-01 Fix a comment typo - in a comment used to generate documentation.
454a426e3 2025-02-01 Remove an ALWAYS() added by [2567298f4b0fdfeb] because dbsqlfuzz found a way to reach it.  The test case was added to TH3.
5c72a39cf 2025-02-01 Enable SQLITE_ENABLE_NORMALIZE for several test configurations.
de50617bc 2025-02-01 Fix an issue with sqlite3_normalized_sql() caused by changes needed to support SQLITE_DBCONFIG_ENABLE_COMMENT.
fdc17e0bc 2025-02-01 JS doc typo fixes. No functional changes.
276d213b2 2025-01-31 Tweaks to [4b4f33d791fe4318] to make it easier to test.
45b2669ad 2025-01-31 Fix test case numbering in tests recently added to like3.test.
82f3052e6 2025-01-31 Expose the new SQLITE_DBCONFIG_ENABLE_ATTACH_CREATE/WRITE and SQLITE_DBCONFIG_ENABLE_COMMENTS (from [325e547a21955]) to JS/WASM.
8fbf400bb 2025-01-31 Remove an assert() that is not true if a trace-callback is deregistered while there are active statements.
f6ca35d88 2025-01-31 Fix a problem with LIKE and GLOB processing in utf-16be databases in cases where the utf-8 encoding of a character ends with the byte 0xBF.
a03379030 2025-01-31 If any errors occur while processing sqlite_dbpage changes, cancel pending truncate operations.
efbf48154 2025-01-31 Minor wasm-specific doc touchups.
824a5bfcf 2025-01-31 Improvements to the SQLITE_DBCONFIG option documentation.
80cf9fa00 2025-01-31 Correct a typo in tool/emcc.sh.in which could cause all of the configure-time work to locate the emcc binary to go unused. Reported in [forum:feb325cdde5b6f37|forum post feb325cdde5b6f37].
e16b34524 2025-01-31 Add the SQLITE_DBCONFIG_ENABLE_COMMENTS setting (default on) to enable or disable the ability to include comments in SQL input text.
49906e8e4 2025-01-30 The reuse-subroutine optimization [c9a3498113074bbc] might have generated byte-code that loops forever.  This check-in fixes the problem.
8bffd498e 2025-01-30 Remove an unused parameter from an internal-use subroutine in the TCL interface.
000e39e9a 2025-01-30 Improvements to the TCL interface for Tcl9 as suggested by Jan Nijtmans.
8dacf7104 2025-01-30 Updates to the compile-for-windows.md document.
73dcf45a3 2025-01-30 Minor code de-duplication across the top-level auto.def and autoconf/auto.def.
1392ff553 2025-01-30 Disable a test case that (intentionally) does use-after-free, as it does occasionally cause problems even for non-sanitizer builds.
00d6b7abf 2025-01-30 Fix build regression, introduced in [d2fe6b05f38d9d] (3.48.0), in which SQLITE_OMIT and SQLITE_ENABLE flags passed to configure via CFLAGS were not propagated to the OPT_FEATURE_FLAGS list. Reported in [forum:9801e54665afd728|forum post 9801e54665afd728].
4f8f1965f 2025-01-29 Fix bug in sessions handling of FK constraints introduced by [e09a0c02] (released in 3.48.0). Bug was preventing a changeset containing FK violations from being applied even when the xConflict(CHANGESET_FOREIGN_KEY) returned OMIT.
36279c256 2025-01-28 Enhance the if() and iif() SQL functions so that they support any number of arguments greater than or equal to two. Suggested by [forum:/forumpost/40f7867f75f80|forum post 40f7867f75f80].
9dcf3d08c 2025-01-28 Fix sessions module handling of tables with generated columns.
0424f255e 2025-01-28 Fix a copy/paste typo in the output of vfstrace for xDlClose().
8b62a82ae 2025-01-28 Simplifh the IdList object to remove unnecessary fields.  Performance increases by about 0.8%.
b0c8b0887 2025-01-28 Fix typo in speedtest.md.
50637ca5c 2025-01-28 Apparently I got the logic of [abfe488ed67e2e35] confused, even backwards. Change it so that the SQLITE_USE_W32_FOR_CONSOLE_IO macro causes Win32 APIs to be used for console I/O and for stdio to be used otherwise.  This is reported to be necessary for builds that use a C-language runtime other than the one provided by Microsoft.  This changes if for Windows only.  It is a bug fix, though we don't have a test case that will demonstrate a malfunction.
d8c37bbc5 2025-01-28 Remove an ALWAYS() in the star-query heuristic that is sometimes false if you have a corrupt database.  dbsqlfuzz c37ba7728d79859b79c8341b59297e88fba017d3. Test case in TH3.
44980e816 2025-01-27 Use hashing to accelerate column matching on INSERT statements.  Code is smaller and about 1.8% faster overall according to test/speedtest.tcl.
5dcf5890a 2025-01-27 Enhance ./configure to issue an unambiguious error if the pathname to either the source tree or the build directory contains any space characters.
7c727bb61 2025-01-27 Avoid splitting a hyperlink across lines in the documentation comment for sqlite3_serialize().
e097db721 2025-01-26 Make two private routines in FTS "static" so that they are not callable from outside of SQLite itself.
2228567ad 2025-01-26 Further comment improvements in the star-query heuristic.  Add an ALWAYS() on an unreachable branch to achieve MC/DC.
fe54b7a1f 2025-01-26 Small size and complexity reduction on the star-query heuristic.  Improved comments for the star-query heuristic.
fb9e8e48f 2025-01-25 Revise the strategy used by the star-query heuristic:  Instead of decreasing the cost of all fact-table WhereLoops, increase the run-cost of WhereLoops that are SCANs of dimension tables.
0186ee1cd 2025-01-25 Improvments to debug output on the star-query heuristic.
dea434ea6 2025-01-25 Avoid calling computeMxChoice() after an OOM as some assert()s can fail in that routine if a prior OOM occurred while building the WhereLoop array.
bc7e41c03 2025-01-24 Remove an incorrect ALWAYS() added in check-in [7cfbe14d199bb631].
77731d5ec 2025-01-24 Clarify handling of a NULL for the 2nd argument to sqlite3_serialize(), as pointed out in [forum:3df7168b90|forum post 3df7168b90].
d37412b80 2025-01-24 The debugging output for WhereLoop objects now shows cost estimate changes due to the star-query heuristic.
f1c583031 2025-01-24 Minor tweaks to the star-query detection and processing.
7ae051df2 2025-01-24 Correct a version number in autosetup/README.md.
299fe0239 2025-01-24 When looking for star-queries, do not count a table as a dimension table if that table is separated from the fact table by an OUTER or CROSS join or if the table is a self-join.
7a16413a8 2025-01-24 Update autosetup/README.md to reflect recent refactoring.
8bfb18672 2025-01-24 Replace a handful of hard tabs in string literals with \t in mkwasmbuilds.c.
4331e6bd1 2025-01-24 Minor additions to ext/wasm/README.md.
dfb5f3275 2025-01-24 Update ext/wasm/README.md to reflect simplifications permitted by the current configure script behavior.
c70631623 2025-01-24 Remove extraneous are-we-making-clean guards from the generated wasm build rules, as that guard is set at a higher level. Rename a makefile call()able for consistency.
07a2e5d1e 2025-01-23 wasm: de-list demo-worker1-promiser-esm.html from the test pages because (per Chrome 131) "Module scripts don't support importScripts()", where "don't" means "they used to but no longer do".
1519675a1 2025-01-23 Fix a possible infinity loop in debugging-printf logic in the query planner. No changes to production code.
02e81f72a 2025-01-23 When running wasm-opt, ignore any failure because it will fail for unknown flags and the set of legal flags will change from version to version.  Document the size-reduction effect (or non-effect) of a dozen-odd wasm-opt flags and retain those which demonstrate a wasm file size reduction in -Oz builds (our production build mode). Total size savings: roughly 13kb.
726a047a4 2025-01-23 Remove some now-dead makefile code, rename a var for consistency, and fix a recipe bug introduced in the previous checkin in the bundler-friendly build.
efafde5eb 2025-01-23 Initial support for post-processing wasm files with wasm-opt (if it's available). This currently shaves 12kb off of the release-mode build of sqlite3.wasm but there are many dozens of wasm-opt flags left to try.
72543206e 2025-01-23 Move small parts of ext/wasm/GNUmakefile into ext/wasm/config.make.in and have the configure script populate that, rather than dynamically determining those values on each 'make' invocation. Add a configure-time check for the optional wasm-opt binary in prep for pending experimentation with using it to reduce the wasm file sizes.
c9bf7ed9a 2025-01-23 Remove unnecessary --minify 0 emcc flag from the wasm build, as -g3 implies that capability along with other anti-minification features we rely on.
83baa239e 2025-01-23 Do not strip binaries during 'make install', for consistency with the legacy build and per request from package maintainers.
c850c2be7 2025-01-22 Add two new sqlite3_db_config() options that enable the ATTACH command to create new database files and to open databases read/write.  Both default to on for backwards compatibility.
9489aefb8 2025-01-22 Add the -q/--quiet option to test/speedtest.tcl.  Automatically enable -DSQLITE_OMIT_LOAD_EXTENSION and -DSQLITE_THREADSAFE=0 so that no extra libraries are required.
255548562 2025-01-21 Fix date/time computations to deal with the sub-millisecond rounding problem identified in [forum:/forumpost/766a2c9231|forum post 766a2c9231].
8e7a16895 2025-01-21 Performance improvements to the (debug-use only) Mem.pScopyFrom logic, resulting in about 8x faster performance under -DSQLITE_DEBUG for the query in from [forum:/forumpost/0025389d0860af82|forum post 0025389d0860af82].  This change only affects builds that use -DSQLITE_DEBUG.
a6b62a26d 2025-01-21 Explain the lack of docs in autoconf/Makefile.in and refer interested readers to main.mk in canonical tree. Minor cleanups and fixes in tool/mkautoconfamal.sh.
2e899ccaf 2025-01-21 The FuncDev.nArg field values -3 and -4 now have special meansing of 1 or more or 2 or more arguments, respectively.  This saves space in the built-in function table, resulting in slightly faster performance and a reduced binary size.
631900291 2025-01-21 Remove now-extraneous autoconf/INSTALL and autoconf/configure.ac and update autoconf/README.* to account for the port to autosetup.
b80d01a18 2025-01-21 Have fts5 better handle OOM errors from sqlite3_blob_close().
d0db5edf6 2025-01-21 Use Tcl_GetString() instead of Tcl_GetCharLength() to test for a zero-length string in the TCL interface, since that is much more efficient.
985b4bc15 2025-01-20 configure script: work around msys's inability to 'exec' a '.sh' file by prefixing the call with an explicit 'sh', as reported in [forum:befb352a42a7cd6d|forum post befb352a42a7cd6d].
ae24e13bc 2025-01-20 Add 'dist' and missing 'install' pieces to the autoconf bundle.
c69d537b9 2025-01-20 Remove an assert() in the unix file locking logic that is not true if alternative VFS "unix-excl" is used for a read-only connection.
467e20ad1 2025-01-20 Fix an assert() that could fail if a virtual table called sqlite3_step() from within the xSync() method while committing a "PRAGMA defer_foreign_keys=1" transaction.
e9763e4ed 2025-01-20 configure script: remove an overzealous is-a-file check in the tclsh search which fails to account for implicit .exe extensions on Windows builds. Reported in [forum:c27403ef974df9f1|forum post c27403ef974df9f1]. (Same change as [89306d1a4905] but to a different file, as that content was moved since the 3.48 release.)
87cdd5926 2025-01-19 Get libsqlite3.so and .a building in the autoconf bundle.
17dca772e 2025-01-19 Get the CLI shell building in the autoconf bundle.
364078545 2025-01-19 Add an SQLITE_TESTCTRL_OPTIMIZATION mask that can disable the query planner heuristics that are designed to help with star queries.
2534bf401 2025-01-19 Initial work towards converting the autoconf bundle to autosetup. Currently non-functional.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
