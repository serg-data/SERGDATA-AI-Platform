# SQLite — Git tag version-3.50.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.50.0
Сравнение с предыдущим тегом: version-3.49.0

## Коммиты в диапазоне

```text
3f5236135 2025-05-29 Version 3.50.0
b3bcf489a 2025-05-28 Do not use a partial index if the truth of the WHERE clause does not depend on at least one column from the table being indexed.
f08f71a21 2025-05-26 Slight change to tool/split-sqlite3c.tcl to make it compatible with jimsh
f96d44e5d 2025-05-26 Fix a bug in the speedtest.tcl testing script that was introduced by [7e9845433ff26bdc]
209894c2f 2025-05-26 In the TEA build, enable USE_TCL_STUBS on Mac platforms.
93394ebc2 2025-05-26 On OpenBSD, do not test fuzzcheck with ubsan as part of "make devtest".
8f06aed1d 2025-05-26 Avoid calls to sprintf() in Lemon, since OpenBSD hates sprintf().
3f0104895 2025-05-26 When detecting TCLLIBDIR, skip over //zipfs paths, as the (file isdirectory) command will actually return true for those, but they're useless for installation purposes. This resolves the tea build's inability to install on stock openbsd.
45fa2347f 2025-05-26 tclsqlite.c doc typo fix.
a01b7adb1 2025-05-24 Change json_group_object() so that it ignores entries where the label is NULL.  [forum:/forumpost/e5bd251fb5|Forum post e5bd251fb5].
c5031b578 2025-05-24 vtablog.c doc fixes reported in [forum:416d1e37b2|forum post 416d1e37b2].
81a2f7ba8 2025-05-24 Amend the previous:  Set SQLITE_JSON_MAX_DEPTH to 500 on *all* builds of fuzzcheck.
85f37eba1 2025-05-23 Limit JSON recursion depth to 500 when running ASAN in fuzzcheck, to prevent stack overflow on ARM64.
c1ea1a6d4 2025-05-23 Add the --osmalloc option to the test/speedtest.tcl testing script. Adjust ./configure so that it does not check for malloc_usable_size().
96e16194b 2025-05-22 Fix a problem with using streaming iterators with sqlite3changegroup_add_change().
4a0b7a332 2025-05-19 Clarify some malloc size computations to simplify the proof that they are safe.  Remove some code associated with cygwin that is marked "#if 0".
79c792d5d 2025-05-19 Make the new sqlite3_setlk_timeout() interface accessible to loadable extensions.
890de76cf 2025-05-19 Remove stray tab characters from source files.
a58208a21 2025-05-19 Fix a harmless comment typo
acf95a321 2025-05-19 Adjust the tool/warnings.sh script so that it works on the latest versions of clang on Mac.
c953cb6b3 2025-05-17 Minor tcl doc update.
9bb2548e3 2025-05-17 Rename feature-tests.tcl to feature.tcl. Haiku tcl portability fixes.
1e24694b5 2025-05-17 Latest upstream teaish pieces for minor fixes. Restructure this copy of teaish to simplify maintenance and the autoconf bundle build.
972a0f5e8 2025-05-16 Improved version of the previous check-in.
cd6439230 2025-05-16 Fix the optimization of check-in [663f5dd32d9db832] that strives to avoid duplicate compuations in the GROUP BY clause so that it works even if the GROUP BY term is a subquery on the RHS of a LEFT JOIN.  Problem found by dbsqlfuzz.  Test cases in TH3.
cecf83332 2025-05-15 Add the --enablefk option to the "changeset apply" command of the changeset program.
c63801728 2025-05-15 Enhance the "changeset" utility program with new command-line options for the "changeset apply" command.
4165fd8a8 2025-05-15 Rework the showHelp() function in the CLI implementation so that its purpose and operation are well described by the header commit.  Omit the use of enums that cause issues for MSVC 2025.
691b44a1b 2025-05-14 Back out the "low-quality index" query planner hack of check-in [bcac937526d9a6ef].  Subsequent query planner enhancements for dealing with star-queries make that change unnecessary and the change was recently found to cause a performance regression in an unrelated query. Also fix a typo in a debugging message.
186fd3043 2025-05-13 Adjust the strftime() test in test/date4.test to remove flags not supported in musl libc if that environment is detected.
494830ca8 2025-05-13 First cut at enhancing the fsdir virtual table so that it works with unicode characters on Windows.
0df6c5b9a 2025-05-13 Omit the unused readdir_r() routine from test_windirent.c
0a0777d84 2025-05-12 Session extension doc typo fix reported in [forum:75e9408acb|forum post 75e9408acb].
a0b34dcfc 2025-05-12 Fix a coding mistake in vfstrace.
eb55814c6 2025-05-11 Remove a redundant typedef from the sqlite3_rsync.c source file.
94e22bc07 2025-05-10 Provide the SQLITE_BUG_COMPATIBLE_20250510 compile-time option that restores the JSON5 bug fixed in the previous check-in, in case some applications need it for legacy compatibility.
844b45795 2025-05-10 Add enforcement of the obscure JSON5 syntax rule that the &#92;0 escape sequence must not be followed by a digit. [forum:/forumpost/c061e87faf7d1c55|Forum post c061e87faf].
733aff3be 2025-05-08 Fix PRAGMA trusted_schema=OFF and similar so that it restricts the kinds of functions in CHECK constraints that the documentation says it does.  It was letting through some function that it ought not have.  This is a defect in [5720924cb07766cd].  See [forum:/forumpost/3fa9d44c0b381342|forum thread 2025-05-08T08:50Z]. Additional test cases will be added separately.
cc28137e0 2025-05-08 Internal doc typo fix. No code changes.
f087b6ace 2025-05-07 Fix a harmless warning about and oversize shift operation on malformed JSONB inputs.  [https://issues.oss-fuzz.com/issues/415850463|OSSFuzz 415850463].
f67058367 2025-05-06 Add test cases for the NOT NULL/IS NULL optimization in CHECK constraints fix.
288f35685 2025-05-06 Fix a bug in the NOT NULL/IS NULL optimization of check-in [cb94350185f555c3] that can cause invalid data to be used for a column if that column has a CHECK constraint that includes the NOT NULL or IS NULL operator. Problem discovered by the [https://issues.chromium.org/issues/415397143|Chromium fuzzer].  Never seen in the wild, as far as anybody knows.
ad39fa81a 2025-05-06 Fix the sqlite3VdbeTypeofColumn() function so that it works correctly even when SQLITE_DEBUG is defined.
3b51a1ac0 2025-05-06 Fix console-I/O on Windows for DEBUG=3 builds.  Broken by [925e97e6f4238f02].
d7324103b 2025-05-03 Enhance sqlite3_rsync so that if the first attempt to invoke a copy of itself on the remote system using ssh fails, try again after augmenting the PATH.  This enables sqlite3_rsync to work without the --exe option when the remote system is a Mac.
37b76bac1 2025-05-03 Fix a harmless redundant variable declaration in sqlite3_rsync.
e61867471 2025-05-03 Addition summary results output when using -vvv on sqlite3_rsync.
d7b83224b 2025-05-03 Promote the --protocol option to sqlite3_rsync from being an undocumented debug option to being a supported and user-visible option.  This is sometimes needed to work around bugs in prior versions running on the remote.
e2826db73 2025-05-03 Improvements to protocol negotiation.
5f4d01373 2025-05-02 Clean up command-line parsing.  Add the undocumented -protocol option for debugging.
bef956548 2025-05-02 Now appears to be working.  More testing needed.  Refinement of the version-2 algorithm needed.
f124ddf36 2025-05-02 Bug fixes.  Added new debugging features to better visualize the protocol.
fbafaa561 2025-05-02 This is the start of an experiment in getting sqlite3_rsync to use less bandwidth when the two databases are very similar, by sending hashes over blocks of pages initially, rather than over individual pages, then requesting more detail when hashes do not match.
5db695197 2025-05-02 Do not allow sqlite3_rsync to convert the replica from WAL-mode into DELETE-mode, as that can disrupt existing clients on the replica side. DELETE-mode to WAL-mode conversions are allowed, however.  See [forum:/forumpost/6b575b66156673ee|forum thread 6b575b66156].
391f70c52 2025-05-01 Allow sqlite3_rsync to work on non-WAL-mode databases, as long as the --wal-only flag is not used.
f23a61258 2025-04-30 Fix a harmless problem in the CLI in which SQL errors that occur during the ".schema" command are properly ignored, yes still appear in the ".log" output. [forum:/forumpost/42fe6520b803be51|Forum post 42fe6520b8]
88ed1806a 2025-04-30 Fix an issue in Bloom filters on RHS subsqueries to IN operators. See [forum:/forumpost/792a09cb3df9e69f|forum post 792a09cb3d] for a description of the problem.  Also improve comments related to [baa83b460c677c21] which was origin of the problem.
a20c09c47 2025-04-29 Upstream teaish for a tcl portability fix on Haiku and a much nicer impl of proj-tclConfig-sh-to-autosetup.
5a9a2d852 2025-04-29 Remove the run-fuzzcheck makefile targets, since testrunner now accomplishes that for us, and does a better job of it.
2ba946b34 2025-04-29 Add the "--fuzzdb FILENAME" to testrunner.tcl as an alternative to setting the FUZZDB environment variable (as that can be awkward to do on Windows). Further improvements to the testrunner.tcl documentation.
873fc5dff 2025-04-29 Update testrunner.tcl documentation.  Fix typo in testrunner.tcl output.
c171d7624 2025-04-29 Improved --explain display of FUZZDB test plans in testrunner.tcl.
ece7709f1 2025-04-29 Do not run FUZZDB on either Windows-Memdebug or Windows-Win32Heap.
8a68ab963 2025-04-29 Make testrunner.tcl more restrictive about which configurations run fuzzcheck-asan and fuzzcheck-ubsan.
246dc9235 2025-04-28 Testrunner.tcl now runs fuzzcheck-asan and fuzzcheck-ubsan tests.
d4cc3a42e 2025-04-28 If the FUZZDB environment variable is set when running testrunner.tcl and that env-var points to a fuzzcheck database, then suppliment the fuzzcheck tests with that extra database.
1365bcffb 2025-04-28 Enhance testrunner.tcl so that it does not build testfixture unnecessarily - if the pattern does not match any TCL test.
7fec7c96c 2025-04-28 Fix testrunner.tcl so that it honors pattern matches in non-testfixture tests, such as fuzzcheck and sessionfuzz.
738443c52 2025-04-28 Remove a stray blank line from the test/testrunner.tcl script.
911271718 2025-04-28 Remove long-obsolete performance testing scripts from the tools/ folder. The test/speedtest.tcl script is what should be used these days.  This is just cruft clean-up.
886f67419 2025-04-28 tea: pull in upstream teaish. Consolidate the build definition from the upstream build and this one to ease maintenace. Improve compatibility with historical TEA usage of --with-tcl=... (it insists on a /lib suffix for that path).
c26cde3bf 2025-04-27 proj.tcl: correct the auto-reconfigure rules to include any X=Y passed to configure. Improve handling of quoted CFLAGS.
c49c7dad8 2025-04-27 autoconf/tea: the default value of --threadsafe=X is now based on a pkgconfig query using the target tclsh, which is much more reliable than grepping Tcl's linker flags. Doc touchups.
0f0450eda 2025-04-25 Fix an off-by-one error in an assert(), discovered by oss-fuzz.  This is a harmless error in as much as assert()s are disabled in production builds, and because the off-by-one only occurs on nonsensical CREATE INDEX statements.
ef90c4209 2025-04-25 Teaish internal API tweaks and ensure that -encoding utf-8 is used when source'ing test scripts.
d3b39b18d 2025-04-23 Upstream teaish fixes and improvements.
37f22ff75 2025-04-22 Fix a problem in the fts5matchinfo.test file that prevented it from working on Mac.
024818be2 2025-04-22 Latest upstream jimtcl to fix rare segfault cases.
204d78764 2025-04-22 Generic cleanups and fixes in the teaish build.
d2fd09957 2025-04-21 Remove an extra conditional that was inserted earlier today and which is unreachable.
81cde80f7 2025-04-21 Further improvements to the decision of whether or not a BLOB input is JSONB.
cbe4a26e0 2025-04-21 Do a better job of providing bug compatibility with SQLite 3.44.0.  See [forum:/forumpost/07e206fcd6|forum thread 07e206fcd6] for background.
c4e7cf68c 2025-04-19 Update to comments in sqlite3session.h.
f857482ed 2025-04-18 Add an appropriate _declspec to the declaration of the sqlite3_dbdata_init() function in the recovery extension.
31e08190a 2025-04-17 Upstream teaish, which simplifies how extension metadata are initialized and shrinks proj.tcl by 4k.
10744c61a 2025-04-17 When logging errors using sqlite3_log() and the error text includes the text of an SQL statement, but the SQL statement text at the end so that if the error message buffer overflows it is the SQL statement text that gets truncated, not the statement of the problem.
56747d184 2025-04-17 Increase the size of the output buffer for sqlite3_log().
680a9584c 2025-04-16 Add docs explaining how to test the teaish build.
c264a0fd9 2025-04-16 Latest upstream teaish. Most notably it adds the ability for the extension to specify a minimum Tcl version, and this build now enforces a minimum Tcl of 8.6.
259532c0a 2025-04-16 Update doc/tcl-extension-testing.md for Unix systems, consolidating the Tcl 8.x and 9.x sections.
6fe2a9a8f 2025-04-16 Attempt to provide EBCDIC translations to the tables in the JSON implementation.  The SQLite developers do not have access to any computers using EBCDIC and so have no way to test this patch, and cannot vouch for its accuracy.
cd83a85e0 2025-04-16 Change the target libdir name in the teaish build to match historical tea builds.
b70d45042 2025-04-16 A portability fix for proj.tcl: some Tcl builds do not like (array set x $someArray). Also better --mandir handling on Haiku (where the former problem was found).7
b1cc4aeb6 2025-04-16 Latest upstream teaish for fixes and improvements.
0243ca824 2025-04-15 Correctly handle the case of a multi-column UNIQUE constraint that contains the ROWID as one of it columns, and then the columns of that UNIQUE are used in a row-value IN operator as a WHERE clause constraint.  Reported by [forum:/forumpost/b9647a113b465950|forum post b9647a113b].  Problem introduced by [723f1be3d4a905a6], part of ticket [da78413751863].
8488789d7 2025-04-15 Fix a minor typo in a code comment.
850289bf1 2025-04-15 Cleanups and refactoring in proj.tcl and teaish.
136afcfcc 2025-04-15 Avoid a potential integer overflow in non-default builds of the fts3 matchinfo() function.
56da8772b 2025-04-15 Further cleanups and code consolidation between teaish.tcl and sqlite-config.tcl parts.
dc2d79f80 2025-04-15 Slight simplifications in the teaish build.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
