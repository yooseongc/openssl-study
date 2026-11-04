"""Check the actual HTTP, WebSocket PTY, file API, and local access boundary."""
import asyncio
from pathlib import Path
import secrets
import aiohttp

async def main():
    base = 'http://localhost:8080'
    name = f'notes/test-{secrets.token_hex(5)}.txt'
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as s:
        async with s.get(base+'/api/info') as r:
            assert r.status == 403
        async with s.get(base+'/') as r:
            assert r.status == 200
        async with s.get(base+'/api/info') as r:
            data=await r.json()
            assert len(data['lessons']) == 28 and data['openssl'].startswith('OpenSSL 3.5.7 ')
        async with s.get(base+'/api/info', headers={'Origin':'https://other.example'}) as r:
            assert r.status == 403
        async with s.get(base+'/health', headers={'Host':'other.example'}) as r:
            assert r.status == 403
        async with s.get(base+'/api/file',params={'path':'../../etc/passwd'}) as r:
            assert r.status == 400
        async with s.put(base+'/api/file',json={'path':name,'content':'denied'}) as r:
            assert r.status == 403
        try:
            async with s.put(base+'/api/file',headers={'X-Study-Request':'1'},json={'path':name,'content':'한글 저장 테스트'}) as r:
                assert r.status == 200
            async with s.get(base+'/api/file',params={'path':name}) as r:
                assert (await r.json())['content'] == '한글 저장 테스트'
        finally:
            (Path('/home/student/lab')/name).unlink(missing_ok=True)
        async with s.ws_connect(base+'/ws',origin=base) as ws:
            await ws.send_json({'type':'resize','cols':90,'rows':25})
            await ws.send_json({'type':'input','data':"printf '\\x50\\x54\\x59_OK\\n'\r"})
            text=''
            async with asyncio.timeout(5):
                while 'PTY_OK' not in text:
                    message=await ws.receive()
                    text += message.data.decode(errors='replace') if isinstance(message.data,bytes) else str(message.data)
        async with s.post(base+'/api/check/tls-1',headers={'X-Study-Request':'1'}) as r:
            assert (await r.json())['ok']
    print('PASS: session boundary; Origin/Host rejection; path traversal rejection; file save/load; real PTY input/resize/output; 28 lessons; OpenSSL 3.5.7; lesson check API.')

asyncio.run(main())
