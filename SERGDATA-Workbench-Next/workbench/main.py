from pathlib import Path
from ipaddress import ip_address
from urllib.parse import urlsplit
import asyncio
import logging
import secrets
import traceback
import threading
import time
import subprocess
import sqlite3
import json
import os
import re
import shutil
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn
from workbench.config import load_config
from workbench.db import Store
from workbench.tools import ProjectTools
from workbench.agent import Agent, estimate_tokens
from workbench.attachments import extract_document, _safe_name
from workbench.handoff import collect_handoff_scope
from workbench.execution_resume import run_after_branch_task

cfg=load_config(); BASE=Path(__file__).parent
# This build handles credentials and privileged local actions. It is deliberately
# loopback-only until an authenticated remote-access mode is implemented.
try:
    if cfg.host.casefold() != 'localhost' and not ip_address(cfg.host).is_loopback:
        raise RuntimeError('SERGDATA Workbench разрешён только на localhost/127.0.0.1/::1. Удалённый bind без аутентификации запрещён.')
except ValueError as exc:
    raise RuntimeError('Некорректный HOST: разрешены только localhost и loopback IP') from exc
legacy=BASE/'migration'/'legacy-workbench.sqlite3'
store=Store(BASE/'.workbench'/'workbench.sqlite3',legacy if legacy.exists() else None)
if not store.has_app_settings():
    store.set_app_settings({'context_limit':cfg.context_limit,'max_tool_rounds':cfg.max_tool_rounds,'max_tool_calls':24,'temperature':0.2,'request_timeout':180,'default_project_id':None})

def default_project_row():
    settings = store.get_app_settings()
    project_id = settings.get('default_project_id')
    row = store.project(project_id) if project_id else None
    if row and not row.get('archived_at') and Path(row['root']).is_dir():
        return row
    projects = store.projects()
    return projects[0] if projects else None

# This is only a harmless fallback for prompt metadata when no project-bound
# branch exists. Real file tools always resolve the branch's registered project.
proj = default_project_row()
project = ProjectTools(Path(proj['root']) if proj else BASE)
agent = Agent(cfg,store,project)
ACTIVE_EXECUTIONS={}
ACTIVE_EXECUTIONS_LOCK=threading.RLock()
# One cancellable model request per branch. Cancelling this task interrupts the
# in-flight async LM Studio request without touching separately queued executions.
CHAT_TASKS={}
CHAT_TASKS_LOCK=threading.RLock()
CHAT_ACTIVITY={}
CHAT_ACTIVITY_LOCK=threading.RLock()
def set_chat_activity(branch_id, stage, detail=''):
    with CHAT_ACTIVITY_LOCK:
        CHAT_ACTIVITY[int(branch_id)]={'stage':str(stage or 'idle')[:40], 'detail':str(detail or '')[:160], 'updated_at':time.time()}
def get_chat_activity(branch_id):
    with CHAT_ACTIVITY_LOCK:
        return dict(CHAT_ACTIVITY.get(int(branch_id), {'stage':'idle','detail':'','updated_at':0}))
agent.activity_callback=set_chat_activity
SHUTTING_DOWN=False
logger = logging.getLogger('uvicorn.error')
RESUME_FUTURES=set()
RESUME_FUTURES_LOCK=threading.RLock()
def _forget_resume_future(done):
    with RESUME_FUTURES_LOCK:
        RESUME_FUTURES.discard(done)


def _log_resume_future(done):
    try:
        error = done.exception()
    except Exception:
        logger.exception("Не удалось получить результат фонового продолжения выполнения")
        return
    if error is not None:
        logger.error("Фоновое продолжение выполнения завершилось ошибкой: %s", error,
                     exc_info=(type(error), error, error.__traceback__))


async def run_execution_resume(branch_id: int, execution_id: int, result_text: str):
    return await run_after_branch_task(
        branch_id,
        lambda: agent.resume_execution(execution_id, result_text),
        CHAT_TASKS, CHAT_TASKS_LOCK, run_tracked_agent_task, lambda: SHUTTING_DOWN
    )


async def run_tracked_agent_task(branch_id: int, awaitable):
    """Register model continuations so /api/chat/status and /cancel see them."""
    task = asyncio.current_task()
    bid = int(branch_id)
    with CHAT_TASKS_LOCK:
        existing = CHAT_TASKS.get(bid)
        if existing and not existing.done() and existing is not task:
            if hasattr(awaitable, 'close'):
                awaitable.close()
            raise HTTPException(409, 'Для этой ветки уже выполняется продолжение модели')
        CHAT_TASKS[bid] = task
    set_chat_activity(bid, 'model_generation', 'Продолжение агентного цикла')
    try:
        return await awaitable
    finally:
        with CHAT_TASKS_LOCK:
            if CHAT_TASKS.get(bid) is task:
                CHAT_TASKS.pop(bid, None)
        if get_chat_activity(bid).get('stage') not in {'waiting_input','waiting_approval'}:
            set_chat_activity(bid, 'idle', '')

async def _resume_startup_continuations():
    """Resume saved model conversations after HTTP startup, never during lifespan startup.

    Only already-completed execution results and submitted input results are resumed.
    This function never re-runs PowerShell/SSH commands. A slow/unavailable local LLM
    therefore cannot prevent Uvicorn from becoming ready.
    """
    # Resume only completed results whose continuation had not yet started.
    try:
        executions = store.executions_waiting_resume()
    except Exception:
        logger.exception("Не удалось получить продолжения выполнений для фонового восстановления")
        executions = []
    for completed in executions:
        if SHUTTING_DOWN:
            return
        try:
            await run_execution_resume(
                int(completed['branch_id']), completed['id'], completed.get('result', '')
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            store.mark_execution_resumed(completed['id'], 'failed')
            store.add_message(completed['branch_id'], 'assistant',
                              f"Не удалось восстановить продолжение выполнения #{completed['id']}: {type(exc).__name__}. Проверь задачу вручную.",
                              metadata={'kind':'execution_resume_startup_error','execution_id':completed['id']})
    try:
        input_requests = store.input_requests_waiting_resume()
    except Exception:
        logger.exception("Не удалось получить запросы ввода для фонового восстановления")
        input_requests = []
    for completed in input_requests:
        if SHUTTING_DOWN:
            return
        try:
            await run_tracked_agent_task(
                int(completed['branch_id']),
                agent.resume_input_request(completed['id'])
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            store.mark_input_request_resumed(completed['id'], 'failed')
            store.add_message(completed['branch_id'], 'assistant',
                              f"Не удалось восстановить продолжение пользовательского ввода #{completed['id']}: {type(exc).__name__}.",
                              metadata={'kind':'input_resume_startup_error','input_request_id':completed['id']})

@asynccontextmanager
async def lifespan(app):
    global SHUTTING_DOWN
    SHUTTING_DOWN=False
    agent.credentials.prune(store.credential_refs())
    await agent.connect()
    # A process registry is intentionally in-memory. Never silently re-run a command
    # after a Workbench restart: mark uncertain executions and tell the user to inspect.
    for interrupted in store.recover_interrupted_executions():
        store.add_message(interrupted['branch_id'], 'tool',
                          f"Выполнение #{interrupted['id']} прервано перезапуском Workbench. Фактический результат неизвестен. Проверь состояние операции вручную; автоматический повтор запрещён.",
                          metadata={'kind':'execution_interrupted','execution_id':interrupted['id']})
    for interrupted in store.recover_interrupted_execution_resumes():
        store.add_message(interrupted['branch_id'], 'assistant',
                          f"Продолжение выполнения #{interrupted['id']} было прервано перезапуском Workbench. Результат команды сохранён, но повторное выполнение/продолжение не запускается автоматически.",
                          metadata={'kind':'execution_resume_interrupted','execution_id':interrupted['id']})
    for interrupted in store.recover_interrupted_input_resumes():
        store.add_message(interrupted['branch_id'], 'assistant',
                          f"Автоматическое продолжение запроса ввода #{interrupted['id']} было прервано перезапуском. Запрос не повторён автоматически; проверь задачу и при необходимости повтори ввод.",
                          metadata={'kind':'input_resume_interrupted','input_request_id':interrupted['id']})
    # Start model continuations in the background only after the app is ready.
    # They consume saved results; they do not execute the original OS/SSH command.
    startup_resume_task = asyncio.create_task(
        _resume_startup_continuations(), name='workbench-startup-resume')
    try:
        yield
    finally:
        SHUTTING_DOWN=True
        if not startup_resume_task.done():
            startup_resume_task.cancel()
        await asyncio.gather(startup_resume_task, return_exceptions=True)
        SHUTTING_DOWN=True
        from workbench.processes import processes
        processes.stop_all()
        with RESUME_FUTURES_LOCK:
            futures=list(RESUME_FUTURES)
        for future in futures:
            future.cancel()
        if futures:
            await asyncio.gather(*(asyncio.wrap_future(f) for f in futures), return_exceptions=True)
        await agent.close()

app=FastAPI(title='SERGDATA Workbench', lifespan=lifespan)

@app.middleware('http')
async def local_origin_guard(request, call_next):
    fetch_site = request.headers.get('sec-fetch-site', '').casefold()
    if fetch_site in {'cross-site', 'same-site'}:
        return JSONResponse({'detail':'Cross-site запрос к локальному Workbench заблокирован'}, status_code=403)
    host = (request.url.hostname or '').casefold()
    if host != 'localhost':
        try:
            if not ip_address(host).is_loopback:
                return JSONResponse({'detail':'Workbench доступен только с локального компьютера'}, status_code=403)
        except ValueError:
            return JSONResponse({'detail':'Недопустимый Host'}, status_code=403)
    origin = request.headers.get('origin')
    if origin:
        parsed = urlsplit(origin)
        origin_host = (parsed.hostname or '').casefold()
        origin_is_local = origin_host == 'localhost'
        if not origin_is_local:
            try:
                origin_is_local = ip_address(origin_host).is_loopback
            except ValueError:
                origin_is_local = False
        if not origin_is_local or parsed.netloc.casefold() != request.headers.get('host','').casefold():
            return JSONResponse({'detail':'Cross-origin запрос заблокирован'}, status_code=403)
    return await call_next(request)

app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')

class ChatIn(BaseModel): branch_id:int; text:str; attachment_ids:list[int]=Field(default_factory=list)
class NameIn(BaseModel): name:str
class ProjectIn(BaseModel): name:str; root:str
class TaskIn(BaseModel): name:str; project_id:int
class ContinueTaskIn(BaseModel): branch_id:int; name:str|None=None; recent_messages:int=12; scope:str='branch'
class ContextPreviewIn(BaseModel): branch_id:int; text:str; attachment_ids:list[int]=Field(default_factory=list)
class ContextImportIn(BaseModel): project_id:int; mode:str; content:str; name:str='Импортированный контекст'; task_id:int|None=None; branch_id:int|None=None
class AutonomyIn(BaseModel): autonomy:str
class AgentSettingsIn(BaseModel):
    context_limit:int=Field(ge=8192,le=262144)
    max_tool_rounds:int=Field(ge=1,le=32)
    max_tool_calls:int=Field(ge=1,le=64)
    temperature:float=Field(ge=0.0,le=1.0)
    request_timeout:int=Field(ge=30,le=600)
    default_project_id:int|None=None
class UserInputSubmit(BaseModel):
    value:str=Field(default='',max_length=8000)
    remember:bool=False

class ServerProfileIn(BaseModel):
    profile_id:int|None=None
    name:str=Field(min_length=1,max_length=80)
    host:str=Field(min_length=1,max_length=253)
    port:int=Field(ge=1,le=65535)
    username:str=Field(min_length=1,max_length=32)
    auth_method:str='key'
    password:str=Field(default='',max_length=16384)
    remember_password:bool=False


@app.get('/')
def index(): return FileResponse(BASE/'static'/'index.html', headers={'Cache-Control':'no-store, no-cache, must-revalidate, max-age=0','Pragma':'no-cache'})

# Optional Knowledge management. Existing MCP integration remains untouched.
KNOWLEDGE_JOB = {"running": False, "output": "", "returncode": None, "source": "",
                 "stop_requested": False, "stopped": False, "process_id": None, "status": "idle"}
KNOWLEDGE_JOB_LOCK = threading.RLock()
KNOWLEDGE_PROCESS = None

def _knowledge_paths():
    root = cfg.kb_cwd.expanduser().resolve()
    server = cfg.kb_server.expanduser().resolve()
    script = root / "kb.py"
    db = root / "index" / "knowledge.db"
    return root, server, script, db

def _knowledge_status_data():
    root, server, script, db = _knowledge_paths()
    available = bool(cfg.kb_enabled and server.is_file() and script.is_file())
    count = None
    if db.is_file():
        try:
            with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=2) as con:
                count = con.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        except Exception:
            count = None
    with KNOWLEDGE_JOB_LOCK:
        job = dict(KNOWLEDGE_JOB)
    return {"available": available, "enabled": bool(cfg.kb_enabled),
            "root": str(root), "database_exists": db.is_file(),
            "indexed_files": count, "job": job}

def _terminate_knowledge_process(proc):
    """Terminate the PowerShell/Python process tree without leaving child indexers behind."""
    if proc is None or proc.poll() is not None:
        return False
    try:
        if os.name == "nt":
            killer = shutil.which("taskkill")
            if killer:
                subprocess.run([killer, "/PID", str(proc.pid), "/T", "/F"],
                               capture_output=True, timeout=12, shell=False)
            if proc.poll() is None:
                proc.terminate()
        else:
            import signal
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass
    return True


def _run_knowledge_index(command, cwd):
    """Run a Knowledge job, stream progress, and support stopping the full child process tree."""
    global KNOWLEDGE_PROCESS
    proc = None
    try:
        kwargs = {}
        if os.name != "nt":
            kwargs["start_new_session"] = True
        else:
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        proc = subprocess.Popen(
            command, cwd=str(cwd), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8",
            errors="replace", bufsize=0, shell=False, **kwargs
        )
        with KNOWLEDGE_JOB_LOCK:
            KNOWLEDGE_PROCESS = proc
            KNOWLEDGE_JOB["process_id"] = proc.pid
            stop_now = bool(KNOWLEDGE_JOB.get("stop_requested"))
        if stop_now:
            _terminate_knowledge_process(proc)

        tail = ""
        current = ""
        while True:
            char = proc.stdout.read(1)
            if char == "" and proc.poll() is not None:
                break
            if not char:
                continue
            if char in ("\r", "\n"):
                if current:
                    tail = (tail + current + "\n")[-12000:]
                    current = ""
                    with KNOWLEDGE_JOB_LOCK:
                        KNOWLEDGE_JOB.update({"output": tail})
            else:
                current += char
                if len(current) > 4000:
                    current = current[-4000:]
                if len(current) % 80 == 0:
                    with KNOWLEDGE_JOB_LOCK:
                        KNOWLEDGE_JOB.update({"output": (tail + current)[-12000:]})
        if current:
            tail = (tail + current + "\n")[-12000:]
        returncode = proc.wait()
        with KNOWLEDGE_JOB_LOCK:
            stopped = bool(KNOWLEDGE_JOB.get("stop_requested"))
            KNOWLEDGE_JOB.update({"running": False, "output": tail,
                                  "returncode": returncode, "finished_at": time.time(),
                                  "stopped": stopped, "status": "stopped" if stopped else ("completed" if returncode == 0 else "failed"),
                                  "process_id": None})
    except Exception as exc:
        with KNOWLEDGE_JOB_LOCK:
            stopped = bool(KNOWLEDGE_JOB.get("stop_requested"))
            KNOWLEDGE_JOB.update({"running": False,
                                  "output": f"{type(exc).__name__}: {exc}",
                                  "returncode": -2 if stopped else -1, "finished_at": time.time(),
                                  "stopped": stopped, "status": "stopped" if stopped else "failed",
                                  "process_id": None})
    finally:
        with KNOWLEDGE_JOB_LOCK:
            KNOWLEDGE_PROCESS = None


@app.get('/api/knowledge/status')
def knowledge_status():
    return _knowledge_status_data()

@app.post('/api/knowledge/stop')
def knowledge_stop():
    """Request cancellation of the active Knowledge indexing/sync job."""
    with KNOWLEDGE_JOB_LOCK:
        if not KNOWLEDGE_JOB.get("running"):
            return {"ok": True, "running": False, "stopping": False,
                    "message": "Активной операции нет"}
        KNOWLEDGE_JOB["stop_requested"] = True
        KNOWLEDGE_JOB["output"] = (KNOWLEDGE_JOB.get("output", "") +
                                   "\nЗапрошена остановка пользователем…\n")[-12000:]
        proc = KNOWLEDGE_PROCESS
    if proc is None:
        return {"ok": True, "running": True, "stopping": True,
                "message": "Остановка запрошена; ожидается запуск процесса."}
    _terminate_knowledge_process(proc)
    return {"ok": True, "running": True, "stopping": True,
            "message": "Запрос остановки отправлен процессу и его дочерним процессам."}

class KnowledgeIndexIn(BaseModel):
    path: str = Field(min_length=1, max_length=2000)

@app.post('/api/knowledge/index')
def knowledge_index(data: KnowledgeIndexIn):
    root, server, script, db = _knowledge_paths()
    if not cfg.kb_enabled or not script.is_file():
        raise HTTPException(409, "AI-Knowledge не обнаружена или отключена")
    candidate = Path(data.path.strip().strip('"')).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        candidate = candidate.resolve(strict=True)
    except OSError:
        raise HTTPException(400, "Указанный путь не существует")
    allowed = False
    try:
        candidate.relative_to(root)
        allowed = True
    except ValueError:
        for source in _read_registry("sources.json", "sources")["sources"]:
            try:
                Path(source.get("path", "")).expanduser().resolve(strict=True)
                candidate.relative_to(Path(source.get("path", "")).expanduser().resolve(strict=True))
                allowed = True
                break
            except (ValueError, OSError, AttributeError):
                continue
    if not allowed:
        raise HTTPException(400, "Путь должен находиться внутри AI-Knowledge или зарегистрированного внешнего источника")
    if not (candidate.is_file() or candidate.is_dir()):
        raise HTTPException(400, "Указанный путь не является файлом или папкой")
    with KNOWLEDGE_JOB_LOCK:
        if KNOWLEDGE_JOB["running"]:
            raise HTTPException(409, "Индексация уже выполняется")
        KNOWLEDGE_JOB.update({"running": True, "output": "Индексация запущена…",
                              "returncode": None, "source": str(candidate),
                              "started_at": time.time(), "finished_at": None,
                              "phase": "index", "stop_requested": False,
                              "stopped": False, "process_id": None, "status": "running"})
    command = [cfg.kb_python, str(script), "index", "--no-release-sync", "--path", str(candidate)]
    threading.Thread(target=_run_knowledge_index, args=(command, root),
                     name="knowledge-index", daemon=True).start()
    return {"ok": True, "message": "Индексация запущена", "source": str(candidate)}


# Registry management is intentionally metadata-only: deleting an entry never
# deletes a clone, source directory, or indexed document.
def _knowledge_registry_path(filename):
    root, _, _, _ = _knowledge_paths()
    return root / filename

def _read_registry(filename, key):
    path = _knowledge_registry_path(filename)
    if not path.exists():
        return {key: []}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        rows = data.get(key, []) if isinstance(data, dict) else []
        if not isinstance(rows, list):
            raise ValueError(f"Поле {key} должно быть списком")
        return {key: rows}
    except Exception as exc:
        raise HTTPException(500, f"Не удалось прочитать {filename}: {exc}")

def _write_registry(filename, data):
    path = _knowledge_registry_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)

class KnowledgeSourceIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    path: str = Field(min_length=1, max_length=2000)

class KnowledgeRepositoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    url: str = Field(min_length=4, max_length=1000)

@app.get('/api/knowledge/sources')
def knowledge_sources():
    return _read_registry("sources.json", "sources")

@app.post('/api/knowledge/sources')
def knowledge_source_add(data: KnowledgeSourceIn):
    root, _, script, _ = _knowledge_paths()
    if not script.is_file(): raise HTTPException(409, "AI-Knowledge не обнаружена")
    candidate = Path(data.path.strip().strip('"')).expanduser()
    try: candidate = candidate.resolve(strict=True)
    except OSError: raise HTTPException(400, "Папка не существует")
    if not candidate.is_dir(): raise HTTPException(400, "Источник должен быть папкой")
    try: candidate.relative_to(root)
    except ValueError: pass
    else: raise HTTPException(400, "Внешний источник уже находится внутри AI-Knowledge")
    registry = _read_registry("sources.json", "sources")
    rows = registry["sources"]
    if any(str(x.get("path", "")).casefold() == str(candidate).casefold() for x in rows if isinstance(x, dict)):
        raise HTTPException(409, "Эта папка уже зарегистрирована")
    base = re.sub(r"[^a-zA-Z0-9_-]+", "-", data.name.strip()).strip("-_").lower() or "source"
    sid, n = base, 2
    existing = {str(x.get("id", "")).lower() for x in rows if isinstance(x, dict)}
    while sid in existing: sid, n = f"{base}-{n}", n + 1
    rows.append({"id": sid, "name": data.name.strip(), "path": str(candidate), "enabled": True})
    _write_registry("sources.json", registry)
    return {"ok": True, "source": rows[-1]}

@app.delete('/api/knowledge/sources/{source_id}')
def knowledge_source_delete(source_id: str):
    registry = _read_registry("sources.json", "sources")
    before = len(registry["sources"])
    registry["sources"] = [x for x in registry["sources"] if not (isinstance(x, dict) and x.get("id") == source_id)]
    if len(registry["sources"]) == before: raise HTTPException(404, "Источник не найден")
    _write_registry("sources.json", registry)
    return {"ok": True, "message": "Запись удалена; файлы и индекс не затронуты"}

@app.get('/api/knowledge/repositories')
def knowledge_repositories():
    return _read_registry("repositories.json", "repositories")

@app.post('/api/knowledge/repositories')
def knowledge_repository_add(data: KnowledgeRepositoryIn):
    name = data.name.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", name):
        raise HTTPException(400, "Имя: латинские буквы, цифры, точка, дефис или подчёркивание")
    url = data.url.strip()
    if not (url.startswith("https://") or url.startswith("ssh://") or re.fullmatch(r"[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+:.+", url)):
        raise HTTPException(400, "Разрешены HTTPS и SSH Git URL")
    registry = _read_registry("repositories.json", "repositories")
    if any(str(x.get("name", "")).casefold() == name.casefold() for x in registry["repositories"] if isinstance(x, dict)):
        raise HTTPException(409, "Репозиторий с таким именем уже есть")
    registry["repositories"].append({"name": name, "url": url})
    _write_registry("repositories.json", registry)
    return {"ok": True, "repository": registry["repositories"][-1]}

@app.delete('/api/knowledge/repositories/{name}')
def knowledge_repository_delete(name: str):
    registry = _read_registry("repositories.json", "repositories")
    before = len(registry["repositories"])
    registry["repositories"] = [x for x in registry["repositories"] if not (isinstance(x, dict) and str(x.get("name", "")).casefold() == name.casefold())]
    if len(registry["repositories"]) == before: raise HTTPException(404, "Репозиторий не найден")
    _write_registry("repositories.json", registry)
    return {"ok": True, "message": "Запись удалена; локальная папка и индекс не затронуты"}

@app.post('/api/knowledge/full-update')
def knowledge_full_update():
    root, _, script, _ = _knowledge_paths()
    if not cfg.kb_enabled or not script.is_file(): raise HTTPException(409, "AI-Knowledge не обнаружена или отключена")
    repos = _read_registry("repositories.json", "repositories")["repositories"]
    if not repos: raise HTTPException(409, "Список repositories.json пуст. Сначала добавьте Git-репозитории.")
    updater = root / "update-knowledge.ps1"
    if not updater.is_file(): raise HTTPException(404, "update-knowledge.ps1 не найден")
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell: raise HTTPException(409, "PowerShell не найден (нужен pwsh или Windows PowerShell)")
    with KNOWLEDGE_JOB_LOCK:
        if KNOWLEDGE_JOB["running"]: raise HTTPException(409, "Операция с базой знаний уже выполняется")
        KNOWLEDGE_JOB.update({"running": True, "output": "Запущено обновление Git → Release Notes → индекс…", "returncode": None,
                              "source": "Полная синхронизация", "started_at": time.time(), "finished_at": None,
                              "phase": "full-update", "stop_requested": False,
                              "stopped": False, "process_id": None, "status": "running"})
    command = [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(updater), "-BasePath", str(root), "-PythonPath", cfg.kb_python, "-NoPause"]
    threading.Thread(target=_run_knowledge_index, args=(command, root), name="knowledge-full-update", daemon=True).start()
    return {"ok": True, "message": "Полная синхронизация запущена"}


class KnowledgeGitDoctorIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def _knowledge_git_doctor_repo(name: str) -> Path:
    root, _, _, _ = _knowledge_paths()
    code_root = (root / "code").resolve()
    # Registry membership is required; user-supplied names never become arbitrary paths.
    rows = _read_registry("repositories.json", "repositories")["repositories"]
    if not any(isinstance(row, dict) and str(row.get("name", "")) == name for row in rows):
        raise HTTPException(404, "Репозиторий не зарегистрирован в repositories.json")
    repo = (code_root / name).resolve()
    if code_root not in repo.parents:
        raise HTTPException(400, "Недопустимый путь репозитория")
    if not repo.is_dir():
        raise HTTPException(404, "Локальный клон не найден в AI-Knowledge/code")
    git = shutil.which("git")
    if not git:
        raise HTTPException(503, "Git не найден в PATH")
    return repo


