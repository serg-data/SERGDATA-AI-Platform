# SQLite — Git tag version-3.48.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.48.0
Сравнение с предыдущим тегом: version-3.47.0

## Коммиты в диапазоне

```text
942c95876 2025-01-14 Version 3.48.0
f1747f93e 2025-01-13 Remove a stray tab character from a comment.
43afab28a 2025-01-13 GCC 13 has become more quite pedantic about the signature of functions matching the type of pointers through which the functions are called.  Make adjustments to extension functions and test procedures to work around this.  No changes to the core.
14bc98d8e 2025-01-11 Fix harmless "implicit fall through" warnings that suddenly appeared when I upgraded to gcc-13.
4b5e8c926 2025-01-11 Better job at suppressing harmless scan-build warnings.  This time testing and working.
27661f24c 2025-01-11 Fix harmless scan-build warnings.
c1f914dbc 2025-01-11 Fix an age-old bug in the lower-level wasm/js helper bits which was (A) caused removal of customized WASM func/argument conversion to siltently fail and (B) triggered a warning in the closure toolchain. Reported in [jaccwabyt ticket c5c296e85a7c01360820|https://fossil.wanderinghorse.net/r/jaccwabyt/info/c5c296e85a7c01360820].
35ac4c868 2025-01-09 Update the makefile so that it puts the amalgamation files in a subdirectory in the amalgamation-zip. [forum:/forumpost/b8dd1941e1|Forum post b8dd1941e1].
b1cbae8bd 2025-01-09 When removing an fts5 in secure-delete mode, defer setting the table version to SECUREDELETE until flushing data to disk. This prevents problems that can occur if there is a rollback or statement rollback operation.
c1242d60d 2025-01-08 Fix another assert() failure in fts5.
ad460db7e 2025-01-08 Fix a crash in fts5 that could occur if shadow tables are modified or removed.
af8af121a 2025-01-08 Cross-link and otherwise improve the various how-to-compile documents. No code changes.
45d19952c 2025-01-08 In the doc/tcl-extension-testing.md document, provide enhanced explanation for why the tcl library needs to be copied into the install directory.
6962f3d81 2025-01-07 Further refinement to the Tcl extension testing procedure.
fd11e5c08 2025-01-07 Improvements to [14b38ae6ab86a314] so that the Tcl interface is better able to work with boolean values in both Tcl86 and Tcl90.
ece172995 2025-01-07 Fix a memory error in test logic introduced by [8704034254938662].
4a8331137 2025-01-07 Typo in the previous check-in.
311990d74 2025-01-07 Enhancements to the Tcl SQLite extension testing procedures so that they install a full-featured SQLite and so that Tcl is build statically so that there is no need to worry with LD_LIBRARY_PATH.
4717d573e 2025-01-07 Make the TCL extension aware of the booleanString type within TCL.
e53393250 2025-01-07 Fix a typo in the previous check-in.
4a6896379 2025-01-07 Minor fixes to tclsqlite.c to promote portability.
fbbe26282 2025-01-06 Enhance the makefile to make it easier to build from a read-only source tree.
885f546f9 2025-01-06 Fix a problem with tool/mksqlite3h.tcl that prevents it from running out of a read-only check-out.
a5dbae378 2025-01-06 Fix a minor problem with the sqlite3_get_table_printf() test interface. No core changes.
cee8b04d3 2025-01-06 Add test case for using both SQLITE_CHANGESETAPPLY_IGNORENOOP and SQLITE_CHANGESETAPPLY_FKNOACTION.
f19d7b4de 2025-01-05 Further refactoring of the TCL extension test procedure document, for improved clarity and usability.
15e388d91 2025-01-05 Refactor the TCL extension test procedure to deal with TCL8.6 and TCL9.0 separately, to simplify the procedures and reduce cognative stress on the tester.
85900c04b 2025-01-05 Fix typo in the tcl-extension-testing.md document.
8b53358f8 2025-01-05 Improvements to TCL extension test procedure description.  Improvements to the tclextension-list and tclextension-verify makefile targets to suppress unnecessary output.
1e03bd8a8 2025-01-04 Improvements to testing and validation of the SQLite TCL extension.
1c1b3a0f2 2025-01-04 Show the values of $(JIM_TCLSH) and $(VISUALSTUDIOVERSION) in the output of "nmake tcl-env".
1388a7169 2025-01-04 Allow the 2nd argument to ".param set" to use previously bound parameters, as suggested by [forum:/forumpost/823e1bd746|forum post 823e1bd746].
7a3d03b1f 2025-01-04 Fix a problem in the sessions extension allowing changesets containing foreign key violations to be committed under some circumstances.
827212821 2025-01-04 Adjust the Windows Makefile.msc so that it can build the tclextension with Tcl8.6 successfully.  Updates to the tcl-extension test procedure document.
8f1bdc0f7 2025-01-04 Add new tcl-extension-testing.md document.  The Windows side is not yet working.
ded37f337 2025-01-03 Add comment to the columnIsGoodIndexCandidate() routine to record the results of a failed experiment.  No changes to code.
8d6e3f513 2025-01-03 Avoid using Int32x32To64() with a 64-bit argument in fileio.c - this level of micro-optimization is not really necessary there.
04364cb3c 2025-01-02 Improve the treeview output for CteUse objects.
db258d8ff 2025-01-02 Improvements to the display of subqueries in the FROM clause for treeview output.  (Debug and analysis code only - does not affect production builds.)
1426d2a26 2025-01-02 Close database connections in test/dbpage.test, for Windows.
52c87ac08 2025-01-02 Fix recent test cases so that they work even when auto_vacuum defaults to on.
3835cf6ea 2025-01-02 Add a test case for ROLLBACK TO of database truncate operations made through the sqlite_dbpage vtab.
a683b055f 2025-01-02 Improvements to the way that truncation is implemented in sqlite_dbpage().
e0b6ee518 2025-01-02 Update the build instructions for Windows to note that VS2015 or later is required to avoid the need to install tclsh.exe.
66985fb8f 2025-01-01 Fix the tool/omittest.tcl script, broken by [d8c0e0184226bdae].
f7fcf7f91 2025-01-01 Fix the vfstrace.c extension so that it supports xFetch and xUnfetch.
95f6df5b8 2024-12-30 Add the convenience makefile target (unix-only) "src-archives" that builds the various tarballs and ZIP archives that go on the download page.  This is intended to make it easier and less error prone to put up new "draft" download pages for testing.
71d6456f5 2024-12-30 New assert() statements to show that the sqlite3_value.db field is initialized for MemArrays.
6b19c72f2 2024-12-30 Add an extra assert() to releaseMemArray() just to prove that the sqlite3_value.db field is never NULL.
4112a63b8 2024-12-29 Four new assert() statements to help with static analysis.
8b6890212 2024-12-28 Show ETC in fuzzcheck with the --spinner option when there is only one input file.
e0190a698 2024-12-28 Fixes to the substr() SQL function so that it can handle ridiculously large numbers in its 2nd and 3rd arguments without signed integer overflows.
9591d3fe9 2024-12-22 In the (debugging) rtreenode() function, do not override an error coming out of sqlite3_result_text().
142c5de4d 2024-12-19 Fix a test case in sqllimits1.test so that it works with the Apple configuration which changes the default SQLITE_MAX_LENGTH.
ccfb50d55 2024-12-19 Correction to check-in [a9759fc78d6cb0df] - printf() parameters values must be integers.
be2a40d48 2024-12-19 The BTree mutex must be held when calling sqlite3BtreeLastPage().  This check-in fixes a bug introduced by [cf8b99e17872c054].
f2d422c52 2024-12-19 Fix the sort4.test module so that the first two test cases are omitted when SQLite has been compiled using SQLITE_MAX_WORKER_THREADS=0.
166f4eb5c 2024-12-19 configure script: only set the SQLITE_TEMP_STORE feature flag if --with-tempstore is explicitly set, to avoid colliding with that flag being set by other means via the test fixture scripts.
019de3d55 2024-12-19 Fix the Microsoft makefile so that it does not set SQLITE_TEMP_STORE unnecessarily.
543ee479e 2024-12-19 Enhance lemon so that it accepts the -U command-line option that undefines a preprocessor macro.
2dcd4fad6 2024-12-19 Fix additional integer overflow problems in the substr() function.
b097ef29d 2024-12-18 Fix possible integer oveflow in the second and third argument to substr().
47bc07d42 2024-12-18 Avoid 32-bit roundoff error on the second argument to round(). [forum:/forumpost/170aeab92a|Forum post 170aeab92a].
0c34eab47 2024-12-18 Rename some var refs in ext/lsm1/Makefile for the new build process.
2fb488d10 2024-12-17 Do not attempt to truncate a database in sqlite_dbpage if the database is not larger than the requested truncation size.
32dd04b41 2024-12-16 Code formatting changes to make trunk more like wal2.
bd1a5932d 2024-12-16 Changes for better alignment with the wal2 branch.
276172e4a 2024-12-16 Remove unnecessary end-of-line whitespace.
bba195342 2024-12-16 Tiny makefile/configure script doc tweaks. No functional changes.
9ee02515c 2024-12-13 Fix a harmless compiler warning that comes up when using SQLITE_DEBUG in separate compilation mode.
35d302ccb 2024-12-12 Increase the maximum number of arguments on an SQL function to 1000 with the capability to increase it further up to 32767 using a compile-time option.
6e53f67c6 2024-12-10 Fix harmless typo in a comment describing the columnMallocFailure() function.
e57527c14 2024-12-09 Make the TCL interface more rebust against very large strings coming out of TCL9.
e85e33d39 2024-12-09 Enhance the ".import" command of the CLI so that it is able to insert into a view that has an instead-of trigger. [forum:/info/3e03c73150f8b9f8|Forum post 3e03c73150f8b9f8].
c29bc733b 2024-12-09 Add NEVER() around branches that seems to have been made obsolete by [a350ea7c6b89725b].
54f96dc50 2024-12-09 Further improvements to the decimal-to-float conversion for values close to LARGEST_UINT64.
4f5ae3fc4 2024-12-09 Fix an obscure problem with multiple outer joins, ON clauses and query flattening. Forum [forum:5c8a069d23|thread 5c8a069d23].
fd360c394 2024-12-09 Resynchronize autoconf/Makefile.msc
29d1d9150 2024-12-08 Add a note in Makefile.msc about EXTRA_SRC files possibly requiring manual editing, as discussed in [forum:903f721f3e7c0d25|forum thread 903f721f3e7c0d25].
9f53d0c81 2024-12-07 Yet another iteration of the solution to the floating-point conversion problem - this what avoids complaints about oversize double values from -fsanitize.
870364280 2024-12-07 A cleaner and more robust solution to the floating-point conversion problem originally fixed by [81342fa6dd03fffb].
92d252e06 2024-12-07 Fix more harmless compiler warnings.
459787010 2024-12-07 Fix harmless compiler warning caused by the previous check-in.
1a4b2117f 2024-12-07 On x64 hardware, round-trip uint64_t&rarr;double&rarr;uint64_t conversions fail for values greater than UINT64_MAX-2047.  This caused the SQLite text-to-float converter routine to give incorrect results for values between '1.8446744073709550592eNNN' and '1.8446744073709551609eNNN' for any exponent NNN.  This problem was introduced by check-in [761d8fd18b0ee868] and first appeared in version 3.47.0 and was reported by [forum:/forumpost/569a7209179a7f5e|forum post 569a7209179a7f5e].  Fixed by this check-in.
ef636cc3c 2024-12-06 Add the SQLITE_PREPARE_DONT_LOG option for sqlite3_prepare_v3(), that prevents errors in the compilation of the SQL from being sent to sqlite3_log().
c40329c9b 2024-12-06 Minor doc update in auto.def. No functional changes.
0448e00aa 2024-12-06 Ensure that the post-config checks for @UNEXPANDED_VARS@ pass even if --disable-tcl is used, as reported in [forum:74ef8059fc|forum post 74ef8059fc].
eed134c4d 2024-12-05 Fix the build of sqlite3_analyzer.exe on Windows that was broken by check-in [80f3bf8c2ee31ba1].
76412af15 2024-12-04 Minor doc correction in ext/misc/shathree.c, as reported in the forum. No functional changes.
33c120f9b 2024-12-02 Improve the output from the ".testctrl opt" command in the CLI.
4b491d856 2024-12-02 Ensure that the query flattener does not change an ON clause term to a WHERE clause term.
c9ac238b9 2024-12-02 Fix a comment typo on the sqlite3ExprIsSingleTableConstraint() routine.
bfdeb1f6d 2024-12-02 Fix a harmless typo in debugging output.
ed7fe45c7 2024-12-02 Reformulate [9e09d5d6] so that memsys5 shows up in the late-config summary as being enabled and does the right thing if both --debug and --memsys3 are used.
3e1f302db 2024-12-02 Enable MEMSYS5 with the --dev configure option.
224e35608 2024-12-02 Slighly less confusing output from treeview during debugging.
d004268b2 2024-12-01 Trim a bit more from the sqlite370.svg border to get it closer in scaled size to the logo currently on the docsrc site.
fd66549cb 2024-12-01 Correct the fill color for the background of sqlite370.svg - it was slightly darker than it should have been.
a13a645cd 2024-12-01 Re-export sqlite370.svg to retain the gradient part and clip the size using the cutting guides in sqlite370.eps.
9bc351b3c 2024-12-01 Export a clipped copy of sqlite370.eps as sqlite370.svg, based on discussion in [forum:1bbd6d17ca|forum post 1bbd6d17ca].
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
