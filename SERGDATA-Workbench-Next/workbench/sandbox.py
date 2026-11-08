"""Project-local experimental workspaces. These are filesystem workspaces, not OS security sandboxes."""
from __future__ import annotations
import json, os, re, shutil, subprocess, time, uuid
from pathlib import Path
from .security import is_sensitive_path

SKIP_DIRS={'.git','.venv','venv','node_modules','__pycache__','.workbench','.ssh','.aws','.azure','.gnupg','secrets','credentials','chat_media','uploads','media','backups','backup','dist','build'}
SKIP_SUFFIXES={'.sqlite','.sqlite3','.db','.wal','.shm','.pyc','.pyo','.pem','.key','.p12','.pfx'}
MAX_FILE=2_000_000
MAX_OUTPUT=12000

class SandboxManager:
    def __init__(self, project_root: Path):
        self.root=Path(project_root).expanduser().resolve()
        if not self.root.is_dir(): raise ValueError('Корень проекта не существует')
        self.base=(self.root/'.workbench'/'sandboxes').resolve()
        self.base.mkdir(parents=True,exist_ok=True)
        if self.base.is_symlink() or self.root not in self.base.parents: raise ValueError('Недопустимый каталог песочниц')

    def _dir(self, sid):
        sid=str(sid or '')
        if len(sid)!=32 or any(c not in '0123456789abcdef' for c in sid): raise ValueError('Некорректный ID эксперимента')
        p=(self.base/sid).resolve()
        if self.base not in p.parents or p.is_symlink(): raise ValueError('Недопустимый путь песочницы')
        if not p.is_dir(): raise ValueError('Эксперимент не найден')
        return p

    def _safe(self, sid, rel):
        base=self._dir(sid); rel=str(rel or '').replace('\\','/')
        if not rel or rel.startswith('/') or any(x in ('..','') for x in rel.split('/')): raise ValueError('Укажи безопасный относительный путь')
        p=(base/'workspace'/rel).resolve()
        if p != base/'workspace' and (base/'workspace') not in p.parents: raise ValueError('Выход за пределы песочницы запрещён')
        if is_sensitive_path(Path(rel)): raise ValueError('Секретные файлы запрещены в песочнице')
        cur=base/'workspace'
        for part in Path(rel).parts:
            cur=cur/part
            if cur.is_symlink(): raise ValueError('Символические ссылки запрещены')
        return p

    def create(self, name='Эксперимент', paths=None):
        sid=uuid.uuid4().hex; dest=self.base/sid; workspace=dest/'workspace'; workspace.mkdir(parents=True)
        selected=[str(x) for x in (paths or [])]
        if selected:
            for rel in selected: self._copy_one(rel,workspace)
        else:
            for current, dirs, files in os.walk(self.root,topdown=True,followlinks=False):
                cur=Path(current); dirs[:]=[d for d in dirs if d not in SKIP_DIRS and not (cur/d).is_symlink() and not is_sensitive_path((cur/d).relative_to(self.root))]
                for fn in files:
                    src=cur/fn; rel=src.relative_to(self.root)
                    if src.is_symlink() or is_sensitive_path(rel) or src.suffix.lower() in SKIP_SUFFIXES or fn.lower() in {'.env','.env.local','.env.production'} or fn.endswith(('.bak','.tmp','.workbench.bak')): continue
                    try:
                        if src.stat().st_size>MAX_FILE: continue
                        target=workspace/rel; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,target)
                    except OSError: continue
        manifest={'id':sid,'name':str(name or 'Эксперимент')[:120],'created_at':time.time(),'source_root':str(self.root),'status':'active','paths':selected,'revision':0,'note':'Файловая копия. Не является изоляцией ОС.'}
        (dest/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        return {'id':sid,'name':manifest['name'],'workspace':str(workspace),'status':'active','copied_files':sum(1 for p in workspace.rglob('*') if p.is_file()),'warning':manifest['note']}

    def _copy_one(self, rel, workspace):
        src=(self.root/rel).resolve()
        if self.root not in src.parents or src.is_symlink() or is_sensitive_path(Path(rel)): raise ValueError(f'Недопустимый путь: {rel}')
        if not src.is_file() or src.stat().st_size>MAX_FILE or src.suffix.lower() in SKIP_SUFFIXES: raise ValueError(f'Файл не подходит для копирования: {rel}')
        dst=workspace/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)

    def revision(self, sid):
        manifest_path = self._dir(sid) / 'manifest.json'
        try:
            return int(json.loads(manifest_path.read_text(encoding='utf-8')).get('revision', 0))
        except (OSError, ValueError, TypeError):
            return 0

    def _bump_revision(self, sid):
        manifest_path = self._dir(sid) / 'manifest.json'
        data = json.loads(manifest_path.read_text(encoding='utf-8'))
        data['revision'] = int(data.get('revision', 0)) + 1
        tmp = manifest_path.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(manifest_path)
        return data['revision']

    def list_files(self, sid, limit=300):
        root=self._dir(sid)/'workspace'; rows=[]
        for p in sorted(root.rglob('*')):
            if p.is_symlink(): continue
            if p.is_file(): rows.append(p.relative_to(root).as_posix())
            if len(rows)>=max(1,min(int(limit),500)): break
        return rows

    def read(self,sid,rel):
        p=self._safe(sid,rel)
        if not p.is_file() or p.stat().st_size>MAX_FILE: raise ValueError('Файл отсутствует или превышает 2 МБ')
        return p.read_text(encoding='utf-8',errors='replace')

    def write(self,sid,rel,content):
        if len(str(content).encode('utf-8'))>MAX_FILE: raise ValueError('Размер файла превышает 2 МБ')
        p=self._safe(sid,rel); p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() and not p.is_file(): raise ValueError('Путь не является файлом')
        tmp=p.with_name(p.name+'.sandbox-tmp'); tmp.write_text(str(content),encoding='utf-8',newline='\n'); tmp.replace(p)
        revision = self._bump_revision(sid)
        return {'path':str(Path(rel)),'bytes':p.stat().st_size,'written':True,'revision':revision}

    def run_check(self,sid,kind,timeout=120,path=None,args=None):
        root=self._dir(sid)/'workspace'
        commands={
            'pytest':['python','-m','pytest','-q'],
            'compile':['python','-m','compileall','-q','.'],
            'ruff':['python','-m','ruff','check','.'],
        }
        if kind == 'pytest':
            safe_args=[]
            for item in (args or []):
                if not isinstance(item,str) or not item or item.startswith(('-', '/')) and item not in ('-v','-q','-x','--disable-warnings','--tb=short','--tb=line') and not re.fullmatch(r'--maxfail=[1-9][0-9]?',item):
                    raise ValueError('Недопустимый аргумент pytest')
                if item.startswith('-'):
                    if item not in ('-v','-q','-x','--disable-warnings','--tb=short','--tb=line') and not re.fullmatch(r'--maxfail=[1-9][0-9]?',item):
                        raise ValueError('Разрешены только безопасные флаги pytest')
                else:
                    target=self._safe(sid,item)
                    if not target.exists(): raise ValueError(f'Путь pytest не найден: {item}')
                    safe_args.append(item)
                if item.startswith('-'): safe_args.append(item)
            argv=commands[kind]+safe_args
        elif kind in ('sh_syntax','bash_syntax','shellcheck'):
            if not path:
                raise ValueError('Для Shell-проверки укажи относительный path внутри песочницы')
            target=self._safe(sid,path)
            if not target.is_file() or target.stat().st_size>MAX_FILE:
                raise ValueError('Shell-файл отсутствует или превышает 2 МБ')
            if kind in ('sh_syntax','bash_syntax') and target.suffix.lower() not in ('.sh','.bash'):
                raise ValueError('Синтаксическая проверка разрешена только для .sh/.bash')
            executable={'sh_syntax':'sh','bash_syntax':'bash','shellcheck':'shellcheck'}[kind]
            resolved=shutil.which(executable)
            if not resolved:
                return {'status':'unavailable','exit_code':None,'duration_sec':0,'stdout':'',
                        'stderr':f'Не найден инструмент {executable}. Установи его или добавь в PATH.'}
            argv=[resolved,'-n',str(target)] if kind in ('sh_syntax','bash_syntax') else [resolved,'--format=gcc',str(target)]
        elif kind in commands:
            argv=commands[kind]
        else:
            raise ValueError('Разрешены pytest, compile, ruff, sh_syntax, bash_syntax и shellcheck')
        started=time.monotonic()
        try:
            r=subprocess.run(argv,cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',
                             timeout=max(1,min(int(timeout),120)),shell=False)
            return {'status':'completed' if r.returncode==0 else 'failed','exit_code':r.returncode,
                    'duration_sec':round(time.monotonic()-started,2),
                    'stdout':(r.stdout or '')[-MAX_OUTPUT:],'stderr':(r.stderr or '')[-MAX_OUTPUT:]}
        except subprocess.TimeoutExpired as exc:
            return {'status':'timed_out','exit_code':None,'duration_sec':round(time.monotonic()-started,2),
                    'stdout':str(exc.stdout or '')[-MAX_OUTPUT:],
                    'stderr':(str(exc.stderr or '')+'\\nПревышено время выполнения')[-MAX_OUTPUT:]}

    def diff(self,sid,limit=100):
        root=self._dir(sid)/'workspace'; rows=[]
        seen=set()
        for p in sorted(root.rglob('*')):
            if not p.is_file() or p.is_symlink(): continue
            rel=p.relative_to(root); key=rel.as_posix(); seen.add(key); src=self.root/rel
            try:
                same=src.is_file() and src.stat().st_size==p.stat().st_size and src.read_bytes()==p.read_bytes()
            except OSError: same=False
            if not same: rows.append({'path':key,'change':'modified' if src.exists() else 'added'})
            if len(rows)>=max(1,min(int(limit),300)): break
        # Detect source files deliberately removed from the experimental copy.
        if len(rows)<max(1,min(int(limit),300)):
            for src in sorted(self.root.rglob('*')):
                if not src.is_file() or src.is_symlink(): continue
                rel=src.relative_to(self.root); key=rel.as_posix()
                if key in seen or any(part in SKIP_DIRS for part in rel.parts) or is_sensitive_path(rel) or src.suffix.lower() in SKIP_SUFFIXES: continue
                if not (root/rel).exists(): rows.append({'path':key,'change':'deleted'})
                if len(rows)>=max(1,min(int(limit),300)): break
        return {'experiment_id':sid,'changes':rows,'count':len(rows)}
