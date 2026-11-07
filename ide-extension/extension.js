'use strict';
const vscode = require('vscode');
const http = require('http');
const path = require('path');
const fs = require('fs');
const root = '/home/student/lab';
let server;
const registry = '/tmp/openssl-study-ide-' + process.pid + '.json';
function advertise() {
    const address=server?.address();
    if(address)fs.writeFileSync(registry,JSON.stringify({port:address.port,updated:Date.now()}),{mode:0o600});
}
let lastEditor;
function currentEditor() { return vscode.window.activeTextEditor || (lastEditor && !lastEditor.document.isClosed ? lastEditor : vscode.window.visibleTextEditors[0]); }
function activePath() {
    const doc = currentEditor()?.document;
    return doc && !doc.isUntitled && doc.uri.fsPath.startsWith(root + '/') ? path.relative(root, doc.uri.fsPath) : '';
}
function workspaceFile(relative) {
    if (typeof relative !== 'string') throw new Error('파일 경로가 필요합니다.');
    const full = fs.realpathSync(path.resolve(root, relative));
    if (!full.startsWith(root + '/')) throw new Error('실습 폴더의 파일만 열 수 있습니다.');
    return full;
}
exports.activate = context => {
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(editor=>{if(editor)lastEditor=editor;}));
    context.subscriptions.push(vscode.window.onDidChangeWindowState(state=>{if(state.focused)advertise();}));
    if (!context.workspaceState.get('layoutInitialized')) {
        vscode.commands.executeCommand('workbench.action.closeSidebar');
        vscode.commands.executeCommand('workbench.action.closeAuxiliaryBar');
        context.workspaceState.update('layoutInitialized', true);
    }
    server = http.createServer(async (req,res) => {
        res.setHeader('Content-Type','application/json');
        if (req.headers.authorization !== 'Bearer ' + process.env.IDE_BRIDGE_TOKEN) {
            res.writeHead(403); res.end('{}'); return;
        }
        try {
            let body=''; for await(const part of req) {body+=part; if(body.length>65536) throw new Error('Request too large');}
            const data=JSON.parse(body);
            switch(data.action) {
                case 'status': break;
                case 'open': {
                    const doc = await vscode.workspace.openTextDocument(workspaceFile(data.path));
                    await vscode.window.showTextDocument(doc,{preview:false}); break;
                }
                case 'new': await vscode.window.showTextDocument(await vscode.workspace.openTextDocument({language:'cpp'})); break;
                case 'save':
                    if (!currentEditor() || !await currentEditor().document.save()) throw new Error('저장할 파일을 선택하세요.');
                    break;
                case 'run': {
                    const doc = currentEditor()?.document;
                    if (data.path !== activePath()) throw new Error('선택한 파일이 바뀌었습니다. 인자 안내가 갱신된 후 다시 실행하세요.');
                    if (!doc || !await doc.save()) throw new Error('실행할 소스를 먼저 저장하세요.');
                    const file=workspaceFile(activePath());
                    if (!/\.(c|cpp|cc|cxx)$/.test(file)) throw new Error('C 또는 C++ 소스를 선택하세요.');
                    if (!Array.isArray(data.args) || data.args.some(a=>typeof a!=='string')) throw new Error('잘못된 실행 인자');
                    if (vscode.tasks.taskExecutions.some(t=>t.task.source==='OpenSSL Study')) throw new Error('실행 중인 작업을 터미널에서 먼저 중단하세요.');
                    const task=new vscode.Task({type:'openssl-study'}, vscode.TaskScope.Workspace,
                        path.basename(file), 'OpenSSL Study',
                        new vscode.ProcessExecution('/usr/local/bin/study-build',[file,...data.args],{cwd:root}), ['$gcc']);
                    task.presentationOptions={reveal:vscode.TaskRevealKind.Always,panel:vscode.TaskPanelKind.Shared,clear:false,focus:false};
                    await vscode.tasks.executeTask(task); break;
                }
                default: throw new Error('Unknown action');
            }
            res.end(JSON.stringify({ready:true,path:activePath(),dirty:!!currentEditor()?.document.isDirty}));
        } catch(error) {res.writeHead(400); res.end(JSON.stringify({error:error.message}));}
    });
    server.on('error', error=>console.error('Study bridge:',error));
    server.listen(0,'127.0.0.1',advertise);
    context.subscriptions.push({dispose:()=>{server.close();try{fs.unlinkSync(registry);}catch{}}});
};
exports.deactivate = ()=>server?.close();
