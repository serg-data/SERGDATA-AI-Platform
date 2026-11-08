const $=id=>document.getElementById(id);
// Diagnostic marker: verify the browser has loaded the DOM-token highlighter.
window.SERGDATA_CODE_RENDER_VERSION='20261106-dom-tokens-v1';
const rawCodeSources=new WeakMap();
let releaseCompareRows=[], releasePlanId=null, openedProjectFile='', openedProjectFileContent='', fileViewerFontSize=12, messagesLoadSeq=0;
let activeProject=null, activeTask=null, activeBranch=null, busy=false, activeChatBranch=null, previewTimer=null, selectedAttachments=[], baseContextEstimate=0, credentialPersistenceAvailable=false, chatBusySince=0, chatElapsedTimer=null, waitingForUserInput=false, waitingForApproval=false, chatPollTimer=null, chatPollBusy=false, statsPollBusy=false, statsPollLastAt=0, statsRequestSeq=0, executionQueuePollTimer=null, executionQueuePollBusy=false, executionQueueLastKnown=null, chatActivity={stage:'idle',detail:''};
async function api(url,opts={}){
 const headers={...(opts.headers||{})};
 if(!(opts.body instanceof FormData))headers['Content-Type']=headers['Content-Type']||'application/json';
 const r=await fetch(url,{...opts,headers});
 const contentType=(r.headers.get('content-type')||'').toLowerCase();
 let d;
 if(contentType.includes('application/json')) d=await r.json().catch(()=>({}));
 else d=await r.text();
 if(!r.ok){
  const message=typeof d==='string'?d:(d?.detail||d?.message||r.statusText);
  throw new Error(message||`HTTP ${r.status}`);
 }
 return d;
}
function toast(s){$('toast').textContent=s;$('toast').classList.add('show');setTimeout(()=>$('toast').classList.remove('show'),3200)}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function init(){
 try{
  const s=await api('/api/status');
  credentialPersistenceAvailable=!!s.credential_persistence_available;
  $('modelName').textContent=s.models?.[0]||s.configured_model;
  $('lmStatus').textContent='LM Studio: '+(s.models?.[0]?.startsWith('Ошибка')?'ошибка':'доступна');
  $('lmDot').className=s.models?.[0]?.startsWith('Ошибка')?'':'ok';
  $('kbStatus').textContent='Knowledge: '+s.kb;$('kbDot').className=s.kb.startsWith('Подключена')?'ok':'';
  $('projectSelect').innerHTML='<option value="">Загрузка проектов…</option>';
  const ps=await api('/api/projects');
  if(!Array.isArray(ps)||!ps.length){
   $('projectSelect').innerHTML='<option value="">Проекты не найдены</option>';
   $('projectName').textContent='Добавь проект кнопкой ＋';
   $('taskCount').textContent='0';$('tasks').innerHTML='';
   return;
  }
  $('projectSelect').innerHTML=ps.map(x=>`<option value="${x.id}" title="${esc(x.root)}">${esc(x.name)} · ${esc(x.root||'путь не задан')} · ${x.task_count||0}</option>`).join('');
  const saved=Number(localStorage.getItem('sergdata.activeProject')||s.project?.id||0);
  const selected=ps.find(x=>x.id===saved)||ps.find(x=>x.id===s.project?.id)||ps[0];
  await selectProject(selected.id);
 }catch(e){
  $('projectSelect').innerHTML='<option value="">Ошибка загрузки проектов</option>';
  $('projectName').textContent='Не удалось загрузить список';
  toast('Ошибка инициализации: '+e.message);
 }
}
async function selectProject(id){
 const ps=await api('/api/projects');activeProject=ps.find(x=>x.id===Number(id));if(!activeProject)return;
 localStorage.setItem('sergdata.activeProject',String(activeProject.id));
 $('projectSelect').value=activeProject.id;$('projectName').textContent=activeProject.root;$('projectRoot').textContent=activeProject.root;if($('agentWorkspaceRoot'))$('agentWorkspaceRoot').textContent=activeProject.root;
 if(executionQueuePollTimer){clearInterval(executionQueuePollTimer);executionQueuePollTimer=null;}activeTask=null;activeBranch=null;selectedAttachments=[];renderAttachmentChips();$('saveTaskMemory').disabled=true;$('chat').classList.add('hidden');$('welcome').classList.remove('hidden');
 $('taskTitle').textContent='Выберите задачу';$('branchTitle').textContent='Проект: '+activeProject.name;
 await loadTasks();await loadProjectMemory();await refreshFiles();await refreshGit();await loadReleaseTargets();
}
async function loadTaskMemory(){
 try{const m=await api(`/api/tasks/${activeTask.id}/memory`);$('taskMemoryInput').value=m.summary||''}
 catch(e){$('taskMemoryInput').value='';}
}
async function loadProjectMemory(){
 try{const m=await api(`/api/projects/${activeProject.id}/memory`);$('projectMemoryInput').value=m.summary||''}
 catch(e){toast('Не удалось загрузить память проекта: '+e.message)}
}
async function loadTasks(){
 const a=await api(`/api/tasks?project_id=${activeProject.id}`);$('taskCount').textContent=a.length;
 $('tasks').innerHTML=a.map(t=>`<div class="task-item ${activeTask?.id===t.id?'active':''}" data-id="${t.id}"><span>▤</span><span class="task-text">${esc(t.title)}</span></div>`).join('');
 document.querySelectorAll('.task-item').forEach(el=>el.onclick=()=>selectTask(Number(el.dataset.id)));
}
async function newProject(){
 const dialog=document.getElementById('projectDialog');if(!dialog)return;
 document.getElementById('projectNewName').value='Новый проект';
 document.getElementById('projectNewRoot').value='';dialog.showModal();
}
(()=>{
 const dialog=document.getElementById('projectDialog');if(!dialog)return;
 document.getElementById('projectBrowse').addEventListener('click',async()=>{
  try{const r=await fetch('/api/local-dialog',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:'folder',title:'Выберите папку проекта'})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Не удалось открыть диалог');if(d.path)document.getElementById('projectNewRoot').value=d.path;}catch(e){toast(e.message)}
 });
 document.getElementById('projectCancel').addEventListener('click',()=>dialog.close());
 document.getElementById('projectForm').addEventListener('submit',async e=>{
  e.preventDefault();const name=document.getElementById('projectNewName').value.trim(),root=document.getElementById('projectNewRoot').value.trim();
  if(!name||!root){toast('Укажи название и выбери папку проекта');return;}
  const b=document.getElementById('projectCreate');b.disabled=true;
  try{const x=await api('/api/projects',{method:'POST',body:JSON.stringify({name,root})});dialog.close();toast('Проект добавлен или восстановлен');await reloadProjects(x.id)}catch(err){toast(err.message)}finally{b.disabled=false;}
 });
})();

