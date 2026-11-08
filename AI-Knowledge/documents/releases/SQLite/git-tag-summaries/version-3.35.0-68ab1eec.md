# SQLite — Git tag version-3.35.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.35.0
Сравнение с предыдущим тегом: version-3.34.0

## Коммиты в диапазоне

```text
f1c43ea64 2021-03-12 Version 3.35.0
0ca23aa43 2021-03-12 Fix broken requirement marks.
9d59e3b1b 2021-03-12 Fix the ".read" command in the CLI so that SQLITE_OMIT_POPEN disables reading from a pipeline.
ab6098cfa 2021-03-12 Conform description of sqlite3changeset_op() arguments to implemented behavior, some reformatting. This is a comment-only change; no code is affected.
3ddc3809b 2021-03-11 Fix a Tcl object leak in test_session.c.
407cfe994 2021-03-11 Bug fix in appendvfs.c:  Adjust the size parameter for SQLITE_FCNTL_SIZE_HINT to account for the prefix.
632f0ed26 2021-03-11 Have the Tcl tests support environment variable SQLITE_TEST_PATTERN_LIST, so that if it is set it is interpreted as a list of patterns that are matched against tests file names. Only test files that match at least one pattern are run.
3fb7bd5ee 2021-03-10 Fix sanitizer complaint in fts3 code.
55b2e8b06 2021-03-10 Fix further sanitizer complaints in the fts5 code.
662a1426c 2021-03-10 Improved testcase() related the SQLITE_MAX_ATTACHED vs. SQLITE_MAX_DB problem.
4d17e3062 2021-03-10 Improvement to the ATTACH-abuse authorizer logic in fuzzcheck.
ba34b79f1 2021-03-10 Do not run avfs.test when testing SQLITE_OMIT_VIRTUALTABLE builds.
099b385d1 2021-03-10 Do not confuse the constant SQLITE_MAX_ATTACHED with the maximum number of schemas.  Add the new SQLITE_MAX_DB constant for the maximum number of schemas.  [forum:/forumpost/a006d86f72|Forum post a006d86f72].
bc3c4e083 2021-03-10 Fix test file avfs.test so that it works with SQLITE_DEFAULT_AUTOVACUUM builds. Do not run avfs.test under test permutation "journaltest".
3be2b860d 2021-03-10 Fix a few sanitizer complaints in fts5.
a1c467f51 2021-03-10 Fix a problem preventing wapptest from setting SQLITE_ENABLE_LOCKING_STYLE for OSX tests. Also modify the "Sanitize" configuration in releasetest_data.tcl to subsume test item 6g.
c5edbd1cf 2021-03-10 When shell has no .ar, fake its effect w.r.t. page_size and table creation/filling.
a94c48458 2021-03-09 Add appendvfs.c to the MSVC makefile.
4049ede97 2021-03-09 Update a comment in btree.h.
0db20c490 2021-03-09 Fix a bad comment (copy-paste error) in the byte code engine.  No code changes.
45e4cb8e7 2021-03-09 Improved comments on the NOT NULL strength reduction optimization.
6d0053cfa 2021-03-09 Extra comments and testcase() macros associated with the new sqlite3ParserAddCleanup() mechanism.  No changes to release builds.
e7a377046 2021-03-09 Add --enable-math to the amalgamation autoconf.  On be default.  Improved logging of the amalgamation autoconf.
42c93b5e9 2021-03-09 Math functions are enabled by default in the main configure script.
24ec37c3b 2021-03-09 Improvements to the configure script.  Math functions are enabled by --enable-all.
657a7a66c 2021-03-09 Update the authorizer in fuzzcheck to align with dbsqlfuzz.
ddf497206 2021-03-08 Add tests for too-tiny appended DBs, clarify align macro.
52a075315 2021-03-08 Add test cases for ALTER TABLE.
e58b2b4a8 2021-03-08 Fix a bad assert in RENAME COLUMN. dbsqlfuzz 3f0a7245b69cd08617d7d7781ebaedb0fe765a93.
baca9807f 2021-03-08 Fix a harmless compiler warning in appendvfs.c
7ae054996 2021-03-08 Enable internal functions for fuzzcheck.
b47e4c281 2021-03-08 Added test/avfs.test (missing from branch merge for some reason.)
e02189095 2021-03-08 Require that the appendvfs suffix mark indicate that the appended database begins at an offset that is a muliple of 512 and that the appended database contains at least 512 bytes.
1e6f33464 2021-03-08 Correct the precendence order for rules that determine how a database is opened by appendvfs when a database is appended to another database.
40942f22f 2021-03-08 Minor comment and formatting changes.
5777380d1 2021-03-08 Add tests for sqlite3 shell with -append flag.
7e398c04f 2021-03-07 Add grow/shrink tests. Fix truncate bug. Make appendvfs.c easier to inspect.
1b22ad8ae 2021-03-06 Create initial tests for appendvfs, and make it available as a statically loaded extension.
4bb4293b2 2021-03-06 Limit parenthesis nesting depth in FTS3 expressions to SQLITE_MAX_EXPR_DEPTH.
7f8653a25 2021-03-06 Ensure the correct collation sequence is used for comparisons when delimiting a RANGE window.
fa9011ec7 2021-03-06 Fix a crash in fts3 that could occur when running a NEAR query on a corrupt database.
747cc9425 2021-03-06 Fix a possible NULL pointer dereference when applying a DROP COLUMN to a corrupt database schema.  dbsqlfuzz 419aa525df93db6e463772c686ac6da27b46da9e
feecc9f54 2021-03-05 Fix appendvfs bug exposed by docsapp build (in docsrc), and tighten/revise published behavior.
70149ba47 2021-03-05 Modify the SQLITE_DBCONFIG_ENABLE_VIEW option so that it always permits TEMP views, just as SQLITE_DBCONFIG_ENABLE_TRIGGER always permits TEMP triggers.
0d08072b6 2021-03-05 Fix another problem with RETURNING clauses in UPDATEs against tables with virtual columns.
a7e16a2f0 2021-03-05 Fix an assert() failure that could be triggered by a correlated sub-query in a RETURNING clause.
bc7819d17 2021-03-05 Fix the processing of implied LIMIT clauses when flattening a compound query.
b14d14696 2021-03-05 Create new branch named "appendvfs_tighten"
05edf729f 2021-03-04 Mark the NotUsed parameter to the dropColumnFunc() function as unused, to avoid a harmless compiler warning.
91be05a91 2021-03-04 Put ALWAYS() on a branch that is now always true because of changes in OOM behavior due to check-in [9adf6e2469d18bc3].
39b6bd5e1 2021-03-04 Update shell.c.in so that SQLITE_SHELL_IS_UTF8 is set to 0 if the -municode option is passed to gcc on windows.
5f0922b96 2021-03-04 Remove a branch made unreachable by check-in [e893f88750ea64d4].
e8dd6a4e7 2021-03-04 Fix a segfault that could occur following an OOM condition.
aae0f74e6 2021-03-04 Earlier detection of a misplaced ORDER BY or LIMIT clause in a compound SELECT.  This prevents problems in recursive CTEs with multiple recursive terms in which there is an ORDER BY or LIMIT clause on the last non-recursive term.
50f9f6c64 2021-03-04 Fix a crash that could occur if a sub-select inside an EXISTS expression features an ORDER BY clause containing one or more window functions.
8718f0b61 2021-03-03 Fix a buffer overrun that could occur in fts5 when running a prefix query against a corrupt db.
0bff34aea 2021-03-03 Remove the --timeout option from the valgrindfuzz Makefile target.
c6920cdb0 2021-03-03 Fix a case where fts3 was erroneously reporting corruption.
fad1ad052 2021-03-03 Fix a harmless assertion fault resulting from [6e6b3729e0549de0] that was discovered by dbsqlfuzz.  Enhance .selecttrace output to show omitted ORDER BY clauses.  New dbsqlfuzz test cases added.
3083d5f5e 2021-03-03 Fix a problem with using ALTER TABLE commands on database schemas that contain expressions of the form "<expr> NOT NULL" or "<expr> IS NULL" that can be evaluated at prepare time.
bb05976da 2021-03-02 Cast a string size variable to 64-bit to avoid any possibility of integer overflow.
898ec7927 2021-03-02 Limit the size of the exponent input in the second argument to the ieee754() SQL function, to avoid integer overflow. Ticket [22dea1cfdb9151e4].
730629680 2021-03-02 Change the timeout for test case "valgrindfuzz" from 600 seconds to 1200.
eefef9ae8 2021-03-02 Do not run test file windowpushd.test as part of the "no_optimization" permutation.
1b1a1dda9 2021-03-02 Add ALWAYS() to an always-true conditional.
2d7a691fb 2021-03-01 Add #ifndef macros so that the build works again with -DSQLITE_OMIT_AUTHORIZATION and -DSQLITE_OMIT_WINDOWFUNC.
1f9f57669 2021-03-01 Fix another msan complain triggered by a corrupt database.
1e06c70eb 2021-02-28 Initialize extra field in PgHdr1 to fix an msan complaint.
a3944bc4f 2021-02-27 Add OOM test case associated with the fix in the previous commit.
676c869d5 2021-02-27 Remove a NEVER() that might sometimes be tree following an OOM.
15de3ce9a 2021-02-26 Fix a segfault that could occur when optimizing a NOT NULL constraint against an IPK column of a sub-query.
8ddf68626 2021-02-26 Attempt to optimize "x IS NULL" and "x IS NOT NULL" expressions when x is a column with a NOT NULL constraint.
4b17455ab 2021-02-26 Minor simplification in resolve.c.
b3617e9d2 2021-02-25 Fix test case in altercorrupt.test so that it works with SQLITE_ENABLE_OVERSIZE_CELL_CHECK builds.
a4656e390 2021-02-25 Fix a problem with UPDATE and DELETE statements that use both INDEXED BY and LIMIT clauses in SQLITE_ENABLE_UPDATE_DELETE_LIMIT builds.
3dc864b57 2021-02-25 Fix handling of INSERT on views with implicitly named hidden columns in SQLITE_ENABLE_HIDDEN_COLUMNS builds.
ce5de60ff 2021-02-25 Ensure that tests like "rbu.test" and "notify2.test" that are only run by specific configurations during release testing are run for both release and debug versions of the tests.
34a224a13 2021-02-23 Further tests for the push-down optimization with window functions.
903fdd483 2021-02-22 Allow WHERE terms to be pushed down into sub-queries that contain window functions, provided that the WHERE term is made up of entirely of constants and copies of expressions found in the PARTITION BY clauses of all window functions in the sub-query.
dee1cb300 2021-02-22 Add a few simple test cases for MATERIALIZED and NOT MATERIALIZED.
f43fef29b 2021-02-22 When a sub-transaction is released, if no pages required by containing sub-transactions were journaled, truncate the statement journal. This might prevent out-of-control statement journal growth in some cases.
606411bf9 2021-02-22 Add an ALWAYS() on a branch that is now unreachable.
17267fe39 2021-02-22 Fix inverted logic regarding the materialization hint on the push-down optimization.
745912efa 2021-02-22 Add the AS MATERIALIZED and AS NOT MATERIALIZED syntax that works like it does in PostgreSQL.
a79e2a2d2 2021-02-21 Materialize any CTE that is used more than once.
7601294ad 2021-02-21 Rename the "struct SrcList_item" object to the more succinct "SrcItem". This is a symbolic change only.  The logic is unmodified.
5abe1d3d5 2021-02-21 Simplified resolution of CTE names.  Slightly faster and about 100 bytes of code smaller.
1862271f7 2021-02-20 Performance improvement in resolving the INDEXED BY index name for the common case where there is no INDEXED BY clause.
1e0cfd718 2021-02-20 Fix a case where FTS3/4 could pass a NULL pointer to memcpy() when handling a corrupt db.
1e25d20cc 2021-02-20 Update sqlite3changeset_apply_v2() so that it handles no-op UPDATE changes (UPDATE changes that modify no columns). This fixes a regression introduced by [e4ccfac09b]. Also modify sqlite3rebaser_rebase() so that it does not output changesets containing such UPDATEs.
f824b41e6 2021-02-20 Break out the Cte object from the With object.  This will make it simpler to add new kinds of Cte objects (ex: DML statements) and/or MATERIALIZED keywords in the future.  It brings trunk into closer alignment with the experimental as-materialize branch.
271d7c267 2021-02-20 Simplification to where.c manually cherrypicked from the as-materialize branch.
578277c25 2021-02-19 Fix another problem handling corrupt database files in the ALTER TABLE DROP COLUMN code.
d97471e1a 2021-02-19 Add tests for ALTER TABLE DROP COLUMN commands.
f4a72788a 2021-02-19 Fix a crash that could occur in ALTER TABLE DROP COLUMN if the sqlite_schema table was corrupt.
60fe2352f 2021-02-19 Omit an branch made unreachable by the improved error message from dropping the last column of a table.
329cb9eb8 2021-02-19 The COLUMN keyword in ALTER TABLE DROP COLUMN is optional.
239c84fc6 2021-02-19 Give a better error message on DROP COLUMN when attempting to drop the last column of a table.
c90fa01db 2021-02-19 Add a NEVER() to an unreachable branch in the DROP COLUMN logic.
0336140cd 2021-02-18 Add missing VdbeCoverage() macros.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
