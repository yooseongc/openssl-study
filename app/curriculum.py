"""Korean lessons. Commands are deliberately visible and explicitly user-triggered."""
LESSONS = []
def lesson(id, module, title, minutes, intro, concepts, steps, question, options, answer, explanation, docs, file=None):
    LESSONS.append(dict(id=id, module=module, title=title, minutes=minutes, intro=intro, concepts=concepts,
        steps=[dict(title=s[0], text=s[1], command=s[2], expect=s[3]) for s in steps],
        quiz=dict(question=question, options=options, answer=answer, explanation=explanation), docs=docs, file=file))

lesson('tls-1', 1, '암호화 연결의 첫 순간', 15,
 '준비된 로컬 서버에 연결하면서 TLS가 실제로 협상하는 값을 관찰합니다. 서버와 CA는 실습 전용이며 호스트 PC의 신뢰 저장소에는 설치하지 않습니다.',
 ['TLS는 전송 구간의 기밀성·무결성과 상대 인증을 제공합니다. 일반적인 HTTPS는 서버를 인증하고, 클라이언트 인증서는 선택 사항입니다.',
  'TLS 1.3에서 (EC)DHE는 공유 비밀을 만들고 HKDF가 트래픽 키를 유도합니다. 인증서의 공개키로 HTTP 본문 전체를 암호화하는 방식이 아닙니다.',
  '암호 스위트는 TLS 1.3에서 AEAD와 해시를 정합니다. 키 교환 그룹과 서명 알고리즘은 따로 협상합니다.'],
 [('환경 확인', 'OpenSSL 버전, 작업 경로, 준비된 서버를 확인합니다.', 'openssl version -a\npwd\nlab-server status', 'OpenSSL 3.x, /home/student/lab, running :4433'),
  ('검증하는 연결', 'CA 신뢰와 호스트 이름을 모두 검사합니다. EOF로 입력을 종료합니다.', 'openssl s_client -connect 127.0.0.1:4433 -servername localhost -CAfile ~/lab/tls/ca.pem -verify_hostname localhost -verify_return_error -brief </dev/null', 'TLSv1.3, Verification: OK. 출력 일부는 stderr에 표시됩니다.')],
 'TLS 1.3에서 인증서 공개키의 주된 역할은?', ['HTTP 본문 전체 암호화', '서버 인증에 사용되는 서명 검증', '세션 키를 평문으로 전달'], 1,
 '인증서의 공개키로 CertificateVerify 서명을 검증합니다. 실제 애플리케이션 데이터는 별도로 유도한 대칭키로 보호합니다.',
 ['https://docs.openssl.org/3.5/man1/openssl-s_client/', 'https://www.rfc-editor.org/rfc/rfc8446'])

