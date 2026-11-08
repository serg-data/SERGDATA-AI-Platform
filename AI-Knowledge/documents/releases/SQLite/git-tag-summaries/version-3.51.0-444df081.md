# SQLite — Git tag version-3.51.0

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.51.0
Сравнение с предыдущим тегом: version-3.50.0

## Коммиты в диапазоне

```text
c2aa8e387 2025-11-04 Version 3.51.0
1bf7eb3d4 2025-11-03 Use the same compile-time options for the CLI in the auto-setup tarball as are used in the canonical source tree. [forum:/forumpost/8975130218|Forum post 8975130218].
f1c37a357 2025-11-03 Add new column "cwd" to the jobs table in testrunner.db. For recording the directory in which the test ran or is running.
d95fffc9a 2025-11-03 Adjust the dbstatus2.test module so that it works on 32-bit builds in addition to 64-bit builds.
4733884ea 2025-11-03 Update test result output from test/dbstatus2.test module so that it reports the actual value of nTmpSpill when that value is out of range.
0dfa31d27 2025-11-03 Fix the test/speedtest.tcl script so that the CC= command-line option works.
15c6d8838 2025-11-03 Fix a harmless memory leak in the CLI caused by the --cmd option generating an error message.
eaacb4ac3 2025-11-02 Add pedantic OOM detection logic to some disused diagnostic and test code. No changes to any deliverables.
0c747e165 2025-11-01 Update the test/walthread.test testing script so that it uses a random database name.
e5c8467a8 2025-11-01 Fix ext/wasm/mkdist.sh to use ./version-info instead of ../../version-info (a recent build change made to ensure that builds with a custom sqlite3.c embed that version info).
b2b8ab6bc 2025-10-31 Updates to the compile-for-windows.md document.  No changes to code.
7f7008507 2025-10-31 Detect some cases of ambiguous column references in USING clauses that can come up with nested joins.
a183595ed 2025-10-31 Change the name of a file-scope constant array in carray.c so that it does not conflict with other variables names in other files when carray.c is amalgamated.  This is down to resolve a harmless compiler warning.
63ab7c625 2025-10-31 Update the main README.md file to use the robot-safe /rchvdwnld page on the server for downloads.
1c19c0624 2025-10-31 Fix the output of ".dump" in the CLI so that the sqlite_sequence table is created using correct syntax.
da17de532 2025-10-30 New assert() statements to help out static analyzers.
1ed6441bb 2025-10-30 Add SQLITE_OMIT_WAL checks around some functions to avoid defining unused statics in such builds. Fixes OMIT_WAL builds on msys2 and passes tool/omittest-msvc.tcl.
139ec38ac 2025-10-30 Further improvements the ".dump" command to handle corner cases.
41fda52f3 2025-10-30 Another (void), as per [dd6edfc09434].
7fb254590 2025-10-30 Add (void) to two places for the sake of SQLITE_OMIT_WAL builds. Why these do not complain on tests in this tree, but do on a downstream tree (same machine, same compiler), is a mystery.
3a61466a2 2025-10-30 wasm: re-add SQLITE_OMIT_WAL to the c-pp-lite build flags.
916fc1129 2025-10-30 Macro tweaks to get SQLITE_OMIT_WAL building. Remove some nearby stray EOL whitespace.
a8a99becb 2025-10-30 Fix a typo and improve wording in README.md
f3b396494 2025-10-30 Updates to the tool/warnings.sh script for better compiler warnings.
4ebf49168 2025-10-30 Fix a harmless compiler warning associated with flexarrays.
c6b86ba2a 2025-10-30 Updates to the main README.md file.
c5ff2aa7c 2025-10-30 Fix the CLI ".dump" command so that it does not make duplicate sqlite_sequence table entries as described in [forum:/forumpost/b1674b56ad|forum thread b1674b56ad].
cb36dc3f3 2025-10-30 Prevent a harmless signed integer overflow in the CLI if the argument to the --skip option of the ".inport" command is -9223372036854775808.
7c86a0321 2025-10-30 Remove an OMIT_WAL from the wasm build because it breaks with the current amalgamation (and isn't strictly needed here anyway).
d443f0a95 2025-10-29 Fix a logic error introduced by [cea8bf79e18d55a8] which caused "0 OR 2" to be evaluated as "2" instead of as "1".  Problem reported at [forum:/forumpost/d5f32040c5d50d2d|forum post d5f32040c].
34b1bf16e 2025-10-28 Tiny cosmetic tweak to configure script output. No functional changes.
74cd3c53f 2025-10-28 Typo fixes in LICENSE.md from BrickViking.
ffbfc27fa 2025-10-28 Fix an signed integer overflow problem that can occur when using an oversize value for the SQLITE_MAX_LENGTH compile-time option together with multi-gigabyte operands to the OP_Concat operator.
9c0770537 2025-10-28 Enhance the CLI so that it can handle inputs larger than 2 billion lines.
6cc222c3b 2025-10-28 Additional comments explaining what unixIsSharingShmNode() does.  No changes to code.
db0d47b74 2025-10-27 Omit unnecessary branches from the unixIsSharingShmNode() implementation.
e34f35c83 2025-10-27 The unixIsSharingShmNode() function should always return false for the unix-excl VFS.
626351d44 2025-10-27 Implement an experimental defensive measure to try to prevent the -wal and -shm files of an active WAL-mode database connection from being deleted out from under the database connection in the case where the database SHARED lock has been released by an accidental call to close() in a different thread, or similar.
6e2784632 2025-10-27 Fix a minor over-allocation of heap memory in wal.c.
8ce786f17 2025-10-27 Fix sanitizer complaints in the regexp extension.
6b9230d2a 2025-10-26 Merge the OPFS/SEE tests into trunk (where they should have been committed).
d4ead9b9e 2025-10-26 A better/cleaner fix for [1c80ff88c0ce].
f57d36807 2025-10-26 c-pp-lite: Fix another newline-related off-by-one which could cause newlines to get lost in @token@ filtering. Problem found in out-of-tree testing.
3fceae3b9 2025-10-26 Doc typo fix reported in the forum. No code changes.
a10598985 2025-10-25 Rename the file control to SQLITE_FCNTL_FILESTAT.  Rename the SQL function to sqlite_filestat().  Rename the enable macro to SQLITE_ENABLE_FILESTAT.
ecbeefecd 2025-10-25 Fix a bug in sqlite_file_info() output:  It was showing the "pal" for the main file descriptor when traversing other unused file descriptors for the same inode.
2b24d8957 2025-10-25 New --normal option for the ".open" command in the CLI.  Also, when opening the database for deduceDatabaseType(), use the same open-flags that will be used subsequently for the official open, to avoid creating unusable file descriptors that need to be held until all database instances close.
726e83610 2025-10-25 Add additional information about unix file descriptors to the same database file in the sqlite_file_info() output.
7be565f0c 2025-10-25 Adjust unixPosixAdvisorLocks() to use redirectable system calls so that it can be tested.
0d859b482 2025-10-25 Fix the CLI so that it does not try to open what might be an SQLite database using open() in the deduceDatabaseType() routine, as this can lead to broken posix advisory locks.
ab29c24dc 2025-10-25 Additional information about the unixShm shown.
dcc07d3ca 2025-10-25 Do not attempt to show posix-advisory-locking status on journal files.
234c6c4bf 2025-10-25 The sqlite_file_info() function should always return JSON, unless there is an OOM.
86319b841 2025-10-25 New symbolic representation of posix advisory locking information
76db3a6e6 2025-10-25 Stricter assert() statements on unixShmSystemLock().
003737d1d 2025-10-24 Improvements to the design of the /proc lock analysis.
be4d0c2e2 2025-10-24 Make it particularly clear in the wasm build output that unsupported builds are exactly that. Cosmetic tweak only, no functional changes.
aeb886bc5 2025-10-24 Easier to read /proc lock interpretation.
2f9311c5c 2025-10-24 Flesh out the sqlite_file_info() function further, and in particular show locks based in /proc/PID/fdinfo/FD, when that information is available.
093b26e8e 2025-10-24 New diagnostic SQL function "sqlite_file_info()" and its associated file-control SQLITE_FCNTL_GET_INFO.
63ee85426 2025-10-24 Fix a duplicate SQLITE_API on sqlite3_carray_bind(), as reported in [forum:7499e8a19edc8908|forum post 7499e8a19e].
3ba506d9c 2025-10-24 ext/wasm: dependencies fix for parallel builds attempted immediately after a distclean. Add version-info to the distclean rules.
67fa33774 2025-10-24 ext/wasm/GNUmakefile: (A) When using a custom sqlite3.c, use sqlite3.h from the same directory instead of the top of this tree. (B) Re-add preprocessor flags for SEE which were misplaced during recent build refactoring.
033dbac51 2025-10-24 Fix [4e713558f6c6ea3d] so that it supports separate builds of rtree.
9af334f54 2025-10-24 Document minor discrepancies in how sqlite3_bind_pointer() and sqlite3_carray_bind() react to the SQLITE_TRANSIENT and SQLITE_STATIC finalizers.
4bb53ab2e 2025-10-24 Make explicit that sqlite3_bind_pointer() and sqlite3_carray_bind() call the provided destructor even if those routines fail, per [forum:6d81b10952|forum feedback].
7adc9a597 2025-10-24 Update the MSVC makefile for the amalgamation distribution.
acdda1075 2025-10-24 Enhance the tokenizer so that it is able to deal with individual tokens larger than 2GiB.
bc2691d5c 2025-10-24 In the CLI, improved error messages on input errors.  Limit the size of a single SQL statement to a little more than 2GB.
95c188d55 2025-10-24 Limit the size of --hexdb files in the CLI to 2 billion lines, to avoid overflowing the line number counter.
404309640 2025-10-23 Additional defenses against over-sized inputs in the (unused) amatch.c demonstration code.
d06a0be51 2025-10-23 Fix a faulty error message in the ext/misc/fileio.c extension.
984e44689 2025-10-22 Adjust some of the markdown in the LICENSE.md file so that it will hopefully work better on GitHub.
774ce0ba4 2025-10-21 Back out [b144f875d6bddce6] and remove the former check for strchrnul() from the configure script.
d41f5ef7e 2025-10-19 Reduce the maximum size of LIKE and GLOB patterns in the ossfuzz.c test module to avoid false-positive infinite loop reports from OSS-Fuzz based on long and complex fuzzer-generated LIKE/GLOB patterns that are not actually infinite loops, but which do take a long time to resolve.
efe8ae567 2025-10-18 Use 64-bit memory allocations everywhere in the expert extension.
21c57abc5 2025-10-18 Increase the range of integer indexes in the the merge() family of SQL functions.
31c86ca0a 2025-10-17 Fix a minor memory leak in the CLI that can occur following an error in the ".output" dot-command.
9f36870a7 2025-10-16 Resolve the MacOS-specific build issue reported in [forum:95edc7a8d7d1de59|forum post 95edc7a8d7d1de59], with help from Bo Lindbergh.
0a585a64d 2025-10-16 In dbpage.c, disable truncation on any update error, including errors in sqlite3PagerWrite().
6eaeea0a3 2025-10-16 Fix an off-by-one in c-pp-lite.c which could cause @token@-processed output to get one duplicated byte.
e826aa8e0 2025-10-15 Minor JS doc updates. No code changes.
ff5d4c348 2025-10-15 Resolve a valgrind-reported error in ext/wasm/c-pp-lite.c caused by successful exit colliding with the atexit() handler. Add -e SCRIPT support to c-pp-lite to facilitate testing.
f66a0600d 2025-10-15 Improve performance of the shell tool ".ar" command when it is given a large number of arguments.
34c1e04cb 2025-10-15 Fix memory allocation in the ".table" command of the .cli when the number of tables in the database file approaches 2 billion.
f83df5b15 2025-10-14 Reestablish APIARMOR for the sqlite3_db_status() interface.
d6cb2ccee 2025-10-14 JS/WASM: Expose sqlite3_db_status64(), sqlite3changeset_apply_v3(), sqlite3changeset_apply_v3_strm(), and SQLITE_DBSTATUS_TEMPBUF_SPILL.
e7cf3fe4c 2025-10-14 Add the test/testloadext.c loadable extension to test the ability to use the latest APIs using the loadable extension mechanism.
53a6b7d13 2025-10-14 Make the new sqlite3_db_status64() API accessible to extensions.
4472c967a 2025-10-14 Fix two links in ext/wasm/README.md.
abe709be8 2025-10-14 Extra defenses against integer overflow in the decimal extension.
5dbbe5075 2025-10-14 Add a section to ext/wasm/README.md about the dependency on wabt/wasm-strip for release builds.
9f136fc5e 2025-10-14 Fix a makefile typo which caused a build directory to not get mkdir'd for the fiddle build.
264bcad69 2025-10-13 Avoid integer overflows (a) when dealing with zeroblob(N) calls when 2*N is larger than 2^31, and (b) in fts5 when a corrupt record is close to 2^31 bytes in size. Both of these require special builds with SQLITE_MAX_LENGTH set to a non-default value.
a8bb50ce9 2025-10-13 Fix a bug in concat_ws() in which an initial empty string was treated as if it was a NULL value.
c93270ebc 2025-10-13 Enable CLI documentation for .imposter
94356039d 2025-10-12 Fix broken hyperlinks in the documentation.
ee4676b3f 2025-10-12 Fix order of operations in the OP_Concat operator of the byte-code engine to avoid any possibility of an integer overflow.
e4eaf174a 2025-10-11 Remove an unused variable from the generate_series implementation.
59e1ab557 2025-10-11 Fix an assert() that could fail when reading a blob or text value larger than 1GiB from the database (requires a non-default build configuration). This is an assert() fix only, production builds were functioning correctly.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