@app.get('/api/knowledge/git-doctor/repositories')
def knowledge_git_doctor_repositories():
    root, _, _, _ = _knowledge_paths()
    code_root = (root / "code").resolve()
    rows = _read_registry("repositories.json", "repositories")["repositories"]
    found = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", ""))
        if not name or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", name):
            continue
        candidate = (code_root / name).resolve()
        if code_root in candidate.parents and candidate.is_dir() and (candidate / ".git").exists():
            found.append({"name": name})
    return {"repositories": found}


@app.post('/api/knowledge/git-doctor/inspect')
def knowledge_git_doctor_inspect(data: KnowledgeGitDoctorIn):
    repo = _knowledge_git_doctor_repo(data.name)
    git = shutil.which("git")
    def run(*args):
        try:
            result = subprocess.run([git, "-C", str(repo), *args], capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=25, shell=False)
        except subprocess.TimeoutExpired:
            raise HTTPException(504, "Git-команда превысила лимит времени")
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    rc, top, err = run("rev-parse", "--show-toplevel")
    if rc or Path(top).resolve() != repo:
        raise HTTPException(409, "Папка не является самостоятельным Git-репозиторием")
    rc, head, err = run("rev-parse", "HEAD")
    if rc:
        raise HTTPException(409, "Не удалось прочитать HEAD: " + err[:400])
    # Use NUL-delimited porcelain output: unlike line parsing, this safely handles
    # spaces, tabs, newlines, quotes and non-ASCII filenames on Windows.
    try:
        result = subprocess.run([git, "-C", str(repo), "status", "--porcelain=v2", "-uall", "-z"],
            capture_output=True, timeout=25, shell=False)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Git status превысил лимит времени")
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace")[:400]
        raise HTTPException(409, "Не удалось прочитать статус: " + detail)
    raw_status = result.stdout
    records = []
    issues = []
    chunks = raw_status.split(b"\0")
    i = 0
    while i < len(chunks):
        item = chunks[i]
        i += 1
        if not item:
            continue
        kind = item[:1]
        path_bytes = b""
        xy = ""
        if kind == b"?":
            path_bytes = item[2:] if item.startswith(b"? ") else item[1:]
            state = "untracked"
        elif kind == b"!":
            path_bytes = item[2:] if item.startswith(b"! ") else item[1:]
            state = "ignored"
        elif kind == b"1":
            fields = item.split(b" ", 8)
            if len(fields) < 9:
                continue
            xy = fields[1].decode("ascii", "replace")
            path_bytes = fields[8]
            state = "tracked"
        elif kind == b"2":
            fields = item.split(b" ", 9)
            if len(fields) < 10:
                continue
            xy = fields[1].decode("ascii", "replace")
            path_bytes = fields[9]
            state = "renamed_or_copied"
            if i < len(chunks):
                i += 1  # original path follows as a second NUL-terminated field
        elif kind == b"u":
            fields = item.split(b" ", 10)
            if len(fields) < 11:
                continue
            xy = fields[1].decode("ascii", "replace")
            path_bytes = fields[10]
            state = "unmerged"
        else:
            continue
        # Git paths are byte strings. Decode with surrogateescape, then create a
        # safe visible representation for unusual/control/private-use characters.
        path = path_bytes.decode("utf-8", "surrogateescape")
        display = path.encode("unicode_escape", "backslashreplace").decode("ascii")
        rec = {"state": state, "xy": xy, "path": display, "path_raw": path}
        records.append(rec)
        if state == "unmerged":
            issues.append({"kind": "merge_conflict", "path": display})
        if "D" in xy:
            issues.append({"kind": "deletion_status_review", "path": display})
        suspicious = (state == "untracked" and (
            any(ord(ch) < 32 or 0xE000 <= ord(ch) <= 0xF8FF or 0xF0000 <= ord(ch) <= 0xFFFFD for ch in path)
            or len(path) > 180
            or any(token in path.casefold() for token in ("foregroundcolor", "write-host", "копироватьудалить", "root@", "powershell"))
        ))
        if suspicious:
            issues.append({"kind": "suspicious_untracked_name", "path": display})
    _, branch, _ = run("branch", "--show-current")
    _, upstream, _ = run("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    ahead = behind = None
    if upstream:
        # Counts compare local HEAD (left) with the last fetched upstream ref (right).
        count_rc, counts, _ = run("rev-list", "--left-right", "--count", f"HEAD...{upstream}")
        if count_rc == 0:
            try: ahead, behind = [int(x) for x in counts.split()[:2]]
            except (ValueError, IndexError): pass
    return {"name": data.name, "path": str(repo), "head": head, "branch": branch,
        "upstream": upstream, "ahead": ahead, "behind": behind,
        "clean": not bool(records), "records": records, "issues": issues,
        "repairable": any(x["state"] == "untracked" for x in records),
        "message": "Диагностика завершена. Обнаружены записи, требующие проверки." if issues else ("Есть изменения в рабочей копии; проверь список записей." if records else "Рабочая копия чистая: незакоммиченных изменений не обнаружено."),
        "status_count": len(records)}


class KnowledgeGitDoctorFileIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=4000)

class KnowledgeGitDoctorRestoreIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    quarantine_id: str = Field(min_length=32, max_length=32)


def _doctor_safe_relative(repo: Path, value: str) -> Path:
    rel = Path(value)
    if rel.is_absolute() or not rel.parts or any(x in ("..", "") for x in rel.parts):
        raise HTTPException(400, "Недопустимый относительный путь")
    candidate = repo / rel
    # Reject symlinks in every path component before resolving. This prevents
    # viewing/moving a target outside the clone through a symlink.
    current = repo
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise HTTPException(400, "Путь содержит символическую ссылку; операция запрещена")
    target = candidate.resolve()
    if repo not in target.parents:
        raise HTTPException(400, "Путь выходит за пределы репозитория")
    return candidate




class KnowledgeGitDoctorUpdateIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)

@app.post('/api/knowledge/git-doctor/update-upstream')
def knowledge_git_doctor_update_upstream(data: KnowledgeGitDoctorUpdateIn):
    """Advance one clean clone to its fetched upstream, preserving local-only commits by backup ref."""
    repo = _knowledge_git_doctor_repo(data.name)
    with KNOWLEDGE_JOB_LOCK:
        if KNOWLEDGE_JOB.get("running"):
            raise HTTPException(409, "Сейчас выполняется индексация/синхронизация. Дождись её завершения.")
    git = shutil.which("git")
    def call(*args, check=True, timeout=180):
        try:
            p = subprocess.run([git, "-C", str(repo), *args], capture_output=True, timeout=timeout, shell=False)
        except subprocess.TimeoutExpired:
            raise HTTPException(504, "Git-команда превысила лимит времени")
        if check and p.returncode:
            msg = (p.stderr or p.stdout).decode("utf-8", "replace")[-3000:]
            raise HTTPException(409, f"Git {' '.join(args[:3])}: {msg or 'ошибка'}")
        return p
    top = call("rev-parse", "--show-toplevel").stdout.decode("utf-8", "replace").strip()
    if Path(top).resolve() != repo:
        raise HTTPException(409, "Папка не является самостоятельным Git-репозиторием")
    branch = call("branch", "--show-current").stdout.decode("utf-8", "replace").strip()
    if not branch:
        raise HTTPException(409, "Detached HEAD: автоматическое обновление запрещено")
    status = call("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    if status:
        raise HTTPException(409, "Рабочая копия не чистая. Сначала проверь tracked/untracked изменения в Git Doctor.")
    upstream = call("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}", check=False)
    if upstream.returncode:
        raise HTTPException(409, "У ветки не настроен upstream. Автоматически выбирать remote нельзя.")
    upstream_name = upstream.stdout.decode("utf-8", "replace").strip()
    if not upstream_name.startswith("refs/remotes/"):
        full = call("rev-parse", "--symbolic-full-name", "@{upstream}").stdout.decode("utf-8", "replace").strip()
        upstream_ref = full
        parts = full.split("/")
        if len(parts) < 4 or parts[1] != "remotes":
            raise HTTPException(409, f"Неожиданный upstream: {full}")
        remote, remote_branch = parts[2], "/".join(parts[3:])
    else:
        upstream_ref = upstream_name
        parts = upstream_ref.split("/")
        remote, remote_branch = parts[2], "/".join(parts[3:])
    old = call("rev-parse", "HEAD").stdout.decode("ascii", "replace").strip()
    # Fetch updates only the configured upstream ref; it does not touch worktree files.
    call("fetch", "--no-tags", remote, f"+refs/heads/{remote_branch}:refs/remotes/{remote}/{remote_branch}")
    target = call("rev-parse", upstream_ref).stdout.decode("ascii", "replace").strip()
    counts = call("rev-list", "--left-right", "--count", f"{old}...{target}").stdout.decode("ascii", "replace").split()
    ahead, behind = (int(counts[0]), int(counts[1]))
    if behind == 0:
        return {"ok": True, "name": data.name, "branch": branch, "ahead": ahead, "behind": 0,
                "message": "Удалённых обновлений нет. Локальная ветка не изменялась.", "backup_ref": None}
    # Load/validate the durable index manifest BEFORE moving HEAD, so a corrupt
    # pending manifest cannot leave an updated repository without an index queue.
    root, _, _, _ = _knowledge_paths()
    manifest_path = root / "index" / "pending-git-changes.json"
    manifest = {"version": 1, "paths": [], "deleted": [], "repositories": {}}
    if manifest_path.exists():
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            if not isinstance(loaded, dict) or loaded.get("version") != 1:
                raise ValueError("неподдерживаемая версия манифеста")
            manifest = loaded
        except Exception as exc:
            raise HTTPException(409, f"Манифест точечной индексации повреждён. Обновление остановлено до исправления манифеста: {exc}")

    backup_ref = None
    if ahead:
        stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", data.name)
        backup_ref = f"refs/backup/ai-knowledge/manual-update/{safe_name}/{stamp}-{old[:12]}"
        # Ref creation is non-destructive; local commits remain reachable even after branch advance.
        call("update-ref", backup_ref, old)
    # --keep refuses if an uncommitted worktree change would be overwritten.
    # Since the worktree was verified clean, it safely advances the active branch.
    moved = call("reset", "--keep", target, check=False)
    if moved.returncode:
        detail = (moved.stderr or moved.stdout).decode("utf-8", "replace")[-2500:]
        now = call("rev-parse", "HEAD").stdout.decode("ascii", "replace").strip()
        if now != old:
            raise HTTPException(500, f"Git reset --keep завершился ошибкой и HEAD изменился неожиданно. Старый HEAD сохранён: {backup_ref or old}. {detail}")
        raise HTTPException(409, f"Обновление не применено; текущая ветка осталась на прежнем коммите. Локальная резервная ссылка: {backup_ref or 'не требовалась'}. {detail}")
    new_head = call("rev-parse", "HEAD").stdout.decode("ascii", "replace").strip()
    if new_head != target:
        raise HTTPException(500, "После обновления HEAD не совпадает с upstream. Требуется ручная проверка.")
    post_status = call("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    if post_status:
        raise HTTPException(500, "После обновления рабочая копия не чистая. Локальные коммиты сохранены в резервной ссылке.")
    changed = call("diff", "--name-only", "-z", old, new_head).stdout.split(b"\0")
    deleted = call("diff", "--name-only", "--diff-filter=D", "-z", old, new_head).stdout.split(b"\0")
    prefix = f"code/{data.name}/"
    paths = {prefix + os.fsdecode(x).replace("\\", "/") for x in changed if x}
    deleted_paths = {prefix + os.fsdecode(x).replace("\\", "/") for x in deleted if x}
    manifest["paths"] = sorted(set(manifest.get("paths", [])) | (paths - deleted_paths))
    manifest["deleted"] = sorted(set(manifest.get("deleted", [])) | deleted_paths)
    manifest.setdefault("repositories", {})[data.name] = {"old": old, "new": new_head}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, manifest_path)
    return {"ok": True, "name": data.name, "branch": branch, "old_head": old, "new_head": new_head,
            "ahead_before": ahead, "behind_before": behind, "backup_ref": backup_ref,
            "indexed_paths": len(paths - deleted_paths), "deleted_paths": len(deleted_paths),
            "message": "Репозиторий обновлён до upstream. Локальные коммиты сохранены в резервной ссылке." if ahead else "Репозиторий обновлён до upstream."}



class KnowledgeGitDoctorRestoreTrackedIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=4000)