async function reloadProjects(selectId){
 const ps=await api('/api/projects');
 if(!ps.length){$('projectSelect').innerHTML='<option value="">Проекты не найдены</option>';activeProject=null;$('projectName').textContent='Добавь проект кнопкой ＋';$('taskCount').textContent='0';$('tasks').innerHTML='';$('taskTitle').textContent='Выберите задачу';$('branchTitle').textContent='Создайте задачу, чтобы начать';$('chat').classList.add('hidden');$('welcome').classList.remove('hidden');return}
 $('projectSelect').innerHTML=ps.map(x=>`<option value="${x.id}" title="${esc(x.root)}">${esc(x.name)} · ${esc(x.root||'путь не задан')} · ${x.task_count||0}</option>`).join('');
 const target=ps.find(x=>x.id===Number(selectId))||ps.find(x=>x.id===activeProject?.id)||ps[0];
 await selectProject(target.id);
}
async function newTask(){
 if(!activeProject){toast('Сначала выбери проект');return}
 let name=prompt('Название задачи:','Новая задача');if(!name?.trim())return;
 let x=await api('/api/tasks',{method:'POST',body:JSON.stringify({name:name.trim(),project_id:activeProject.id})});
 await loadTasks();await selectTask(x.task_id,x.branch_id)
}
async function selectTask(id,branchId){
 activeTask=(await api(`/api/tasks?project_id=${activeProject.id}`)).find(t=>t.id===id);if(!activeTask)return;
 let bs=await api(`/api/tasks/${id}/branches`);activeBranch=branchId||bs[0]?.id;
 renderTop(bs);$('welcome').classList.add('hidden');$('chat').classList.remove('hidden');
 await loadMessages();await syncChatStatus(activeBranch);await loadStats();await loadProjectSettings();await loadPending();await loadExecutionQueue({loadAux:true});startExecutionQueuePolling();await loadTasks();await loadProjectMemory();await loadTaskMemory();await loadAttachments();selectedAttachments=[];renderAttachmentChips();
}
function renderTop(bs){
 $('saveTaskMemory').disabled=false;
 $('taskTitle').textContent=activeTask.title;$('branchTitle').textContent=`Проект: ${activeProject.name} · задача #${activeTask.id} · ${bs.length} веток`;
 $('branchSelect').innerHTML=bs.map(b=>`<option value="${b.id}" ${b.id===activeBranch?'selected':''}>${esc(b.name)}</option>`).join('');
 $('branchSelect').disabled=false;
 ['newBranch','renameBranch','deleteBranch','renameTask','deleteTask','checkpoint','exportCheckpoint','importCheckpoint','continueNewTask'].forEach(id=>$(id).disabled=false);
}
function inlineMd(s){
 let x=esc(s);
 x=x.replace(/`([^`]+)`/g,'<code class="inline-code">$1</code>');
 x=x.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
 x=x.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g,'<em>$1</em>');
 x=x.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
 return x;
}
function appendCodeToken(parent,text,className=''){
 if(!text)return;
 if(!className){parent.appendChild(document.createTextNode(text));return;}
 const span=document.createElement('span');
 span.className=className;
 span.textContent=text;
 parent.appendChild(span);
}
function highlightCodeFragment(code,lang){
 const language=String(lang||'').toLowerCase();
 const lines=String(code??'').replace(/\r\n?/g,'\n').split('\n');
 const keywordList=({
  json:['true','false','null'],
  sh:['if','then','else','elif','fi','for','while','do','done','case','esac','in','function','local','export','return','exit','readonly','set','unset'],
  bash:['if','then','else','elif','fi','for','while','do','done','case','esac','in','function','local','export','return','exit','readonly','set','unset'],
  shell:['if','then','else','elif','fi','for','while','do','done','case','esac','in','function','local','export','return','exit','readonly','set','unset'],
  py:['def','class','return','if','elif','else','for','while','in','import','from','as','try','except','finally','with','pass','raise','async','await','yield','lambda','True','False','None'],
  python:['def','class','return','if','elif','else','for','while','in','import','from','as','try','except','finally','with','pass','raise','async','await','yield','lambda','True','False','None'],
  js:['function','const','let','var','new','throw','try','catch','finally','return','if','else','for','while','class','extends','async','await','import','from','export','default','null','true','false','undefined'],
  javascript:['function','const','let','var','new','throw','try','catch','finally','return','if','else','for','while','class','extends','async','await','import','from','export','default','null','true','false','undefined'],
  ts:['function','const','let','var','new','throw','try','catch','finally','return','if','else','for','while','class','extends','async','await','import','from','export','default','null','true','false','undefined','interface','type','public','private'],
  typescript:['function','const','let','var','new','throw','try','catch','finally','return','if','else','for','while','class','extends','async','await','import','from','export','default','null','true','false','undefined','interface','type','public','private'],
  sql:['SELECT','FROM','WHERE','INSERT','UPDATE','DELETE','CREATE','TABLE','JOIN','ON','AND','OR','NOT','NULL','AS','INTO','VALUES','SET','GROUP','ORDER','BY','LIMIT'],
  powershell:['function','param','begin','process','end','if','else','elseif','foreach','for','while','switch','return','throw','try','catch','finally'],
  ps1:['function','param','begin','process','end','if','else','elseif','foreach','for','while','switch','return','throw','try','catch','finally']
 })[language]||[];
 const keywordSet=new Set(keywordList.map(x=>language==='sql'?x.toUpperCase():x));
 const hashComments=['sh','bash','shell','py','python','yaml','yml','toml','ini','powershell','ps1'].includes(language);
 const slashComments=['js','javascript','ts','typescript','java','c','cpp','go','rust'].includes(language);
 const dashComments=language==='sql';
 const fragment=document.createDocumentFragment();
 const emit=(text,cls='')=>appendCodeToken(fragment,text,cls);
 lines.forEach((line,lineIndex)=>{
  let i=0;
  while(i<line.length){
   const rest=line.slice(i);
   if((hashComments&&line[i]==='#')||(slashComments&&rest.startsWith('//'))||(dashComments&&rest.startsWith('--'))){
    emit(rest,'tok-comment');i=line.length;break;
   }
   const ch=line[i];
   if(ch==='"'||ch==="'"||ch==='`'){
    let j=i+1,closed=false;
    while(j<line.length){if(line[j]==='\\'){j+=2;continue;}if(line[j]===ch){j++;closed=true;break;}j++;}
    emit(line.slice(i,Math.min(j,line.length)),'tok-string');
    i=Math.min(j,line.length);
    if(language==='json'&&closed&&/^\s*:/.test(line.slice(i))){
     const ws=line.slice(i).match(/^\s*/)[0];emit(ws);i+=ws.length;
     if(line[i]===':'){emit(':','tok-punct');i++;}
    }
    continue;
   }
   const number=rest.match(/^(?:0[xX][\da-fA-F]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/);
   if(number){emit(number[0],'tok-number');i+=number[0].length;continue;}
   const ident=rest.match(/^[A-Za-z_$][\w$]*/);
   if(ident){
    const word=ident[0],key=language==='sql'?word.toUpperCase():word,next=line.slice(i+word.length);
    if(keywordSet.has(key))emit(word,'tok-keyword');
    else if(/^\s*\(/.test(next))emit(word,'tok-function');
    else emit(word);
    i+=word.length;continue;
   }
   emit(ch);i++;
  }
  if(lineIndex<lines.length-1)emit('\n');
 });
 return fragment;
}
function highlightCodeElement(codeElement,language){
 const source=codeElement.textContent||'';
 rawCodeSources.set(codeElement,source);
 codeElement.replaceChildren(highlightCodeFragment(source,language));
 codeElement.dataset.syntaxHighlighted='dom-v1';
}
function applyCodeHighlighting(root){
 root.querySelectorAll('code[data-code-language]').forEach(codeElement=>{
  if(codeElement.dataset.syntaxHighlighted==='dom-v1')return;
  highlightCodeElement(codeElement,codeElement.dataset.codeLanguage||'text');
 });
}
function renderMarkdown(src){
 const lines=String(src??'').replace(/\r\n?/g,'\n').split('\n');let out=[],para=[],list=null;
 const flush=()=>{if(para.length){out.push(`<p>${para.map(inlineMd).join('<br>')}</p>`);para=[]}};
 const closeList=()=>{if(list){out.push(`</${list}>`);list=null}};
 const isTableSep=line=>/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
 const cells=line=>{let s=line.trim().replace(/^\|/,'').replace(/\|$/,'');return s.split(/(?<!\\)\|/).map(v=>v.replace(/\\\|/g,'|').trim())};
 const renderTable=(header,rows,sep)=>{
  const hs=cells(header), aligns=cells(sep).map(v=>v.startsWith(':')&&v.endsWith(':')?'center':v.endsWith(':')?'right':'left');
  const count=Math.max(hs.length,aligns.length,1);
  const th=Array.from({length:count},(_,j)=>`<th style="text-align:${aligns[j]||'left'}">${inlineMd(hs[j]||'')}</th>`).join('');
  const body=rows.map(row=>{const cs=cells(row);return `<tr>${Array.from({length:count},(_,j)=>`<td style="text-align:${aligns[j]||'left'}">${inlineMd(cs[j]||'')}</td>`).join('')}</tr>`}).join('');
  return `<div class="md-table-wrap" role="region" aria-label="Таблица" tabindex="0"><table class="md-table"><thead><tr>${th}</tr></thead><tbody>${body}</tbody></table></div>`;
 };
 for(let i=0;i<lines.length;i++){
  const line=lines[i];
  const fence=line.match(/^\s*```([\w.+-]*)\s*$/);
  if(fence){flush();closeList();let code=[];i++;while(i<lines.length&&!/^\s*```\s*$/.test(lines[i]))code.push(lines[i++]);const lang=fence[1]||'text';out.push(`<div class="code-card"><div class="code-head"><span>${esc(lang.toUpperCase())}</span><button class="copy-code" type="button">Копировать</button></div><pre><code class="language-${esc(lang)}" data-code-language="${esc(lang)}">${esc(code.join('\n'))}</code></pre></div>`);continue}
  if(i+1<lines.length&&line.includes('|')&&isTableSep(lines[i+1])){flush();closeList();const head=line;const sep=lines[++i];const rows=[];while(i+1<lines.length&&lines[i+1].trim()&&lines[i+1].includes('|')&&!/^\s*```/.test(lines[i+1]))rows.push(lines[++i]);out.push(renderTable(head,rows,sep));continue}
  if(!line.trim()){flush();closeList();continue}
  const h=line.match(/^(#{1,6})\s+(.+)$/);if(h){flush();closeList();let n=Math.min(h[1].length+1,6);out.push(`<h${n}>${inlineMd(h[2])}</h${n}>`);continue}
  if(/^(\s*[-*+]|\s*\d+[.)])\s+/.test(line)){flush();const ordered=/^\s*\d+[.)]/.test(line);const tag=ordered?'ol':'ul';if(list!==tag){closeList();out.push(`<${tag}>`);list=tag}out.push(`<li>${inlineMd(line.replace(/^\s*(?:[-*+]|\d+[.)])\s+/,''))}</li>`);continue}
  const quote=line.match(/^\s*>\s?(.*)$/);if(quote){flush();closeList();out.push(`<blockquote>${inlineMd(quote[1])}</blockquote>`);continue}
  if(/^---+$/.test(line.trim())){flush();closeList();out.push('<hr>');continue}
  para.push(line);
 }
 flush();closeList();return out.join('');
}
function renderAssistant(text){
 let source=String(text??'');const blocks=[];
 source=source.replace(/<(think|analysis|reasoning)>([\s\S]*?)<\/\1>/gi,(_,tag,body)=>{blocks.push({type:'thought',tag:tag.toLowerCase(),body});return `\n@@THOUGHT_${blocks.length-1}@@\n`});
 const parts=source.split(/(@@THOUGHT_\d+@@)/g);
 return parts.map(part=>{
  const m=part.match(/^@@THOUGHT_(\d+)@@$/);if(m){const b=blocks[Number(m[1])];return `<details class="thought-block"><summary><span>✧</span> Рассуждения модели <span class="thought-hint">показать / скрыть</span></summary><div class="thought-content">${renderMarkdown(b.body)}</div></details>`}
  return renderMarkdown(part);
 }).join('');
}
function renderTool(content, metadata){
 const meta=metadata&&typeof metadata==='object'?metadata:{};
 const legacy=String(content??'');
 const name=meta.name||(legacy.includes(':\n')?legacy.slice(0,legacy.indexOf(':\n')):'Инструмент');
 const result=legacy.includes(':\n')&&!meta.name?legacy.slice(legacy.indexOf(':\n')+2):legacy;
 const args=meta.arguments&&typeof meta.arguments==='object'?meta.arguments:{};
 const status=meta.status||'legacy';
 const statusLabel=({completed:'Выполнено',error:'Ошибка',blocked:'Заблокировано',legacy:'Старый вызов'})[status]||status;
 const statusClass=({completed:'ok',error:'error',blocked:'blocked'})[status]||'legacy';
 const argsText=Object.keys(args).length?JSON.stringify(args,null,2):'Аргументы этого вызова в старой истории не сохранены.';
 const preview=String(meta.result_preview||result||'').replace(/\s+/g,' ').slice(0,220);
 const duration=Number.isFinite(Number(meta.duration_ms))?` · ${Number(meta.duration_ms)} мс`:'';
 return `<section class="tool-card"><div class="tool-card-head"><span class="tool-icon">⚙</span><strong>${esc(name)}</strong><span class="tool-status ${statusClass}">${esc(statusLabel)}${duration}</span></div><div class="tool-action">${esc(Object.keys(args).length?Object.entries(args).map(([k,v])=>`${k}: ${typeof v==='string'?v:JSON.stringify(v)}`).join(' · '):'Вызов инструмента')}</div><div class="tool-preview">${esc(preview||'Инструмент не вернул текстовый результат.')}</div><details class="tool-details"><summary>Аргументы и полный результат</summary><div class="tool-result"><b>Аргументы</b><pre>${esc(argsText)}</pre><b>Результат</b>${renderMarkdown(result)}</div></details></section>`;
}
async function loadMessages(){
  const branch=Number(activeBranch);
  if(!branch)return;
  const requestSeq=++messagesLoadSeq;
  const box=$('messages');
  const wasNearBottom=box.scrollHeight-box.scrollTop-box.clientHeight<90;
  const oldScrollTop=box.scrollTop;
  const ms=await api(`/api/branches/${branch}/messages`);
  // Ignore stale responses (for example, a slow poll completing after a newer
  // refresh or after the user switched branches).
  if(requestSeq!==messagesLoadSeq||Number(activeBranch)!==branch)return;
  box.innerHTML=ms.map(m=>{
   const role=m.role==='user'?'Вы':m.role==='assistant'?'Модель':'Инструмент';
   const body=m.role==='user'?`<p>${inlineMd(m.content)}</p>`:m.role==='tool'?renderTool(m.content,m.metadata):renderAssistant(m.content);
   const files=(m.attachments||[]).map(a=>`<a class="message-attachment" href="/api/attachments/${a.id}/download" target="_blank" rel="noopener">📎 ${esc(a.original_name)}</a>`).join('');
   return `<article class="message ${m.role==='user'?'user':m.role==='tool'?'tool':'assistant'}" data-message-id="${m.id}" data-message-content="${esc(m.content)}"><div class="role">${role} · ${new Date(m.created_at).toLocaleString()}</div><div class="bubble">${body}${files?`<div class="message-attachments">${files}</div>`:''}</div><div class="message-actions"><button type="button" class="message-action" data-message-copy="${m.id}" title="Копировать сообщение">Копировать</button><button type="button" class="message-action danger" data-message-delete="${m.id}" title="Удалить сообщение">Удалить</button></div></article>`;
  }).join('');
  applyCodeHighlighting(box);
  $('messages').querySelectorAll('.copy-code').forEach(btn=>btn.addEventListener('click',()=>{const codeElement=btn.closest('.code-card').querySelector('code');const code=rawCodeSources.get(codeElement)??codeElement.textContent??'';navigator.clipboard?.writeText(code).then(()=>toast('Код скопирован')).catch(()=>toast('Не удалось скопировать код'))}));
  $('messages').querySelectorAll('[data-message-copy]').forEach(btn=>btn.addEventListener('click',async()=>{const item=ms.find(x=>String(x.id)===btn.dataset.messageCopy);if(!item)return;try{await navigator.clipboard.writeText(item.content);toast('Сообщение скопировано')}catch{toast('Браузер не разрешил копирование')}}));
  $('messages').querySelectorAll('[data-message-delete]').forEach(btn=>btn.addEventListener('click',async()=>{const id=Number(btn.dataset.messageDelete);if(!confirm('Удалить это сообщение? Действие нельзя отменить.'))return;try{await api(`/api/branches/${activeBranch}/messages/${id}`,{method:'DELETE'});await loadMessages();await loadStats();toast('Сообщение удалено')}catch(e){toast(e.message)}}));
  if(wasNearBottom)box.scrollTop=box.scrollHeight;else box.scrollTop=oldScrollTop;
 }
function setContextLevel(level,message,tokens,limit,percent,remaining,reserve=0,approx=true){
 $('contextBarWrap').className='bar level-'+level;$('contextBar').style.width=Math.min(100,Math.max(0,percent||0))+'%';
 const pct=Number(percent||0), value=$('contextNotice');
 value.className='context-indicator level-'+level;
 value.querySelector('.context-indicator-value').textContent=(approx?'≈':'')+pct.toLocaleString('ru-RU')+'%';
 value.querySelector('.context-indicator-label').textContent=level==='critical'?'Критично':level==='high'?'Высокая':level==='warning'?'Внимание':'Контекст';
 const left=Number.isFinite(Number(remaining))?` · свободно ~${Number(remaining||0).toLocaleString('ru-RU')}`:'';
 const reserveText=reserve?` · резерв ответа ${Number(reserve).toLocaleString('ru-RU')}`:'';
 $('contextState').textContent=`${approx?'≈':''}${Number(tokens||0).toLocaleString('ru-RU')} / ${Number(limit||0).toLocaleString('ru-RU')} токенов · ${pct.toLocaleString('ru-RU')}%${reserveText}${left}`;
 value.title=`${message}\n${$('contextState').textContent}`;
}

async function continueInNewTask(){
 if(!activeTask||!activeBranch)return;
 $('handoffName').value='Продолжение: '+activeTask.title;
 $('handoffScope').value='branch';
 $('handoffScopeHelp').textContent='Только выбранная ветка, её история и контрольная точка. Самый компактный перенос.';
 $('handoffDialog').showModal();
}
$('cancelHandoff').addEventListener('click',()=>$('handoffDialog').close());
$('handoffScope').addEventListener('change',()=>{const help={branch:'Только выбранная ветка, её история и контрольная точка. Самый компактный перенос.',task:'Память задачи и сведения всех её веток. Подходит, если в разных ветках одной задачи принимались важные решения.',project:'Память проекта, текущая задача и сводные сведения других задач/веток этого проекта. Самый широкий перенос; объём ограничивается, чтобы не переполнить контекст.'};$('handoffScopeHelp').textContent=help[$('handoffScope').value]||''});
$('handoffForm').addEventListener('submit',async ev=>{
 ev.preventDefault();if(!activeTask||!activeBranch)return;
 const scope=$('handoffScope').value;
 const name=$('handoffName').value.trim()||('Продолжение: '+activeTask.title);
 const button=$('confirmHandoff'),oldLabel=button.textContent;
 button.disabled=true;button.textContent='Анализирую контекст…';
 try{
  const r=await api(`/api/tasks/${activeTask.id}/continue`,{method:'POST',body:JSON.stringify({branch_id:activeBranch,name,scope})});
  $('handoffDialog').close();
  toast(r.message+` Веток: ${r.included_branches}; сообщений в источниках: ${r.total_source_messages}; вложений: ${r.attachment_count}; ограничений объёма: ${r.omitted_tasks||0} задач / ${r.omitted_branches||0} веток; токены резюме: ${r.summary_prompt_tokens||'н/д'} + ${r.summary_completion_tokens||'н/д'}.`);
  await loadTasks();await selectTask(r.task_id,r.branch_id);
 }catch(e){toast('Не удалось перенести контекст: '+e.message)}
 finally{button.disabled=false;button.textContent=oldLabel}
});

async function previewContext(){
 if(!activeBranch)return;const text=$('prompt').value.trim();
 if(!text&&!selectedAttachments.length){$('statContext').textContent=baseContextEstimate.toLocaleString('ru-RU');$('contextNotice').className='context-indicator level-ok';$('contextNotice').title='Введите сообщение для оценки следующего запроса.';$('contextNotice').querySelector('.context-indicator-value').textContent='—';$('contextNotice').querySelector('.context-indicator-label').textContent='Контекст';return}const previewText=text||'Проанализируй приложенные файлы.';
 try{const p=await api('/api/context-preview',{method:'POST',body:JSON.stringify({branch_id:activeBranch,text:previewText,attachment_ids:selectedAttachments.map(x=>x.id)})});$('statContext').textContent=Number(p.estimated_prompt_tokens||0).toLocaleString('ru-RU');$('tokenSpent').textContent=Number(p.estimated_prompt_tokens||0).toLocaleString('ru-RU');$('tokenRemaining').textContent=Number(p.remaining_estimate||0).toLocaleString('ru-RU');$('tokenMiniBar').style.width=Math.min(100,Math.max(0,Number(p.percent||0)))+'%';$('tokenCompactHint').textContent=`Следующий запрос · заполнение с резервом ${Number(p.percent||0)}%`;setContextLevel(p.level,p.message,p.estimated_prompt_tokens,p.context_limit,p.percent,p.remaining_estimate,p.output_reserve_tokens,true)}
 catch(e){$('contextNotice').title='Не удалось оценить контекст: '+e.message;$('contextNotice').querySelector('.context-indicator-value').textContent='!';$('contextNotice').className='context-indicator level-warning'}
}
function usageKindLabel(kind){return ({chat:'Ответ модели',tool_call:'Вызов инструментов',memory_summary:'Сжатие памяти',tool_error_final:'Завершение после ошибки инструмента'})[kind]||kind||'Запрос'}
async function loadStats(branch=activeBranch){
 if(!branch)return;
 const requestBranch=Number(branch),requestSeq=++statsRequestSeq;
 const s=await api(`/api/branches/${requestBranch}/stats`);
 // Ignore late responses from a branch that is no longer selected.
 if(requestSeq!==statsRequestSeq||Number(activeBranch)!==requestBranch)return;
 $('statMessages').textContent=s.messages;baseContextEstimate=Number(s.estimated_context_tokens||0);$('statContext').textContent=baseContextEstimate.toLocaleString('ru-RU');
 const usage=s.usage||{p:0,c:0,t:0},inherited=s.usage_inherited||{p:0,c:0,t:0},direct=s.usage_direct||{p:0,c:0,t:0};
 $('tokenSpent').textContent=Number(s.context_tokens_used??s.estimated_context_tokens??0).toLocaleString('ru-RU'); $('tokenRemaining').textContent=Number(s.remaining_estimate||0).toLocaleString('ru-RU'); $('tokenMiniBar').style.width=Math.min(100,Math.max(0,Number(s.context_percent||0)))+'%'; $('tokenCompactHint').textContent=`Заполнение с резервом ${Number(s.context_percent||0)}% · API за историю ${Number(s.api_tokens_lifetime??usage.t??0).toLocaleString('ru-RU')}`;
 $('statPrompt').textContent=(usage.p||0).toLocaleString('ru-RU');$('statCompletion').textContent=(usage.c||0).toLocaleString('ru-RU');$('statTotal').textContent=(usage.t||0).toLocaleString('ru-RU');
 $('statInherited').textContent=(inherited.t||0).toLocaleString('ru-RU');$('statOwn').textContent=(direct.t||0).toLocaleString('ru-RU');$('statUnreported').textContent=Number(s.usage_unreported_calls||0).toLocaleString('ru-RU');
 const turn=s.last_turn,last=s.last_call;
 $('statTurnPrompt').textContent=turn?.prompt_tokens!=null?Number(turn.prompt_tokens).toLocaleString('ru-RU')+(turn.complete?'':'*'):'нет данных';
 $('statTurnCompletion').textContent=turn?.completion_tokens!=null?Number(turn.completion_tokens).toLocaleString('ru-RU')+(turn.complete?'':'*'):'нет данных';
 $('statTurnCalls').textContent=turn?`${turn.call_count} (учтено ${turn.reported_calls}${turn.unreported_calls?`, без usage ${turn.unreported_calls}`:''})`:'—';
 $('statLastPrompt').textContent=last?.usage_reported&&last.prompt_tokens!=null?Number(last.prompt_tokens).toLocaleString('ru-RU'):'нет данных';
 $('statLastCompletion').textContent=last?.usage_reported&&last.completion_tokens!=null?Number(last.completion_tokens).toLocaleString('ru-RU'):'нет данных';
 const modelLimit=s.model_context_limit?Number(s.model_context_limit).toLocaleString('ru-RU'):'активный не определён';
 const modelMax=s.model_max_context_limit?` · максимум модели ${Number(s.model_max_context_limit).toLocaleString('ru-RU')}`:'';
 const tokenParts=s.messages_tokens!=null?` · сообщения ${Number(s.messages_tokens).toLocaleString('ru-RU')} + инструменты ≈${Number(s.tools_tokens_estimate||0).toLocaleString('ru-RU')} + формат ${Number(s.format_overhead_estimate||0).toLocaleString('ru-RU')}`:'';
 $('tokenMethod').textContent=`${s.estimate_method||'Оценка токенов'}${tokenParts} · активный лимит: ${modelLimit}${modelMax} · ${s.limit_source||''}`;
 if(s.tokenizer_error)$('tokenMethod').textContent+=' · SDK: '+s.tokenizer_error;
 if(s.usage_unreported_calls)$('tokenMethod').textContent+=` · без usage от сервера: ${s.usage_unreported_calls} вызв.`;
 if(turn&&!turn.complete)$('tokenMethod').textContent+=' · * в сумме последнего обращения учтены только вызовы с usage';
 $('statLimit').textContent=(s.context_limit||0).toLocaleString('ru-RU');
 const pct=s.context_percent||0,level=pct>=85?'critical':pct>=75?'high':pct>=60?'warning':'ok';
 let message=level==='critical'?'Контекст достиг 85%. Рекомендуется перенести работу в новую задачу.':level==='high'?'Контекст близок к рабочему пределу. Рекомендуется подготовить перенос.':level==='warning'?'Контекст растёт. Workbench может автоматически сжать старую историю при достижении 60%.':'Запас контекста достаточный.';
 if(s.tokenizer_status!=='model_tokenizer')message+=' Предварительный подсчёт не использует токенизатор модели; после запроса точные числа придут из LM Studio.';
 setContextLevel(level,message,s.estimated_context_tokens,s.context_limit,pct,s.remaining_estimate,s.output_reserve_tokens,true);
 $('usageLog').innerHTML=(s.llm_calls||[]).length?(s.llm_calls||[]).map(x=>`<div class="usage-log-row"><b>${esc(usageKindLabel(x.call_kind))}</b><span>${esc(new Date(x.created_at).toLocaleString())}</span><small>${esc(x.model||'Модель') } · ${x.usage_reported?`вход ${Number(x.prompt_tokens||0).toLocaleString('ru-RU')} / выход ${Number(x.completion_tokens||0).toLocaleString('ru-RU')}`:'сервер не сообщил usage'}</small></div>`).join(''):'Подробный журнал начнёт заполняться после новых запросов. Старые API-итоги сохранены, но разбивки по отдельным вызовам для них нет.';
 $('memoryStatus').textContent=s.memory?`Память ветки сохранена · до сообщения #${s.memory.through_message_id}`:'Память ветки ещё не сформирована';
 $('memoryText').textContent=s.memory?.summary||'Пока пусто';
}
async function loadPending(){
 const p=await api(`/api/pending?branch_id=${activeBranch}`);
 $('pending').innerHTML=p.map(x=>`<div class="pending-card"><b>Требуется подтверждение изменения</b><div>Файл: <code>${esc(x.path)}</code></div><div class="muted small">ID ${x.id} · файл ещё не изменён</div><div class="pending-actions"><button class="primary" onclick="approve(${x.id})">Подтвердить запись</button><button class="ghost" onclick="reject(${x.id})">Отклонить</button></div></div>`).join('');
}
async function approve(id){
 if(!confirm('Разрешить модели записать этот файл в проект?'))return;
 try{let r=await api(`/api/pending/${id}/approve`,{method:'POST'});toast(r.result);await loadPending();await refreshFiles()}catch(e){toast(e.message)}
}
async function reject(id){await api(`/api/pending/${id}/reject`,{method:'POST'});toast('Изменение отклонено');await loadPending()}
async function refreshExecutionQueueState(branch=activeBranch){
 if(!branch||Number(branch)!==Number(activeBranch))return null;
 try{
  const rows=await api(`/api/execution/pending?branch_id=${encodeURIComponent(branch)}`);
  if(Number(branch)!==Number(activeBranch)||!Array.isArray(rows))return null;
  executionQueueLastKnown=rows;waitingForApproval=rows.length>0;renderChatComputeButton(false);
  return rows;
 }catch(e){console.warn('Не удалось синхронизировать очередь подтверждений:',e);return null;}
}
async function loadExecutionQueue(options={}){
 if(!activeBranch)return;
 const silent=!!options.silent, loadAux=!!options.loadAux;
 if(executionQueuePollBusy){if(!silent)toast('Обновление очереди уже выполняется; дождись результата.');return null;}
 executionQueuePollBusy=true;
 const queue=$('executionQueue');
 try{
  const rows=await api(`/api/execution/pending?branch_id=${encodeURIComponent(activeBranch)}`);
  if(!Array.isArray(rows))throw new Error('Сервер вернул некорректный формат очереди подтверждений');
  executionQueueLastKnown=rows;
  waitingForApproval=rows.length>0;
  queue.innerHTML=rows.length?`<div class="queue-status" role="status">Очередь обновлена · ожидают решения: ${rows.length}</div>`+rows.map(x=>`<div class="execution-card"><b>Запрос #${x.id} · ожидает подтверждения</b><div class="muted small">${esc(x.project_name||'Проект')} · ${esc(x.task_title||'Задача')} · ${esc(x.branch_name||'Ветка')}</div><pre>${esc(x.display_script||x.script)}</pre><div class="execution-actions"><button class="primary" onclick="approveExecution(${x.id})">Выполнить</button><button class="ghost" onclick="rejectExecution(${x.id})">Отклонить</button></div></div>`).join(''):`<div class="queue-status" role="status">Очередь обновлена · ожидающих команд нет</div>`;
  renderChatComputeButton(false);
  if(loadAux){await loadInputRequests();await loadServerProfiles();}
  if(!silent)toast(rows.length?`Очередь обновлена: ${rows.length} ожидающих команд`:'Очередь обновлена: ожидающих команд нет');
  return rows;
 }catch(e){
  // Never turn an API failure into a false "empty queue" state.
  queue.innerHTML=`<div class="queue-error" role="alert"><b>Не удалось обновить очередь подтверждений</b><div>${esc(e.message)}</div><div class="muted small">Последнее успешное состояние не считается актуальным.</div></div>`;
  if(!silent)toast(`Ошибка обновления очереди: ${e.message}`);
  console.error('Execution approval queue refresh failed:',e);
  return null;
 }finally{executionQueuePollBusy=false;}
}
function startExecutionQueuePolling(){
 if(executionQueuePollTimer)clearInterval(executionQueuePollTimer);
 executionQueuePollTimer=setInterval(()=>{if(activeBranch)loadExecutionQueue({silent:true})},2000);
}
async function loadInputRequests(){if(!activeBranch)return;try{const rows=await api(`/api/input-requests/pending?branch_id=${activeBranch}`);waitingForUserInput=rows.length>0;$('inputRequestQueue').innerHTML=rows.length?rows.map(x=>`<div class="input-request-card"><b>${esc(x.title)} · запрос #${x.id}</b><p>${esc(x.prompt)}</p>${x.input_type==='secret'?`<input id="inputValue-${x.id}" type="password" autocomplete="new-password" placeholder="Введи секрет" class="secure-value"> <label class="profile-remember"><input id="inputRemember-${x.id}" type="checkbox" ${credentialPersistenceAvailable?'':'disabled'}> Сохранить через DPAPI ${credentialPersistenceAvailable?'':'(только Windows)'}</label>`:`<textarea id="inputValue-${x.id}" rows="2" placeholder="Твой ответ" class="secure-value"></textarea>`}<div class="execution-actions"><button class="primary" onclick="submitInputRequest(${x.id},'${x.input_type}')">Отправить ответ</button><button class="ghost" onclick="rejectInputRequest(${x.id})">Отклонить</button></div></div>`).join(''):'Нет ожидающих запросов ввода';if(!busy)renderChatComputeButton(false);}catch(e){$('inputRequestQueue').textContent=e.message}}
async function submitInputRequest(id,type){const field=$(`inputValue-${id}`);const value=field?.value||'';if(!value.trim())return toast('Заполни поле ввода');const remember=type==='secret'&&!!$(`inputRemember-${id}`)?.checked;waitingForUserInput=false;setChatUiActive(true,activeBranch);try{await api(`/api/input-requests/${id}/submit`,{method:'POST',body:JSON.stringify({value,remember})});if(field)field.value='';toast('Ответ передан модели; секрет не добавлен в историю');await loadMessages();await loadExecutionQueue();}catch(e){toast(e.message);await loadInputRequests()}finally{await syncChatStatus(activeBranch)}}
async function rejectInputRequest(id){waitingForUserInput=false;setChatUiActive(true,activeBranch);try{await api(`/api/input-requests/${id}/reject`,{method:'POST'});toast('Запрос ввода отклонён');await loadMessages();await loadExecutionQueue()}catch(e){toast(e.message);await loadInputRequests()}finally{await syncChatStatus(activeBranch)}}
async function loadServerProfiles(){try{const rows=await api('/api/server-profiles');$('serverProfileList').innerHTML=rows.length?rows.map(x=>`<div class="profile-row"><span><b>${esc(x.name)}</b><small>${esc(x.username)}@${esc(x.host)}:${x.port} · ${x.auth_method==='password'?(x.credential_status==='persistent'?'пароль сохранён DPAPI':x.credential_status==='session'?'пароль доступен до перезапуска':'пароль недоступен'):'SSH-ключ'}</small></span><button class="ghost" onclick="deleteServerProfile(${x.id})">Удалить</button></div>`).join(''):'Нет сохранённых SSH-профилей';}catch(e){$('serverProfileList').textContent=e.message}}
async function deleteServerProfile(id){if(!confirm('Удалить SSH-профиль и связанный сохранённый пароль?'))return;try{const r=await api(`/api/server-profiles/${id}`,{method:'DELETE'});toast(r.credential_cleanup_warning?'Профиль удалён, но защищённый секрет не удалось очистить автоматически':'SSH-профиль удалён');await loadServerProfiles()}catch(e){toast(e.message)}}
$('profileAuth')?.addEventListener('change',()=>{const pass=$('profileAuth').value==='password';$('profilePassword').disabled=!pass;$('profileRemember').disabled=!pass||!credentialPersistenceAvailable;$('profilePassword').placeholder=pass?'Пароль SSH':'Не требуется для SSH-ключа'});
$('profileAuth')?.dispatchEvent(new Event('change'));
$('serverProfileForm')?.addEventListener('submit',async e=>{e.preventDefault();const auth_method=$('profileAuth').value;const password=$('profilePassword').value; if(auth_method==='password'&&!password)return toast('Для парольного профиля введи пароль');const body={name:$('profileName').value.trim(),host:$('profileHost').value.trim(),username:$('profileUser').value.trim(),port:Number($('profilePort').value),auth_method,password,remember_password:$('profileRemember').checked};try{await api('/api/server-profiles',{method:'POST',body:JSON.stringify(body)});$('profilePassword').value='';$('profileName').value='';$('profileHost').value='';$('profileUser').value='';$('profileRemember').checked=false;toast('SSH-профиль добавлен');await loadServerProfiles()}catch(e){toast(e.message)}});
let activeProcessId=null,processPollTimer=null,processStopRequested=false;
async function pollLiveProcess(){
 if(!activeProcessId)return;
 try{
  const p=await api(`/api/processes/${activeProcessId}`);
  $('liveProcess').classList.remove('hidden');
  $('liveProcessTitle').textContent=`${p.command} · ${p.status}${p.exit_code!==null?' · exit '+p.exit_code:''}`;
  $('liveProcessStdout').textContent=p.stdout||'';
  $('liveProcessStderr').textContent=p.stderr||'';
  $('liveProcessStdout').scrollTop=$('liveProcessStdout').scrollHeight;
  $('liveProcessStdout').classList.toggle('hidden',!p.stdout);
  $('liveProcessStdout').dataset.empty=p.stdout?'0':'1';
  const stopButton=$('stopLiveProcess');
  if(['completed','failed','stopped'].includes(p.status)){
   if(['waiting','running'].includes(p.execution_resume_status)){
    $('liveProcessTitle').textContent=`${p.command} · ${p.status} · модель продолжает работу…`;
    if(stopButton){stopButton.disabled=true;stopButton.textContent='Модель…';}
    await syncChatStatus(activeBranch);
    return;
   }
   clearInterval(processPollTimer);processPollTimer=null;
   await syncChatStatus(activeBranch);
   const wasStopRequested=processStopRequested;
   processStopRequested=false;
   if(stopButton){stopButton.disabled=true;stopButton.textContent='Остановить';}
   toast(wasStopRequested&&p.status==='stopped'?'Процесс остановлен':`Процесс завершён: ${p.status}, код ${p.exit_code}`);
   activeProcessId=null;
   await loadMessages();await loadExecutionQueue();
  }else if(stopButton){
   stopButton.disabled=processStopRequested;
   stopButton.textContent=processStopRequested?'Останавливаю…':'Остановить';
  }
 }catch(e){
  clearInterval(processPollTimer);processPollTimer=null;
  processStopRequested=false;
  const stopButton=$('stopLiveProcess');
  if(stopButton){stopButton.disabled=true;stopButton.textContent='Остановить';}
  toast(e.message);
 }
}
async function approveExecution(id){if(!confirm('Выполнить подготовленную команду? Проверь хост, пользователя и текст операции. Подтверждение в чате не запускает команду — для реального запуска нажми эту кнопку. SSH использует сохранённый профиль, строгий known_hosts и выбранный способ авторизации.'))return;try{const r=await api(`/api/execution/${id}/approve`,{method:'POST'});activeProcessId=r.job_id;$('liveProcess').classList.remove('hidden');$('liveProcessTitle').textContent='Запуск команды…';if(processPollTimer)clearInterval(processPollTimer);processPollTimer=setInterval(pollLiveProcess,500);await pollLiveProcess();await loadExecutionQueue()}catch(e){toast(e.message);await loadExecutionQueue()}}
$('stopLiveProcess')?.addEventListener('click',async()=>{if(!activeProcessId||processStopRequested)return;processStopRequested=true;const b=$('stopLiveProcess');if(b){b.disabled=true;b.textContent='Останавливаю…';}try{const r=await api(`/api/processes/${activeProcessId}/stop`,{method:'POST'});if(!r.ok)throw new Error('Сервер не подтвердил запрос остановки');if(r.active){toast(r.message||'Процесс ещё завершает работу');if(processPollTimer)clearInterval(processPollTimer);processPollTimer=setInterval(pollLiveProcess,500)}await pollLiveProcess();}catch(e){processStopRequested=false;if(b){b.disabled=false;b.textContent='Остановить';}toast(e.message)}});
async function rejectExecution(id){await api(`/api/execution/${id}/reject`,{method:'POST'});toast('Команда отклонена');await loadExecutionQueue()}
$('runTerminal')?.addEventListener('click',async()=>{const script=$('terminalCommand').value.trim();if(!script)return toast('Введи команду');if(!activeBranch)return toast('Сначала выбери задачу');try{const r=await api('/api/chat',{method:'POST',body:JSON.stringify({branch_id:activeBranch,text:'Подготовь к выполнению следующую PowerShell-команду через execute_powershell. Не выполняй её самостоятельно и кратко объясни назначение.\n\n'+script})});$('terminalCommand').value='';await loadMessages();await loadExecutionQueue();toast('Запрос передан агенту')}catch(e){toast(e.message)}});$('refreshExecution')?.addEventListener('click',()=>loadExecutionQueue({silent:false}));
async function refreshGit(){
 if(!activeProject)return;
 try{
  const r=await api(`/api/git/status?project_id=${activeProject.id}`);
  $('gitStatus').textContent=r.text;
  $('gitState').textContent=r.initialized?`Ветка: ${r.branch||'—'}${r.remote?' · Remote настроен':''}`:'Репозиторий не инициализирован';
  $('gitInit').classList.toggle('hidden',!!r.initialized);
  $('gitRepoActions').classList.toggle('hidden',!r.initialized);
  $('gitRemoteActions').classList.toggle('hidden',!r.initialized);
 }catch(e){$('gitStatus').textContent=e.message;$('gitState').textContent='Ошибка Git'}
}
async function gitPost(path,body={}){
 if(!activeProject)throw new Error('Сначала выбери проект');
 return await api(`/api/git/${path}?project_id=${activeProject.id}`,{method:'POST',body:JSON.stringify(body)});
}
function gitSelectedPaths(){
 const paths=$('gitPaths').value.split(/\\r?\\n/).map(x=>x.trim()).filter(Boolean);
 if(!paths.length)throw new Error('Укажи пути файлов, по одному на строку');
 return paths;
}
async function gitSync(action){
 if(!confirm(`${action.toUpperCase()}: выполнить операцию Git для текущего проекта? Проверь выбранный репозиторий и ветку.`))return;
 try{const r=await gitPost('sync',{action});toast(r.message||'Git: готово');await refreshGit()}catch(e){toast(e.message)}
}
async function loadReleaseTargets(){
 const select=$('releaseTarget');if(!select||!activeProject)return;
 try{
  const projects=await api('/api/projects');
  const choices=projects.filter(p=>p.id!==activeProject.id);
  select.innerHTML=choices.map(p=>`<option value="${p.id}">${esc(p.name)} · ${esc(p.root)}</option>`).join('');
  if(!choices.length){
   select.innerHTML='<option value="">Нет другого активного проекта</option>';
   $('releaseSummary').textContent='Добавь стабильный проект в Workbench, чтобы сравнить его с текущим.';
   $('releasePrepare').disabled=true;
  }else{
   $('releaseSummary').textContent='Текущий проект — источник изменений. Выбери стабильный проект-получатель.';
  }
  releaseCompareRows=[];releasePlanId=null;
  $('releaseFiles').innerHTML='';$('releasePlan').textContent='';
  $('releaseApply').classList.add('hidden');$('releasePrepare').disabled=true;
 }catch(e){$('releaseSummary').textContent='Не удалось загрузить проекты: '+e.message}
}
async function compareRelease(){
 if(!activeProject)return toast('Сначала выбери экспериментальный проект');
 const target=Number($('releaseTarget').value);
 if(!target)return toast('Выбери целевой стабильный проект');
 try{
  $('releaseCompare').disabled=true;$('releaseSummary').textContent='Сравниваю файлы…';
  const r=await api(`/api/releases/compare?project_id=${activeProject.id}`,{method:'POST',body:JSON.stringify({target_project_id:target})});
  releaseCompareRows=r.files||[];releasePlanId=null;$('releasePlan').textContent='';$('releaseApply').classList.add('hidden');
  const c=r.counts||{};
  $('releaseSummary').textContent=`Источник: ${r.source} → Получатель: ${r.target}. Добавлено: ${c.added||0} · Изменено: ${c.modified||0} · Отсутствует в источнике: ${c.deleted||0}.`;
  $('releaseFiles').innerHTML=releaseCompareRows.length?releaseCompareRows.map((f,i)=>`<label class="release-file"><input type="checkbox" data-release-index="${i}" ${f.change==='deleted'?'':'checked'}><span><b>${esc(f.change==='added'?'＋ Добавить':f.change==='modified'?'Изменить':'− Удалить из стабильного')}</b><code>${esc(f.path)}</code></span></label>`).join(''):'<div class="muted small">Различий нет.</div>';
  $('releasePrepare').disabled=!releaseCompareRows.some(f=>f.change!=='deleted');
  if(c.deleted)$('releaseSummary').textContent+=` Удаления не выбраны автоматически (${c.deleted}).`;
 }catch(e){$('releaseSummary').textContent='Сравнение не выполнено: '+e.message;toast(e.message)}
 finally{$('releaseCompare').disabled=false}
}
async function prepareRelease(){
 const paths=[...$('releaseFiles').querySelectorAll('[data-release-index]:checked')].map(x=>releaseCompareRows[Number(x.dataset.releaseIndex)]?.path).filter(Boolean);
 if(!paths.length)return toast('Выбери хотя бы один файл');
 try{
  const target=Number($('releaseTarget').value);
  const r=await api(`/api/releases/prepare?project_id=${activeProject.id}`,{method:'POST',body:JSON.stringify({target_project_id:target,paths})});
  releasePlanId=r.plan_id;
  $('releasePlan').textContent=`План ${releasePlanId.slice(0,8)} подготовлен: ${r.files.length} файлов. Стабильный проект пока не изменён.`;
  $('releaseApply').classList.remove('hidden');toast('План подготовлен. Целевой проект не изменён.')
 }catch(e){toast(e.message)}
}
async function applyRelease(){
 if(!releasePlanId)return;
 const target=Number($('releaseTarget').value);
 const count=[...$('releaseFiles').querySelectorAll('[data-release-index]:checked')].length;
 if(!confirm(`Последнее подтверждение: перенести ${count} выбранных файлов в стабильный проект? Перед изменением создаётся резервная копия. Commit и Push не выполняются.`))return;
 try{
  const r=await api(`/api/releases/apply?project_id=${activeProject.id}`,{method:'POST',body:JSON.stringify({target_project_id:target,plan_id:releasePlanId})});
  $('releasePlan').textContent=`Перенесено файлов: ${r.applied.length}. Резервная копия: ${r.backup}`;
  $('releaseApply').classList.add('hidden');releasePlanId=null;toast(r.message||'Файлы перенесены')
 }catch(e){toast(e.message)}
}
async function refreshFiles(){
 const button=$('refreshFiles'), output=$('fileList');
 if(!output)return;
 if(!activeProject){output.textContent='Сначала выбери проект';toast('Сначала выбери проект');return}
 const original=button?.textContent;
 if(button){button.disabled=true;button.textContent='Обновляю…'}
 output.textContent='Обновление списка файлов…';
 try{
  const r=await api(`/api/files?project_id=${encodeURIComponent(activeProject.id)}`);
  const listing=r.listing||'В проекте нет файлов для отображения';
  output.textContent=listing;
  output.innerHTML=listing.split('\n').map(line=>{const m=line.match(/^FILE\s+(.+)$/);return m?`<span class="file-list-row"><button type="button" class="file-open-link" data-file-path="${esc(m[1])}">${esc(line)}</button></span>`:esc(line)}).join('\n');
  $('projectRoot').textContent=r.project_root||activeProject.root||'—';
  if(button)button.title='Список обновлён';
 }catch(e){
  output.textContent=`Не удалось обновить список файлов: ${e.message}`;
  toast(`Файлы проекта: ${e.message}`);
 }finally{if(button){button.disabled=false;button.textContent=original||'Обновить список'}}
}
async function openProjectFile(path){
 if(!activeProject)return toast('Сначала выбери проект');
 const rel=String(path||'').trim();if(!rel)return toast('Укажи относительный путь к файлу');
 const meta=$('fileViewerMeta'), viewer=$('fileViewer'), copy=$('copyProjectFile');
 meta.textContent='Читаю файл…';viewer.classList.remove('hidden');viewer.textContent='Загрузка…';copy.disabled=true;
 try{
  const r=await api(`/api/files/read?project_id=${encodeURIComponent(activeProject.id)}&path=${encodeURIComponent(rel)}`);
  if(!activeProject||Number(r.project_id)!==Number(activeProject.id))return;
  openedProjectFile=r.path;openedProjectFileContent=r.content;
  $('fileOpenPath').value=r.path;meta.textContent=`${r.path} · ${r.language} · ${r.line_count} строк · ${r.size.toLocaleString()} байт · ${r.encoding}`;
  const allLines=String(r.content).replace(/\r\n?/g,'\n').split('\n');const lines=allLines.slice(0,20000);
  const viewerFragment=document.createDocumentFragment();
  lines.forEach((line,i)=>{
   const row=document.createElement('div');row.className='code-view-line';
   const number=document.createElement('span');number.className='code-line-number';number.textContent=String(i+1);
   const text=document.createElement('span');text.className='code-line-text';
   text.appendChild(highlightCodeFragment(line,r.language));
   row.append(number,text);viewerFragment.appendChild(row);
  });
  viewer.replaceChildren(viewerFragment);
  if(allLines.length>lines.length)meta.textContent+=` · показаны первые ${lines.length.toLocaleString()} строк`;
  viewer.style.fontSize=`${fileViewerFontSize}px`;viewer.classList.toggle('wrap-lines',$('fileWrap').checked);copy.disabled=false;
 }catch(e){meta.textContent=`Не удалось открыть файл: ${e.message}`;viewer.textContent='';toast(`Просмотр файла: ${e.message}`)}
}
function adjustFileViewerFont(delta){fileViewerFontSize=Math.max(10,Math.min(20,fileViewerFontSize+delta));$('fileViewer').style.fontSize=`${fileViewerFontSize}px`}
function renderChatComputeButton(stopping=false){
 const button=$('send');if(!button)return;
 const stage=chatActivity?.stage||'idle',detail=chatActivity?.detail||'';
 if(waitingForUserInput||stage==='waiting_input'){
  button.disabled=true;button.classList.remove('danger','is-computing','is-stopping','is-waiting-approval');button.classList.add('is-waiting-input');
  button.setAttribute('aria-label','Ожидается защищённый ввод');button.title='Ответь в панели «Защищённый ввод пользователя»';
  button.innerHTML='<span class="compute-main"><span class="compute-lock" aria-hidden="true">🔒</span><span>Ввод</span></span>';return;
 }
 if(waitingForApproval||stage==='waiting_approval'){
  button.disabled=true;button.classList.remove('danger','is-computing','is-stopping','is-waiting-input');button.classList.add('is-waiting-approval');
  button.setAttribute('aria-label','Ожидается подтверждение команды');button.title='Открой панель выполнения и подтверди или отклони команду';
  button.innerHTML='<span class="compute-main"><span aria-hidden="true">◷</span><span>Подтверждение</span></span>';return;
 }
 button.classList.remove('is-waiting-input','is-waiting-approval');
 if(stopping){button.disabled=true;button.classList.add('danger','is-computing','is-stopping');button.setAttribute('aria-label','Останавливаю');button.title='Ожидаю подтверждения остановки';button.innerHTML='<span class="compute-main"><span class="compute-spinner"></span><span>Стоп…</span></span>';return;}
 if(busy){
  button.disabled=false;button.classList.add('danger','is-computing');button.classList.remove('is-stopping');
  button.setAttribute('aria-label','Остановить генерацию модели или текущую операцию агента');
  const activityStarted=Number(chatActivity?.updated_at||0)*1000;const elapsed=activityStarted?Math.max(0,Math.floor((Date.now()-activityStarted)/1000)):(chatBusySince?Math.max(0,Math.floor((Date.now()-chatBusySince)/1000)):0);
  const mm=String(Math.floor(elapsed/60)).padStart(2,'0'),ss=String(elapsed%60).padStart(2,'0');
  const stageLabel=stage==='tool_running'?'Tool':stage==='preparing'?'Подготовка':'Compute';
  button.title=detail?`${stageLabel}: ${detail}`:stageLabel;
  button.innerHTML=`<span class="compute-main"><span class="compute-spinner"></span><span>${stageLabel}</span><span class="compute-time">${mm}:${ss}</span><span class="compute-stop-label">· Стоп</span></span>`;return;
 }
 button.disabled=false;button.classList.remove('danger','is-computing','is-stopping');button.removeAttribute('aria-label');button.title='Отправить сообщение';button.textContent='Отправить ↑';
}

function stopChatPolling(){if(chatPollTimer){clearInterval(chatPollTimer);chatPollTimer=null}}
async function pollChatActivity(branch){
 if(chatPollBusy||!branch)return;chatPollBusy=true;
 try{
  const state=await api(`/api/chat/status?branch_id=${encodeURIComponent(branch)}`);
  if(Number(activeBranch)!==Number(branch))return;
  chatActivity=state.activity||{stage:'idle',detail:''};
  if(typeof refreshExecutionQueueState==='function')await refreshExecutionQueueState(branch);
  if(!!state.active!==busy)setChatUiActive(!!state.active,branch);
  renderChatComputeButton(false);
  // Tool events are committed before the full agent turn returns. Refresh the
  // transcript while busy so users never need to press Stop to reveal them.
  if(state.active){
   await loadMessages();
   // Context statistics are more expensive than activity polling (the API
   // also queries LM Studio metadata). Refresh them sparingly while active.
   if(Date.now()-statsPollLastAt>=15000&&!statsPollBusy){
    statsPollLastAt=Date.now();statsPollBusy=true;
    loadStats(branch).catch(e=>console.warn('Не удалось обновить статистику контекста:',e)).finally(()=>{statsPollBusy=false});
   }
  }
  else if(['waiting_input','waiting_approval'].includes(chatActivity.stage))await loadMessages();
  else{
   // The server may have committed the final assistant message immediately
   // before CHAT_TASKS became inactive. Fetch the final transcript before
   // stopping polling so it is visible without a subsequent user action.
   await loadMessages();
   stopChatPolling();
  }
 }catch(e){console.warn('Не удалось обновить состояние агента:',e)}finally{chatPollBusy=false}
}
function setChatUiActive(active,branch=activeBranch){
 const wasBusy=busy;busy=!!active;activeChatBranch=busy?Number(branch):null;
 if(busy&&!wasBusy){chatBusySince=Date.now();statsPollLastAt=0;if(chatElapsedTimer)clearInterval(chatElapsedTimer);chatElapsedTimer=setInterval(()=>{if(busy)renderChatComputeButton(false);else{clearInterval(chatElapsedTimer);chatElapsedTimer=null}},1000);stopChatPolling();chatPollTimer=setInterval(()=>pollChatActivity(Number(branch)),1200)}
 if(!busy){chatBusySince=0;if(chatElapsedTimer){clearInterval(chatElapsedTimer);chatElapsedTimer=null}stopChatPolling()}
 renderChatComputeButton(false);
}
async function syncChatStatus(branch=activeBranch){
 if(!branch)return false;
 try{const state=await api(`/api/chat/status?branch_id=${encodeURIComponent(branch)}`);if(Number(activeBranch)===Number(branch)){chatActivity=state.activity||{stage:'idle',detail:''};setChatUiActive(!!state.active,branch);renderChatComputeButton(false)}return !!state.active}
 catch(e){console.warn('Не удалось синхронизировать состояние модели:',e);return false}
}
async function stopChat(){
 const branch=activeChatBranch||activeBranch;
 if(!branch)return;
 renderChatComputeButton(true);
 try{
  const result=await api(`/api/chat/cancel?branch_id=${encodeURIComponent(branch)}`,{method:'POST'});
  if(result.active){setChatUiActive(true,branch);toast(result.message||'Сервер ещё завершает запрос');return}
  chatActivity={stage:'idle',detail:''};setChatUiActive(false);toast(result.cancelled?'Генерация остановлена':'Активной генерации уже нет');
  await loadMessages();await loadStats();
 }catch(e){setChatUiActive(true,branch);toast(`Не удалось остановить генерацию: ${e.message}`)}
}
async function send(){
 if(busy){await stopChat();return}
 if(!activeBranch)return;let text=$('prompt').value.trim();if(!text&&!selectedAttachments.length)return;if(!text)text='Проанализируй приложенные файлы. Сначала определи их содержимое и структуру, затем укажи, какие материалы требуют дополнительного поиска.';
 const requestBranch=Number(activeBranch);
 chatActivity={stage:'preparing',detail:'Подготовка запроса'};waitingForUserInput=false;waitingForApproval=false;
 setChatUiActive(true,requestBranch);$('prompt').value='';
 const temp=document.createElement('div');temp.className='message user pending-send';temp.innerHTML='<div class="role">Вы · отправляется</div><div class="bubble"></div>';temp.querySelector('.bubble').textContent=text;
 $('messages').appendChild(temp);$('messages').scrollTop=$('messages').scrollHeight;
 let preserveActive=false;
 try{let r=await api('/api/chat',{method:'POST',body:JSON.stringify({branch_id:requestBranch,text,attachment_ids:selectedAttachments.map(x=>x.id)})});selectedAttachments=[];renderAttachmentChips();await loadMessages();await loadStats();await loadPending();await loadExecutionQueue();await loadAttachments();await syncChatStatus(requestBranch);if(r.stopped)toast('Генерация остановлена');else if(r.usage?.prompt_tokens||r.usage?.completion_tokens)toast(`Запрос: ${r.usage.prompt_tokens||0} · ответ: ${r.usage.completion_tokens||0} токенов`)}
 catch(e){
  temp.classList.add('send-failed');temp.querySelector('.role').textContent='Вы · сообщение не отправлено';
  const stillActive=await syncChatStatus(requestBranch);
  if(stillActive){preserveActive=true;$('prompt').value=text;temp.querySelector('.bubble').textContent=text+'\n\nПредыдущий запрос модели ещё выполняется. Сообщение не отправлено. Нажми «Остановить» или дождись завершения.';toast('Предыдущий запрос ещё выполняется — состояние остановки восстановлено')}
  else{temp.querySelector('.bubble').textContent=text+'\n\nОшибка: '+e.message;toast(e.message)}
 }
 finally{if(!preserveActive)setChatUiActive(false)}
}
function renderAttachmentChips(){
 const root=$('attachmentChips');if(!root)return;
 root.innerHTML=selectedAttachments.map(a=>`<div class="attachment-chip"><span>📎 ${esc(a.original_name)}</span><button type="button" data-remove-attachment="${a.id}" title="Убрать">×</button></div>`).join('');
 root.querySelectorAll('[data-remove-attachment]').forEach(b=>b.onclick=()=>{selectedAttachments=selectedAttachments.filter(x=>x.id!==Number(b.dataset.removeAttachment));renderAttachmentChips()});
}
async function uploadFile(file){
 if(!activeProject){toast('Сначала выбери проект');return}
 const fd=new FormData();fd.append('file',file);fd.append('project_id',activeProject.id);
 const scope=$('attachmentScope').value;if(scope!=='project'&&activeTask)fd.append('task_id',activeTask.id);if(scope==='branch'&&activeBranch)fd.append('branch_id',activeBranch);
 try{const a=await api('/api/attachments',{method:'POST',body:fd});selectedAttachments.push(a);renderAttachmentChips();await loadAttachments();previewContext();toast(`Файл загружен: ${a.original_name}`)}catch(e){toast(`Не удалось загрузить ${file.name}: ${e.message}`)}
}
async function loadAttachments(){
 if(!activeProject)return;
 try{
  const q=new URLSearchParams({project_id:String(activeProject.id)});if(activeTask)q.set('task_id',String(activeTask.id));if(activeBranch)q.set('branch_id',String(activeBranch));
  const files=await api('/api/attachments?'+q.toString());
  $('attachmentList').innerHTML=files.length?files.map(a=>`<div class="attachment-row"><div class="attachment-info"><a href="/api/attachments/${a.id}/download" target="_blank" rel="noopener">${esc(a.original_name)}</a><small>${esc(a.kind)} · ${(a.size/1024).toFixed(1)} КБ · фрагментов: ${a.chunks}</small><small>${esc(a.note||'')}</small></div><button class="ghost attachment-select" data-select-attachment="${a.id}" title="Прикрепить к следующему сообщению">＋</button><button class="ghost attachment-delete" data-delete-attachment="${a.id}" title="Удалить">×</button></div>`).join(''):'Пока нет загруженных файлов';
  $('attachmentList').querySelectorAll('[data-delete-attachment]').forEach(b=>b.onclick=async()=>{const id=Number(b.dataset.deleteAttachment);if(!confirm('Удалить вложение из Workbench?'))return;try{await api(`/api/attachments/${id}?project_id=${activeProject.id}`,{method:'DELETE'});selectedAttachments=selectedAttachments.filter(x=>x.id!==id);renderAttachmentChips();await loadAttachments();toast('Вложение удалено')}catch(e){toast(e.message)}});
  $('attachmentList').querySelectorAll('[data-select-attachment]').forEach(b=>b.onclick=()=>{const id=Number(b.dataset.selectAttachment);const a=files.find(x=>x.id===id);if(!a)return;if(selectedAttachments.some(x=>x.id===id)){toast('Файл уже прикреплён к сообщению');return}if(selectedAttachments.length>=12){toast('Максимум 12 файлов на сообщение');return}selectedAttachments.push(a);renderAttachmentChips();previewContext();toast('Файл добавлен к следующему сообщению')});
 }catch(e){$('attachmentList').textContent=e.message}
}
async function searchAttachments(){
 const input=$('attachmentSearch'), results=$('attachmentSearchResults'), button=$('searchAttachments');
 const query=input?.value.trim()||'';
 if(!query){toast('Введи текст для поиска');input?.focus();return}
 if(!activeProject){toast('Сначала выбери проект');return}
 const original=button?.textContent;
 if(button){button.disabled=true;button.textContent='Ищу…'}
 if(results){results.classList.remove('hidden');results.textContent='Поиск по вложениям…'}
 try{
  const q=new URLSearchParams({project_id:String(activeProject.id),q:query});
  if(activeTask)q.set('task_id',String(activeTask.id));
  if(activeBranch)q.set('branch_id',String(activeBranch));
  const rows=await api('/api/attachments/search?'+q.toString());
  results.classList.remove('hidden');
  results.innerHTML=rows.length?rows.map(x=>`<div class="attachment-hit"><b>${esc(x.name)}</b><small>${esc(x.path)}</small><pre>${esc(x.excerpt)}</pre><button class="ghost" data-insert-excerpt="${encodeURIComponent(x.excerpt)}">Вставить фрагмент в сообщение</button></div>`).join(''):'Совпадений не найдено';
  results.querySelectorAll('[data-insert-excerpt]').forEach(b=>b.onclick=()=>{$('prompt').value+=`\n\nФрагмент из вложения:\n${decodeURIComponent(b.dataset.insertExcerpt)}`;$('prompt').focus()});
 }catch(e){if(results){results.classList.remove('hidden');results.textContent=`Ошибка поиска: ${e.message}`}toast(`Поиск вложений: ${e.message}`)}
 finally{if(button){button.disabled=false;button.textContent=original||'Найти'}}
}
function openImportDialog(){
 if(!activeProject)return; $('importName').value='Импортированный контекст';$('importContent').value='';$('importFile').value='';$('importMode').value='new_branch';$('importDialog').showModal();
}
$('importFile').addEventListener('change',async e=>{const f=e.target.files?.[0];if(!f)return;if(f.size>2*1024*1024){toast('Файл контекста должен быть не больше 2 МБ');e.target.value='';return}try{$('importContent').value=await f.text()}catch(err){toast('Не удалось прочитать файл: '+err.message)}});
$('cancelImport').onclick=()=>$('importDialog').close();
$('importForm').addEventListener('submit',async e=>{
 e.preventDefault();const content=$('importContent').value.trim();if(!content){toast('Вставь текст или выбери файл контекста');return}
 const mode=$('importMode').value;const payload={project_id:activeProject.id,mode,content,name:$('importName').value.trim()||'Импортированный контекст'};
 if(mode!=='new_task'){if(!activeBranch){toast('Сначала выбери задачу и ветку');return}payload.branch_id=activeBranch}
 if(mode==='current_branch'&&activeTask)payload.task_id=activeTask.id;
 try{const result=await api('/api/context/import',{method:'POST',body:JSON.stringify(payload)});$('importDialog').close();toast(result.message);if(mode==='new_task'){await loadTasks();await selectTask(result.task_id,result.branch_id)}else if(mode==='new_branch'){await selectTask(activeTask.id,result.branch_id)}else{await loadStats()}}
 catch(err){toast(err.message)}
});
$('attachFiles').onclick=()=>$('fileInput').click();
$('fileInput').addEventListener('change',async e=>{for(const f of Array.from(e.target.files||[]))await uploadFile(f);e.target.value=''});
$('composer').addEventListener('dragover',e=>{e.preventDefault();$('composer').classList.add('drag-over')});
$('composer').addEventListener('dragleave',e=>{if(!$('composer').contains(e.relatedTarget))$('composer').classList.remove('drag-over')});
$('composer').addEventListener('drop',async e=>{e.preventDefault();$('composer').classList.remove('drag-over');for(const f of Array.from(e.dataTransfer?.files||[]))await uploadFile(f)});
$('searchAttachments').onclick=searchAttachments;
$('attachmentSearch').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();searchAttachments()}});
$('importCheckpoint').onclick=openImportDialog;