lesson('tls-2', 1, '핸드셰이크를 한 줄씩 추적하기', 20,
 '메시지 흐름과 실제 OpenSSL 출력을 연결해 봅니다. -msg는 TLS 구현 내부에서 복호화된 핸드셰이크도 보여주므로 네트워크 패킷 캡처와 같지 않습니다.',
 ['ClientHello는 지원 버전·암호 스위트·키 공유 등을 보냅니다. ServerHello가 협상 결과와 서버 키 공유를 응답합니다.',
  '일반적인 TLS 1.3 전체 핸드셰이크에서 ServerHello 이후의 EncryptedExtensions, Certificate, CertificateVerify, Finished는 암호화됩니다.',
  'CertificateVerify는 서명으로 개인키 소유를 증명하고, Finished는 핸드셰이크 transcript에 대한 검증값입니다. 세션 재개는 다른 흐름을 가질 수 있습니다.'],
 [('기록 남기기', '출력을 파일로 남기고 메시지 이름을 찾아봅니다.', 'openssl s_client -connect 127.0.0.1:4433 -servername localhost -CAfile ~/lab/tls/ca.pem -verify_hostname localhost -verify_return_error -tls1_3 -msg -state </dev/null > ~/lab/handshake.txt 2>&1\ngrep -E "ClientHello|ServerHello|EncryptedExtensions|CertificateVerify|Finished|Verification" ~/lab/handshake.txt', 'ClientHello → ServerHello → … → CertificateVerify → Finished'),
  ('HTTP 요청 보내기', 'TLS 연결 위에 HTTP 요청을 보내 봅니다. timeout은 실습이 무한히 기다리는 것을 방지합니다.', 'printf "GET / HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n" | timeout 8 openssl s_client -connect 127.0.0.1:4433 -servername localhost -CAfile ~/lab/tls/ca.pem -verify_hostname localhost -verify_return_error -quiet', 'HTTP/1.0 200 ok 및 s_server 상태 페이지')],
 'CertificateVerify와 Finished에 대한 올바른 설명은?', ['둘 다 인증서 파일이다', '각각 서명 기반 개인키 소유 증명과 핸드셰이크 무결성 검증을 담당한다', '둘 다 평문 HTTP 응답이다'], 1,
 '두 메시지는 다른 암호학적 역할을 합니다. 인증서 자체를 보내는 것만으로 개인키를 보유했다는 증명이 끝나지는 않습니다.',
 ['https://www.rfc-editor.org/rfc/rfc8446#section-4', 'https://docs.openssl.org/3.5/man1/openssl-s_client/'])

lesson('tls-3', 1, '실패를 통해 배우는 인증', 15,
 '암호화 연결이 만들어지는 것과 믿을 수 있는 상대에게 연결하는 것은 별개의 조건입니다. 의도적인 실패를 재현합니다.',
 ['체인 검증은 신뢰할 CA까지 이어지는 서명·제약·유효기간 등을 확인합니다. 호스트 이름 검증은 접속 대상 이름과 인증서 SAN을 비교합니다.',
  '-servername은 SNI를 전송하는 옵션이며 호스트 이름 검증을 켜 주지 않습니다.',
  's_client는 진단 도구라 기본적으로 검증 오류 이후에도 진행할 수 있습니다. -verify_return_error로 오류 때 중단하도록 합니다.'],
 [('잘못된 이름', '실패하는 것이 정답입니다. 바로 다음 줄에서 종료 코드를 확인하세요.', 'openssl s_client -connect 127.0.0.1:4433 -servername localhost -CAfile ~/lab/tls/ca.pem -verify_hostname wrong.example -verify_return_error -brief </dev/null\necho "exit=$?"', 'hostname mismatch 및 0이 아닌 종료 코드'),
  ('신뢰할 CA 제거', '모든 기본 CA 소스를 제외합니다.', 'openssl s_client -connect 127.0.0.1:4433 -servername localhost -no-CAfile -no-CApath -no-CAstore -verify_return_error -brief </dev/null\necho "exit=$?"', 'unable to get local issuer certificate 등 인증서 검증 실패')],
 'SNI를 localhost로 설정하면 호스트 이름 검증도 자동으로 활성화될까요?', ['예', '아니요, 별도로 검증을 설정해야 합니다'], 1,
 'SNI는 서버가 인증서·가상 호스트를 선택하게 돕습니다. 검증은 -verify_hostname 또는 SSL_set1_host로 설정합니다.',
 ['https://docs.openssl.org/3.5/man1/openssl-verification-options/'])

