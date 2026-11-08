# SQLite — Git tag version-3.42.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.42.0
Сравнение с предыдущим тегом: version-3.41.0

## Коммиты в диапазоне

```text
89efa8977 2023-05-16 Version 3.42.0
89caab814 2023-05-16 Update the tool/mkmsvcmin.tcl script so that it prints a one-line message to explain what it has done.
e680b6dcf 2023-05-15 Fix a C++-style variable declaration in the generate_series() extension.
ff4e771c0 2023-05-15 Increase the stack size available to fuzzcheck to 8MB on Windows.
4042d2b42 2023-05-15 Limit the number of nested NOT nodes in an fts5 expression to 256.
307db965c 2023-05-15 Add the --wait command-line option to fuzzcheck.
b579db6d5 2023-05-15 Make generate_series() correct on ones complement ALUs and acceptable to UBSAN.
eb4455e4e 2023-05-15 As evidenced by [forum:/forumpost/f3f546025a|forum post f3f546025a], the new RIGHT JOIN related restriction on the push-down optimization implemented by [da3fba18742b6e0b] also needs to apply to the automatic index (a.k.a. hash-join) optimization and to the Bloom filter optimization. Computation of the restriction is now moved into the sqlite3ExprIsSingleTableConstraint() routine.
fa746af4a 2023-05-15 Simplify the interface to constructAutomaticIndex().
b8d689b66 2023-05-13 Fix windows-specific problems in test scripts sessionnoop2.test and sessionrowid.test.
5e65cd1ca 2023-05-13 Remove unnecessary call to sqlite3_dbdata_init() from shell.c.
fd0791587 2023-05-13 Add an "#ifndef SQLITE_HAVE_SQLITE3R" directive to shell.c.in, to avoid including the recovery code a second time if the shell is being compiled with sqlite3r.c.
ea51c09a8 2023-05-13 Mention that sqlite3_mutex_free() accepts NULL as a no-op.
273c2a942 2023-05-13 Fix compilation issue seen with MSVC.
59b6a2bcb 2023-05-12 Fix harmless compiler warning caused by [0772ddf56713d013].
83be5586a 2023-05-12 Add multi-threaded test for "INSERT ... RETURNING ..." and SQLITE_BUSY errors.
4f3dc9397 2023-05-12 Make the regexp extension more robust against OOM errors during compilation of the recognizer engine. [forum:/forumpost/f50aecd5e8|Forum post f50aecd5e8].
fb74019a1 2023-05-12 Fix unlikely strange result of CLI edit().
69bc8c70f 2023-05-12 Ensure the _O_U16TEXT is defined for Windows builds of the CLI. [forum:/forumpost/c80aa942dc6bf2|Forum post c80aa942dc6bf2].
26a3e5664 2023-05-12 Remove a stray CR from end of line in a source file.
61791c6f4 2023-05-12 Fix harmless typos in comments.
6b429dc11 2023-05-12 Ensure that all prepared statements are expired and forced to reprepare whenever the database text encoding changes. [forum:/forumpost/43cbfc4d23|Forum post 43cbfc4d23].
78b404d97 2023-05-11 Add [/info/cec6a06508239c09e363?ln=5525-5531|restriction (5)] to the omit-noop-join optimization.  Fix for the issue reported by [forum/forumpost/49f2c7f690|forum post 49f2c7f690].
5ca40d84a 2023-05-11 Fix a minor typo in a comment.  No code changes.
418d21230 2023-05-11 Fix the rbu_exclusive_checkpoint=1 option so that it works with a zipvfs database in pass-through mode.
28f4e7b28 2023-05-10 Enhance the split-sqlite3c.tcl script so that it uses single-character extensions on subordinate source files, even when the number of subordinates exceeds 9.  This is not yet needed, but might be soon.
0051a56de 2023-05-10 Fix harmless compiler warnings from the CBMC compiler.
5af043c2e 2023-05-10 Rename sqlite3IsTableConstraint() to sqlite3IsSingleTableConstraint() and improve its header comment, in an attempt to make the code easier to reason about.  No functional changes - should generate identical machine code.
d733ee5cc 2023-05-10 Add a missing comma to the documentation for the OP_Jump opcode.  No changes to code.
88a99437b 2023-05-10 New restriction on the push-down optimization to prevent an ON or USING clause on the left side of a RIGHT JOIN from being pushed down into a subquery that is on the right side of that RIGHT JOIN. [forum:/forumpost/a7d4be7fb6|Forum post a7d4be7fb6]. Also add comments to describe previously undocumented push-down optimization restrictions.
5fbb2adf7 2023-05-10 Fix bug in fall-back logic of CLI .clone
d9be38736 2023-05-08 Fix recover1.test so that it works with DEFAULT_AUTOVACUUM builds.
bbd0ae2e8 2023-05-08 Improved error handling when ".open" fails in the CLI.
addc7e0e5 2023-05-08 In editPage(), if an attempt is made to edit an empty 64KB page, then take the slow path through rebuildPage(), in order to maintain strict invariants in the editPage() code. [forum:/forumpost/0f37727c0d|Forum post 0f37727c0d].
c42bbfc55 2023-05-08 Ensure that the label for a JSON object really is a string and not an array or object that just happens to end with a string. dbsqfuzz 32f62ed8676d0a153dbe756aeae3202d3670fe50.
6d841fdc8 2023-05-08 Add tests for recovering data to a lost-and-found table from a utf-16 db. No code changes.
28f32bedd 2023-05-07 It turns out that pagerExclusiveLock() can be called with the lock state already set to RESERVED if the SQLITE_FCNTL_PERSIST_WAL setting is set and a specific sequence of multiple journal mode changes occur. Enhance pagerExclusiveLock() to deal with this. [forum:/forumpost/8130545bc6|Forum post 8130545bc6]
4e73863fd 2023-05-05 Fix a comment in the JSON logic.  No code changes.
77eb3e305 2023-05-05 Fix a buffer overrun that could occur when using the format() function to format a very small real value with the "," modifier.
ed96436f2 2023-05-05 Reduce the maximum depth of nesting in json objects to 1000.
3e49355e1 2023-05-05 Do not attempt to run json502.test with SQLITE_OMIT_VIRTUALTABLE builds.
e03061910 2023-05-05 Updates to compile-time option usage and especially to the compile-time option test script in tool/omittest.tcl.
fb18d8103 2023-05-05 Fix the pager2-3.1 test case so that it does not run if a required dependence (shared-cache) is omitted from the build.  Fix for [forum:/forumpost/7a028538a7|forum post 7a028538a7].
cad6aae45 2023-05-05 Allow virtual tables to prepare writes to shadow tables in defensive mode from with xRelease() callbacks - even if the xRelease() is invoked from within sqlite3_finalize().
0498caec8 2023-05-05 Improved formatting of comments on SQLITE_CONFIG_xxx defines as those comments are used by documentation.
e8468098a 2023-05-04 Add support for the comma (,) modifier to %f formats in the format() function.
c1e40a3a0 2023-05-04 Fix a bug in cursor hints that can cause references to tables that have not been opened.  Cursor hints are intended for use by COMDB2 only and should not appear in production builds, so this should not be a factor for the vast majority of users.
62b28db5c 2023-05-03 Add another assert() to FTS5 to demonstrate that a pointer is never NULL.
3f23eb681 2023-05-03 Add an assert() to fts5_config to ensure that a potential OOM is being handled correctly.
344230698 2023-05-03 Protect a macro argument with parentheses in FTS5.
dda2833a4 2023-05-03 Add a comment to the [0512f82a2cde7447] change to link it to its TH3 test case.
69e242297 2023-05-03 Enhancement to showwal such that it shows what the page hash should be on a hash mismatch.
b4824b055 2023-05-03 In the zipfile extension, leave the catalog list in a consistent state when the last entry is removed from the list. [forum:/info/f03f1e4c5a5c9959|forum post f03f1e4c5a5c9959].
ce2aa8beb 2023-05-03 If the page size is wrong on the page1 content inside a WAL file, then running VACUUM could trigger an assert().  This check-in changes that assert() into a branch that returns SQLITE_CORRUPT. [forum:/info/4ef9b37d74d2d2e8|Forum post 4ef9b37d74d2d2e8]
681307dc8 2023-05-03 Improved detection of excess recursion on arrays and objects in the JSON parser.  Fixes a problem detected by dbsqlfuzz.
790adfd8e 2023-05-03 Do not overflow the Index.aSample[] array if the same index appears in the sqlite_stat4 table under multiple names because it is a WITHOUT ROWID primary key index.  [forum:/info/537d8ab118df7edd|Forum post 537d8ab118df7edd]
8777bdb78 2023-05-03 Do not even attempt to load the sqlite_stat4 table if the use of STAT4 is disabled using sqlite3_test_control().
164b332d8 2023-05-03 Fix CLI mishandling of OOM during .import _of_ a DB. [forum:7ed4a250d3|Reported by forum post 7ed4a250d3].
b50462380 2023-05-03 In the CLI, ensure that the argument to quoteChar() is not a NULL pointer due to a prior OOM.
9cf09b567 2023-05-02 Fix a problem with the sqlite3changeset_size() API and rowid tables.
d8200de04 2023-05-02 Give CLI quoted args hex escapes (as documented.)
8594f02c5 2023-05-02 Cure CLI hang on .import with high-ASCII column separator.
bdb40cb18 2023-05-02 Allow for lower-case "nan" to mean NaN in JSON.
d6b3a02d2 2023-05-02 Interpret negative arguments to sqlite3_sleep() as zero.
8c79ea844 2023-05-02 Improved handling of NULL arguments to json_valid() and json_error_position(). [forum:/forumpost/06c6334412|Forum post 06c6334412].
67a17779c 2023-05-02 Fix typo in comment.  [forum:/forumpost/3da7d9c445|Forum post 3da7d9c445].
53ffe6e21 2023-05-02 Minor code change in the CLI to make a UAF warning from scan-build go away.
f9b58eb4f 2023-05-01 Fix harmless compiler warnings.
0f97dc28b 2023-05-01 The gcc definition of the SQLITE_INLINE macro is not compatible with string ANSI, so disable it if the -std=c89 command-line option is used.
1f02cd6cd 2023-05-01 Fix harmless compiler warnings in FTS5.
58d40363b 2023-05-01 Remove xFileControl() handling from the OPFS VFS altogether, re-routing all syncing through xSync() instead. This eliminates superfluous syncing introduced in [a371374148a2], as discussed in [forum:647d2f811dbc2dfe|forum thread 647d2f811dbc2dfe].
59fe13e39 2023-05-01 Fix harmless compiler warnings.
5ecee3dae 2023-05-01 Fix typos in comments in sqlite3session.h preventing documentation from being correctly generated.
4cc6f869a 2023-05-01 New enhancements to the sqlite3_db_config() constants documentation.
043353483 2023-05-01 Expose the SQLITE_DBCONFIG_STMT_SCANSTATUS and SQLITE_DBCONFIG_REVERSE_SCANORDER sqlite3_db_config() options to JS.
d45bbbb05 2023-05-01 Implement full xSync() for the OPFS VFS. The previous implementation was not correct for journal files. Reported in [forum:647d2f811dbc2dfe|forum post 647d2f811dbc2dfe].
b5fab6816 2023-05-01 Fix typos in documentation comments in sqlite3.h.
908dec740 2023-05-01 Do not apply the "AND false" optimization if either operand comes from the ON clause of a join.  Fix for the problem identified by [forum:/forumpost/96cd4a7e9e|forum post 96cd4a7e9e].
e210c9390 2023-05-01 Fix abbreviated paths for objects such that they work even if the object key begins with '$'.
5196d9350 2023-04-30 Fix a problem with json_patch() when one side or the other is JSON5. dbsqlfuzz bc10593a4ba8e7a7862593532285be31f00f8e41
dae7ae359 2023-04-30 Accept the full ECMAScript 5.1 IdentifyName syntax for keys in objects.
4a398c317 2023-04-30 All JSON to understand floating point literals "Inf" and "QNaN" and "SNaN" in any case, without the SQLITE_EXTENDED_NAN_INF compile-time option.  This extension is always available.
7be1473cc 2023-04-30 Omit the json_valid() function.  Change the name of json_error() to json_error_position().  Use "NOT json_error_position(X)" as a substitute for "json_valid5(X)".
e01e3b5b9 2023-04-29 Fix a crash that could occur in fts5 'secure-delete' mode when operating on corrupt records.
440f7b483 2023-04-29 More ALWAYS() macros.
f8ae2d2a2 2023-04-29 Add ALWAYS macros on unreachable branches in the new JSON5 logic.
399875f6c 2023-04-29 Simplification of the logic that normalizes JSON5 integer literals into canonical JSON integer literals.  Improved reporting of OOM.
d76d954de 2023-04-29 Do not allow leading zeros on non-zero numeric literals in JSON.
29c2f0366 2023-04-29 Replace duped generate_series() test with another corner case.
64953f0fb 2023-04-29 Minor fixes to to the JSON% parser.
f176776bd 2023-04-29 Correctly recognize an isolated U+feff as a space character in JSON5.
7667f5f12 2023-04-28 Add tests for generate_series(), and change an existing test that enforced varying rowid-to-value mapping with query ordering. (That no longer varies.)
8f3fe2ead 2023-04-28 Bug fixes in the logic to skip over JSON5 comments.
6e2de5796 2023-04-28 Bug fix in the offset computation for json_error().
b0d46fcd7 2023-04-28 Revise generate_series() extension (in CLI) to address overflow reported in [forum:754e2d4db2a5|forum post #754e2d4db2a5] and to make behavior better match the like-named PostgreSQL function.
8e7efe376 2023-04-28 Improvements to the accuracy of json_error().  Add the extension SQL functions random_json(SEED) and random_json5(SEED).
272ae627c 2023-04-28 Add the json_error(X) function that returns the 1-based character offset to the first syntax error in JSON5 string X, or 0 if there are no errors.
016f46666 2023-04-28 Fix indentation and omit trailing whitespace in the random JSON generator script.
1170fb52e 2023-04-28 Fix json_tree() so that it is able to deal with the JNODE_RAW labels of a JSON5 object.
90f549a0c 2023-04-28 Do not assert() a bad string representation in an sqlite3_value after an OOM.  dbsqlfuzz c822a17a23c524a0ac7cfb203c7198209da15de8.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
