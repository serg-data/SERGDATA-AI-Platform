import os, subprocess, sys, tempfile, json, shutil
from pathlib import Path
SRC=Path(__file__).parent/ 'ai'
T=Path(tempfile.mkdtemp(prefix='kb-git-incremental-'))
base=T/'AI-Knowledge'; (base/'code').mkdir(parents=True); (base/'index').mkdir()
shutil.copy(SRC/'kb.py',base/'kb.py'); shutil.copy(SRC/'document_readers.py',base/'document_readers.py'); shutil.copy(SRC/'git_incremental.py',base/'git_incremental.py')

def git(cwd,*a):
 p=subprocess.run(['git','-C',str(cwd),*a],capture_output=True,text=True)
 if p.returncode: raise RuntimeError((a,p.stderr))
 return p.stdout.strip()
origin=T/'origin.git'; subprocess.run(['git','init','--bare',str(origin)],check=True,capture_output=True)
seed=T/'seed'; seed.mkdir(); git(seed,'init','-b','main'); git(seed,'config','user.email','test@example.com'); git(seed,'config','user.name','Test')
(seed/'a.md').write_text('alpha original\n'); git(seed,'add','.'); git(seed,'commit','-m','initial'); git(seed,'remote','add','origin',str(origin)); git(seed,'push','-u','origin','main')
repo=base/'code'/'demo'; subprocess.run(['git','clone','-b','main',str(origin),str(repo)],check=True,capture_output=True); git(repo,'config','user.email','test@example.com'); git(repo,'config','user.name','Test')
# remote add/update and deletion
(seed/'a.md').write_text('alpha updated\n'); (seed/'b.md').write_text('bravo added\n'); git(seed,'add','-A'); git(seed,'commit','-m','remote update'); git(seed,'push')
manifest=base/'index'/'pending-git-changes.json'
def sync():
 p=subprocess.run([sys.executable,str(base/'git_incremental.py'),'--base',str(base),'--name','demo','--url',str(origin),'--manifest',str(manifest)],capture_output=True,text=True)
 if p.returncode: raise AssertionError(p.stdout+p.stderr)
 print(p.stdout.strip())
