"""Capture one bounded, non-interactive study-build invocation."""
import asyncio
import os
import signal
from pathlib import Path
from tempfile import TemporaryDirectory

from aiohttp import web


async def run_example(root, path, args):
    if path.suffix not in {'.c', '.cpp', '.cc', '.cxx'} or not path.is_file():
        raise web.HTTPBadRequest(text='컴파일할 C/C++ 소스를 선택하세요.')
    if not isinstance(args, list) or len(args) > 64 or not all(
        isinstance(arg, str) and len(arg) <= 4096 and '\x00' not in arg for arg in args
    ):
        raise web.HTTPBadRequest(text='실행 인자를 확인하세요.')
    with TemporaryDirectory() as directory:
        proc = await asyncio.create_subprocess_exec(
            'study-build', str(path), *args, cwd=root,
            env={**os.environ, 'STUDY_BUILD_OUTPUT': str(Path(directory) / 'program')},
            start_new_session=True, stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        output = bytearray()
        reason = ''
        try:
            async with asyncio.timeout(50):
                while chunk := await proc.stdout.read(8192):
                    output.extend(chunk)
                    if len(output) > 65536:
                        reason = '출력 한도 64 KiB에 도달해 중단했습니다.'
                        break
                if not reason:
                    await proc.wait()
        except TimeoutError:
            reason = '컴파일·실행 제한 시간에 도달했습니다.'
        finally:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await proc.communicate()
        return {'code': proc.returncode, 'output': output[:65536].decode(errors='replace'), 'notice': reason}