@app.post('/api/knowledge/git-doctor/restore-tracked-deletion')
def knowledge_git_doctor_restore_tracked_deletion(data: KnowledgeGitDoctorRestoreTrackedIn):
    """Restore a staged deletion, including Git's D. + duplicate-untracked-file state."""
    repo = _knowledge_git_doctor_repo(data.name)
    with KNOWLEDGE_JOB_LOCK:
        if KNOWLEDGE_JOB.get("running"):
            raise HTTPException(409, "Сейчас выполняется индексация/синхронизация. Дождись её завершения.")
    target = _doctor_safe_relative(repo, data.path)
    git = shutil.which("git")

    def call(*args, check=True):
        p = subprocess.run([git, "-C", str(repo), *args], capture_output=True,
                           timeout=30, shell=False)
        if check and p.returncode:
            raise HTTPException(409, (p.stderr or p.stdout).decode("utf-8", "replace")[-2000:])
        return p

    rel = target.relative_to(repo).as_posix()
    raw = call("status", "--porcelain=v2", "-z", "--", rel).stdout
    records = [x for x in raw.split(b"\\0") if x]
    deletion_records = [x for x in records if x.startswith(b"1 D. ")]
    duplicate_untracked = [x for x in records if x.startswith(b"? ") and x[2:] == os.fsencode(rel)]
    if len(deletion_records) != 1 or len(records) != 1 + len(duplicate_untracked):
        raise HTTPException(409, "Состояние больше не является staged deletion D. (возможно, изменилось). Обнови диагностику.")
    tracked = call("ls-files", "--error-unmatch", "--", rel, check=False)
    if tracked.returncode == 0:
        raise HTTPException(409, "Файл всё ещё присутствует в индексе Git; staged deletion не подтверждён.")
    if call("cat-file", "-e", f"HEAD:{rel}", check=False).returncode:
        raise HTTPException(409, "Файл отсутствует и в HEAD. Автоматическое восстановление запрещено.")

    head_blob = call("show", f"HEAD:{rel}").stdout
    backup_id = None
    if target.exists() or target.is_symlink():
        if target.is_symlink() or not target.is_file():
            raise HTTPException(409, "На месте файла находится ссылка или каталог. Автоматическое восстановление остановлено.")
        current = target.read_bytes()
        if current == head_blob:
            # Only the index needs restoring. Preserve the identical working-tree file in place.
            call("restore", "--source=HEAD", "--staged", "--", rel)
        else:
            # Preserve differing bytes outside the clone before replacing the staged-deletion duplicate.
            root, _, _, _ = _knowledge_paths()
            backup_id = secrets.token_hex(16)
            slot = root / ".doctor-quarantine" / data.name / backup_id
            saved = slot / "files" / Path(rel)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
            manifest = {"version": 1, "quarantine_id": backup_id, "repository": data.name,
                        "relative_path": rel, "reason": "existing file at staged-deletion path",
                        "saved_path": str(saved.relative_to(root))}
            (slot / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\\n", encoding="utf-8")
            call("restore", "--source=HEAD", "--staged", "--worktree", "--", rel)
    else:
        call("restore", "--source=HEAD", "--staged", "--worktree", "--", rel)

    verify = call("status", "--porcelain=v1", "-z", "--", rel).stdout
    if verify:
        raise HTTPException(500, "Восстановление выполнено, но Git продолжает показывать изменение. Резервная копия сохранена.")
    result = {"ok": True, "path": rel,
              "message": "Отслеживаемый файл восстановлен из HEAD; staged deletion отменено."}
    if backup_id:
        result["backup_id"] = backup_id
        result["message"] += " Отличавшаяся версия сохранена в карантине."
    return result


@app.post('/api/knowledge/git-doctor/view')
def knowledge_git_doctor_view(data: KnowledgeGitDoctorFileIn):
    repo = _knowledge_git_doctor_repo(data.name)
    target = _doctor_safe_relative(repo, data.path)
    if not target.is_file() or target.is_symlink():
        raise HTTPException(400, "Просмотр поддерживается только для обычных файлов")
    size = target.stat().st_size
    if size > 1024 * 1024:
        raise HTTPException(413, "Файл больше 1 МБ. Просмотр содержимого отключён; проверь его локально")
    raw = target.read_bytes()
    try: content = raw.decode("utf-8-sig")
    except UnicodeDecodeError: content = raw.decode("utf-8", "replace")
    return {"path": data.path, "size": size, "content": content[:50000],
            "truncated": len(content) > 50000}


@app.post('/api/knowledge/git-doctor/quarantine')
def knowledge_git_doctor_quarantine(data: KnowledgeGitDoctorFileIn):
    repo = _knowledge_git_doctor_repo(data.name)
    target = _doctor_safe_relative(repo, data.path)
    if not target.exists() or target.is_symlink():
        raise HTTPException(404, "Файл не найден или является ссылкой; перемещение отменено")
    # Only untracked items can be quarantined. Tracked edits/deletions must be
    # reviewed or committed explicitly; this endpoint never stages or overwrites.
    check = subprocess.run([shutil.which("git"), "-C", str(repo), "ls-files", "--error-unmatch", "--", data.path],
        capture_output=True, timeout=15, shell=False)
    if check.returncode == 0:
        raise HTTPException(409, "Это отслеживаемый Git-файл. Автоматическое перемещение запрещено")
    status = subprocess.run([shutil.which("git"), "-C", str(repo), "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", data.path],
        capture_output=True, timeout=15, shell=False)
    if status.returncode or not status.stdout.startswith(b"?? "):
        raise HTTPException(409, "Файл больше не подтверждается как неотслеживаемый. Обнови диагностику")
    root, _, _, _ = _knowledge_paths()
    qroot = (root / ".doctor-quarantine" / data.name).resolve()
    qroot.mkdir(parents=True, exist_ok=True)
    import uuid
    qid = uuid.uuid4().hex
    slot = qroot / qid
    slot.mkdir()
    rel = target.relative_to(repo)
    destination = slot / "files" / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(target), str(destination))
        manifest = {"version": 1, "repository": data.name, "quarantine_id": qid,
                    "relative_path": rel.as_posix(), "is_dir": destination.is_dir()}
        (slot / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        # Best-effort rollback if the move completed but manifest writing failed.
        if destination.exists() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(destination), str(target))
        shutil.rmtree(slot, ignore_errors=True)
        raise HTTPException(500, f"Не удалось переместить в карантин: {exc}")
    return {"ok": True, "quarantine_id": qid, "path": rel.as_posix(),
            "message": "Файл перемещён в карантин вне Git-клона. Его можно восстановить."}


@app.get('/api/knowledge/git-doctor/quarantine/{name}')
def knowledge_git_doctor_quarantine_list(name: str):
    _knowledge_git_doctor_repo(name)
    root, _, _, _ = _knowledge_paths()
    qroot = root / ".doctor-quarantine" / name
    items = []
    if qroot.is_dir():
        for manifest_path in sorted(qroot.glob("*/manifest.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                item = json.loads(manifest_path.read_text(encoding="utf-8"))
                if item.get("repository") == name and (manifest_path.parent / "files" / item.get("relative_path", "")).exists():
                    items.append({"quarantine_id": item["quarantine_id"], "path": item["relative_path"]})
            except Exception:
                continue
    return {"items": items[:200]}


@app.post('/api/knowledge/git-doctor/restore')
def knowledge_git_doctor_restore(data: KnowledgeGitDoctorRestoreIn):
    repo = _knowledge_git_doctor_repo(data.name)
    root, _, _, _ = _knowledge_paths()
    slot = (root / ".doctor-quarantine" / data.name / data.quarantine_id).resolve()
    qbase = (root / ".doctor-quarantine" / data.name).resolve()
    if qbase not in slot.parents or not (slot / "manifest.json").is_file():
        raise HTTPException(404, "Запись карантина не найдена")
    try: manifest = json.loads((slot / "manifest.json").read_text(encoding="utf-8"))
    except Exception: raise HTTPException(500, "Повреждён манифест карантина; данные сохранены")
    if manifest.get("repository") != data.name or manifest.get("quarantine_id") != data.quarantine_id:
        raise HTTPException(409, "Манифест не соответствует запросу")
    rel = Path(manifest.get("relative_path", ""))
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise HTTPException(400, "Недопустимый путь восстановления")
    source = slot / "files" / rel
    target = _doctor_safe_relative(repo, rel.as_posix())
    if not source.exists(): raise HTTPException(404, "Файл в карантине не найден")
    if target.exists(): raise HTTPException(409, "В Git-клоне уже существует файл по этому пути. Ничего не перезаписано")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))
    shutil.rmtree(slot, ignore_errors=True)
    return {"ok": True, "path": rel.as_posix(), "message": "Файл восстановлен на исходное место"}


# Native Windows file/folder picker. This only returns a user-selected path;
# it does not modify project files or Knowledge data.
class LocalDialogIn(BaseModel):
    kind: str = Field(pattern='^(folder|file)$')
    initialdir: str = Field(default='', max_length=2000)
    title: str = Field(default='', max_length=200)

@app.post('/api/local-dialog')
def local_dialog(data: LocalDialogIn):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes('-topmost', True)
            kwargs = {'parent': root, 'title': data.title or ('Выбор папки' if data.kind == 'folder' else 'Выбор файла')}
            initial = Path(data.initialdir).expanduser() if data.initialdir else None
            if initial and initial.exists(): kwargs['initialdir'] = str(initial)
            selected = filedialog.askdirectory(**kwargs) if data.kind == 'folder' else filedialog.askopenfilename(**kwargs)
        finally:
            root.destroy()
        return {'path': selected or ''}
    except Exception as exc:
        raise HTTPException(500, f'Не удалось открыть системный диалог: {type(exc).__name__}: {exc}')

@app.get('/api/status')
async def status():
    models=await agent.models()
    selected_default = default_project_row()
    return {'project':selected_default,'projects':store.projects(),'project_root':selected_default['root'] if selected_default else '', 'kb':agent.kb_status,'models':models,'configured_model':cfg.lm_model,'context_limit':store.get_app_settings()['context_limit'],'agent_settings':store.get_app_settings(),'credential_persistence_available':agent.credentials.persistence_available}
class GitPathsIn(BaseModel):
    paths:list[str]=Field(min_length=1,max_length=100)
class GitCommitIn(BaseModel):
    message:str=Field(min_length=1,max_length=200)
class GitRemoteIn(BaseModel):
    name:str='origin'
    url:str=Field(min_length=1,max_length=1000)
class GitSyncIn(BaseModel):
    action:str
class ReleaseCompareIn(BaseModel):
    target_project_id:int=Field(ge=1)
class ReleasePrepareIn(ReleaseCompareIn):
    paths:list[str]=Field(min_length=1,max_length=500)
class ReleaseApplyIn(ReleaseCompareIn):
    plan_id:str=Field(min_length=32,max_length=32)

