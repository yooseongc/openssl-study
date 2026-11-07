"""Same-origin gateway to the loopback-only IDE and its study extension."""
import asyncio
import os
import json
from pathlib import Path
from aiohttp import ClientSession, ClientTimeout, WSMsgType, web

HOP = {'connection', 'upgrade', 'keep-alive', 'transfer-encoding', 'content-length',
       'proxy-authenticate', 'proxy-authorization', 'te', 'trailer'}

async def lifecycle(app):
    app['ide_http'] = ClientSession(auto_decompress=False, timeout=ClientTimeout(total=None, sock_connect=5))
    yield
    await app['ide_http'].close()

async def proxy(request):
    suffix = request.raw_path[len('/ide'):]
    url = 'http://127.0.0.1:8090' + suffix
    headers = {k:v for k,v in request.headers.items() if k.lower() not in HOP | {'cookie', 'accept-encoding'}}
    headers['X-Forwarded-Host'] = request.host
    headers['X-Forwarded-Proto'] = 'http'
    session = request.app['ide_http']
    try:
        if request.headers.get('Upgrade', '').lower() == 'websocket':
            protocols = [p.strip() for p in request.headers.get('Sec-WebSocket-Protocol', '').split(',') if p.strip()]
            headers = {k:v for k,v in headers.items() if not k.lower().startswith('sec-websocket-')}
            async with session.ws_connect(url, headers=headers, protocols=protocols, max_msg_size=0) as upstream:
                downstream = web.WebSocketResponse(protocols=protocols, max_msg_size=0)
                await downstream.prepare(request)
                async def relay(source, target):
                    async for msg in source:
                        if msg.type == WSMsgType.TEXT: await target.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY: await target.send_bytes(msg.data)
                    await target.close()
                tasks = [asyncio.create_task(relay(upstream, downstream)), asyncio.create_task(relay(downstream, upstream))]
                try:
                    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                finally:
                    for task in tasks: task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
                return downstream
        async with session.request(request.method, url, headers=headers, data=await request.read(), allow_redirects=False) as upstream:
            outgoing = {k:v for k,v in upstream.headers.items() if k.lower() not in HOP | {'x-frame-options'}}
            location = outgoing.get('Location')
            if location and location.startswith('/') and not location.startswith('/ide/'):
                outgoing['Location'] = '/ide' + location
            return web.Response(status=upstream.status, headers=outgoing, body=await upstream.read())
    except (OSError, asyncio.TimeoutError) as exc:
        raise web.HTTPServiceUnavailable(text='IDE starting; try again shortly') from exc

async def bridge(request):
    data = {} if request.method == 'GET' else await request.json()
    action = 'status' if request.method == 'GET' else data.get('action')
    if action not in {'status', 'open', 'save', 'run', 'new'}:
        raise web.HTTPBadRequest(text='Unknown IDE action')
    registrations=[]
    for path in Path('/tmp').glob('openssl-study-ide-*.json'):
        try:
            entry=json.loads(path.read_text())
            if 1024 <= entry['port'] <= 65535: registrations.append(entry)
        except (OSError, ValueError, KeyError, TypeError): pass
    if not registrations:
        return web.json_response({'ready':False}, status=503)
    target=max(registrations, key=lambda item:item['updated'])
    try:
        async with request.app['ide_http'].post(f"http://127.0.0.1:{target['port']}", json={**data, 'action':action},
                headers={'Authorization': 'Bearer ' + os.environ['IDE_BRIDGE_TOKEN']}, timeout=ClientTimeout(total=10)) as result:
            return web.Response(status=result.status, body=await result.read(), content_type='application/json')
    except (OSError, asyncio.TimeoutError):
        return web.json_response({'ready':False}, status=503)
