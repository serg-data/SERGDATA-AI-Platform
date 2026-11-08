"""Background process registry with bounded output and cooperative termination."""
from __future__ import annotations
import subprocess, threading, time, uuid, os
from pathlib import Path

class CancellationToken:
    """Thread-safe cancellation signal with callbacks for blocking resources."""
    def __init__(self):
        self._event = threading.Event()
        self._lock = threading.RLock()
        self._callbacks = []

    def is_set(self):
        return self._event.is_set()

    def register(self, callback):
        if not callable(callback):
            return
        with self._lock:
            if self._event.is_set():
                call_now = True
            else:
                self._callbacks.append(callback)
                call_now = False
        if call_now:
            try:
                callback()
            except Exception:
                pass

    def set(self):
        self._event.set()
        with self._lock:
            callbacks, self._callbacks = self._callbacks, []
        for callback in callbacks:
            try:
                callback()
            except Exception:
                pass


class ProcessRegistry:
    MAX_RETAINED_TERMINAL_JOBS = 100

    def __init__(self):
        self.lock=threading.RLock(); self.jobs={}

    def _prune_locked(self):
        """Bound completed-job memory without ever evicting a running process."""
        terminal = sorted(
            ((float(job.get('started_at') or 0), jid)
             for jid, job in self.jobs.items()
             if job.get('status') in ('completed', 'failed', 'stopped')),
            key=lambda item: (item[0], item[1]),
        )
        excess = len(terminal) - self.MAX_RETAINED_TERMINAL_JOBS
        for _started, jid in terminal[:max(0, excess)]:
            self.jobs.pop(jid, None)
    def start(self, command, cwd:Path, timeout=180, shell=False, on_complete=None, execution_id=None):
        jid=uuid.uuid4().hex[:12]
        job={'id':jid,'status':'starting','command':command if isinstance(command,str) else ' '.join(command),'cwd':str(cwd),'stdout':'','stderr':'','exit_code':None,'started_at':time.time(),'finished_at':None,'truncated':False,'proc':None,'stop':False,'thread':None,'on_complete':on_complete,'notified':False,'execution_id':execution_id}
        with self.lock:
            self.jobs[jid]=job
            self._prune_locked()
        thread=threading.Thread(target=self._worker,args=(jid,command,Path(cwd),timeout,shell),daemon=True)
        with self.lock:self.jobs[jid]['thread']=thread
        thread.start()
        return jid

    def start_callable(self, func, args, cwd: Path, timeout=180, display='SSH profile command', on_complete=None, execution_id=None):
        jid = uuid.uuid4().hex[:12]
        cancel_event = CancellationToken()
        job = {'id': jid, 'status': 'starting', 'command': display, 'cwd': str(cwd),
               'stdout': '', 'stderr': '', 'exit_code': None, 'started_at': time.time(),
               'finished_at': None, 'truncated': False, 'proc': None, 'stop': False,
               'cancel_event': cancel_event, 'thread': None, 'on_complete':on_complete, 'notified':False, 'execution_id':execution_id}
        with self.lock:
            self.jobs[jid] = job
            self._prune_locked()
        thread=threading.Thread(target=self._callable_worker, args=(jid, func, args, timeout), daemon=True)
        with self.lock:self.jobs[jid]['thread']=thread
        thread.start()
        return jid

    def _callable_worker(self, jid, func, args, timeout):
        with self.lock:
            if jid not in self.jobs:
                return
            self.jobs[jid]['status'] = 'running'
            cancel_event = self.jobs[jid]['cancel_event']
        try:
            result = func(*args, timeout=timeout, cancel_event=cancel_event)
            stdout = str(result.get('stdout') or '')
            stderr = str(result.get('stderr') or '')
            with self.lock:
                job = self.jobs[jid]
                job['stdout'] = stdout[-50000:]
                job['stderr'] = stderr[-50000:]
                job['truncated'] = len(stdout) > 50000 or len(stderr) > 50000
                job['exit_code'] = result.get('exit_code')
                if result.get('status') == 'timed_out':
                    job['status'] = 'failed'
                elif result.get('status') == 'stopped' or job['stop']:
                    job['status'] = 'stopped'
                else:
                    job['status'] = 'completed' if result.get('exit_code') == 0 else 'failed'
                job['finished_at'] = time.time()
            self._notify(jid)
        except Exception as exc:
            with self.lock:
                job = self.jobs[jid]
                job['status'] = 'failed'
                job['stderr'] = f'{type(exc).__name__}: {exc}'
                job['finished_at'] = time.time()
            self._notify(jid)

    def _notify(self,jid):
        with self.lock:
            job=self.jobs.get(jid)
            if not job or job.get('notified'):
                return
            job['notified']=True
            callback=job.get('on_complete')
            snapshot={k:v for k,v in job.items() if k not in ('proc','stop','cancel_event','thread','on_complete','notified')}
        if callback:
            try: callback(snapshot)
            except Exception: pass

    def _append(self,jid,key,data):
        with self.lock:
            j=self.jobs.get(jid)
            if not j:return
            s=j[key]+data
            if len(s)>50000:j[key]=s[-50000:];j['truncated']=True
            else:j[key]=s
    def _worker(self,jid,command,cwd,timeout,shell):
        try:
            p=subprocess.Popen(command,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.DEVNULL,text=True,encoding='utf-8',errors='replace',shell=shell,bufsize=1,creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0),start_new_session=(os.name!='nt'))
            with self.lock:
                self.jobs[jid]['proc']=p;self.jobs[jid]['status']='running'
                stop_requested=self.jobs[jid]['stop']
            def reader(pipe,key):
                # Preserve live progress emitted with either newline or carriage
                # return (common for CLI progress bars); cap each append chunk.
                chunk=[]
                try:
                    while True:
                        char=pipe.read(1)
                        if char=='':
                            break
                        if char in ('\r','\n'):
                            if chunk:
                                self._append(jid,key,''.join(chunk)+'\n')
                                chunk=[]
                        else:
                            chunk.append(char)
                            if len(chunk)>=160:
                                self._append(jid,key,''.join(chunk))
                                chunk=[]
                    if chunk:
                        self._append(jid,key,''.join(chunk))
                finally:
                    pipe.close()
            a=threading.Thread(target=reader,args=(p.stdout,'stdout'),daemon=True);b=threading.Thread(target=reader,args=(p.stderr,'stderr'),daemon=True);a.start();b.start()
            # If cancellation arrived before Popen was attached to the job,
            # stop through the same process-tree-aware path now that it exists.
            if stop_requested:
                self.stop(jid)
            try: code=p.wait(timeout=max(1,min(int(timeout),900)))
            except subprocess.TimeoutExpired:
                p.kill();code=p.wait();self._append(jid,'stderr','\n[Workbench: превышено время выполнения]\n')
            a.join(2);b.join(2)
            with self.lock:
                j=self.jobs[jid];j['exit_code']=code;j['status']='stopped' if j['stop'] else ('completed' if code==0 else 'failed');j['finished_at']=time.time();j['proc']=None
            self._notify(jid)
        except Exception as e:
            with self.lock:
                j=self.jobs[jid];j['status']='failed';j['stderr']+=f'{type(e).__name__}: {e}';j['finished_at']=time.time()
            self._notify(jid)
    def get(self,jid):
        with self.lock:
            j=self.jobs.get(jid)
            if not j:return None
            return {k:v for k,v in j.items() if k not in ('proc','stop','cancel_event','thread','on_complete','notified')}
    def stop(self,jid):
        with self.lock:
            j=self.jobs.get(jid)
            if not j or j.get('status') in ('completed','failed','stopped'):
                return False
            p=j.get('proc')
            j['stop']=True
            cancel_event=j.get('cancel_event')
        # Callable SSH jobs can register their active Paramiko client/channel here.
        if cancel_event is not None:
            cancel_event.set()
        if p and p.poll() is None:
            if os.name == 'nt':
                try:
                    result=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,text=True,
                                          timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),check=False)
                except Exception:
                    result=None
                try: p.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    try: p.kill()
                    except Exception: pass
                    try: p.wait(timeout=2)
                    except subprocess.TimeoutExpired: return False
                if p.poll() is None:return False
            else:
                try: os.killpg(os.getpgid(p.pid),15)
                except Exception:
                    try:p.terminate()
                    except Exception:pass
                try:p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:os.killpg(os.getpgid(p.pid),9)
                    except Exception:
                        try:p.kill()
                        except Exception:pass
                    try:p.wait(timeout=2)
                    except subprocess.TimeoutExpired:return False
        # A callable SSH worker may still be unwinding a blocked connect/read after
        # its cancellation callbacks closed the transport. Join briefly and report
        # active=true to the UI rather than pretending the stop completed.
        with self.lock:
            thread=self.jobs.get(jid,{}).get('thread')
        if thread and thread is not threading.current_thread():thread.join(timeout=5)
        with self.lock:
            current=self.jobs.get(jid)
            return bool(current and current.get('status') in ('completed','failed','stopped'))

    def stop_all(self, join_timeout=25):
        with self.lock:
            active=[jid for jid,job in self.jobs.items() if job.get('status') not in ('completed','failed','stopped')]
            threads=[job.get('thread') for job in self.jobs.values() if job.get('thread')]
        for jid in active:
            self.stop(jid)
        deadline=time.monotonic()+max(0.0,float(join_timeout))
        for thread in threads:
            if thread and thread is not threading.current_thread():
                thread.join(max(0.0,deadline-time.monotonic()))
        return len(active)

processes=ProcessRegistry()
