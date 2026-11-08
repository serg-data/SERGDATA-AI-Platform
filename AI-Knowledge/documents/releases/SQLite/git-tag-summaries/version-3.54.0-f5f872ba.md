# SQLite — Git tag version-3.54.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.54.0
Сравнение с предыдущим тегом: version-3.53.0

## Коммиты в диапазоне

```text
6932c59ee 2026-10-09 Version 3.54.0
039ef9acc 2026-10-09 Fix a typo in a comment.  No changes to code.
0e62f142b 2026-10-09 In the CLI, add comments to internal SQL functions making it clear that those functions are subject to change and removal at any time, lest people come to depend on them.  No changes to code.
fdc06f364 2026-10-09 Fix a build script problem causing generated file sqlite3-all.c to #include "sqlite-10.c" instead of "sqlite-A.c".
9cba46343 2026-10-08 Remove the OP_IfNotOpen opcode.  The OP_IfNullRow opcode is sufficient to get the job done.  This is a follow-up to [e71b0465b9fa13db].
bfb858c59 2026-10-08 Ensure the join flags on the parent are set correctly when flattening UNION ALL sub-queries that include branches with RIGHT joins. Report [bugs:/info/2026-10-08T15:27:33Z | 2026-10-08T15:27:33Z].
d0fe192fa 2026-10-08 Disable the "expr IN (const)" to "expr=const" optimization of "const" has a COLLATE clause, as using the collating on "=" would give the wrong answer. [bugs:/info/2026-10-08T12:36:41Z|Bugs 2026-10-08T12:36:41Z]
f19a90c56 2026-10-08 Improvements to the display of DDL SQL statements in the CLI and in the sqldiff command-line tool in order to close comments and similar in the case of a corrupt schema, and avoid possible SQL injection attacks.  ANT-2026-9VFH4DZS.
28e05e55f 2026-10-08 Avoid clearing unrelated join related expression flags when processing window function queries. Report [bugs:/info/2026-10-08T15:38:26Z | 2026-10-08T15:38:26Z].
ab1268f75 2026-10-08 Fix test script errors causing problems on windows.
fd6452aff 2026-10-08 Make the sqlite3_incomplete() SQL function available in debugging builds of the CLI, for testing.
64c2f58d7 2026-10-08 Disable legacy "go" and "/" command terminator options in the CLI unless compiled with -DSQLITE_SHELL_LEGACY_COMMAND_TERMINATOR. ANT-2026-FE9980M1 and ANT-2026-G9MMWYGM.
82fda1d99 2026-10-08 Sanitize "*/" in tables names of the output of the .diskused command in the CLI, and in sqlite3_analyzer, so that it doesn't prematurely close the comment. ANT-2026-XQM1QD48
97048e902 2026-10-08 Update check-in [e71b0465b9fa13db] so that it does not try to to generate an OP_NullRow opcode for cursors of an IN operator that do not actually exist.
74675a9e8 2026-10-08 Assign the correct encoding to the BLOB values read from an overflow page. [bugs:/info/2026-10-07T15:44:40Z|Bug 2026-10-07T15:44:40Z]
644fa6251 2026-10-08 Fix processing of LEFT JOIN when the right operand is controlled by an IN loop.  [bugs:/info/2026-10-07T23:22:09Z|Bug 2026-10-07T23:22:09Z].
b0db2db98 2026-10-07 Improved escaping of filenames with unusual characters sent over the SSH link by the sqlite3_rsync utility program.  ANT-2026-31X9HVRR.
aa49b4609 2026-10-07 Mark vec1 training function vec1_train() as SQLITE_DIRECTONLY, on the grounds that it sometimes prepares and executes SQL statements based on user-supplied arguments.
1ffe6567e 2026-10-07 Include a work-around of the Microsoft "WorstFit" bug on Windows builds of the sqlite3_rsync utility program.  ANT-2026-H5TXKR5J.
5af1b822f 2026-10-07 Doc-only tweaks in main.mk. No build changes.
7e3819f40 2026-10-07 When calculating TCLLIBDIR from the configure script, filter out //zipfs: paths. Tcl9's (file isdir) returns true for those but they are not usable for our purposes, causing (make install DESTDIR...) to install tclsqlite3 under /zipfs. main.mk's counterpart to this piece already does that filtering by virtue of the shell's (test -d) behaving more conventionally.
9d50c7ebf 2026-10-07 Fix the expansion of "TABLE.*" so that it works the same as PostgreSQL when TABLE is the left operand of a RIGHT JOIN USING. [bugs:/info/2026-10-07T02:56:24Z|Bug 2026-10-07T02:56:24Z]
caa0b5886 2026-10-07 In the treeview display for Expr, show TK_ASTERISK nodes.  Debugging logic only - not used in production builds.
9f05c6e66 2026-10-06 Fix the implementation of O_TMPFILE so that it actually works.
6222fff3a 2026-10-06 In the CLI, further improvements to delayed temp-file deletion so that the test/output-redirect-test.txt script works even better.
bf45b5e6a 2026-10-06 Fix to the time-delay temporary-file deletion logic in the CLI, added by [4e9ee211ca661fe8] but never fully debugged.  Now working with the test/output-redir-test.txt test script.
cd47f23e3 2026-10-06 Increase version number returned by vec1_info() to "0.8". Also fix some warnings in vec1.c.
77dd26bbe 2026-10-06 Fix a case causing infinitely recursive calls to vec1.xSavepoint.
a3426a5bc 2026-10-06 Fix the build for SQLITE_OMIT_WSD.
466e0851d 2026-10-05 When a 3-byte cell on the leaf of an index page, which has a reported size of 4, is moved up to an intermediate page due to a DELETE, the 4-byte page number is added.  The cell should should become 7, not 8.  If it becomes 8, then the fragment count on the page header goes off by one. This is technically corrupt, but is easily fixed with VACUUM. [bugs:/info/2026-10-05T19:18:18Z|Bug 2026-10-05T19:18:18Z].  This issue has been in the code for at least 12.5 years.
c62b4abb9 2026-10-05 Handle temp triggers attached to databases clobbered by sqlite3_deserialize() in the same way as those attached to DETACHed databases.
b642a1d56 2026-10-05 Ensure that deserializing into a database expires existing prepared statements.
95170adc3 2026-10-05 Fixes to sqlite3_incomplete() so that it does not appear to presume a trailing newline if there is none. [forum:/info/2026-10-05T16:22:33Z|Forum 2026-10-05T16:22:33Z]
8a91f5484 2026-10-05 Do not run new virtual table tests in memdb1.test for SQLITE_OMIT_VIRTUALTABLE builds.
5ee733bef 2026-10-05 Allow windows clients to open and recover a wal mode database even if an old client still has the *-shm file mapped. Forum post [forum:/info/2026-10-05T14:07:31Z | 2026-10-05T14:07:31Z].
f0c7055db 2026-10-05 Omit the -r command-line option from Lemon.  That does not affect SQLite. [forum:/info/2026-10-05T15:11:11Z|Forum 2026-10-05T15:11:11Z].
45cd455d7 2026-10-05 Update test cases so that they work for configuration that use -DSQLITE_MAX_EXPR_DEPTH=0.
6e20be1c5 2026-10-05 Ensure that eponymous virtual table objects are not left with dangling schema pointers if the main database is overwritten using sqlite3_serialize().
8532bf12f 2026-10-05 Correctly rollback "OR REPLACE" changes following a "datatype mismatch" error. [bugs:/info/2026-10-05T07:15:40Z|Bug 2026-10-05T07:15:40Z].
eff50a067 2026-10-05 Prevent the expression generated by the count-of-view optimization from getting too deep and causing a CPU stack overflow. [bugs:/info/2026-10-04T05:34:47Z|Bug 2026-10-04T05:34:47Z]
4cf3766d0 2026-10-05 Ensure that when a value that may be stored without data loss as an integer is stored in a column with REAL affinity, the values passed to the preupdate-hook are of type SQLITE_FLOAT, not SQLITE_INTEGER. Report [bugs:/info/2026-10-04T16:18:21Z | 2026-10-04T16:18:21Z].
1ad569d14 2026-10-05 Ensure that it is not a constraint violation if a CHECK constraint that evaluates to NULL for one or more existing rows is added to a table using ALTER TABLE. Report [bugs:/info/2026-10-05T07:36:38Z | 2026-10-05T07:36:38Z].
996ded6c4 2026-10-05 Raise a "nested too deep" error if the number of cursors consumed when resolving a CTE name exceeds SQLITE_LIMIT_EXPR_DEPTH. [bugs:/info/2026-10-04T05:35:14Z|Bug 2026-10-04T05:35:14Z]
e6ff280c8 2026-10-05 Limit the depth of recursion for CTEs using SQLITE_LIMIT_EXPR_DEPTH. [bugs:/info/2026-10-04T04:58:58Z|Bug 2026-10-04T04:58:58Z].
d54522a5b 2026-10-04 Fix expression tree depth calculations for COLLATE. [bugs:/info/2026-10-04T04:50:56Z|Bug 2026-10-04T04:50:56Z]
e4e1b4a46 2026-10-04 When using --with-tcl and friends during cross-compilation, emit a warning that tclConfig.sh will not be used. Addresses [forum:9771d82cd0cd7923|forum post 2026-10-04T17:25:09Z]. Normalize TCL to Tcl in nearby docs and help text because that's how tcl-lang.org types it.
e8cbe2c96 2026-10-04 In QRF, add the zero-pad flag to the default floating-point format in output modes that render JSON or INSERT, so that infinities are shown as 9e999 or similar instead of as "Inf". [bugs:/info/2026-10-04T05:35:43Z|Bug 2026-10-04T05:35:43Z]
cb0a13c7d 2026-10-04 Avoid truncation of a 64-bit value into 32-bits when it is the N parameter to the geopoly_regular() function.
47a64b863 2026-10-04 In the geopoly extension, any polygon with 16,777,216 or more vertexes is considered malformed.  So the number of edges must be between 4 and and 16,777,215. [bugs:/info/2026-10-04T04:58:23Z|Bug 2026-10-04T04:58:23Z].
390c658c6 2026-10-04 Make no changes to the busy timeout if the argument to "PRAGMA busy_timeout" is too large. [bugs:/info/2026-10-04T00:05:36Z|Bug 2026-10-04T00:05:36Z].
ccbdec844 2026-10-03 Fix some formatting issues in test program vec1bench.tcl.
11e6caf06 2026-10-03 Fix a test case in rbuvacuum.test that was assuming SQLite ignored trailing SQL stored in a db schema. As of [e21c5bc59a] this is not true.
2f77d50f7 2026-10-03 Fix test cases added by [e21c5bc59ae66173] so that they work with in-memory configurations.
49437882e 2026-10-03 Enhance the sqlite3_incomplete() interface so that it returns SQLITE_EMPTY if the input consists purely of whitespace and comments.  Fix bugs in the continuation prompt mechanism of the CLI discovered while making this enhancement.
cb547ab3e 2026-10-02 Update the CLI and the sqldiff utility program to use "COLLATE nocase" when comparing table names in sqlite_schema.  Add the --unsafe flag to sqldiff so that it can attempt to process corrupt database files. Changes inspired by ANT-2026-YKVW6RS4.
61978d90e 2026-10-02 Do not allow surplus SQL text to come after the CREATE statement in the sqlite_schema.sql field.  Any such text is flagged as an error.  However, the schema will still work if PRAGMA writable_schema is engaged.
ac5f698cc 2026-10-02 Fix the "sqldiff" utility so that when using the --primarykey option on a table that has a PRIMARY KEY with redundant columns, it does not overflow the array of PRIMARY KEY column names.  Bug discovered by Anthropic as ANT-2026-Y36XS4M7.
cb5651e46 2026-10-02 Fix integrity-check fails that would occur if the database contained a contentless fts4 table. Report [bugs:/info/2026-10-02T12:22:03Z | 2026-10-02T12:22:03Z].
0caf6b532 2026-10-01 SAHPool VFS tweaks contributed off-list by Jure Rotar: hardening against malicious inputs and I/O errors. Truncate to the shorter length when overwriting a db file with a shorter one via importDb(). Correct xOpen() to honor the combination of CREATE/EXCLUSIVE flags.
58fddadb2 2026-09-30 Remove an extraneous nearly-full-file level of indentation in ext/wasm/tester1.c-pp.js.
ca9a8adfa 2026-09-30 Add tests demonstrating kvvfs locking errors across multiple connections to the same storage. Add sqlite3.oo1.Stmt.resetNoThrow() for reasons described in its API docs.
c15f5adad 2026-09-30 Rework the JS kvvfs xLock(), xUnlock(), xCheckReserved(), and xSleep() analog to the recent opfs-sahpool changes to make it more robust when a given kvvfs store is accessed via multiple handles (all necessarily from the same thread). This does not break anything but also does not prove anything - tests are pending.
066a18e5c 2026-09-30 Fix a typo in the VERTICAL_SUM_GENERIC() macro in vec1.c.
9559d8940 2026-09-30 For msvc, __AVX2__ implies __FMA__.
6ae81db9b 2026-09-30 Fix a faulty assert() that was failing when running vec1 OOM tests.
23a070666 2026-09-30 Fix problems in vec1rollback.test preventing it from running on windows.
806fd19e3 2026-09-30 Fix definition of VEC1_META_4BYTEMIN so that it works with msvc.
519e4c23a 2026-09-30 [fa44643f65d6] inadvertently removed its circular-cleanup protection by fixing the finalizer ordering. This check-in fixes that. Spotted in [forum:ba4cb328a7|forum post 2026-09-30T14:59:13Z].
e32fbe0c2 2026-09-30 Import vec1 sources into directory ext/vec1/ of this project.
cdbfe6a93 2026-09-30 Do not inherit the OPFS SAHPool's xSleep method from the default VFS, as doing so can cause the thread to freeze. This VFS only deals with contention originating in the same thread, so xSleep() needs to be a no-op. Addresses [forum:3f0794c5d8|bug report 2026-09-30T12:52:54Z].
f4786666d 2026-09-30 JS: when disposing of a C struct instance, do not unmap the 'pointer' property interceptor until after all client-added finalizers have been called.
3b28aa1ce 2026-09-30 Fix the OPFS SAHPool VFS's xLock/xUnlock to properly deal with multiple handles to the same underlying file within the same JS thread. Addresses [forum:5e66a600ba6e57de|bug report 2026-09-30T10:49:15Z]. Also (unrelated but code-adjacent) make sure that the VFS releases all of its internal mappings when it's paused.
737c12a04 2026-09-30 Minor JS doc correction.
9fd5a0bc5 2026-09-30 Correct the xCheckReserveLock() impl of the OPFS SAHPool VFS to fix a corruption case involving multiple handles in the same JS thread to the same filename when one leaves a journal behind. Addresses [forum:b2fbb61642|bug report 2026-09-29T18:25:28Z].
226a2c0d6 2026-09-30 Generic internal JS cleanups. No functional changes. Update the preprocessor for the ability to use C-style comments in directive arguments.
3a11beb10 2026-09-29 Change the way the session module applies changesets containing two or more UPDATE changes that form a dependency loop in order to avoid triggering ON DELETE CASCADE actions.
a7d4cd04b 2026-09-29 Fix a harmless compiler warning in fts3ChecksumIndex().
34615b9c1 2026-09-29 Reset the nullRow flag on the pseudo-cursor on each iteration of the loop when the RHS of a LEFT JOIN is a multi-row VALUES clause.  Fix for [bugs:/info/2026-09-29T00:41:09Z|Bug 2026-09-29T00:41:09Z].  Problem introduced by check-in [a120c9235f125e05] with a missed opportunity to fix the problem at check-in [8c0f69e0e4ae0a44].
ad1bbfc2b 2026-09-29 OPFS SAHPool: more cleanly handle an init failure. Add an init option which tells it not to wipe the storage if initialization fails. Based on the discussion and patch in [forum:5664cd4baee50236|forum post 5664cd4b]. Minor doc updates in unrelated code.
1059bc8ea 2026-09-28 Fix a duplicate test case identifier label in speedtest1.c.
86876d2f6 2026-09-27 Enable the --column-metadata configuration flag in the 'autoconf' build. It was previously disabled with a comment that it changed how sqlite3.c was generated, but that's not the case. Addresses [bugs:2026-09-27T13:25:48Z|bug report 2026-09-27T13:25:48Z].
2acb2ea90 2026-09-26 Improvements to detection of invalid JSONB in the json_pretty() function. This is an enhancement, not a bug fix, as json_pretty() does not guarantee detection of invalid JSONB, as long as the invalid JSONB does not cause a memory error. [bugs:/info/2026-09-25T15:59:04Z|Bug 2026-09-25T15:59:04Z]. Test cases in TH3.
ac70487e1 2026-09-26 New assert()s added to demonstrate that calls to sqlite3_aggregate_context() within an xInverse() callback never return NULL.
f23756319 2026-09-26 Never let the SQLITE_FP_PRECISION_LIMIT exceed 100 million. [bugs:/info/2026-09-26T07:06:12Z|Bug 2026-09-26T07:06:12Z]
998173efc 2026-09-26 Update some long-dormant JS test code for refactoring-/renaming breakage induced since it was last used. Remove a separate long-dormant JS demo which cannot work with the current code.
7a5d84c68 2026-09-25 Avoid dropping an error code in fts5 contentless-delete mode after parsing an %_docize record. Report [bugs:/info/2026-09-25T15:52:10Z | 2026-09-25T15:52:10Z].
2c723787f 2026-09-25 Have RBU refuse to update any table with GENERATED columns. Bug report [bugs:/info/2026-09-25T10:43:02Z | 2026-09-25T10:43:02Z].
078d71402 2026-09-25 Fix 8 byte buffer overwrite that could occur when applying RBU updates to databases containing indexes with more than 16 columns. Report [bugs:/info/2026-09-25T11:18:49Z | 2026-09-25T11:18:49Z].
00830b281 2026-09-25 Fix some cases where fts3 integrity-check was not detecting corrupt databases. Report [bugs:/info/2026-09-25T11:18:11Z | 2026-09-25T11:18:11Z].
d21bd37c7 2026-09-24 Avoid a use-after-free problem in rtree triggered by an attacker manipulating the shadow table schema to ensure sqlite3_last_insert_rowid() returns 0 after certain INSERTs. Problem reported by Claude and Ada Logics.
2503dc618 2026-09-24 Avoid marking little-known extension function next_char() as SQLITE_INNOCUOUS by default.
6842d54eb 2026-09-24 Avoid potential buffer overwrite in debugging tool showwal when dealing with a wal file containing records with a very large number of fields.
f544d3599 2026-09-24 Avoid leaving an fts3 porter tokenizer cursor in an inconsistent state following an OOM error. At the moment, this does not cause problems because fts3 always frees a tokenizer cursor following an OOM. But it might if some other code used the porter tokenizer implementation.
4d577dfb3 2026-09-24 Fix an off-by-one error in sqlite3GetUInt32(). The only user-visible effect of fixing this problem is that the error message emitted for a corrupt database has changed in one obscure case.
c62a4430f 2026-09-24 Work around quirks in MSVC associated with [d046d5f4c6855].
28c6f996b 2026-09-24 Fix test case inaccuracy introduced by [4f4ca57309c82d9e].
e034ece5a 2026-09-24 In accordance with [https://www.unicode.org/versions/corrigendum9.html|Unicode Corrigendum #9], allow characters U+fffe and U+fffd to pass through unchanged. [bugs:/info/2026-09-23T02:39:21Z|Bug 2026-09-23T02:39:21Z].
fb58e3065 2026-09-24 Avoid truncating the argument of flag pragmas to 8 bits. [bugs:/info/2026-09-23T02:42:23Z|Bug 2026-09-23T02:42:23Z].
4b495f91a 2026-09-24 In date/time functions, the hour can be 24 as long as the minutes and seconds are zero. [bugs:/info/2026-09-23T02:44:48Z|Bug 2026-09-23T02:44:48Z]
9da2d2374 2026-09-23 The --escape mode for CSV should default to "off". [bugs:/info/2026-09-23T16:25:07Z|Bug 2026-09-23T16:25:07Z]
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