$('newProject').onclick=newProject;
$('archiveProject').onclick=async()=>{if(!activeProject)return;const count=Number(activeProject.task_count||0);const message=`Удалить проект «${activeProject.name}» из списка Workbench?\n\nПуть: ${activeProject.root}\nЗадач: ${count}\n\nПапка на диске, задачи, переписка, память, вложения и Git-история НЕ удаляются. Проект можно вернуть, добавив ту же папку повторно.`;if(!confirm(message))return;try{await api(`/api/projects/${activeProject.id}`,{method:'DELETE'});localStorage.removeItem('sergdata.activeProject');toast('Проект удалён из списка; данные сохранены');await reloadProjects()}catch(e){toast(e.message)}};
$('renameProject').onclick=async()=>{if(!activeProject)return;const name=prompt('Новое название проекта:',activeProject.name);if(!name?.trim())return;try{await api(`/api/projects/${activeProject.id}`,{method:'PATCH',body:JSON.stringify({name:name.trim()})});await reloadProjects(activeProject.id);toast('Проект переименован')}catch(e){toast(e.message)}};
$('projectSelect').onchange=e=>{if(e.target.value)selectProject(Number(e.target.value)).catch(e=>toast(e.message))};
$('newTask').onclick=newTask;$('welcomeNew').onclick=newTask;$('send').onclick=send;$('refreshFiles').onclick=refreshFiles;$('refreshGit').onclick=refreshGit;
$('openProjectFile').onclick=()=>openProjectFile($('fileOpenPath').value);$('fileOpenPath').addEventListener('keydown',e=>{if(e.key==='Enter')openProjectFile(e.target.value)});$('fileFontDown').onclick=()=>adjustFileViewerFont(-1);$('fileFontUp').onclick=()=>adjustFileViewerFont(1);$('fileWrap').onchange=e=>$('fileViewer').classList.toggle('wrap-lines',e.target.checked);$('copyProjectFile').onclick=async()=>{try{await navigator.clipboard.writeText(openedProjectFileContent);toast('Содержимое файла скопировано')}catch(e){toast('Не удалось скопировать: '+e.message)}};$('fileList').addEventListener('click',e=>{const b=e.target.closest('[data-file-path]');if(b)openProjectFile(b.dataset.filePath)});
$('saveTaskMemory').onclick=async()=>{try{await api(`/api/tasks/${activeTask.id}/memory`,{method:'PUT',body:JSON.stringify({name:$('taskMemoryInput').value})});toast('Память задачи сохранена')}catch(e){toast(e.message)}};
$('saveProjectMemory').onclick=async()=>{try{await api(`/api/projects/${activeProject.id}/memory`,{method:'PUT',body:JSON.stringify({name:$('projectMemoryInput').value})});toast('Память проекта сохранена')}catch(e){toast(e.message)}};
$('releaseCompare')?.addEventListener('click',compareRelease);$('releasePrepare')?.addEventListener('click',prepareRelease);$('releaseApply')?.addEventListener('click',applyRelease);
 $('showDiff').onclick=async()=>{try{const r=await api(`/api/git/diff?project_id=${activeProject.id}`);$('gitDiff').textContent=typeof r==='string'?r:(r?.diff??JSON.stringify(r,null,2));$('gitDiff').classList.remove('hidden')}catch(e){toast(e.message)}};
 $('gitInit').onclick=async()=>{if(!confirm('Создать Git-репозиторий в корне выбранного проекта? Файлы проекта не будут удалены.'))return;try{const r=await gitPost('init');toast(r.message||'Git инициализирован');await refreshGit()}catch(e){toast(e.message)}};
 $('gitStage').onclick=async()=>{try{const r=await gitPost('stage',{paths:gitSelectedPaths()});toast(r.message);await refreshGit()}catch(e){toast(e.message)}};
 $('gitUnstage').onclick=async()=>{try{const r=await gitPost('unstage',{paths:gitSelectedPaths()});toast(r.message);await refreshGit()}catch(e){toast(e.message)}};
 $('gitCommit').onclick=async()=>{const message=$('gitCommitMessage').value.trim();if(!message)return toast('Введи сообщение коммита');if(!confirm('Создать коммит из подготовленных файлов? Сначала проверь diff.'))return;try{const r=await gitPost('commit',{message});$('gitCommitMessage').value='';toast(r.message||'Коммит создан');await refreshGit()}catch(e){toast(e.message)}};
 $('gitHistory').onclick=async()=>{try{const r=await api(`/api/git/history?project_id=${activeProject.id}`);$('gitHistoryOutput').textContent=r.history||'История пуста';$('gitHistoryOutput').classList.remove('hidden')}catch(e){toast(e.message)}};
 $('gitRemoteSave').onclick=async()=>{const url=$('gitRemoteUrl').value.trim();if(!url)return toast('Введи URL GitHub/Git-сервера');if(!confirm('Подключить этот адрес как origin?'))return;try{const r=await gitPost('remote',{name:'origin',url});toast(r.message);await refreshGit()}catch(e){toast(e.message)}};
 $('gitFetch').onclick=()=>gitSync('fetch');$('gitPull').onclick=()=>gitSync('pull');$('gitPush').onclick=()=>gitSync('push');
