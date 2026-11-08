#!/usr/bin/env python3
"""Safe incremental Git synchronization for AI-Knowledge repositories.

Fetches missing Git objects even when the worktree is dirty, preserves local
commits in backup refs and emits an exact durable index manifest. Fetch never changes
checked-out files. A clean worktree is advanced to its configured upstream; local-only
commits are retained in backup refs and are not silently merged. Dirty worktrees remain blocked.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, tempfile
from pathlib import Path


def run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run(["git", "-C", str(repo), *args], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="surrogateescape")
    if check and p.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip() or p.stdout.strip()}")
    return p


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=True, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise


def backup_ref(repo: Path, old: str, name: str) -> str:
    ref = f"refs/backup/ai-knowledge/{name}/{old[:12]}"
    run(repo, "update-ref", ref, old)
    return ref


def parse_name_status(repo: Path, old: str, new: str, prefix: str):
    p = run(repo, "diff", "--name-status", "-z", "-M", old, new)
    fields = p.stdout.split("\0")
    paths, deleted = set(), set()
    i = 0
    while i < len(fields) and fields[i]:
        status = fields[i]; i += 1
        code = status[:1]
        if code in ("R", "C"):
            old_path, new_path = fields[i], fields[i+1]; i += 2
            if code == "R": deleted.add(prefix + old_path.replace("\\", "/"))
            paths.add(prefix + new_path.replace("\\", "/"))
        else:
            path = fields[i]; i += 1
            key = prefix + path.replace("\\", "/")
            if code == "D": deleted.add(key)
            else: paths.add(key)
    return paths, deleted


def merge_manifest(manifest_path: Path, name: str, old: str, new: str, paths, deleted):
    data = {"version": 1, "paths": [], "deleted": [], "repositories": {}}
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            if isinstance(existing, dict) and existing.get("version") == 1:
                data = existing
        except Exception as exc:
            raise RuntimeError(f"Нельзя прочитать незавершённый манифест {manifest_path}: {exc}")
    data["paths"] = sorted(set(data.get("paths", [])) | set(paths))
    data["deleted"] = sorted(set(data.get("deleted", [])) | set(deleted))
    data.setdefault("repositories", {})[name] = {"old": old, "new": new}
    atomic_json(manifest_path, data)


def sync_one(base: Path, name: str, url: str, manifest_path: Path):
    repo = base / "code" / name
    if not (repo / ".git").exists():
        if repo.exists():
            raise RuntimeError(f"{name}: папка существует, но это не Git-репозиторий; сохранена")
        repo.parent.mkdir(parents=True, exist_ok=True)
        run(base, "clone", "--depth", "1", url, str(repo))
        head = run(repo, "rev-parse", "HEAD").stdout.strip()
        tree = run(repo, "ls-tree", "-r", "--name-only", "-z", head).stdout.split("\0")
        initial_paths = {f"code/{name}/" + x.replace("\\", "/") for x in tree if x}
        merge_manifest(manifest_path, name, "", head, initial_paths, set())
        print(f"{name}: первичное клонирование; файлов в очереди индексации: {len(initial_paths)}")
        return

    # Validate the pending index queue before moving the checked-out branch.
    if manifest_path.exists():
        try:
            pending = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            if not isinstance(pending, dict) or pending.get("version") != 1:
                raise ValueError("неподдерживаемая версия")
            if not isinstance(pending.get("paths", []), list) or not isinstance(pending.get("deleted", []), list):
                raise ValueError("некорректная структура paths/deleted")
        except Exception as exc:
            raise RuntimeError(f"{name}: манифест индексации повреждён; обновление остановлено до изменения ветки: {exc}")

    old = run(repo, "rev-parse", "HEAD").stdout.strip()
    upstream = run(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}", check=False)
    if upstream.returncode:
        remotes = run(repo, "remote", "-v").stdout
        if url not in remotes:
            raise RuntimeError(f"{name}: upstream не настроен и URL не совпадает с remote; требуется ручная проверка")
        branch = run(repo, "branch", "--show-current").stdout.strip()
        remote_names = run(repo, "remote").stdout.splitlines()
        if not branch or not remote_names:
            raise RuntimeError(f"{name}: невозможно определить ветку/upstream автоматически")
        remote = remote_names[0].strip()
    else:
        candidate_name = upstream.stdout.strip()
        if "/" not in candidate_name:
            raise RuntimeError(f"{name}: некорректное имя upstream: {candidate_name}")
        remote, branch = candidate_name.split("/", 1)

    # Explicit refspec guarantees that the exact remote-tracking ref used below is refreshed.
    tracking_ref = f"refs/remotes/{remote}/{branch}"
    run(repo, "fetch", "--no-tags", remote, f"+refs/heads/{branch}:{tracking_ref}")
    print(f"{name}: fetch обновил {tracking_ref}; рабочие файлы пока не менялись")

    status = run(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    if status:
        raise RuntimeError(f"{name}: fetch выполнен, но рабочая копия содержит локальные/неотслеживаемые изменения. Они сохранены; сначала разберись с ними через Git Doctor.")

    new = run(repo, "rev-parse", tracking_ref).stdout.strip()
    if old == new:
        print(f"{name}: уже синхронизирован с upstream; изменений нет")
        return

    counts = run(repo, "rev-list", "--left-right", "--count", f"{old}...{new}").stdout.split()
    ahead, behind = int(counts[0]), int(counts[1])
    if behind == 0:
        print(f"{name}: удалённых обновлений нет; локальные коммиты остаются активными ({ahead} впереди)")
        return

    # Preserve the complete previous local tip before moving the active branch.
    # This is an explicit update-to-upstream policy, not a merge/rebase.
    ref = backup_ref(repo, old, name) if ahead else None
    moved = run(repo, "reset", "--keep", new, check=False)
    if moved.returncode:
        detail = moved.stderr.strip() or moved.stdout.strip()
        raise RuntimeError(f"{name}: обновление до upstream не применено; ветка должна остаться на прежнем HEAD. Резервная ссылка: {ref or 'не требовалась'}. {detail}")

    new_head = run(repo, "rev-parse", "HEAD").stdout.strip()
    if new_head != new:
        raise RuntimeError(f"{name}: после обновления HEAD не совпадает с upstream; предыдущая история сохранена: {ref or old}")
    post_status = run(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    if post_status:
        raise RuntimeError(f"{name}: HEAD обновлён, но рабочая копия не чистая. Локальная история сохранена: {ref or old}; проверь Git Doctor.")

    paths, deleted = parse_name_status(repo, old, new_head, f"code/{name}/")
    merge_manifest(manifest_path, name, old, new_head, paths, deleted)
    print(f"{name}: обновлён до upstream; было локально впереди {ahead}, удалённо впереди {behind}")
    if ref:
        print(f"{name}: локальная история сохранена в {ref} (не вливалась автоматически)")
    print(f"{name}: изменено путей {len(paths)}; удалено {len(deleted)}; HEAD {new_head[:12]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--manifest", required=True)
    a = ap.parse_args()
    try:
        sync_one(Path(a.base).resolve(), a.name, a.url, Path(a.manifest).resolve())
        return 0
    except Exception as exc:
        print(f"ОШИБКА Git {a.name}: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
