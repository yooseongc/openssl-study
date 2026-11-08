"""Exercise signed revocation material and real local HTTP/TLS without student file changes."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import tempfile
import revocation_lab as lab


def execute(args, directory, code, marker):
    result = subprocess.run(args, cwd=directory, capture_output=True, text=True, timeout=15)
    assert result.returncode == code, (args, result.returncode, result.stdout, result.stderr)
    assert marker in result.stdout + result.stderr, (args, result.stdout, result.stderr)


with tempfile.TemporaryDirectory(prefix='revocation-test-') as temporary:
    directory = Path(temporary)/'pki'
    with redirect_stdout(StringIO()):
        lab.setup(directory)
        crl = lab.build('crl_verify', directory)
        ocsp = lab.build('ocsp_verify', directory)
    for cert, mode, code, marker in [
        ('good','current',0,'CHAIN + NAME + PURPOSE OK'),
        ('revoked','current',5,'certificate revoked'),
        ('good','missing',5,'unable to get certificate CRL'),
        ('good','stale',5,'CRL has expired'),
    ]:
        execute([crl,str(directory),cert,mode], directory, code, marker)
        print(f'PASS CRL {cert}/{mode}: {marker}', flush=True)
    for cert, response, code, marker in [
        ('good','good',0,'GOOD:'),('revoked','revoked',2,'REVOKED:'),
        ('unknown','unknown',3,'UNKNOWN:'),('good','revoked',5,'different certificate'),
        ('good','badsig',5,'signature or signer authorization'),
        ('good','unauthorized',5,'signature or signer authorization'),
        ('good','stale',5,'stale, future'),('good','future',5,'stale, future'),
        ('good','no-next',5,'missing nextUpdate'),
    ]:
        execute([ocsp,str(directory),cert,response], directory, code, marker)
        print(f'PASS OCSP DER {cert}/{response}: exit={code}', flush=True)
    (directory/'malformed.der').write_bytes(b'not DER')
    execute([ocsp,str(directory),'good','malformed'],directory,5,'malformed DER')
    print('PASS malformed OCSP rejected',flush=True)
    for mode, code in [('good',0),('revoked',2),('unknown',3),('badsig',5),('unavailable',4)]:
        output=StringIO()
        with redirect_stdout(output):
            actual=lab.query(directory,mode)
        assert actual == code, (mode,actual,output.getvalue())
        print(f'PASS HTTP OCSP {mode}: exit={code}',flush=True)
    for mode, policy, code in [
        ('good','strict',0),('revoked','strict',2),('unknown','strict',3),
        ('missing','strict',4),('stale','strict',5),('badsig','strict',5),
        ('wrong-id','strict',5),('unauthorized','strict',5),('future','strict',5),('no-next','strict',5),('missing','soft-missing',0),('revoked','soft-missing',2),
    ]:
        output=StringIO()
        with redirect_stdout(output):
            actual=lab.staple(directory,mode,policy)
        assert actual == code, (mode,policy,actual,output.getvalue())
        if policy == 'soft-missing' and mode == 'missing':
            assert 'status NOT established' in output.getvalue()
        print(f'PASS TLS staple {mode}/{policy}: exit={code}',flush=True)
print('PASS revocation suite: CRL, signed OCSP, HTTP, TLS stapling; temporary workspace only')
