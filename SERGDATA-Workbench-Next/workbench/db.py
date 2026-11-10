import json, sqlite3
from pathlib import Path
from datetime import datetime, timezone

class Store:
    PENDING_TOOL_RESULT = '[WORKBENCH_PENDING_TOOL_RESULT]'

    @classmethod
    def _resume_context_snapshot(cls, context, tool_call_id):
        # Build a valid OpenAI tool-call batch: preserve completed siblings,
        # reserve the awaited call, and mark unexecuted siblings as blocked.
        snapshot = json.loads(json.dumps(context, ensure_ascii=False))
        target_index = None
        call_ids = []
        for index, message in enumerate(snapshot):
            if not isinstance(message, dict) or message.get('role') != 'assistant':
                continue
            calls = message.get('tool_calls') or []
            ids = [str(call.get('id') or '') for call in calls if isinstance(call, dict)]
            if str(tool_call_id) in ids:
                target_index = index
                call_ids = ids
                break
        if target_index is None:
            raise ValueError('Исходный tool_call_id отсутствует в контексте')

        existing = {}
        suffix = []
        for message in snapshot[target_index + 1:]:
            if (isinstance(message, dict) and message.get('role') == 'tool'
                    and str(message.get('tool_call_id') or '') in call_ids):
                existing.setdefault(str(message['tool_call_id']), message)
            else:
                suffix.append(message)

        batch_results = []
        for call_id in call_ids:
            if call_id == str(tool_call_id):
                batch_results.append({'role': 'tool', 'tool_call_id': call_id,
                                      'content': cls.PENDING_TOOL_RESULT})
            elif call_id in existing:
                batch_results.append(existing[call_id])
            else:
                batch_results.append({'role': 'tool', 'tool_call_id': call_id,
                                      'content': 'Вызов не выполнен: предыдущий инструмент ожидает пользователя.'})
        return snapshot[:target_index + 1] + batch_results + suffix

    def __init__(self, path: Path, legacy_path: Path|None=None):
        self.path=path; path.parent.mkdir(parents=True,exist_ok=True)
        self._init()
        if legacy_path and legacy_path.exists() and legacy_path.resolve()!=path.resolve():
            self.import_legacy_once(legacy_path)
    def conn(self):
        c=sqlite3.connect(self.path, timeout=15); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); c.execute('PRAGMA busy_timeout=15000'); return c
    @staticmethod
    def now(): return datetime.now(timezone.utc).isoformat()
    def _init(self):
        with self.conn() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,root TEXT NOT NULL,created_at TEXT NOT NULL,archived_at TEXT);
            CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id INTEGER,title TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',summary TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(project_id) REFERENCES projects(id));
            CREATE TABLE IF NOT EXISTS branches(id INTEGER PRIMARY KEY AUTOINCREMENT,task_id INTEGER NOT NULL,name TEXT NOT NULL,parent_branch_id INTEGER,fork_message_id INTEGER,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,FOREIGN KEY(parent_branch_id) REFERENCES branches(id));
            CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,branch_id INTEGER NOT NULL,role TEXT NOT NULL,content TEXT NOT NULL,created_at TEXT NOT NULL,prompt_tokens INTEGER DEFAULT 0,completion_tokens INTEGER DEFAULT 0,metadata TEXT NOT NULL DEFAULT '{}',FOREIGN KEY(branch_id) REFERENCES branches(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,task_id INTEGER NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS pending_changes(id INTEGER PRIMARY KEY AUTOINCREMENT,branch_id INTEGER NOT NULL,path TEXT NOT NULL,content TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',created_at TEXT NOT NULL,FOREIGN KEY(branch_id) REFERENCES branches(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS pending_execution(id INTEGER PRIMARY KEY AUTOINCREMENT,branch_id INTEGER NOT NULL,script TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',created_at TEXT NOT NULL,finished_at TEXT,result TEXT NOT NULL DEFAULT '',context_json TEXT NOT NULL DEFAULT '',tool_call_id TEXT NOT NULL DEFAULT '',model TEXT NOT NULL DEFAULT '',user_message_id INTEGER,FOREIGN KEY(branch_id) REFERENCES branches(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS input_requests(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                input_type TEXT NOT NULL CHECK(input_type IN ('text','secret')),
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                finished_at TEXT,
                context_json TEXT NOT NULL DEFAULT '',
                tool_call_id TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT '',
                user_message_id INTEGER,
                result_text TEXT NOT NULL DEFAULT '',
                credential_ref TEXT NOT NULL DEFAULT '',
                resume_status TEXT NOT NULL DEFAULT 'not_applicable',
                FOREIGN KEY(branch_id) REFERENCES branches(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_input_requests_pending ON input_requests(status, branch_id);
            CREATE TABLE IF NOT EXISTS server_profiles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                username TEXT NOT NULL,
                auth_method TEXT NOT NULL CHECK(auth_method IN ('key','password')),
                credential_ref TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS usage(id INTEGER PRIMARY KEY AUTOINCREMENT,branch_id INTEGER NOT NULL,model TEXT,prompt_tokens INTEGER,completion_tokens INTEGER,total_tokens INTEGER,created_at TEXT NOT NULL,turn_message_id INTEGER,FOREIGN KEY(branch_id) REFERENCES branches(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS llm_calls(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL,
                message_id INTEGER,
                model TEXT NOT NULL DEFAULT '',
                call_kind TEXT NOT NULL DEFAULT 'chat',
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                usage_reported INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(branch_id) REFERENCES branches(id) ON DELETE CASCADE,
                FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS idx_llm_calls_branch ON llm_calls(branch_id,created_at);
            CREATE INDEX IF NOT EXISTS idx_llm_calls_message ON llm_calls(message_id);
            CREATE TABLE IF NOT EXISTS project_memory(project_id INTEGER PRIMARY KEY,summary TEXT NOT NULL DEFAULT '',updated_at TEXT NOT NULL,FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS project_settings(project_id INTEGER PRIMARY KEY, autonomy TEXT NOT NULL DEFAULT 'analysis', updated_at TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS branch_memory(branch_id INTEGER PRIMARY KEY,summary TEXT NOT NULL,through_message_id INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL,FOREIGN KEY(branch_id) REFERENCES branches(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS execution_checkpoints(id INTEGER PRIMARY KEY AUTOINCREMENT,branch_id INTEGER NOT NULL,status TEXT NOT NULL CHECK(status IN ('active','paused','completed','failed','superseded')),reason TEXT NOT NULL,payload_json TEXT NOT NULL,source_message_id INTEGER,sequence INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(branch_id) REFERENCES branches(id) ON DELETE CASCADE,FOREIGN KEY(source_message_id) REFERENCES messages(id) ON DELETE SET NULL);
            CREATE INDEX IF NOT EXISTS idx_execution_checkpoints_branch ON execution_checkpoints(branch_id,id DESC);
            CREATE TABLE IF NOT EXISTS migration_state(key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS app_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS attachments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                task_id INTEGER,
                branch_id INTEGER,
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL UNIQUE,
                media_type TEXT NOT NULL DEFAULT 'application/octet-stream',
                kind TEXT NOT NULL DEFAULT 'binary',
                size INTEGER NOT NULL DEFAULT 0,
                sha256 TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL,
                FOREIGN KEY(branch_id) REFERENCES branches(id) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS attachment_chunks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attachment_id INTEGER NOT NULL,
                source_path TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY(attachment_id) REFERENCES attachments(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_attachment_chunks_attachment ON attachment_chunks(attachment_id);
            CREATE TABLE IF NOT EXISTS message_attachments(
                message_id INTEGER NOT NULL,
                attachment_id INTEGER NOT NULL,
                PRIMARY KEY(message_id, attachment_id),
                FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE,
                FOREIGN KEY(attachment_id) REFERENCES attachments(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS task_attachment_access(
                task_id INTEGER NOT NULL,
                attachment_id INTEGER NOT NULL,
                granted_at TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'handoff',
                PRIMARY KEY(task_id, attachment_id),
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY(attachment_id) REFERENCES attachments(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_task_attachment_access_attachment ON task_attachment_access(attachment_id);
            ''')
            project_columns = {row[1] for row in c.execute('PRAGMA table_info(projects)').fetchall()}
            if 'archived_at' not in project_columns:
                c.execute('ALTER TABLE projects ADD COLUMN archived_at TEXT')
            message_columns = {row[1] for row in c.execute('PRAGMA table_info(messages)').fetchall()}
            if 'metadata' not in message_columns:
                c.execute("ALTER TABLE messages ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}'")
            execution_columns = {row[1] for row in c.execute('PRAGMA table_info(pending_execution)').fetchall()}
            for column, declaration in {
                'context_json': "TEXT NOT NULL DEFAULT ''",
                'tool_call_id': "TEXT NOT NULL DEFAULT ''",
                'model': "TEXT NOT NULL DEFAULT ''",
                'user_message_id': 'INTEGER',
                'resume_status': "TEXT NOT NULL DEFAULT 'not_applicable'",
                'approved_at': 'TEXT',
                'approved_via': "TEXT NOT NULL DEFAULT ''",
                'rejected_at': 'TEXT',
                'rejected_via': "TEXT NOT NULL DEFAULT ''",
            }.items():
                if column not in execution_columns:
                    c.execute(f'ALTER TABLE pending_execution ADD COLUMN {column} {declaration}')
            usage_columns = {row[1] for row in c.execute('PRAGMA table_info(usage)').fetchall()}
            if 'turn_message_id' not in usage_columns:
                c.execute('ALTER TABLE usage ADD COLUMN turn_message_id INTEGER')
            branch_memory_columns = {row[1] for row in c.execute('PRAGMA table_info(branch_memory)').fetchall()}
            if 'created_at' not in branch_memory_columns:
                c.execute('ALTER TABLE branch_memory ADD COLUMN created_at TEXT')
                c.execute('UPDATE branch_memory SET created_at=updated_at WHERE created_at IS NULL OR created_at=\'\'')
    def import_legacy_once(self, old):
        """Import MVP data only once; never resurrect user-deleted tasks on later startups."""
        with self.conn() as c:
            done = c.execute("SELECT value FROM migration_state WHERE key='legacy_mvp_import_v1'").fetchone()
            if done:
                return
            existing = c.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
            if existing:
                c.execute("INSERT INTO migration_state(key,value,updated_at) VALUES(?,?,?)",
                          ('legacy_mvp_import_v1','skipped_existing_database',self.now()))
                return
        self.import_legacy(old)
        with self.conn() as c:
            c.execute("INSERT OR REPLACE INTO migration_state(key,value,updated_at) VALUES(?,?,?)",
                      ('legacy_mvp_import_v1','imported',self.now()))

    def import_legacy(self, old):
        try:
            src=sqlite3.connect(old); src.row_factory=sqlite3.Row
            tasks=src.execute('SELECT * FROM tasks').fetchall(); events=src.execute('SELECT * FROM events').fetchall()
            with self.conn() as dst:
                project=dst.execute('SELECT id FROM projects WHERE name=?',('Импорт из MVP',)).fetchone()
                if not project:
                    pid=dst.execute('INSERT INTO projects(name,root,created_at) VALUES(?,?,?)',('Импорт из MVP','',self.now())).lastrowid
                else: pid=project['id']
                for t in tasks:
                    found=dst.execute('SELECT id FROM tasks WHERE title=? AND created_at=?',(t['title'],t['created_at'])).fetchone()
                    if found: continue
                    tid=dst.execute('INSERT INTO tasks(project_id,title,status,summary,created_at,updated_at) VALUES(?,?,?,?,?,?)',(pid,t['title'],t['status'],t['summary'],t['created_at'],t['updated_at'])).lastrowid
                    bid=dst.execute('INSERT INTO branches(task_id,name,created_at,updated_at) VALUES(?,?,?,?)',(tid,'Основная',t['created_at'],t['updated_at'])).lastrowid
                    for e in events:
                        if e['task_id']==t['id']:
                            try: payload=json.loads(e['payload']); content=payload.get('text') or json.dumps(payload,ensure_ascii=False)
                            except: content=e['payload']
                            dst.execute('INSERT INTO messages(branch_id,role,content,created_at) VALUES(?,?,?,?)',(bid,'assistant' if e['kind']=='assistant' else 'user' if e['kind']=='user' else 'tool',content,e['created_at']))
                            dst.execute('INSERT INTO events(task_id,kind,payload,created_at) VALUES(?,?,?,?)',(tid,e['kind'],e['payload'],e['created_at']))
            src.close()
        except Exception as e: print('Предупреждение: импорт старой БД пропущен:',e)


    def has_app_settings(self):
        with self.conn() as c:
            return c.execute('SELECT 1 FROM app_settings LIMIT 1').fetchone() is not None

    def get_app_settings(self):
        defaults = {
            'context_limit': 50000,
            'max_tool_rounds': 16,
            'max_tool_calls': 24,
            'temperature': 0.2,
            'request_timeout': 180,
            'summary_message_max_chars': 15000,
            'default_project_id': None,
        }
        with self.conn() as c:
            rows = c.execute('SELECT key,value FROM app_settings').fetchall()
        values = dict(defaults)
        for row in rows:
            try:
                values[row['key']] = json.loads(row['value'])
            except Exception:
                continue
        return values

    def set_app_settings(self, values):
        allowed = {'context_limit','max_tool_rounds','max_tool_calls','temperature','request_timeout','summary_message_max_chars','default_project_id'}
        if set(values) - allowed:
            raise ValueError('Переданы неизвестные настройки')
        current = self.get_app_settings()
        current.update(values)
        limits = {
            'context_limit': (8192, 262144),
            'max_tool_rounds': (1, 32),
            'max_tool_calls': (1, 64),
            'request_timeout': (30, 600),
            'summary_message_max_chars': (1000, 50000),
        }
        for key, (low, high) in limits.items():
            try: value = int(current[key])
            except Exception: raise ValueError(f'{key}: требуется целое число')
            if not low <= value <= high: raise ValueError(f'{key}: допустимый диапазон {low}–{high}')
            current[key] = value
        try: temperature = float(current['temperature'])
        except Exception: raise ValueError('temperature: требуется число')
        if not 0.0 <= temperature <= 1.0: raise ValueError('temperature: допустимый диапазон 0–1')
        current['temperature'] = temperature
        default_project_id = current.get('default_project_id')
        if default_project_id in ('', 0):
            default_project_id = None
        if default_project_id is not None:
            try:
                default_project_id = int(default_project_id)
            except (TypeError, ValueError):
                raise ValueError('Проект по умолчанию: некорректный идентификатор')
            project = self.project(default_project_id)
            if not project or project.get('archived_at'):
                raise ValueError('Проект по умолчанию не найден или находится в архиве')
        current['default_project_id'] = default_project_id
        with self.conn() as c:
            now = self.now()
            for key, value in current.items():
                c.execute('INSERT INTO app_settings(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                          (key,json.dumps(value,ensure_ascii=False),now))
        return current

    def get_project_settings(self, project_id):
        with self.conn() as c:
            row=c.execute('SELECT autonomy FROM project_settings WHERE project_id=?',(project_id,)).fetchone()
            return {'autonomy':row['autonomy'] if row else 'analysis'}

    def set_project_autonomy(self, project_id, autonomy):
        if autonomy not in {'analysis','development','full'}: raise ValueError('Недопустимый уровень автономности')
        with self.conn() as c:
            c.execute('INSERT INTO project_settings(project_id,autonomy,updated_at) VALUES(?,?,?) ON CONFLICT(project_id) DO UPDATE SET autonomy=excluded.autonomy,updated_at=excluded.updated_at',(project_id,autonomy,self.now()))

    def create_project(self,name,root):
        with self.conn() as c: return c.execute('INSERT INTO projects(name,root,created_at) VALUES(?,?,?)',(name,root,self.now())).lastrowid
    def projects(self, include_archived=False):
        with self.conn() as c:
            where = '' if include_archived else 'WHERE p.archived_at IS NULL'
            return [dict(r) for r in c.execute(f'SELECT p.*, (SELECT COUNT(*) FROM tasks t WHERE t.project_id=p.id) task_count FROM projects p {where} ORDER BY p.id DESC')]

    def project(self, project_id):
        with self.conn() as c:
            row=c.execute('SELECT * FROM projects WHERE id=?',(project_id,)).fetchone()
            return dict(row) if row else None

    def task_for_branch(self, branch_id):
        with self.conn() as c:
            row=c.execute('SELECT t.* FROM tasks t JOIN branches b ON b.task_id=t.id WHERE b.id=?',(branch_id,)).fetchone()
            return dict(row) if row else None

    def project_for_branch(self, branch_id):
        with self.conn() as c:
            row=c.execute('SELECT p.* FROM projects p JOIN tasks t ON t.project_id=p.id JOIN branches b ON b.task_id=t.id WHERE b.id=?',(branch_id,)).fetchone()
            return dict(row) if row else None

    def project_for_pending(self, pending_id):
        with self.conn() as c:
            row=c.execute('SELECT p.* FROM projects p JOIN tasks t ON t.project_id=p.id JOIN branches b ON b.task_id=t.id JOIN pending_changes pc ON pc.branch_id=b.id WHERE pc.id=?',(pending_id,)).fetchone()
            return dict(row) if row else None

    def rename_project(self, project_id, name):
        with self.conn() as c:
            c.execute('UPDATE projects SET name=? WHERE id=?',(name,project_id))
    def archive_project(self, project_id):
        with self.conn() as c:
            cur=c.execute('UPDATE projects SET archived_at=? WHERE id=? AND archived_at IS NULL',(self.now(),project_id))
            return cur.rowcount > 0
    def restore_project(self, project_id):
        with self.conn() as c:
            cur=c.execute('UPDATE projects SET archived_at=NULL WHERE id=? AND archived_at IS NOT NULL',(project_id,))
            return cur.rowcount > 0
    def find_project_by_root(self, root):
        target=str(root).replace('\\','/').rstrip('/').casefold()
        with self.conn() as c:
            rows=c.execute('SELECT * FROM projects').fetchall()
            for row in rows:
                candidate=str(row['root'] or '').replace('\\','/').rstrip('/').casefold()
                if candidate == target:
                    return dict(row)
        return None
    def ensure_project(self,name,root):
        with self.conn() as c:
            r=c.execute('SELECT * FROM projects WHERE root=?',(root,)).fetchone()
            if r:
                if r['archived_at'] is not None: c.execute('UPDATE projects SET archived_at=NULL WHERE id=?',(r['id'],))
                return dict(c.execute('SELECT * FROM projects WHERE id=?',(r['id'],)).fetchone())
            pid=c.execute('INSERT INTO projects(name,root,created_at) VALUES(?,?,?)',(name,root,self.now())).lastrowid
            return dict(c.execute('SELECT * FROM projects WHERE id=?',(pid,)).fetchone())
    def save_task_memory(self, task_id, summary):
        with self.conn() as c:
            c.execute('UPDATE tasks SET summary=?,updated_at=? WHERE id=?',(summary,self.now(),task_id))

    def get_project_memory(self, project_id):
        with self.conn() as c:
            row=c.execute('SELECT summary,updated_at FROM project_memory WHERE project_id=?',(project_id,)).fetchone()
            return dict(row) if row else None

    def save_project_memory(self, project_id, summary):
        with self.conn() as c:
            c.execute('INSERT INTO project_memory(project_id,summary,updated_at) VALUES(?,?,?) ON CONFLICT(project_id) DO UPDATE SET summary=excluded.summary,updated_at=excluded.updated_at',(project_id,summary,self.now()))

    def create_task(self,project_id,title):
        n=self.now()
        with self.conn() as c:
            tid=c.execute('INSERT INTO tasks(project_id,title,created_at,updated_at) VALUES(?,?,?,?)',(project_id,title,n,n)).lastrowid
            bid=c.execute('INSERT INTO branches(task_id,name,created_at,updated_at) VALUES(?,?,?,?)',(tid,'Основная',n,n)).lastrowid
            return tid,bid
    def create_task_with_memory(self, project_id, title, summary, attachment_ids=None):
        """Atomically create a continuation task, persist its handoff and grant scoped attachment access."""
        n = self.now()
        ids = list(dict.fromkeys(int(x) for x in (attachment_ids or [])))
        with self.conn() as c:
            if ids:
                marks = ','.join('?' for _ in ids)
                found = c.execute(f'SELECT id FROM attachments WHERE project_id=? AND id IN ({marks})', [project_id, *ids]).fetchall()
                if len(found) != len(ids):
                    raise ValueError('Одно из переносимых вложений не найдено в исходном проекте')
            tid = c.execute(
                'INSERT INTO tasks(project_id,title,summary,created_at,updated_at) VALUES(?,?,?,?,?)',
                (project_id, title, summary, n, n),
            ).lastrowid
            bid = c.execute(
                'INSERT INTO branches(task_id,name,created_at,updated_at) VALUES(?,?,?,?)',
                (tid, 'Основная', n, n),
            ).lastrowid
            c.executemany(
                'INSERT INTO task_attachment_access(task_id,attachment_id,granted_at,source) VALUES(?,?,?,?)',
                [(tid, aid, n, 'handoff') for aid in ids],
            )
            return tid, bid
    def tasks(self,project_id=None):
        with self.conn() as c:
            q='SELECT * FROM tasks'; args=()
            if project_id: q+=' WHERE project_id=?'; args=(project_id,)
            return [dict(r) for r in c.execute(q+' ORDER BY updated_at DESC',args)]
    def branches(self,task_id):
        with self.conn() as c: return [dict(r) for r in c.execute('SELECT * FROM branches WHERE task_id=? ORDER BY id',(task_id,))]
    def create_branch(self,branch_id,name):
        n=self.now()
        inherited=self.messages(branch_id)
        mid=inherited[-1]['id'] if inherited else None
        with self.conn() as c:
            src=c.execute('SELECT * FROM branches WHERE id=?',(branch_id,)).fetchone()
            if not src: raise ValueError('Ветка не найдена')
            new_id=c.execute('INSERT INTO branches(task_id,name,parent_branch_id,fork_message_id,created_at,updated_at) VALUES(?,?,?,?,?,?)',(src['task_id'],name,branch_id,mid,n,n)).lastrowid
            mem=c.execute('SELECT summary,through_message_id,created_at FROM branch_memory WHERE branch_id=?',(branch_id,)).fetchone()
            if mem and mid and int(mem['through_message_id']) <= int(mid):
                c.execute('INSERT INTO branch_memory(branch_id,summary,through_message_id,updated_at,created_at) VALUES(?,?,?,?,?)',(new_id,mem['summary'],mem['through_message_id'],n,mem['created_at'] or n))
            return new_id
    def rename_branch(self,bid,name):
        with self.conn() as c: c.execute('UPDATE branches SET name=?,updated_at=? WHERE id=?',(name,self.now(),bid))
    def delete_branch(self,bid):
        with self.conn() as c:
            row=c.execute('SELECT task_id FROM branches WHERE id=?',(bid,)).fetchone()
            if not row: return
            count=c.execute('SELECT COUNT(*) FROM branches WHERE task_id=?',(row['task_id'],)).fetchone()[0]
            # Delete this branch and all its descendants, deepest first, to satisfy self-FK.
            ids=[]; frontier=[bid]
            while frontier:
                ids.extend(frontier)
                marks=','.join('?' for _ in frontier)
                frontier=[r[0] for r in c.execute(f'SELECT id FROM branches WHERE parent_branch_id IN ({marks})',frontier)]
            if count-len(ids)<1: raise ValueError('Нельзя удалить последнюю ветку задачи')
            for branch_id in reversed(ids):
                c.execute('DELETE FROM branches WHERE id=?',(branch_id,))
    def rename_task(self,tid,title):
        with self.conn() as c: c.execute('UPDATE tasks SET title=?,updated_at=? WHERE id=?',(title,self.now(),tid))
    def delete_task(self,tid):
        with self.conn() as c:
            ids=[r[0] for r in c.execute('SELECT id FROM branches WHERE task_id=?',(tid,))]
            # Remove branch trees deepest-first; explicit deletion avoids self-FK cascade failures.
            pending=set(ids)
            while pending:
                leaves=[bid for bid in pending if not c.execute('SELECT 1 FROM branches WHERE parent_branch_id=?',(bid,)).fetchone()]
                if not leaves:
                    raise ValueError('Обнаружен циклический или повреждённый граф веток')
                for bid in leaves:
                    c.execute('DELETE FROM branches WHERE id=?',(bid,))
                    pending.remove(bid)
            c.execute('DELETE FROM tasks WHERE id=?',(tid,))
    def _lineage(self,bid):
        with self.conn() as c:
            b=c.execute('SELECT * FROM branches WHERE id=?',(bid,)).fetchone()
            if not b: raise ValueError('Ветка не найдена')
            chain=[]; cur=b
            while cur:
                chain.append(dict(cur)); cur=c.execute('SELECT * FROM branches WHERE id=?',(cur['parent_branch_id'],)).fetchone() if cur['parent_branch_id'] else None
            chain.reverse(); return chain
    def messages(self,bid,limit=500):
        chain=self._lineage(bid); out=[]
        with self.conn() as c:
            for i,b in enumerate(chain):
                rows=c.execute('SELECT * FROM messages WHERE branch_id=? ORDER BY id',(b['id'],)).fetchall()
                if i<len(chain)-1 and chain[i+1]['fork_message_id']:
                    rows=[r for r in rows if r['id']<=chain[i+1]['fork_message_id']]
                out.extend(dict(r) for r in rows)
            result = out[-limit:]
            if result:
                ids = [int(m['id']) for m in result]
                marks = ','.join('?' for _ in ids)
                links = c.execute(
                    f'''SELECT ma.message_id,a.id,a.original_name,a.media_type,a.kind,a.size,a.note
                        FROM message_attachments ma JOIN attachments a ON a.id=ma.attachment_id
                        WHERE ma.message_id IN ({marks}) ORDER BY a.id''', ids
                ).fetchall()
                by_message = {}
                for link in links:
                    by_message.setdefault(int(link['message_id']), []).append({k: link[k] for k in ('id','original_name','media_type','kind','size','note')})
                for message in result:
                    message['attachments'] = by_message.get(int(message['id']), [])
                    try:
                        message['metadata'] = json.loads(message.get('metadata') or '{}')
                    except (TypeError, json.JSONDecodeError):
                        message['metadata'] = {}
            return result
    def delete_message(self, bid, message_id):
        """Delete only a message owned by this branch; inherited fork history is immutable here."""
        with self.conn() as c:
            row = c.execute('SELECT id,branch_id FROM messages WHERE id=?', (message_id,)).fetchone()
            if not row:
                return False
            if int(row['branch_id']) != int(bid):
                raise ValueError('Нельзя удалить унаследованное сообщение из другой ветки')
            c.execute('DELETE FROM usage WHERE branch_id=? AND turn_message_id=?', (bid, message_id))
            c.execute('DELETE FROM llm_calls WHERE branch_id=? AND message_id=?', (bid, message_id))
            c.execute('DELETE FROM messages WHERE id=? AND branch_id=?', (message_id, bid))
            c.execute('UPDATE branches SET updated_at=? WHERE id=?', (self.now(), bid))
            return True

    def add_message(self,bid,role,content,prompt=0,completion=0,usage_message_id=None,metadata=None):
        n=self.now()
        meta = json.dumps(metadata or {}, ensure_ascii=False)
        with self.conn() as c:
            mid=c.execute('INSERT INTO messages(branch_id,role,content,created_at,prompt_tokens,completion_tokens,metadata) VALUES(?,?,?,?,?,?,?)',(bid,role,content,n,prompt,completion,meta)).lastrowid
            c.execute('UPDATE branches SET updated_at=? WHERE id=?',(n,bid))
            c.execute('UPDATE tasks SET updated_at=? WHERE id=(SELECT task_id FROM branches WHERE id=?)',(n,bid))
            if prompt or completion: c.execute('INSERT INTO usage(branch_id,model,prompt_tokens,completion_tokens,total_tokens,created_at,turn_message_id) VALUES(?,?,?,?,?,?,?)',(bid,'',prompt,completion,prompt+completion,n,usage_message_id))
            return mid
    def save_execution_checkpoint(self, bid, payload, status="paused", reason="tool_event", source_message_id=None):
        """Append an immutable checkpoint version; never overwrite prior recovery state."""
        allowed = {"active", "paused", "completed", "failed", "superseded"}
        if status not in allowed:
            raise ValueError("Недопустимый статус контрольной точки")
        if not isinstance(payload, dict):
            raise TypeError("payload контрольной точки должен быть объектом")
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > 256_000:
            raise ValueError("Контрольная точка превышает лимит 256 КБ")
        now = self.now()
        with self.conn() as c:
            exists = c.execute("SELECT 1 FROM branches WHERE id=?", (int(bid),)).fetchone()
            if not exists:
                raise ValueError("Ветка для контрольной точки не найдена")
            seq = int(c.execute("SELECT COALESCE(MAX(sequence),0)+1 FROM execution_checkpoints WHERE branch_id=?", (int(bid),)).fetchone()[0])
            cur = c.execute("INSERT INTO execution_checkpoints(branch_id,status,reason,payload_json,source_message_id,sequence,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)", (int(bid), status, str(reason)[:80], encoded, source_message_id, seq, now, now))
            # A new resumable checkpoint supersedes older resumable versions, preserving their history.
            if status in {"active", "paused"}:
                c.execute("UPDATE execution_checkpoints SET status='superseded',updated_at=? WHERE branch_id=? AND id<>? AND status IN ('active','paused')", (now, int(bid), cur.lastrowid))
            return {"id": int(cur.lastrowid), "branch_id": int(bid), "status": status, "reason": str(reason)[:80], "sequence": seq, "created_at": now}

    def get_latest_execution_checkpoint(self, bid, resumable_only=True):
        sql = "SELECT * FROM execution_checkpoints WHERE branch_id=?"
        params = [int(bid)]
        if resumable_only:
            sql += " AND status IN ('active','paused')"
        sql += " ORDER BY id DESC LIMIT 1"
        with self.conn() as c:
            row = c.execute(sql, params).fetchone()
        if not row:
            return None
        item = dict(row)
        try:
            item["payload"] = json.loads(item.pop("payload_json"))
        except (TypeError, json.JSONDecodeError):
            item["payload"] = {}
            item["payload_error"] = True
        return item

    def transition_execution_checkpoint(self, checkpoint_id, status):
        if status not in {"active", "paused", "completed", "failed", "superseded"}:
            raise ValueError("Недопустимый статус контрольной точки")
        with self.conn() as c:
            cur = c.execute("UPDATE execution_checkpoints SET status=?,updated_at=? WHERE id=? AND status IN ('active','paused')", (status, self.now(), int(checkpoint_id)))
            return cur.rowcount == 1

    def checkpoint_tool_events(self, bid, limit=12):
        rows = self.messages(bid, limit=max(1, min(100, int(limit) * 3)))
        events = []
        for row in rows:
            if row.get("role") != "tool":
                continue
            meta = row.get("metadata") or {}
            if isinstance(meta, str):
                try: meta = json.loads(meta)
                except Exception: meta = {}
            if isinstance(meta, dict) and meta.get("name"):
                events.append({k: meta.get(k) for k in ("name", "arguments", "status", "duration_ms", "result_preview", "tool_call_id")})
        return events[-max(1, min(100, int(limit))):]

    def usage(self,bid):
        with self.conn() as c:
            rows=c.execute('SELECT COALESCE(SUM(prompt_tokens),0) p,COALESCE(SUM(completion_tokens),0) c,COALESCE(SUM(total_tokens),0) t FROM usage WHERE branch_id=?',(bid,)).fetchone()
            return dict(rows)

    def record_llm_call(self, bid, message_id, model, call_kind, prompt_tokens=None, completion_tokens=None):
        # One API response; turn aggregates remain in the existing usage table.
        reported = prompt_tokens is not None and completion_tokens is not None
        with self.conn() as c:
            return c.execute(
                """INSERT INTO llm_calls(branch_id,message_id,model,call_kind,prompt_tokens,completion_tokens,usage_reported,created_at)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (bid, message_id, model or '', call_kind or 'chat',
                 int(prompt_tokens) if prompt_tokens is not None else None,
                 int(completion_tokens) if completion_tokens is not None else None,
                 1 if reported else 0, self.now())
            ).lastrowid

    def usage_lineage(self, bid):
        # New API calls are read from llm_calls; legacy aggregate rows remain in usage.
        # turn_message_id marks aggregates represented by detailed calls, preventing double counting.
        chain = self._lineage(bid)
        direct = {'p': 0, 'c': 0, 't': 0}
        inherited = {'p': 0, 'c': 0, 't': 0}
        with self.conn() as c:
            for i, branch in enumerate(chain):
                if i == len(chain) - 1:
                    target = direct
                    legacy_rows = c.execute(
                        'SELECT COALESCE(SUM(prompt_tokens),0) p, COALESCE(SUM(completion_tokens),0) c, COALESCE(SUM(total_tokens),0) t FROM usage WHERE branch_id=? AND turn_message_id IS NULL',
                        (branch['id'],)
                    ).fetchone()
                    call_rows = c.execute(
                        'SELECT COALESCE(SUM(prompt_tokens),0) p, COALESCE(SUM(completion_tokens),0) c FROM llm_calls WHERE branch_id=? AND usage_reported=1',
                        (branch['id'],)
                    ).fetchone()
                else:
                    target = inherited
                    cutoff = chain[i + 1].get('fork_message_id')
                    if not cutoff:
                        continue
                    msg = c.execute('SELECT created_at FROM messages WHERE id=? AND branch_id=?',
                                    (cutoff, branch['id'])).fetchone()
                    if not msg:
                        continue
                    legacy_rows = c.execute(
                        'SELECT COALESCE(SUM(prompt_tokens),0) p, COALESCE(SUM(completion_tokens),0) c, COALESCE(SUM(total_tokens),0) t FROM usage WHERE branch_id=? AND turn_message_id IS NULL AND created_at<=?',
                        (branch['id'], msg['created_at'])
                    ).fetchone()
                    call_rows = c.execute(
                        'SELECT COALESCE(SUM(prompt_tokens),0) p, COALESCE(SUM(completion_tokens),0) c FROM llm_calls WHERE branch_id=? AND message_id IS NOT NULL AND message_id<=? AND usage_reported=1',
                        (branch['id'], cutoff)
                    ).fetchone()
                target['p'] += int(legacy_rows['p'] or 0) + int(call_rows['p'] or 0)
                target['c'] += int(legacy_rows['c'] or 0) + int(call_rows['c'] or 0)
                target['t'] += int(legacy_rows['t'] or 0) + int(call_rows['p'] or 0) + int(call_rows['c'] or 0)
        return {'direct': direct, 'inherited': inherited,
                'history': {k: direct[k] + inherited[k] for k in ('p', 'c', 't')}}

    def llm_call_history(self, bid, limit=12):
        # Includes detailed calls from ancestors only up to each fork point.
        chain = self._lineage(bid)
        rows_out = []
        with self.conn() as c:
            for i, branch in enumerate(chain):
                if i == len(chain) - 1:
                    rows = c.execute('SELECT * FROM llm_calls WHERE branch_id=?', (branch['id'],)).fetchall()
                else:
                    cutoff = chain[i + 1].get('fork_message_id')
                    if not cutoff:
                        continue
                    rows = c.execute(
                        'SELECT * FROM llm_calls WHERE branch_id=? AND message_id IS NOT NULL AND message_id<=?',
                        (branch['id'], cutoff)
                    ).fetchall()
                rows_out.extend(dict(r) for r in rows)
        rows_out.sort(key=lambda x: (x['created_at'], x['id']))
        return rows_out[-max(1, int(limit)):]

    def last_llm_turn(self, bid):
        """Return API usage for the latest user turn across the visible branch lineage."""
        chain = self._lineage(bid)
        user_turns = []
        with self.conn() as c:
            for i, branch in enumerate(chain):
                if i < len(chain) - 1:
                    cutoff = chain[i + 1].get('fork_message_id')
                    if not cutoff:
                        continue
                    rows = c.execute(
                        "SELECT id,created_at FROM messages WHERE branch_id=? AND role='user' AND id<=?",
                        (branch['id'], cutoff)
                    ).fetchall()
                else:
                    rows = c.execute(
                        "SELECT id,created_at FROM messages WHERE branch_id=? AND role='user'",
                        (branch['id'],)
                    ).fetchall()
                user_turns.extend(dict(r) for r in rows)
            if not user_turns:
                return None
            user_turns.sort(key=lambda x: (x['created_at'], x['id']))
            turn = user_turns[-1]
            rows = c.execute('SELECT * FROM llm_calls WHERE message_id=? ORDER BY id',
                             (turn['id'],)).fetchall()
            if not rows:
                return None
            reported = [r for r in rows if r['usage_reported']]
            unreported = len(rows) - len(reported)
            prompt = sum(int(r['prompt_tokens'] or 0) for r in reported)
            completion = sum(int(r['completion_tokens'] or 0) for r in reported)
            return {
                'message_id': int(turn['id']),
                'created_at': turn['created_at'],
                'call_count': len(rows),
                'reported_calls': len(reported),
                'unreported_calls': unreported,
                'prompt_tokens': prompt if reported else None,
                'completion_tokens': completion if reported else None,
                'total_tokens': prompt + completion if reported else None,
                'complete': bool(reported) and unreported == 0,
            }

    def llm_unreported_count(self, bid):
        chain = self._lineage(bid)
        total = 0
        with self.conn() as c:
            for i, branch in enumerate(chain):
                if i == len(chain) - 1:
                    total += c.execute('SELECT COUNT(*) FROM llm_calls WHERE branch_id=? AND usage_reported=0',
                                       (branch['id'],)).fetchone()[0]
                else:
                    cutoff = chain[i + 1].get('fork_message_id')
                    if cutoff:
                        total += c.execute('SELECT COUNT(*) FROM llm_calls WHERE branch_id=? AND message_id IS NOT NULL AND message_id<=? AND usage_reported=0',
                                            (branch['id'], cutoff)).fetchone()[0]
        return int(total)

    def get_memory(self,bid):
        with self.conn() as c:
            row=c.execute('SELECT summary,through_message_id,created_at,updated_at FROM branch_memory WHERE branch_id=?',(bid,)).fetchone()
            return dict(row) if row else None
    def save_memory(self,bid,summary,through_message_id):
        with self.conn() as c:
            now=self.now()
            c.execute('INSERT INTO branch_memory(branch_id,summary,through_message_id,updated_at,created_at) VALUES(?,?,?,?,?) ON CONFLICT(branch_id) DO UPDATE SET summary=excluded.summary,through_message_id=excluded.through_message_id,updated_at=excluded.updated_at',(bid,summary,through_message_id,now,now))
    def add_attachment(self, *, project_id, task_id, branch_id, original_name, stored_name, media_type, kind, size, sha256, note, chunks):
        with self.conn() as c:
            aid = c.execute(
                "INSERT INTO attachments(project_id,task_id,branch_id,original_name,stored_name,media_type,kind,size,sha256,note,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (project_id,task_id,branch_id,original_name,stored_name,media_type,kind,size,sha256,note,self.now())
            ).lastrowid
            c.executemany(
                'INSERT INTO attachment_chunks(attachment_id,source_path,chunk_index,content) VALUES(?,?,?,?)',
                [(aid, x.get('source_path', original_name), int(x.get('chunk_index', i)), x.get('content','')) for i,x in enumerate(chunks) if x.get('content')]
            )
            return aid

    def attachment(self, aid):
        with self.conn() as c:
            row = c.execute('SELECT * FROM attachments WHERE id=?', (aid,)).fetchone()
            return dict(row) if row else None

    def read_attachment_chunks(self, aid, project_id, task_id=None, branch_id=None, start_chunk=0, max_chunks=3):
        """Read a deterministic range of indexed chunks and report exact coverage."""
        start_chunk = max(0, int(start_chunk or 0))
        max_chunks = max(1, min(6, int(max_chunks or 3)))
        lineage_ids = [int(x['id']) for x in self._lineage(branch_id)] if branch_id is not None else []
        with self.conn() as c:
            row = c.execute('SELECT * FROM attachments WHERE id=? AND project_id=?', (aid, project_id)).fetchone()
            if not row:
                raise ValueError('Вложение не найдено в текущем проекте')
            item = dict(row)
            granted = bool(task_id is not None and c.execute(
                'SELECT 1 FROM task_attachment_access WHERE task_id=? AND attachment_id=?', (task_id, aid)
            ).fetchone())
            if not granted:
                if item['task_id'] is not None and (task_id is None or int(item['task_id']) != int(task_id)):
                    raise ValueError('Вложение относится к другой задаче')
                if item['branch_id'] is not None and int(item['branch_id']) not in lineage_ids:
                    raise ValueError('Вложение относится к другой ветке')
            total = int(c.execute('SELECT COUNT(*) FROM attachment_chunks WHERE attachment_id=?', (aid,)).fetchone()[0])
            rows = c.execute("SELECT source_path,chunk_index,content FROM attachment_chunks WHERE attachment_id=? ORDER BY id LIMIT ? OFFSET ?", (aid, max_chunks, start_chunk)).fetchall()
            selected = [dict(x) for x in rows]
            for index, chunk in enumerate(selected):
                chunk['chunk_index'] = start_chunk + index
            returned = len(selected)
            next_chunk = start_chunk + returned
            complete = next_chunk >= total
            return {
                'attachment': {k: item[k] for k in ('id','original_name','kind','size','note','created_at')},
                'total_chunks': total, 'start_chunk': start_chunk,
                'end_chunk': (next_chunk - 1) if returned else None,
                'returned_chunks': returned, 'next_chunk': None if complete else next_chunk,
                'complete': complete, 'chunks': selected,
            }

    def pending_for_path(self, bid, path):
        with self.conn() as c:
            row = c.execute("SELECT id,path,content,status FROM pending_changes WHERE branch_id=? AND path=? AND status='pending' ORDER BY id DESC LIMIT 1", (bid, path)).fetchone()
            return dict(row) if row else None

    def attachments(self, project_id, task_id=None, branch_id=None):
        q = 'SELECT * FROM attachments WHERE project_id=?'
        args = [project_id]
        if task_id is not None:
            q += ' AND (task_id IS NULL OR task_id=? OR EXISTS (SELECT 1 FROM task_attachment_access taa WHERE taa.task_id=? AND taa.attachment_id=attachments.id))'
            args.extend([task_id, task_id])
        if branch_id is not None:
            lineage_ids = [int(x['id']) for x in self._lineage(branch_id)]
            marks = ','.join('?' for _ in lineage_ids)
            q += f' AND (branch_id IS NULL OR branch_id IN ({marks}) OR EXISTS (SELECT 1 FROM task_attachment_access taa WHERE taa.task_id=? AND taa.attachment_id=attachments.id))'
            args.extend(lineage_ids)
            if task_id is None:
                q = q.replace('taa.task_id=? AND taa.attachment_id=attachments.id))', 'taa.task_id=-1 AND taa.attachment_id=attachments.id))')
            else:
                args.append(task_id)
        with self.conn() as c:
            rows = c.execute(q + ' ORDER BY created_at DESC,id DESC', args).fetchall()
            out=[]
            for row in rows:
                item=dict(row)
                item.pop('stored_name', None); item.pop('sha256', None)
                item['chunks'] = c.execute('SELECT COUNT(*) FROM attachment_chunks WHERE attachment_id=?',(item['id'],)).fetchone()[0]
                out.append(item)
            return out

    def link_message_attachments(self, message_id, attachment_ids):
        with self.conn() as c:
            c.executemany('INSERT OR IGNORE INTO message_attachments(message_id,attachment_id) VALUES(?,?)', [(message_id, int(a)) for a in attachment_ids])

    def attachment_payload(self, attachment_ids, project_id, task_id, branch_id, max_total=26000):
        ids = list(dict.fromkeys(int(x) for x in (attachment_ids or [])))
        if not ids:
            return [], ''
        if len(ids) > 12:
            raise ValueError('За одно сообщение можно приложить не более 12 файлов')
        marks=','.join('?' for _ in ids)
        lineage_ids = [int(x['id']) for x in self._lineage(branch_id)] if branch_id is not None else []
        with self.conn() as c:
            rows=c.execute(f'SELECT * FROM attachments WHERE id IN ({marks})',ids).fetchall()
            found={int(r['id']):dict(r) for r in rows}
            if len(found) != len(ids):
                raise ValueError('Одно из вложений не найдено')
            output=[]; sections=[]; used=0
            for aid in ids:
                a=found[aid]
                if int(a['project_id']) != int(project_id):
                    raise ValueError('Вложение относится к другому проекту')
                granted = bool(c.execute(
                    'SELECT 1 FROM task_attachment_access WHERE task_id=? AND attachment_id=?', (task_id, aid)
                ).fetchone()) if task_id is not None else False
                if not granted:
                    if a['task_id'] is not None and int(a['task_id']) != int(task_id):
                        raise ValueError('Вложение относится к другой задаче')
                    if a['branch_id'] is not None and int(a['branch_id']) not in lineage_ids:
                        raise ValueError('Вложение относится к другой ветке')
                output.append(aid)
                chunks=c.execute('SELECT source_path,chunk_index,content FROM attachment_chunks WHERE attachment_id=? ORDER BY id',(aid,)).fetchall()
                if chunks and used < max_total:
                    header=f"\n\n--- ВЛОЖЕНИЕ: {a['original_name']} ---\n"
                    section=header
                    for ch in chunks:
                        remaining=max_total-used-len(section)
                        if remaining <= 0: break
                        text=ch['content'][:remaining]
                        section += f"\n[Файл внутри архива: {ch['source_path']}]\n{text}\n"
                        used += len(text)
                    sections.append(section)
                else:
                    sections.append(f"\n\n[Вложение: {a['original_name']}. {a['note'] or 'Содержимое не индексировано; файл доступен в списке вложений.'}]")
            model_text='\n'.join(sections)
            if len(model_text)>max_total:
                model_text=model_text[:max_total]+'\n[Контекст вложений сокращён по лимиту. Используй поиск по файлам для нужного фрагмента.]'
            return output, model_text

    def search_attachments(self, project_id, query, task_id=None, branch_id=None, limit=30):
        q="SELECT c.attachment_id,c.source_path,c.chunk_index,c.content,a.original_name,a.task_id,a.branch_id FROM attachment_chunks c JOIN attachments a ON a.id=c.attachment_id WHERE a.project_id=? AND c.content LIKE ?"
        args=[project_id, '%'+query+'%']
        if task_id is not None:
            q+=' AND (a.task_id IS NULL OR a.task_id=? OR EXISTS (SELECT 1 FROM task_attachment_access taa WHERE taa.task_id=? AND taa.attachment_id=a.id))'; args.extend([task_id, task_id])
        if branch_id is not None:
            lineage_ids = [int(x['id']) for x in self._lineage(branch_id)]
            marks = ','.join('?' for _ in lineage_ids)
            q+=f' AND (a.branch_id IS NULL OR a.branch_id IN ({marks}) OR EXISTS (SELECT 1 FROM task_attachment_access taa WHERE taa.task_id=? AND taa.attachment_id=a.id))'; args.extend(lineage_ids)
            args.append(task_id if task_id is not None else -1)
        args.append(limit)
        with self.conn() as c:
            return [dict(r) for r in c.execute(q+' ORDER BY a.created_at DESC,c.id LIMIT ?',args)]

    def delete_attachment(self, aid, project_id):
        with self.conn() as c:
            row=c.execute('SELECT stored_name FROM attachments WHERE id=? AND project_id=?',(aid,project_id)).fetchone()
            if not row: return None
            stored=row['stored_name']
            c.execute('DELETE FROM attachments WHERE id=?',(aid,))
            return stored

    def add_pending(self,bid,path,content):
        with self.conn() as c: return c.execute('INSERT INTO pending_changes(branch_id,path,content,created_at) VALUES(?,?,?,?)',(bid,path,content,self.now())).lastrowid
    def pending(self,bid=None):
        with self.conn() as c:
            q="SELECT * FROM pending_changes WHERE status='pending'"; a=()
            if bid: q+=' AND branch_id=?'; a=(bid,)
            return [dict(r) for r in c.execute(q+' ORDER BY id DESC',a)]
    def set_pending(self,pid,status):
        with self.conn() as c: c.execute('UPDATE pending_changes SET status=? WHERE id=?',(status,pid))

    def add_input_request(self, bid, title, prompt, input_type):
        if input_type not in {'text', 'secret'}:
            raise ValueError('Недопустимый тип ввода')
        with self.conn() as c:
            return c.execute('INSERT INTO input_requests(branch_id,title,prompt,input_type,created_at) VALUES(?,?,?,?,?)',
                             (bid, str(title)[:160], str(prompt)[:2000], input_type, self.now())).lastrowid

    def set_input_request_context(self, request_id, context, tool_call_id, model, user_message_id):
        if len(json.dumps(context, ensure_ascii=False).encode('utf-8')) > 8 * 1024 * 1024:
            raise ValueError('Контекст продолжения превышает безопасный лимит 8 МБ')
        snapshot = self._resume_context_snapshot(context, tool_call_id)
        payload = json.dumps(snapshot, ensure_ascii=False, separators=(',', ':'))
        if len(payload.encode('utf-8')) > 8 * 1024 * 1024:
            raise ValueError('Контекст продолжения превышает безопасный лимит 8 МБ')
        with self.conn() as c:
            changed = c.execute("UPDATE input_requests SET context_json=?,tool_call_id=?,model=?,user_message_id=?,resume_status='waiting' WHERE id=? AND status='pending'",
                                (payload, str(tool_call_id or ''), str(model or ''), user_message_id, request_id)).rowcount
            if not changed:
                raise ValueError('Запрос ввода уже обработан или не существует')

    def pending_input_requests(self, bid=None):
        with self.conn() as c:
            q = "SELECT id,branch_id,title,prompt,input_type,status,created_at FROM input_requests WHERE status='pending' AND context_json<>'' AND tool_call_id<>''"
            args = ()
            if bid is not None:
                q += ' AND branch_id=?'; args = (bid,)
            return [dict(r) for r in c.execute(q + ' ORDER BY id DESC', args)]

    def input_request(self, request_id):
        with self.conn() as c:
            row = c.execute('SELECT * FROM input_requests WHERE id=?', (request_id,)).fetchone()
            return dict(row) if row else None

    def complete_input_request(self, request_id, result_text='', credential_ref=''):
        with self.conn() as c:
            changed = c.execute("UPDATE input_requests SET status='completed',finished_at=?,result_text=?,credential_ref=? WHERE id=? AND status='pending'",
                                (self.now(), str(result_text)[:8000], str(credential_ref), request_id)).rowcount
            return bool(changed)

    def reject_input_request(self, request_id):
        with self.conn() as c:
            return c.execute("UPDATE input_requests SET status='rejected',finished_at=?,result_text='Отклонено пользователем' WHERE id=? AND status='pending'",
                             (self.now(), request_id)).rowcount == 1

    def claim_input_request_resume(self, request_id):
        with self.conn() as c:
            return c.execute("UPDATE input_requests SET resume_status='running' WHERE id=? AND resume_status='waiting'", (request_id,)).rowcount == 1

    def mark_input_request_resumed(self, request_id, status='completed'):
        with self.conn() as c:
            c.execute('UPDATE input_requests SET resume_status=? WHERE id=?', (status, request_id))

    def input_requests_waiting_resume(self):
        with self.conn() as c:
            return [dict(r) for r in c.execute("SELECT * FROM input_requests WHERE status IN ('completed','rejected') AND resume_status='waiting' AND context_json<>'' AND tool_call_id<>'' ORDER BY id")]

    def recover_interrupted_input_resumes(self):
        with self.conn() as c:
            rows = [dict(r) for r in c.execute("SELECT * FROM input_requests WHERE resume_status='running'")]
            for row in rows:
                c.execute("UPDATE input_requests SET resume_status='failed' WHERE id=? AND resume_status='running'", (row['id'],))
            return rows

    def server_profiles(self):
        with self.conn() as c:
            return [dict(r) for r in c.execute('SELECT id,name,host,port,username,auth_method,credential_ref,created_at,updated_at FROM server_profiles ORDER BY name COLLATE NOCASE')]

    def server_profile(self, profile_id):
        with self.conn() as c:
            row = c.execute('SELECT * FROM server_profiles WHERE id=?', (profile_id,)).fetchone()
            return dict(row) if row else None

    def save_server_profile(self, profile_id, name, host, port, username, auth_method, credential_ref=''):
        with self.conn() as c:
            now = self.now()
            if profile_id:
                changed = c.execute('UPDATE server_profiles SET name=?,host=?,port=?,username=?,auth_method=?,credential_ref=?,updated_at=? WHERE id=?',
                                    (name,host,port,username,auth_method,credential_ref,now,profile_id)).rowcount
                if not changed:
                    raise ValueError('SSH-профиль не найден')
                return profile_id
            return c.execute('INSERT INTO server_profiles(name,host,port,username,auth_method,credential_ref,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',
                             (name,host,port,username,auth_method,credential_ref,now,now)).lastrowid

    def delete_server_profile(self, profile_id):
        with self.conn() as c:
            return c.execute('DELETE FROM server_profiles WHERE id=?', (profile_id,)).rowcount == 1

    def credential_ref_used_by_profile(self, credential_ref, exclude_profile_id=None):
        if not credential_ref:
            return False
        with self.conn() as c:
            q = 'SELECT 1 FROM server_profiles WHERE credential_ref=?'
            args = [credential_ref]
            if exclude_profile_id is not None:
                q += ' AND id<>?'; args.append(exclude_profile_id)
            return c.execute(q + ' LIMIT 1', args).fetchone() is not None

    def detach_credential_ref_from_input_requests(self, credential_ref):
        if not credential_ref:
            return 0
        with self.conn() as c:
            return c.execute("UPDATE input_requests SET credential_ref='' WHERE credential_ref=?", (credential_ref,)).rowcount

    def credential_refs(self):
        with self.conn() as c:
            rows = c.execute("SELECT credential_ref FROM server_profiles WHERE credential_ref<>'' UNION SELECT credential_ref FROM input_requests WHERE credential_ref<>''").fetchall()
            return {str(row['credential_ref']) for row in rows}

    def claim_execution_approval(self, eid, via='workbench_ui'):
        with self.conn() as c:
            return c.execute("UPDATE pending_execution SET status='running',approved_at=?,approved_via=? WHERE id=? AND status='pending'", (self.now(), str(via), eid)).rowcount == 1

    def reject_execution_by_user(self, eid, via='workbench_ui'):
        with self.conn() as c:
            return c.execute("UPDATE pending_execution SET status='rejected',finished_at=?,rejected_at=?,rejected_via=?,result='Отклонено пользователем' WHERE id=? AND status='pending'", (self.now(), self.now(), str(via), eid)).rowcount == 1

    def add_pending_execution(self,bid,script):
        with self.conn() as c: return c.execute('INSERT INTO pending_execution(branch_id,script,created_at) VALUES(?,?,?)',(bid,script,self.now())).lastrowid
    def set_execution_context(self, eid, context, tool_call_id, model, user_message_id):
        if len(json.dumps(context, ensure_ascii=False).encode('utf-8')) > 8 * 1024 * 1024:
            raise ValueError('Контекст продолжения превышает безопасный лимит 8 МБ')
        snapshot = self._resume_context_snapshot(context, tool_call_id)
        payload = json.dumps(snapshot, ensure_ascii=False, separators=(',', ':'))
        if len(payload.encode('utf-8')) > 8 * 1024 * 1024:
            raise ValueError('Контекст продолжения превышает безопасный лимит 8 МБ')
        with self.conn() as c:
            c.execute("UPDATE pending_execution SET context_json=?,tool_call_id=?,model=?,user_message_id=?,resume_status='waiting' WHERE id=? AND status='pending'",
                      (payload, str(tool_call_id or ''), str(model or ''), user_message_id, eid))
    def set_execution_process(self, eid, process_id):
        with self.conn() as c:
            c.execute("UPDATE pending_execution SET result=? WHERE id=? AND status='running'",
                      (f'process_id={process_id}', eid))
    def claim_execution_resume(self, eid):
        with self.conn() as c:
            return c.execute("UPDATE pending_execution SET resume_status='running' WHERE id=? AND resume_status='waiting'", (eid,)).rowcount == 1

    def mark_execution_resumed(self, eid, status='completed'):
        with self.conn() as c:
            c.execute("UPDATE pending_execution SET resume_status=? WHERE id=?", (status, eid))

    def executions_waiting_resume(self):
        with self.conn() as c:
            return [dict(r) for r in c.execute("SELECT * FROM pending_execution WHERE status IN ('completed','failed','rejected') AND resume_status='waiting' AND context_json<>'' AND tool_call_id<>'' ORDER BY id")]

    def recover_interrupted_execution_resumes(self):
        with self.conn() as c:
            rows = [dict(r) for r in c.execute("SELECT * FROM pending_execution WHERE resume_status='running'")]
            for row in rows:
                c.execute("UPDATE pending_execution SET resume_status='failed' WHERE id=? AND resume_status='running'", (row['id'],))
            return rows

    def recover_interrupted_executions(self):
        with self.conn() as c:
            rows = [dict(r) for r in c.execute("SELECT * FROM pending_execution WHERE status='running'")]
            for row in rows:
                c.execute("UPDATE pending_execution SET status='failed',finished_at=?,result=?,resume_status=CASE WHEN resume_status='waiting' THEN 'failed' ELSE resume_status END WHERE id=? AND status='running'",
                          (self.now(), 'Workbench перезапущен во время выполнения. Фактический результат неизвестен; проверь состояние сервера/операции вручную и не повторяй команду вслепую.', row['id']))
            return rows
    def pending_executions(self,bid=None):
        with self.conn() as c:
            q="SELECT * FROM pending_execution WHERE status='pending'"; a=()
            if bid is not None: q+=' AND branch_id=?'; a=(bid,)
            return [dict(x) for x in c.execute(q+' ORDER BY id DESC',a)]

    def pending_executions_for_project(self, project_id):
        """Return every pending command in a project with its originating task/branch.

        The approval queue is project-scoped rather than branch-scoped so a pending
        command cannot disappear merely because the UI restored a sibling branch.
        Execution still resumes against the original branch stored on the row.
        """
        with self.conn() as c:
            rows = c.execute("""
                SELECT pe.*, b.name AS branch_name, t.id AS task_id, t.title AS task_title,
                       p.id AS project_id, p.name AS project_name
                FROM pending_execution pe
                JOIN branches b ON b.id=pe.branch_id
                JOIN tasks t ON t.id=b.task_id
                JOIN projects p ON p.id=t.project_id
                WHERE pe.status='pending' AND p.id=?
                ORDER BY pe.id DESC
            """, (project_id,)).fetchall()
            return [dict(row) for row in rows]
    def execution_by_id(self,eid):
        with self.conn() as c:
            x=c.execute('SELECT * FROM pending_execution WHERE id=?',(eid,)).fetchone(); return dict(x) if x else None
    def finish_execution(self,eid,status,result):
        with self.conn() as c: c.execute("UPDATE pending_execution SET status=?,finished_at=?,result=? WHERE id=? AND status IN ('pending','running')",(status,self.now(),result,eid))
    def finish_execution_once(self, eid, status, exit_code, stdout, stderr):
        result = (f"Статус: {status}\nКод завершения: {exit_code}\n\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
        with self.conn() as c:
            changed = c.execute("UPDATE pending_execution SET status=?,finished_at=?,result=? WHERE id=? AND status='running'",
                                (status, self.now(), result, eid)).rowcount
            return bool(changed), result
