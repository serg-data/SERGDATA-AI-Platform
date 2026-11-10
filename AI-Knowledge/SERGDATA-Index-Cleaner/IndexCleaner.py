from __future__ import annotations

import json
import os
import sqlite3
import sys
import threading
import queue
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


APP_TITLE = "SERGDATA Index Cleaner"
DB_RELATIVE = Path("index") / "knowledge.db"
TABLES = ("files", "chunks", "search", "chunk_search")


def find_base() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / "kb.py").is_file() and (candidate / DB_RELATIVE).exists():
            return candidate
        if (candidate / "repositories.json").is_file() and (candidate / "index").is_dir():
            return candidate
    return here.parent


def quote_identifier(name: str) -> str:
    # Table names are constants, never user input.
    return '"' + name.replace('"', '""') + '"'


class KnowledgeDB:
    def __init__(self, db_path: Path, base_path: Path):
        self.db_path = db_path.resolve()
        self.base_path = base_path.resolve()
        self.timeout = 5.0

    def connect(self, readonly: bool = False) -> sqlite3.Connection:
        if readonly:
            uri = self.db_path.as_uri() + "?mode=ro"
            con = sqlite3.connect(uri, uri=True, timeout=self.timeout)
        else:
            con = sqlite3.connect(self.db_path, timeout=self.timeout)
        con.row_factory = sqlite3.Row
        con.execute(f"PRAGMA busy_timeout={int(self.timeout * 1000)}")
        return con

    def validate_schema(self, con: sqlite3.Connection) -> None:
        found = {
            row["name"]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
            )
        }
        missing = set(TABLES) - found
        if missing:
            raise RuntimeError(
                "Структура базы не соответствует AI-Knowledge. "
                f"Не найдены таблицы: {', '.join(sorted(missing))}"
            )
        for table in TABLES:
            con.execute(f"SELECT path FROM {quote_identifier(table)} LIMIT 0")

    def list_paths(self):
        """Read only canonical tables; avoid full scans of the two large FTS indexes."""
        con = self.connect(readonly=True)
        try:
            self.validate_schema(con)
            rows = con.execute(
                """
                WITH file_counts AS (
                    SELECT path, COUNT(*) AS file_count FROM files GROUP BY path
                ), chunk_counts AS (
                    SELECT path, COUNT(*) AS chunk_count FROM chunks GROUP BY path
                ), all_paths AS (
                    SELECT path FROM files UNION SELECT path FROM chunks
                )
                SELECT p.path,
                       COALESCE(f.file_count, 0) AS file_count,
                       COALESCE(c.chunk_count, 0) AS chunk_count
                FROM all_paths p
                LEFT JOIN file_counts f ON f.path = p.path
                LEFT JOIN chunk_counts c ON c.path = p.path
                ORDER BY p.path COLLATE NOCASE
                """
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            con.close()

    def source_root_for_external(self, key: str):
        # Key format is @external/<source-id>/<relative-path>.
        parts = key.replace("\\", "/").split("/", 2)
        if len(parts) < 3 or parts[0] != "@external":
            return None
        registry = self.base_path / "sources.json"
        if not registry.is_file():
            return None
        try:
            data = json.loads(registry.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            return None
        for source in data.get("sources", []):
            if not isinstance(source, dict):
                continue
            if str(source.get("id", "")) == parts[1]:
                root = Path(str(source.get("path", ""))).expanduser()
                return root / parts[2]
        return None

    def resolve_key(self, key: str) -> Path | None:
        if key.startswith("@external/"):
            candidate = self.source_root_for_external(key)
            return candidate.resolve() if candidate else None
        return (self.base_path / Path(key.replace("/", os_sep()))).resolve()

    def scan_missing(self, paths):
        missing = []
        for item in paths:
            path = self.resolve_key(item["path"])
            exists = bool(path and path.exists())
            item["exists"] = exists
            if not exists:
                missing.append(item)
        return missing

    def backup(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = self.db_path.parent / "cleaner-backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / f"knowledge-before-clean-{stamp}.db"
        source = self.connect(readonly=True)
        destination = sqlite3.connect(target)
        try:
            source.backup(destination)
            check = destination.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise RuntimeError(f"Резервная копия не прошла integrity_check: {check}")
            destination.commit()
        finally:
            destination.close()
            source.close()
        return target

    def delete_paths(self, paths: list[str]) -> tuple[int, Path]:
        paths = sorted(set(paths))
        if not paths:
            raise ValueError("Не выбраны записи для удаления.")

        # Back up first. The UI asks the user to stop Workbench/indexing before this step.
        backup_path = self.backup()
        con = self.connect()
        removed = 0
        try:
            self.validate_schema(con)
            con.execute("BEGIN IMMEDIATE")
            for path in paths:
                # Remove every row for this exact indexed path from all four tables.
                for table in ("search", "chunk_search", "chunks", "files"):
                    cur = con.execute(
                        f"DELETE FROM {quote_identifier(table)} WHERE path = ?",
                        (path,),
                    )
                    if table == "files":
                        removed += cur.rowcount if cur.rowcount >= 0 else 0

            # Ask FTS5 to verify its own index consistency before committing.
            con.execute("INSERT INTO search(search) VALUES('integrity-check')")
            con.execute("INSERT INTO chunk_search(chunk_search) VALUES('integrity-check')")
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

        check = self.connect(readonly=True)
        try:
            remaining = 0
            for path in paths:
                for table in TABLES:
                    remaining += check.execute(
                        f"SELECT COUNT(*) FROM {quote_identifier(table)} WHERE path = ?",
                        (path,),
                    ).fetchone()[0]
            integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            check.close()
        if remaining or integrity != "ok":
            raise RuntimeError(
                f"Проверка после удаления не пройдена: оставшихся строк={remaining}, "
                f"integrity_check={integrity}. Резервная копия: {backup_path}"
            )
        return removed, backup_path


def os_sep() -> str:
    return "\\" if sys.platform == "win32" else "/"


def folder_key_for(path: str) -> str | None:
    normalized = path.replace("\\", "/").strip("/")
    if "/" not in normalized:
        return None
    return normalized.rsplit("/", 1)[0]


def all_folder_keys(paths: list[str]) -> list[str]:
    folders = set()
    for path in paths:
        normalized = path.replace("\\", "/").strip("/")
        parts = normalized.split("/")
        # For external keys, @external/<id> is a namespace, not a deletable source root.
        start = 2 if parts and parts[0] == "@external" else 0
        for i in range(start + 1, len(parts)):
            folders.add("/".join(parts[:i]))
    return sorted(folders, key=str.casefold)


class CleanerApp:
    MAX_FILE_ROWS = 1500
    MAX_TREE_ROWS = 1500
    FILTER_DEBOUNCE_MS = 300
    RENDER_BATCH_SIZE = 50
    RENDER_BATCH_DELAY_MS = 10
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1080x690")
        self.root.minsize(850, 560)

        self.base_path = find_base()
        self.db_path = self.base_path / DB_RELATIVE
        self.db: KnowledgeDB | None = None
        self.path_rows: list[dict] = []
        self.loading = False
        self.result_queue = queue.Queue()
        self._filter_after_ids = {}
        self._render_after_ids = {}
        self._render_generations = {"folder_tree": 0, "file_tree": 0}
        self.folder_rows: list[dict] = []

        self._build_ui()
        self.root.after(100, self._poll_worker)
        self._connect_initial()

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x")
        ttk.Label(header, text=APP_TITLE, font=("Segoe UI", 17, "bold")).pack(side="left")
        ttk.Button(header, text="Выбрать базу…", command=self.choose_db).pack(side="right")

        self.db_label = ttk.Label(outer, text="", foreground="#555")
        self.db_label.pack(anchor="w", pady=(6, 10))

        warning = ttk.Label(
            outer,
            text="Перед удалением остановите индексацию и закройте Workbench. "
                 "Утилита не удаляет исходные файлы с диска.",
            wraplength=1000,
            foreground="#9a5b00",
        )
        warning.pack(anchor="w", pady=(0, 10))

        self.tabs = ttk.Notebook(outer)
        self.tabs.pack(fill="both", expand=True)

        folders_tab = ttk.Frame(self.tabs, padding=8)
        files_tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(folders_tab, text="Папки и репозитории")
        self.tabs.add(files_tab, text="Отдельные файлы")

        self.folder_search = tk.StringVar()
        self.file_search = tk.StringVar()
        self._build_tree_tab(
            folders_tab, self.folder_search, "folder_tree",
            ("path", "files", "chunks", "status"),
            ("Папка / репозиторий", "Файлов", "Фрагментов", "Состояние"),
            self.filter_folders,
        )
        self._build_tree_tab(
            files_tab, self.file_search, "file_tree",
            ("path", "chunks", "status"),
            ("Индексированный путь", "Фрагментов", "Состояние"),
            self.filter_files,
        )

        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(10, 0))
        self.status = tk.StringVar(value="Готово.")
        ttk.Label(footer, textvariable=self.status).pack(side="left", fill="x", expand=True)
        ttk.Button(footer, text="Обновить список", command=self.refresh).pack(side="right", padx=(6, 0))
        ttk.Button(footer, text="Удалить выбранное из индекса", command=self.delete_selected).pack(side="right")

    def _build_tree_tab(self, parent, variable, attr, columns, headings, filter_command):
        search_row = ttk.Frame(parent)
        search_row.pack(fill="x", pady=(0, 8))
        ttk.Label(search_row, text="Фильтр:").pack(side="left")
        entry = ttk.Entry(search_row, textvariable=variable)
        entry.pack(side="left", fill="x", expand=True, padx=6)
        entry.bind("<KeyRelease>", lambda _event, name=attr, command=filter_command: self._schedule_filter(name, command))

        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="extended")
        for col, heading in zip(columns, headings):
            tree.heading(col, text=heading)
            tree.column(col, width=620 if col == "path" else 110, anchor="w" if col in ("path", "status") else "center")
        yscroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        xscroll.pack(side="bottom", fill="x")
        setattr(self, attr, tree)

    def _connect_initial(self):
        if not self.db_path.is_file():
            self.db_label.configure(text=f"База не найдена: {self.db_path}")
            self.status.set("Выберите существующую knowledge.db.")
            return
        self._set_db(self.db_path)

    def _set_db(self, path: Path):
        self.db_path = path.resolve()
        self.base_path = self.db_path.parent.parent
        self.db = KnowledgeDB(self.db_path, self.base_path)
        self.loading = False  # invalidate any previous read against another database
        self.db_label.configure(text=f"Выбрана база: {self.db_path}")
        self.refresh()

    def choose_db(self):
        selected = filedialog.askopenfilename(
            title="Выберите knowledge.db",
            filetypes=[("SQLite database", "*.db"), ("All files", "*.*")],
            initialdir=str(self.db_path.parent if self.db_path.parent.exists() else Path.home()),
        )
        if selected:
            self._set_db(Path(selected))

    def refresh(self):
        # Full SQLite read is intentionally limited to initial load, database
        # selection, and the explicit "Обновить список" / post-delete refresh.
        if not self.db or self.loading:
            return
        if not self.db_path.is_file():
            self.db_label.configure(text=f"База не найдена: {self.db_path}")
            self.status.set("Выберите существующую knowledge.db.")
            return
        db = self.db
        self.loading = True
        self.status.set("Чтение базы… Большая база может обрабатываться несколько минут. Окно останется доступным.")

        def worker():
            try:
                rows = db.list_paths()
                folders = self._build_folder_rows(db, rows)
                self.result_queue.put(("ok", db, (rows, folders)))
            except Exception as exc:
                self.result_queue.put(("error", db, str(exc)))

        threading.Thread(target=worker, name="IndexCleaner-DB-Reader", daemon=True).start()

    def _poll_worker(self):
        try:
            while True:
                kind, db, payload = self.result_queue.get_nowait()
                if db is not self.db:
                    continue
                self.loading = False
                if kind == "error":
                    self.status.set("Ошибка чтения базы.")
                    messagebox.showerror("Ошибка чтения базы", payload)
                    continue
                self.path_rows, self.folder_rows = payload
                self._render_folders()
                self._render_files()
                total_files = sum(1 for row in self.path_rows if row["file_count"])
                total_chunks = sum(row["chunk_count"] for row in self.path_rows)
                self.status.set(
                    f"База загружена в память: путей {len(self.path_rows):,} | "
                    f"файлов: {total_files:,} | фрагментов: {total_chunks:,}".replace(",", " ")
                )
        except queue.Empty:
            pass
        self.root.after(100, self._poll_worker)

    def _build_folder_rows(self, db: KnowledgeDB, rows: list[dict]) -> list[dict]:
        """Build folder aggregates and check disk state off the Tk main thread."""
        aggregates = {}
        for row in rows:
            normalized = row["path"].replace("\\", "/").strip("/")
            parts = normalized.split("/")
            start = 2 if parts and parts[0] == "@external" else 0
            for i in range(start + 1, len(parts)):
                folder = "/".join(parts[:i])
                item = aggregates.setdefault(folder, [0, 0])
                if row["file_count"]:
                    item[0] += 1
                item[1] += row["chunk_count"]

        result = []
        for folder, counts in aggregates.items():
            folder_path = db.resolve_key(folder + "/__index_cleaner_probe__")
            exists = bool(folder_path and folder_path.parent.exists())
            result.append({
                "path": folder,
                "file_count": counts[0],
                "chunk_count": counts[1],
                "status": "На диске" if exists else "Каталог отсутствует",
            })
        result.sort(key=lambda item: item["path"].casefold())
        return result

    def _schedule_filter(self, name, command):
        """Debounce keystrokes so a large index is never re-rendered per character."""
        previous = self._filter_after_ids.get(name)
        if previous is not None:
            try:
                self.root.after_cancel(previous)
            except tk.TclError:
                pass
        self._filter_after_ids[name] = self.root.after(
            self.FILTER_DEBOUNCE_MS,
            lambda: self._run_scheduled_filter(name, command),
        )

    def _run_scheduled_filter(self, name, command):
        self._filter_after_ids.pop(name, None)
        command()

    def _render_tree_incrementally(self, name, tree, items, max_rows, values_factory, label):
        """Render cached rows in small UI batches; never query SQLite here."""
        generation = self._render_generations[name] + 1
        self._render_generations[name] = generation

        previous = self._render_after_ids.pop(name, None)
        if previous is not None:
            try:
                self.root.after_cancel(previous)
            except tk.TclError:
                pass

        # The data is already in memory. Filtering below does not touch SQLite
        # or the filesystem; only the Treeview presentation is refreshed.
        query = (self.folder_search if name == "folder_tree" else self.file_search).get().casefold().strip()
        matches = [item for item in items if not query or query in item["path"].casefold()]
        visible = matches[:max_rows]

        children = tree.get_children("")
        if children:
            tree.delete(*children)

        if len(matches) > max_rows:
            self.status.set(
                f"{label}: найдено {len(matches):,}, показываю {max_rows:,}; уточните фильтр".replace(",", " ")
            )
        else:
            self.status.set(f"{label}: {len(matches):,}".replace(",", " "))

        def insert_batch(offset=0):
            if generation != self._render_generations[name]:
                return
            stop = min(offset + self.RENDER_BATCH_SIZE, len(visible))
            for item in visible[offset:stop]:
                path = item["path"]
                try:
                    tree.insert("", "end", iid=path, values=values_factory(item))
                except tk.TclError:
                    # A stale/duplicate item must not abort the remaining UI.
                    continue
            if stop < len(visible):
                self._render_after_ids[name] = self.root.after(
                    self.RENDER_BATCH_DELAY_MS, lambda: insert_batch(stop)
                )
            else:
                self._render_after_ids.pop(name, None)

        if visible:
            self._render_after_ids[name] = self.root.after(1, insert_batch)

    def _render_folders(self):
        self._render_tree_incrementally(
            "folder_tree", self.folder_tree, self.folder_rows, self.MAX_TREE_ROWS,
            lambda item: (item["path"], item["file_count"], item["chunk_count"], item["status"]),
            "Папок",
        )

    def _render_files(self):
        self._render_tree_incrementally(
            "file_tree", self.file_tree, self.path_rows, self.MAX_FILE_ROWS,
            lambda row: (row["path"], row["chunk_count"], "В индексе"),
            "Файлов",
        )

    def filter_folders(self):
        self._render_folders()

    def filter_files(self):
        self._render_files()

    def delete_selected(self):
        if not self.db:
            return
        if self.loading:
            messagebox.showinfo("Идёт чтение", "Дождитесь завершения чтения базы.")
            return
        selected_tab = self.tabs.index(self.tabs.select())
        if selected_tab == 0:
            tree = self.folder_tree
            selected = list(tree.selection())
            if not selected:
                messagebox.showinfo("Нет выбора", "Выберите одну или несколько папок.")
                return
            paths = set()
            normalized_roots = [item.replace("\\", "/").rstrip("/") for item in selected]
            for row in self.path_rows:
                key = row["path"].replace("\\", "/")
                if any(key.startswith(root + "/") for root in normalized_roots):
                    paths.add(row["path"])
            label = f"{len(selected)} папок и {len(paths)} индексированных путей"
        else:
            tree = self.file_tree
            paths = set(tree.selection())
            if not paths:
                messagebox.showinfo("Нет выбора", "Выберите один или несколько файлов.")
                return
            label = f"{len(paths)} индексированных файлов/путей"

        if not paths:
            messagebox.showinfo("Нет данных", "Для выбранного элемента индексированных записей не найдено.")
            return

        preview = (
            f"Будут удалены записи из индекса: {label}.\n\n"
            "Исходные файлы и папки на диске останутся без изменений.\n"
            "Внешние источники и другие пути не затрагиваются.\n\n"
            "Перед продолжением убедитесь, что Workbench и индексация остановлены.\n\n"
            "Продолжить?"
        )
        if not messagebox.askyesno("Подтверждение очистки", preview, icon="warning"):
            return

        try:
            removed, backup = self.db.delete_paths(list(paths))
            messagebox.showinfo(
                "Очистка завершена",
                f"Удалено записей файлов: {removed}\n"
                f"Удалено индексированных путей: {len(paths)}\n\n"
                f"Резервная копия:\n{backup}",
            )
            self.refresh()
        except Exception as exc:
            messagebox.showerror(
                "Очистка не выполнена",
                f"{exc}\n\nЕсли была создана резервная копия, она сохранена отдельно.",
            )


def main():
    root = tk.Tk()
    try:
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass
    CleanerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
