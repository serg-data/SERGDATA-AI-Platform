# SQLite — Git tag version-3.40.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.40.0
Сравнение с предыдущим тегом: version-3.39.0

## Коммиты в диапазоне

```text
2f2c5e206 2022-11-16 Version 3.40.0
a70a01dbc 2022-11-14 Previous change to the fake_big_file command in the test harness was not correct.  This one should fix the problem.
1da477d3a 2022-11-14 Change the fake_big_file test command so that it fails for files larger than 2MB on Windows, as we have observed that Window10 will sometimes bluescreen when operating on very large sparse files.
cfce889cd 2022-11-14 Avoid running bigsort.test with SQLITE_DEBUG builds. The assert() statements added in [7c96a56] make it too slow.
8d7b41302 2022-11-13 Remove some outdated code comments. No code changes.
7e475e571 2022-11-12 Disable the ability to change the schema_version cookie when SQLITE_DBCONFIG_DEFENSIVE mode is enabled.  This is a security enhancement inspired by the question in [forum:/forumpost/2b9cc3dae1f1e5f6|forum post 2b9cc3dae1f1e5f6].
a6303704a 2022-11-10 Remove unnecessary tabs in the ChaCha20 implementation. [forum:/forumpost/0cdce5db8c|Forum post 0cdce5db8c].
da2641597 2022-11-10 Rework automatically acquired OPFS locks to be released during idle time. This eliminates the performance hit reported in [46304ba057707c].
aafa022f5 2022-11-10 OPFS: if an op which needs a lock is called when no lock has been obtained, automatically lock it at the start of the op and unlock it at the end of that op. This is an attempt to alleviate the cross-tab contention described in [forum post 58a377083cd24a|forum:58a377083cd24a] but it increases speedtest1 run time by approximately 4x. Perhaps auto-lock can be combined with the older idle-time-based auto-unlock to unlock such locks (but not those from xLock()) to improve this?
838865c0b 2022-11-09 Better handle an error in the fts5 integrity-check code. dbsqlfuzz e87c62f9b67ea21aebdc36ab71cab7cc3eda8dc3.
ea038d3d2 2022-11-09 Additional defense against corrupt database files in dbdata.c.
92c0881d9 2022-11-09 Increase the precision of the nData parameter to the dbdataValue() routine inside the sqlite_dbdata virtual table, to avoid the possibility of integer overflow.
50ba1a021 2022-11-08 Fix a problem with URI formatting in calls to sqlite3rbu_vacuum(zDb, NULL) causing problems on win32. First reported here <https://sqlite.org/forum/forumpost/a7ae915a9d>.
afe768193 2022-11-08 Do not attempt to run test script dbpagefault.test with SQLITE_OMIT_VIRTUALTABLE builds.
64c40ec2c 2022-11-08 Fix a problem in main.mk preventing the amalgamation-testfixture target from building.
80fafc25c 2022-11-07 Further improvements to the handling of the u32 and u16 typedefs in the shell.c source file.
d9324a522 2022-11-07 Improve the ability of mkshellc.tcl to remove redundant typedefs from the generated shell.c code.  This is needed to get shell.c to build on older C compilers.
40503750f 2022-11-07 Add the sqlite3rbu_rename_handler() API. To override the default routine that RBU uses to rename files.
49507d2af 2022-11-07 Minor doc updates in speed-check.sh. No code changes.
54422235e 2022-11-07 Fix an obsolete comment.
e38b6e031 2022-11-07 Fix typo in comment.
690d4c545 2022-11-07 Add sqlite3.wasm.alloc.impl() as a "public back door" into the low-level non-throwing allocator. Correct sqlite3.WasmAllocError constructor to behave like its usages expect it to and add tests for that.
da0175787 2022-11-07 Fix requirements marks so that they match documentation corrections.
c0a18d6a5 2022-11-07 Minor wasm doc touchups. No code changes.
1407458c6 2022-11-07 Fix the documentation regarding negative length parameters for sqlite3_result_text() interfaces, to point out that the length parameter to sqlite3_result_text64() cannot be negative. [forum:/forumpost/cf1d043b07|Forum post cf1d043b07]. Comment/documentation change only.
b36f697b5 2022-11-07 Make sure that the recoverStrlen() function (used internally by the new recovery extension) is 64-bit safe.
b819202ac 2022-11-06 The recoverAssertMutexHeld() function is for testing and verification only and should be a harmless no-op for production builds. [forum/forumpost/b4f2c7d402|Forum post b4f2c7d402].
f53c0a0d4 2022-11-05 Update test file dbpagefault.test to account for the restriction on using SQLITE_VTAB_DIRECTONLY virtual tables from within triggers.
a16edfa29 2022-11-04 Tweaks to recover module test scripts to work with various permutations.
5f7e173ab 2022-11-04 Another test case fix for auto-vacuum builds.
80dbd818f 2022-11-04 Fixes to recover module test scripts so that they may be used with SQLITE_DEFAULT_AUTOVACUUM and SQLITE_SECURE_DELETE builds.
ffc9b1b04 2022-11-04 Fix Tcl tests so that they again build and run with SQLITE_OMIT_VIRTUALTABLE defined.
881f0f411 2022-11-04 Remove an unimportant testcase() macro that is no longer reachable due to the improvement in corruption detection.
4868a8651 2022-11-04 Add another test case for the OP_Found fix.
093677add 2022-11-04 Enhance the ability of the OP_Found and similar opcodes to detect truncated index records and report SQLITE_CORRUPT. dbsqlfuzz 2b12f90aeff8e081706c7e9b58834f04869f446c.  Test cases in TH3.
c75445087 2022-11-04 Correct sqlite3-wasm.c's SQLITE_DEFAULT_CACHE_SIZE (it's measured in kb, not bytes).
7d24ff297 2022-11-03 Add experimental esm target to ext/wasm/GNUmakefile to tell emcc to generate sqlite3.mjs (ES6 module) instead of sqlite3.js. Related to discussion at [forum:ed4596cf8496a39b].
4df2ab575 2022-11-03 Globally replace '' with "" for empty JS strings to please C preprocessor.
de6186e04 2022-11-02 Minor build cleanups and fix a harmless race condition in the OPFS part of tester1.js.
2cdcc7f01 2022-11-02 Clarify documentation regarding the --recovery-db option to ".recover" and the magic 789 configuration option it is associated with.
12de518db 2022-11-02 Minor improvements to API documentation in comments for the recovery extension.
f45c33701 2022-11-02 Add sqlite3_wasm_vfs_create_file() to replace Emscripten's FS.createDataFile() in a (mostly) VFS-agnostic way. Add a test for worker1's export (to bytearray) support. Re-add worker1 open-from-bytearray using sqlite3_wasm_vfs_create_file() but it's untested (requires a new interactive test app or maybe reconsideration).
faff0410d 2022-11-02 Emcc seems confused by SQLITE_DEBUG, for reasons unknown.  Use NDEBUG instead to simplify the #ifdef logic in sqlite3recover.c.
c18c8bf95 2022-11-02 Fix a symbol name typo which broke and exception-handling case in OPFS xOpen().
f170b9798 2022-11-02 Fix a missing symbol in non-SQLITE_DEBUG builds.
b9f8ff0e8 2022-11-01 Fix a harmless compiler warning.
6da7cc9b4 2022-11-01 Fix harmless compiler warnings.
52d5d474f 2022-11-01 Instead of (const char*), use a special type - sqlite3_filename - as the filename argument passed to VFS method xOpen().
11980a6b8 2022-11-01 Fix compilation errors in the recover API seen with MSVC.
dddec5cad 2022-11-01 Fix a #ifdef involving SQLITE_OS_KV that was adding code unnecessarily.
dc5e8c63b 2022-11-01 Improvements to comments.  Change the "optimization_control" TCL command in the test harness so that it returns the new optimization mask, for verification.
0f32760e3 2022-11-01 Minor internal cleanups in the js pieces.
49048b148 2022-11-01 Significant cleanups and expansion of the sqlite3.opfs utilities. Add oo1.DB.dbVfsName(). Add VFS name to worker1:open's arguments and result.
b6d916794 2022-11-01 Do not flatten a UNION ALL subquery where the column affinities do not match on all arms.  Force that subquery to be materialized.
5fdb9a352 2022-11-01 Enforce column affinity on the materialization of a subquery or view.
c7dd9b60e 2022-10-31 Make the UPDATE method of the sqlite_dbpage virtual table rebust against OOM errors.  [forum:/forumpost/bbcf0dd6ca|Forum post bbcf0dd6ca].  Test case in TH3.
02d15a7eb 2022-10-31 Worker1: use a list, rather than a single slot, to manage the default db link so that we can keep the least-recently-opened db as the default. Re-introduce worker1.export() but do not yet expose it until an equivalent import() (or open() option) is implemented.
43b442a62 2022-10-31 Internal tweaks to the OPFS VFS result codes.
1acfe9158 2022-10-31 Add oo1.DB.exec() 'returnValue' option, which specifies what exec() should return. Defaults to the db object and enables direct return of the result rows array or a list of the individual SQL statements. Other code-adjacent internal cleanups.
549907fd6 2022-10-31 Avoid a segfault that could occur when running the recover API on a database handle with memory-mapping enabled.
1e84e1e63 2022-10-31 Extra OOM check in shell_error_context() of the CLI. [forum:/forumpost/5708841db0|forum post 5708841db0].
50ef01398 2022-10-30 Add oo1.DB.selectArray() and selectObject().
9163ef1f4 2022-10-30 Adjust automatic OPFS locking retries such that they will wait up to a total of 3 seconds spanning 4 attempts.
1fc6ffccc 2022-10-30 Minor WASM build cleanups. Enable custom Module.instantiateWasm() when not in WASMFS mode (where it doesn't work). Add sqlite3.debugModule URL param to enable some module-init-time debugging output.
af9cee12c 2022-10-30 Reduce wasm module's starting memory from 128mb to 16mb. The latter value is needed only for WASMFS-based batch-runner.js, as WASMFS builds cannot be configured for dynamic memory growth without a tremendous performance hit.
f5e7691e2 2022-10-30 Minor updates to the Windows batch tools.
1cc77c954 2022-10-29 Update ext/wasm/README.md for recent developments.
da27e4aa0 2022-10-29 More styling of module-symbols.html.
df52a0bc7 2022-10-29 Expand and document the wasm doc-update make rules. Extend the dist rules to fail more readily if there's a problem.
8948fbee2 2022-10-29 Move the sqlite3.capi.wasm namespace to sqlite3.wasm. This causes a tiny bit of naming confusion with the sqlite3.wasm *file*, but seems to make more sense than having it as a sub-namespace of capi.
053bb22f3 2022-10-28 Fix harmless compiler warnings in testing code.
71b65e88e 2022-10-28 Add sqlite3recover() support to fuzzcheck.
ffbc653d8 2022-10-28 Remove sqlite3_interrupt() from the WASM build, as it is essentially impossible to employ in JS's threading model.
f03ddcca3 2022-10-28 Add ext/wasm/module-symbols.html. Adjacent minor JS touchups.
e681b651e 2022-10-28 Minor sqlite3.oo1 API reorg prompted by documenting.
c97bb14fa 2022-10-27 Fix a minor problem with sqlite_dbdata.
676d1cda9 2022-10-27 Fix another crash in the recover extension triggered by a corrupt database.
10f552541 2022-10-27 Fix another problem to do with recovering from in-memory databases.
ac16a4716 2022-10-27 Ensure that the VFS wrapper in the recover extension does not attempt to invoke undefined methods on the underlying VFS.
895f12dfe 2022-10-27 Fix an assert() failure in the recover extension triggered by a zero value as the first page-number in an overflow page chain.
4853aa18f 2022-10-27 In the CLI, ensure that input to utf8_width_print is not NULL, or if it is, change it to an empty string.  For for the problem reported by [forum:/forumpost/2961cf13eec61876|forum post 2961cf13eec61876].
f7fea5b4b 2022-10-27 Change the name of the ".recover" command option "--freelist-corrupt" to "--ignore-freelist".
674b312ed 2022-10-27 speedtest1.html: when vfs==kvvfs, increase --size from 2 to 4, as enabled by [a4d40f6346e7]. --size 5 is 4.96mb out of (supposedly) 5mb, which works but is a bit too close to the edge.
fd6080637 2022-10-27 Automatically set temp_store=MEMORY if the VFS is kvvfs.
9c17ee4f9 2022-10-27 Do not accept a NULL pointer for the filename in KVVFS.
f7b58da83 2022-10-27 The kvvfs VFS should remember the page size when writing to the database.
bb5136e5c 2022-10-27 Re-enable the .recovery and .dbinfo commands in shell.c.in in the fiddle build, as those were fixed by [3d20d77a3511] and [cd0aa27d1732].
340b1d1a7 2022-10-27 Do not use sqlite3_result_text16() in the recover extension if SQLITE_OMIT_UTF16 is defined.
48a4a4b73 2022-10-27 Fix a problem with running ".recover" on an in-memory database.
21fd7ce09 2022-10-27 Do not use sqlite3_mutex_xxx() functions in sqlite3recover.c when built with SQLITE_THREADSAFE=0.
4f975c337 2022-10-27 Minor doc typo fixes.
3d420836f 2022-10-27 Restructure and simplify the feature-detection #defines of the recovery support in shell.c.in and disable it when building fiddle because it uses features we elide from the wasm build (e.g. utf16), leading to link errors.
de868175c 2022-10-27 Expose sqlite3_randomness() to WASM and add a custom binding for it which can populate a JS byte array. Add WhWasmUtil.isPtr().
195687f1b 2022-10-26 Disable the push-down optimization for sub-queries that are INTERSECT, UNION or EXCEPT compounds. dbsqlfuzz a34f455c91ad75a0cf8cd9476841903f42930a7a.
07dd48101 2022-10-26 Remove an unused variable from the recovery extension.
50632afa6 2022-10-26 Remove an undefined left-shift operation from the recover extension.
8364ce2aa 2022-10-26 Make the shell .recover command and the dbdata.c module more robust in the face of corrupted databases.
8c3e234ad 2022-10-26 Correct misuse of localhost-mode-only symbol S in fiddle-worker.js, which should fix the outage reported in [forum:67d985ac0bbe407f|forum post 67d985ac0bbe407f].
7731dfca4 2022-10-26 Corrected link to fiddle in ext/wasm/index.html (broken by [3d7b4f36b7dd]).
34b92b19f 2022-10-26 Replace the newly-removed oo1.DB.getFilename() with DB.dbFilename() with the hope that the distinction from the dbInstance.filename property is clearer.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
