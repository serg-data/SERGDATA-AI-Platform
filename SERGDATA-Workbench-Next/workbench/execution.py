"""Controlled local execution for SERGDATA Workbench."""
from __future__ import annotations
import os, subprocess, time
from pathlib import Path
from .security import is_sensitive_path

MAX_SCRIPT = 12000
MAX_OUTPUT = 16000
DEFAULT_TIMEOUT = 60

class ExecutionEngine:
    def __init__(self, root: Path):
        self.root = Path(root).expanduser().resolve()
        if not self.root.is_dir(): raise ValueError('Корень проекта не существует')

    def safe_path(self, rel: str) -> Path:
        rel = str(rel or '.')
        p = (self.root / rel).resolve()
        if p != self.root and self.root not in p.parents:
            raise ValueError('Запрещён выход за пределы папки проекта')
        try:
            relative = p.relative_to(self.root)
        except ValueError:
            raise ValueError('Запрещён выход за пределы папки проекта')
        if is_sensitive_path(relative):
            raise ValueError('Доступ к потенциально секретному файлу запрещён')
        return p

    def list_files(self, rel='.', limit=500):
        base=self.safe_path(rel)
        if not base.is_dir(): raise ValueError('Каталог не найден')
        skip={'.git','.venv','venv','node_modules','__pycache__','dist','build','.workbench','.ssh','.aws','.azure','.gnupg','secrets','credentials'}
        denied_files={'.env','.env.local','.env.production','.env.development','.npmrc','.pypirc'}
        rows=[]
        for root, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = [d for d in dirs if d not in skip and not is_sensitive_path((Path(root)/d).relative_to(self.root)) and not (Path(root)/d).is_symlink()]
            dirs[:] = [d for d in dirs if not d.endswith(('.workbench.bak','.workbench.tmp','.bak','.tmp'))]
            for name in dirs+files:
                if is_sensitive_path(name) or name.lower().endswith(('.workbench.bak','.workbench.tmp','.bak','.tmp')): continue
                q=Path(root)/name
                try: q.resolve().relative_to(self.root)
                except ValueError: continue
                if q.is_symlink(): continue
                rows.append(('DIR ' if q.is_dir() else 'FILE')+' '+q.relative_to(self.root).as_posix())
                if len(rows)>=limit: return '\n'.join(rows)+'\n[лимит списка]'
        return '\n'.join(rows) or 'Файлы не найдены'

    def search(self, query, rel='.', limit=40):
        query=str(query or '').strip().lower()
        if not query: raise ValueError('Пустой поисковый запрос')
        base=self.safe_path(rel); matches=[]
        skip={'.git','.venv','venv','node_modules','__pycache__','dist','build','.workbench','.ssh','.aws','.azure','.gnupg','secrets','credentials'}
        denied_files={'.env','.env.local','.env.production','.env.development','.npmrc','.pypirc'}
        for root, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = [d for d in dirs if d not in skip and not is_sensitive_path((Path(root)/d).relative_to(self.root)) and not (Path(root)/d).is_symlink()]
            for name in files:
                f=Path(root)/name
                if is_sensitive_path(name) or name.lower().endswith(('.workbench.bak','.workbench.tmp','.bak','.tmp')): continue
                if f.is_symlink() or f.suffix.lower() in {'.png','.jpg','.jpeg','.gif','.webp','.ico','.pdf','.zip','.db','.sqlite','.exe','.dll','.bin','.pyc'}: continue
                try:
                    f.resolve().relative_to(self.root)
                    if f.stat().st_size>1_000_000: continue
                    for n,line in enumerate(f.read_text('utf-8',errors='ignore').splitlines(),1):
                        if query in line.lower(): matches.append(f'{f.relative_to(self.root).as_posix()}:{n}: {line[:300]}')
                        if len(matches)>=limit: return '\n'.join(matches)
                except (OSError,ValueError): continue
        return '\n'.join(matches) or 'Совпадений нет'

    def read_file(self, rel, start_line=1, max_lines=400):
        f=self.safe_path(rel)
        if not f.is_file(): raise ValueError('Файл не найден')
        if f.stat().st_size>2_000_000: raise ValueError('Файл больше 2 МБ; чтение запрещено')
        lines=f.read_text('utf-8',errors='replace').splitlines(); a=max(1,int(start_line)); b=min(len(lines),a+max(1,min(int(max_lines),1000))-1)
        return f'Файл: {f.relative_to(self.root)}; строки {a}-{b} из {len(lines)}\n'+'\n'.join(f'{i}: {s}' for i,s in enumerate(lines[a-1:b],a))

    def run_check(self, kind, timeout=180):
        commands={'pytest':['python','-m','pytest','-q'], 'compile':['python','-m','compileall','-q','.'], 'ruff':['python','-m','ruff','check','.'], 'git_status':['git','status','--short'], 'git_diff':['git','diff','--','.', ':(exclude)**/.env*', ':(exclude)**/.netrc', ':(exclude)**/.npmrc', ':(exclude)**/.pypirc', ':(exclude)**/*.pem', ':(exclude)**/*.key', ':(exclude)**/*.p12', ':(exclude)**/*.pfx']}
        if kind not in commands: raise ValueError('Команда не входит в разрешённый список')
        return self._run(commands[kind],timeout)

    def run_powershell(self, script, timeout=DEFAULT_TIMEOUT):
        script=str(script or '').strip()
        if not script or len(script)>MAX_SCRIPT: raise ValueError(f'Команда должна содержать от 1 до {MAX_SCRIPT} символов')
        # Explicit user approval is required before this method is called.
        exe=os.environ.get('ComSpec','cmd.exe')
        if os.name=='nt':
            cmd=['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Restricted','-Command',script]
        else:
            cmd=['pwsh','-NoLogo','-NoProfile','-NonInteractive','-Command',script]
        return self._run(cmd,timeout)

    def _run(self, cmd, timeout):
        started=time.monotonic()
        try:
            r=subprocess.run(cmd,cwd=self.root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=max(1,min(int(timeout),180)),shell=False)
            stdout=(r.stdout or '')[-MAX_OUTPUT:]
            stderr=(r.stderr or '')[-MAX_OUTPUT:]
            return {'status':'completed' if r.returncode == 0 else 'failed','exit_code':r.returncode,
                    'duration_sec':round(time.monotonic()-started,2),
                    'stdout':stdout,'stderr':stderr,'output':(stdout+'\n'+stderr)[-MAX_OUTPUT:]}
        except subprocess.TimeoutExpired as e:
            out=(e.stdout or '')+(e.stderr or '')
            if isinstance(out,bytes): out=out.decode('utf-8','replace')
            return {'status':'timed_out','exit_code':None,'timed_out':True,'duration_sec':round(time.monotonic()-started,2),
                    'stdout':str(e.stdout or '')[-MAX_OUTPUT:] if not isinstance(e.stdout,bytes) else e.stdout.decode('utf-8','replace')[-MAX_OUTPUT:],
                    'stderr':(str(e.stderr or '') if not isinstance(e.stderr,bytes) else e.stderr.decode('utf-8','replace'))[-MAX_OUTPUT:]+'\n[ВРЕМЯ ВЫПОЛНЕНИЯ ИСТЕКЛО]',
                    'output':str(out)[-MAX_OUTPUT:]+'\n[ВРЕМЯ ВЫПОЛНЕНИЯ ИСТЕКЛО]'}