lesson('x509-1', 2, '인증서를 읽는 눈', 15,
 '인증서는 공개키와 주체 정보, 확장 필드, 발급자 서명을 묶은 구조입니다. 개인키는 들어 있지 않습니다.',
 ['Subject와 Issuer는 인증서 주체와 발급자를 나타냅니다. 이름 문자열이 같다고 신뢰가 성립하는 것은 아닙니다.',
  'SAN은 서비스의 DNS 이름 등을 담습니다. Basic Constraints는 CA 여부를, Key Usage와 Extended Key Usage는 사용 목적을 제한합니다.',
  '인증서 fingerprint는 인증서 전체의 해시입니다. 공개키만의 해시와는 다릅니다.'],
 [('전체 구조', 'Signature Algorithm과 Public Key Algorithm도 비교해 보세요.', 'openssl x509 -in ~/lab/tls/server.pem -noout -text', 'CA:FALSE, DNS:localhost, TLS Web Server Authentication'),
  ('필드만 추출', '운영 중 자주 사용하는 출력 옵션입니다.', 'openssl x509 -in ~/lab/tls/server.pem -noout -subject -issuer -dates -serial -fingerprint -sha256\nopenssl x509 -in ~/lab/tls/server.pem -noout -ext subjectAltName\nopenssl x509 -in ~/lab/tls/server.pem -checkend 86400 -noout', '발급자·유효기간·SHA-256 fingerprint. 최소 하루 유효하면 exit 0.')],
 '서버가 접속 대상 DNS 이름에 대해 발급되었는지 확인할 핵심 필드는?', ['Serial Number', 'Subject Alternative Name', '개인키'], 1,
 'SAN의 DNS 항목이 핵심입니다. 개인키는 인증서에 포함되지 않습니다.',
 ['https://docs.openssl.org/3.5/man1/openssl-x509/'])

lesson('x509-2', 2, '나만의 CA로 인증서 발급하기', 25,
 'pki 폴더에서 별도의 학습용 CA와 서버 인증서를 발급합니다. 기존 TLS 서버의 인증서는 그대로 두므로 다른 레슨을 방해하지 않습니다.',
 ['CSR은 공개키·요청 정보·요청자의 서명을 포함합니다. CSR 생성 자체가 CA의 신뢰를 부여하지는 않습니다.',
  'CA는 요청을 검토하고 인증서를 서명합니다. 이 실습은 x509 -req를 사용하는 작은 예제로 발급 DB·폐기 관리까지 구현하지 않습니다.',
  '학습용 개인키는 암호 없이 생성하며 이 컨테이너에서만 사용합니다. 실제 운영 CA 관리 절차와는 구분하세요.'],
 [('CA 생성', '같은 명령을 다시 실행하면 이 레슨의 CA와 키를 교체합니다. 뒤의 CSR·발급 단계까지 함께 진행하세요.', 'cd ~/lab/pki\nopenssl req -x509 -newkey rsa:2048 -nodes -keyout root.key -out root.pem -days 365 -subj "/CN=My Study CA" -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign"', 'root.key와 root.pem 생성'),
  ('키와 CSR 생성', '서버 키와 CA 키가 별개임을 확인합니다.', 'cd ~/lab/pki\nopenssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out site.key\nopenssl req -new -key site.key -out site.csr -subj "/CN=study.local"\nopenssl req -in site.csr -noout -verify', 'Certificate request self-signature verify OK'),
  ('발급과 검증', 'SAN과 용도를 명시하여 서명합니다.', 'cd ~/lab/pki\nprintf "subjectAltName=DNS:study.local\\nbasicConstraints=critical,CA:FALSE\\nkeyUsage=critical,digitalSignature\\nextendedKeyUsage=serverAuth\\n" > site.ext\nopenssl x509 -req -in site.csr -CA root.pem -CAkey root.key -CAcreateserial -out site.pem -days 30 -extfile site.ext\nopenssl verify -CAfile root.pem -purpose sslserver -verify_hostname study.local site.pem', 'site.pem: OK')],
 '서버 인증서를 서명하는 데 사용하는 키는?', ['서버 공개키', 'CA 개인키', '클라이언트 세션 키'], 1,
 'CA 개인키로 서명하고 검증자는 CA 공개키로 서명을 검증합니다.',
 ['https://docs.openssl.org/3.5/man1/openssl-req/', 'https://docs.openssl.org/3.5/man1/openssl-x509/'])

