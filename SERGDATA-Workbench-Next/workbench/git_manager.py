"""Safe, project-scoped Git operations for SERGDATA Workbench."""
from __future__ import annotations
import subprocess
import shutil
import time
from pathlib import Path

MAX_OUTPUT = 30000
SENSITIVE_PARTS = {".env", ".workbench", "credentials", "secrets", ".ssh"}

class GitManager:
    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).expanduser().resolve()
        if not self.root.is_dir():
            raise ValueError("Корень проекта не существует")

    def _run(self, *args: str, timeout: int = 30) -> str:
        cmd = ["git", *map(str, args)]
        try:
            r = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout,
                               shell=False)
        except FileNotFoundError:
            raise RuntimeError("Git не найден в PATH")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Время выполнения Git-команды истекло")
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        if r.returncode:
            raise RuntimeError((err or out or f"Git завершился с кодом {r.returncode}")[-5000:])
        return out

    def is_repo(self) -> bool:
        """Return True only when this exact project root is a Git work tree.

        Compare normalized filesystem paths rather than strings: Git on Windows
        commonly prints forward slashes while pathlib retains backslashes.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=self.root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                shell=False,
            )
            if result.returncode != 0:
                return False
            reported_root = Path(result.stdout.strip()).expanduser().resolve()
            return reported_root == self.root
        except (OSError, subprocess.SubprocessError, RuntimeError, ValueError):
            return False

    def status(self) -> dict:
        if not self.is_repo():
            return {"available": False, "initialized": False,
                    "text": "Эта папка пока не является Git-репозиторием."}
        status = self._run("status", "--short", "--branch")
        branch = self._run("branch", "--show-current")
        remotes = self._run("remote")
        return {"available": True, "initialized": True, "branch": branch or "(detached)",
                "remote": remotes, "text": status or "Нет незакоммиченных изменений."}

    def init(self) -> dict:
        if self.is_repo():
            return {"ok": True, "message": "Git-репозиторий уже существует.", **self.status()}
        self._run("init", "-b", "main", timeout=30)
        return {"ok": True, "message": "Git-репозиторий создан.", **self.status()}

    def diff(self) -> str:
        if not self.is_repo():
            raise ValueError("Сначала инициализируй Git-репозиторий")
        staged = self._run("diff", "--cached", "--", ".", ":(exclude)**/.env*", ":(exclude)**/*.pem", ":(exclude)**/*.key")
        unstaged = self._run("diff", "--", ".", ":(exclude)**/.env*", ":(exclude)**/*.pem", ":(exclude)**/*.key")
        return ("=== STAGED ===\n" + (staged or "(нет)") + "\n\n=== UNSTAGED ===\n" + (unstaged or "(нет)"))[:MAX_OUTPUT]

    def files(self) -> list[str]:
        if not self.is_repo():
            return []
        return self._run("status", "--porcelain", "-uall").splitlines()[:500]

    def stage(self, paths: list[str]) -> dict:
        if not self.is_repo(): raise ValueError("Git-репозиторий не инициализирован")
        if not paths or len(paths) > 100: raise ValueError("Выбери от 1 до 100 файлов")
        clean=[]
        for item in paths:
            rel=Path(str(item).replace("\\\\", "/"))
            if rel.is_absolute() or ".." in rel.parts: raise ValueError("Недопустимый путь")
            if any(part.casefold() in SENSITIVE_PARTS for part in rel.parts) or rel.name.casefold().startswith(".env"):
                raise ValueError("Попытка добавить потенциально секретный файл")
            candidate=(self.root/rel).resolve()
            if candidate != self.root and self.root not in candidate.parents:
                raise ValueError("Путь выходит за пределы проекта")
            clean.append(rel.as_posix())
        self._run("add", "--", *clean)
        return {"ok": True, "message": f"Добавлено в индекс: {len(clean)}"}

    def unstage(self, paths: list[str]) -> dict:
        if not self.is_repo(): raise ValueError("Git-репозиторий не инициализирован")
        if not paths or len(paths) > 100: raise ValueError("Выбери от 1 до 100 файлов")
        for item in paths:
            rel=Path(str(item).replace("\\\\", "/"))
            if rel.is_absolute() or ".." in rel.parts: raise ValueError("Недопустимый путь")
        self._run("restore", "--staged", "--", *[str(x) for x in paths])
        return {"ok": True, "message": "Индекс обновлён"}

    def commit(self, message: str) -> dict:
        if not self.is_repo(): raise ValueError("Git-репозиторий не инициализирован")
        message=str(message or "").strip()
        if not message or len(message)>200: raise ValueError("Сообщение коммита: 1–200 символов")
        # --quiet exits 1 when there are staged changes.
        check=subprocess.run(["git","diff","--cached","--quiet"],cwd=self.root,capture_output=True,timeout=15,shell=False)
        if check.returncode == 0: raise ValueError("Нет подготовленных изменений. Сначала выполни Stage.")
        if check.returncode > 1: raise RuntimeError("Не удалось проверить индекс Git")
        self._run("commit", "-m", message, timeout=120)
        return {"ok": True, "message": self._run("log", "-1", "--oneline")}

    def branches(self) -> list[str]:
        if not self.is_repo(): return []
        return self._run("branch", "--list", "--format=%(refname:short)").splitlines()

    def history(self, limit: int = 20) -> str:
        if not self.is_repo(): raise ValueError("Git-репозиторий не инициализирован")
        return self._run("log", f"-{max(1,min(int(limit),50))}", "--oneline", "--decorate")

    def create_branch(self, name: str, checkout: bool = True) -> dict:
        if not self.is_repo(): raise ValueError("Git-репозиторий не инициализирован")
        name=str(name or "").strip()
        if not name or len(name)>100 or name.startswith('-'): raise ValueError("Некорректное имя ветки")
        self._run("check-ref-format", "--branch", name)
        self._run("switch", "-c" if checkout else "--create", name)
        return {"ok":True,"branch":name,"message":f"Ветка {name} создана"}

    def checkout_branch(self, name: str) -> dict:
        if not self.is_repo(): raise ValueError("Git-репозиторий не инициализирован")
        name=str(name or "").strip()
        if name not in self.branches(): raise ValueError("Ветка не найдена")
        check=subprocess.run(["git","status","--porcelain"],cwd=self.root,capture_output=True,text=True,timeout=15,shell=False)
        if check.returncode or check.stdout.strip(): raise ValueError("Сначала сохрани или убери локальные изменения")
        self._run("switch", name)
        return {"ok":True,"branch":name,"message":f"Переключено на {name}"}

    def delete_branch(self, name: str) -> dict:
        if not self.is_repo(): raise ValueError("Git-репозиторий не инициализирован")
        name=str(name or "").strip()
        if not name or name==self._run("branch","--show-current"): raise ValueError("Нельзя удалить текущую ветку")
        if name not in self.branches(): raise ValueError("Ветка не найдена")
        self._run("branch","-d",name)
        return {"ok":True,"message":f"Ветка {name} удалена (только если слита)"}

    def remotes(self) -> list[dict]:
        if not self.is_repo(): return []
        out=self._run("remote","-v")
        rows=[]
        for line in out.splitlines():
            parts=line.split()
            if len(parts)>=3 and parts[2] in {"(fetch)","(push)"}: rows.append({"name":parts[0],"url":parts[1],"direction":parts[2][1:-1]})
        return rows

    def remote_add(self, name: str, url: str) -> dict:
        if not self.is_repo(): raise ValueError("Git-репозиторий не инициализирован")
        name=str(name or "origin").strip()
        url=str(url or "").strip()
        if not name or len(name)>50 or any(c.isspace() for c in name): raise ValueError("Некорректное имя Remote")
        if url.startswith("https://") and "@" in url.split("/", 3)[2]:
            raise ValueError("Не помещай токены и пароли в URL Remote; используй Git Credential Manager или SSH-ключ")
        if not (url.startswith("https://") or url.startswith("ssh://") or (":" in url and "@" in url and not url.startswith("-"))):
            raise ValueError("Разрешены HTTPS/SSH URL Git-репозиториев")
        existing=self._run("remote")
        if name in existing.splitlines(): self._run("remote", "set-url", name, url)
        else: self._run("remote", "add", name, url)
        return {"ok": True, "message": f"Remote {name} настроен"}


    def doctor(self) -> dict:
        """Diagnose Git index/worktree consistency without changing repository data."""
        if not self.is_repo():
            return {"ok": False, "available": False, "issues": [], "message": "Папка не является Git-репозиторием."}
        status = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false",
             "status", "--porcelain=v2", "-z", "--untracked-files=all"],
            cwd=self.root, capture_output=True, timeout=30, shell=False
        )
        if status.returncode:
            raise RuntimeError((status.stderr or "Ошибка git status".encode("utf-8")).decode("utf-8", "replace")[-3000:])
        raw = status.stdout.decode("utf-8", "surrogateescape")
        records = [x for x in raw.split("\0") if x]
        issues = []
        for record in records:
            if not record.startswith("1 ") and not record.startswith("2 "):
                continue
            fields = record.split(" ", 8)
            if len(fields) < 9:
                continue
            xy, path = fields[1], fields[8]
            if xy[0] != "D":
                continue
            # A staged deletion is suspicious only if HEAD and the index both
            # still contain the same object and the working file is present.
            head = subprocess.run(["git", "rev-parse", f"HEAD:{path}"], cwd=self.root, capture_output=True, text=True, timeout=10, shell=False)
            index = subprocess.run(["git", "rev-parse", f":{path}"], cwd=self.root, capture_output=True, text=True, timeout=10, shell=False)
            file_path = (self.root / Path(path)).resolve()
            exists = file_path.is_file() and self.root in file_path.parents
            worktree = subprocess.run(["git", "hash-object", "--", path], cwd=self.root, capture_output=True, text=True, timeout=15, shell=False) if exists else None
            head_blob = head.stdout.strip() if head.returncode == 0 else None
            index_blob = index.stdout.strip() if index.returncode == 0 else None
            work_blob = worktree.stdout.strip() if worktree and worktree.returncode == 0 else None
            if exists and head_blob and head_blob == index_blob == work_blob:
                issues.append({"code": "index_status_contradiction", "path": path, "severity": "high",
                               "message": "Git сообщает о staged deletion, хотя HEAD, индекс и файл содержат одинаковый объект.",
                               "repairable": True})
        return {"ok": True, "available": True, "clean": not records, "issues": issues,
                "status": [r.replace("\n", " ")[:1000] for r in records[:200]],
                "message": "Противоречий не обнаружено." if not issues else f"Обнаружено противоречий: {len(issues)}."}

    def repair_index_contradiction(self, path: str) -> dict:
        """Safely reinsert one proven-identical tracked entry, with index backup/rollback."""
        if not self.is_repo():
            raise ValueError("Git-репозиторий не инициализирован")
        rel = Path(str(path).replace("\\", "/"))
        if rel.is_absolute() or ".." in rel.parts or not rel.parts:
            raise ValueError("Недопустимый путь")
        normalized = rel.as_posix()
        # Re-run the proof immediately before mutation; never trust stale GUI data.
        head = self._run("rev-parse", f"HEAD:{normalized}")
        index = self._run("rev-parse", f":{normalized}")
        target = (self.root / rel).resolve()
        if not target.is_file() or self.root not in target.parents:
            raise ValueError("Файл отсутствует или выходит за пределы проекта")
        worktree = self._run("hash-object", "--", normalized)
        if not (head == index == worktree):
            raise ValueError("Содержимое HEAD, индекса и файла различается. Автоматическое исправление заблокировано.")
        status = subprocess.run(["git", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false",
                                 "status", "--porcelain=v2", "-z", "--", normalized],
                                cwd=self.root, capture_output=True, timeout=20, shell=False)
        if status.returncode or b"1 D." not in status.stdout:
            raise ValueError("Противоречие больше не подтверждается. Обнови диагностику.")
        index_path_text = self._run("rev-parse", "--git-path", "index")
        index_path = Path(index_path_text)
        if not index_path.is_absolute(): index_path = self.root / index_path
        index_path = index_path.resolve()
        if not index_path.is_file(): raise RuntimeError("Файл индекса Git не найден; исправление отменено")
        lock_path = index_path.with_name(index_path.name + ".lock")
        if lock_path.exists(): raise RuntimeError("Обнаружен index.lock. Закрой другие операции Git и повтори диагностику")
        backup = index_path.with_name(index_path.name + f".doctor-backup-{int(time.time())}")
        shutil.copy2(index_path, backup)
        try:
            self._run("update-index", "--force-remove", "--", normalized)
            self._run("update-index", "--add", "--", normalized)
            verify = self.doctor()
            if any(i.get("path") == normalized for i in verify.get("issues", [])):
                raise RuntimeError("Противоречие сохранилось после обновления индекса")
            return {"ok": True, "message": "Запись индекса восстановлена. Содержимое файла не менялось.",
                    "backup": str(backup), "verification": verify}
        except Exception:
            shutil.copy2(backup, index_path)
            raise

    def sync(self, action: str) -> dict:
        if not self.is_repo(): raise ValueError("Git-репозиторий не инициализирован")
        if action not in {"fetch","pull","push"}: raise ValueError("Недопустимая операция")
        if action in {"pull","push"}:
            check=subprocess.run(["git","status","--porcelain"],cwd=self.root,capture_output=True,text=True,timeout=15,shell=False)
            if check.returncode or check.stdout.strip(): raise ValueError("Сначала разберись с локальными изменениями. Pull/Push заблокирован.")
        out=self._run(action, timeout=180)
        return {"ok": True, "message": out or f"{action} выполнен"}
