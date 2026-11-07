"""Reading goals and source locations, kept separate from general API contracts."""
from pathlib import Path
import re

# id: prerequisite, question, observable outcome, visual topic, source anchor
ROUTES = {
 'basic-bytes': ('C++의 배열과 문자열을 구분할 수 있으면 시작할 수 있습니다.', '암호 함수는 화면의 글자를 받는가, 메모리의 바이트를 받는가?', 'bytes 모드에서 배열 길이 3과 strlen 결과 1이 다른 이유를 설명해 보세요.', 'overview', "const std::array<unsigned char, 3> bytes"),
 'basic-hash': ('앞 레슨에서 바이트 수와 문자열 길이를 구분했습니다.', '같은 메시지를 나누어 넣어도 해시가 같을까?', '두 Update가 같은 digest_context에 입력을 이어 넣고 Final이 결과를 꺼내는 흐름을 확인합니다.', 'overview', 'const auto first_chunk_size'),
 'basic-random': ('해시는 같은 입력에서 같은 결과를 얻는 계산이었습니다. 이번에는 예측하기 어려운 값을 생성합니다.', '32바이트라는 길이만으로 안전한 난수라고 할 수 있을까?', 'random을 두 번 실행해 보세요. 결과가 다르다는 관찰과 예측 불가능성을 구분해야 합니다.', 'overview', 'RAND_bytes_ex('),
 'basic-mac': ('해시만으로는 누가 메시지를 만들었는지 알 수 없었습니다. 이번에는 양쪽이 비밀키를 공유한다고 가정합니다.', '받은 메시지가 공유키를 아는 쪽에서 만들어졌는지 어떻게 확인할까?', 'mac은 exit=0, tamper는 exit=2입니다. 이 예제는 태그 비교를 실험하며 실제 네트워크 수신이나 수신 메시지의 재계산은 구현하지 않습니다.', 'mac', 'auto received = tag'),
 'basic-kdf': ('HMAC의 출력은 인증 태그였습니다. HKDF는 HMAC을 사용해 비밀로 보관할 키 재료를 만듭니다.', '같은 공유 비밀에서 송신용·수신용 키를 어떻게 구분할까?', 'info만 바꾸었을 때 출력이 바뀌는지 비교합니다. 이 코드는 Extract와 Expand를 한 derive 호출로 수행하는 기본 HKDF 모드입니다.', 'kdf', 'OSSL_PARAM params[]'),
 'basic-aead': ('HMAC은 무결성을 제공하지만 원문을 숨기지는 않습니다. 이번에는 두 기능을 함께 사용합니다.', '복호화 결과가 나왔다는 이유만으로 사용해도 될까?', 'ok와 tag/aad/ciphertext 모드를 비교하고, plaintext_candidate가 최종 인증 뒤에만 출력되는지 확인합니다.', 'aead', 'const int decrypt_data_result'),
 'basic-kex': ('앞 실습에서는 키 재료를 이미 갖고 있다고 가정했습니다. 이번에는 두 참여자가 같은 비밀을 계산합니다.', '개인키를 보내지 않고 같은 비밀을 얻는 과정은 무엇인가?', '두 derive 결과가 일치해도 신원 인증은 끝나지 않았다는 점을 확인합니다. bad-peer는 X25519 대신 Ed25519 상대 키를 넣는 실패 실험입니다.', 'kdf', 'const int set_peer_result'),
 'tls-1': ('키 합의, 키 유도, 서명, AEAD의 역할을 배웠습니다. TLS가 이들을 한 연결에 결합합니다.', 'TLS 연결에는 왜 여러 암호 기법이 필요한가?', 's_client 출력에서 버전·암호 스위트·검증 결과를 찾아 각각 무엇을 뜻하는지 구분합니다.', 'tls', None),
 'tls-2': ('TLS의 구성요소를 알았다면 이제 실제 핸드셰이크 순서와 연결해 봅니다.', 'Certificate, CertificateVerify, Finished는 각각 무엇을 증명하는가?', '-msg로 저장한 handshake.txt와 흐름 지도의 메시지 순서를 비교합니다. 이 출력은 OpenSSL 내부 관찰이며 패킷 캡처와 다릅니다.', 'tls', None),
 'tls-3': ('핸드셰이크 흐름 중 서버 인증 단계에 집중합니다.', '암호화는 가능해도 연결을 거부해야 하는 경우는 언제인가?', 'SNI는 localhost로 두고 검증 이름만 바꿨을 때 hostname mismatch가 발생하는지 확인합니다.', 'x509', None),
 'tls-record': ('핸드셰이크가 끝난 뒤 애플리케이션 바이트를 읽는 단계입니다.', 'read 한 번이 메시지 하나와 같은가?', '읽기 반복문이 bytes_read만큼만 누적하는지 봅니다. TCP 세그먼트·TLS 레코드·HTTP 응답 경계는 같지 않습니다.', 'tls', 'SSL_read_ex('),
 'tls-shutdown': ('데이터를 읽은 뒤에도 정상 종료와 중간 절단을 구분해야 합니다.', '소켓이 닫혔다는 사실만으로 응답을 모두 받았다고 할 수 있는가?', '정상 서버와 failure_lab.py의 강제 종료 서버를 비교합니다. SSL_shutdown의 0은 일반적인 API 실패 0과 의미가 다릅니다.', 'tls', 'SSL_shutdown('),
 'x509-1': ('TLS에서 받은 인증서를 파일로 살펴봅니다.', '인증서 안에는 누구의 공개키와 누구의 서명이 있는가?', 'Subject, Issuer, 공개키 알고리즘, 서명 알고리즘을 구분해 읽습니다. x509 -text는 신뢰 검증 명령이 아닙니다.', 'x509', None),
 'x509-2': ('인증서 필드를 읽었다면 CSR을 제출하고 발급받는 과정을 살펴봅니다.', '요청자가 원하는 정보와 CA가 보증하는 정보는 어떻게 다른가?', 'CSR과 발급 인증서의 Subject·SAN·확장을 비교하고, CA 서명 뒤 어떤 정보가 인증서에 들어갔는지 확인합니다.', 'x509', None),
 'x509-3': ('같은 인증서를 서로 다른 파일 표현으로 저장해 봅니다.', 'PEM을 DER로 바꾸면 인증서의 의미도 달라지는가?', 'PEM → DER → PEM 왕복에서 인증서 바이트를 DER로 맞추어 비교합니다. 텍스트 줄바꿈만 비교하면 안 됩니다.', 'x509', None),
 'x509-chain': ('인증서 한 장의 서명을 넘어 신뢰 루트까지 이어지는 경로를 검사합니다.', '중간 인증서를 받는 것과 신뢰 루트를 선택하는 것은 어떻게 다른가?', '-untrusted의 중간 인증서와 -CAfile의 신뢰 루트를 구분하고, 중간 인증서 누락 시 실패를 확인합니다.', 'x509', None),
 'x509-api': ('명령행에서 수행한 인증서 검증을 C++ 객체와 호출로 옮깁니다.', '파싱, 검증 정책 설정, 검증 실행은 코드의 어디에서 나뉘는가?', 'certificate는 파싱 결과이고 verify_context는 이번 검증 상태입니다. 이름을 바꾸면 파싱 성공 이후 검증이 거부됩니다.', 'x509', 'const int verify_init_result'),
 'arch-1': ('앞에서 사용한 openssl 명령과 EVP API가 어떤 구현을 사용하는지 살펴봅니다.', '알고리즘 이름, 라이브러리, Provider는 어떤 관계인가?', 'openssl list -providers와 연결 라이브러리 출력을 비교합니다. Provider는 알고리즘 구현을 공급하며 인증서의 발급자와는 다릅니다.', 'overview', None),
 'arch-2': ('Provider의 역할을 확인한 뒤 구현 선택 조건을 직접 지정합니다.', 'SHA256이라는 이름이 있는데도 fetch가 실패할 수 있는가?', 'provider=default와 provider=missing을 비교합니다. 실패 시 algorithm이 비어 있으므로 계산 초기화로 넘어가면 안 됩니다.', 'overview', 'study::Md algorithm'),
 'arch-3': ('구현 선택이 결과에 영향을 주는 이유를 바탕으로 기존 코드를 이식할 때의 판단을 정리합니다.', '예전 알고리즘이 동작하게 만드는 것과 새 코드에 채택하는 것은 같은 결정인가?', 'legacy Provider로 MD4를 실행하되, 호환성 실험의 성공을 알고리즘의 안전성 판단으로 해석하지 않습니다.', 'overview', None),
 'arch-ownership': ('앞 예제의 get(), reset(), Handle이 실제로 어떤 해제 책임을 표현하는지 확인합니다.', '포인터가 같으면 소유자도 하나인가?', 'first_owner를 reset해도 second_owner가 객체를 유지합니다. move는 참조 추가가 아니라 소유자 교체입니다.', 'overview', 'const int up_ref_result'),
 'arch-bio': ('객체 소유권을 배웠다면 내부 버퍼를 잠시 빌리는 경우를 살펴봅니다.', 'BIO 내부 메모리를 조회하는 것과 복사해 읽는 것은 어떻게 다른가?', 'borrowed_data는 소유하지 않은 포인터이고, read_buffer는 호출자 버퍼입니다. read 이후에도 같은 내부 뷰가 유효하다고 가정하지 않습니다.', 'overview', 'char* borrowed_data'),
 'arch-errors': ('성공 경로뿐 아니라 실패 원인을 호출 위치와 함께 기록하는 연습입니다.', '오류 큐와 함수 반환값은 각각 무엇을 알려주는가?', '없는 알고리즘을 fetch해 오류를 만든 뒤 peek과 get의 차이를 봅니다. 오류 큐를 읽고 비웠다는 사실과 실패를 복구했다는 사실은 다릅니다.', 'overview', 'study::Md missing'),
 'code-1': ('basic-hash에서 사용한 digest.cpp를 다시 엽니다. 이번에는 결과보다 C++ 객체의 수명과 함수 인자를 봅니다.', '누가 알고리즘과 계산 상태를 소유하고 언제 해제하는가?', 'algorithm과 digest_context의 get()은 포인터를 빌려줍니다. 실패 시 study::require가 던진 예외가 catch에 도착하기 전에 지역 핸들이 정리됩니다.', 'overview', 'study::Md algorithm'),
 'code-2': ('HMAC에서는 양쪽이 같은 키를 가졌습니다. 서명은 개인키와 공개키의 역할을 분리합니다.', '검증자는 개인키 없이 무엇을 검사하는가?', 'message는 서명 입력, received_message는 검증 입력입니다. tamper와 wrong-key가 서로 다른 입력을 바꾸지만 모두 거부되는지 확인합니다.', 'signature', 'const int verify_result'),
 'code-3': ('TLS 명령행 실습을 C++ 클라이언트로 옮깁니다. 먼저 blocking 모드로 큰 순서를 익힙니다.', 'TCP 연결부터 응답 종료까지 필요한 TLS 설정은 어디에 있는가?', 'tls_context 설정 → fd 연결 → SSL 객체 설정 → 핸드셰이크 → 요청/응답 → 종료 순서로 읽습니다.', 'tls', 'SSL_CTX_set_verify('),
 'code-nonblock': ('같은 tls_client.cpp의 nonblock 모드입니다. 새 연결을 만들지 않고 중단한 연산을 이어갑니다.', 'WANT_READ/WRITE 이후 어떤 입력과 상태를 보존해야 하는가?', 'wait_ready가 필요한 이벤트를 기다린 뒤 같은 SSL 호출을 재시도하는지 확인합니다. 이벤트 발생 자체가 연산 성공은 아닙니다.', 'tls', 'auto wait_ready'),
 'code-asio': ('직접 epoll을 구동한 흐름을 Asio의 완료 콜백으로 옮깁니다.', '비동기 요청을 시작한 함수가 반환된 뒤에도 무엇이 살아 있어야 하는가?', 'request·buffer·stream의 수명과 finished 플래그를 봅니다. native_handle은 설정에 빌려 쓰며 Asio와 원시 SSL I/O를 섞지 않습니다.', 'tls', 'auto finish'),
 'quic-basics': ('TLS 1.3의 역할을 알고 있다면 QUIC에서 전송 계층이 어떻게 달라지는지 비교합니다.', 'QUIC은 TLS를 어디에 사용하고 전송은 누가 담당하는가?', 'ok 모드로 로컬 echo를 실행합니다. study/1은 실습용 프로토콜이며 HTTP/3 응답을 구현한 것이 아닙니다.', 'quic', 'const pid_t pid = fork()'),
 'quic-connection': ('로컬 QUIC 실행이 되었다면 서버와 클라이언트의 연결 설정을 나눠 읽습니다.', 'listener, connection, UDP fd는 각각 무엇을 나타내는가?', 'serve의 listener와 main의 connection을 구분합니다. 접속 주소, SNI, 이름 검증, ALPN은 따로 설정됩니다.', 'quic', 'study::Ssl listener'),
 'quic-streams': ('연결 하나 안에서 별도 stream 객체로 데이터를 주고받습니다.', '스트림의 한 방향 종료와 전체 연결 종료는 어떻게 다른가?', 'multi 모드의 ID 0·4·8과 FIN을 확인합니다. send_message는 송신 방향을 끝내고 receive_message는 수신 FIN까지 읽습니다.', 'quic', 'study::Ssl stream(SSL_new_stream'),
 'quic-failures': ('정상 연결 설정 중 조건 하나씩 바꾸어 거부 이유를 확인합니다.', '이름 검증 실패와 ALPN 불일치를 어떻게 구분하는가?', 'bad-host와 bad-alpn 모두 exit=1입니다. verify: ok만으로 전체 핸드셰이크 성공을 판단하지 않습니다.', 'quic', 'const char* host ='),
 'quic-events': ('blocking 연결을 이해한 뒤 클라이언트 I/O를 비동기로 바꿉니다.', '소켓 이벤트가 없어도 QUIC을 다시 실행해야 하는 이유는 무엇인가?', 'transfer에서 WANT를 만나면 wait_events가 네트워크 요구와 타이머를 조회합니다. 서버와 마지막 종료는 여전히 blocking입니다.', 'quic', 'void wait_events('),
}

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
        before, question, observe, flow, anchor = ROUTES[lesson['id']]
        lesson['reading'] = dict(before=before, question=question, observe=observe, flow=flow)
        file = lesson.get('file')
        if file and anchor:
            lesson['reading']['code'] = excerpt(file, anchor)
        section_anchors = {
            '예제 코드 읽기': 'const auto first_chunk_size',
            '검증과 오류 구분': 'auto received = tag',
            '코드에서 신뢰 경계 찾기': 'const int decrypt_data_result',
            '두 단계 출력 버퍼 API': 'size_t size = 0',
            '검증 파라미터의 의미': 'X509_VERIFY_PARAM* verify_parameters',
            '명시적 fetch의 수명': 'study::Md algorithm',
            '주소와 소유권은 다르다': 'const int up_ref_result',
            'write와 read 사이': 'char* borrowed_data',
            '이제 C++ 객체 관점으로 다시 읽기': 'study::Md algorithm',
            '콜백과 버퍼 수명': 'const std::string request',
            '서버의 준비 순서': 'study::Ssl listener',
            '예제의 재시도 루프': 'bool transfer(',
        }
        if file:
            for section in lesson.get('sections', []):
                anchor = section_anchors.get(section['title'])
                if anchor:
                    section['code'] = excerpt(file, anchor)
        for api in lesson.get('apis', []):
            targets = reference_targets.get((lesson['id'], api['name']),
                cli_targets.get(lesson['id'], [(lesson['id'], 1 if lesson['id'] in {'basic-kex', 'quic-basics'} else 0)]))
            api['practice_links'] = [dict(
                lesson=id, step=index, title=by_id[id]['title'],
                label=by_id[id]['steps'][index]['title'],
                href=f'/#{id}/step/{index+1}') for id, index in targets]
            # Only link calls that are actually present; grouped and conceptual APIs
            # are never presented as a single C function prototype.
            symbols = re.findall(r'\b(?:EVP|SSL|OSSL|RAND|BIO|X509|PEM|ERR|CRYPTO|TLS|OpenSSL)_[A-Za-z0-9_]+', api['name'])
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
            if not api['examples'] and api['name'] in related:
                other_file = related[api['name']]
                api['examples'].append(excerpt(other_file, symbols[0]+'('))
                continue
