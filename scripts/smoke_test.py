"""Verify real crypto and TLS behavior without changing student exercises."""
import hashlib
from pathlib import Path
import subprocess
import tempfile

def run(args, expected=0, data=None):
    result = subprocess.run(args, input=data, text=True, capture_output=True, timeout=12)
    assert result.returncode == expected, f'{args}\nexit={result.returncode}\n{result.stdout}\n{result.stderr}'
    return result.stdout + result.stderr

with tempfile.TemporaryDirectory(prefix='openssl-smoke-') as folder:
    p = Path(folder)
    for name in ['digest', 'provider', 'sign', 'tls_client']:
        run(['gcc', '-Wall', '-Wextra', '-Werror', f'/opt/examples/{name}.c', '-o', str(p/name), '-lssl', '-lcrypto'])
    for value in ['', 'abc', 'hello openssl', '한글 입력']:
        assert run([str(p/'digest'), value]).strip() == hashlib.sha256(value.encode()).hexdigest()
    assert 'provider=default' in run([str(p/'provider')])
    run([str(p/'provider'), 'provider=missing'], 1)
    assert 'VERIFIED' in run([str(p/'sign')])
    assert 'REJECTED' in run([str(p/'sign'), 'tamper'], 2)
    assert 'HTTP/1.0 200' in run([str(p/'tls_client')])
    assert 'certificate verify failed' in run([str(p/'tls_client'), 'wrong.example'], 1)
    run([str(p/'tls_client'), 'localhost', '/missing-ca.pem'], 1)
    run(['openssl', 'dgst', '-md4'], 1, 'abc')
    assert 'a448017aaf21d8525fc10ae87aa6729d' in run(['openssl','dgst','-provider','default','-provider','legacy','-md4'], data='abc')
    run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(p/'ca.key'),'-out',str(p/'ca.pem'),'-days','2','-subj','/CN=Test CA','-addext','basicConstraints=critical,CA:TRUE','-addext','keyUsage=critical,keyCertSign,cRLSign'])
    run(['openssl','req','-new','-newkey','rsa:2048','-nodes','-keyout',str(p/'site.key'),'-out',str(p/'site.csr'),'-subj','/CN=study.local'])
    (p/'site.ext').write_text('subjectAltName=DNS:study.local\nbasicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\nextendedKeyUsage=serverAuth\n')
    run(['openssl','x509','-req','-in',str(p/'site.csr'),'-CA',str(p/'ca.pem'),'-CAkey',str(p/'ca.key'),'-CAcreateserial','-out',str(p/'site.pem'),'-days','1','-extfile',str(p/'site.ext')])
    run(['openssl','verify','-CAfile',str(p/'ca.pem'),'-purpose','sslserver','-verify_hostname','study.local',str(p/'site.pem')])
    run(['openssl','verify','-CAfile',str(p/'ca.pem'),'-verify_hostname','wrong.local',str(p/'site.pem')], 2)
    run(['openssl','x509','-in',str(p/'site.pem'),'-outform','DER','-out',str(p/'site.der')])
    run(['openssl','x509','-inform','DER','-in',str(p/'site.der'),'-out',str(p/'roundtrip.pem')])
    assert (p/'site.pem').read_bytes() == (p/'roundtrip.pem').read_bytes()
print('PASS: 4 C examples; SHA-256 vectors; Provider success/failure; signature tamper; TLS trust/name checks; legacy; CA issuance; DER round trip.')