@app.get('/api/projects')
def projects(): return store.projects()
@app.post('/api/projects')
def create_project(data:ProjectIn):
    root=Path(data.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise HTTPException(400,'Укажи существующую папку проекта')
    if not data.name.strip(): raise HTTPException(400,'Название проекта не может быть пустым')
    existing=store.find_project_by_root(str(root))
    if existing:
        if existing.get('archived_at'):
            store.restore_project(existing['id'])
            return store.project(existing['id'])
        raise HTTPException(409, f"Эта папка уже зарегистрирована как «{existing['name']}» (ID {existing['id']}). Путь: {existing['root']}")
    pid=store.create_project(data.name.strip(),str(root))
    return store.project(pid)

@app.delete('/api/projects/{pid}')
def archive_project(pid:int):
    row=store.project(pid)
    if not row: raise HTTPException(404,'Проект не найден')
    if row.get('archived_at'): return {'ok':True,'archived':True,'already_archived':True}
    # Keep tasks, branches, messages, memories, attachments and the on-disk folder.
    store.archive_project(pid)
    return {'ok':True,'archived':True,'project_id':pid,'name':row['name'],'root':row['root']}

@app.get('/api/projects/archived')
def archived_projects():
    return [x for x in store.projects(include_archived=True) if x.get('archived_at')]

@app.post('/api/projects/{pid}/restore')
def restore_project(pid:int):
    row=store.project(pid)
    if not row: raise HTTPException(404,'Проект не найден')
    store.restore_project(pid)
    return {'ok':True,'project':store.project(pid)}
@app.patch('/api/projects/{pid}')
def rename_project(pid:int,data:NameIn):
    if not store.project(pid): raise HTTPException(404,'Проект не найден')
    if not data.name.strip(): raise HTTPException(400,'Название не может быть пустым')
    store.rename_project(pid,data.name.strip()); return {'ok':True}
@app.get('/api/projects/{pid}/memory')
def project_memory(pid:int):
    if not store.project(pid): raise HTTPException(404,'Проект не найден')
    return store.get_project_memory(pid) or {'summary':''}
@app.put('/api/projects/{pid}/memory')
def update_project_memory(pid:int,data:NameIn):
    if not store.project(pid): raise HTTPException(404,'Проект не найден')
    store.save_project_memory(pid,data.name)
    return {'ok':True}
@app.get('/api/projects/{pid}/settings')
def project_settings(pid:int):
    if not store.project(pid): raise HTTPException(404,'Проект не найден')
    return store.get_project_settings(pid)
@app.put('/api/projects/{pid}/settings')
def update_project_settings(pid:int,data:AutonomyIn):
    if not store.project(pid): raise HTTPException(404,'Проект не найден')
    try: store.set_project_autonomy(pid,data.autonomy)
    except ValueError as e: raise HTTPException(400,str(e))
    return store.get_project_settings(pid)

@app.get('/api/settings/agent')
def get_agent_settings():
    settings = store.get_app_settings()
    # One-time safe default for existing installations: use a registered active
    # project, never a path from the legacy PROJECT_ROOT environment variable.
    if settings.get('default_project_id') is None:
        projects = store.projects()
        if projects:
            settings = store.set_app_settings({'default_project_id': projects[0]['id']})
    return settings

@app.put('/api/settings/agent')
def update_agent_settings(data:AgentSettingsIn):
    try:
        return store.set_app_settings(data.model_dump())
    except ValueError as e:
        raise HTTPException(400,str(e))

@app.get('/api/tasks')
def tasks(project_id:int|None=None): return store.tasks(project_id)
@app.post('/api/tasks')
def create_task(data:TaskIn):
    if not store.project(data.project_id): raise HTTPException(404,'Проект не найден')
    tid,bid=store.create_task(data.project_id,data.name.strip() or 'Новая задача'); return {'task_id':tid,'branch_id':bid}
@app.post('/api/tasks/{tid}/continue')
async def continue_in_new_task(tid:int, data:ContinueTaskIn):
    """Create a clean task from a deliberately selected context scope."""
    if data.scope not in {'branch', 'task', 'project'}:
        raise HTTPException(400, 'Недопустимый уровень переноса контекста')
    source_task = next((t for t in store.tasks() if int(t['id']) == int(tid)), None)
    if not source_task:
        raise HTTPException(404, 'Исходная задача не найдена')
    source_task_for_branch = store.task_for_branch(data.branch_id)
    if not source_task_for_branch or int(source_task_for_branch['id']) != int(tid):
        raise HTTPException(400, 'Выбранная ветка не относится к исходной задаче')
    project_row = store.project(source_task['project_id'])
    if not project_row:
        raise HTTPException(404, 'Проект исходной задачи не найден')

    project_memory = store.get_project_memory(project_row['id'])
    try:
        collected = collect_handoff_scope(
            store, project_row, source_task, data.branch_id, data.scope, data.recent_messages
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if not collected['total_source_messages'] and not collected['task_memory_lines'] and not collected['branch_memory_lines'] and not ((project_memory or {}).get('summary') or '').strip():
        raise HTTPException(400, 'В выбранной области нет истории или сохранённой памяти для переноса')

    prior_parts = [
        'МЕТАДАННЫЕ ИСТОЧНИКА:\n'
        f"Проект: {project_row['name']}\nКорень проекта: {project_row['root']}\n"
        f"Исходная задача: {source_task['title']} (ID {tid})\nАктивная ветка: ID {data.branch_id}\n"
        f"Область переноса: {data.scope}",
        'ПАМЯТЬ ПРОЕКТА (справочно; автоматически подключается в новой задаче, не дублировать без необходимости):\n' + ((project_memory or {}).get('summary') or 'Не сформирована'),
    ]
    if collected['task_memory_lines']:
        prior_parts.append('ПАМЯТЬ ВЫБРАННЫХ ЗАДАЧ:\n' + '\n\n'.join(collected['task_memory_lines']))
    if collected['branch_memory_lines']:
        prior_parts.append('ПАМЯТЬ ВЕТОК:\n' + '\n\n'.join(collected['branch_memory_lines']))
    if collected['attachment_lines']:
        prior_parts.append('ВЛОЖЕНИЯ (файлы не копируются и остаются в исходном хранилище):\n' + '\n'.join(collected['attachment_lines']))
    if collected['omitted_task_count'] or collected['omitted_branch_count'] or collected['omitted_evidence_branches']:
        prior_parts.append('ОГРАНИЧЕНИЕ ОБЪЁМА: для защиты контекста часть дальних данных большого проекта не передана полностью. Не делай выводов об отсутствующих задачах/ветках; при необходимости пользователь может повторить перенос с более узкой областью. ' + f"Пропущено задач: {collected['omitted_task_count']}; веток сверх лимита: {collected['omitted_branch_count']}; веток без места в лимите резюме: {collected['omitted_evidence_branches']}.")

    models = await agent.models()
    model = cfg.lm_model if cfg.lm_model != 'local-model' else (models[0] if models and not models[0].startswith('Ошибка') else cfg.lm_model)
    try:
        summary, prompt_tokens, completion_tokens = await agent._summarize(
            model, collected['evidence_messages'], '\n\n'.join(prior_parts), data.branch_id, None
        )
    except Exception as exc:
        raise HTTPException(502, f'Не удалось сформировать интеллектуальный перенос через LM Studio: {str(exc)[:500]}')
    if not (summary or '').strip():
        raise HTTPException(502, 'Модель вернула пустое резюме. Исходная задача не изменена; новая задача не создана.')

    scope_label = {'branch':'только текущая ветка','task':'вся задача (все её ветки)','project':'задача и сводная память проекта'}[data.scope]
    handoff = '\n'.join([
        '# SERGDATA Workbench — технический пакет продолжения', '',
        f"Проект: {project_row['name']}", f"Корень проекта: {project_row['root']}",
        f"Источник: задача {tid}, активная ветка {data.branch_id}", f"Область переноса: {scope_label}", '',
        '## Сжатое резюме, сформированное моделью', summary.strip(), '',
        '## Постоянная память проекта',
        'Подключается автоматически из памяти проекта. Не дублируется в памяти задачи.', '',
        '## Вложения',
        'Файлы не копировались и остаются в исходных областях хранения. Перед использованием проверь их доступность и область доступа.', '',
        '## Правила продолжения',
        '- Сначала проверь фактическое состояние файлов, Git и окружения; старые сведения о состоянии файлов считай историческими до проверки.',
        '- Не заявляй о выполнении изменений или тестов без фактического результата инструмента.',
        '- Сохраняй подтверждённые решения и ограничения; отделяй факты от гипотез.',
        '- Продолжай с раздела «Следующий конкретный шаг» резюме. Если он отсутствует или неоднозначен — сначала уточни состояние проекта.',
        '- Исходная задача, ветки, вложения и история не изменялись.', '',
        f"Сводка создана моделью {model}. Область: {data.scope}. Веток учтено: {len(collected['selected_branches'])}; сообщений в источниках: {collected['total_source_messages']}."
    ]).strip()

    new_title = (data.name or '').strip() or f"Продолжение: {source_task['title']}"
    try:
        new_tid, new_bid = store.create_task_with_memory(
            source_task['project_id'], new_title, handoff, collected.get('attachment_ids', [])
        )
    except ValueError as exc:
        raise HTTPException(409, f'Не удалось безопасно перенести доступ к вложениям: {exc}')
    return {
        'ok': True, 'task_id': new_tid, 'branch_id': new_bid,
        'source_task_id': tid, 'source_branch_id': data.branch_id, 'scope': data.scope,
        'included_branches': len(collected['selected_branches']), 'total_source_messages': collected['total_source_messages'],
        'omitted_tasks': collected['omitted_task_count'], 'omitted_branches': collected['omitted_branch_count'] + collected['omitted_evidence_branches'],
        'handoff_chars': len(handoff), 'summary_prompt_tokens': prompt_tokens,
        'summary_completion_tokens': completion_tokens, 'model': model,
        'attachment_count': collected['attachment_count'],
        'attachments_granted': len(collected.get('attachment_ids', [])),
        'message': f'Создана новая задача. Перенесён контекст: {scope_label}; доступ к {len(collected.get("attachment_ids", []))} вложениям передан без копирования файлов. Исходные данные сохранены.'
    }

@app.get('/api/tasks/{tid}/memory')
def task_memory(tid:int):
    with store.conn() as c:
        row=c.execute('SELECT summary FROM tasks WHERE id=?',(tid,)).fetchone()
    if not row: raise HTTPException(404,'Задача не найдена')
    return {'summary':row['summary'] or ''}
@app.put('/api/tasks/{tid}/memory')
def update_task_memory(tid:int,data:NameIn):
    with store.conn() as c:
        row=c.execute('SELECT id FROM tasks WHERE id=?',(tid,)).fetchone()
    if not row: raise HTTPException(404,'Задача не найдена')
    store.save_task_memory(tid,data.name)
    return {'ok':True}
@app.patch('/api/tasks/{tid}')
def rename_task(tid:int,data:NameIn): store.rename_task(tid,data.name); return {'ok':True}
@app.delete('/api/tasks/{tid}')
def delete_task(tid:int): store.delete_task(tid); return {'ok':True}
@app.get('/api/tasks/{tid}/branches')
def branches(tid:int): return store.branches(tid)
@app.post('/api/branches/{bid}/fork')
def fork(bid:int,data:NameIn): return {'branch_id':store.create_branch(bid,data.name.strip() or 'Новая ветка')}
@app.patch('/api/branches/{bid}')
def rename_branch(bid:int,data:NameIn): store.rename_branch(bid,data.name); return {'ok':True}
@app.delete('/api/branches/{bid}')
def delete_branch(bid:int):
    try: store.delete_branch(bid); return {'ok':True}
    except ValueError as e: raise HTTPException(400,str(e))
@app.get('/api/branches/{bid}/messages')
def messages(bid:int): return store.messages(bid)
@app.delete('/api/branches/{bid}/messages/{mid}')
def delete_message(bid:int, mid:int):
    try:
        if not store.delete_message(bid, mid): raise HTTPException(404, 'Сообщение не найдено')
        return {'ok':True}
    except ValueError as e: raise HTTPException(403, str(e))
@app.get('/api/branches/{bid}/stats')
async def stats(bid:int):
    msgs=store.messages(bid)
    chars=sum(len(m['content']) for m in msgs)
    memory=store.get_memory(bid)
    through=int(memory['through_message_id']) if memory else 0
    active=[m for m in msgs if int(m.get('id',0))>through]
    branch_project=store.project_for_branch(bid)
    pm=store.get_project_memory(branch_project['id']) if branch_project else None
    task_row=store.task_for_branch(bid)
    context_messages=agent._context_messages(active, memory['summary'] if memory else '',
                                             branch_project['root'] if branch_project else str(project.root),
                                             pm['summary'] if pm else '',
                                             task_row['summary'] if task_row else '')
    model_id=await agent.resolve_model_id()
    metrics=await asyncio.to_thread(agent.prompt_metrics,context_messages,agent.specs(),model_id)
    metadata=await agent.model_context_metadata(model_id)
    sdk_limit=metrics.get('model_context_limit')
    model_limit=sdk_limit or metadata.get('model_context_limit')
    configured_limit=max(8192,int(cfg.context_limit or 50000))
    effective_limit=min(int(model_limit),configured_limit) if model_limit else configured_limit
    active_estimate=int(metrics.get('estimated_prompt_tokens') or 0)
    output_reserve=max(512,min(2048,round(effective_limit*0.05)))
    percent=round((active_estimate+output_reserve)/effective_limit*100,1) if effective_limit else 0
    usage=store.usage_lineage(bid)
    calls=store.llm_call_history(bid,limit=12)
    last_call=calls[-1] if calls else None
    last_turn=store.last_llm_turn(bid)
    return {
        'messages':len(msgs),'chars':chars,
        'estimated_context_tokens':active_estimate,
        'context_tokens_used':active_estimate,
        'api_tokens_lifetime':usage['history']['t'],
        'messages_tokens':metrics.get('messages_tokens'),
        'tools_tokens_estimate':metrics.get('tools_tokens_estimate'),
        'format_overhead_estimate':metrics.get('format_overhead_estimate'),
        'estimate_method':metrics.get('estimate_method'),
        'tokenizer_status':metrics.get('tokenizer_status'),
        'tokenizer_error':metrics.get('tokenizer_error'),
        'usage':usage['history'],
        'usage_direct':usage['direct'],'usage_inherited':usage['inherited'],
        'usage_unreported_calls':store.llm_unreported_count(bid),
        'last_call':last_call,
        'last_turn':last_turn,
        'llm_calls':list(reversed(calls)),
        'context_limit':effective_limit,'model_context_limit':model_limit,
        'workbench_context_limit':configured_limit,
        'limit_source':'Текущий лимит LM Studio' if sdk_limit else metadata.get('context_limit_source', 'CONTEXT_LIMIT из .env'),
        'output_reserve_tokens':max(512,min(2048,round(effective_limit*0.05))),
        'remaining_estimate':max(0,effective_limit-active_estimate-max(512,min(2048,round(effective_limit*0.05)))),
        'context_percent':min(100,round((active_estimate+max(512,min(2048,round(effective_limit*0.05))))/effective_limit*100,1)),
        'memory':memory,
    }
@app.post('/api/context-preview')
async def context_preview(data:ContextPreviewIn):
    if not data.text.strip() and not data.attachment_ids:
        raise HTTPException(400, 'Пустое сообщение')
    history = store.messages(data.branch_id)
    preview_text = data.text.strip() or 'Проанализируй приложенные файлы.'
    try:
        model_id=await agent.resolve_model_id()
        metadata=await agent.model_context_metadata(model_id)
        return await asyncio.to_thread(
            agent.preview_context,data.branch_id,preview_text,history,data.attachment_ids,model_id,metadata
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post('/api/chat')
async def chat(data:ChatIn):
    if not data.text.strip(): raise HTTPException(400,'Пустое сообщение')
    task=asyncio.current_task()
    with CHAT_TASKS_LOCK:
        existing=CHAT_TASKS.get(data.branch_id)
        if existing and not existing.done():
            raise HTTPException(409,'Для этой ветки уже выполняется запрос модели')
        CHAT_TASKS[data.branch_id]=task
    set_chat_activity(data.branch_id, 'preparing', 'Подготовка контекста')
    try:
        history=store.messages(data.branch_id)
        return await agent.chat(data.branch_id,data.text,history,data.attachment_ids)
    except asyncio.CancelledError:
        # Cancellation is an intentional user action, not an LM Studio failure.
        # Preserve a visible marker and return a normal response to the browser.
        try:
            store.add_message(data.branch_id,'assistant','Генерация остановлена пользователем.')
        except Exception:
            pass
        return {'answer':'Генерация остановлена пользователем.','stopped':True}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        detail = str(e)
        # OpenAI SDK errors sometimes stringify without the useful upstream
        # status. Inspect the bounded response body only for classification;
        # do not write request/response bodies or model content to server logs.
        body = getattr(e, 'body', None)
        if body is None:
            response = getattr(e, 'response', None)
            try:
                body = response.text if response is not None else None
            except Exception:
                body = None
        if body:
            try:
                import json
                body_text = json.dumps(body, ensure_ascii=False, default=str) if not isinstance(body, str) else body
            except Exception:
                body_text = str(body)
            detail = (detail + ' | LM Studio: ' + body_text[:1200]).strip()
        error_id = secrets.token_hex(6)
        upstream_status = getattr(e, 'status_code', None)
        # Log the exception class, upstream status and traceback frames, but not
        # exception text or payloads which might contain prompts or credentials.
        trace_frames = ''.join(traceback.format_tb(e.__traceback__))[-5000:]
        logger.error(
            'CHAT_API_FAILURE id=%s branch_id=%s exception_type=%s upstream_status=%s\n%s',
            error_id, data.branch_id, type(e).__name__, upstream_status, trace_frames
        )
        low = detail.lower()
        if any(x in low for x in ('context length', 'maximum context', 'too many tokens', 'prompt is too long', 'maximum number of tokens')):
            raise HTTPException(413, f'LM Studio отклонила запрос: превышен размер контекстного окна. История требует сжатия или переноса в новую задачу. Диагностический ID: {error_id}.')
        raise HTTPException(502, f'Ошибка обработки запроса ({type(e).__name__}). Диагностический ID: {error_id}. Подробности без содержимого запроса записаны в журнал Workbench.')
    finally:
        with CHAT_TASKS_LOCK:
            if CHAT_TASKS.get(data.branch_id) is task:
                CHAT_TASKS.pop(data.branch_id,None)
        if get_chat_activity(data.branch_id).get('stage') not in {'waiting_input','waiting_approval'}:
            set_chat_activity(data.branch_id, 'idle', '')

@app.get('/api/chat/status')
def chat_status(branch_id:int):
    # The browser may be reloaded while a model request is still running.
    # Expose server-side state so the composer can restore the Stop button.
    with CHAT_TASKS_LOCK:
        task=CHAT_TASKS.get(branch_id)
        active=bool(task and not task.done())
    pending = store.pending_executions(branch_id)
    activity = get_chat_activity(branch_id)
    if pending:
        activity = {'stage':'waiting_approval','detail':f"Ожидается подтверждение команды #{pending[-1]['id']}"}
        set_chat_activity(branch_id,'waiting_approval',activity['detail'])
    elif not active and activity.get('stage') == 'waiting_approval':
        set_chat_activity(branch_id,'idle','')
        activity = get_chat_activity(branch_id)
    return {'ok':True,'branch_id':branch_id,'active':active,'activity':get_chat_activity(branch_id)}

@app.post('/api/chat/cancel')
async def cancel_chat(branch_id:int):
    with CHAT_TASKS_LOCK:
        task=CHAT_TASKS.get(branch_id)
        if not task or task.done():
            return {'ok':True,'cancelled':False,'active':False,'message':'Активной генерации для этой ветки нет'}
        task.cancel()
    # Wait briefly for the chat handler to catch CancelledError and release its
    # branch lock. This avoids returning a false sense of completion while the
    # next request would still receive HTTP 409.
    try:
        await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), timeout=8)
    except asyncio.TimeoutError:
        return {'ok':True,'cancelled':True,'active':True,'message':'Остановка отправлена; сервер ещё завершает запрос'}
    with CHAT_TASKS_LOCK:
        current=CHAT_TASKS.get(branch_id)
        active=bool(current and not current.done())
    return {'ok':True,'cancelled':True,'active':active,'message':'Запрос модели остановлен' if not active else 'Остановка отправлена'}

@app.get('/api/branches/{bid}/memory')
def branch_memory(bid:int): return store.get_memory(bid) or {'summary':'','through_message_id':0}
@app.get('/api/pending')
def pending(branch_id:int|None=None): return store.pending(branch_id)
@app.post('/api/pending/{pid}/approve')
def approve(pid:int):
    rows=[x for x in store.pending() if x['id']==pid]
    if not rows: raise HTTPException(404,'Изменение не найдено или уже обработано')
    item=rows[0]
    try:
        row=store.project_for_pending(pid)
        if not row: raise ValueError('Проект изменения не найден')
        from workbench.tools import ProjectTools
        target=ProjectTools(Path(row['root']))
        result=target.write(item['path'],item['content'])
        store.set_pending(pid,'approved')
        return {'ok':True,'result':result}
    except Exception as e: raise HTTPException(400,str(e))
@app.post('/api/pending/{pid}/reject')
def reject(pid:int): store.set_pending(pid,'rejected'); return {'ok':True}
@app.get('/api/input-requests/pending')
def pending_input_requests(branch_id:int|None=None):
    return store.pending_input_requests(branch_id)

@app.post('/api/input-requests/{request_id}/submit')
async def submit_input_request(request_id:int, data:UserInputSubmit):
    item = store.input_request(request_id)
    if not item or item['status'] != 'pending':
        raise HTTPException(404, 'Запрос ввода не найден или уже обработан')
    if not item.get('context_json') or not item.get('tool_call_id'):
        raise HTTPException(409, 'Запрос ещё не связан с исходным вызовом модели; обнови очередь через несколько секунд')
    if item['input_type'] == 'secret':
        if not data.value:
            raise HTTPException(400, 'Секрет не может быть пустым')
        try:
            credential_ref = agent.credentials.put(data.value, persist=data.remember)
        except Exception as exc:
            raise HTTPException(400, str(exc))
        changed = store.complete_input_request(request_id, '', credential_ref)
        if not changed:
            agent.credentials.delete(credential_ref)
            raise HTTPException(409, 'Запрос уже обработан другим действием')
    else:
        if not data.value.strip():
            raise HTTPException(400, 'Ответ не может быть пустым')
        if not store.complete_input_request(request_id, data.value, ''):
            raise HTTPException(409, 'Запрос уже обработан другим действием')
    resume = await run_tracked_agent_task(int(item['branch_id']), agent.resume_input_request(request_id))
    return {'ok':True, 'agent_resume':resume}

@app.post('/api/input-requests/{request_id}/reject')
async def reject_input_request(request_id:int):
    item = store.input_request(request_id)
    if not item or item['status'] != 'pending':
        raise HTTPException(404, 'Запрос ввода не найден или уже обработан')
    if not item.get('context_json') or not item.get('tool_call_id'):
        raise HTTPException(409, 'Запрос ещё не связан с исходным вызовом модели')
    if not store.reject_input_request(request_id):
        raise HTTPException(409, 'Запрос уже обработан другим действием')
    resume = await run_tracked_agent_task(
        int(item['branch_id']),
        agent.resume_input_request(request_id, 'Пользователь отклонил запрос ввода. Не повторяй запрос автоматически; объясни, какие данные не получены, и предложи безопасный следующий шаг.')
    )
    return {'ok':True, 'agent_resume':resume}

@app.get('/api/server-profiles')
def get_server_profiles():
    result = []
    for row in store.server_profiles():
        status = agent.credentials.status(row.get('credential_ref', '')) if row.get('auth_method') == 'password' else 'key'
        result.append({k:v for k,v in row.items() if k != 'credential_ref'} |
                      {'has_credential': status in {'persistent', 'session'},
                       'credential_status': status})
    return result

@app.post('/api/server-profiles')
def save_server_profile(data:ServerProfileIn):
    from workbench.ssh import validate_fields
    name = data.name.strip()
    if not name:
        raise HTTPException(400, 'Название профиля не может быть пустым')
    if data.auth_method not in {'key','password'}:
        raise HTTPException(400, 'Поддерживаются только key и password')
    try:
        host, username, port = validate_fields(data.host, data.username, data.port)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    old = store.server_profile(data.profile_id) if data.profile_id else None
    if data.profile_id and not old:
        raise HTTPException(404, 'SSH-профиль не найден')
    credential_ref = ''
    new_ref = ''
    try:
        if data.auth_method == 'password':
            if data.password:
                new_ref = agent.credentials.put(data.password, persist=data.remember_password)
                credential_ref = new_ref
            elif old and old.get('auth_method') == 'password':
                credential_ref = old.get('credential_ref','')
            if not credential_ref:
                raise HTTPException(400, 'Для парольной авторизации нужен пароль')
        profile_id = store.save_server_profile(data.profile_id, name, host, port, username,
                                               data.auth_method, credential_ref)
        cleanup_warning = False
        if old and old.get('credential_ref') and old.get('credential_ref') != credential_ref:
            if not store.credential_ref_used_by_profile(old['credential_ref']):
                try:
                    agent.credentials.delete(old['credential_ref'])
                except Exception:
                    cleanup_warning = True
        return {'ok':True, 'profile_id':profile_id, 'credential_cleanup_warning':cleanup_warning}
    except HTTPException:
        if new_ref:
            agent.credentials.delete(new_ref)
        raise
    except Exception as exc:
        if new_ref:
            agent.credentials.delete(new_ref)
        raise HTTPException(400, f'Не удалось сохранить SSH-профиль: {type(exc).__name__}')

@app.delete('/api/server-profiles/{profile_id}')
def delete_server_profile(profile_id:int):
    old = store.server_profile(profile_id)
    if not old:
        raise HTTPException(404, 'SSH-профиль не найден')
    store.delete_server_profile(profile_id)
    cleanup_warning = False
    if old.get('credential_ref') and not store.credential_ref_used_by_profile(old['credential_ref']):
        try:
            agent.credentials.delete(old['credential_ref'])
        except Exception:
            cleanup_warning = True
    return {'ok':True, 'credential_cleanup_warning':cleanup_warning}

@app.get('/api/execution/pending')
def pending_execution(branch_id:int|None=None):
    # Resolve the active branch to its project, then return all pending commands
    # in that project. A sibling-branch restore must not hide an approval request.
    if branch_id is None:
        raise HTTPException(400, 'Не указан branch_id для очереди подтверждений')
    branch = store.project_for_branch(branch_id)
    if not branch:
        raise HTTPException(404, 'Ветка для очереди подтверждений не найдена')
    rows = store.pending_executions_for_project(int(branch['id']))
    for item in rows:
        raw = item.get('script', '')
        if raw.startswith('__SERGDATA_PROFILE_EXEC_V1__'):
            try:
                payload = __import__('json').loads(raw[len('__SERGDATA_PROFILE_EXEC_V1__'):])
                profile = store.server_profile(int(payload.get('profile_id', 0)))
                item['display_script'] = (f"SSH профиль: {profile['name']} · {profile['username']}@{profile['host']}:{profile['port']}\n"
                                          f"{payload.get('command', '')}") if profile else '[SSH-профиль удалён]'
                item['execution_kind'] = 'ssh_profile'
            except Exception:
                item['display_script'] = '[Некорректная запись SSH-профиля]'
                item['execution_kind'] = 'unknown'
        elif raw.startswith('__SERGDATA_EXEC_V1__'):
            try:
                payload = __import__('json').loads(raw[len('__SERGDATA_EXEC_V1__'):])
                item['display_script'] = (f"SSH {payload.get('user')}@{payload.get('host')}:{payload.get('port')}\n"
                                          f"{payload.get('command', '')}")
                item['execution_kind'] = 'ssh'
            except Exception:
                item['display_script'] = '[Некорректная запись SSH-команды]'
                item['execution_kind'] = 'unknown'
        else:
            item['display_script'] = raw
            item['execution_kind'] = 'powershell'
        # Internal resume snapshots contain the full conversation/tool-call context;
        # the browser needs only the display-safe approval card fields.
        for private_field in ('context_json', 'tool_call_id', 'model', 'user_message_id', 'result', 'script'):
            item.pop(private_field, None)
    return rows
@app.post('/api/execution/{eid}/approve')
async def approve_execution(eid:int):
    item=store.execution_by_id(eid)
    if not item or item['status']!='pending': raise HTTPException(404,'Команда не найдена или уже обработана')
    row=store.project_for_branch(item['branch_id'])
    if not row: raise HTTPException(404,'Проект команды не найден')
    raw_script = item['script']
    if not raw_script.startswith(('__SERGDATA_EXEC_V1__', '__SERGDATA_PROFILE_EXEC_V1__')) and __import__('re').search(
            r'(?i)(?:\bssh(?:\.exe)?\b|ssh[_A-Za-z]*exe|(?:fin|sub)\.sergdata\.top)', raw_script):
        store.finish_execution(eid, 'rejected', 'Заблокировано: SSH нельзя запускать через PowerShell. Используй ssh_run_command.')
        raise HTTPException(400, 'SSH через PowerShell заблокирован. Используй специализированный инструмент ssh_run_command.')
    try:
        # Claim the row atomically before starting a process; double-clicks/retries
        # must never execute the same approved command twice.
        if not store.claim_execution_approval(eid, 'workbench_ui'):
            raise HTTPException(409, 'Команда уже подтверждена или обрабатывается')
        from workbench.processes import processes
        from workbench.execution import ExecutionEngine
        engine=ExecutionEngine(Path(row['root']))
        loop=asyncio.get_running_loop()
        completion_state={'done':False}
        def on_process_complete(job):
            status=job.get('status','failed')
            changed, rendered = store.finish_execution_once(eid, status, job.get('exit_code'),
                                                            job.get('stdout',''), job.get('stderr',''))
            with ACTIVE_EXECUTIONS_LOCK:
                completion_state['done']=True
                ACTIVE_EXECUTIONS.pop(job.get('id'), None)
            if not changed:
                return
            try:
                store.add_message(item['branch_id'], 'tool', f"Выполнение · процесс {job.get('id')}:\n{rendered}",
                                  metadata={'kind':'execution_result','execution_id':eid,
                                            'status':status,'exit_code':job.get('exit_code')})
            except Exception:
                pass
            if not SHUTTING_DOWN:
                set_chat_activity(item['branch_id'], 'model_generation', 'Анализ результата инструмента')
                resume_coro = run_execution_resume(item['branch_id'], eid, rendered)
                try:
                    future=asyncio.run_coroutine_threadsafe(resume_coro, loop)
                    with RESUME_FUTURES_LOCK:
                        RESUME_FUTURES.add(future)
                    future.add_done_callback(_forget_resume_future)
                    future.add_done_callback(_log_resume_future)
                except Exception:
                    resume_coro.close()
                    logger.exception("Не удалось запланировать продолжение выполнения #%s", eid)
        raw_script = item['script']
        if raw_script.startswith('__SERGDATA_PROFILE_EXEC_V1__'):
            import json
            from workbench.ssh import run_profile_command
            payload = json.loads(raw_script[len('__SERGDATA_PROFILE_EXEC_V1__'):])
            if payload.get('kind') != 'ssh_profile':
                raise ValueError('Неизвестный тип SSH-профиля')
            profile = store.server_profile(int(payload['profile_id']))
            if not profile:
                raise ValueError('SSH-профиль удалён')
            if profile['auth_method'] == 'password' and not agent.credentials.exists(profile.get('credential_ref','')):
                raise ValueError('Пароль SSH-профиля отсутствует в CredentialBroker')
            jid = processes.start_callable(run_profile_command, (profile, payload['command'], agent.credentials),
                                           engine.root, timeout=180,
                                           display=f"SSH {profile['name']} · {profile['username']}@{profile['host']}:{profile['port']}",
                                           on_complete=on_process_complete, execution_id=eid)
            set_chat_activity(item['branch_id'], 'tool_running', f"SSH · {profile['name']}")
            store.set_execution_process(eid, jid)
            with ACTIVE_EXECUTIONS_LOCK:
                if not completion_state['done']:
                    ACTIVE_EXECUTIONS[jid]={'execution_id':eid,'branch_id':item['branch_id']}
            return {'ok':True,'job_id':jid,'message':'SSH-команда запущена через профиль. Вывод доступен в панели выполнения.'}
        elif raw_script.startswith('__SERGDATA_EXEC_V1__'):
            import json
            from workbench.ssh import ssh_argv
            payload = json.loads(raw_script[len('__SERGDATA_EXEC_V1__'):])
            if payload.get('kind') != 'ssh':
                raise ValueError('Неизвестный тип удалённой команды')
            command = ssh_argv(payload['host'], payload['user'], payload['port'], payload['command'], timeout=180)
        elif __import__('os').name=='nt':
            wrapped = "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); try { & {\n" + raw_script + "\n}; if ($LASTEXITCODE -ne $null) { exit $LASTEXITCODE } } catch { [Console]::Error.WriteLine($_.ToString()); exit 1 }"
            command=['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Restricted','-Command',wrapped]
        else:
            import shutil
            shell = shutil.which('pwsh') or shutil.which('powershell')
            if not shell: raise ValueError('PowerShell не найден; используйте Bash/SSH для Linux-команд')
            command=[shell,'-NoLogo','-NoProfile','-NonInteractive','-Command',raw_script]
        jid=processes.start(command,engine.root,timeout=180,on_complete=on_process_complete,execution_id=eid)
        set_chat_activity(item['branch_id'], 'tool_running', 'PowerShell / SSH')
        store.set_execution_process(eid, jid)
        with ACTIVE_EXECUTIONS_LOCK:
            if not completion_state['done']:
                ACTIVE_EXECUTIONS[jid]={'execution_id':eid,'branch_id':item['branch_id']}
        return {'ok':True,'job_id':jid,'message':'Команда запущена. Вывод доступен в панели выполнения.'}
    except HTTPException:
        # HTTP control-flow responses (especially 409 from the atomic approval
        # claim) must not mutate execution state or resume the agent. A retry or
        # double-click is not a process-start failure.
        raise
    except Exception as e:
        store.finish_execution(eid,'failed',f'{type(e).__name__}: {e}')
        try:
            await run_tracked_agent_task(
                int(item['branch_id']),
                agent.resume_execution(eid, f'Выполнение не удалось запустить: {type(e).__name__}: {e}')
            )
        except Exception:
            pass
        raise HTTPException(400,str(e))
@app.get('/api/processes/{jid}')
async def process_status(jid:str):
    from workbench.processes import processes
    item=processes.get(jid)
    if not item: raise HTTPException(404,'Процесс не найден в текущей сессии Workbench')
    if item['status'] in ('completed','failed','stopped'):
        with ACTIVE_EXECUTIONS_LOCK:
            link=ACTIVE_EXECUTIONS.get(jid)
        if link:
            changed, rendered = store.finish_execution_once(link['execution_id'], item['status'],
                                                            item['exit_code'], item['stdout'], item['stderr'])
            with ACTIVE_EXECUTIONS_LOCK:
                ACTIVE_EXECUTIONS.pop(jid, None)
            if changed:
                store.add_message(link['branch_id'],'tool',f"Выполнение · процесс {jid}:\n{rendered}",
                                  metadata={'kind':'execution_result','execution_id':link['execution_id'],
                                            'status':item['status'],'exit_code':item['exit_code']})
                resume = await run_execution_resume(
                    int(link['branch_id']), link['execution_id'], rendered
                )
                item['agent_resume'] = resume
        execution_id=item.get('execution_id')
        if execution_id:
            execution_row=store.execution_by_id(int(execution_id))
            if execution_row and execution_row.get('resume_status') == 'waiting':
                # Fallback if the worker callback could not schedule the resume.
                item['agent_resume'] = await run_execution_resume(
                    int(execution_row['branch_id']), int(execution_id), execution_row.get('result','')
                )
                execution_row=store.execution_by_id(int(execution_id))
            if execution_row:
                item['execution_resume_status']=execution_row.get('resume_status')
    return item
@app.post('/api/processes/{jid}/stop')
def stop_process(jid:str):
    from workbench.processes import processes
    job=processes.get(jid)
    if not job: raise HTTPException(404,'Процесс не найден')
    stopped=processes.stop(jid)
    current=processes.get(jid) or job
    return {'ok':True,'stopped':stopped,'active':current.get('status') not in ('completed','failed','stopped'),
            'status':current.get('status'),'message':'Процесс остановлен' if stopped else 'Остановка отправлена; процесс ещё завершает работу'}
@app.post('/api/execution/{eid}/reject')
async def reject_execution(eid:int):
    item=store.execution_by_id(eid)
    if not item: raise HTTPException(404,'Команда не найдена')
    if not store.reject_execution_by_user(eid, 'workbench_ui'):
        raise HTTPException(409,'Команда уже подтверждена, отклонена или обрабатывается')
    resume = await run_tracked_agent_task(
        int(item['branch_id']),
        agent.resume_execution(eid, 'Команда отклонена пользователем. Не повторяй её и продолжи без этого действия.')
    )
    return {'ok':True, 'agent_resume':resume}
@app.get('/api/files')
def files(path:str='.', project_id:int|None=None):
    from workbench.tools import ProjectTools
    row=store.project(project_id) if project_id else proj
    if not row: raise HTTPException(404,'Проект не найден')
    tool=ProjectTools(Path(row['root']))
    return {'path':path,'project_root':row['root'],'listing':tool.listing(path)}

@app.get('/api/files/read')
def read_project_file(path: str, project_id: int):
    """Read a bounded, non-sensitive text file from the explicitly selected project."""
    from workbench.tools import ProjectTools
    row = store.project(project_id)
    if not row:
        raise HTTPException(404, 'Проект не найден')
    try:
        tool = ProjectTools(Path(row['root']))
        target = tool.safe(path)
        if not target.is_file():
            raise HTTPException(404, 'Файл не найден')
        if target.is_symlink():
            raise HTTPException(403, 'Чтение символических ссылок запрещено')
        size = target.stat().st_size
        if size > 1_000_000:
            raise HTTPException(413, 'Файл больше 1 МБ. Для больших файлов используй чтение через модель по частям.')
        raw = target.read_bytes()
        if b'\x00' in raw[:8192]:
            raise HTTPException(415, 'Похоже, это бинарный файл; текстовый просмотр недоступен')
        try:
            content = raw.decode('utf-8-sig')
            encoding = 'UTF-8'
        except UnicodeDecodeError:
            try:
                content = raw.decode('cp1251')
                encoding = 'Windows-1251'
            except UnicodeDecodeError:
                raise HTTPException(415, 'Не удалось определить текстовую кодировку файла')
        suffix = target.suffix.lower().lstrip('.')
        language_map = {'py':'python','pyw':'python','js':'javascript','mjs':'javascript','cjs':'javascript','ts':'typescript','tsx':'tsx','jsx':'jsx','html':'html','htm':'html','css':'css','scss':'scss','json':'json','jsonc':'json','yaml':'yaml','yml':'yaml','toml':'toml','ini':'ini','cfg':'ini','conf':'ini','md':'markdown','markdown':'markdown','sh':'bash','bash':'bash','ps1':'powershell','psm1':'powershell','sql':'sql','xml':'xml','svg':'xml','bat':'batch','cmd':'batch','txt':'text'}
        if target.name.lower() == '.env.example':
            suffix = 'ini'
        return {'project_id': project_id, 'project_root': row['root'], 'path': target.relative_to(tool.root).as_posix(),
                'name': target.name, 'content': content, 'encoding': encoding,
                'language': language_map.get(suffix, 'text'), 'size': size,
                'line_count': len(content.splitlines()) or 1}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(403, str(exc))
    except OSError as exc:
        raise HTTPException(400, f'Не удалось прочитать файл: {exc}')

UPLOAD_DIR = BASE / '.workbench' / 'uploads'
MAX_UPLOAD_BYTES = 20 * 1024 * 1024

@app.post('/api/attachments')
async def upload_attachment(file: UploadFile = File(...), project_id: int = Form(...), task_id: int | None = Form(None), branch_id: int | None = Form(None)):
    row = store.project(project_id)
    if not row:
        raise HTTPException(404, 'Проект не найден')
    if task_id is not None:
        with store.conn() as c:
            task = c.execute('SELECT id,project_id FROM tasks WHERE id=?', (task_id,)).fetchone()
        if not task or int(task['project_id']) != int(project_id):
            raise HTTPException(400, 'Задача не относится к выбранному проекту')
    if branch_id is not None:
        branch_project = store.project_for_branch(branch_id)
        branch_task = store.task_for_branch(branch_id)
        if not branch_project or int(branch_project['id']) != int(project_id) or (task_id is not None and int(branch_task['id']) != int(task_id)):
            raise HTTPException(400, 'Ветка не относится к выбранному проекту или задаче')
        if task_id is None:
            task_id = int(branch_task['id'])
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, 'Максимальный размер одного вложения — 20 МБ')
    if not data:
        raise HTTPException(400, 'Файл пуст')
    original = _safe_name(file.filename or 'attachment')
    try:
        kind, chunks, note = extract_document(original, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    import hashlib, uuid
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(original).suffix[:16]
    stored = uuid.uuid4().hex + suffix
    target = (UPLOAD_DIR / stored).resolve()
    if target.parent != UPLOAD_DIR.resolve():
        raise HTTPException(400, 'Некорректное имя файла')
    target.write_bytes(data)
    try:
        aid = store.add_attachment(project_id=project_id, task_id=task_id, branch_id=branch_id,
            original_name=original, stored_name=stored, media_type=file.content_type or 'application/octet-stream',
            kind=kind, size=len(data), sha256=hashlib.sha256(data).hexdigest(), note=note, chunks=chunks)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    item = store.attachment(aid)
    item.pop('stored_name', None); item.pop('sha256', None)
    item['chunks'] = len(chunks)
    return item

@app.get('/api/attachments')
def list_attachments(project_id:int, task_id:int|None=None, branch_id:int|None=None):
    if not store.project(project_id): raise HTTPException(404, 'Проект не найден')
    return store.attachments(project_id, task_id, branch_id)

@app.get('/api/attachments/search')
def search_attachments(project_id:int, q:str, task_id:int|None=None, branch_id:int|None=None):
    if not q.strip(): raise HTTPException(400, 'Введи поисковый запрос')
    if not store.project(project_id): raise HTTPException(404, 'Проект не найден')
    rows = store.search_attachments(project_id, q.strip()[:200], task_id, branch_id, limit=30)
    return [{'attachment_id':r['attachment_id'],'name':r['original_name'],'path':r['source_path'],'chunk_index':r['chunk_index'],'excerpt':r['content'][:1800]} for r in rows]

@app.get('/api/attachments/{aid}/download')
def download_attachment(aid:int):
    item = store.attachment(aid)
    if not item: raise HTTPException(404, 'Вложение не найдено')
    path = (UPLOAD_DIR / item['stored_name']).resolve()
    if path.parent != UPLOAD_DIR.resolve() or not path.is_file(): raise HTTPException(404, 'Файл вложения отсутствует на диске')
    return FileResponse(path, filename=item['original_name'], media_type=item['media_type'])

@app.delete('/api/attachments/{aid}')
def remove_attachment(aid:int, project_id:int):
    stored = store.delete_attachment(aid, project_id)
    if not stored: raise HTTPException(404, 'Вложение не найдено в этом проекте')
    path = (UPLOAD_DIR / stored).resolve()
    if path.parent == UPLOAD_DIR.resolve(): path.unlink(missing_ok=True)
    return {'ok':True}

@app.post('/api/context/import')
def import_context(data:ContextImportIn):
    if not data.content.strip(): raise HTTPException(400, 'Контекст пуст')
    if len(data.content) > 120000: raise HTTPException(413, 'Контекст слишком большой: максимум 120 000 символов')
    project_row = store.project(data.project_id)
    if not project_row: raise HTTPException(404, 'Проект не найден')
    content = data.content.strip()
    mode = data.mode
    if mode == 'current_branch':
        if not data.branch_id: raise HTTPException(400, 'Не выбрана текущая ветка')
        branch_project = store.project_for_branch(data.branch_id)
        if not branch_project or int(branch_project['id']) != data.project_id: raise HTTPException(400, 'Ветка относится к другому проекту')
        current = store.get_memory(data.branch_id)
        merged = (current['summary'].rstrip() + '\n\n--- Импортированный контекст ---\n\n' if current and current['summary'] else '') + content
        through = int(current['through_message_id']) if current else 0
        store.save_memory(data.branch_id, merged, through)
        return {'ok':True,'mode':mode,'branch_id':data.branch_id,'message':'Контекст добавлен в память текущей ветки.'}
    if mode == 'new_branch':
        if not data.branch_id: raise HTTPException(400, 'Не выбрана исходная ветка')
        branch_project = store.project_for_branch(data.branch_id)
        if not branch_project or int(branch_project['id']) != data.project_id: raise HTTPException(400, 'Исходная ветка относится к другому проекту')
        bid = store.create_branch(data.branch_id, data.name.strip() or 'Импортированный контекст')
        inherited_memory = store.get_memory(bid)
        through = int(inherited_memory['through_message_id']) if inherited_memory else 0
        merged = (inherited_memory['summary'].rstrip() + '\n\n--- Импортированный контекст ---\n\n' if inherited_memory and inherited_memory['summary'] else '') + content
        store.save_memory(bid, merged, through)
        return {'ok':True,'mode':mode,'branch_id':bid,'message':'Создана новая ветка с импортированным контекстом.'}
    if mode == 'new_task':
        tid,bid = store.create_task(data.project_id, data.name.strip() or 'Импортированный контекст')
        store.save_memory(bid, content, 0)
        return {'ok':True,'mode':mode,'task_id':tid,'branch_id':bid,'message':'Создана новая задача с импортированным контекстом.'}
    raise HTTPException(400, 'Неизвестный режим импорта')

def _git_manager(project_id:int):
    from workbench.git_manager import GitManager
    row=store.project(project_id)
    if not row: raise HTTPException(404,'Проект не найден')
    return GitManager(row['root'])

@app.get('/api/git/status')
def git_status(project_id:int):
    try: return _git_manager(project_id).status()
    except RuntimeError as e: raise HTTPException(503,str(e))
    except Exception as e: raise HTTPException(400,str(e))

@app.get('/api/git/diff')
def git_diff(project_id:int):
    try: return PlainTextResponse(_git_manager(project_id).diff())
    except RuntimeError as e: raise HTTPException(503,str(e))
    except Exception as e: raise HTTPException(400,str(e))

@app.post('/api/git/init')
def git_init(project_id:int):
    try: return _git_manager(project_id).init()
    except Exception as e: raise HTTPException(400,str(e))

@app.get('/api/git/files')
def git_files(project_id:int):
    try: return {'files':_git_manager(project_id).files()}
    except Exception as e: raise HTTPException(400,str(e))

@app.post('/api/git/stage')
def git_stage(project_id:int,data:GitPathsIn):
    try: return _git_manager(project_id).stage(data.paths)
    except Exception as e: raise HTTPException(400,str(e))

@app.post('/api/git/unstage')
def git_unstage(project_id:int,data:GitPathsIn):
    try: return _git_manager(project_id).unstage(data.paths)
    except Exception as e: raise HTTPException(400,str(e))

@app.post('/api/git/commit')
def git_commit(project_id:int,data:GitCommitIn):
    try: return _git_manager(project_id).commit(data.message)
    except Exception as e: raise HTTPException(400,str(e))

@app.get('/api/git/branches')
def git_branches(project_id:int):
    try: return {'branches':_git_manager(project_id).branches()}
    except Exception as e: raise HTTPException(400,str(e))

@app.get('/api/git/history')
def git_history(project_id:int,limit:int=20):
    try: return {'history':_git_manager(project_id).history(limit)}
    except Exception as e: raise HTTPException(400,str(e))

@app.post('/api/git/remote')
def git_remote(project_id:int,data:GitRemoteIn):
    try: return _git_manager(project_id).remote_add(data.name,data.url)
    except Exception as e: raise HTTPException(400,str(e))

@app.post('/api/git/sync')
def git_sync(project_id:int,data:GitSyncIn):
    if data.action in {'pull','push'}:
        # The browser asks for an explicit confirmation before this endpoint is called.
        pass
    try: return _git_manager(project_id).sync(data.action)
    except Exception as e: raise HTTPException(400,str(e))

def _release_manager(source_project_id:int,target_project_id:int):
    from workbench.release_manager import ReleaseManager
    if source_project_id == target_project_id:
        raise HTTPException(400,'Исходный и целевой проекты должны различаться')
    source=store.project(source_project_id); target=store.project(target_project_id)
    if not source or source.get('archived_at') or not target or target.get('archived_at'):
        raise HTTPException(404,'Исходный или целевой активный проект не найден')
    try:
        return ReleaseManager(source['root'],target['root'])
    except (ValueError, OSError) as exc:
        raise HTTPException(400,str(exc))

@app.post('/api/releases/compare')
def release_compare(data:ReleaseCompareIn,project_id:int):
    try:
        return _release_manager(project_id,data.target_project_id).compare()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400,str(exc))