$('prompt').addEventListener('input',()=>{clearTimeout(previewTimer);previewTimer=setTimeout(previewContext,250)});
$('prompt').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
$('branchSelect').onchange=async e=>{activeBranch=Number(e.target.value);selectedAttachments=[];renderAttachmentChips();await loadMessages();await syncChatStatus(activeBranch);await loadStats();await loadPending();await loadAttachments()};
$('renameBranch').onclick=async()=>{let n=prompt('Новое название ветки:');if(!n)return;await api(`/api/branches/${activeBranch}`,{method:'PATCH',body:JSON.stringify({name:n})});await selectTask(activeTask.id,activeBranch)};
$('deleteBranch').onclick=async()=>{if(!confirm('Удалить эту ветку и её сообщения?'))return;try{await api(`/api/branches/${activeBranch}`,{method:'DELETE'});await selectTask(activeTask.id)}catch(e){toast(e.message)}};
$('newBranch').onclick=async()=>{let n=prompt('Название новой ветки:','Эксперимент');if(!n)return;let r=await api(`/api/branches/${activeBranch}/fork`,{method:'POST',body:JSON.stringify({name:n})});await selectTask(activeTask.id,r.branch_id)};
$('renameTask').onclick=async()=>{let n=prompt('Новое название задачи:',activeTask.title);if(!n)return;await api(`/api/tasks/${activeTask.id}`,{method:'PATCH',body:JSON.stringify({name:n})});await selectTask(activeTask.id,activeBranch)};
$('deleteTask').onclick=async()=>{if(!confirm('Удалить задачу, все ветки и переписку? Это действие нельзя отменить.'))return;await api(`/api/tasks/${activeTask.id}`,{method:'DELETE'});activeTask=null;activeBranch=null;selectedAttachments=[];renderAttachmentChips();$('saveTaskMemory').disabled=true;$('chat').classList.add('hidden');$('welcome').classList.remove('hidden');$('taskTitle').textContent='Выберите задачу';$('branchTitle').textContent='Создайте задачу, чтобы начать';await loadTasks()};
$('checkpoint').onclick=async()=>{
 if(!activeBranch){toast('Сначала выбери задачу и ветку');return}
 const button=$('checkpoint');
 if(button.disabled)return;
 button.disabled=true;
 const original=button.textContent;
 button.textContent='Сохраняю…';
 try{
  const r=await api(`/api/branches/${activeBranch}/checkpoint`,{method:'POST'});
  toast(r.message||`Контрольная точка сохранена до сообщения #${r.through_message_id}`);
  await loadStats();
 }catch(e){toast(`Не удалось сохранить контрольную точку: ${e.message}`)}
 finally{button.disabled=false;button.textContent=original}
};
$('exportCheckpoint').onclick=()=>{if(activeBranch)window.open(`/api/branches/${activeBranch}/checkpoint.md`,'_blank')};
$('continueNewTask').onclick=continueInNewTask;

