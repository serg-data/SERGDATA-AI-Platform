# SQLite — Git tag version-3.43.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.43.0
Сравнение с предыдущим тегом: version-3.42.0

## Коммиты в диапазоне

```text
995f96f8e 2023-08-24 Version 3.43.0
e174dba73 2023-08-24 Change a variable name in fts5FlushOneHash() to avoid shadowing another.
af885d9fc 2023-08-23 Fix typo in the Lemon documentation.
a4709f27d 2023-08-23 More changes to documents for GitHub-style markdown.
2bab8774b 2023-08-23 Fix the Markdown in the compile-for-windows.md document so that it works on GitHub.  Improved header text in README.md.
44a430b33 2023-08-23 Minor adjustments to the wording about pull requests in the README.md file.
a2a4c3f14 2023-08-23 The pageOnDirtyList() assertion is too slow even for debugging builds, for some corner cases.  It makes the query appear to hang.  So make it an EXPENSIVE_ASSERT instead.
675342a5a 2023-08-22 Fix a harmless memory leak in the sqldiff utility.
44e24e964 2023-08-22 Add makefile target "sdevtest" - like "mdevtest" except asan and usan enabled for the non-debug test.
310700228 2023-08-22 Update version number in autoconf/tea/configure.ac.
216524f85 2023-08-22 Update autoconf/Makefile.msc (by running mkmsvcmin.tcl) to support the "ASAN=1" option.
da7662a4b 2023-08-21 Fix an undefined integer overflow in fts5.
ba481c375 2023-08-21 ifdef adjustments so that SQLITE_OMIT_WAL works with SQLITE_USE_SEH.
3404b452a 2023-08-21 Fix another UBSAN inaccuracy in fuzzcheck.
114ad2f86 2023-08-21 Address minor inaccuracies in fuzzcheck and RTREE found by UBSAN.
78ad745ab 2023-08-19 shell.c.in help text typo fix. No functional changes.
4d8eb16f0 2023-08-18 Rename the decimal_sci() function to decimal_exp(). [forum:/forumpost/fa027bb0ab|Forum post fa027bb0ab].
d5a9d522f 2023-08-18 Avoid running test case sort2.2.3 under address-sanitizer. It runs out of memory on some 32-bit platforms.
f0eabde9a 2023-08-18 Enhance the CLI and the fuzzcheck utility programs to report whether they are compiled as 32-bit or 64-bit for things like the --version option.
2cffc5be2 2023-08-18 Enhance the notes on compiling for Windows11 to explain how to do 32-bit builds on a 64-bit system.
2e0ce58d2 2023-08-17 Do not allow bound parameters in the ON CONFLICT clause of an UPSERT. dbsqlfuzz 9983e2c77634a8ccf33b5c91fa9982599de5f9e9
e15b35d5a 2023-08-17 Fix an error in documentation comments in fts5.h.
fab6882fd 2023-08-17 Add extra test to fts5synonym2.test.
699803e11 2023-08-17 Add "Windows-Sanitize" configuration to "testrunner.tcl release" tests on windows.
58c44132d 2023-08-17 Have all test names in json101.test start with "json101".
81ef0f8e8 2023-08-17 Enable address sanitizer in Makefile.msc by adding the ASAN=1 argument on the nmake command line.
36a9f5c24 2023-08-17 Fix a possible UAF in SEH if an exception occurs at an inopportune moment during WAL processing.
936f7deee 2023-08-16 Refinements to instructions on compiling for Windows.
7335f75da 2023-08-16 Improved instructions on how to build SQLite on Windows 11 and similar.
0d83c71b3 2023-08-16 Make sqlite3_stmt_explain() accessible to loadable extensions.
7309b50fb 2023-08-16 Mix the current process ID into the randomness used for generating temporary filenames on Windows.
af8980bdc 2023-08-16 Update testrunner.tcl to use environment variable %NUMBER_OF_PROCESSES% when running under tclsh on windows. Also modify the internal database schema used by testrunner.tcl to be compatible with old versions of SQLite.
fe1835526 2023-08-16 Fix test script problem preventing veryquick.test from running.
ff9ff5480 2023-08-15 Cherrypick [00ac653562a6] to remove stray JNI debug output. No functional changes.
c13167540 2023-08-15 Cherrypick [653ed92dc391] (went to wrong branch). Doc change only, no code changes.
f05630fb1 2023-08-15 Update testrunner.tcl to make it easier to add things like mdevtest.
baa574ef3 2023-08-15 Improve the portability of the src-verify.c tool on Windows.
8c5611a16 2023-08-15 Fix problems in fts5 test code.
b93760e1e 2023-08-15 Use a dodgy substitute if the INFINITY macro is not available. See [forum:/forumpost/8e66e19bb9|forumpost 8e66e19bb9].
00eee0791 2023-08-15 Fix the PRAGMA case_sensitive_like command so that the LIKE function continues to be innocuous after the PRAGMA. [forum:/forumpost/925dc9f67804c540|Forum post 925dc9f67804c540].
f0c1ea9e8 2023-08-15 Fix an off-by-one error causing a buffer overread in test2.c.
db9a708ee 2023-08-14 Fix the autoconf makefile for the CLI such that it disables double-quoted strings by default, as all other builds of the CLI do. [forum:/forumpost/9794b6aaa5|forum post 9794b6aaa5].
9541fbc28 2023-08-14 Fix a problem in sqlite3_snapshot_recover() introduced by the [8a6b0c24937e855b] merge.
1f72b5346 2023-08-14 Change the name of the ".binary" command in the CLI to ".crnl".  The sense of the setting is inverted.  The original ".binary" still works for backwards compatibility but is now undocumented.  ".crnl" is also undocumented on machines where it is a no-op (all machines other than Windows). [forum:/forumpost/8bd0b0fbdbc12477|forum thread 8bd0b0fbdbc12477]
592ae2823 2023-08-14 Fix harmless compiler warnings reported by MSVC.
07ef60350 2023-08-14 Enable SEH be default in Windows builds.
8a6888c19 2023-08-13 Remove SQLITE_DEBUG from JNI build.
54402964b 2023-08-12 Update wasm's push-testing rule to exclude files which were recently removed from the build.
d8a94dbb3 2023-08-12 Correct JNI .jar rules to only include *.java/class files, not *.* (*~ files).
46451fa8b 2023-08-12 Fix the mdevtest target so that it works with msvc.
890a9ede3 2023-08-12 Fix testrunner.tcl so that it restarts itself using [testfixture] if its current interpreter does not support [package require sqlite3].
7c036fabe 2023-08-12 Have the mdevtest target support the OPTS variable on unix.
a6f09a019 2023-08-12 Add "mdevtest" target to makefiles. Equivalent to running "devtest" on both debug and non-debug builds.
68522e162 2023-08-12 More JNI docs.
5b3a75436 2023-08-12 Further simplifications in the interface of the OutputPointer family of Java classes.
c216df75c 2023-08-12 Tweaks and docs for the OutputPointer family of Java classes.
613390680 2023-08-12 Bind sqlite3_db_status() to JNI.
238bea2ae 2023-08-12 Bind sqlite3_status(64)() to JNI.
6c6badd2e 2023-08-11 Modernize the sqlite3 shell man page a bit, per [forum:d9aa201dee553bb2|forum request].
48dcdd3b7 2023-08-11 Add timing info to SQLTester.
783f5b5aa 2023-08-11 Fix a makefile deps problem which caused ext/jni build to fail if sqlite3.c/h were not created beforehand.
16c8c9674 2023-08-11 Minor SQLTester test tweaks and have 'make tester' include the out-of-tree tests if they are found.
7009c43ea 2023-08-11 Bind sqlite3_sql() and sqlite3_expanded_sql() to JNI. Start marking C-side functions which would need explicit mutex support if we remove 'synchronized' from their Java entry points (but there are many more left to mark).
c3b7e1c4e 2023-08-11 Add a doc link for the new sqlite3_js_posix_create_file().
b949244ea 2023-08-11 Add sqlite3.capi.sqlite3_js_posix_create_file() and oo1.OpfsDb.importDb() as alternatives for the newly-deprecated sqlite3_js_vfs_create_file().
7e1315295 2023-08-11 Deprecate sqlite3_js_vfs_create_file() because, it was discovered today, its out-of-scope use of the sqlite3_vfs, sqlite3_file, and sqlite3_io_methods APIs triggers unresolvable assertions in the core when built with SQLITE_DEBUG.
b8a0fc52a 2023-08-11 Fix bug in the test case for the previous check-in.
91c009291 2023-08-11 Up until version 3.42.0, there was a bug in json_valid() such that it would return False (0) for a NULL input.  That bug is fixed in 3.42.0.  This check-in adds a compile-time option -DSQLITE_LEGACY_JSON_VALID that restores the old buggy behavior for applications that depend on it.
a0423e0fc 2023-08-10 Mark _all_ JNI binding funcs as synchronized so that Java can lock them and protect our global-state access. The alternative is writing a mountain of C-side code to do the same thing.
5c9f5e402 2023-08-10 Work around jdk8 and jdk19 mangling the C name of sqlite3_db_config() differently. Correct the variadic arg handling of the JNI-side subset of sqlite3_db_config() options.
0c08c8c20 2023-08-10 Add a working dist zip file for the JNI bits.
a52b8c884 2023-08-10 Initial pass at 'make dist' rules for the JNI bundle, but they still need a bare-bones, posix-make-compatible makefile to include in the bundle.
89e1caf29 2023-08-10 New testcase() macro in the tokenizer, to better document its behavior.
bb51af68f 2023-08-10 Move ext/wasm/version-info.c to tool/ for re-use in build other dist bundles.
a22a2d266 2023-08-10 Add SQLTester --keep-going flag to allow it to continue to the next script after an error.
92f699d38 2023-08-10 Document that auto-extensions registered via JNI will fail if they open a db (to avoid triggering an endless loop in the auto-extensions). Discover the hard way that JDKv19 creates different mangled JNI names for some functions than JDKv8. Start reformatting much of the JNI API decls in prep for making them even longer.
152801470 2023-08-10 Resolve two assertions in the auto-extension JNI which were triggered via new SQLTester infrastructure. Move SQLTester's db-init SQL injection into an auto-extension.
61186d124 2023-08-10 Make test completion status more visible at a glance on modern terminals.
e51fae413 2023-08-10 Disable REQUIRED_PROPERTIES handling in SQLTester, per /chat. Scripts with that directive are now skipped.
0a8cc1f63 2023-08-10 Add a visual indicator (emoji) to TestScript verbose messages, dependent on the message's level of verbosity.
34fac7436 2023-08-10 Add the current --testcase name to SQLTester --verbose output.
ec8298fbd 2023-08-10 More SQLTester docs. Add --verbosity command to help zoom in on script areas while debugging. Spice up test-start/end output with some emoji.
63fb588d3 2023-08-10 Give DbException the option of closing the db to simplify error handling in one case.
6a61a19f9 2023-08-10 Initial version of REQUIRED_PROPERTIES support for SQLTester, with TEMPSTORE_(FILE/MEM) and RECURSIVE_TRIGGERS options.
f703dfa38 2023-08-10 Generic cleanups and fixes in SQLTester.
eda67031d 2023-08-10 Change the SQLite3Jni API annotations to use SOURCE retention (used only at compile-time).
0c6df29cb 2023-08-10 Move all of the SQLTester code into a single file, since it's only got 1 public class. Remove 'public' from many methods which don't need it. Add more documentation to it.
2a9106514 2023-08-10 Defer static JNI-side init of SQLTester until main() is called so that its auto-extensions do not leak over to clients of the main library.
50a17a1b3 2023-08-10 Treat all args to --glob as a single glob.
3a0e45d0a 2023-08-10 Remove --print's ability to read ahead.
84c1a7b49 2023-08-10 Replace the SQLTester infrastructure with a line-oriented, non-regex-heavy parser. Add --column-names command.
e35a703b7 2023-08-09 Port the SQLTester 'v1' commands to the 'v2' evaluation bits. Still TODO is swapping out v1 with these separate impls.
35af4c5ff 2023-08-09 Correct REQUIRED_PROPERTIES handling to not fail if there are no properties.
bef0369ff 2023-08-09 More for the SQLTester rework. Can read input and dispatch commands, but only --print is currently implemented.
e41c09ac8 2023-08-09 Initial sketches of a line-by-line parser for SQLTester to overcome its compatibility shortcomings. Far from complete.
e0fb44090 2023-08-09 Adapt TestScript to skip REQUIRED_PROPERTIES, per [7a07863e082664da], and improve a couple of adject reasons-for-skipping messages.
7f66a3eeb 2023-08-09 Add an extra constraint to the test-script-interpreter.md spec.
16e620e07 2023-08-09 SQLTester --result command: do not double-{}-wrap error messages and do not throw on db error.
5d2a61834 2023-08-09 Move the test command body's trim() back into the TestScript class (to simplify Command-level code) but do it after double-verbose has had the chance to emit it as-is (so that debug output is not mangled by the trim).
583fc5b96 2023-08-09 Tweak the SQLTester --verbose and double-verbose output a bit for legibility.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
