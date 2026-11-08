"""Reading goals and source locations, kept separate from general API contracts."""
from pathlib import Path
import re

# Related diagrams and fallback source anchors; explanations live in lesson_text.json.
ROUTES = {'basic-bytes': ('overview', 'const std::array<unsigned char, 3> bytes'),
 'basic-hash': ('overview', 'const auto first_chunk_size'),
 'basic-random': ('overview', 'RAND_bytes_ex('),
 'basic-mac': ('mac', 'auto received = tag'),
 'basic-kdf': ('kdf', 'OSSL_PARAM params[]'),
 'basic-aead': ('aead', 'const int decrypt_data_result'),
 'basic-kex': ('kdf', 'const int set_peer_result'),
 'tls-1': ('tls', None),
 'tls-2': ('tls', None),
 'tls-3': ('x509', None),
 'tls-record': ('tls', 'SSL_read_ex('),
 'tls-shutdown': ('tls', 'SSL_shutdown('),
 'x509-1': ('x509', None),
 'x509-2': ('x509', None),
 'x509-3': ('x509', None),
 'x509-chain': ('x509', None),
 'x509-api': ('x509', 'const int verify_init_result'),
 'arch-1': ('overview', None),
 'arch-2': ('overview', 'study::Md algorithm'),
 'arch-3': ('overview', None),
 'arch-ownership': ('overview', 'const int up_ref_result'),
 'arch-bio': ('overview', 'char* borrowed_data'),
 'arch-errors': ('overview', 'study::Md missing'),
 'code-1': ('overview', 'study::Md algorithm'),
 'code-2': ('signature', 'const int verify_result'),
 'code-3': ('tls', 'SSL_CTX_set_verify('),
 'code-nonblock': ('tls', 'auto wait_ready'),
 'code-asio': ('tls', 'auto finish'),
 'quic-basics': ('quic', 'const pid_t pid = fork()'),
 'quic-connection': ('quic', 'study::Ssl listener'),
 'quic-streams': ('quic', 'study::Ssl stream(SSL_new_stream'),
 'quic-failures': ('quic', 'const char* host ='),
 'quic-events': ('quic', 'void wait_events(')}


ROUTES.update({
    'qat-basics': ('qat', None),
    'qat-provider': ('qat', 'const std::string properties'),
    'qat-async': ('qat', 'int state = ASYNC_start_job'),
    'qat-performance': ('qat', None),
})

ROUTES.update({
    'revocation-basics': ('revocation', None),
    'revocation-crl': ('revocation', 'X509_STORE_set_flags('),
    'revocation-ocsp': ('revocation', 'revocation::verify_ocsp('),
    'revocation-stapling': ('revocation', 'int check_staple('),
    'revocation-api': ('revocation', 'revocation::verify_ocsp('),
})

def enrich(lessons):
    source_root = Path('/opt/examples')
    if not source_root.exists():
        source_root = Path(__file__).resolve().parent.parent / 'examples'

    def excerpt(file, anchor):
        path = source_root / file.removeprefix('examples/')
        lines = path.read_text(encoding='utf8').splitlines()
        found = next((i for i, line in enumerate(lines) if anchor in line and not line.lstrip().startswith('//')), None)
        if found is None:
            raise ValueError(f'Missing teaching anchor: {file}: {anchor}')
        start = max(0, found - 1)
        end = min(len(lines), found + 9)
        # Finish the current statement rather than cutting a multiline argument list.
        while end < min(len(lines), found + 18) and lines[end-1].strip() and not lines[end-1].rstrip().endswith((';', '}')):
            end += 1
        return dict(file=file, anchor=anchor, line=start+1, text='\n'.join(lines[start:end]))

    by_id = {lesson['id']: lesson for lesson in lessons}
    cli_targets = {
        'revocation-basics': [('revocation-crl', 2)],
        'qat-basics': [('qat-provider', 0), ('qat-provider', 2)],
        'qat-performance': [('qat-provider', 0), ('qat-performance', 0)],
        'tls-1': [('code-3', 0)],
        'tls-2': [('code-3', 0), ('code-nonblock', 0)],
        'tls-3': [('code-3', 1)],
        'x509-1': [('x509-api', 0)],
        'x509-2': [('x509-2', 1), ('x509-2', 2)],
        'x509-3': [('x509-3', 0), ('x509-api', 0)],
        'x509-chain': [('x509-api', 0), ('x509-chain', 1)],
        'arch-1': [('arch-1', 0)],
        'arch-3': [('arch-2', 0), ('arch-2', 1)],
    }
    reference_targets = {
        ('basic-random', 'RAND_priv_bytes(buf, num)'): [('basic-aead', 0)],
        ('arch-ownership', 'SSL_get1_peer_certificate(ssl)'): [('code-3', 0)],
        ('arch-errors', 'SSL_get_error(ssl, ret)'): [('code-nonblock', 0), ('tls-shutdown', 1)],
    }
    for lesson in lessons:
        flow, anchor = ROUTES[lesson['id']]
        lesson['reading'] = dict(flow=flow)
        file = lesson.get('file')
        if file and anchor:
            lesson['reading']['code'] = excerpt(file, anchor)
        if file:
            for section in lesson.get('sections', []):
                anchor = section.get('code_anchor')
                if anchor:
                    section['code'] = excerpt(section.get('code_file', file), anchor)
        for api in lesson.get('apis', []):
            targets = reference_targets.get((lesson['id'], api['name']),
                cli_targets.get(lesson['id'], [(lesson['id'], 1 if lesson['id'] in {'basic-kex', 'quic-basics'} else 0)]))
            api['practice_links'] = [dict(
                lesson=id, step=index, title=by_id[id]['title'],
                label=by_id[id]['steps'][index]['title'],
                href=f'/#{id}/step/{index+1}') for id, index in targets]
            # Only link calls that are actually present; grouped and conceptual APIs
            # are never presented as a single C function prototype.
            symbols = re.findall(r'\b(?:EVP|SSL|OSSL|RAND|BIO|X509|PEM|ERR|CRYPTO|TLS|OpenSSL|ASYNC|OCSP)_[A-Za-z0-9_]+', api['name'])
            if 'native_handle' in api['name']:
                symbols = ['native_handle']
            elif api['name'].startswith('async_handshake'):
                symbols = ['async_handshake', 'async_read_some', 'async_write']
            if not file:
                continue
            api['examples'] = []
            for symbol in dict.fromkeys(symbols):
                try:
                    api['examples'].append(excerpt(file, symbol+'('))
                except ValueError:
                    continue
                if len(api['examples']) == 2:
                    break
            related = {
                'RAND_priv_bytes(buf, num)': 'examples/cpp/aead.cpp',
                'SSL_get1_peer_certificate(ssl)': 'examples/cpp/tls_client.cpp',
                'SSL_get_error(ssl, ret)': 'examples/cpp/tls_client.cpp',
            }
            if not api['examples'] and lesson['id'].startswith('revocation-'):
                for symbol in symbols:
                    try:
                        api['examples'].append(excerpt('examples/cpp/revocation.hpp', symbol+'('))
                    except ValueError:
                        continue
                    break
            if not api['examples'] and api['name'] in related:
                other_file = related[api['name']]
                api['examples'].append(excerpt(other_file, symbols[0]+'('))
                continue
