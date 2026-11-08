# SQLite — Git tag version-3.30.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.30.0
Сравнение с предыдущим тегом: нет предыдущего тега в локальном списке

## Коммиты в диапазоне

```text
228a52d97 2019-10-04 Version 3.30.0
6117a1732 2019-10-03 Avoid running a couple of tests in affinity2.test as part of the valgrind permutations, as the way floating point computations are simulated by valgrind causes them to fail.
d1c472dab 2019-10-03 Increase the precision of floating point value display in VDBE debugging output.  No changes to normally deployed code.
b008e4d74 2019-10-03 Fix some test script issues that come up with SQLITE_OMIT_VIRTUALTABLE builds.
367b8d7aa 2019-10-03 Fix issues with command line invocation of wapptest.tcl.
9a50f4c72 2019-10-02 Update error detection logic in releasetest.tcl to account for new output formats in USAN.
f0578823d 2019-10-02 Update corruptM.test to account for the fact that the database schema may be loaded from within the "sqlite3" command for some test permutations.
23d3f5d66 2019-10-02 Fix a long-standing problem in fts4 incrmental merge.
e2b7a7693 2019-10-02 Disable sqlite3_drop_module() tests when virtual tables are omitted from the build.
cfee884e7 2019-10-01 Remove references to test scripts analyzeA.test and analyzeB.test from permutations.test, since those test modules no longer exist.
5e81e9fda 2019-09-30 The nodeReaderInit() function in FTS3 may not assume that the node is non-empty.
905d4729d 2019-09-28 Add missing comment to constant definitions.
018dbb17a 2019-09-28 Improvements to a comment.  No code changes.
5c0666d9e 2019-09-28 In FTS3/4, the poslist end marker must be larger than any other possible poslist value, even on a corrupt poslist.
5f419b3bb 2019-09-27 Update requirement marks due to changes in documentation wording.
e4079e1fc 2019-09-27 Allow compile-time options -DHAVE_GETHOSTUUID=0 and -DHAVE_GETHOSTUUID=1.
ebc640848 2019-09-27 Alternative implementation of the previous check-in which is testable.
818a3b548 2019-09-27 Fix sqlite3ExprCompare() so that it ignores differences in the Expr.iTable field for IN operators, as otherwise it can lead to false negatives, which is usually harmless, but can cause problems for an assert() in the window function logic.
7971b7fe9 2019-09-26 More minor test file fixes.
91f34eab2 2019-09-26 Allow DROP TABLE to work on tables name "sqlite_parameters" just as it does with tables named "sqlite_stat%".  Fix for the ".parameter clear" command in the shell.
9d30c8ff8 2019-09-26 Minor fix for test file indexexpr1.test.
ec39707fe 2019-09-26 New dbsqlfuzz cases added to test/fuzzdata8.db.
d79cd92b2 2019-09-26 Test for an OOM condition in resolveAlias().
a51ddb1ed 2019-09-26 Fix a window-functions problem that could occur if an ORDER BY clause contains an alias for a window-function that is not a top-level expression.
b19131a8c 2019-09-25 Add a missing VdbeCoverage() macro.
2829df082 2019-09-25 Remove an unused variable.
e7579a53f 2019-09-25 Further simplifications to window-function code.
edf8a7bf5 2019-09-25 In the previous check-in, the variable should be openMode, not openFlags.
1116b1785 2019-09-25 In the unix VFS layer, do not attempt to chown() the journal to be the same as the database if running in 8+3 filename mode.  Also, update the comments on the chown() attempt to be more precise.
c5b35ae56 2019-09-25 Simplifications to the window-function code.
37d296a71 2019-09-24 Bug fixes for window frames of the form (... RANGE BETWEEN b PRECEDING AND a PRECEDING) or (... RANGE a FOLLOWING AND b FOLLOWING) where (a > b).
5776ee5cf 2019-09-23 Omit the sqlite3IntTokens array constant for a code simplification.
7ca1347f5 2019-09-23 When a scalar subquery has a pre-existing "LIMIT X" then change it to "LIMIT X<>0" rather than just "LIMIT 1" so that if X is 0 the limit will still be zero.  Ticket [99cd4807dc03f178]
b7fc7c855 2019-09-21 Fix a harmless unused variable warning in the test logic.
e39f388eb 2019-09-21 Fix harmless compiler warnings.
8c9bcb232 2019-09-21 Allow SQLite to omit redundant ORDER BY sorts in the case where a SELECT statement has GROUP BY and ORDER BY clauses that use the same expressions, even when the ORDER BY expressions are marked "DESC".
e47d5ca73 2019-09-21 Add --multithread, --serialized, and --singlethread options to the speed-check.sh test script.
af9b58b33 2019-09-20 Simplify the fix in the previous commit.
ed09dddec 2019-09-20 Fix a problem with queries containing a min() or max() function for which the FILTER clause excludes all rows.
14e3e2277 2019-09-19 Fix an assert() in fts3 that could fail when accessing a corrupt database.
6d2566dfc 2019-09-18 Always clear the temporary register cache after coding a subroutine.
572b0ddde 2019-09-18 Add extra tests for the handling of corrupt records in fts3.
aa16c603a 2019-09-18 Fix another potential "jump depends on uninitialized value" warning.
4b48c7272 2019-09-18 Fix a "jump depends on unititialized value" valgrind error in fts5 triggered by corrupt database records.
9d7028402 2019-09-18 Fix an OOB read in the INSTR() function introduced yesterday by check-in [3fb40f518086c1e8] and detected by OSSFuzz.  The test case is in TH3.
ec722c108 2019-09-17 Do not change the OP_String8 opcode into OP_String until *after* any necessary encoding conversions are accomplished.  Otherwise, a rerun of the prepared statement after an OOM can result in errors.  Test case in TH3.
e691dcb50 2019-09-17 Test cases for ticket [587791f92620090e]
97b025059 2019-09-17 Fix the instr() SQL function so that it makes a copy of its argument before changing the datatype, since the datatype affects processing. Also fix the sqlite3_value_text() routine so that it always works even for values obtained form sqlite3_value_dup().  Ticket [587791f92620090e]
70738712d 2019-09-16 Improved type information display when tracing VDBE execution.
91f473b5c 2019-09-16 Do not attempt the LIKE optimization for non-text columns and a pattern prefix of "-".  Ticket [0f0428096f17252a]
130dbc3d9 2019-09-16 Add recent interesting cases from dbsqlfuzz.
2ad35d980 2019-09-16 Documentation updates for the SQLITE_DIRECTONLY flag.
b42eb3571 2019-09-16 Fix a problem with processing CTEs that use a WINDOW clause.
8cce6b831 2019-09-14 Add the --no-rowids option to the ".recover" command.
d44c617ad 2019-09-14 Extra comments on fields of the Window object.
fab5b0739 2019-09-14 Fix the windows inverse function on the JSON aggregates.
51a75aaa7 2019-09-13 Fix a problem with using json1 window functions with an EXCLUDE clause.
e087a7c35 2019-09-13 Fix the windowB test module so that it works even if SQLite is built without JSON support.
477f1f12e 2019-09-13 Fix a typo in the carray extension header comment - the comment that serves as the documentation to this extension.
01a3b6b1b 2019-09-13 Change the meaning of the SQLITE_SUBTYPE flag so that it indicates that the user-defined function cares about the subtypes of its arguments.
3f3f2c735 2019-09-13 Ensure that the idxStr for FTS5 is always zero-terminated. Fix for check-in [e6db945454a0dae2]
fbb9a5b1e 2019-09-13 Fix harmless compiler warnings.
685b2ee0c 2019-09-12 Allow fts5 to filter on multiple MATCH clauses in a single scan.
acf6e08d2 2019-09-11 Fix typo for one instance of line number handling in the Lemon tool.
c204d81a6 2019-09-10 Enhance treeview to show SOFT-COLLATE for TK_COLLATE operators that omit the EP_Collate flag.
fa5083491 2019-09-10 Ensure the columns of views and sub-queries maintain their implicit collation sequences when the "push-down" optimization is applied. Fix for [18458b1a].
e08663946 2019-09-09 Ensure the columns of views and sub-selects in the FROM clause of a select are always assigned implicit collation sequences, just as table columns are. Possible fix for [a7debbe0].
e2ba6df9f 2019-09-07 Add the SQLITE_SUBTYPE flag, which can be passed to sqlite3_create_function() and similar to indicate to the core that a user function is likely to use sqlite3_result_subtype().
1a97c413f 2019-09-04 Fix handling of NULL, text and blob values in window queries that use "RANGE BETWEEN A FOLLOWING AND B FOLLOWING", or "B PRECEDING AND A PRECEDING", where A>B.
7dc3547ee 2019-09-03 Updates to the default settings in Makefile.linux-gcc.
c7d12f4ad 2019-09-03 When we play games with COLLATE in order to commute an operator in the WHERE clause processing, be sure not to use the commuted operator to qualify a partial index, as insufficient COLLATE information is preserved to verify that the expression will correctly qualify the index. Ticket [767a8cbc6d20bd68]
4fc836546 2019-09-02 Fix a bug introduced earlier today by check-in [88833a9c2849c959]. Ticket [29f635e0af71234b]
229ae1ae7 2019-09-02 Fix a potential crash in fts5 caused by using an auxiliary function on a "special" query like '*id' or '*reads'.
dd668c26b 2019-09-02 When applying the IN_INDEX_NOOP optimization and the LHS has REAL affinity, also apply REAL affinity to each element of the RHS. Ticket [2841e99d104c6436].
0167ef202 2019-09-02 Fix an obsolete comment that defines the meaning of one of the parameters to the sqlite3FindInIndex() subroutine.  No changes to code.
bffdd6363 2019-09-02 When computing an expression value for an index-on-expression or a CHECK constraint and the expressions uses a REAL table column, but the value of that column is an integer (in other words, when it is using the store-real-as-integer optimization) be sure to promote the value to real before evaluating the expression.  Ticket [57af00b6642ecd68].
cc80db69e 2019-09-01 Remove an obsolete paragraph from the OP_Column documentation.  No code changes.
35a38e083 2019-08-31 Fix a harmless compiler warning.
81d25cf53 2019-08-31 Mark new VDBE branches never taken.
80f6bfc06 2019-08-31 Improvements to the algorithm that determines which SELECT in a sequence of nested SELECT statements that an aggregate function belongs to.  This resolves an issue identified by dbsqlfuzz.
f66bfcb74 2019-08-31 If a DELETE trigger fired by an UPDATE OR REPLACE statement deletes the row being updated, do not attempt to proceed with the original UPDATE operation. Fix for [d6a0fbc1].
6a19865ff 2019-08-31 Remove some affinity tests that became unreachable due to the prior change.
7314495ff 2019-08-30 When the affinity of a table column is INT or REAL, make the affinity of corresponding index columns NUMERIC.  This increases the precision of index lookups for large numbers so that it matches the precision of ordinary comparison operators.  Ticket [40812aea1fde9594]
a7ce167e5 2019-08-30 Make sure OP_RealAffinity has been applied to all columns of type REAL in the excluded.* pseudo-table of an UPSERT. Ticket [5a3dba8104421320]
efb5f9a17 2019-08-30 Improvements to VDBE tracing.  No changes to code in normal deliverables.
9889ede28 2019-08-30 Add test case to window8.test. Also fix an error in a comment in window.c.
db3a32ed1 2019-08-30 Back out the change at [47cd634c98b502d4] which was incorrect.  Add a test case so that we don't accidently back out that change again.
1cac1766d 2019-08-30 Add further comments to window.c.
ac6627327 2019-08-30 New test cases for window functions with RANGE BETWEEN and DESC NULLS FIRST.
8b47f5208 2019-08-30 Fix a bug in RANGE window functions that use "ORDER BY <expr> DESC NULLS FIRST" as the window-frame ORDER BY clause.
ae144a1c9 2019-08-30 The expression "(X IS FALSE) IN (FALSE)" does not imply that X is NOT NULL. Ticket [f8f472cbc77ba9c9]
7a231b497 2019-08-30 The expression "(X IS FALSE) BETWEEN FALSE AND TRUE" does not implie that X is not NULL.  Ticket [fba33c8b1df6a915]
38cefc83c 2019-08-30 The expression "(x IS FALSE) IS FALSE" does not imply that X is not NULL. Ticket [a6408d42b9f44462]
f4d9c9822 2019-08-29 Remove a faulty testcase() macro.
bd717a4d2 2019-08-29 Improve vdbe branch coverage of NULLS LAST code.
9d23ea74d 2019-08-29 Fix other problems similar to ticket [c0390363].
db586e484 2019-08-29 Add a missing VdbeCoverage() macro.
f76ccb7d5 2019-08-29 Remove an unreachable branch in the NULLS LAST logic of RANGE window functions.
b6a9121bb 2019-08-29 Fix another case where SQLite assumes that if "~(? AND FALSE)" is true, "?" must be non-null.
1cd382e35 2019-08-29 Avoid assuming that for "~ (? OR TRUE)" to be true, "?" must not be NULL, just as we do for "NOT (? OR TRUE)". Fix for ticket [c0390363].
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