lesson('x509-3', 2, 'PEM·DER와 검증 실패', 15,
 '표현 형식 변환과 인증서의 의미를 구분합니다. 이 레슨은 앞 레슨에서 발급한 pki/site.pem을 사용합니다.',
 ['DER은 ASN.1 구조의 바이너리 인코딩이고 PEM은 이를 Base64와 경계 줄로 표현합니다. 확장자만으로 내용을 단정할 수 없습니다.',
  'PEM에서 DER로 바꾸어도 인증서의 서명 대상 데이터나 공개키가 바뀌지 않습니다.',
  '인증서 검증 실패 원인을 신뢰 경로·시간·이름·용도로 나누어 진단하세요.'],
 [('형식 왕복', '바이너리 파일은 웹 텍스트 편집기 대신 openssl로 읽습니다.', 'cd ~/lab/pki\nopenssl x509 -in site.pem -outform DER -out site.der\nopenssl x509 -inform DER -in site.der -out roundtrip.pem\nopenssl x509 -in roundtrip.pem -noout -fingerprint -sha256\nopenssl x509 -in site.pem -noout -fingerprint -sha256', '두 fingerprint가 같습니다.'),
  ('이름·시간 실패', '두 검증 모두 실패해야 합니다. 각각의 오류 이유를 읽어보세요.', 'cd ~/lab/pki\nopenssl verify -CAfile root.pem -verify_hostname other.local site.pem\nopenssl verify -CAfile root.pem -attime 4102444800 site.pem', 'hostname mismatch, certificate has expired (2100년 기준 검증)')],
 'PEM을 DER로 변환하면 인증서를 재발급해야 할까요?', ['예', '아니요, 같은 인증서의 표현만 달라집니다'], 1,
 '인코딩 표현 변환은 발급이나 서명 교체가 아닙니다.',
 ['https://docs.openssl.org/3.5/man1/openssl-x509/', 'https://docs.openssl.org/3.5/man1/openssl-verify/'])

lesson('arch-1', 3, 'libssl → libcrypto → Provider', 15,
 'OpenSSL 3의 구성요소를 실제 설치 정보와 연결합니다. 웹 터미널도 같은 라이브러리와 명령어를 사용합니다.',
 ['libssl은 TLS 프로토콜을 처리하고 libcrypto는 암호·키·인증서 기능을 제공합니다. EVP는 고수준 암호 API 계층입니다.',
  'Provider는 알고리즘 구현을 제공합니다. default, legacy, FIPS 등의 역할이 다릅니다. 이 환경은 FIPS 검증 환경이 아닙니다.',
  '명령어별 프로세스는 별도의 로딩 상태를 갖습니다. 한 번 list -provider legacy를 실행했다고 다음 명령에도 로딩 상태가 유지되지는 않습니다.'],
 [('구성 탐색', 'provider 모듈 경로와 동적 라이브러리 의존성을 확인합니다.', 'openssl version -a\nopenssl list -providers -verbose\nldd /usr/bin/openssl', 'default Provider와 libssl.so.3 / libcrypto.so.3'),
  ('알고리즘 조회', '출력 끝의 @ default는 구현 제공자를 나타냅니다.', 'openssl list -digest-algorithms -provider default -propquery "provider=default"', 'SHA2-256 등을 제공하는 default 구현')],
 'TLS 프로토콜을 담당하는 라이브러리는?', ['libssl', 'Provider 파일만', 'gcc'], 0,
 'libssl이 TLS를 처리하며 libcrypto의 암호 기능을 사용합니다.',
 ['https://docs.openssl.org/3.5/man7/crypto/', 'https://docs.openssl.org/3.5/man7/provider/'])

