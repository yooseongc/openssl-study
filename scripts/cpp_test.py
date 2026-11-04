"""Build pristine examples in a temporary folder and verify real outcomes."""
from pathlib import Path
import shutil
import subprocess
import tempfile
from check_cpp import verify
from failure_lab import exercise

with tempfile.TemporaryDirectory(prefix='cpp-study-test-') as folder:
    root=Path(folder)
    source=root/'examples/cpp'
    shutil.copytree('/opt/examples/cpp',source)
    version=subprocess.check_output(['openssl','version'],text=True)
    assert version.startswith('OpenSSL 3.5.7 '),version
    for cpp in sorted(source.glob('*.cpp')):
        subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-g','-O0','-pthread',str(cpp),'-o',str(cpp.with_suffix('')),'-lssl','-lcrypto'],check=True,timeout=60)
        print('BUILD PASS',cpp.name,flush=True)
    ids=['basic-bytes','basic-hash','basic-random','basic-mac','basic-kdf','basic-aead','basic-kex',
         'arch-2','arch-ownership','arch-bio','arch-errors','x509-api','code-1','code-2','code-3','code-nonblock','tls-record','tls-shutdown','code-asio']
    for id in ids:print(verify(id,root),flush=True)
    exercise(source/'tls_client',stall=True)
    print('PASS nonblocking absolute deadline',flush=True)
    # Ref-count and exception cleanup: sanitizers must also accept intentional exit 1.
    binary=root/'ownership-sanitized'
    subprocess.run(['g++','-std=c++20','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer',str(source/'ownership.cpp'),'-o',str(binary),'-lcrypto','-lssl'],check=True,timeout=30)
    for args,expected in [([],0),(['throw'],1)]:
        p=subprocess.run([str(binary),*args],text=True,capture_output=True,timeout=10)
        assert p.returncode==expected,(p.returncode,p.stdout,p.stderr)
        assert 'AddressSanitizer' not in p.stderr and 'runtime error:' not in p.stderr,p.stderr
    print('PASS RAII/refcount normal + exception cleanup under ASan/UBSan',flush=True)
print('PASS: all 13 C++ examples on OpenSSL 3.5.7; student files unchanged.')