@app.post('/api/releases/prepare')
def release_prepare(data:ReleasePrepareIn,project_id:int):
    try:
        return _release_manager(project_id,data.target_project_id).prepare(data.paths)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400,str(exc))

@app.post('/api/releases/apply')
def release_apply(data:ReleaseApplyIn,project_id:int):
    try:
        return _release_manager(project_id,data.target_project_id).apply(data.plan_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400,str(exc))

@app.post('/api/branches/{bid}/checkpoint')
async def checkpoint(bid:int):
    history=store.messages(bid)
    if len(history)<2: raise HTTPException(400,'Пока недостаточно истории для контрольной точки')
    memory=store.get_memory(bid)
    through=int(memory['through_message_id']) if memory else 0
    fresh=[m for m in history if int(m.get('id',0))>through]
    if len(fresh)<2: return {'ok':True,'message':'Память уже актуальна','through_message_id':through}
    old=fresh[:-8] if len(fresh)>8 else fresh
    if not old: raise HTTPException(400,'Слишком мало старых сообщений; продолжай работу до следующей контрольной точки')
    models=await agent.models()
    model=cfg.lm_model if cfg.lm_model!='local-model' else (models[0] if models and not models[0].startswith('Ошибка') else cfg.lm_model)
    summary,pt,ct=await agent._summarize(model,old,memory['summary'] if memory else '')
    if not summary.strip(): raise HTTPException(502,'Модель не сформировала контрольную точку')
    through_id=int(old[-1]['id'])
    store.save_memory(bid,summary,through_id)
    return {'ok':True,'through_message_id':through_id,'summary':summary,'summary_usage':{'prompt_tokens':pt,'completion_tokens':ct}}

