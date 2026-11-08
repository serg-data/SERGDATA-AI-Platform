# SQLite — Git tag version-3.39.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.39.0
Сравнение с предыдущим тегом: version-3.38.0

## Коммиты в диапазоне

```text
47d8c40ca 2022-06-25 Version 3.39.0
a36fedbda 2022-06-25 Change a harmless assert() into a testcase().  The actually test case code is in TH3.  Fix for the problem described at [forum:/info/ed29e196d5c4f3d5|forum post ed29e196d5c4f3d5].
86bc5e41b 2022-06-24 Fix a harmless UBSAN warning associated with PRAGMA schema_version found by OSSFuzz.
a5ec23a70 2022-06-24 In sqlite3WhereBegin, do not proceed with coding the loop if an error is detected as part of WHERE expression analysis.
2a40a882f 2022-06-24 A minor fix to test/fuzzinvariants.c so that it works even with column names that originally contain a ':' and that are disambiguated.
9efc61860 2022-06-23 Minor correction to a comment.  No code changes.
2b0ea0204 2022-06-22 Enhance the TCL scrip that generates sqlite3-all.c so that it outputs all text in its original order.
f221e4b5d 2022-06-22 Fix requirements marks that changed due to typo fixes in the documentation.
cf5cab01c 2022-06-22 More comment fixes.  No changes to code.
0751fc3b8 2022-06-22 Allow more line with on the debugging output for SrcItem elements in the parse tree.  This affects debugging builds only and is a no-op for production builds.
2591cfb67 2022-06-22 Additional enhancements to comments.  No changes to code.
b88574470 2022-06-22 Give dbtotxt an option to prepend .open --hexdb
861ac67a9 2022-06-22 Fix a typo in a comment.  No changes to code.
8c44962aa 2022-06-21 Disable the short-cut query planner if the NOT INDEXED modifier is used. [forum:/forumpost/454d706296|Forum post 454d706296].
b9294de1e 2022-06-21 Allow a HAVING clause on any aggregate query, even if there is no GROUP BY clause.  This brings SQLite into closer agreement with PostgreSQL and fixes the concern raised by [forum:/forumpost/1a7fea4651|forum post 1a7fea4651].
4af6462fb 2022-06-20 Add an ALWAYS() macro to an always-true branch.
436c28a26 2022-06-20 Do not allow FROM-clause terms on the left side of a RIGHT or FULL JOIN to be reordered. [forum:/forumpost/6650cd40b5634f35|forum post 6650cd40b5634f35]. This is probably more strict that necessary to get correct behavior, but for the first release that supports RIGHT/FULL JOIN it is perhaps better to be correct than fast.  A less strict constraint might be to prohibit FROM-clause terms that originate on the left side of a RIGHT JOIN from crossing from the right side to the left side of a LEFT JOIN.  Revisit this later.
d7480403b 2022-06-20 Do not allow an ON clause to references tables to its right if there is a RIGHT or LEFT join anywhere in the query.  Other RDBMSes prohibit this always, but SQLite must allow ON clauses to reference tables to their right for legacy compatibility, unless there is a RIGHT or LEFT join someplace in the query, in which case there is no legacy to support.
ae8776e09 2022-06-20 The fix at [cab9b4cccd13bf0a] was incomplete, as demonstrated by [forum:/forumpost/57bdf2217d|forum post 57bdf2217d].  This check-in should complete the fix.
1d4976815 2022-06-19 Follow-up to check-in [0057bbb508e7662b] - ensure that the database page has been initialized prior to continuing with the optimization.  If the page is not initialized, that indicates that the database is corrupt. dbsqlfuzz 09ee46becd5e6d1b2a55c9f8ad767335a90aadb0.
13736999d 2022-06-18 Enable query invariant checking in fuzzcheck by default.  There is no way to turn it off.  Update the invariant checking logic to be consistant with dbsqlfuzz.
d0d21f556 2022-06-18 Abandon a query-invariant check in fuzzcheck if the call to sqlite3_bind_value() returns anything other than SQLITE_OK or SQLITE_RANGE.
8fa6206bc 2022-06-18 In the --query-invariants option of fuzzcheck, correctly deal with OOMs causing the return value of sqlite3_column_name() to be NULL.
01156ec1c 2022-06-17 Fix the OP_Concat operator such that when concatenating a BLOB with an odd number of bytes on a database that is UTF16, the size of the resulting string is reduced to a multiple of two.
c2beb0d8f 2022-06-17 Omit the --query-invariants processing in fuzzcheck for queries that contain the implies_nonnull_row() test function.
f26e45139 2022-06-17 Do not run --query-invariants on statements that make use of sqlite_offset().
ea64cb31a 2022-06-17 Allow integers and floating point numbers to compare equal.
63880362e 2022-06-17 Improve query-invariants to the point that it would have discovered the [f23a429d4153518d] bug if that bug had not already been fixed.
c68fb8475 2022-06-17 Only run query-invariant checks after the original query has run to completion, so that we know it does not error-out on a subsequent row.
36f904f06 2022-06-17 Fix the virtual table detection mechanism to avoid false-positives that were blocking all failures.  Then fix a few of the additional problems that are revealed by that fix.  More fixes are needed.
6efabd6cd 2022-06-17 Fix the new --query-invariants option on fuzzcheck so that it does not use an unprotected sqlite3_value object as an argument to sqlite3_value_int64().
2a7aff93e 2022-06-17 Avoid omitting the rhs of FULL JOINs in cases where it is only correct to omit the rhs of a LEFT JOIN.
3e245bcef 2022-06-16 Minor fix to the query invariant testing logic of fuzzcheck.
8f9261a8e 2022-06-15 Improvements to query invariants in fuzzcheck.
e3bf2c8e9 2022-06-15 Improvements to query invariant checking in fuzzcheck.
dba3a5ab8 2022-06-15 When running an incremental vacuum, detect growth in the size of the database file (which can only occur if the file is corrupt) and fail with SQLITE_CORRUPT.
10c5341c7 2022-06-15 Dbsqlfuzz discovered a case where a bytecode branch is in fact taken, so change the designator from VdbeCoverageNeverTaken() to VdbeCoverage().  Test case in TH3.
0c278c3d7 2022-06-15 Add the --query-invariants flag to fuzzcheck.  The query invariant checks are only run if that flag is enabled.
a913f9b99 2022-06-15 Improvements to query invariant testing.  Almost working now.
27a242c63 2022-06-14 Fix the OP_NullRow opcode so that it works even if it applied to an ephemeral cursor that has not yet been created.
bbf71138c 2022-06-14 Add missing SQLITE_FCNTL_SIZE_HINT call to a path taken during transaction rollback.
a1f79dae9 2022-06-14 Attempt to enhance fuzzcheck to do some simple invariant testing on queries. This is an incremental check-in for a work-in-progress.
92d1afba9 2022-06-13 Do not remove the EP_CanBeNull flag from expressions during a LEFT JOIN strength reduction if the query also contains a RIGHT JOIN. Fix for the problem identified by [forum/forumpost/b40696f50145d21c|forum post b40696f50145d21c].
1cc5c4ac8 2022-06-10 The same restrictions on the use of WHERE clause terms to drive indexes in the presence of RIGHT JOINs also apply to the use of WHERE clause terms to manufacture automatic indexes.  This fixes a problem identified by [forum:/forumpost/51e6959f61|forum post 51e6959f61].
e45b87a9b 2022-06-10 fiddle: minor style tweaks, including using swapped colors for the input/output fields to help (hopefully) reduce the "which field is which?" dissonance.
958fcd417 2022-06-10 Do not allow constant propagation between WHERE-clause terms and ON-clause terms as this can confuse RIGHT JOIN.  Fix for the problem reported by [forum:/forumpost/8e4c352937e82929|forum post 8e4c352937e82929].
a27e350b6 2022-06-10 Fix a faulty assert() statement identified by [forum:/forumpost/0b91a75039|forum post 0b91a75039].
0c2b00b0d 2022-06-10 fiddle: modernized the UI based on related code in fossil's /pikchrshow. Changed the color scheme to match sqlite.org.
e5dea2848 2022-06-09 Prevent subtype values from slipping across a subquery boundry when the subquery is implemented as a co-routine.
8878f8a8d 2022-06-09 The subtype of a value should not propagate across a subquery boundary. Proposed fix for the problem reported by [forum:/forumpost/3d9caa45cbe38c78|forum post 3d9caa45cbe38c78]. Additional works is needed as not all cases are covered.
048366800 2022-06-08 Move an #ifdef in shell.c to avoid a harmless "unused function" compiler warning.
0a841a2b8 2022-06-08 Avoid zeroing the value returned by sqlite3_changes() when a DML statement is automatically reprepared in sqlite3_step().
8a5469b6f 2022-06-08 Improved comments on the new query flattener restriction of the previous check-in.  Also a NEVER() macro on an unreachable branch.
5c118e394 2022-06-08 Add restriction (29) to the query flattener - do not allow flattening that would leave both EP_InnerON and EP_OuterON constraints on the same join term.
a341bae94 2022-06-08 New test cases refute check-in [3f45007d544e5f78].
093dd41e9 2022-06-08 Do not allow a partial index scan on the left table of a RIGHT JOIN, because since the index is partial, some rows will be omitted from the scan, and those rows will subsequently be picked up by the no-match logic in the right-join post-processing loop. [forum:/forumpost/c4676c4956|forum post c4676c4956].
f6bee94e2 2022-06-08 Minor fix to test/index9.test so that it can be invoked with other index tests using a wildcard.
644817721 2022-06-08 Update the routine that determines whether or not a partial index can be used so that it is not specific to LEFT JOIN.
33b2cb9ae 2022-06-07 Fix the query flattener to deal with a RIGHT JOIN corner case described by [forum:/forumpost/323f86cc30|forum post 323f86cc30].
bb1369037 2022-06-07 Test cases for [forum:/forumpost/323f86cc30|forum post 323f86cc30] added to join8.test, though commented out so that they do not (yet) run.
d580bea7d 2022-06-07 Preserve the database encoding on the CAST operator in the sqlite3ValueFromExpr() routine. [forum:/forumpost/800eecf5e6cdc3f4|Forum thread 800eecf5e6cdc3f4]. Test case in TH3.
16828c8c1 2022-06-06 More precise determination of when a WHERE/ON clause term can be used as an indexed join constraint.  Testcase macros added to ensure test coverage.
93c4087ff 2022-06-06 Extra test cases for outer joins.
c18fc6134 2022-06-06 Do not allow a WHERE clause constraint to be used to drive an index for the right operand of a RIGHT JOIN, since this can cause problem if the constraint implies a not-NULL value for one of the columns for the left operand of the same join.  See [forum:/forumpost/206d99a16dd9212f|forum post 206d99a16dd9212f].
8fca1c704 2022-06-06 fiddle: replaced the huge file selection widget with a smaller proxy button.
fd80fa9b6 2022-06-06 Fix a test case in fts3corrupt6.test. Was failing due to [f1dfbc4f].
626aa48c2 2022-06-06 shell: in WASM mode, permit ATTACH because the filesystem is a virtual sandbox and ATTACH can be used to provide more import/export options. Minor doc updates in sqlite3-api.js.
f3d6e8fd6 2022-06-05 In CLI, drop .dbinfo command when build options prevent it from working.
b61c2424d 2022-06-05 Create new branch named "dbinfo-guard"
93a4b411e 2022-06-03 Fix to test case in fts3corrupt.test. No changes to source code.
181d75ef9 2022-06-03 Fix a 1-byte overread in fts3 that could occur when processing corrupt records.
410fac35d 2022-06-02 Fix a problem with flattening and window functions causing an "IS <column>" to be transformed to "IS TRUE" or "IS FALSE" when <column> is a view or sub-select expression that is the literal value "TRUE" or "FALSE".
bf154369e 2022-06-02 Avoid a direct use of abort() in debug builds to prevent a compilation issue for Windows CE.
486191603 2022-06-01 New test cases for row values and RIGHT JOIN.
4e5aeb54f 2022-06-01 fiddle: added another UI element to the list of those which are disabled during long-running activities. Added DB.close() binding to the Worker-based wasm binding.
a5d06a3d5 2022-06-01 Ensure that all necessary row-value subqueries are invoked while running the right-join post processing.
23aa8ff4d 2022-06-01 Minor tweaks to, and consolidation of, the wasm-related build flags.
f74f4ed5b 2022-06-01 Fix a minor problem in the Tcl "incrblob" command. This does not affect the SQLite core.
0f4b534b6 2022-06-01 Candidate fix for the problem with row-value WHERE clause constraints on a RIGHT JOIN.
6d013d890 2022-06-01 Only include the code for sqlite_offset() if compiled with -DSQLITE_ENABLE_OFFSET_SQL_FUNC.
1324b2830 2022-06-01 Fix a typo in a comment in a test case.  No changes to code.
0286cdbca 2022-06-01 Additional enhancements to the test cases.
47b4969e2 2022-06-01 Fix test cases in the previous check-in to make them postgres-compatible.
36c19f779 2022-06-01 Test case for [forum:/forumpost/087de2d9ec|forum post 087de2d9ec] showing a problem when a row-value constraint is used with RIGHT JOIN.
ea7a4e4fb 2022-06-01 The Worker-specific variants of the most significant DB-class JS bindings are implemented, most notably various uses of DB.exec().
645682a7c 2022-06-01 Move the sqlite_offset() function implementation to be an in-line function, thereby avoiding special case code and freeing up a bit in the FuncDef.flags field.
6ffa89588 2022-06-01 Initial proof of concept code for a JavaScript binding which runs in the main window thread but acts on a db handle running in a Worker thread. Expanded the DB.exec() and DB() constructor to simplify certain use cases.
bff17db43 2022-06-01 Initial bits for a JS API variant in which the client operates in the main thread and sqlite3 in a Worker. This is far from complete.
c7fc08f69 2022-05-31 New FULL JOIN test cases.  No changes to code.
aa03c6959 2022-05-31 More JOIN test cases inspired by the problem fixed in [3869fd9a2b9483cb].
f51672a94 2022-05-31 Fix an assert that is incorrect for a corrupt database.
d69820c42 2022-05-31 Many new PG-confirmed test cases in joinD.test.
c9dfe2b80 2022-05-31 Add back in a test case for ON-clauses that was removed yesterday by [3869fd9a2b9483cbf] but which turned out to be necessary after all.
b1f08bc69 2022-05-31 Add test cases for [forum:/forumpost/c2554d560bac97c5|forum post c2554d560bac97c5].
5fd9f0329 2022-05-31 Updated the wasm builds to generate gzip'ed copies of relevant files to take advantage of althttpd's new capability of substituting gzip files in place of requested files. This cuts over-the-wire size of the fiddle app by more than half.
404bf6bac 2022-05-30 For an outer join, then ON-clause constraints need to be evaluated at just the right moment - not too early and not too late.  Fix for the problem reported by [forum:/forumpost/3902c7b833|forum post 3902c7b833].
1943005f6 2022-05-28 Apply the UPDATE-FROM file from check-in [98b3816bbaf539ea] to update-delete-limit builds.
1a66ff359 2022-05-28 fiddle: changed the internal key of the session/local storage to avoid conflicts with the pikchr fiddle app (which is derived from this one) when running from the same HTTP origin as an instance of that app in a dev environment.
e9ab04a44 2022-05-28 fiddle: corrected a piece of far-corner-case error handling and made the various checkbox config options persistent.
5af8a86d6 2022-05-27 Mark an always-true conditional as ALWAYS().
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