// Global agent settings: persisted by the Workbench database, applied to the next request.
const AGENT_DEFAULTS={context_limit:50000,max_tool_rounds:16,max_tool_calls:24,temperature:0.2,request_timeout:180};
async function fillAgentSettings(s){
 const contextSelect=$('agentContextLimit'), contextValue=String(s.context_limit);
 const defaultSelect=$('agentDefaultProject');
 if(defaultSelect){
  const projects=await api('/api/projects');
  defaultSelect.innerHTML='<option value="">Не выбирать автоматически</option>'+projects.map(p=>`<option value="${p.id}">${esc(p.name)} · ${esc(p.root)}</option>`).join('');
  defaultSelect.value=s.default_project_id==null?'':String(s.default_project_id);
 }
 const workspaceRoot=$('agentWorkspaceRoot');
 if(workspaceRoot){workspaceRoot.textContent=activeProject?.root||'Определяется активным проектом автоматически; без выбранного проекта файловые операции запрещены.';}
 if(![...contextSelect.options].some(o=>o.value===contextValue)){
  const opt=document.createElement('option');opt.value=contextValue;opt.textContent=contextValue+' токенов — текущее значение';contextSelect.add(opt);
 }
 contextSelect.value=contextValue;
 $('agentToolRounds').value=String(s.max_tool_rounds);
 $('agentToolCalls').value=String(s.max_tool_calls);
 $('agentTemperature').value=String(s.temperature);
 $('agentTimeout').value=String(s.request_timeout);
}
async function loadAgentSettings(){
 try{const s=await api('/api/settings/agent');await fillAgentSettings(s);$('agentSettingsStatus').textContent='Настройки загружены.'}
 catch(e){$('agentSettingsStatus').textContent='Не удалось загрузить настройки: '+e.message}
}

// Make every toolbar action reachable without wrapping: mouse wheel scrolls the row horizontally.
(()=>{
 const toolbar=document.querySelector('.top-actions');
 if(!toolbar)return;
 toolbar.addEventListener('wheel',event=>{
  if(Math.abs(event.deltaY)>Math.abs(event.deltaX)&&toolbar.scrollWidth>toolbar.clientWidth){
   event.preventDefault();toolbar.scrollLeft+=event.deltaY;
  }
 },{passive:false});
 toolbar.addEventListener('keydown',event=>{
  if(event.altKey||event.ctrlKey||event.metaKey)return;
  if(event.key==='ArrowRight'){toolbar.scrollLeft+=90;}
  else if(event.key==='ArrowLeft'){toolbar.scrollLeft-=90;}
  else if(event.key==='End'){toolbar.scrollLeft=toolbar.scrollWidth;}
  else if(event.key==='Home'){toolbar.scrollLeft=0;}
 });
})();

