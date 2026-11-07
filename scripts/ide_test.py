"""Exercise the IDE gateway's session boundary without modifying student files."""
import asyncio
import aiohttp

async def main():
    base='http://localhost:8080'
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        for route in ['/ide/', '/ide/healthz', '/api/ide']:
            async with session.get(base+route) as response:
                assert response.status==403, (route,response.status)
        async with session.get(base+'/') as response: assert response.status==200
        async with session.get(base+'/ide/?folder=/home/student/lab') as response:
            assert response.status==200
            assert response.headers['X-Frame-Options']=='SAMEORIGIN'
            assert 'workbench' in await response.text()
        for headers in [{'Origin':'https://other.example'},{'Host':'other.example'}]:
            async with session.get(base+'/ide/',headers=headers) as response: assert response.status==403
        async with session.post(base+'/api/ide',json={'action':'save'}) as response: assert response.status==403
        async with session.post(base+'/api/ide',headers={'X-Study-Request':'1'},json={'action':'arbitrary'}) as response: assert response.status==400
        async with session.get(base+'/ide/healthz') as response: assert response.status==200
    print('PASS IDE session/Host/Origin boundary; same-origin embedding; upstream health; action validation')
asyncio.run(main())
