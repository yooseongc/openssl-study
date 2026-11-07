import asyncio
import os
import signal

COMMANDS = {
 'tls-1': "openssl s_client -connect 127.0.0.1:4433 -servername localhost -CAfile tls/ca.pem -verify_hostname localhost -verify_return_error -brief </dev/null",
 'tls-2': "test -f handshake.txt && grep ClientHello handshake.txt && grep ServerHello handshake.txt && grep CertificateVerify handshake.txt && grep Finished handshake.txt",
 'tls-3': "if openssl s_client -connect 127.0.0.1:4433 -CAfile tls/ca.pem -verify_hostname wrong.example -verify_return_error </dev/null > /tmp/check-host.txt 2>&1; then exit 1; fi; grep 'hostname mismatch' /tmp/check-host.txt",
 'x509-1': "openssl x509 -in tls/server.pem -noout -ext subjectAltName | grep 'DNS:localhost'",
 'x509-2': "openssl verify -CAfile pki/root.pem -purpose sslserver -verify_hostname study.local pki/site.pem",
 'x509-3': "test -f pki/site.der && cmp <(openssl x509 -in pki/site.pem -outform DER) <(openssl x509 -in pki/roundtrip.pem -outform DER) && cmp pki/site.der <(openssl x509 -in pki/site.pem -outform DER) && echo 'PEM / DER round trip OK'",
 'arch-1': "openssl list -providers | grep default && ldd /usr/bin/openssl | grep libcrypto.so.3",
 'arch-2': "./examples/provider provider=default && if ./examples/provider provider=missing; then exit 1; else echo 'Missing provider correctly rejected'; fi",
 'arch-3': "printf abc | openssl dgst -provider default -provider legacy -md4 | grep a448017aaf21d8525fc10ae87aa6729d",
 'code-1': "test \"$(./examples/digest abc)\" = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad && test \"$(./examples/digest '')\" = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 && echo 'SHA-256 abc + empty string OK'",
 'code-2': "./examples/sign; set +e; ./examples/sign tamper; status=$?; test $status -eq 2 && echo 'Tampered message rejected with exit 2'",
 'code-3': "./examples/tls_client > /tmp/check-tls.txt; grep 'Verified TLS: TLSv1.3' /tmp/check-tls.txt; grep 'HTTP/1.0 200' /tmp/check-tls.txt; if ./examples/tls_client wrong.example >/tmp/check-tls-bad.txt 2>&1; then exit 1; fi; grep 'certificate verify failed' /tmp/check-tls-bad.txt",
}

CPP_IDS = ['basic-bytes','basic-hash','basic-random','basic-mac','basic-kdf','basic-aead','basic-kex',
           'tls-record','tls-shutdown','x509-api','arch-2','arch-ownership','arch-bio','arch-errors',
           'code-1','code-2','code-3','code-nonblock','code-asio']
for lid in CPP_IDS:
    COMMANDS[lid] = f'python /opt/scripts/check_cpp.py {lid}'
COMMANDS['x509-chain'] = "openssl verify -CAfile chain/root.pem -untrusted chain/intermediate.pem -purpose sslserver -verify_hostname chain.local chain/leaf.pem"

async def check(lid):
    proc = await asyncio.create_subprocess_exec('/bin/bash', '-e', '-o', 'pipefail', '-c', COMMANDS[lid],
        cwd='/home/student/lab', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, start_new_session=True)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), 12)
        return {'ok': proc.returncode == 0, 'output': out.decode(errors='replace')[-12000:], 'exit': proc.returncode}
    except asyncio.TimeoutError:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        await proc.communicate()
        return {'ok': False, 'output': '검사 시간 초과. lab-server status로 서버와 프로그램을 확인하세요.', 'exit': 124}

# Internal regression checks; no automatic exercise checker is exposed in the UI.
COMMANDS['quic-basics'] = "timeout 12 ./examples/cpp/quic_local ok | grep 'PASS ok'"
COMMANDS['quic-connection'] = COMMANDS['quic-basics']
COMMANDS['quic-streams'] = "timeout 12 ./examples/cpp/quic_local multi | grep 'stream=8'"
COMMANDS['quic-events'] = "timeout 12 ./examples/cpp/quic_local epoll | grep 'PASS epoll'"
COMMANDS['quic-failures'] = "python /opt/scripts/quic_test.py --existing"