// Render the settings panel in the document layer so toolbar scrolling cannot clip it.
(()=>{
 const details=$('agentSettingsMenu');
 const summary=details?.querySelector(':scope > summary');
 const panel=details?.querySelector('.agent-settings-popover');
 const toolbar=details?.closest('.top-actions');
 if(!details||!summary||!panel)return;
 const placeholder=document.createComment('agent-settings-popover');
 panel.before(placeholder);
 document.body.appendChild(panel);
 panel.hidden=true;
 const place=()=>{
  if(!details.open||panel.hidden)return;
  const r=summary.getBoundingClientRect();
  const width=Math.min(360,window.innerWidth-24);
  const left=Math.max(12,Math.min(r.left,window.innerWidth-width-12));
  const panelHeight=panel.getBoundingClientRect().height;
  const top=Math.max(12,Math.min(r.bottom+8,window.innerHeight-panelHeight-12));
  panel.style.left=`${left}px`;panel.style.top=`${top}px`;
 };
 const sync=()=>{panel.hidden=!details.open;if(details.open){place();requestAnimationFrame(place)}};
 details.addEventListener('toggle',sync);
 window.addEventListener('resize',place,{passive:true});
 window.addEventListener('scroll',place,{passive:true,capture:true});
 toolbar?.addEventListener('scroll',place,{passive:true});
 document.addEventListener('pointerdown',event=>{if(details.open&&!panel.contains(event.target)&&!details.contains(event.target))details.open=false});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&details.open)details.open=false});
})();

// The top "More" menu follows the same dismissal behavior as Agent Settings.
// Keep its native <details> toggle (including repeated-summary clicks), while
// adding outside-click, Escape, and peer-menu dismissal. In focus mode this
// <details> is intentionally kept open to expose the toolbar actions inline.
(()=>{
 const details=$('topMoreMenu');
 const summary=details?.querySelector(':scope > summary');
 const panel=details?.querySelector('.top-more-popover');
 const app=document.querySelector('.app');
 const inFocusMode=()=>!!app?.classList.contains('focus-mode');
 if(!details||!summary||!panel)return;
 document.addEventListener('pointerdown',event=>{
  if(!inFocusMode()&&details.open&&!details.contains(event.target))details.open=false;
 });
 document.addEventListener('keydown',event=>{
  if(event.key==='Escape'&&!inFocusMode()&&details.open){
   details.open=false;
   summary.focus({preventScroll:true});
  }
 });
 panel.addEventListener('click',event=>{
  if(!inFocusMode()&&event.target.closest('button'))details.open=false;
 });
 details.addEventListener('toggle',()=>{
  const agentSettings=$('agentSettingsMenu');
  if(details.open&&!inFocusMode()&&agentSettings?.open)agentSettings.open=false;
 });
})();
$('agentSettingsSave')?.addEventListener('click',async()=>{
 const payload={
  context_limit:Number($('agentContextLimit').value),
  max_tool_rounds:Number($('agentToolRounds').value),
  max_tool_calls:Number($('agentToolCalls').value),
  temperature:Number($('agentTemperature').value),
  request_timeout:Number($('agentTimeout').value)
 };
 const b=$('agentSettingsSave');b.disabled=true;
 try{payload.default_project_id=$('agentDefaultProject').value?Number($('agentDefaultProject').value):null;const saved=await api('/api/settings/agent',{method:'PUT',body:JSON.stringify(payload)});await fillAgentSettings(saved);$('agentSettingsStatus').textContent='Сохранено. Проект по умолчанию будет использоваться при следующем запуске без сохранённого выбора.';toast('Настройки агента сохранены')}
 catch(e){$('agentSettingsStatus').textContent='Ошибка сохранения: '+e.message;toast(e.message)}
 finally{b.disabled=false}
});
$('agentSettingsReset')?.addEventListener('click',()=>{fillAgentSettings(AGENT_DEFAULTS);$('agentSettingsStatus').textContent='Выбраны значения по умолчанию. Нажми «Сохранить», чтобы применить.'});

document.addEventListener('visibilitychange',()=>{
 if(document.visibilityState!=='visible'||!activeBranch)return;
 const branch=Number(activeBranch);
 // One immediate refresh on return; the in-flight guard prevents overlap.
 if(!statsPollBusy){statsPollLastAt=Date.now();statsPollBusy=true;loadStats(branch).catch(e=>console.warn('Не удалось синхронизировать статистику контекста:',e)).finally(()=>{statsPollBusy=false})}
 pollChatActivity(branch);
});
window.addEventListener('pageshow',()=>{
 if(document.visibilityState==='visible'&&activeBranch){
  const branch=Number(activeBranch);
  if(!statsPollBusy){statsPollLastAt=Date.now();statsPollBusy=true;loadStats(branch).catch(e=>console.warn('Не удалось восстановить статистику контекста:',e)).finally(()=>{statsPollBusy=false})}
  pollChatActivity(branch);
 }
});
init();
loadAgentSettings();

// Resizable workspace columns. Persist user widths, but let focus/hidden-panel CSS states own the grid.
(()=>{
 const app=document.querySelector('.app');if(!app)return;
 const read=()=>{try{return JSON.parse(localStorage.getItem('sergdata-layout')||'{}')}catch{return {}}};
 const saved=read();
 let left=Math.max(190,Math.min(420,Number(saved.left)||260));
 let right=Math.max(220,Math.min(460,Number(saved.right)||290));
 const clampLayout=()=>{
   const width=app.clientWidth||innerWidth;
   // CSS collapses side panels at narrow widths; retain their saved widths.
   if(width<=1050)return;
   const centerMin=520, handles=12;
   const sideBudget=Math.max(0,width-centerMin-handles);
   const leftMin=width>1050?190:0, rightMin=width>1050?220:0;
   left=Math.max(leftMin,Math.min(420,left,Math.max(leftMin,sideBudget-rightMin)));
   right=Math.max(rightMin,Math.min(460,right,Math.max(rightMin,sideBudget-left)));
 };
 const apply=()=>{
   clampLayout();
   app.style.setProperty('--wb-left-width',`${left}px`);
   app.style.setProperty('--wb-right-width',`${right}px`);
 };
 const persist=()=>{try{localStorage.setItem('sergdata-layout',JSON.stringify({left,right,version:3}))}catch(e){console.warn('Не удалось сохранить размеры панелей',e)}};
 apply();
 window.addEventListener('resize',apply,{passive:true});
 document.querySelectorAll('.resize-handle').forEach(h=>{
   h.addEventListener('pointerdown',e=>{
     if(innerWidth<=1050||app.classList.contains('focus-mode'))return;
     const side=h.dataset.resize;
     if((side==='left'&&app.classList.contains('hide-sidebar'))||(side==='right'&&app.classList.contains('hide-inspector')))return;
     e.preventDefault();
     try{h.setPointerCapture(e.pointerId)}catch{}
     const move=ev=>{
       if(side==='left')left=Math.max(190,Math.min(420,ev.clientX));
       else right=Math.max(220,Math.min(460,innerWidth-ev.clientX));
       apply();
     };
     const finish=()=>{
       try{h.releasePointerCapture(e.pointerId)}catch{}
       persist();
       h.removeEventListener('pointermove',move);
       h.removeEventListener('pointerup',finish);
       h.removeEventListener('pointercancel',finish);
     };
     h.addEventListener('pointermove',move);
     h.addEventListener('pointerup',finish);
     h.addEventListener('pointercancel',finish);
   });
 });
})();

// Persistable workspace controls and collapsible information blocks.
(()=>{
 const app=document.querySelector('.app'); if(!app)return;
 let prefs={};try{prefs=JSON.parse(localStorage.getItem('sergdata-workspace-prefs')||'{}')}catch{}
 const save=()=>{try{localStorage.setItem('sergdata-workspace-prefs',JSON.stringify({...prefs,version:2}))}catch(e){console.warn('Не удалось сохранить настройки интерфейса',e)}};
 // Inspector cards collapse independently; content remains mounted and state is preserved.
 document.querySelectorAll('.inspector .panel').forEach((panel,i)=>{
   const title=panel.querySelector('.panel-title'); if(!title)return;
   const key='panel_'+i; if(prefs[key])panel.classList.add('is-collapsed');
   const bar=document.createElement('div');bar.className='panel-titlebar';
   title.parentNode.insertBefore(bar,title);bar.appendChild(title);
   const b=document.createElement('button');b.type='button';b.className='ghost panel-collapse';b.textContent=panel.classList.contains('is-collapsed')?'Развернуть':'Свернуть';
   b.addEventListener('click',()=>{panel.classList.toggle('is-collapsed');prefs[key]=panel.classList.contains('is-collapsed');b.textContent=prefs[key]?'Развернуть':'Свернуть';save()});bar.appendChild(b);
 });
 const ep=document.getElementById('executionPanel'), eb=document.querySelector('[data-collapse="executionBody"]');
 if(ep&&eb){
   const msg=document.getElementById('messages');
   const readVertical=()=>{try{return JSON.parse(localStorage.getItem('sergdata-layout-vertical')||'{}')}catch{return {}}};
   if(prefs.executionCollapsed)ep.classList.add('is-collapsed');
   const collapsed=()=>ep.classList.contains('is-collapsed');
   const applyVertical=()=>{
     const v=readVertical();
     if(collapsed()){
       // A collapsed terminal must release all remaining height to the message list.
       msg.style.flex='1 1 0px'; msg.style.maxHeight='none';
       ep.style.flex='0 0 42px';
     }else{
       msg.style.maxHeight='none';
       msg.style.flex=v.messages?`0 0 ${v.messages}px`:'1 1 0px';
       ep.style.flex=v.terminal?`0 1 ${v.terminal}px`:'0 1 auto';
     }
   };
   eb.textContent=collapsed()?'Развернуть':'Свернуть';
   applyVertical();
   eb.onclick=()=>{
     ep.classList.toggle('is-collapsed');
     prefs.executionCollapsed=collapsed();
     eb.textContent=collapsed()?'Развернуть':'Свернуть';
     applyVertical(); save();
     requestAnimationFrame(()=>window.dispatchEvent(new Event('resize')));
   };
 }
 const at=document.getElementById('attachmentTools');if(at){at.open=!!prefs.attachmentsOpen;at.addEventListener('toggle',()=>{prefs.attachmentsOpen=at.open;save()})}
 const focus=document.getElementById('focusMode');const topMore=document.getElementById('topMoreMenu');if(focus){if(prefs.focus){app.classList.add('focus-mode');if(topMore)topMore.open=true}focus.textContent=prefs.focus?'Вернуть панели':'Фокус';focus.onclick=()=>{prefs.focus=!prefs.focus;app.classList.toggle('focus-mode',prefs.focus);if(topMore)topMore.open=!!prefs.focus;focus.textContent=prefs.focus?'Вернуть панели':'Фокус';save();requestAnimationFrame(()=>window.dispatchEvent(new Event('resize')))}}
 const inspector=document.getElementById('toggleInspector');if(inspector){if(prefs.hideInspector)app.classList.add('hide-inspector');inspector.onclick=()=>{prefs.hideInspector=!prefs.hideInspector;app.classList.toggle('hide-inspector',prefs.hideInspector);inspector.textContent=prefs.hideInspector?'Показать инфо':'Инфо';save()};inspector.textContent=prefs.hideInspector?'Показать инфо':'Инфо'}
})();

async function loadProjectSettings(){if(!activeProject)return;try{const x=await api(`/api/projects/${activeProject.id}/settings`);$('autonomySelect').value=x.autonomy||'analysis'}catch(e){console.warn(e)}}
$('autonomySelect')?.addEventListener('change',async e=>{if(!activeProject)return;try{await api(`/api/projects/${activeProject.id}/settings`,{method:'PUT',body:JSON.stringify({autonomy:e.target.value})});toast('Уровень автономности сохранён для проекта')}catch(err){toast(err.message);await loadProjectSettings()}});

