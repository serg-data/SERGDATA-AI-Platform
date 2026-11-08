# SQLite — Git tag version-3.54.1

Тип документа: сводка Git-коммитов, НЕ официальные релиз-ноты
Репозиторий: https://github.com/sqlite/sqlite.git
Тег: version-3.54.1
Сравнение с предыдущим тегом: version-3.54.0

## Коммиты в диапазоне

```text
57520227c 2026-10-16 Version 3.54.1
1bf688324 2026-10-15 Fixes to the handling of time 24:00:00. [forum:/info/2026-10-15T10:26:06Z|Forum post 2026-10-15T10:26:06Z]
23500fbf1 2026-10-14 Ensure the internal DBFLAG_SchemaKnownOk flag is always cleared after a database schema is reset. Report [bugs:/info/2026-10-14T01:25:35Z | 2026-10-14T01:25:35Z].
eba536e8f 2026-10-14 The previous check-in was not quite correct.  Both rLhsOrig and rLhs are vectors and so neither should be freed using sqlite3ReleaseTempReg().  Indeed, neither should be freed at all since both vectors remain in use.
9266f1518 2026-10-14 In check-in [8800c13deca3717c], fix a double-free of a byte-code register, resulting in the same register being on the reusable register list twice. [bugs:/info/2026-10-14T05:52:10Z|Bug 2026-10-14T05:52:10Z].
0fbd83dc9 2026-10-13 Avoid an assert() failure by clearing Vdbe.smimask when Vdbe.expmask is cleared.
cb1bf41aa 2026-10-13 Restore 3.53.0 handling of codepoints u+fffe and u+ffff (they are separator characters) in fts3 and fts5. See forum post [forum:/info/9c6ec90d24 | 2026-10-13T08:37:16Z].
c8922e6f6 2026-10-13 Merge fixes to vec1 made on trunk into this branch.
76b61a60d 2026-10-13 Enhance OP_MustBeInt so that it is able to handle -9223372036854775808.0. [bugs:/info/2026-10-11T20:33:51Z|Bug 2026-10-11T20:33:51Z].  See also [987ba5a3dc5f2a22].
ed9745eb7 2026-10-13 Fix "csv" output mode in the CLI so that it responds to --colsep and --rowsep as it should. [forum:/info/2026-10-12T17:59:34Z|Forum post 2026-10-12T17:59:34Z].
394e7bc1a 2026-10-12 Prevent scalar subqueries from ever returning a value with a non-zero subtype. Report [bugs:/info/2026-10-12T13:52:22Z | 2026-10-12T13:52:22Z].  Re-added after the addition of a necessary prerequisite in the previous check-in.
7815214b6 2026-10-12 An unknown function can be seen in exprNodeCanReturnSubtype(), but only if SQLite is compiled with SQLITE_ENABLE_UNKNOWN_SQL_FUNCTIONS.  Adjust asserts accordingly.
5e43afae7 2026-10-12 Failed to increase the memory allocation size as required in the previous check-in.  Fixed here.
d50d824d4 2026-10-12 Improvements to [313ab6c4e517e599] to address the concern raised by [bugs:/info/2026-10-12T17:03:33Z|Bug comment 2026-10-12T17:03:33Z].
31c9762d0 2026-10-12 Avoid leaking pages when remapping a database file on unix. Forum post [forum:3cfba36128 | 3cfba36128].
e26021ed6 2026-10-12 Temporarily back out the penultimate check-in on this branch in order to prevent an assertion fault.  Need to reconsider this approach in light of [bug:/info/2026-05-18T14:04:01Z|Bug 2026-05-18T14:04:01Z].  That other bug might be fixed incorrectly, and might also need to be backed out. Both bugs reopened until we can complete the analysis.
5bf189146 2026-10-12 Fix a problem causing "aggregate( t1.col1 ORDER BY t2.col2 )" where col1 and col2 are in the same positions in their tables to be treated as "aggregate( t2.col2 ORDER BY t2.col2 )". Report [bugs:info/2026-10-12T13:31:40Z | 2026-10-12T13:31:40Z].
3922c4242 2026-10-12 Prevent scalar subqueries from ever returning a value with a non-zero subtype. Report [bugs:/info/2026-10-12T13:52:22Z | 2026-10-12T13:52:22Z].
1201b826e 2026-10-12 Fix a harmless compiler warning in [7f154192db5a3a79].
e037ddd70 2026-10-12 Avoid ever repreparing a statement if a call to sqlite3_bind_int64() does not actually change the bound value.
b853a8f04 2026-10-12 Add test case for [bugs:/info/2026-10-11T16:09:34Z | 2026-10-11T16:09:34Z]. Bug was already fixed by [7f154192db].
48fedaa40 2026-10-12 Avoid excessive reprepares when there is an unindexed "col=?" constraint on a join query. This should only be reprepared when the bound value toggles between integer values 0 or 1 and any other value. Report [bugs:/info/2026-10-11T16:06:46Z | 2026-10-11T16:06:46Z].
eb61c5229 2026-10-12 When configuring with --editline, be sure to define HAVE_EDITLINE. Addresses [forum:8b9b30f6f4|forum post 2026-10-12T12:33:03Z].
55373fee0 2026-10-12 Improved detection of complete input in the CLI. [bugs:/info/2026-10-12T09:57:26Z|Bug 2026-10-12T09:57:26Z]
e326d6eff 2026-10-12 Do not use an index expression to evaluate a constant expression, as that uses unnecessary disk access and might actually give incorrect results if the expression was moved outside of the indexed loop.  The error condition arose in check-in [44200596aa943963] for version 3.41.0 and was first reported 3.5 years later by [bugs:/info/2026-10-11T19:26:40Z|Bug 2026-10-11T19:26:40Z].
d67fe4cc4 2026-10-12 Fix a minor typo in a comment.
03e00d6b8 2026-10-11 Do not allow the json_valid() routine to use a cached (and possibly edited) copy of the JSON.  It needs to parse the JSON for itself. [bugs:/info/2026-10-11T18:32:23Z|Bug 2026-10-11T18:32:23Z].
50575da52 2026-10-11 Another fix to the order-by-subquery optimization of check-in [7a0cdc7edb704a88]. Trouble reported by [bugs:/info/2026-10-11T17:00:56Z|Bug 2026-10-11T17:00:56Z].
513c19fa3 2026-10-11 Fix a problem in the query flattener associated with RIGHT JOIN, as reported by [bugs:/info/2026-10-11T16:49:00Z|Bug 2026-10-11T16:49:00Z]. This problem surfaced after the fix to [forum:/info/2025-08-21T14:14:03Z|Forum post 2025-08-21T14:14:03Z] at check-in [e0beda7ffe92abf6].  Before that, the query would not parse.
d85a80711 2026-10-10 Back out a minor performance optimization associated with sqlite3VdbeMakeReady() as it has been found to not work correctly on some 32-bit builds. [bugs:/info/2026-10-10T18:05:46Z|Bug 2026-10-10T18:05:46Z]
e89208468 2026-10-10 In the CLI, disallow any use of the fileio extension in --safe mode. [bugs:/info/2026-10-10T13:15:05Z|Bug 2026-10-10T13:15:05Z]
0a8c82266 2026-10-09 Improved error handling in the ".import" command of the CLI. [forum:/info/2026-10-09T17:57:07Z|Forum post 2026-10-09T17:57:07Z].
581f55819 2026-10-09 Start a new branch to receive patches for the 3.54 release.  Put all bug fixes that will go into a patch release on this branch.  The plan it to periodically merge the branch into trunk, rather than cherrypicking from trunk to branch as has been done before.
40f8f7494 2026-10-05 OPFS SAHPool VFS: fix an improbable corner case in which the VFS's in-memory state and its on-disk state could differ with regards to availability of a given SAH if a write failure happens at one very specific point during de-registration of the SAH. Addresses [bugs:432f260aa7|bug report 2026-10-05T17:51:35Z].
5be47b15c 2026-10-04 Adapt wasm build for emcc's deprecation of-sMEMORY64=1 and -sWASM_BIGINT=1. Enable emcc -sASSERTIONS for fiddle at the suggestion of an emcc OOM error, as that flag makes such errors more informative.
```

Примечание: сообщения коммитов не гарантируют полного описания пользовательских изменений. Использовать как вспомогательный источник, проверяя вывод по исходному коду.