@app.get('/api/branches/{bid}/checkpoint.md')
def checkpoint_export(bid:int):
    history=store.messages(bid)
    if not history: raise HTTPException(404,'История ветки пуста')
    row=store.project_for_branch(bid)
    branch=next((b for t in store.tasks(row['id']) for b in store.branches(t['id']) if b['id']==bid),None) if row else None
    memory=store.get_memory(bid)
    project_memory=store.get_project_memory(row['id']) if row else None
    task_row=store.task_for_branch(bid)
    lines=['# Пакет продолжения SERGDATA Workbench','',f"Проект: {row['name'] if row else 'Неизвестен'}",f"Папка: {row['root'] if row else ''}",f"Ветка: {branch['name'] if branch else bid}",'',
           '## Память проекта',project_memory['summary'] if project_memory else 'Не сформирована','',
           '## Память задачи',task_row['summary'] if task_row and task_row['summary'] else 'Не сформирована','',
           '## Контрольная точка ветки',memory['summary'] if memory else 'Не сформирована','',
           '## Последние сообщения']
    for m in history[-20:]:
        role={'user':'Пользователь','assistant':'Модель','tool':'Инструмент'}.get(m['role'],m['role'])
        lines += [f"### {role} · {m['created_at']}",m['content'],'']
    lines += ['## Инструкция продолжения','Сначала изучи актуальные файлы проекта и проверь, совпадает ли их состояние с этой контрольной точкой. Не считай неподтверждённые предположения фактами. Продолжай с последнего незавершённого шага.']
    return PlainTextResponse('\\n'.join(lines),media_type='text/markdown',headers={'Content-Disposition':'attachment; filename="workbench-checkpoint.md"'})

if __name__=='__main__': uvicorn.run('main:app',host=cfg.host,port=cfg.port,reload=False)