sync(); data=json.loads(manifest.read_text()); assert 'code/demo/a.md' in data['paths'] and 'code/demo/b.md' in data['paths']
# index exact paths; assert 2 files
p=subprocess.run([sys.executable,str(base/'kb.py'),'index','--no-release-sync','--paths-file',str(manifest)],capture_output=True,text=True)
print(p.stdout,p.stderr); assert p.returncode==0
import sqlite3
con=sqlite3.connect(base/'index'/'knowledge.db'); rows=con.execute('select path,content from files order by path').fetchall(); assert len(rows)==2 and 'updated' in rows[0][1]; con.close()
manifest.unlink()
# second update deletes a.md and changes b.md
(seed/'a.md').unlink(); (seed/'b.md').write_text('bravo revised\n'); git(seed,'add','-A'); git(seed,'commit','-m','delete and change'); git(seed,'push')
sync(); data=json.loads(manifest.read_text()); assert 'code/demo/a.md' in data['deleted'] and 'code/demo/b.md' in data['paths']
p=subprocess.run([sys.executable,str(base/'kb.py'),'index','--no-release-sync','--paths-file',str(manifest)],capture_output=True,text=True); print(p.stdout,p.stderr); assert p.returncode==0
con=sqlite3.connect(base/'index'/'knowledge.db'); rows=con.execute('select path,content from files').fetchall(); assert len(rows)==1 and rows[0][0]=='code/demo/b.md' and 'revised' in rows[0][1]; con.close()
print('PASS: fetch-only update, exact changed paths, add/change/delete indexing, FTS DB updated. Test root:',T)
# Verify diverged-but-patch-equivalent local commit sync is safe and keeps backup ref.
# Reinitialize a second repository with equivalent change committed independently.
origin2=T/'origin2.git'; subprocess.run(['git','init','--bare',str(origin2)],check=True,capture_output=True)
repo2=base/'code'/'equiv'; repo2.mkdir(); git(repo2,'init','-b','main'); git(repo2,'config','user.email','test@example.com'); git(repo2,'config','user.name','Test')
(repo2/'x.md').write_text('base\n'); git(repo2,'add','.'); git(repo2,'commit','-m','base'); git(repo2,'remote','add','origin',str(origin2)); git(repo2,'push','-u','origin','main')
# local commit changes x; remember its patch
(repo2/'x.md').write_text('same patch\n'); git(repo2,'commit','-am','same patch')
# remote independently creates same patch from base
remote_work=T/'remote-equiv'; subprocess.run(['git','clone','-b','main',str(origin2),str(remote_work)],check=True,capture_output=True); git(remote_work,'config','user.email','test@example.com'); git(remote_work,'config','user.name','Test')
(remote_work/'x.md').write_text('same patch\n'); git(remote_work,'commit','-am','same patch remote'); git(remote_work,'push')
# manifest path same, use helper for repo equiv
p=subprocess.run([sys.executable,str(base/'git_incremental.py'),'--base',str(base),'--name','equiv','--url',str(origin2),'--manifest',str(manifest)],capture_output=True,text=True)
print(p.stdout,p.stderr); assert p.returncode==0
assert git(repo2,'rev-parse','HEAD')==git(repo2,'rev-parse','origin/main')
refs=git(repo2,'for-each-ref','--format=%(refname)','refs/backup/ai-knowledge/equiv'); assert refs
print('PASS: patch-equivalent diverged branch synchronized with preserved backup ref')
# Verify a clean divergent merge preserves both local and remote commits.
origin3=T/'origin3.git'; subprocess.run(['git','init','--bare',str(origin3)],check=True,capture_output=True)
seed3=T/'seed3'; seed3.mkdir(); git(seed3,'init','-b','main'); git(seed3,'config','user.email','test@example.com'); git(seed3,'config','user.name','Test')
(seed3/'base.md').write_text('base\n'); git(seed3,'add','.'); git(seed3,'commit','-m','base'); git(seed3,'remote','add','origin',str(origin3)); git(seed3,'push','-u','origin','main')
repo3=base/'code'/'mergeok'; subprocess.run(['git','clone','-b','main',str(origin3),str(repo3)],check=True,capture_output=True); git(repo3,'config','user.email','test@example.com'); git(repo3,'config','user.name','Test')
(repo3/'local.md').write_text('local only\n'); git(repo3,'add','.'); git(repo3,'commit','-m','local unique')
remote3=T/'remote3'; subprocess.run(['git','clone','-b','main',str(origin3),str(remote3)],check=True,capture_output=True); git(remote3,'config','user.email','test@example.com'); git(remote3,'config','user.name','Test')
(remote3/'remote.md').write_text('remote only\n'); git(remote3,'add','.'); git(remote3,'commit','-m','remote unique'); git(remote3,'push')
p=subprocess.run([sys.executable,str(base/'git_incremental.py'),'--base',str(base),'--name','mergeok','--url',str(origin3),'--manifest',str(manifest)],capture_output=True,text=True)
print(p.stdout,p.stderr); assert p.returncode==0
assert (repo3/'local.md').exists() and (repo3/'remote.md').exists()
assert int(git(repo3,'rev-list','--count','HEAD'))==4
print('PASS: non-conflicting divergent local+remote histories merged without losing either side')
# No-change fetch must not create an index manifest; dirty working tree must not be touched.
manifest.unlink(missing_ok=True)
p=subprocess.run([sys.executable,str(base/'git_incremental.py'),'--base',str(base),'--name','demo','--url',str(origin),'--manifest',str(manifest)],capture_output=True,text=True)
assert p.returncode==0 and not manifest.exists(), (p.stdout,p.stderr)
(repo/'local-untracked.txt').write_text('keep me')
head_before=git(repo,'rev-parse','HEAD')
p=subprocess.run([sys.executable,str(base/'git_incremental.py'),'--base',str(base),'--name','demo','--url',str(origin),'--manifest',str(manifest)],capture_output=True,text=True)
assert p.returncode!=0 and git(repo,'rev-parse','HEAD')==head_before and (repo/'local-untracked.txt').read_text()=='keep me'
print('PASS: no-change run avoids index manifest; dirty worktree is preserved and skipped')
# Conflicting divergent history must be left untouched.
origin4=T/'origin4.git'; subprocess.run(['git','init','--bare',str(origin4)],check=True,capture_output=True)
seed4=T/'seed4'; seed4.mkdir(); git(seed4,'init','-b','main'); git(seed4,'config','user.email','test@example.com'); git(seed4,'config','user.name','Test'); (seed4/'conflict.md').write_text('base\n'); git(seed4,'add','.'); git(seed4,'commit','-m','base'); git(seed4,'remote','add','origin',str(origin4)); git(seed4,'push','-u','origin','main')
repo4=base/'code'/'conflict'; subprocess.run(['git','clone','-b','main',str(origin4),str(repo4)],check=True,capture_output=True); git(repo4,'config','user.email','test@example.com'); git(repo4,'config','user.name','Test'); (repo4/'conflict.md').write_text('local\n'); git(repo4,'commit','-am','local')
remote4=T/'remote4'; subprocess.run(['git','clone','-b','main',str(origin4),str(remote4)],check=True,capture_output=True); git(remote4,'config','user.email','test@example.com'); git(remote4,'config','user.name','Test'); (remote4/'conflict.md').write_text('remote\n'); git(remote4,'commit','-am','remote'); git(remote4,'push')
head4=git(repo4,'rev-parse','HEAD'); p=subprocess.run([sys.executable,str(base/'git_incremental.py'),'--base',str(base),'--name','conflict','--url',str(origin4),'--manifest',str(manifest)],capture_output=True,text=True); assert p.returncode!=0 and git(repo4,'rev-parse','HEAD')==head4 and (repo4/'conflict.md').read_text()=='local\n'
print('PASS: merge conflict detected before changing local HEAD/worktree')
