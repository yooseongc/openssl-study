"""Meaningful checks against compiled learner programs; never compile or replace them."""
import hashlib
import hmac
from pathlib import Path
import re
import subprocess
import sys
from failure_lab import exercise

def verify(lid,root=Path('/home/student/lab')):
    def run(name,*args,code=0):
        binary=root/'examples'/'cpp'/name
        assert binary.is_file(),f'먼저 study-build examples/cpp/{name}.cpp 로 컴파일하세요.'
        p=subprocess.run([str(binary),*args],capture_output=True,text=True,timeout=11)
        out=p.stdout+p.stderr
        assert p.returncode==code,f'{name} {args}: expected exit={code}, actual={p.returncode}\n{out}'
        return out
    if lid=='basic-bytes':assert 'bytes=3 hex=410042 strlen=1' in run('digest','bytes')
    elif lid in ('basic-hash','code-1'):
        for value in ('','abc','한글 입력'):
            assert run('digest','hash',value).strip()==hashlib.sha256(value.encode()).hexdigest()
    elif lid=='basic-random':
        a=run('random_mac','random');b=run('random_mac','random')
        assert re.fullmatch(r'random=[0-9a-f]{64}\n',a) and a!=b
    elif lid=='basic-mac':
        expected=hmac.new(b'study-only-key',b'hello',hashlib.sha256).hexdigest()
        assert expected in run('random_mac','mac','hello')
        assert 'MAC REJECTED' in run('random_mac','tamper','hello',code=2)
    elif lid=='basic-kdf':
        def hkdf(info):
            prk=hmac.new(b'public-salt',b'shared-secret-for-demo',hashlib.sha256).digest()
            return hmac.new(prk,info+b'\x01',hashlib.sha256).hexdigest()
        assert run('kdf','client traffic').strip()==hkdf(b'client traffic')
        assert run('kdf','server traffic').strip()==hkdf(b'server traffic')
    elif lid=='basic-aead':
        assert 'AUTH OK: authenticated message' in run('aead')
        for mode in ('tag','aad','ciphertext'):assert 'AUTH REJECTED' in run('aead',mode,code=2)
    elif lid=='basic-kex':
        assert 'SHARED SECRET MATCH; size=32' in run('kex')
        assert 'set peer' in run('kex','bad-peer',code=1)
    elif lid=='arch-2':
        assert 'provider=default' in run('provider','provider=default')
        assert 'EVP_MD_fetch' in run('provider','provider=missing',code=1)
    elif lid=='arch-ownership':
        assert 'MOVE OK' in run('ownership')
        assert 'intentional exception' in run('ownership','throw',code=1)
    elif lid=='arch-bio':
        assert 'read=3 hex=410042' in run('bio')
        assert 'retry=1' in run('bio','empty')
    elif lid=='arch-errors':assert 'DRAINED; recovery OK' in run('errors')
    elif lid=='x509-api':
        assert 'CHAIN + HOST + PURPOSE OK' in run('x509')
        assert 'hostname mismatch' in run('x509','/home/student/lab/tls/server.pem','/home/student/lab/tls/ca.pem','wrong.example',code=2)
        assert 'open PEM' in run('x509','/missing.pem',code=1)
    elif lid=='code-2':
        assert 'VERIFIED' in run('sign')
        for mode in ('tamper','wrong-key'):assert 'REJECTED' in run('sign',mode,code=2)
    elif lid in ('code-3','code-nonblock','tls-record'):
        mode='nonblock' if lid=='code-nonblock' else 'blocking'
        out=run('tls_client',mode)
        assert 'Verified TLS: TLSv1.3' in out and 'shutdown complete' in out and 'HTTP/1.0 200' in out
        assert 'certificate verify failed' in run('tls_client',mode,'wrong.example',code=1)
    elif lid=='tls-shutdown':exercise(root/'examples/cpp/tls_client')
    elif lid=='code-asio':
        assert 'ASIO VERIFIED' in run('asio_client')
        assert 'certificate verify failed' in run('asio_client','wrong.example',code=1)
    else:raise AssertionError(f'Unknown checkpoint {lid}')
    return f'PASS {lid}: 정상 결과 및 해당 실패 경로 확인'

if __name__=='__main__':
    try:print(verify(sys.argv[1],Path.cwd()))
    except Exception as e:print(f'검사 실패: {e}');sys.exit(1)
