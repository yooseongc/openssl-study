"""Local CA, CRLs, a loopback HTTP OCSP responder, and short-lived TLS servers.

No host trust-store changes. Each child process is owned and reaped by this script.
The HTTP wrapper passes request DER to the real openssl ocsp responder implementation.
"""
import argparse
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from pathlib import Path
import shlex
import socket
import subprocess
import tempfile
import threading
import time


def run(arguments, directory, allowed=(0,), show=False):
    if show:
        print('$ ' + shlex.join(arguments), flush=True)
    result = subprocess.run(arguments, cwd=directory, capture_output=True, text=True, timeout=15)
    if show or result.returncode not in allowed:
        print(result.stdout, end='')
        print(result.stderr, end='')
    if result.returncode not in allowed:
        raise RuntimeError(f'command failed ({result.returncode}): {shlex.join(arguments)}')
    return result


def source(name):
    local = Path.cwd()/'examples/cpp'/name
    return local if local.is_file() else Path('/opt/examples/cpp')/name


def build(name, directory):
    file = source(name + '.cpp')
    target = directory/'bin'/name
    target.parent.mkdir(exist_ok=True)
    run(['g++', '-std=c++20', '-Wall', '-Wextra', '-Werror', '-pthread',
         '-I'+str(file.parent), str(file), '-o', str(target), '-lssl', '-lcrypto'], directory)
    return str(target)


def response(directory, request, output, bad_signature=False):
    args = ['openssl', 'ocsp', '-index', 'index.txt', '-CA', 'ca.pem',
            '-rsigner', 'responder.pem', '-rkey', 'responder.key', '-rmd', 'sha256',
            '-reqin', str(request), '-respout', str(output), '-nmin', '60']
    if bad_signature:
        args.append('-badsig')
    return run(args, directory)


def setup(directory):
    marker = directory/'.study-revocation-v1'
    if directory.exists():
        if not marker.exists():
            raise RuntimeError('Directory already exists and is not a completed lab. Choose --dir another-directory.')
        print(f'Reusing {directory}; existing files kept. Use --dir revocation-2 for fresh fixtures.')
        return
    directory.mkdir(parents=True, mode=0o700)
    (directory/'newcerts').mkdir()
    (directory/'index.txt').write_text('')
    (directory/'index.txt.attr').write_text('unique_subject = no\n')
    (directory/'serial').write_text('1000\n')
    (directory/'crlnumber').write_text('1000\n')
    (directory/'ca.cnf').write_text('''[ ca ]
default_ca = local_ca
[ local_ca ]
dir = .
database = $dir/index.txt
new_certs_dir = $dir/newcerts
certificate = $dir/ca.pem
private_key = $dir/ca.key
serial = $dir/serial
crlnumber = $dir/crlnumber
default_md = sha256
default_days = 365
default_crl_days = 7
policy = names
x509_extensions = server_cert
crl_extensions = crl_ext
[ names ]
commonName = supplied
[ server_cert ]
basicConstraints = critical,CA:FALSE
keyUsage = critical,digitalSignature
extendedKeyUsage = serverAuth
subjectAltName = DNS:localhost
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
[ responder_cert ]
basicConstraints = critical,CA:FALSE
keyUsage = critical,digitalSignature
extendedKeyUsage = OCSPSigning
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
[ crl_ext ]
authorityKeyIdentifier = keyid:always
''')
    run(['openssl', 'req', '-x509', '-newkey', 'ec', '-pkeyopt', 'ec_paramgen_curve:P-256',
         '-noenc', '-keyout', 'ca.key', '-out', 'ca.pem', '-days', '3650', '-subj', '/CN=Revocation Study CA',
         '-addext', 'basicConstraints=critical,CA:TRUE', '-addext', 'keyUsage=critical,keyCertSign,cRLSign'], directory, show=True)
    for name in ('good', 'revoked', 'responder', 'unknown'):
        run(['openssl', 'req', '-new', '-newkey', 'ec', '-pkeyopt', 'ec_paramgen_curve:P-256',
             '-noenc', '-keyout', name+'.key', '-out', name+'.csr', '-subj', '/CN='+name], directory)
        if name == 'unknown':
            # Validly signed leaf deliberately not entered in the responder's CA database.
            run(['openssl', 'x509', '-req', '-in', 'unknown.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key',
                 '-set_serial', '9999', '-days', '365', '-sha256', '-extfile', 'ca.cnf',
                 '-extensions', 'server_cert', '-out', 'unknown.pem'], directory, show=True)
        else:
            run(['openssl', 'ca', '-batch', '-notext', '-config', 'ca.cnf', '-in', name+'.csr',
                 '-out', name+'.pem', '-extensions', 'responder_cert' if name == 'responder' else 'server_cert'], directory, show=True)
    run(['openssl', 'ca', '-config', 'ca.cnf', '-revoke', 'revoked.pem', '-crl_reason', 'keyCompromise'], directory, show=True)
    run(['openssl', 'ca', '-config', 'ca.cnf', '-gencrl', '-out', 'current.crl.pem'], directory, show=True)
    run(['openssl', 'ca', '-config', 'ca.cnf', '-gencrl', '-crl_lastupdate', '20000101000000Z',
         '-crl_nextupdate', '20000102000000Z', '-out', 'stale.crl.pem'], directory, show=True)
    for name in ('good', 'revoked', 'unknown'):
        run(['openssl', 'ocsp', '-issuer', 'ca.pem', '-cert', name+'.pem', '-no_nonce', '-reqout', name+'.req.der'], directory)
        response(directory, name+'.req.der', name+'.der')
    response(directory, 'good.req.der', 'badsig.der', True)
    # The signature is mathematically valid, but a serverAuth leaf is not a delegated OCSP signer.
    run(['openssl', 'ocsp', '-index', 'index.txt', '-CA', 'ca.pem', '-rsigner', 'good.pem',
         '-rkey', 'good.key', '-rmd', 'sha256', '-reqin', 'good.req.der',
         '-respout', 'unauthorized.der', '-nmin', '60'], directory)
    binary = build('ocsp_fixture', directory)
    for mode in ('stale', 'future', 'no-next'):
        run([binary, str(directory), mode], directory, show=True)
    marker.write_text('Local study CA; never install in host trust store.\n')
    print(f'READY {directory}: CA database, CRLs, OCSP DER fixtures')