// Drag handles for vertical work-area sizing.
// The selected splitter controls its adjacent panel; the other content panel
// absorbs the remaining space. This keeps both splitters usable independently
// without allowing the composer to be pushed out of the chat viewport.
(()=>{
 const chat=document.getElementById('chat'); if(!chat)return;
 let pref={}; try{pref=JSON.parse(localStorage.getItem('sergdata-layout-vertical')||'{}')}catch{}
 const msg=document.getElementById('messages');
 const pending=document.getElementById('pending');
 const term=document.getElementById('executionPanel');
 const composer=document.getElementById('composer');
 if(!msg||!term||!composer)return;
 // Migrate earlier layouts that stored both sizes but had no active-panel field.
 let active=['messages','terminal'].includes(pref.active)?pref.active:(pref.terminal?'terminal':pref.messages?'messages':'');
 const isCollapsed=()=>term.classList.contains('is-collapsed');
 const save=()=>{try{pref.active=active;localStorage.setItem('sergdata-layout-vertical',JSON.stringify(pref))}catch(e){console.warn('Не удалось сохранить высоту панелей',e)}};
 const visibleHeight=el=>el&&!el.classList.contains('hidden')?el.getBoundingClientRect().height:0;
 const panelBudget=()=>{
  const chatHeight=chat.clientHeight;
  if(!chatHeight)return 0;
  const handles=Array.from(chat.querySelectorAll('.v-resize')).reduce((sum,h)=>sum+visibleHeight(h),0);
  return Math.max(0,chatHeight-visibleHeight(composer)-visibleHeight(pending)-handles);
 };
 const minHeight=(kind,budget)=>kind==='messages'?Math.min(120,budget*.45):Math.min(110,budget*.4);
 const clamp=(kind,value)=>{
  const budget=panelBudget();
  if(!budget)return Math.max(kind==='messages'?120:110,Math.round(Number(value)||0));
  const minimum=minHeight(kind,budget);
  const otherMinimum=minHeight(kind==='messages'?'terminal':'messages',budget);
  const maximum=Math.max(minimum,budget-otherMinimum);
  return Math.round(Math.max(minimum,Math.min(maximum,Number(value)||minimum)));
 };
 const apply=()=>{
  if(!chat.clientHeight)return;
  if(isCollapsed()){
   msg.style.flex='1 1 0px';msg.style.maxHeight='none';
   term.style.flex='0 0 42px';term.style.height='42px';term.style.maxHeight='42px';
   return;
  }
  term.style.height='auto';term.style.maxHeight='none';
  msg.style.maxHeight='none';
  if(active==='messages'&&Number(pref.messages)>0){
   const size=clamp('messages',pref.messages);
   msg.style.flex=`0 0 ${size}px`;
   term.style.flex='1 1 0px';
  }else if(active==='terminal'&&Number(pref.terminal)>0){
   const size=clamp('terminal',pref.terminal);
   msg.style.flex='1 1 0px';
   term.style.flex=`0 0 ${size}px`;
  }else{
   msg.style.flex='1 1 0px';
   term.style.flex='0 1 auto';
  }
 };
 apply();
 document.querySelectorAll('[data-vresize]').forEach(handle=>{
  handle.setAttribute('tabindex','0');
  handle.setAttribute('aria-orientation','horizontal');
  handle.addEventListener('pointerdown',event=>{
   const kind=handle.dataset.vresize;
   if(isCollapsed()&&kind==='terminal')return;
   if(event.button!==undefined&&event.button!==0)return;
   event.preventDefault();
   const target=kind==='messages'?msg:term;
   const startY=event.clientY;
   const startHeight=target.getBoundingClientRect().height;
   const previousSelect=document.body.style.userSelect;
   document.body.style.userSelect='none';
   handle.classList.add('is-dragging');
   try{handle.setPointerCapture(event.pointerId)}catch{}
   const move=ev=>{
    if(ev.pointerId!==undefined&&event.pointerId!==undefined&&ev.pointerId!==event.pointerId)return;
    const next=clamp(kind,startHeight+(ev.clientY-startY));
    target.style.maxHeight='none';
    target.style.flex=`0 0 ${next}px`;
    if(kind==='terminal')target.style.height='auto';
   };
   const finish=()=>{
    const finalHeight=Math.round(target.getBoundingClientRect().height);
    active=kind;
    pref[kind]=clamp(kind,finalHeight);
    save();
    document.body.style.userSelect=previousSelect;
    handle.classList.remove('is-dragging');
    window.removeEventListener('pointermove',move);
    window.removeEventListener('pointerup',finish);
    window.removeEventListener('pointercancel',finish);
    try{handle.releasePointerCapture(event.pointerId)}catch{}
    apply();
   };
   window.addEventListener('pointermove',move,{passive:false});
   window.addEventListener('pointerup',finish,{once:true});
   window.addEventListener('pointercancel',finish,{once:true});
  });
  handle.addEventListener('keydown',event=>{
   if(!['ArrowUp','ArrowDown'].includes(event.key)||isCollapsed()&&handle.dataset.vresize==='terminal')return;
   event.preventDefault();
   const kind=handle.dataset.vresize,target=kind==='messages'?msg:term;
   const direction=event.key==='ArrowDown'?1:-1;
   const next=clamp(kind,target.getBoundingClientRect().height+direction*24);
   active=kind;pref[kind]=next;save();apply();
  });
 });
 if(typeof ResizeObserver!=='undefined'){
  const observer=new ResizeObserver(()=>apply());
  observer.observe(chat);
 }
 // Also listen for the existing layout's synthetic resize event (collapse/focus controls).
 window.addEventListener('resize',apply,{passive:true});
})();
// Global interface preferences: language and color theme are independent of project data.
(()=>{
 const root=document.documentElement, langSelect=document.getElementById('uiLanguage'), themeButton=document.getElementById('uiTheme');
 if(!langSelect||!themeButton)return;
 const key='sergdata-ui-preferences-v1';
 let pref={};try{pref=JSON.parse(localStorage.getItem(key)||'{}')}catch{}
 const dict={
  'Основная':'Main','База знаний':'Knowledge Base','Переименовать задачу':'Rename task','Удалить задачу':'Delete task','Переименовать ветку':'Rename branch','Удалить ветку':'Delete branch','Сохранить точку':'Save checkpoint','Экспорт контекста':'Export context','Продолжить в новой задаче ↗':'Continue in new task ↗','Импорт контекста':'Import context','Обзор…':'Browse…','Папка…':'Folder…','Файл…':'File…','Добавить проект':'Add project','Название проекта':'Project name','Папка проекта':'Project folder','Добавить проект':'Add project','Отмена':'Cancel','Выбери папку':'Choose folder','Индексировать':'Index','Обновить статус':'Refresh status','Закрыть':'Close','Путь к файлу или папке внутри AI-Knowledge':'Path to a file or folder inside AI-Knowledge','Можно указать отдельную папку или файл. Индексатор обработает только выбранный источник. Путь должен находиться внутри каталога базы знаний.':'You can select an individual folder or file. Only the selected source will be indexed. The path must be inside the Knowledge Base directory.','Проверка подключения…':'Checking connection…','Индексация запущена…':'Indexing started…',
  'ПРОЕКТЫ':'PROJECTS','Имя':'Name','Загрузка…':'Loading…','Автономность проекта':'Project autonomy','Анализ':'Analysis','Разработка':'Development','Расширенная':'Full','＋ Новая задача':'＋ New task','ЗАДАЧИ':'TASKS','Выберите задачу':'Select a task','Создайте задачу, чтобы начать':'Create a task to get started','Настройки агента':'Agent settings','По умолчанию':'Defaults','Сохранить':'Save','Фокус':'Focus','Вернуть панели':'Show panels','Показать инфо':'Show info','Инфо':'Info','Ветка':'Branch','＋ Ветка':'＋ Branch','Имя ветки':'Rename branch','Удалить ветку':'Delete branch','Переименовать':'Rename','Удалить':'Delete','Сохранить точку':'Save checkpoint','Экспорт контекста':'Export context','Продолжить в новой задаче ↗':'Continue in new task ↗','Импорт контекста':'Import context','Рабочее пространство локального ИИ':'Local AI workspace','Выберите проект, создайте задачу и работайте с локальной моделью. История, ветки и контрольные точки сохраняются отдельно.':'Choose a project, create a task, and work with your local model. History, branches, and checkpoints are stored separately.','Создать первую задачу':'Create first task','Локальное выполнение · PowerShell':'Local execution · PowerShell','Свернуть':'Collapse','Развернуть':'Expand','Команды модели выполняются только после подтверждения. Запуск от имени текущего пользователя, без повышения прав; рабочая папка — корень выбранного проекта.':'Model commands run only after confirmation, as the current user without elevation. Working directory is the selected project root.','Подготовить команду':'Prepare command','Обновить очередь':'Refresh queue','Вложения и дополнительные параметры':'Attachments and options','＋ Прикрепить файлы':'＋ Attach files','Только эта ветка':'This branch only','Вся задача':'Entire task','Весь проект':'Entire project','До 20 МБ на файл · ZIP, PDF, DOCX, код и текст':'Up to 20 MB per file · ZIP, PDF, DOCX, code and text','Контекст':'Context','Отправить ↑':'Send ↑','Модель работает через LM Studio Local Server':'Model runs through LM Studio Local Server','КОНТЕКСТ И СТАТИСТИКА':'CONTEXT & STATISTICS','Текущая ветка':'Current branch','Сообщений':'Messages','В контексте':'In context','Свободно':'Remaining','Подробная статистика токенов и API':'Detailed token and API statistics','Память задачи':'Task memory','Сохранить память задачи':'Save task memory','Память проекта':'Project memory','Сохранить память проекта':'Save project memory','Git · контроль изменений':'Git · change control','Проверка…':'Checking…','Обновить Git':'Refresh Git','Показать diff':'Show diff','Файлы проекта':'Project files','Загрузка…':'Loading…','Обновить список':'Refresh list','Вложения проекта / задачи':'Project / task attachments','Поиск по вложениям…':'Search attachments…','Найти':'Search','Пока нет загруженных файлов':'No uploaded files yet','Модель':'Model','Подключение: OpenAI-compatible API':'Connection: OpenAI-compatible API','Продолжить в новой задаче':'Continue in new task','Выбери объём контекста. Исходная задача и её история останутся без изменений.':'Choose how much context to transfer. The original task and its history will remain unchanged.','Что переносить':'What to transfer','Только текущую ветку — минимальный контекст':'Current branch only — minimal context','Всю задачу — память и сведения всех её веток':'Entire task — memory and information from all its branches','Текущую задачу + важный контекст всего проекта':'Current task + important project context','Название новой задачи':'New task name','Отмена':'Cancel','Сформировать и продолжить':'Prepare and continue','Импорт контекста':'Import context','Вставь пакет экспорта Workbench или загрузи Markdown/TXT. Контекст попадёт в постоянную память и будет использоваться моделью.':'Paste a Workbench export package or upload Markdown/TXT. The context will be saved and used by the model.','Куда импортировать':'Import into','Новая ветка текущей задачи':'New branch in current task','В текущую ветку':'Current branch','Новая задача в текущем проекте':'New task in current project','Импортированный контекст':'Imported context','Файл контекста (необязательно)':'Context file (optional)','Текст контекста':'Context text','Импортировать':'Import'
 };
 const translateText=(node,lang)=>{if(node.nodeType!==Node.TEXT_NODE)return;const raw=node.nodeValue;if(!raw||!raw.trim())return;const lead=raw.match(/^\s*/)?.[0]||'',trail=raw.match(/\s*$/)?.[0]||'',value=raw.trim();if(lang==='en'&&dict[value])node.nodeValue=lead+dict[value]+trail;else if(lang==='ru'){const reverse=reverseDict[value];if(reverse)node.nodeValue=lead+reverse+trail;}};
 const reverseDict=Object.fromEntries(Object.entries(dict).map(([a,b])=>[b,a]));
 const applyLanguage=lang=>{
  document.documentElement.lang=lang;
  document.querySelectorAll('body *').forEach(el=>{for(const n of el.childNodes)if(n.nodeType===Node.TEXT_NODE)translateText(n,lang)});
  document.querySelectorAll('[placeholder]').forEach(el=>{const original=el.dataset.ruPlaceholder||el.getAttribute('placeholder');if(!el.dataset.ruPlaceholder)el.dataset.ruPlaceholder=original;if(lang==='en'&&dict[original])el.setAttribute('placeholder',dict[original]);else if(lang==='ru')el.setAttribute('placeholder',original)});
  document.querySelectorAll('[title],[aria-label]').forEach(el=>['title','aria-label'].forEach(attr=>{const original=el.dataset['ru'+attr.replace('-','').replace(/^./,c=>c.toUpperCase())]||el.getAttribute(attr);const dataKey='ru'+attr.replace('-','').replace(/^./,c=>c.toUpperCase());if(!el.dataset[dataKey])el.dataset[dataKey]=original;if(lang==='en'&&dict[original])el.setAttribute(attr,dict[original]);else if(lang==='ru'&&el.dataset[dataKey])el.setAttribute(attr,el.dataset[dataKey])}));
  langSelect.value=lang;pref.language=lang;persist();if(pref.theme)applyTheme(pref.theme);
 };
 const persist=()=>{try{localStorage.setItem(key,JSON.stringify(pref))}catch{}};
 const applyTheme=theme=>{root.dataset.theme=theme;root.style.colorScheme=theme;const en=(pref.language||'ru')==='en';themeButton.textContent=theme==='light'?(en?'☾ Dark':'☾ Тёмная'):(en?'☀ Light':'☀ Светлая');themeButton.title=theme==='light'?(en?'Switch to dark theme':'Переключить на тёмную тему'):(en?'Switch to light theme':'Переключить на светлую тему');themeButton.setAttribute('aria-label',themeButton.title);pref.theme=theme;persist()};
 langSelect.addEventListener('change',()=>applyLanguage(langSelect.value));
 themeButton.addEventListener('click',()=>applyTheme(root.dataset.theme==='light'?'dark':'light'));
 applyTheme(pref.theme==='light'?'light':'dark');applyLanguage(pref.language==='en'?'en':'ru');
 // Translate newly rendered interface labels too; user/model message content is intentionally untouched unless it exactly matches a UI label.
 const observer=new MutationObserver(records=>{const lang=pref.language||'ru';for(const r of records){for(const n of r.addedNodes){if(n.nodeType===Node.TEXT_NODE)translateText(n,lang);else if(n.nodeType===Node.ELEMENT_NODE){for(const el of [n,...n.querySelectorAll('*')])for(const child of el.childNodes)if(child.nodeType===Node.TEXT_NODE)translateText(child,lang)}}}});
 observer.observe(document.body,{childList:true,subtree:true});
})();

// Universal, safe native tooltips for static and dynamically rendered controls.
// Any accidental "null"/"undefined" title is replaced with a useful description.
(()=>{
 const descriptions={
  renameProject:'Переименовать выбранный проект',
  archiveProject:'Убрать проект из списка. Файлы и история останутся на диске',
  newProject:'Добавить существующую папку как проект',
  newTask:'Создать задачу в выбранном проекте',
  welcomeNew:'Создать первую задачу в выбранном проекте',
  focusMode:'Скрыть второстепенные панели и сосредоточиться на рабочей области',
  toggleInspector:'Показать или скрыть правую информационную панель',
  branchSelect:'Выбрать ветку текущей задачи',
  newBranch:'Создать новую ветку текущей задачи',
  renameBranch:'Переименовать текущую ветку',
  deleteBranch:'Удалить текущую ветку',
  renameTask:'Переименовать текущую задачу',
  deleteTask:'Удалить задачу вместе с её ветками и перепиской',
  checkpoint:'Сохранить контрольную точку текущей ветки',
  exportCheckpoint:'Экспортировать контекст для переноса в другую задачу или Workbench',
  continueNewTask:'Создать новую задачу и перенести выбранный контекст',
  importCheckpoint:'Импортировать ранее сохранённый контекст',
  agentSettingsMenu:'Настроить поведение агента и параметры рабочего окружения',
  agentDefaultProject:'Проект, который будет выбран автоматически при запуске Workbench',
  agentContextLimit:'Максимальный размер контекста модели',
  agentToolRounds:'Максимальное число этапов работы модели за один запрос',
  agentToolCalls:'Максимальное число вызовов инструментов за один запрос',
  agentTemperature:'Управляет вариативностью ответов модели',
  agentTimeout:'Максимальное время ожидания ответа модели',
  agentSettingsReset:'Вернуть настройки агента к стандартным значениям',
  agentSettingsSave:'Сохранить настройки агента',
  refreshGit:'Обновить состояние Git и список изменений',
  showDiff:'Показать изменения относительно последнего коммита',
  gitStage:'Добавить выбранные файлы в подготовленную область Git',
  gitUnstage:'Убрать выбранные файлы из подготовленной области Git',
  gitCommit:'Создать локальный коммит из подготовленных файлов',
  gitHistory:'Показать историю локальных коммитов',
  gitRemoteSave:'Подключить или изменить удалённый репозиторий origin',
  gitFetch:'Получить сведения об обновлениях с удалённого репозитория без изменения файлов',
  gitPull:'Получить изменения из удалённого репозитория в текущую ветку',
  gitPush:'Отправить локальные коммиты в удалённый репозиторий',
  refreshFiles:'Обновить список файлов выбранного проекта',
  openProjectFile:'Открыть файл проекта в просмотрщике',
  copyProjectFile:'Скопировать содержимое открытого файла',
  attachFiles:'Прикрепить файлы к сообщению',
  send:'Отправить сообщение модели',
  runTerminal:'Подготовить команду для выполнения после проверки',
  refreshExecution:'Обновить очередь команд',
  stopLiveProcess:'Остановить текущий процесс',
  saveTaskMemory:'Сохранить память текущей задачи',
  saveProjectMemory:'Сохранить постоянную память проекта',
  uiLanguage:'Выбрать язык интерфейса',
  uiTheme:'Переключить светлую или тёмную тему'
 };
 const bad=v=>!v||/^(null|undefined|none|n\/a)$/i.test(String(v).trim());
 const describe=el=>{
  if(descriptions[el.id])return descriptions[el.id];
  const explicit=el.getAttribute('data-tooltip')||el.getAttribute('aria-label');
  if(!bad(explicit))return explicit.trim();
  const label=el.labels&&el.labels.length?el.labels[0].textContent:'';
  if(!bad(label))return label.trim().replace(/\s+/g,' ');
  const placeholder=el.getAttribute('placeholder');
  if(!bad(placeholder))return placeholder.trim();
  const text=(el.innerText||el.textContent||'').trim().replace(/\s+/g,' ');
  if(!bad(text)&&text.length<=100)return text;
  if(el.matches('input[type="file"]'))return 'Выбрать файл';
  if(el.matches('input[type="checkbox"],input[type="radio"]'))return 'Изменить параметр';
  if(el.matches('select'))return 'Выбрать значение';
  if(el.matches('textarea'))return 'Поле ввода текста';
  return '';
 };
 const enhance=scope=>{
  const nodes=[];
  if(scope.nodeType===Node.ELEMENT_NODE&&scope.matches('button,select,input,textarea,summary,[role="button"],[role="switch"],[data-action],[data-file-path],[data-collapse],[data-resize],[data-vresize]'))nodes.push(scope);
  if(scope.querySelectorAll)nodes.push(...scope.querySelectorAll('button,select,input,textarea,summary,[role="button"],[role="switch"],[data-action],[data-file-path],[data-collapse],[data-resize],[data-vresize]'));
  for(const el of nodes){
   const current=el.getAttribute('title');
   if(!bad(current))continue;
   const tip=describe(el);
   if(tip)el.setAttribute('title',tip);
   else if(current!==null)el.removeAttribute('title');
  }
 };
 enhance(document.body);
 const observer=new MutationObserver(records=>{
  for(const record of records){
   if(record.type==='childList')record.addedNodes.forEach(n=>{if(n.nodeType===Node.ELEMENT_NODE)enhance(n)});
   else if(record.type==='attributes')enhance(record.target);
  }
 });
 observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['title','aria-label','data-tooltip']});
})();


