# SQLite — Git tag version-3.36.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.36.0
Сравнение с предыдущим тегом: version-3.35.2

## Коммиты в диапазоне

```text
6d72858e7 2021-06-18 Version 3.36.0
9c32c914b 2021-06-16 Add an ALWAYS on a branch in STAT4-only logic that is now always true due to check-in [c21bc5a2353e660f].
755708538 2021-06-16 Omit a handful of tests from pager1.test when testing SQLITE_ENABLE_ZIPVFS builds.
7379b455a 2021-06-16 Do not run test file sessionbig.test on 32-bit platforms. It uses too much memory.
a4df1bd5f 2021-06-16 Adjust the mkshellc.tcl script so that the generated code always uses unix-style line endings.
d95a65202 2021-06-16 Avoid ominous warning in showdb.c
cbe83495e 2021-06-16 Adjustments to requirement markings in comments.  No changes to code.
236bcdf3e 2021-06-16 Enhanced defense against integer overflow in ALTER TABLE.
9d82a2ccf 2021-06-15 Fix an incorrect ifdef in the previous check-in.
f54e79405 2021-06-15 Fix some minor #ifdef issues so that all of the supported compile-time options continue to build.
17adf4e5a 2021-06-15 Update the "nmakehlp.c" utility program sources associated with the TCL Extension Architecture, obtained from [https://core.tcl-lang.org/sampleextension/file].  Perhaps this new version will sit better with salmonx's static analyzer [forum:/forumpost/7f0beca9797ee23a|(ref1)], [forum:/forumpost/7d5c8b19231ad57f|(ref2)].
a959bf531 2021-06-15 Add NULL checks on all sqlite3_vfs_find(0) calls.  This is not strictly necessary.  There are no vulnerabilities here.  However, adding these checks avoids unnecessary static analyzer complaints. [forum:/forumpost/ce1193be15|Forum post ce1193be15].
972da4274 2021-06-15 Prevent an infinite loop in the trim() SQL function if the second argument is a carefully malformed UTF8 string.
11e489d6c 2021-06-14 Fix typos in testcase() macros from check-in [c09d90eec2a49b94].
93fd5420d 2021-06-14 In the authorizer, use SQLITE_DROP_INDEX, not SQLITE_DROP_TEMP_INDEX when dropping an index in an attached database.
ac67f5672 2021-06-14 Fix an ALTER TABLE problem with handling infinite loops of CTEs in the database schema.
09612a5bb 2021-06-14 Fix a test script problem in corruptN.test.
21571a94c 2021-06-14 An index on the expression "likely(X)" should store the true value of X, even if X is a real number with no fractional part.  The optimization of storing some REAL indexed values as INT (see [10d851353c2abead]) should be omitted for index columns that are expressions. [forum:/forumpost/3b940c437a|Forum post 3b940c437a].
de5f21d0a 2021-06-14 Avoid allocating oversized column names in the sqllimit1.test module.
0d08402f3 2021-06-13 The opcode that preceeds OP_SeekScan is usually OP_IdxGT but can sometimes be OP_IdxGE.  Adjust asserts accordingly.  Follow-up to [9a2ab6092d644fc3].  dbsqlfuzz e41762333a4d6e90a49e628f488d0873b2dba4c5
7a7cefa0b 2021-06-13 Improved defense against OOM errors in sqliteInitOne(). dbsqlfuzz 429db39cd5777c46479641e8637c48c62890042d
bd0d62c35 2021-06-13 Correct link in .ar help.
24ce9446a 2021-06-12 This is an alternative approach to the use-after-free problem fixed by [193b14a58e378ab3], saved here for historical reference.
35e6cd09f 2021-06-11 Reapply two recent ALTER TABLE error checks that turned out to be necessary after all.  dbsqlfuzz fc5a9deefda00dda914748985155a6d4c44174e5.
cf145047b 2021-06-11 Avoid bugs in some implementations of dlopen() by avoiding calls to dlopen() with a filename argument that exceeds FILENAME_MAX bytes. [forum:/forumpost/08a0d6d9bf|Forum post 08a0d6d9bf].
d03d3a9b7 2021-06-11 Fix a crash in new ALTER TABLE code that could follow an OOM.
6065686d9 2021-06-11 Remove an unreachable branch added by the previous commit.
26d61e5ad 2021-06-11 Fix problems with ALTER TABLE and schemas that contain views with some recursive CTEs, or CTEs that reference other CTEs.
75016050f 2021-06-10 Improved robustness following OOM in the constant propagation optimization. dbsqlfuzz 001a20255c0df7495c21df62a20ea5b51e22c390.
d622855e3 2021-06-09 Set the database connection error code for an oversize argument to sqlite3_bind_blob64() or sqlite3_bind_text64(). [forum:/info/a636276f0d451667|Forum post a636276f0d451667] and [forum/forumpost/33821c8db543c|33821c8db543c].
8d2a9c3b3 2021-06-09 Add defensive code to better handle corrupt records in fts5.
18f9be897 2021-06-08 Remove two assert()s in FTS5 that checks for database corruption right before actual code does the same check. dbsqlfuzz 9680db8f5338cb9b6060eb3a02d984555d4472e3.
26ec568d2 2021-06-08 Try to avoid a double-free in the showdb utility program when running pgidx on a corrupt database. See [forum:/forumpost/a60ea5a4d4|forum post a60ea5a4d4] for context
9025af160 2021-06-08 Add an assert() to prevent the value of the SQLITE_VTABRISK macros from being changed in a way that would break logic.
822810b95 2021-06-08 Avoid a buffer overread in fts3 that could occur when handling corrupt data structures.
bc85a5159 2021-06-07 Fix a buffer overread that could occur in fts5 when handling corrupt records.
ec7354610 2021-06-07 Fix a buffer overrun in fts3 that could occur when handling corrupt records and '^' queries.
09c69fc1b 2021-06-07 Add recent dbsqlfuzz test cases to test/fuzzdata8.db.
ccf0bb49b 2021-06-07 Avoid use of uninitialized memory while running defragmentPage() on a corrupt database file. dbsqlfuzz 4c45cecc0b255aaf2ea85453ccd17e814fd0b6b2
fe972341a 2021-06-07 Fix an assert() in the OP_ParseSchema opcode that might fail on a corrupt database file when running with PRAGMA writable_schema=ON. dbsqlfuzz e7d743ca65f2767e415095f0c5a49166a0f55eea.
9a4127a8c 2021-06-07 Remove unnecessary end-of-line whitespace from the regexp.c extension.
9ae57841d 2021-06-07 Omit the unnecessary highlighting of the security implications of SQLTIE_DIRECTONLY in the sqlite3_create_function() documentation. No changes to code.
06258a426 2021-06-04 A better fix for the problem addressed by [4eb80b0cc61526c1].  This fix also avoids reading uninitialized variables.
e427fe521 2021-06-04 Make MSVC build examples work when taken literally, and say when they do.
50dce5e82 2021-06-04 Add the (missing) dependency of regexp.c to the shell.c rule in the makefiles. This dependency should have been added by [5d4535bfb603d7c8] but was missed.
abc15f1b9 2021-06-04 Fix harmless compiler warnings.
9718bca77 2021-06-04 Fix more cases in the regexp extension where the 0x00 terminator at the end of the input string is being pattern matched. [forum/forumpost/9104f0d9e7|Forum post 9104f0d9e7].
2d26cfcc4 2021-06-04 Revamp SQLITE_TESTCTRL_TUNE to provide visibility of current turning parameter values.
f3c1256a4 2021-06-04 Add support for SQLITE_TESTCTRL_TUNE and the ".testctrl tune ID VALUE" command in the CLI.
19e4eefbc 2021-06-03 Fix a case where combining row-value UPDATE FROM syntax with window functions over aggregates can cause an error.
a6df0e693 2021-06-03 Fix the truncate optimization so that PRAGMA count_changes and changes() return correct values even for a WITHOUT ROWID table. [forum:/forumpost/07dedbf9a1|Forum post 07dedbf9a1].
6468990e7 2021-06-03 Add the regexp() and regexpi() extension functions to the CLI.
de30a3d2e 2021-06-03 Fix a bug in the regexp extension in which the "." wildcard would match the 0x00 terminator at the end of the comparison string.
75f731772 2021-06-03 Fix the case-insensitive version of the regexp() function so that it does not use the prefix optimization incorrectly. [forum:/forumpost/983b43ef8e|Forum post 983b43ef8e].
3074faabe 2021-06-02 Add an optimization control bit to disable the OP_SeekScan optimization.
996643987 2021-06-02 Fix an ALWAYS which can be false.
e847164f5 2021-06-02 Tighten assert() restrictions on the OP_SeekScan opcode.
eda790d28 2021-06-02 Never use WHERE_IN_SEEKSCAN for the 2nd or subsequent IN operator.
b034a2414 2021-06-02 This is an attempt to address the OP_SeekScan performance issue identified by [forum:/forumpost/b4fcb8a598|forum post b4fcb8a598].
f9ac1ab1e 2021-06-01 Fix issue in 'mkopcodeh.tcl' tool that prevented its termination in rare circumstances.
b56a09079 2021-06-01 Fix a problem with running ALTER TABLE against schemas that contain compound SELECT statements with ORDER BY clauses containing one or more references to the second or subsequent component SELECT statements.
d65b7e36e 2021-05-29 Do not confuse the ">" operator with IS NOT NULL when checking to see if a partial index is usable. [forum:/forumpost/d813704d7c|Forum post d813704d7c].
d36bcec9a 2021-05-29 Fix a subtle error in an assert(). dbsqlfuzz eefbd0215c0c1b4bcc32b8141b48b35f7b431300
e9de65201 2021-05-28 Make a deep copy of the result of a subquery in case the subquery is reused.  Fix for the problem reported by [forum:/forumpost/28216b36ac|forum post 28216b36ac] and introduced by check-in [f30fb19ff763a7cb].  Further changes to try to optimize the new OP_Copy opcode back into either OP_SCopy or OP_Move will be attempted separately.  A test case will be in TH3.
d2f55773f 2021-05-28 Fix a potential memory leak in json_group_object() following an error. dbsqlfuzz cd32630de3ff039d97089592b63cb3616f8ec9dd
48a296c58 2021-05-27 Add the merge-test.tcl script to ease verification of LTS branches.
342cb33b2 2021-05-27 Improved comment on the prpagateConstants() routine.  No changes to executable code.
48f4f27cf 2021-05-27 Remove a NEVER that is reachable following OOM in writable_schema=ON mode with a corrupt schema.
a8ed51540 2021-05-26 Minor optimization to opcode comparison logic in the fixes to the constant-propagation optimization on this branch.
c3b48848b 2021-05-26 Add new test file whereM.test. Containing tests for the change on this branch.
40b82f9dc 2021-05-26 Avoid assuming that an expression like "x=10" in a WHERE clause implies that CASE(x AS TEXT)=='10'.
14c4d4287 2021-05-26 Take care that the code is not generated for the same Select object more than once, as transformations that apply during the first pass might cause problems for the second pass. dbsqlfuzz 836b625cd8a41809ef80fc7ebaa6554357bcb463.
151446e79 2021-05-26 Update an assert() in wherecode.c that might fail following an unrelated SQL error.
137b8ebb2 2021-05-25 Do not run sessionbig.test as part of the session_strm permutation. It is too slow.
4df68e0ae 2021-05-25 Update an allocation routine in the sessions module to allow it to allocate the maximum size permitted by sqlite3_realloc64().
78a9d7551 2021-05-25 Enhance the shell tool ".dump PATTERN" command so that it dumps the contents of shadow tables when a virtual table is identified by the PATTERN.
c00727ab5 2021-05-24 Fix a problem in the in-memory journal code that could occasionally lead to a segfault when a sub-transaction that modified zero pages was committed.
0fcf6f01e 2021-05-24 Minor comment improvements in fuzzcheck.c.
b6b06bb33 2021-05-24 New dbsqlfuzz cases added to test/fuzzdata8.db.
bf7f3a005 2021-05-24 Fix the TreeView module so that it works with the TK_ERROR exprssion. Also fix an assert() that was failing due to the recent TK_ERROR addition.
054281272 2021-05-24 Additional defenses (above and beyond [b986600520696b0c]) to prevent an invalid subquery from causing problems downstream.  If an error is found while analyzing a subquery expression, change the expression to TK_ERROR so inhibit further processing on that expression. dbsqlfuzz cf624b8c0484c66e0f552bf6475e3e3f2c22b24e.
7cc73b399 2021-05-23 Do not push a WITH clause onto the processing stack if prior errors have occurred.  dbsqlfuzz 6b7a144674e215f06ddfeb9042c873d9ee956ac0.
5e1a7ded4 2021-05-22 Do not invoke sqlite3ExprAffinity() after a syntax error that might have left the tree in an inconsistent state.  See also [e8a1515b44380cc5] and [forum:/forumpost/7e484e225c|forum post 7e484e225c].
ff9186137 2021-05-22 The fix in the previous check-in was only correct if the OOM occurs on the initial allocation.  This changes should make it correct for a resize as well.
d42dbd9df 2021-05-22 If an FTS5 Cursor fails to enlarge the space for the aInst array, set the size of the aInst array to zero. dbsqlfuzz 294254b8105cca409f27a711f1eb2e9e63cbcac5.
93c8139c1 2021-05-21 If there are errors in a nested CTE, be sure to abandon processing.  Do not continue since the parse tree may have been left in a goofy state which could cause use-after-free and segfaults. See [forum:/forumpost/aa4a7a3980|forum post aa4a7a3980] for an example.
acef1abda 2021-05-21 Fix a problem with SQLITE_MAX_MEMORY in malloc.c.
ec2f689b2 2021-05-20 Fix a faulty assert() statement in sqlite3ExprListDup(). This is a continuation of the fix at [59812e7ef705226c].
a76b7f529 2021-05-20 Enhance one test case to use various alternative definitions of DUAL.
90bc36fb3 2021-05-20 Ensure that objects within view definitions are not incorrectly resolved to CTEs that are part of the statement using the view.
a8f249f1e 2021-05-20 Ensure the required b-tree mutexes are held for "CREATE TABLE IF NOT EXISTS" and "DROP TABLE IF EXISTS" statements on attached databases.
cd1499f47 2021-05-20 Replace [0f0959c6f95046e8] with a new and better solution that also fixes the CTE name resolution problem described in [forum:/forumpost/8590e3f6dc|forum post 8590e3f6dc]. Test cases for both problems added.
1168f8109 2021-05-19 When constructing the synthensized SELECT statement that is used to choose the rows in an UPDATE FROM, make sure the first table is really the table being updated, and not some common-table expression that happens to have the same name.  [forum:/forumpost/a274248080|forum post a274248080].  More changes associated with CTE name resolution are pending.
14e250ac1 2021-05-19 Incorporate ..._DESERIALIZE revision.
04f4b6836 2021-05-19 Fix a formatting error on the comment.
187e2e48a 2021-05-19 Add a table of shared-memory lock offsets in a comment in the os_unix.c code. Include some assert()s to help verify the numbers.
3d691fd9f 2021-05-19 Allow aggregate sub-selects within ORDER BY and PARTITION BY clauses of window frame definitions.
9088186bf 2021-05-19 Improved column name and column type determination for the RETURNING clause.
99bd55250 2021-05-19 Cure some TCL test failures and narrow an object scope.
93ffb50fc 2021-05-18 In the MULTI-INDEX OR query plan, code for sub-expressions can sometimes be generated twice.  But for some subqueries, generating code off of the same tree twice causes problems.  So now MULTI-INDEX OR makes a copy of the sub-expressions it uses to avoid code-generating them more than once. dbsqlfuzz 9ebd2140e7206ff724e665f172faea28af801635.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
