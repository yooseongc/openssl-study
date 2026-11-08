'use strict';
const byId = id => document.getElementById(id);
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let entries = [];
let loaded = false;
let selectedStep = 0;
let currentTopic;
const fields = [['purpose','하는 일'],['usage','사용 순서·제약'],['args','인자'],['ownership','소유권·수명'],['returns','반환값'],['failure','실패 처리']];

function renderFlow(id) {
  const topic = flowTopics.find(t => t.id === id) || flowTopics[0];
  currentTopic = topic;
  selectedStep = 0;
  byId('flow-topics').innerHTML = flowTopics.map(t => `<a href="#flow/${t.id}" ${t===topic?'aria-current="page"':''}>${escape(t.title)}</a>`).join('');
  byId('flow-content').innerHTML = `<h2>${escape(topic.title)}</h2><p>${escape(topic.intro)}</p><p class="reference-scope"><strong>이 그림의 범위</strong> ${escape(topic.scope)}</p>${sequenceDiagram(topic)}<div class="flow-explorer"><div><ol class="diagram-steps" aria-label="단계 선택">${topic.steps.map((s,i)=>`<li><button data-step="${i}" aria-pressed="${i===0}"><span class="step-index">${i+1}</span><span><small>${escape(s[1])}</small><strong>${escape(s[0])}</strong><span>${escape(s[2])}</span></span></button></li>`).join('')}</ol></div><section class="diagram-detail" aria-label="선택한 단계 해설"><div id="step-detail" aria-live="polite"></div><div class="diagram-controls"><button id="step-prev">← 이전 단계</button><button id="step-next">다음 단계 →</button></div></section></div><h3>한눈에 비교하기</h3><div class="reference-table" tabindex="0" role="region" aria-label="${escape(topic.title)} 비교표"><table><caption>${escape(topic.title)} 핵심 비교</caption><thead><tr>${topic.columns.map(c=>`<th scope="col">${escape(c)}</th>`).join('')}</tr></thead><tbody>${topic.rows.map(r=>`<tr>${r.map((v,i)=>i===0?`<th scope="row">${escape(v)}</th>`:`<td>${escape(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p><a href="/#${topic.lesson}">관련 교재·실습으로 이동 ↗</a></p><details class="docs"><summary>근거와 공식 문서</summary>${topic.docs.map(d=>`<a href="${escape(d)}" target="_blank" rel="noopener">${escape(d)} ↗</a>`).join('')}</details>`;
  byId('flow-content').querySelectorAll('[data-step]').forEach(button => button.onclick=()=>{ showStep(Number(button.dataset.step)); document.querySelector('.diagram-detail').scrollIntoView({block:'nearest'}); });
  byId('step-prev').onclick=()=>showStep(selectedStep-1);
  byId('step-next').onclick=()=>showStep(selectedStep+1);
  showStep(0);
}

function showStep(index) {
  selectedStep = Math.max(0, Math.min(index, currentTopic.steps.length-1));
  const step = currentTopic.steps[selectedStep];
  byId('step-detail').innerHTML=`<span class="eyebrow">STEP ${selectedStep+1} / ${currentTopic.steps.length}</span><h3>${escape(step[0])}</h3><p class="diagram-formula">${escape(step[2])}</p><p>${escape(step[3])}</p><a href="#api/${encodeURIComponent(step[4])}">관련 API 찾기: ${escape(step[4])} ↗</a>`;
  byId('flow-content').querySelectorAll('[data-step]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.step)===selectedStep)));
  byId('step-prev').disabled=selectedStep===0;
  byId('step-next').disabled=selectedStep===currentTopic.steps.length-1;
}

function family(name) {
  if (/ASYNC/.test(name)) return 'ASYNC';
  if (/SSL|QUIC/.test(name)) return 'SSL / QUIC';
  if (/EVP/.test(name)) return 'EVP';
  if (/X509|PEM/.test(name)) return 'X509 / 인증서';
  if (/BIO/.test(name)) return 'BIO';
  return '기타';
}

async function loadDictionary() {
  if (loaded) return;
  // Visiting the root establishes the existing localhost session; no new API or policy exception.
  await fetch('/');
  const response=await fetch('/api/info');
  if (!response.ok) throw new Error(`사전을 불러오지 못했습니다 (${response.status}). 새로고침해 주세요.`);
  const data=await response.json();
  const grouped=new Map();
  for (const lesson of data.lessons) for (const api of lesson.apis || []) {
    // Keep variants with different contracts; group only identical explanations.
    const key=JSON.stringify([api.name,...fields.map(([field])=>api[field] || '')]);
    if (!grouped.has(key)) grouped.set(key,{...api,lessons:[],docs:new Set(),family:family(api.name)});
    const entry=grouped.get(key);
    entry.lessons.push({id:lesson.id,title:lesson.title,lab:api.lab,links:api.practice_links||[],examples:api.examples||[]});
    for (const doc of lesson.docs || []) if (doc.startsWith('https://docs.openssl.org/')) entry.docs.add(doc);
  }
  entries=[...grouped.values()].sort((a,b)=>a.name.localeCompare(b.name));
  loaded=true;
}

function renderDictionary() {
  const query=byId('api-search').value.trim().toLowerCase();
  const group=byId('api-family').value;
  const matches=entries.filter(e=>(!group || e.family===group) && [e.name,...fields.map(([f])=>e[f]),...e.lessons.map(l=>l.title)].join(' ').toLowerCase().includes(query));
  byId('api-status').textContent=`${entries.length}개 학습 항목 중 ${matches.length}개 · 복수 함수를 함께 설명하는 항목도 포함합니다.`;
  byId('api-results').innerHTML=matches.length ? matches.map(e=>`<article class="reference-api"><span class="eyebrow">${escape(e.family)}</span><h2>${escape(e.name)}</h2><dl>${fields.map(([f,label])=>`<div><dt>${label}</dt><dd>${escape(e[f] || '관련 교재와 공식 문서를 확인하세요.')}</dd></div>`).join('')}</dl><h3>관련 실습</h3>${e.lessons.map(l=>`<p><a href="/#${encodeURIComponent(l.id)}">${escape(l.title)} ↗</a>${l.lab?`<br><span>${escape(l.lab)}</span>`:''}${l.links.map(link=>`<br><a href="${escape(link.href)}">${escape(link.label)} 실습으로 이동 →</a>`).join('')}</p>${l.examples.map(c=>`<details class="dictionary-code"><summary>${escape(c.file)} · ${c.line}행부터 실제 호출 보기</summary><pre><code>${escape(c.text)}</code></pre></details>`).join('')}`).join('')}<details class="docs"><summary>관련 교재의 공식 문서</summary>${[...e.docs].map(d=>`<a href="${escape(d)}" target="_blank" rel="noopener">${escape(d)} ↗</a>`).join('') || '관련 교재의 문서 링크를 확인하세요.'}</details></article>`).join('') : '<p class="reference-scope">일치하는 학습 항목이 없습니다. 함수 이름의 일부로 검색하거나 분야 필터를 해제해 보세요. 이 사전은 교재에 포함된 API만 다룹니다.</p>';
}

async function route() {
  const [mode,arg] = location.hash.slice(1).split('/');
  const api=mode==='api';
  byId('flow-view').hidden=api;
  byId('api-view').hidden=!api;
  byId('api-tab').setAttribute('aria-current',api?'page':'false');
  byId('flow-tab').setAttribute('aria-current',api?'false':'page');
  if (api) {
    try {
      byId('api-search').value=arg ? decodeURIComponent(arg) : '';
      byId('api-family').value='';
      await loadDictionary();
      if (location.hash.startsWith('#api')) renderDictionary();
    } catch(error) { byId('api-status').textContent=error.message; }
  } else renderFlow(arg);
  document.querySelector('.reference-main').scrollTop=0;
}
byId('api-search').addEventListener('input',renderDictionary);
byId('api-family').addEventListener('change',renderDictionary);
window.addEventListener('hashchange',route);
route();

// Compact lifeline diagram complements the detailed step cards; all content has a text equivalent.
function sequenceDiagram(topic) {
  if (topic.id !== 'tls') return '';
  const rows = [
    ['ClientHello', true], ['ServerHello', false],
    ['EncryptedExtensions · Certificate', false], ['CertificateVerify', false],
    ['Server Finished', false], ['Client Finished', true], ['Application Data', true]
  ];
  return `<figure class="tls-sequence"><figcaption>TLS 1.3 메시지 시퀀스 · 위에서 아래로 진행</figcaption><svg viewBox="0 0 800 450" role="img" aria-labelledby="tls-svg-title tls-svg-desc"><title id="tls-svg-title">클라이언트와 서버의 TLS 1.3 메시지 교환</title><desc id="tls-svg-desc">ClientHello는 서버로, ServerHello부터 서버 Finished까지는 클라이언트로, 클라이언트 Finished는 서버로 전송합니다. 애플리케이션 데이터는 양방향입니다. 아래 단계 카드에 같은 흐름의 자세한 설명이 있습니다.</desc><defs><marker id="arrow-end" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z"/></marker></defs><text x="110" y="30" text-anchor="middle">클라이언트</text><text x="690" y="30" text-anchor="middle">서버</text><line class="lifeline" x1="110" y1="45" x2="110" y2="425"/><line class="lifeline" x1="690" y1="45" x2="690" y2="425"/>${rows.map(([label,right],i)=>{const y=80+i*50;return `<text x="400" y="${y-10}" text-anchor="middle">${i+1}. ${label}${i<2?' [평문]':' [암호화]'}</text><line class="message" x1="${right?110:690}" y1="${y}" x2="${right?690:110}" y2="${y}" marker-end="url(#arrow-end)"/>${i===6?`<line class="message" x1="690" y1="${y+15}" x2="110" y2="${y+15}" marker-end="url(#arrow-end)"/>`:''}`;}).join('')}</svg></figure>`;
}
