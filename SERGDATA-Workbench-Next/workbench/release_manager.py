"""Safe file-level comparison and approved release between registered projects."""
from __future__ import annotations
import hashlib, json, os, shutil, uuid, unicodedata
from pathlib import Path
from datetime import datetime, timezone

EXCLUDED={'.git','.workbench','.venv','venv','__pycache__','node_modules','.pytest_cache','.mypy_cache','.ruff_cache'}
SECRET_NAMES={'.env','.env.local','.env.production','credentials','secrets','.ssh'}
SECRET_SUFFIXES={'.pem','.key','.p12','.pfx','.dpapi','.sqlite','.sqlite3','.db'}
MAX_FILE=5*1024*1024
MAX_FILES=2000
# Console transcripts accidentally saved under malformed filenames must never enter a release.
ARTIFACT_NAMES={'t_cache __pycache__ .workbench'}

def _safe_join(root:Path, rel:Path)->Path:
    """Resolve a relative project path without traversing symlinks."""
    root=root.resolve()
    candidate=root
    for part in rel.parts:
        candidate=candidate/part
        if candidate.is_symlink():
            raise ValueError(f'Символическая ссылка запрещена в пути релиза: {rel.as_posix()}')
    resolved=candidate.resolve(strict=False)
    if resolved!=root and root not in resolved.parents:
        raise ValueError(f'Путь выходит за пределы проекта: {rel.as_posix()}')
    return candidate

def _safe_rel(raw:str)->Path:
    p=Path(str(raw).replace('\\','/'))
    if p.is_absolute() or not p.parts or any(x in {'..',''} for x in p.parts): raise ValueError('Недопустимый путь файла')
    if any(x.casefold() in EXCLUDED|SECRET_NAMES for x in p.parts) or p.name.casefold().startswith('.env') or p.suffix.casefold() in SECRET_SUFFIXES:
        raise ValueError('Путь исключён из релиза (служебные данные или секреты)')
    return p

def _hash(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def _inventory(root:Path):
    result={}
    for base,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[d for d in dirs if d not in EXCLUDED and not (Path(base)/d).is_symlink()]
        for name in files:
            path=Path(base)/name
            try:
                rel=path.relative_to(root).as_posix(); safe=_safe_rel(rel)
                if path.name in ARTIFACT_NAMES or any(unicodedata.category(ch) in {'Cc','Cf','Co'} for ch in path.name):
                    continue
            except ValueError: continue
            if path.is_symlink() or not path.is_file(): continue
            try:
                size=path.stat().st_size
                if size>MAX_FILE: continue
                result[rel]={'sha256':_hash(path),'size':size}
            except OSError: continue
            if len(result)>=MAX_FILES: raise ValueError('Слишком много файлов для сравнения (лимит 2000)')
    return result

class ReleaseManager:
    def __init__(self, source, target):
        self.source=Path(source).expanduser().resolve(); self.target=Path(target).expanduser().resolve()
        if not self.source.is_dir() or not self.target.is_dir(): raise ValueError('Обе папки проектов должны существовать')
        if self.source==self.target or self.source in self.target.parents or self.target in self.source.parents: raise ValueError('Папки проектов должны быть раздельными и не вложенными друг в друга')
    def compare(self):
        src=_inventory(self.source); dst=_inventory(self.target); rows=[]
        for rel in sorted(set(src)|set(dst)):
            a=src.get(rel); b=dst.get(rel)
            if a and not b: kind='added'
            elif b and not a: kind='deleted'
            elif a['sha256']!=b['sha256']: kind='modified'
            else: continue
            rows.append({'path':rel,'change':kind,'source_size':a['size'] if a else None,'target_size':b['size'] if b else None,'safe':True})
        return {'source':str(self.source),'target':str(self.target),'counts':{k:sum(x['change']==k for x in rows) for k in ('added','modified','deleted')},'files':rows[:MAX_FILES]}
    def prepare(self, selected:list[str]):
        if not selected or len(selected)>500: raise ValueError('Выбери от 1 до 500 файлов')
        comp=self.compare(); by={x['path']:x for x in comp['files']}; clean=[]
        for raw in selected:
            p=_safe_rel(raw); rel=p.as_posix()
            if rel not in by: raise ValueError(f'Файл больше не отличается или не найден: {rel}')
            clean.append(rel)
        if len(set(clean)) != len(clean): raise ValueError('Один и тот же файл выбран несколько раз')
        plan_id=uuid.uuid4().hex
        state={'id':plan_id,'created_at':datetime.now(timezone.utc).isoformat(),'source':str(self.source),'target':str(self.target),'files':[]}
        for rel in clean:
            p=Path(rel)
            s=_safe_join(self.source,p); t=_safe_join(self.target,p)
            state['files'].append({'path':rel,'change':by[rel]['change'],'source_hash':_hash(s) if s.is_file() else None,'target_hash':_hash(t) if t.is_file() else None})
        folder=self.target/'.workbench'/'release-plans'; folder.mkdir(parents=True,exist_ok=True)
        (folder/f'{plan_id}.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
        return {'ok':True,'plan_id':plan_id,'files':state['files'],'message':'План подготовлен. Целевой проект не изменён.'}
    def apply(self, plan_id:str):
        if not plan_id or not all(c in '0123456789abcdef' for c in plan_id) or len(plan_id)!=32: raise ValueError('Некорректный идентификатор плана')
        folder=self.target/'.workbench'/'release-plans'; planfile=folder/f'{plan_id}.json'
        if not planfile.is_file(): raise ValueError('План не найден или уже применён')
        state=json.loads(planfile.read_text(encoding='utf-8'))
        if Path(state['source']).resolve()!=self.source or Path(state['target']).resolve()!=self.target: raise ValueError('План относится к другим папкам')
        # Full preflight before writing anything.
        for item in state['files']:
            rel=_safe_rel(item['path']); s=_safe_join(self.source,rel); t=_safe_join(self.target,rel)
            sh=_hash(s) if s.is_file() and not s.is_symlink() else None
            th=_hash(t) if t.is_file() and not t.is_symlink() else None
            if sh!=item['source_hash'] or th!=item['target_hash']: raise ValueError(f'Файл изменился после подготовки. Сравни заново: {rel}')
        backup=folder/'backups'/plan_id; backup.mkdir(parents=True,exist_ok=False)
        applied=[]
        try:
            for item in state['files']:
                rel=_safe_rel(item['path']); s=_safe_join(self.source,rel); t=_safe_join(self.target,rel)
                applied.append(rel)
                if t.exists() and not t.is_file(): raise ValueError(f'Целевой путь не является обычным файлом: {rel}')
                if t.exists():
                    b=backup/rel; b.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(t,b)
                if item['change']=='deleted':
                    if t.exists(): t.unlink()
                else:
                    t.parent.mkdir(parents=True,exist_ok=True)
                    tmp=t.with_name(t.name+'.workbench-release-tmp')
                    shutil.copy2(s,tmp); os.replace(tmp,t)
        except Exception:
            for rel in reversed(applied):
                t=_safe_join(self.target,Path(rel)); b=backup/rel
                tmp=t.with_name(t.name+'.workbench-release-tmp')
                if tmp.exists(): tmp.unlink()
                if b.exists(): t.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(b,t)
                elif t.exists(): t.unlink()
            raise
        state['applied_at']=datetime.now(timezone.utc).isoformat(); state['backup']=str(backup)
        planfile.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
        return {'ok':True,'applied':applied,'backup':str(backup),'message':'Выбранные файлы перенесены. Резервная копия сохранена.'}
