"""Local single-user learning shell. Never expose this service to a network."""
import asyncio
import fcntl
import json
import os
from pathlib import Path
import pty
import secrets
import signal
import struct
import termios
from urllib.parse import urlsplit

from aiohttp import web, WSMsgType
from curriculum import LESSONS
from checks import check
from editor_run import run_example
import ide_proxy

ROOT = Path('/home/student/lab')
STATIC = Path('/opt/app/static')
TOKEN = secrets.token_urlsafe(32)
CLIENTS = set()

@web.middleware
async def local_only(request, handler):
    if request.host.split(':')[0] not in {'localhost', '127.0.0.1'}:
        raise web.HTTPForbidden(text='Localhost only')
    origin = request.headers.get('Origin')
    if origin and origin != f'http://{request.host}':
        raise web.HTTPForbidden(text='Origin rejected')
    if request.path.startswith('/api/') or request.path == '/ws' or request.path.startswith('/ide/'):
        if not secrets.compare_digest(request.cookies.get('study_session', ''), TOKEN):
            raise web.HTTPForbidden(text='Open the study home page first')
        if request.path.startswith('/api/') and request.method != 'GET' and request.headers.get('X-Study-Request') != '1':
            raise web.HTTPForbidden(text='Missing request header')
    response = await handler(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN' if request.path.startswith('/ide/') else 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    if not request.path.startswith('/ide/'):
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'"
    return response

async def index(request):
    res = web.FileResponse(STATIC / 'index.html')
    res.set_cookie('study_session', TOKEN, httponly=True, samesite='Strict')
    return res

async def info(request):
    proc = await asyncio.create_subprocess_exec('openssl', 'version', stdout=asyncio.subprocess.PIPE)
    out, _ = await proc.communicate()
    return web.json_response({'openssl': out.decode().strip(), 'workspace': str(ROOT), 'lessons': LESSONS})

def safe_file(name):
    p = (ROOT / name).resolve()
    if not p.is_relative_to(ROOT) or p == ROOT:
        raise web.HTTPBadRequest(text='Workspace paths only')
    return p

async def files(request):
    items = [str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink() and p.suffix in {'.c', '.cpp', '.cc', '.cxx', '.hpp', '.h', '.txt', '.md', '.ext', '.cnf', '.pem', '.csr'}]
    return web.json_response(sorted(items)[:200])

async def file_get(request):
    p = safe_file(request.query.get('path', ''))
    if not p.is_file():
        raise web.HTTPNotFound()
    if p.stat().st_size > 256_000:
        raise web.HTTPBadRequest(text='File too large')
    try:
        return web.json_response({'path': str(p.relative_to(ROOT)), 'content': p.read_text()})
    except UnicodeError:
        raise web.HTTPBadRequest(text='Text files only')

async def file_put(request):
    data = await request.json()
    p = safe_file(data.get('path', ''))
    if p.suffix not in {'.c', '.cpp', '.cc', '.cxx', '.hpp', '.h', '.txt', '.md', '.ext', '.cnf'}:
        raise web.HTTPBadRequest(text='Allowed: C/C++ source/header, .txt .md .ext .cnf')
    content = data.get('content')
    if not isinstance(content, str) or len(content.encode()) > 256_000:
        raise web.HTTPBadRequest(text='Invalid content')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return web.json_response({'saved': True})

async def editor_run(request):
    data = await request.json()
    if not isinstance(data, dict) or not isinstance(data.get('path'), str):
        raise web.HTTPBadRequest(text='잘못된 실행 요청입니다.')
    path = safe_file(data['path'])
    lock = request.app['run_lock']
    if lock.locked():
        raise web.HTTPTooManyRequests(text='다른 편집기 실행이 진행 중입니다.')
    async with lock:
        return web.json_response(await run_example(ROOT, path, data.get('args')))


async def checkpoint(request):
    lid = request.match_info['id']
    if lid not in {x['id'] for x in LESSONS}:
        raise web.HTTPNotFound()
    async with request.app['check_lock']:
        result = await check(lid)
    return web.json_response(result)

async def terminal(request):
    if len(CLIENTS) >= 8:
        raise web.HTTPServiceUnavailable(text='Too many terminals')
    ws = web.WebSocketResponse(max_msg_size=65536, heartbeat=30)
    await ws.prepare(request)
    CLIENTS.add(ws)
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(ROOT)
        os.execv('/bin/bash', ['/bin/bash', '-i'])
    os.set_blocking(fd, False)
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue(maxsize=256)
    def readable():
        try:
            data = os.read(fd, 16384)
        except (OSError, BlockingIOError):
            data = b''
        if not data:
            loop.remove_reader(fd)
        try:
            queue.put_nowait(data)
        except asyncio.QueueFull:
            loop.remove_reader(fd)
            asyncio.create_task(ws.close(message=b'Terminal output overflow'))
    loop.add_reader(fd, readable)
    async def output():
        while True:
            data = await queue.get()
            if not data:
                await ws.close()
                return
            await ws.send_bytes(data)
    task = asyncio.create_task(output())
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if data.get('type') == 'input':
                        raw = data['data'].encode()
                        while raw:
                            try:
                                n = os.write(fd, raw)
                                raw = raw[n:]
                            except BlockingIOError:
                                await asyncio.sleep(0.01)
                    elif data.get('type') == 'resize':
                        cols = max(20, min(400, int(data['cols'])))
                        rows = max(5, min(200, int(data['rows'])))
                        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))
                except (ValueError, KeyError, TypeError):
                    continue
    finally:
        loop.remove_reader(fd)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        os.close(fd)
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        await asyncio.to_thread(os.waitpid, pid, 0)
        CLIENTS.discard(ws)
    return ws

async def shutdown(app):
    for ws in list(CLIENTS):
        await ws.close(code=1001, message=b'Shutting down')

app = web.Application(middlewares=[local_only], client_max_size=300_000)
app.cleanup_ctx.append(ide_proxy.lifecycle)
app['check_lock'] = asyncio.Lock()
app['run_lock'] = asyncio.Lock()
app.add_routes([web.get('/', index), web.get('/health', lambda r: web.json_response({'ok': True})),
    web.get('/api/info', info), web.get('/api/files', files), web.get('/api/file', file_get),
    web.put('/api/file', file_put), web.post('/api/run', editor_run), web.post('/api/check/{id}', checkpoint), web.get('/ws', terminal)])
app.router.add_route('*', '/ide/{path:.*}', ide_proxy.proxy)
app.router.add_get('/api/ide', ide_proxy.bridge)
app.router.add_post('/api/ide', ide_proxy.bridge)
app.router.add_static('/static/', STATIC)
app.on_shutdown.append(shutdown)
web.run_app(app, host='0.0.0.0', port=8080, print=None)
