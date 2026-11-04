// Last two invocations per source file, for the lifetime of this page.
const runsByPath = new Map();
let resultShare = 32;
let resultsOpen = false;
let running = false;

function currentFile() {
  return $('file-path').value.trim();
}
function showGuide() {
  const guide = exampleGuides[currentFile()];
  $('args-guide').hidden = !guide;
  $('preset-options').replaceChildren();
  if (!guide) return;
  $('args-description').textContent = guide.desc;
  for (const [args, meaning] of guide.choices) {
    const choice = document.createElement('button');
    choice.type = 'button';
    choice.textContent = (args || '(인자 없음)') + ' · ' + meaning;
    choice.onclick = () => {
      $('run-args').value = args;
      $('args-guide').open = false;
      $('run-args').focus();
    };
    $('preset-options').append(choice);
  }
}
function setResultHeight(share) {
  resultShare = Math.max(0, Math.min(85, share));
  openResults(resultShare > 0);
  $('edit-stack').style.setProperty('--result-share', resultShare + '%');
  $('result-divider').setAttribute('aria-valuenow', String(Math.round(resultShare)));
}
function openResults(open) {
  if (open && resultShare === 0) {
    resultShare = 32;
    $('edit-stack').style.setProperty('--result-share', '32%');
    $('result-divider').setAttribute('aria-valuenow', '32');
  }
  resultsOpen = open;
  $('result-output').hidden = !open;
  $('result-toggle').setAttribute('aria-expanded', String(open));
  $('result-toggle').textContent = open ? '결과 접기' : '실행 결과 열기';
}
function drawResult(container, run) {
  const heading = document.createElement('strong');
  heading.textContent = (run.args || '(인자 없음)') + ' · 종료 ' + run.code;
  container.append(heading);
  const pre = document.createElement('pre');
  for (const line of (run.output + (run.notice ? '\n' + run.notice : '')).split('\n')) {
    const match = line.match(/^\/home\/student\/lab\/(.+?):(\d+):(\d+):/);
    if (match) {
      const jump = document.createElement('button');
      jump.className = 'error-jump';
      jump.textContent = line.slice(0, match[0].length);
      jump.onclick = async () => {
        try {
          if (currentFile() !== match[1]) await openFile(match[1]);
          if (currentFile() !== match[1]) return;
          codeEditor.setCursor(Number(match[2]) - 1, Number(match[3]) - 1);
          codeEditor.scrollIntoView(codeEditor.getCursor(), 60);
          codeEditor.focus();
        } catch (error) { toast(error.message); }
      };
      pre.append(jump, line.slice(match[0].length), '\n');
    } else pre.append(line + '\n');
  }
  container.append(pre);
}
function renderResults() {
  const output = $('result-output');
  const runs = runsByPath.get(currentFile()) || [];
  output.replaceChildren();
  if (!runs.length) {
    output.textContent = '이 파일을 실행하면 출력과 종료 코드가 표시됩니다.';
    return;
  }
  drawResult(output, runs[0]);
  if (runs[1]) {
    const previous = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = '직전 실행과 비교';
    previous.append(summary);
    drawResult(previous, runs[1]);
    output.append(previous);
  }
}
async function runCurrentFile() {
  if (running) return;
  const path = currentFile();
  const argsText = $('run-args').value;
  running = true;
  $('build-run').disabled = true;
  try {
    if (!/\.(c|cpp|cc|cxx)$/.test(path)) throw new Error('실행할 C/C++ 소스를 선택하세요.');
    const args = parseArgs(argsText);
    await saveFile();
    openResults(true);
    $('result-output').textContent = '컴파일 및 실행 중…';
    const result = await api('/api/run', {method:'POST', body:JSON.stringify({path,args})});
    const previous = runsByPath.get(path) || [];
    runsByPath.set(path, [{...result,args:argsText}, ...previous.slice(0,1)]);
    renderResults();
  } catch (error) { renderResults(); toast(error.message); }
  finally { running = false; $('build-run').disabled = false; }
}
$('result-toggle').onclick = () => openResults(!resultsOpen);
const divider = $('result-divider');
divider.onpointerdown = event => {
  divider.setPointerCapture(event.pointerId);
  openResults(true);
};
divider.onpointermove = event => {
  if (!divider.hasPointerCapture(event.pointerId)) return;
  const area = $('edit-stack').getBoundingClientRect();
  setResultHeight(100 * (area.bottom - event.clientY) / area.height);
};
divider.onkeydown = event => {
  if (!['ArrowUp','ArrowDown'].includes(event.key)) return;
  event.preventDefault();
  setResultHeight(resultShare + (event.key === 'ArrowUp' ? 5 : -5));
};
setResultHeight(resultShare);
openResults(false);
renderResults();
showGuide();

// Move the same editor into a native dialog, preserving document and undo history.
const editorDialog = $('editor-dialog');
const editorPanel = $('editor-panel');
const editorHome = document.createComment('editor position');
editorPanel.before(editorHome);
let resultsBeforeExpand = false;
$('editor-expand').onclick = () => {
  if (editorDialog.open) {
    editorDialog.close();
    return;
  }
  resultsBeforeExpand = resultsOpen;
  openResults(false);
  editorDialog.append(editorPanel);
  editorDialog.showModal();
  $('editor-expand').textContent = '원래 크기';
  $('editor-expand').setAttribute('aria-expanded', 'true');
  codeEditor.refresh();
  codeEditor.focus();
};
editorDialog.addEventListener('close', () => {
  editorHome.after(editorPanel);
  $('editor-expand').textContent = '최대화';
  $('editor-expand').setAttribute('aria-expanded', 'false');
  openResults(resultsBeforeExpand);
  codeEditor.refresh();
  $('editor-expand').focus();
});
editorDialog.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    event.preventDefault();
    event.stopPropagation();
    editorDialog.close();
  }
}, true);
