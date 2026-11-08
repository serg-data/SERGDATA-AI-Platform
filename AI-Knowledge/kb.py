import argparse
from collections import deque
import hashlib
import os
import re
import sqlite3
import sys
import time
import zipfile
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

from document_readers import SUPPORTED_EXTENSIONS, extract_text

BASE = Path(__file__).resolve().parent
DB = BASE / "index" / "knowledge.db"
SOURCES = [BASE / "documents", BASE / "code"]

EXTENSIONS = SUPPORTED_EXTENSIONS

EXCLUDED_DIRS = {
    "backups",
    "backup",
    "__backup__",
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "out",
    ".idea",
    ".vscode",
}

MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 МиБ
CHUNK_LINES = 100
OVERLAP_LINES = 15
MAX_QUERY_TERMS = 12
# Индексация: настраивается вручную перед запуском.
# Начни с 6; сравни 3, 6 и 8 на одном и том же наборе файлов.
# Для HDD слишком много потоков может снизить скорость из-за случайных чтений.
INDEX_WORKERS = 6

# Сколько задач максимум может быть одновременно в работе/ожидании на один поток.
# Увеличение помогает держать работников занятыми, но расходует больше RAM.
PENDING_TASKS_PER_WORKER = 3
MAX_PENDING_TASKS = max(INDEX_WORKERS, INDEX_WORKERS * PENDING_TASKS_PER_WORKER)


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)

    con.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE NOT NULL,
            modified REAL NOT NULL,
            content TEXT NOT NULL
        )
    """)
    con.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS search
        USING fts5(path, content, tokenize='unicode61')
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            content TEXT NOT NULL,
            digest TEXT NOT NULL
        )
    """)
    con.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunk_search
        USING fts5(path, content, tokenize='unicode61')
    """)
    return con


def excluded(path):
    """Exclude generated, backup, staging and temporary clone directories from indexing."""
    parts = [part.casefold() for part in path.parts]
    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    # Temporary full clones created by older Git Doctor versions lived under
    # code/ as .<repo>.reclone-<timestamp>. Never ingest their working trees.
    for part in parts:
        if ".reclone-" in part or part.startswith(".reclone-"):
            return True
        if part.endswith("-stage") or "-stage-" in part:
            return True
        if "-before-swap-" in part or "-before-sparse-" in part:
            return True
        if "-damaged-" in part or "-restore-check-" in part or "-fresh-" in part:
            return True
    return False


def split_chunks(lines):
    step = max(1, CHUNK_LINES - OVERLAP_LINES)

    for start in range(0, len(lines), step):
        end = min(start + CHUNK_LINES, len(lines))
        content = "".join(lines[start:end])

        if content.strip():
            yield start + 1, end, content

        if end == len(lines):
            break


def read_text_robust(path):
    """Read a file and include the failing path in any OS error."""
    try:
        with open(
            os.fspath(path),
            "r",
            encoding="utf-8",
            errors="replace",
            newline="",
        ) as file:
            return file.read()
    except OSError as exc:
        raise OSError(
            exc.errno,
            f"ошибка чтения ({type(exc).__name__}): {exc}",
            os.fspath(path),
        ) from exc


def _registered_external_source(selected_path):
    """Return (source_id, source_root) only for a registered enabled source."""
    import json

    registry_path = BASE / "sources.json"
    if not registry_path.is_file():
        return None
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Не удалось прочитать реестр внешних источников: {exc}") from exc
    rows = data.get("sources", []) if isinstance(data, dict) else []
    if not isinstance(rows, list):
        raise ValueError("Реестр внешних источников повреждён: поле sources должно быть списком")
    candidate = Path(selected_path).resolve()
    for row in rows:
        if not isinstance(row, dict) or row.get("enabled", True) is False:
            continue
        source_id = str(row.get("id", "")).strip()
        raw_root = row.get("path")
        if not source_id or not isinstance(raw_root, str) or not raw_root.strip():
            continue
        try:
            source_root = Path(raw_root).expanduser().resolve(strict=True)
            candidate.relative_to(source_root)
        except (OSError, ValueError):
            continue
        if source_root.is_dir():
            return source_id, source_root
    return None


def _index_path_key(folder, path):
    """Stable DB key; external files are namespaced by source ID."""
    path = Path(path).resolve()
    base = BASE.resolve()
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        registered = _registered_external_source(path)
        if not registered:
            raise ValueError(f"Внешний путь не зарегистрирован: {path}")
        source_id, source_root = registered
        relative = path.relative_to(source_root).as_posix()
        if not relative or relative == ".":
            raise ValueError("Нельзя индексировать корень внешнего источника как файл")
        return f"@external/{source_id}/{relative}"


def _iter_indexable_files(selected_path=None):
    """Yield supported files from the project or a registered external source."""
    if selected_path is not None:
        selected_path = Path(selected_path).expanduser().resolve()
        if not selected_path.exists():
            raise FileNotFoundError(f"Путь не найден: {selected_path}")
        try:
            selected_path.relative_to(BASE.resolve())
        except ValueError:
            registered = _registered_external_source(selected_path)
            if not registered:
                raise ValueError("Путь должен находиться внутри AI-Knowledge или зарегистрированного внешнего источника")
        if selected_path.is_file():
            if selected_path.suffix.lower() in EXTENSIONS:
                _index_path_key(selected_path.parent, selected_path)
                if not excluded(Path(selected_path.name)):
                    yield selected_path.parent, selected_path
            return
        if not selected_path.is_dir():
            raise ValueError(f"Это не файл и не папка: {selected_path}")
        roots = [selected_path]
    else:
        roots = [folder for folder in SOURCES if folder.is_dir()]

    for root in roots:
        # os.walk(topdown=True) lets us prune backups/staging folders entirely,
        # unlike Path.rglob which still descends into them before filtering.
        import os
        def onerror(exc):
            print(f"Не удалось прочитать каталог: {exc}", file=sys.stderr)

        for current, dirnames, filenames in os.walk(root, topdown=True, onerror=onerror):
            current_path = Path(current)
            dirnames[:] = sorted(
                [name for name in dirnames if not excluded(Path(name))],
                key=str.casefold,
            )
            if excluded(current_path.relative_to(root)):
                dirnames[:] = []
                continue
            for filename in filenames:
                path = current_path / filename
                try:
                    if path.suffix.lower() not in EXTENSIONS:
                        continue
                    if excluded(path.relative_to(root)):
                        continue
                    if path.is_file():
                        yield root, path
                except OSError:
                    # Let the preparation worker report file-specific errors.
                    yield root, path


def _show_progress(done, total, started, current="", recent_rate=None):
    width = 24
    ratio = done / total if total else 1.0
    filled = int(width * ratio)
    bar = "#" * filled + "-" * (width - filled)
    elapsed = max(0.001, time.monotonic() - started)
    average_rate = done / elapsed if done else 0.0
    rate = recent_rate if recent_rate and recent_rate > 0 else average_rate
    remaining = (total - done) / rate if rate > 0 else 0.0
    if remaining >= 3600:
        eta = f"{remaining / 3600:.1f} ч"
    elif remaining >= 60:
        eta = f"{remaining / 60:.1f} мин"
    else:
        eta = f"{remaining:.0f} с"
    name = current.replace("\\", "/")
    if len(name) > 46:
        name = "…" + name[-45:]
    line = f"\r[{bar}] {ratio * 100:5.1f}% {done}/{total} | ETA {eta} | {name}"
    print(line[:160].ljust(160), end="", file=sys.stderr, flush=True)


def _prepare_file(folder, path, known_files, known_chunk_paths, force_paths=None):
    """Read and prepare one file in a worker; never touches SQLite."""
    relpath = _index_path_key(folder, path)
    try:
        if not path.is_file() or excluded(path.relative_to(folder)):
            return {
                "status": "skipped",
                "path": relpath,
                "reason": "файл исчез или исключён",
            }
        if path.suffix.lower() not in EXTENSIONS:
            return {
                "status": "skipped",
                "path": relpath,
                "reason": "неподдерживаемый тип",
            }

        stat = path.stat()
        if stat.st_size > MAX_FILE_BYTES:
            return {"status": "remove", "path": relpath, "reason": "файл больше 5 МиБ"}

        old_modified = known_files.get(relpath)
        force_paths = force_paths or set()
        if (
            relpath not in force_paths
            and old_modified is not None
            and old_modified == stat.st_mtime
            and relpath in known_chunk_paths
        ):
            return {"status": "unchanged", "path": relpath}

        content = extract_text(path)
        if not content.strip():
            return {"status": "remove", "path": relpath, "reason": "пустой файл"}

        lines = content.splitlines(keepends=True)
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        chunks = list(split_chunks(lines))
        return {
            "status": "ready",
            "path": relpath,
            "modified": stat.st_mtime,
            "content": content,
            "chunks": chunks,
            "digest": digest,
        }
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        return {
            "status": "error",
            "path": relpath,
            "reason": f"{type(exc).__name__}: {exc}",
        }


def _write_prepared_file(con, item):
    """Write one prepared file atomically. Called only by the single DB writer."""
    relpath = item["path"]
    content = item["content"]
    with con:
        old = con.execute("SELECT id FROM files WHERE path = ?", (relpath,)).fetchone()
        if old:
            file_id = old[0]
            con.execute("DELETE FROM search WHERE path = ?", (relpath,))
            con.execute("DELETE FROM chunk_search WHERE path = ?", (relpath,))
            con.execute("DELETE FROM chunks WHERE path = ?", (relpath,))
            con.execute(
                "UPDATE files SET modified=?, content=? WHERE id=?",
                (item["modified"], content, file_id),
            )
        else:
            cur = con.execute(
                "INSERT INTO files(path, modified, content) VALUES (?, ?, ?)",
                (relpath, item["modified"], content),
            )
            file_id = cur.lastrowid

        con.execute(
            "INSERT INTO search(rowid, path, content) VALUES (?, ?, ?)",
            (file_id, relpath, content),
        )

        chunks = item["chunks"]
        if chunks:
            con.executemany(
                "INSERT INTO chunks (path, start_line, end_line, content, digest) VALUES (?, ?, ?, ?, ?)",
                [
                    (relpath, start, end, chunk, item["digest"])
                    for start, end, chunk in chunks
                ],
            )
            # Fetch generated chunk IDs, then populate FTS5 in one batch.
            inserted = con.execute(
                "SELECT id, content FROM chunks WHERE path = ? ORDER BY id DESC LIMIT ?",
                (relpath, len(chunks)),
            ).fetchall()
            inserted.reverse()
            con.executemany(
                "INSERT INTO chunk_search(rowid, path, content) VALUES (?, ?, ?)",
                [
                    (chunk_id, relpath, chunk_content)
                    for chunk_id, chunk_content in inserted
                ],
            )


def _load_paths_manifest(manifest_path):
    """Validate a durable, exact Git change manifest. Paths are relative to BASE."""
    import json

    data = json.loads(Path(manifest_path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Манифест должен быть JSON-объектом")
    paths = data.get("paths", [])
    deleted = data.get("deleted", [])
    if not isinstance(paths, list) or not isinstance(deleted, list):
        raise ValueError("Поля paths и deleted должны быть списками")

    base = BASE.resolve()
    candidates, deleted_out, seen = [], [], set()
    for raw in paths:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(f"Некорректный путь: {raw!r}")
        path = (base / raw.replace("\\", "/")).resolve()
        try:
            path.relative_to(base)
        except ValueError:
            raise ValueError(f"Путь выходит за пределы базы: {raw}")
        key = path.relative_to(base).as_posix()
        if key in seen:
            continue
        seen.add(key)
        if path.is_file() and path.suffix.lower() in EXTENSIONS and not excluded(path.relative_to(base)):
            candidates.append((path.parent, path))
        else:
            deleted_out.append(key)

    for raw in deleted:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(f"Некорректный удалённый путь: {raw!r}")
        rel = Path(raw.replace("\\", "/"))
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"Некорректный путь удаления: {raw}")
        key = rel.as_posix()
        if key not in deleted_out:
            deleted_out.append(key)
    return candidates, deleted_out


def _delete_indexed_paths(con, paths):
    removed = 0
    for relpath in paths:
        # One transaction per path: interruption is safe because the durable
        # manifest remains and repeating a deletion is idempotent.
        with con:
            rows = con.execute("SELECT id FROM files WHERE path = ?", (relpath,)).fetchall()
            if not rows:
                continue
            con.execute("DELETE FROM search WHERE path = ?", (relpath,))
            con.execute("DELETE FROM chunk_search WHERE path = ?", (relpath,))
            con.execute("DELETE FROM chunks WHERE path = ?", (relpath,))
            con.execute("DELETE FROM files WHERE path = ?", (relpath,))
            removed += len(rows)
    return removed


def _purge_temporary_clone_index_entries(con):
    """Remove stale KB rows created by legacy .<repo>.reclone-* directories."""
    paths = [
        row[0]
        for row in con.execute("SELECT path FROM files")
        if any(".reclone-" in part.casefold() or part.casefold().startswith(".reclone-")
               for part in Path(row[0].replace("\\\\", "/")).parts)
    ]
    removed = _delete_indexed_paths(con, paths)
    if removed:
        print(f"Удалено старых записей временных Git-клонов из индекса: {removed}")
    return removed


def index_files(selected_path=None, paths_manifest=None):
    con = connect()
    updated = skipped = unchanged = done = errors = 0
    started = time.monotonic()
    deleted_paths = []
    force_paths = set()

    try:
        _purge_temporary_clone_index_entries(con)
        if paths_manifest:
            if selected_path is not None:
                raise ValueError("--paths-file нельзя совмещать с --path")
            candidates, deleted_paths = _load_paths_manifest(paths_manifest)
            force_paths = {_index_path_key(folder, path) for folder, path in candidates}
            removed = _delete_indexed_paths(con, deleted_paths)
            print(f"Удалено записей из индекса: {removed}")
        else:
            candidates = list(_iter_indexable_files(selected_path))
    except (OSError, ValueError, TypeError) as exc:
        con.close()
        print(f"Не удалось выбрать источник: {exc}")
        return False

    total = len(candidates)
    if total == 0:
        print("Нет поддерживаемых файлов для индексации в выбранном источнике.")
        print("Проверьте, что в папке есть файлы поддерживаемых типов и у процесса есть права чтения.")
        con.close()
        return True

    try:
        known_files = dict(con.execute("SELECT path, modified FROM files"))
        known_chunk_paths = {row[0] for row in con.execute("SELECT DISTINCT path FROM chunks")}
    except sqlite3.Error:
        con.close()
        raise

    print(f"Подготовлено файлов для проверки: {total}; рабочих потоков: {INDEX_WORKERS}; очередь задач: {MAX_PENDING_TASKS}")
    iterator = iter(candidates)
    pending = {}
    recent_completions = deque(maxlen=120)

    try:
        with ThreadPoolExecutor(max_workers=INDEX_WORKERS, thread_name_prefix="kb-index") as pool:
            while len(pending) < MAX_PENDING_TASKS:
                try:
                    folder, path = next(iterator)
                except StopIteration:
                    break
                future = pool.submit(_prepare_file, folder, path, known_files, known_chunk_paths, force_paths)
                pending[future] = (folder, path)

            while pending:
                completed, _ = wait(pending, return_when=FIRST_COMPLETED)
                for future in completed:
                    folder, path = pending.pop(future)
                    relpath = _index_path_key(folder, path)
                    try:
                        item = future.result()
                        status = item["status"]
                        if status == "unchanged":
                            unchanged += 1
                        elif status in {"skipped", "remove"}:
                            skipped += 1
                            if status == "remove":
                                _delete_indexed_paths(con, [relpath])
                            reason = item.get("reason", "файл не индексируется")
                            if reason not in {"файл исчез или исключён", "неподдерживаемый тип"}:
                                print(f"\nПропущен {relpath}: {reason}")
                        elif status == "error":
                            skipped += 1
                            errors += 1
                            print(f"\nОшибка обработки {relpath}: {item['reason']}")
                        else:
                            _write_prepared_file(con, item)
                            updated += 1
                            known_files[relpath] = item["modified"]
                            known_chunk_paths.add(relpath)
                    except (sqlite3.Error, OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
                        skipped += 1
                        errors += 1
                        print(f"\nОшибка записи {relpath}: {type(exc).__name__}: {exc}")
                    finally:
                        done += 1
                        now = time.monotonic()
                        recent_completions.append(now)
                        recent_rate = None
                        if len(recent_completions) >= 10:
                            span = recent_completions[-1] - recent_completions[0]
                            if span > 0:
                                recent_rate = (len(recent_completions) - 1) / span
                        _show_progress(done, total, started, relpath, recent_rate)

                    try:
                        next_folder, next_path = next(iterator)
                    except StopIteration:
                        continue
                    next_future = pool.submit(_prepare_file, next_folder, next_path, known_files, known_chunk_paths, force_paths)
                    pending[next_future] = (next_folder, next_path)

        print(file=sys.stderr)
        con.commit()
        elapsed = time.monotonic() - started
        rate = done / elapsed if elapsed > 0 else 0
        print(f"Индексация завершена за {elapsed:.1f} с ({rate:.2f} файлов/с). Обновлено файлов: {updated}; без изменений: {unchanged}; пропущено: {skipped}; ошибок: {errors}")
        print("Всего фрагментов:", con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])
        return errors == 0
    finally:
        con.close()


def _query_terms(query):
    terms = re.findall(r"[\w.-]+", query, flags=re.UNICODE)
    unique = []
    seen = set()

    for term in terms:
        term = term.strip(".-_")
        folded = term.casefold()

        if term and folded not in seen:
            unique.append(term)
            seen.add(folded)

    return unique[:MAX_QUERY_TERMS]


def _fts_quote(term):
    return '"' + term.replace('"', '""') + '"'


def _run_chunk_query(con, expression, limit):
    return con.execute(
        """
        SELECT
            chunks.path,
            chunks.start_line,
            chunks.end_line,
            snippet(chunk_search, 1, '>>>', '<<<', ' ... ', 24),
            bm25(chunk_search, 4.0, 1.0) AS score
        FROM chunk_search
        JOIN chunks ON chunks.id = chunk_search.rowid
        WHERE chunk_search MATCH ?
        ORDER BY score
        LIMIT ?
    """,
        (expression, limit),
    ).fetchall()


def search_files(query, limit=5):
    """Search using strict, broad and per-term routes; merge without duplicates."""
    terms = _query_terms(query)

    if not terms:
        print("Укажи поисковый запрос.")
        return

    safe_limit = max(1, min(limit, 20))
    candidate_limit = min(100, max(30, safe_limit * 10))
    con = connect()
    ranked = {}

    try:
        routes = []
        if len(terms) > 1:
            routes.append(("strict", " AND ".join(_fts_quote(term) for term in terms)))
        routes.append(("broad", " OR ".join(_fts_quote(term) for term in terms)))
        # Single-term routes help retrieve relevant material when one query word
        # is rare, misspelled, or absent from an otherwise useful chunk.
        if len(terms) > 1:
            routes.extend(
                (f"term:{i}", _fts_quote(term)) for i, term in enumerate(terms[:6])
            )

        for route_name, expression in routes:
            try:
                candidates = _run_chunk_query(con, expression, candidate_limit)
            except sqlite3.OperationalError:
                # A malformed/unsupported route must not suppress other routes.
                continue
            for rank, row in enumerate(candidates, start=1):
                key = (row[0], row[1], row[2])
                state = ranked.setdefault(
                    key, {"row": row, "rrf": 0.0, "strict": False}
                )
                state["rrf"] += 1.0 / (60 + rank)
                if route_name == "strict":
                    state["strict"] = True
                # Prefer the better FTS score if the same chunk is returned twice.
                if row[4] < state["row"][4]:
                    state["row"] = row

        def ranking_key(state):
            row = state["row"]
            path, _start, _end, snippet_text, score = row
            searchable = f"{path} {snippet_text}".casefold()
            coverage = sum(1 for term in terms if term.casefold() in searchable)
            # Full-query matches lead; then prefer term coverage, multi-route
            # consensus, and FTS relevance. Negative BM25 values are better.
            return (not state["strict"], -coverage, -state["rrf"], score)

        rows = [
            state["row"]
            for state in sorted(ranked.values(), key=ranking_key)[:safe_limit]
        ]

    except sqlite3.OperationalError as exc:
        print(f"Ошибка поиска: {exc}")
        return
    finally:
        con.close()

    if not rows:
        print(
            "Совпадений нет. Попробуй более короткий запрос или отдельный технический термин."
        )
        return

    for path, start, end, snippet_text, _score in rows:
        print(f"\n--- {path}:{start}-{end} ---\n{snippet_text}")


def main():
    parser = argparse.ArgumentParser(description="Локальная база знаний SERGDATA")
    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    index_parser = sub.add_parser(
        "index",
        help="Синхронизировать релизы и индексировать документы и код",
    )
    index_parser.add_argument(
        "--no-release-sync",
        action="store_true",
        help="Не обращаться к сетевым источникам релизов; индексировать только локальные файлы",
    )
    index_parser.add_argument(
        "--select",
        action="store_true",
        help="Интерактивно выбрать один файл или папку для индексации",
    )
    index_parser.add_argument(
        "--path",
        help="Индексировать только указанный файл или папку внутри проекта",
    )
    index_parser.add_argument(
        "--paths-file",
        help="Точный JSON-манифест изменённых и удалённых файлов; без полного обхода",
    )
    index_parser.add_argument(
        "--release-count",
        type=int,
        default=30,
        help="Сколько последних релизов запрашивать при синхронизации (по умолчанию 30)",
    )

    search = sub.add_parser(
        "search",
        help="Искать по базе",
    )
    search.add_argument(
        "query",
        nargs="+",
        help="Слова для поиска",
    )
    search.add_argument(
        "--limit",
        type=int,
        default=5,
    )

    args = parser.parse_args()

    if args.command == "index":
        selected_path = args.path
        if args.select and args.path:
            parser.error("Используй либо --select, либо --path, но не оба параметра")
        if args.select:
            print("Выбор источника для индексации")
            print("  1 — файл")
            print("  2 — папка (включая подпапки)")
            choice = input("Что индексируем? [1/2]: ").strip()
            if choice not in {"1", "2"}:
                print("Отмена: нужно выбрать 1 или 2.")
                return
            selected_path = (
                input("Путь к файлу или папке (относительный или абсолютный): ")
                .strip()
                .strip('"')
            )
            if not selected_path:
                print("Отмена: путь не указан.")
                return
            selected_path = Path(selected_path).expanduser()
            if not selected_path.is_absolute():
                selected_path = BASE / selected_path
            if choice == "1" and selected_path.exists() and selected_path.is_dir():
                print("Отмена: выбран путь к папке, а не к файлу.")
                return
            if choice == "2" and selected_path.exists() and selected_path.is_file():
                print("Отмена: выбран путь к файлу, а не к папке.")
                return
        if selected_path is None and not args.no_release_sync:
            try:
                from release_sync import sync as sync_releases

                sync_releases(count=args.release_count)
            except Exception as exc:
                # Release synchronization must never prevent local indexing.
                print(
                    f"Синхронизация релизов не удалась; продолжаю локальную индексацию: {type(exc).__name__}: {exc}"
                )
        elif selected_path is None:
            print("Синхронизация релизов отключена параметром --no-release-sync")
        else:
            print("Выбран точечный источник: синхронизация релизов пропущена.")
        if args.paths_file:
            if args.select or args.path:
                parser.error("--paths-file нельзя совмещать с --select или --path")
            ok = index_files(paths_manifest=args.paths_file)
        else:
            ok = index_files(selected_path)
        if not ok:
            return 2
    elif args.command == "search":
        search_files(" ".join(args.query), args.limit)


if __name__ == "__main__":
    main()