@contextmanager
def local_responder(directory, bad_signature=False, unavailable=False):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.connection.settimeout(3)
            if unavailable:
                self.send_error(503, 'Study responder unavailable')
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 65536:
                    self.send_error(400)
                    return
                data = self.rfile.read(length)
                if len(data) != length:
                    self.send_error(400)
                    return
                with tempfile.TemporaryDirectory(prefix='ocsp-http-') as temporary:
                    req = Path(temporary)/'request.der'
                    out = Path(temporary)/'response.der'
                    req.write_bytes(data)
                    response(directory, req, out, bad_signature)
                    body = out.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'application/ocsp-response')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError):
                self.send_error(500)
    server = HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def query(directory, mode):
    certificate = mode if mode in ('good', 'revoked', 'unknown') else 'good'
    output = directory/('online-'+mode+'.der')
    with local_responder(directory, mode == 'badsig', mode == 'unavailable') as url:
        args = ['openssl', 'ocsp', '-issuer', 'ca.pem', '-cert', certificate+'.pem',
                '-url', url, '-no_proxy', '127.0.0.1', '-timeout', '3', '-CAfile', 'ca.pem',
                '-no-CApath', '-no-CAstore', '-no_nonce', '-respout', str(output)]
        result = run(args, directory, allowed=(0, 1), show=True)
    print(f'CLI exit={result.returncode}; certificate status must be read separately')
    if mode == 'unavailable':
        if result.returncode == 0:
            raise RuntimeError('Expected transport failure')
        print('UNAVAILABLE: HTTP 503 is not GOOD and not REVOKED')
        return 4
    # The standalone verifier's filename interface accepts the generated online response name.
    binary = build('ocsp_verify', directory)
    checked = run([binary, str(directory), certificate, 'online-'+mode], directory,
                  allowed=(0, 1, 2, 3, 4, 5), show=True)
    print(f'C++ policy exit={checked.returncode}')
    return checked.returncode


@contextmanager
def tls_server(directory, mode):
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    name = mode if mode in ('revoked', 'unknown') else 'good'
    args = ['openssl', 's_server', '-accept', f'127.0.0.1:{port}', '-cert', name+'.pem',
            '-key', name+'.key', '-tls1_3', '-www', '-quiet']
    if mode != 'missing':
        args += ['-status_file', ('revoked' if mode == 'wrong-id' else mode)+'.der']
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(args, cwd=directory, stdout=log, stderr=log)
        try:
            for _ in range(100):
                if process.poll() is not None:
                    log.seek(0)
                    raise RuntimeError(log.read().decode(errors='replace'))
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=.1):
                        break
                except OSError:
                    time.sleep(.02)
            else:
                raise RuntimeError('TLS server readiness timeout')
            print('$ ' + shlex.join(args), flush=True)
            yield port
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def staple(directory, mode, policy):
    binary = build('staple_client', directory)
    with tls_server(directory, mode) as port:
        result = run([binary, str(directory), str(port), policy], directory,
                     allowed=(0, 1, 2, 3, 4, 5), show=True)
    print(f'C++ TLS policy exit={result.returncode}')
    return result.returncode


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'ocsp', 'staple'])
    parser.add_argument('mode', nargs='?', default='good')
    parser.add_argument('--policy', choices=['strict', 'soft-missing'], default='strict')
    parser.add_argument('--dir', default='revocation', help='new isolated directory for setup; existing lab for requests')
    args = parser.parse_args()
    directory = Path(args.dir).resolve()
    if args.action == 'setup':
        setup(directory)
        return 0
    if not (directory/'.study-revocation-v1').is_file():
        raise RuntimeError('Run setup first in this lab directory')
    if args.action == 'ocsp':
        if args.mode not in ('good', 'revoked', 'unknown', 'badsig', 'unavailable'):
            parser.error('ocsp mode: good|revoked|unknown|badsig|unavailable')
        return query(directory, args.mode)
    if args.mode not in ('good', 'revoked', 'unknown', 'badsig', 'missing', 'stale', 'future', 'no-next', 'wrong-id', 'unauthorized'):
        parser.error('unsupported staple mode')
    return staple(directory, args.mode, args.policy)


if __name__ == '__main__':
    raise SystemExit(main())
