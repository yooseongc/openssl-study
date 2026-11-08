"""Check real EVP/ASYNC results in a temporary directory, without student file changes."""
from pathlib import Path
import subprocess
import tempfile

with tempfile.TemporaryDirectory(prefix='qat-study-') as directory:
    root = Path(directory)
    for name in ('qat_probe', 'async_pause'):
        subprocess.run(['g++', '-std=c++20', '-Wall', '-Wextra', '-Werror', '-pthread',
                        '-I/opt/examples/cpp', f'/opt/examples/cpp/{name}.cpp',
                        '-o', str(root/name), '-lssl', '-lcrypto'], check=True)
    for name, mode, expected, marker in [
        ('qat_probe', 'default', 0, 'PASS known-answer'),
        ('qat_probe', 'missing', 77, 'UNAVAILABLE provider=missing'),
        ('async_pause', 'ok', 0, 'operation_result=42'),
        ('async_pause', 'fail', 2, 'operation_result=-1'),
    ]:
        result = subprocess.run([str(root/name), mode], capture_output=True, text=True, timeout=10)
        assert result.returncode == expected, (name, mode, result.stdout, result.stderr)
        assert marker in result.stdout, result.stdout
        if name == 'async_pause':
            assert result.stdout.index('before pause') < result.stdout.index('caller: PAUSE') < result.stdout.index('job: resumed') < result.stdout.index('caller: FINISH')
        print(f'PASS {name} {mode}: exit={result.returncode}')
    result = subprocess.run([str(root/'qat_probe'), 'qatprovider'], capture_output=True, text=True, timeout=10)
    assert result.returncode in (0, 77), (result.stdout, result.stderr)
    if result.returncode == 77:
        assert 'UNAVAILABLE' in result.stdout
        print('SKIP QAT implementation: unavailable; no hardware performance claim')
    else:
        assert 'selected=qatprovider' in result.stdout and 'PASS known-answer' in result.stdout
        print('PASS QAT provider calculation; hardware path still not established')

