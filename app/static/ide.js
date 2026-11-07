'use strict';
let ideStarted=false, ideReady=false, pendingFile='', activeFile='', polling=false;
const argsByFile=new Map();
function ensureIDE() {
  if(ideStarted)return;
  ideStarted=true;
  $('ide-frame').src='/ide/?folder=/home/student/lab';
  $('ide-status').textContent='VS Code 시작 중…';
}
async function ideAction(action, extra={}) {
  const result=await api('/api/ide',{method:'POST',body:JSON.stringify({action,...extra})});
  if(result.error)throw new Error(result.error);
  return result;
}
async function openFile(path) {
  pendingFile=path;switchTab('editor');
  if(ideReady){await ideAction('open',{path});pendingFile='';}
}
function showGuide(path) {
  const guide=exampleGuides[path];$('args-guide').hidden=!guide;$('preset-options').replaceChildren();
  if(!guide)return;
  $('args-description').textContent=guide.desc;
  for(const [args,meaning] of guide.choices){
    const button=document.createElement('button');button.textContent=(args||'(인자 없음)')+' · '+meaning;
    button.onclick=()=>{$('run-args').value=args;argsByFile.set(activeFile,args);$('args-guide').open=false;};
    $('preset-options').append(button);
  }
}
async function pollIDE() {
  if(!ideStarted||polling)return;polling=true;
  try {
    const result=await api('/api/ide');ideReady=result.ready;
    $('ide-status').textContent='● VS Code 연결됨';
    if(result.path!==activeFile){
      argsByFile.set(activeFile,$('run-args').value);activeFile=result.path;
      $('run-args').value=argsByFile.get(activeFile)||'';showGuide(activeFile);
    }
    $('ide-file').textContent=(activeFile||'IDE에서 파일을 선택하거나 새 파일을 만드세요')+(result.dirty?' · 미저장':'');
    if(pendingFile){const file=pendingFile;await ideAction('open',{path:file});if(pendingFile===file)pendingFile='';}
  } catch {ideReady=false;$('ide-status').textContent='VS Code 연결 대기 중…';}
  finally{polling=false;}
}
setInterval(pollIDE,1200);
$('ide-retry').onclick=()=>{ideStarted=false;ensureIDE();};
$('ide-new').onclick=()=>ideAction('new').catch(e=>toast(e.message));
$('save-file').onclick=()=>ideAction('save').then(()=>toast('저장했습니다.')).catch(e=>toast(e.message));
$('build-run').onclick=async()=>{
  try{await ideAction('run',{path:activeFile,args:parseArgs($('run-args').value)});toast('VS Code 터미널에서 빌드와 실행 결과를 확인하세요.');}
  catch(e){toast(e.message);}
};
$('editor-expand').onclick=()=>{
  const expanded=document.body.classList.toggle('ide-expanded');
  $('editor-expand').textContent=expanded?'원래 크기':'최대화';
  $('editor-expand').setAttribute('aria-expanded',String(expanded));
  $('lesson-pane').inert=expanded;
};
window.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.body.classList.contains('ide-expanded'))$('editor-expand').click();});