// Git Doctor: диагностика, просмотр и безопасный карантин неотслеживаемых файлов.
(()=>{
 const $=id=>document.getElementById(id);
 const open=$('knowledgeGitDoctorOpen'),panel=$('knowledgeGitDoctorPanel');
 if(!open||!panel)return;
 const select=$('knowledgeGitDoctorRepo'),output=$('knowledgeGitDoctorOutput'),run=$('knowledgeGitDoctorRun'),actions=$('knowledgeGitDoctorActions'),update=$('knowledgeGitDoctorUpdate');
 let lastInspection=null;
 async function post(url,payload){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Ошибка запроса');return d;}
 async function inspect(){if(!select.value)return;run.disabled=true;actions.replaceChildren();output.textContent='Проверяю Git…';
  try{const d=await post('/api/knowledge/git-doctor/inspect',{name:select.value});lastInspection=d;
   update.hidden=!(d.clean && d.upstream && Number(d.behind)>0);update.disabled=false;
   const lines=[`Репозиторий: ${d.name}`,`Путь: ${d.path}`,`Ветка: ${d.branch||'(detached)'}`,`Upstream: ${d.upstream||'(не настроен)'}`,`HEAD: ${d.head}`,`Локальных коммитов впереди: ${d.ahead??'—'}`,`Удалённых коммитов впереди: ${d.behind??'—'}`,`Состояние: ${d.clean?'чистое':'есть изменения'}`,`Записей: ${d.status_count??0}`,d.message,''];
   const labels={untracked:'Неотслеживаемый файл',tracked:'Отслеживаемое изменение',renamed_or_copied:'Переименование/копирование',unmerged:'Конфликт'};
   if(d.records?.length){lines.push('СОСТОЯНИЕ РАБОЧЕЙ КОПИИ:');for(const x of d.records)lines.push(`• ${labels[x.state]||x.state}${x.xy?' ['+x.xy+']':''}: ${x.path}`)}else lines.push('Рабочая копия без изменений.');
   if(d.issues?.length){lines.push('','ТРЕБУЮТ ВНИМАНИЯ:');for(const x of d.issues){const names={merge_conflict:'КОНФЛИКТ',deletion_status_review:'УДАЛЕНИЕ — проверить',suspicious_untracked_name:'ПОДОЗРИТЕЛЬНОЕ ИМЯ ФАЙЛА'};lines.push(`⚠ ${names[x.kind]||x.kind}: ${x.path}`)}}
   lines.push('','Fetch/merge не запускались. Файлы не изменялись.');output.textContent=lines.join('\n');
   try{const qr=await fetch('/api/knowledge/git-doctor/quarantine/'+encodeURIComponent(d.name));const qd=await qr.json();if(qr.ok&&qd.items?.length){const restoreRow=document.createElement('div');restoreRow.className='knowledge-doctor-controls';const restoreLabel=document.createElement('span');restoreLabel.textContent=`В карантине: ${qd.items.length}`;restoreLabel.style.flex='1';restoreRow.append(restoreLabel);const restoreBtn=document.createElement('button');restoreBtn.type='button';restoreBtn.className='ghost';restoreBtn.textContent='Восстановить последний';restoreBtn.addEventListener('click',async()=>{const item=qd.items[0];if(!confirm(`Восстановить файл?\n${item.path}\n\nЕсли исходный путь занят, восстановление будет отменено.`))return;restoreBtn.disabled=true;try{const rr=await post('/api/knowledge/git-doctor/restore',{name:d.name,quarantine_id:item.quarantine_id});output.textContent=rr.message+': '+rr.path;await inspect();}catch(e){output.textContent='Ошибка восстановления: '+e.message;restoreBtn.disabled=false;}});restoreRow.append(restoreBtn);actions.append(restoreRow);}}catch{}
   for(const rec of (d.records||[])){
    if(rec.state==='tracked'&&rec.xy==='D.'&&rec.path_raw){
     const row=document.createElement('div');row.className='knowledge-doctor-controls';
     const label=document.createElement('span');label.textContent=`Удалён отслеживаемый файл: ${rec.path}`;label.style.flex='1';row.append(label);
     const restore=document.createElement('button');restore.type='button';restore.className='ghost';restore.textContent='Восстановить из HEAD';restore.addEventListener('click',async()=>{
      if(!confirm(`Восстановить файл из текущего HEAD?\n${rec.path}\n\nБудет отменено только это staged-удаление. Другие изменения не затрагиваются.`))return;
      restore.disabled=true;try{const result=await post('/api/knowledge/git-doctor/restore-tracked-deletion',{name:d.name,path:rec.path_raw});output.textContent=result.message+`\n${result.path}`;await inspect();}catch(e){output.textContent='Ошибка восстановления: '+e.message;restore.disabled=false;}
     });row.append(restore);actions.append(row);
    }
    if(rec.state!=='untracked'||!rec.path_raw)continue;
    const row=document.createElement('div');row.className='knowledge-doctor-controls';
    const label=document.createElement('span');label.textContent=rec.path;label.style.flex='1';row.append(label);
    const view=document.createElement('button');view.type='button';view.className='ghost';view.textContent='Просмотреть';view.addEventListener('click',async()=>{try{const v=await post('/api/knowledge/git-doctor/view',{name:d.name,path:rec.path_raw});output.textContent=`ФАЙЛ: ${v.path}\nРазмер: ${v.size} байт${v.truncated?'\n[Показаны первые 50 000 символов]':''}\n\n${v.content}`;}catch(e){output.textContent='Ошибка просмотра: '+e.message;}});row.append(view);
    const quarantine=document.createElement('button');quarantine.type='button';quarantine.className='ghost';quarantine.textContent='В карантин';quarantine.addEventListener('click',async()=>{if(!confirm(`Переместить в карантин?\n${rec.path}\n\nФайл не удаляется и может быть восстановлен.`))return;quarantine.disabled=true;try{const q=await post('/api/knowledge/git-doctor/quarantine',{name:d.name,path:rec.path_raw});output.textContent=`${q.message}\nПуть: ${q.path}\nID карантина: ${q.quarantine_id}\n\nЗапусти повторную диагностику, затем полную синхронизацию.`;await inspect();}catch(e){output.textContent='Ошибка карантина: '+e.message;quarantine.disabled=false;}});row.append(quarantine);actions.append(row);
   }
  }catch(e){output.textContent='Ошибка: '+e.message;}finally{run.disabled=false;}
 }
 update?.addEventListener('click',async()=>{
  if(!lastInspection||!select.value)return;
  const d=lastInspection;
  const ahead=Number(d.ahead)||0,behind=Number(d.behind)||0;
  const warning=ahead
   ? `\n\nВНИМАНИЕ: ${ahead} локальных коммит(а) будут сохранены в отдельной резервной ссылке Git, а активная ветка перейдёт на upstream. Локальные коммиты не попадут в обновлённую ветку автоматически, но останутся доступными для восстановления.`
   : '';
  if(!confirm(`Обновить ${d.name} до ${d.upstream}?\nУдалённых коммитов впереди: ${behind}.${warning}\n\nРабочая копия должна быть чистой. Неотслеживаемые файлы не удаляются.`))return;
  update.disabled=true;output.textContent='Выполняю fetch и безопасное обновление…';
  try{const result=await post('/api/knowledge/git-doctor/update-upstream',{name:select.value});
   output.textContent=`${result.message}\nВетка: ${result.branch}\nНовый HEAD: ${result.new_head||'(без изменений)'}\nЛокальных коммитов до обновления: ${result.ahead_before??result.ahead??0}\nУдалённых коммитов до обновления: ${result.behind_before??result.behind??0}\nРезервная ссылка локальной истории: ${result.backup_ref||'не требовалась'}\nФайлов для точечной индексации: ${result.indexed_paths??0}\nУдалённых путей: ${result.deleted_paths??0}\n\nТеперь запусти «Git + Releases + полная индексация», чтобы обновить индекс по сохранённому манифесту.`;
   await inspect();
  }catch(e){output.textContent='Обновление не выполнено: '+e.message+'\nПроверь состояние репозитория повторной диагностикой.';update.disabled=false;}
 });
 open.addEventListener('click',async()=>{panel.hidden=false;output.textContent='Загружаю локальные клоны…';run.disabled=true;
  try{const r=await fetch('/api/knowledge/git-doctor/repositories',{cache:'no-store'});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Ошибка списка');select.replaceChildren();for(const repo of (d.repositories||[])){const o=document.createElement('option');o.value=repo.name;o.textContent=repo.name;select.append(o)}if(!select.options.length){const o=document.createElement('option');o.value='';o.textContent='Локальные клоны не найдены';select.append(o);output.textContent='В repositories.json нет обнаруженных локальных клонов в AI-Knowledge/code.'}else{run.disabled=false;output.textContent='Выбери репозиторий и нажми «Проверить».'}}
  catch(e){output.textContent='Ошибка: '+e.message;}
 });
 $('knowledgeGitDoctorClose')?.addEventListener('click',()=>{panel.hidden=true});
 run.addEventListener('click',inspect);
})();

// Optional AI-Knowledge controls. This UI is additive; chat/MCP behavior is unchanged.
(()=> {
 const $ = id => document.getElementById(id);
 const open=$('knowledgeOpen'), dialog=$('knowledgeDialog');
 if(!open||!dialog)return;
 async function refresh(){
  const status=$('knowledgeStatus'), output=$('knowledgeOutput'), start=$('knowledgeStart');
  const stop=$('knowledgeStop'), full=$('knowledgeFullUpdate');
  try{
   const r=await fetch('/api/knowledge/status',{cache:'no-store'}); const d=await r.json();
   if(!r.ok)throw new Error(d.detail||'Не удалось получить состояние');
   status.textContent=d.available
    ? `Подключена · ${d.root} · файлов в индексе: ${d.indexed_files??'неизвестно'}`
    : `База знаний не обнаружена или отключена · ${d.root}`;
   const running=!!d.job?.running, stopping=!!d.job?.stop_requested;
   start.disabled=!d.available||running;
   if(stop){stop.hidden=!running;stop.disabled=stopping;stop.textContent=stopping?'Останавливаю…':'Остановить';}
   if(full)full.disabled=!d.available||running;
   output.textContent=running
    ? `${d.job?.phase==='full-update'?'Синхронизация выполняется':'Индексация выполняется'}: ${d.job.source||''}\n${d.job.output||''}`
    : (d.job?.output||'');
   if(d.job?.returncode!==null&&d.job?.returncode!==undefined&&!d.job.running)
    output.textContent+=`\n\nКод завершения: ${d.job.returncode}`;
  }catch(e){status.textContent=`Ошибка: ${e.message}`;start.disabled=true;}
 }
 fetch('/api/knowledge/status').then(r=>r.json()).then(d=>{open.hidden=!d.available}).catch(()=>{open.hidden=true});
 open.addEventListener('click',()=>{dialog.showModal();refresh();refreshKnowledgeSources();if(timer)clearInterval(timer);timer=setInterval(refresh,2000)});
 $('knowledgeClose').addEventListener('click',()=>dialog.close());
 $('knowledgeStop')?.addEventListener('click',async()=>{
  const b=$('knowledgeStop');if(b.disabled)return;
  b.disabled=true;b.textContent='Останавливаю…';
  try{
   const r=await fetch('/api/knowledge/stop',{method:'POST'});
   const d=await r.json();if(!r.ok)throw new Error(d.detail||'Не удалось остановить процесс');
   $('knowledgeOutput').textContent=d.message||'Запрос остановки отправлен.';
  }catch(e){$('knowledgeOutput').textContent='Ошибка остановки: '+e.message;b.disabled=false;b.textContent='Остановить';}
  await refresh();
 });

 $('knowledgeRefresh').addEventListener('click',async()=>{await refresh();await refreshKnowledgeSources();});
 $('knowledgeRepos')?.addEventListener('click',async()=>{
  try{
   const r=await fetch('/api/knowledge/repositories');const d=await r.json();if(!r.ok)throw new Error(d.detail||'Ошибка списка');
   const rows=d.repositories||[];
   const listing=rows.length?rows.map(x=>`${x.name} — ${x.url}`).join('\n'):'Список пуст.';
   const action=prompt(`Git-репозитории:\n${listing}\n\nВведите имя нового репозитория для добавления или оставьте пустым для отмены:`);
   if(action===null||!action.trim())return;
   const url=prompt(`URL Git для ${action.trim()}:`);if(!url||!url.trim())return;
   const a=await fetch('/api/knowledge/repositories',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:action.trim(),url:url.trim()})});const result=await a.json();if(!a.ok)throw new Error(result.detail||'Не удалось добавить');
   $('knowledgeOutput').textContent=`Репозиторий добавлен: ${result.repository.name}\nПапка клона не создаётся автоматически. Для клонирования и обновления используйте полный цикл.`;
  }catch(e){$('knowledgeOutput').textContent='Ошибка: '+e.message;}
 });
 async function refreshKnowledgeSources(){
  const host=$('knowledgeSources'); if(!host)return;
  try{
   const r=await fetch('/api/knowledge/sources'); const d=await r.json();
   if(!r.ok)throw new Error(d.detail||'Не удалось получить список источников');
   const rows=Array.isArray(d.sources)?d.sources:[]; host.replaceChildren();
   const heading=document.createElement('div'); heading.className='muted small'; heading.textContent=`Внешние источники: ${rows.length}`; host.append(heading);
   if(!rows.length){const empty=document.createElement('div');empty.className='muted small';empty.textContent='Внешние источники ещё не добавлены.';host.append(empty);return;}
   for(const source of rows){
    const row=document.createElement('div');row.className='knowledge-source-row';
    const info=document.createElement('div');info.className='knowledge-source-info';
    const name=document.createElement('strong');name.textContent=source.name||source.id||'Источник';
    const path=document.createElement('small');path.textContent=source.path||'';path.title=source.path||'';info.append(name,path);
    const use=document.createElement('button');use.type='button';use.className='ghost';use.textContent='Выбрать';use.addEventListener('click',()=>{$('knowledgePath').value=source.path||'';});
    const remove=document.createElement('button');remove.type='button';remove.className='ghost';remove.textContent='Убрать';
    remove.addEventListener('click',async()=>{if(!confirm(`Убрать источник «${source.name}» из списка? Файлы и индекс не удаляются.`))return;try{const del=await fetch(`/api/knowledge/sources/${encodeURIComponent(source.id)}`,{method:'DELETE'});const result=await del.json();if(!del.ok)throw new Error(result.detail||'Не удалось удалить запись');$('knowledgeOutput').textContent=result.message||'Запись источника удалена.';await refreshKnowledgeSources();}catch(e){$('knowledgeOutput').textContent='Ошибка: '+e.message;}});
    row.append(info,use,remove);host.append(row);
   }
  }catch(e){host.textContent='Ошибка списка источников: '+e.message;}
 }
 $('knowledgeAddSource')?.addEventListener('click',async()=>{
  // Reuse the path selected with «Папка…». Open the picker only if empty.
  let chosen=$('knowledgePath').value.trim();
  if(!chosen){try{const r=await fetch('/api/local-dialog',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:'folder',title:'Выберите внешний источник'})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Ошибка выбора папки');chosen=d.path||'';}catch(e){$('knowledgeOutput').textContent='Ошибка: '+e.message;return;}}
  if(!chosen)return;
  const name=chosen.replace(/[\\/]+$/,'').split(/[\\/]/).pop(); const button=$('knowledgeAddSource');button.disabled=true;
  try{const r=await fetch('/api/knowledge/sources',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,path:chosen})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Не удалось добавить источник');$('knowledgePath').value=d.source.path;$('knowledgeOutput').textContent=`Внешний источник зарегистрирован: ${d.source.name}\nПуть: ${d.source.path}\nРегистрация не запускает индексацию.`;await refreshKnowledgeSources();}
  catch(e){$('knowledgeOutput').textContent='Ошибка регистрации внешнего источника: '+e.message;}
  finally{button.disabled=false;}
 });
 $('knowledgeFullUpdate')?.addEventListener('click',async()=>{
  if(!confirm('Запустить обновление всех Git-репозиториев, синхронизацию Release Notes и полную индексацию? Операция может занять время.'))return;
  const b=$('knowledgeFullUpdate');b.disabled=true;
  try{const r=await fetch('/api/knowledge/full-update',{method:'POST'});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Не удалось запустить синхронизацию');$('knowledgeOutput').textContent=d.message;await refresh();}
  catch(e){$('knowledgeOutput').textContent='Ошибка: '+e.message;b.disabled=false;}
 });
 async function pickKnowledge(kind){try{const r=await fetch('/api/local-dialog',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind,initialdir:document.getElementById('knowledgePath').value||undefined,title:kind==='folder'?'Выберите папку для индексации':'Выберите файл для индексации'})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Не удалось открыть диалог');if(d.path){const root=(await (await fetch('/api/knowledge/status')).json()).root;let rel=d.path; if(rel.toLowerCase().startsWith(root.toLowerCase()))rel=rel.slice(root.length).replace(/^[\\/]+/,'');document.getElementById('knowledgePath').value=rel||d.path;}}catch(e){$('knowledgeOutput').textContent='Ошибка: '+e.message}}
 $('knowledgeBrowseFolder').addEventListener('click',()=>pickKnowledge('folder'));
 $('knowledgeBrowseFile').addEventListener('click',()=>pickKnowledge('file'));
 $('knowledgeStart').addEventListener('click',async()=>{
  const path=$('knowledgePath').value.trim();
  if(!path){$('knowledgeOutput').textContent='Укажи путь к файлу или папке.';return;}
  const b=$('knowledgeStart');b.disabled=true;
  try{
   const r=await fetch('/api/knowledge/index',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path})});
   const d=await r.json();if(!r.ok)throw new Error(d.detail||'Не удалось запустить индексацию');
   $('knowledgeOutput').textContent=`${d.message}: ${d.source}`;
   await refresh();
  }catch(e){$('knowledgeOutput').textContent=`Ошибка: ${e.message}`;b.disabled=false;}
 });
 let timer=null;
 dialog.addEventListener('close',()=>{if(timer)clearInterval(timer);timer=null});

})();
