"""Compile and exercise real QUIC in an isolated workspace, including rejection paths."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def verify(folder, binary):
    for mode in ('ok', 'multi', 'epoll', 'bad-host', 'bad-alpn'):
        result = subprocess.run(['timeout', '12', str(binary), mode], cwd=folder,
                                capture_output=True, text=True, timeout=15)
        output = result.stdout + result.stderr
        if mode.startswith('bad-'):
            assert result.returncode == 1, (mode, result.returncode, output)
            assert 'PASS' not in output and 'connect:' in output, output
            if mode == 'bad-host':
                assert 'hostname mismatch' in output, output
        else:
            assert result.returncode == 0 and f'PASS {mode}' in output, output
            assert 'FIN received' in output, output
            if mode == 'multi':
                assert all(f'stream={n} ' in output for n in (0, 4, 8)), output
        print(f'PASS QUIC {mode}: exit={result.returncode}')


if '--existing' in sys.argv:
    verify(Path.cwd(), Path.cwd()/'examples/cpp/quic_local')
else:
    with tempfile.TemporaryDirectory(prefix='quic-study-test-') as temp:
        folder = Path(temp)
        shutil.copytree('/home/student/lab/tls', folder/'tls')
        binary = folder/'quic_local'
        subprocess.run(['g++', '-std=c++20', '-Wall', '-Wextra', '-Werror', '-g', '-O0',
                        '-I/opt/examples/cpp', '/opt/examples/cpp/quic_local.cpp',
                        '-lssl', '-lcrypto', '-o', str(binary)], check=True)
        verify(folder, binary)