lesson('arch-2', 3, 'Fetch와 Property를 코드로 보기', 20,
 '같은 알고리즘 이름이라도 property 조건을 충족하는 구현이 있어야 fetch가 성공합니다. 코드 편집기에서 provider.c를 열어보세요.',
 ['EVP_MD_fetch(libctx, "SHA256", "provider=default")는 해당 컨텍스트에서 조건에 맞는 구현을 가져옵니다.',
  'OSSL_LIB_CTX는 Provider와 설정을 분리하는 라이브러리 컨텍스트입니다. NULL은 기본 컨텍스트를 의미합니다.',
  '명시적으로 fetch한 객체는 free해야 합니다. 알고리즘 이름이 맞더라도 조건에 맞는 Provider가 없으면 실패합니다.'],
 [('빌드와 정상 fetch', '편집기에서도 저장 후 컴파일·실행할 수 있습니다.', 'cd ~/lab\ngcc -Wall -Wextra -Werror examples/provider.c -o examples/provider -lcrypto\n./examples/provider "provider=default"', 'provider=default'),
  ('조건 불일치', '없는 Provider 조건으로 바꿔 실패를 확인합니다.', 'cd ~/lab\n./examples/provider "provider=missing"\necho "exit=$?"', 'unsupported 오류와 exit=1')],
 'EVP_MD_fetch가 반환한 객체는 누가 해제하나요?', ['호출자가 EVP_MD_free로 해제', '절대로 해제하지 않음', '파일 시스템'], 0,
 'fetch 결과의 소유권은 호출자에게 있습니다. get0 등 빌린 포인터를 반환하는 API와 구분하세요.',
 ['https://docs.openssl.org/3.5/man3/EVP_MD_fetch/', 'https://docs.openssl.org/3.5/man3/OSSL_LIB_CTX/'], 'examples/provider.c')

lesson('arch-3', 3, 'Legacy와 마이그레이션', 15,
 '오래된 알고리즘이 기본 환경에서 실패하는 이유를 알아봅니다. MD4는 호환성 동작을 확인하는 실습에만 사용합니다.',
 ['legacy Provider는 오래되었거나 안전하지 않은 알고리즘의 호환성 구현을 제공합니다. 새 설계의 권장 알고리즘 목록이 아닙니다.',
  'Provider를 명시적으로 로딩할 때 default도 필요한 경우 함께 명시합니다. 자동 로딩에 의존하면 예상과 다른 결과가 나올 수 있습니다.',
  '1.1.1 기반 코드를 이식할 때 저수준 RSA/AES API와 ENGINE 의존성, 설정 파일, fetch 실패를 점검합니다. 새 코드는 EVP 중심으로 작성합니다.'],
 [('기본 환경에서 실패', '의도한 실패입니다.', 'printf abc | openssl dgst -md4\necho "exit=$?"', 'unsupported 오류'),
  ('명시적으로 로딩', '이 명령에서만 default와 legacy를 함께 사용합니다.', 'printf abc | openssl dgst -provider default -provider legacy -md4\nopenssl list -providers -provider default -provider legacy', 'MD4(abc) = a448017aaf21d8525fc10ae87aa6729d 및 두 Provider')],
 'legacy Provider를 쓸 수 있으면 MD4를 새 서비스에 사용해도 될까요?', ['예', '아니요, 사용 가능성과 암호학적 안전성은 다릅니다'], 1,
 '호환성 기능이 있다는 사실은 새 용도에 안전하다는 뜻이 아닙니다.',
 ['https://docs.openssl.org/3.5/man7/OSSL_PROVIDER-legacy/', 'https://docs.openssl.org/3.5/man7/ossl-guide-migration/'])

lesson('code-1', 4, 'EVP로 SHA-256 구현하기', 25,
 '예제를 읽거나 새 파일에 직접 입력한 후 컴파일합니다. 명령어와 프로그램이 같은 바이트에 대해 같은 해시를 만드는지 비교합니다.',
 ['EVP_MD_fetch → EVP_MD_CTX_new → Init → Update → Final → free 흐름을 익힙니다. Update는 여러 번 호출해도 됩니다.',
  'C 문자열의 끝 NUL은 strlen 길이에 포함되지 않습니다. echo는 기본적으로 개행을 추가하므로 printf와 해시가 다를 수 있습니다.',
  '모든 실패 경로에서도 컨텍스트와 알고리즘 객체를 해제하고, 오류 큐는 ERR_print_errors_fp로 확인합니다.'],
 [('빌드하고 실행', 'digest.c의 메시지를 바꾸거나 두 번의 Update 호출로 나누어 보세요.', 'cd ~/lab\ngcc -Wall -Wextra -Werror examples/digest.c -o examples/digest -lcrypto\n./examples/digest "hello openssl"', '64자리 16진수 SHA-256'),
  ('CLI와 비교', 'abc의 표준 해시를 두 방식으로 계산합니다.', 'cd ~/lab\n./examples/digest abc\nprintf abc | openssl dgst -sha256\nprintf "abc\\n" | openssl dgst -sha256', '처음 두 해시는 같고 개행이 추가된 세 번째는 다릅니다.')],
 'printf abc와 echo abc의 해시가 다른 가장 흔한 이유는?', ['해시가 무작위라서', 'echo가 추가하는 개행 바이트', '공개키가 달라서'], 1,
 '해시는 입력 바이트에 민감합니다. 개행 하나도 다른 입력입니다.',
 ['https://docs.openssl.org/3.5/man3/EVP_DigestInit/'], 'examples/digest.c')

