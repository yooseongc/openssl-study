'use strict';
const $ = id => document.getElementById(id);
const scrollBehavior = () => matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth';
const modules = ['암호학 기초와 TLS', 'X.509 인증서', 'OpenSSL 3 구조', 'OpenSSL 프로그래밍', 'QUIC: 전송·스트림·이벤트', 'QAT: 암호 연산 가속', '인증서 폐기: CRL·OCSP'];
let lessons = [], current = 0, socket, dirty = false, loadedPath = '', toastTimer;
let progress = {};
try { progress = JSON.parse(localStorage.getItem('openssl-study-progress-v1') || '{}'); } catch { progress = {}; }
const escapeHTML = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const shellQuote = s => "'" + s.replace(/'/g, "'\\''") + "'";
function toast(s) { $('toast').textContent = s; $('toast').classList.add('show'); clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').classList.remove('show'), 4000); }
async function api(path, options = {}) {
  const r = await fetch(path, {...options, headers: {'Content-Type':'application/json', 'X-Study-Request':'1', ...options.headers}});
  if (!r.ok) throw new Error((await r.text()).slice(0, 180));
  return r.json();
}
function done(l) { return progress[l.id]?.completed ?? !!(progress[l.id]?.check && progress[l.id]?.quiz); }
function saveProgress() { try { localStorage.setItem('openssl-study-progress-v1', JSON.stringify(progress)); } catch { toast('브라우저에서 진행 저장이 차단되었습니다.'); } renderNav(); }
function renderNav() {
  const query = ($('lesson-search')?.value || '').toLowerCase();
  $('navigation').innerHTML = modules.map((m, i) => {
    const matches = lessons.map((l,n)=>({l,n})).filter(({l})=>l.module===i+1 && (!query || (l.title+' '+l.intro+' '+(l.apis||[]).map(a=>a.name).join(' ')+' '+(l.terms||[]).map(t=>t.name+' '+t.meaning).join(' ')).toLowerCase().includes(query)));
    if(!matches.length)return '';
    return `<details class="module-group" ${query || lessons[current]?.module===i+1?'open':''}><summary class="module-heading"><span class="module-number">0${i+1}</span>${m}<small>${matches.length}</small></summary>${matches.map(({l,n})=>`<button class="lesson-link ${n === current ? 'active':''}" data-lesson="${n}" ${n === current ? 'aria-current="step"':''}><span class="mark">${done(l)?'✓':'·'}</span>${escapeHTML(l.title)}</button>`).join('')}</details>`;
  }).join('') || '<p class="no-results">검색 결과가 없습니다.</p>';
  document.querySelectorAll('[data-lesson]').forEach(b => b.onclick = () => { showLesson(Number(b.dataset.lesson)); $('lesson-pane').focus({preventScroll:true}); });
  const count = lessons.filter(done).length;
  $('progress-label').textContent = `${count} / ${lessons.length}`;
  $('progress').max = lessons.length; $('progress').value = count;
}
function renderTerms(l) {
  return `<section class="lesson-terms" id="lesson-terms" aria-labelledby="terms-heading"><h2 id="terms-heading">용어 다시 찾기</h2><dl>${(l.terms || []).map(t => `<div><dt>${escapeHTML(t.name)}</dt><dd>${escapeHTML(t.meaning)}</dd></div>`).join('')}</dl></section>`;
}

function renderCodeExcerpt(code) {
  if (!code) return '';
  return `<figure class="teaching-code"><figcaption><code>${escapeHTML(code.file)}</code> · 배포 예제 ${code.line}행부터<br>찾을 표현: <code>${escapeHTML(code.anchor)}</code></figcaption><pre><code>${escapeHTML(code.text)}</code></pre><button data-source-file="${escapeHTML(code.file)}">이 파일을 편집기에서 열기</button></figure>`;
}
function renderReadingRoute(l) {
  const r = l.reading;
  if (!r) return '';
  return `<nav class="api-practice-links" aria-label="관련 참고 자료"><a href="/static/reference.html#flow/${encodeURIComponent(r.flow)}" target="_blank" rel="noopener">관련 흐름 지도 ↗</a><a href="/static/reference.html#api" target="_blank" rel="noopener">API 사전 ↗</a></nav>`;
}

function renderReading(l) {
  return `<div class="reading" id="reading">${(l.sections||[]).map(s=>`<article><h3>${escapeHTML(s.title)}</h3>${s.paragraphs.map(p=>`<p>${escapeHTML(p)}</p>`).join('')}${s.code?renderCodeExcerpt(s.code):''}</article>`).join('')}${l.reading?.code && !(l.sections||[]).some(s=>s.code)?`<article><h3>설명과 함께 볼 코드</h3><p>아래는 배포 예제의 일부입니다. 편집기에서 파일을 열고 표시된 표현을 검색하면 주변 흐름을 함께 읽을 수 있습니다. 직접 수정한 파일은 내용이나 줄 번호가 달라질 수 있습니다.</p>${renderCodeExcerpt(l.reading.code)}</article>`:""}</div>${renderTerms(l)}<section class="api-contracts" id="api-contracts"><span class="eyebrow">API CONTRACT</span><h2>함수의 역할부터 호출 방법까지</h2>${(l.apis||[]).map(a=>`<article class="api-card"><h3><code>${escapeHTML(a.name)}</code></h3><dl><dt>하는 일</dt><dd>${escapeHTML(a.purpose)}</dd><dt>사용 순서·제약</dt><dd>${escapeHTML(a.usage)}</dd><dt>인자</dt><dd>${escapeHTML(a.args)}</dd><dt>소유권 / 수명</dt><dd>${escapeHTML(a.ownership)}</dd><dt>반환값</dt><dd>${escapeHTML(a.returns)}</dd><dt>실패 시</dt><dd>${escapeHTML(a.failure)}</dd><dt>이 예제에서의 역할</dt><dd>${escapeHTML(a.lab)}</dd></dl><nav class="api-practice-links" aria-label="관련 실습">${(a.practice_links||[]).map(link=>`<a href="${escapeHTML(link.href)}">${escapeHTML(link.title)} · ${escapeHTML(link.label)} →</a>`).join("")}</nav>${(a.examples||[]).map(renderCodeExcerpt).join("")}<a href="/static/reference.html#api/${encodeURIComponent(a.name.split("(")[0])}" target="_blank" rel="noopener">API 사전에서 찾아보기 ↗</a></article>`).join('')}</section>`;
}
function showLesson(index) {
  current = index;
  const l = lessons[index];
  history.replaceState(null, '', `#${l.id}`);
  $('module-name').textContent = modules[l.module-1];
  $('lesson-content').innerHTML = `<div class="lesson-meta"><span class="eyebrow">MODULE 0${l.module} · LAB ${String(index+1).padStart(2,'0')}</span><span class="time">약 ${l.minutes}분</span></div><div id="lesson-completed" class="completed-badge" hidden>✓ 학습 완료</div><h1>${escapeHTML(l.title)}</h1><p class="intro">${escapeHTML(l.intro)}</p><div class="lesson-jumps"><button data-jump="lesson-terms">용어 설명</button><button data-jump="reading">개념 해설</button><button data-jump="api-contracts">API 계약</button><button data-jump="practice">실습</button><button data-jump="quiz-card">퀴즈</button></div>${renderReadingRoute(l)}${renderReading(l)}<div id="practice" class="practice-label"><span class="eyebrow">HANDS-ON · C++20 / OPENSSL 3.5.7</span><h2>직접 실행하고 바꿔보기</h2></div>${l.file?`<button class="open-example" id="open-example">↗ ${escapeHTML(l.file)} 편집기에서 열기</button><button id="open-header" class="header-button">공통 헤더 study.hpp</button>`:''}${l.steps.map((s,i)=>`<section class="step" id="practice-step-${i+1}" tabindex="-1"><h3><span class="step-index">${i+1}</span>${escapeHTML(s.title)}</h3><p>${escapeHTML(s.text)}</p><div class="command"><div class="command-top"><span>BASH</span><button data-command="${i}">터미널에 입력 ↗</button></div><pre><code>${escapeHTML(s.command)}</code></pre></div><div class="expect"><b>EXPECTED</b><span>${escapeHTML(s.expect)}</span></div></section>`).join('')}<section class="challenge"><span class="eyebrow">TRY IT YOURSELF</span><p>${escapeHTML(l.challenge||'예상 결과와 실제 결과를 비교해 보세요.')}</p></section><section class="quiz-card" id="quiz-card"><div class="quiz"><span class="eyebrow">QUICK CHECK</span><h4>${escapeHTML(l.quiz.question)}</h4>${l.quiz.options.map((o,i)=>`<button class="quiz-option" data-answer="${i}">${String.fromCharCode(65+i)}. ${escapeHTML(o)}</button>`).join('')}<div id="quiz-feedback" class="quiz-feedback" role="status">${progress[l.id]?.quiz?'✓ 이전에 퀴즈를 통과했습니다.':''}</div></div></section><div class="lesson-footer"><button id="complete-lesson" aria-pressed="false">학습 완료로 표시</button><button id="previous" ${index===0?'disabled':''}>← 이전 레슨</button><button id="next" ${index===lessons.length-1?'disabled':''}>다음 레슨 →</button></div><details class="docs"><summary>공식 문서로 더 알아보기</summary>${l.docs.map(d=>`<a href="${escapeHTML(d)}" target="_blank" rel="noopener noreferrer">${escapeHTML(d.replace('https://',''))} ↗</a>`).join('')}</details>`;
  document.querySelectorAll('[data-command]').forEach(b => b.onclick = () => {
    if (!terminalReady()) return;
    switchTab('terminal'); term.paste(l.steps[Number(b.dataset.command)].command); term.focus();
    toast('명령을 확인한 뒤 터미널에서 Enter를 누르세요.');

  });
  $('lesson-content').querySelectorAll('[data-source-file]').forEach(b => b.onclick=()=>openFile(b.dataset.sourceFile).catch(e=>toast(e.message)));
  if (l.file) { $('open-example').onclick = () => openFile(l.file).catch(e=>toast(e.message)); $('open-header').onclick = () => openFile('examples/cpp/study.hpp').catch(e=>toast(e.message)); }
  document.querySelectorAll('[data-jump]').forEach(b=>b.onclick=()=>scrollLessonTo($(b.dataset.jump)));
  function updateCompletion() {
    $('complete-lesson').textContent = done(l) ? '완료 표시 해제' : '학습 완료로 표시';
    $('complete-lesson').setAttribute('aria-pressed', String(done(l)));
    $('lesson-completed').hidden = !done(l);
  }
  $('complete-lesson').onclick = () => {
    progress[l.id] = {...progress[l.id], completed: !done(l)};
    saveProgress();
    updateCompletion();
  document.querySelectorAll('[data-answer]').forEach(b=>b.onclick=()=>{
    document.querySelectorAll('[data-answer]').forEach(x=>x.classList.remove('correct','wrong'));
    const correct = Number(b.dataset.answer) === l.quiz.answer;
    b.classList.add(correct?'correct':'wrong');
    $('quiz-feedback').textContent = correct ? `✓ ${l.quiz.explanation}` : '다시 생각해 보세요. 위의 핵심 개념과 실행 결과를 확인하면 도움이 됩니다.';
    if(correct) { progress[l.id] = {...progress[l.id], completed:done(l), quiz:true}; saveProgress(); }
  });
  };
  updateCompletion();
  document.querySelectorAll('[data-answer]').forEach(b=>b.onclick=()=>{
    document.querySelectorAll('[data-answer]').forEach(x=>x.classList.remove('correct','wrong'));
    const correct = Number(b.dataset.answer) === l.quiz.answer;
    b.classList.add(correct?'correct':'wrong');
    $('quiz-feedback').textContent = correct ? `✓ ${l.quiz.explanation}` : '다시 생각해 보세요. 위의 핵심 개념과 실행 결과를 확인하면 도움이 됩니다.';
    if(correct) { progress[l.id] = {...progress[l.id], completed:done(l), quiz:true}; saveProgress(); }
  });
  $('previous').onclick=()=>showLesson(index-1); $('next').onclick=()=>showLesson(index+1);
  closeCourse(); setPane('lesson');
  $('lesson-pane').scrollTop=0; renderNav();
}
const term = new Terminal({fontFamily:'Consolas, "Liberation Mono", monospace', fontSize:13, lineHeight:1.45, cursorBlink:true, scrollback:5000, theme:{background:'#101b28',foreground:'#d8e5e0',cursor:'#8ed6b1',selectionBackground:'#34574c',black:'#101b28',green:'#8bd4a8',blue:'#80b7dd',cyan:'#91cfc7'}});
const fit = new FitAddon.FitAddon(); term.loadAddon(fit); term.open($('terminal'));
function resizeTerminal(){ if(!$('terminal-panel').hidden){ try { fit.fit(); if(socket?.readyState===WebSocket.OPEN) socket.send(JSON.stringify({type:'resize',cols:term.cols,rows:term.rows})); }catch{} } }
new ResizeObserver(resizeTerminal).observe($('terminal'));
term.onData(data=>{if(socket?.readyState===WebSocket.OPEN) socket.send(JSON.stringify({type:'input',data}));});
function terminalReady(){if(socket?.readyState!==WebSocket.OPEN){toast('터미널 연결이 필요합니다. 다시 연결을 눌러주세요.');return false;}return true;}
function connect(){
  if(socket) {socket.onclose=null;socket.close();}
  term.reset(); $('connection').textContent='연결 중'; $('connection').classList.remove('offline');
  socket = new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws`);socket.binaryType='arraybuffer';
  socket.onopen=()=>{$('connection').textContent='● 연결됨';resizeTerminal();};
  socket.onmessage=e=>term.write(typeof e.data==='string'?e.data:new Uint8Array(e.data));
  socket.onclose=()=>{$('connection').textContent='연결 종료';$('connection').classList.add('offline');term.writeln('\r\n\x1b[33m연결이 종료되었습니다. 다시 연결을 눌러 새 셸을 여세요.\x1b[0m');};
  socket.onerror=()=>toast('터미널 연결 오류: Docker 컨테이너 상태를 확인하세요.');
}
function switchTab(tab){
  document.body.dataset.tool=tab;
  const terminal=tab==='terminal'; $('terminal-panel').hidden=!terminal;$('editor-panel').hidden=terminal;
  $('terminal-tab').classList.toggle('active',terminal);$('editor-tab').classList.toggle('active',!terminal);
  $('terminal-tab').setAttribute('aria-selected',terminal);$('editor-tab').setAttribute('aria-selected',!terminal);
  if(!terminal) ensureIDE();
  requestAnimationFrame(resizeTerminal);
  setPane('lab');
}
function parseArgs(text) {
  const result=[];let word='', quote='', escaped=false, started=false;
  for(const ch of text){
    if(escaped){word+=ch;escaped=false;started=true;continue;}
    if(ch==='\\' && quote!=="'"){escaped=true;started=true;continue;}
    if(quote){if(ch===quote)quote='';else word+=ch;started=true;continue;}
    if(ch==='"'||ch==="'"){quote=ch;started=true;continue;}
    if(/\s/.test(ch)){if(started){result.push(word);word='';started=false;}continue;}
    word+=ch;started=true;
  }
  if(quote||escaped)throw new Error('실행 인자의 따옴표 또는 역슬래시를 닫아 주세요.');
  if(started)result.push(word);return result;
}
function setLayout(choice, persist = true) {
  const layout = ['reading','balanced','practice'].includes(choice) ? choice : 'balanced';
  document.body.dataset.layout = layout;
  document.querySelectorAll('[data-layout-choice]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.layoutChoice===layout)));
  if(persist) { try { localStorage.setItem('openssl-study-layout-v1',layout); } catch {} }
  requestAnimationFrame(resizeTerminal);
}
document.querySelectorAll('[data-layout-choice]').forEach(b=>b.onclick=()=>setLayout(b.dataset.layoutChoice));
let savedLayout='balanced';
try { savedLayout=localStorage.getItem('openssl-study-layout-v1')||'balanced'; } catch {}
setLayout(savedLayout,false);
$('lesson-search').oninput=renderNav;
function closeCourse() {
  if($('course-panel').open) $('course-panel').close();
  $('course-toggle').setAttribute('aria-expanded','false');
}
function setPane(pane) {
  document.body.dataset.pane=pane;
  document.querySelectorAll('[data-pane-choice]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.paneChoice===pane)));
  requestAnimationFrame(resizeTerminal);
}
function scrollLessonTo(element) {
  const panel=$('lesson-pane');
  const top=element.getBoundingClientRect().top-panel.getBoundingClientRect().top+panel.scrollTop-16;
  panel.scrollTo({top,behavior:scrollBehavior()});
}
document.querySelectorAll('[data-pane-choice]').forEach(b=>b.onclick=()=>setPane(b.dataset.paneChoice));
$('course-toggle').onclick=()=>{
  $('course-panel').showModal();
  $('course-toggle').setAttribute('aria-expanded','true');
  $('lesson-search').focus();
};
$('course-close').onclick=()=>{closeCourse();$('course-toggle').focus();};
$('course-panel').addEventListener('close',()=>$('course-toggle').setAttribute('aria-expanded','false'));
$('lab-jump').onclick=()=>{setPane('lab');$('lab-pane').focus({preventScroll:true});};
$('terminal-tab').onclick=()=>switchTab('terminal');$('editor-tab').onclick=()=>switchTab('editor');$('reconnect').onclick=connect;
function navigateLessonAnchor() {
  const [id, section, number] = location.hash.slice(1).split('/');
  const index = lessons.findIndex(l => l.id === id);
  showLesson(index < 0 ? 0 : index);
  if (index >= 0 && section === 'step' && /^[1-9][0-9]*$/.test(number || '')) {
    const target = $(`practice-step-${number}`);
    if (target) {
      history.replaceState(null, '', `#${id}/step/${number}`);
      setPane('lesson');
      requestAnimationFrame(() => { scrollLessonTo(target); target.focus({preventScroll:true}); });
    }
  }
}
window.addEventListener('hashchange', () => { if (lessons.length) navigateLessonAnchor(); });
async function init(){
  try{const data=await api('/api/info');lessons=data.lessons;$('version').textContent=data.openssl;
    navigateLessonAnchor();connect();
  }catch(e){$('lesson-content').textContent=`환경을 불러오지 못했습니다: ${e.message}. 페이지를 새로고침해 주세요.`;}
}
init();
