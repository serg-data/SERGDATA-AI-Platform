import subprocess
import os
from pathlib import Path
from .security import is_sensitive_path

class ProjectTools:
    def __init__(self,root:Path):
        self.root=Path(root).expanduser().resolve()
        if not self.root.is_dir(): raise ValueError(f'Корень проекта не существует или не является каталогом: {self.root}')
    def safe(self,rel):
        raw=Path(str(rel or '.'))
        p=(self.root/raw).resolve()
        if p!=self.root and self.root not in p.parents: raise ValueError('Запрещён выход за пределы папки проекта')
        try:
            relative = p.relative_to(self.root)
        except ValueError:
            raise ValueError('Запрещён выход за пределы папки проекта')
        if is_sensitive_path(relative):
            raise ValueError('Доступ к потенциально секретному файлу запрещён')
        return p
    def listing(self,path='.',max_depth=5,include_backups=False,limit=500):
        p=self.safe(path)
        if not p.is_dir(): return 'Каталог не найден'
        max_depth=max(1,min(int(max_depth or 5),8)); limit=max(20,min(int(limit or 500),1500))
        skip={'.git','.venv','venv','node_modules','__pycache__','dist','build','.workbench','.ssh','.aws','.azure','.gnupg','secrets','credentials'}
        backup_suffixes=('.workbench.bak','.workbench.tmp','.bak','.tmp')
        rows=[]; files_count=dirs_count=0
        for current, dirs, files in os.walk(p,topdown=True,followlinks=False):
            cur=Path(current)
            depth=len(cur.relative_to(p).parts)
            dirs[:]=sorted([d for d in dirs if d not in skip and not is_sensitive_path((cur/d).relative_to(self.root)) and not (cur/d).is_symlink() and (include_backups or not d.endswith(backup_suffixes))],key=str.lower)
            if depth>=max_depth: dirs[:]=[]
            rel_dir=cur.relative_to(self.root).as_posix()
            if rel_dir=='.': rel_dir='.'
            for d in dirs:
                dirs_count+=1
                rows.append(f'DIR  {((cur/d).relative_to(self.root)).as_posix()}/')
            for name in sorted(files,key=str.lower):
                if is_sensitive_path(name): continue
                if not include_backups and name.endswith(backup_suffixes): continue
                f=cur/name
                if f.is_symlink(): continue
                try: f.resolve().relative_to(self.root)
                except ValueError: continue
                files_count+=1; rows.append(f'FILE {f.relative_to(self.root).as_posix()}')
                if len(rows)>=limit: break
            if len(rows)>=limit: break
        header=f'Корень проекта: {self.root}\nКаталог: {p.relative_to(self.root) if p!=self.root else "."}\nГлубина: {max_depth}\nКаталогов: {dirs_count}; файлов: {files_count}\n'
        if not rows: return header+'Файлы и каталоги не найдены.'
        suffix='\n[Достигнут лимит вывода; список может быть неполным.]' if len(rows)>=limit else ''
        return header+'\n'.join(rows)+suffix
    def read(self, path, start_line=1, end_line=0):
        """Read a bounded, explicitly numbered chunk and report how to continue.

        The result is deliberately kept below Agent's tool-result compaction
        threshold so a large file cannot be silently cut in the chat loop.
        """
        p = self.safe(path)
        if not p.is_file():
            return 'Файл не найден'
        size = p.stat().st_size
        if size > 2_000_000:
            raise ValueError('Файл больше 2 МБ; чтение через инструмент запрещено')
        lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
        total = len(lines)
        start = max(1, int(start_line or 1))
        requested_end = int(end_line or 0)
        if requested_end and requested_end < start:
            raise ValueError('end_line не может быть меньше start_line')
        if start > total + 1:
            raise ValueError(f'Начальная строка {start} находится за концом файла ({total} строк).')
        # Limit both lines and characters. Agent's outer loop truncates tool
        # results above 7,000 chars; keep this response comfortably below it.
        max_lines = 180
        target_end = min(total, requested_end if requested_end > 0 else start + max_lines - 1,
                         start + max_lines - 1)
        header = f'Файл: {p.relative_to(self.root).as_posix()} | Всего строк: {total} | Размер: {size} байт\n'
        output = []
        used = len(header)
        actual_end = start - 1
        char_limit = 5200
        for number in range(start, target_end + 1):
            row = f'{number}: {lines[number - 1]}'
            if used + len(row) + 1 > char_limit:
                if not output:
                    raise ValueError(f'Строка {number} слишком длинная для безопасного чтения одним фрагментом ({len(row)} символов).')
                break
            output.append(row)
            used += len(row) + 1
            actual_end = number
        if actual_end >= total:
            footer = f'\nСТАТУС ЧТЕНИЯ: COMPLETE. Получены все строки 1–{total}.' if start == 1 else f'\nСТАТУС ФРАГМЕНТА: END_OF_FILE. Получены строки {start}–{actual_end} из {total}.'
        else:
            footer = (f'\nСТАТУС ЧТЕНИЯ: INCOMPLETE. Получены строки {start}–{actual_end} из {total}. '
                      f'NEXT_START_LINE={actual_end + 1}. Вызови read_project_file с path="{p.relative_to(self.root).as_posix()}" '
                      f'и start_line={actual_end + 1}; продолжай до END_OF_FILE. Не называй файл прочитанным полностью.')
        return header + '\n'.join(output) + footer
    def write(self,path,content):
        p=self.safe(path); p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists(): p.with_name(p.name+'.workbench.bak').write_bytes(p.read_bytes())
        tmp=p.with_name(p.name+'.workbench.tmp')
        tmp.write_text(content,encoding='utf-8',newline='\n'); tmp.replace(p); return f'Записан {p.relative_to(self.root)}'
    def check(self,command):
        cmds={'pytest':['python','-m','pytest','-q'],'ruff':['python','-m','ruff','check','.'],'compile':['python','-m','compileall','-q','.']}
        if command not in cmds: return 'Разрешены pytest, ruff, compile'
        r=subprocess.run(cmds[command],cwd=self.root,capture_output=True,text=True,timeout=180)
        return f'exit_code={r.returncode}\n{(r.stdout+r.stderr)[-12000:]}'