lesson('code-2', 4, '서명하고 변조를 검출하기', 25,
 'Ed25519로 메시지에 서명하고 공개키만 가진 객체로 검증합니다. tamper 인자를 주면 검증 대상 메시지만 바뀝니다.',
 ['개인키로 서명하고 공개키로 검증합니다. 서명은 메시지를 숨기는 암호화가 아닙니다.',
  'Ed25519의 이 예제는 별도 digest를 지정하지 않는 one-shot EVP_DigestSign/Verify를 사용합니다.',
  '검증 API 반환값 1은 성공, 0은 유효하지 않은 서명, 음수는 기타 오류를 의미합니다. 예제는 검증 거부 때 종료 코드 2를 반환합니다.'],
 [('정상 서명', '편집기에서 공개키만 분리하는 부분을 찾아보세요.', 'cd ~/lab\ngcc -Wall -Wextra -Werror examples/sign.c -o examples/sign -lcrypto\n./examples/sign', 'signature VERIFIED (public key only)'),
  ('변조 테스트', '서명은 그대로 두고 메시지만 바꿉니다.', 'cd ~/lab\n./examples/sign tamper\necho "exit=$?"', 'signature REJECTED: message changed, exit=2')],
 '서명 검증에 반드시 필요한 비밀키는?', ['CA 개인키', '서명자의 개인키', '비밀키는 필요 없고 신뢰할 공개키가 필요하다'], 2,
 '검증 자체는 공개키로 수행합니다. 그 공개키가 누구의 것인지 믿는 문제는 별도로 해결해야 합니다.',
 ['https://docs.openssl.org/3.5/man3/EVP_DigestSignInit/', 'https://docs.openssl.org/3.5/man7/EVP_SIGNATURE-ED25519/'], 'examples/sign.c')

lesson('code-3', 4, '인증하는 TLS 클라이언트 완성', 30,
 '마지막 실습은 앞의 세 영역을 하나로 묶습니다. 로컬 TLS 서버에 연결하고, CA·이름 검증을 통과한 뒤 HTTP 요청을 전송합니다.',
 ['SSL_CTX는 공통 설정을, SSL은 개별 연결 상태를 담습니다. 예제는 BIO가 SSL 객체를 소유하므로 BIO_free_all로 함께 해제합니다.',
  'SSL_VERIFY_PEER, CA 로딩, SSL_set1_host를 함께 사용합니다. SSL_set_tlsext_host_name으로 설정하는 SNI와 이름 검증은 구분합니다.',
  '이 코드는 학습용 블로킹 클라이언트입니다. 운영 코드는 시간 제한, 취소, 재시도, HTTP 파싱, 비동기 I/O 등의 요구도 다뤄야 합니다.'],
 [('빌드와 실행', '예제에 있는 검증 설정 세 가지를 먼저 찾아보세요.', 'cd ~/lab\nlab-server start\ngcc -Wall -Wextra -Werror examples/tls_client.c -o examples/tls_client -lssl -lcrypto\ntimeout 10 ./examples/tls_client', 'Verified TLS: TLSv1.3 및 HTTP/1.0 200 ok'),
  ('실패도 테스트', '다른 호스트 이름으로 검증하면 HTTP 요청 이전에 실패해야 합니다.', 'cd ~/lab\ntimeout 10 ./examples/tls_client wrong.example\necho "exit=$?"', 'certificate verify failed와 exit=1')],
 'SSL_set_tlsext_host_name만으로 충분하지 않은 이유는?', ['SNI는 호스트 이름 검증을 대신하지 않아서', 'TLS는 인증서를 쓰지 않아서', 'C는 TLS를 지원하지 않아서'], 0,
 '체인 검증과 이름 검증을 명시적으로 켜야 합니다. 정상 경로뿐 아니라 거부해야 할 연결도 테스트하세요.',
 ['https://docs.openssl.org/3.5/man7/ossl-guide-tls-client-block/'], 'examples/tls_client.c')

from advanced import extend
extend(LESSONS)

# Attach terminology before rendering, including direct lesson links.
import json
from pathlib import Path
_terms = json.loads(Path(__file__).with_name('lesson_terms.json').read_text(encoding='utf8'))
for _lesson in LESSONS:
    _lesson['terms'] = [
        {'name': name, 'meaning': _terms['terms'][name]}
        for name in _terms['lessons'][_lesson['id']]
    ]
_mac = next(item for item in LESSONS if item['id'] == 'basic-mac')
_mac['sections'].insert(0, {
    'title': 'MAC과 HMAC을 실제 메시지로 이해하기',
    'paragraphs': [
        '송신자와 수신자가 비밀키 K를 공유한다고 해봅시다. 송신자는 메시지 hello와 K로 HMAC-SHA256 태그를 계산하고, 메시지와 태그를 보냅니다. 수신자도 받은 메시지와 K로 태그를 계산해서 받은 태그와 비교합니다. 공격자가 메시지만 바꾸면 검증이 실패하며, K를 모르면 바뀐 메시지에 맞는 태그를 만드는 것이 어렵습니다.',
        'MAC은 메시지 인증 코드라는 넓은 범주이고 HMAC은 해시를 사용하는 MAC 방식입니다. HMAC-SHA256이라는 이름은 내부에서 SHA-256을 쓴다는 뜻입니다. 원문을 숨기는 기능은 별도로 필요합니다. 또한 같은 키를 가진 수신자도 태그를 만들 수 있으므로 특정 한 사람이 작성했다는 공개적인 증명으로 사용할 수는 없습니다.',
        'random_mac.cpp에서는 먼저 tag를 계산하고 received = tag로 받은 태그를 모사합니다. tamper hello는 received의 한 비트만 뒤집습니다. 따라서 이 실습은 정상·변조 태그의 비교를 보여주며, 실제 수신 메시지로 HMAC을 다시 계산하는 수신자 전체 코드는 아닙니다. MAC VERIFIED와 MAC REJECTED의 차이를 이 범위 안에서 해석하세요.'
    ]
})
_mac['docs'].append('https://www.rfc-editor.org/rfc/rfc2104.html')

_purposes = json.loads(Path(__file__).with_name('api_purposes.json').read_text(encoding='utf8'))
for _lesson in LESSONS:
    for _api in _lesson.get('apis', []):
        _api.update(_purposes[_api['name']])

from concept_connections import enrich as connect_concepts
connect_concepts(LESSONS)

from quic_lessons import LESSONS as QUIC_LESSONS
LESSONS.extend(QUIC_LESSONS)

# Authoritative narrative: replace legacy section text rather than append summaries.
_text = json.loads(Path(__file__).with_name('lesson_text.json').read_text(encoding='utf8'))
if set(_text) != {lesson['id'] for lesson in LESSONS}:
    raise ValueError('lesson_text.json must cover every lesson exactly')
for _lesson in LESSONS:
    _lesson.update(_text[_lesson['id']])
    _lesson.pop('concepts', None)

from reading_routes import enrich as connect_reading
connect_reading(LESSONS)
