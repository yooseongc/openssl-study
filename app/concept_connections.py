"""Connect primitives, wire values and trust decisions in the existing lesson order."""

def enrich(lessons):
    by = {lesson['id']: lesson for lesson in lessons}

    def section(title, *paragraphs):
        return {'title': title, 'paragraphs': list(paragraphs)}

    def before(id, *sections):
        by[id]['sections'][0:0] = sections

    def after(id, *sections):
        by[id]['sections'].extend(sections)

    def terms(id, **items):
        existing = {term['name'] for term in by[id]['terms']}
        by[id]['terms'].extend({'name': name, 'meaning': meaning}
                              for name, meaning in items.items() if name not in existing)

    def docs(id, *urls):
        by[id]['docs'].extend(url for url in urls if url not in by[id]['docs'])

    before('basic-bytes', section('암호 도구를 읽는 네 가지 질문',
        '새 이름을 만날 때 ① 해결할 문제 ② 입력과 출력 ③ 공개해도 되는 값 ④ 다음 단계에서 쓰는 곳을 먼저 적어보세요. 이름에 Key가 들어간다고 모두 메시지를 암호화하는 함수는 아닙니다.',
        '연결의 큰 흐름은 키 합의 → 공유 비밀 → 키 유도 → 통신용 키 → 데이터 보호입니다. 상대가 누구인지 확인하는 인증 경로도 필요합니다. 같은 비밀을 계산했다는 사실만으로 올바른 서버에 연결했다고 결론낼 수는 없습니다.',
        '예를 들어 X25519는 양쪽이 같은 비밀을 얻는 연산, HKDF는 그 비밀에서 용도별 키 재료를 만드는 연산, AES-GCM은 키로 메시지를 보호하는 연산입니다. 인증서와 서명은 공개키를 신원 및 현재 대화에 연결합니다. 뒤 레슨에서 이 화살표를 하나씩 채웁니다.'))

    after('basic-random', section('개인키·nonce·salt는 서로 대체하는 값이 아니다',
        '임시 개인키는 해당 연결에서만 쓰더라도 비밀입니다. 키 생성 API가 암호학적 난수 생성기(CSPRNG)를 이용해 만들도록 합니다. 공개 nonce나 현재 시각에서 개인키를 계산하는 구조와 구분하세요.',
        'GCM nonce는 같은 키로 수행하는 암호화들을 구별하는 입력입니다. 공개해도 되지만 같은 키와 nonce의 조합을 반복하면 안 됩니다. 올바르게 관리되는 카운터도 사용할 수 있으므로 nonce가 반드시 난수인 것은 아닙니다.',
        '비밀번호 해싱의 salt는 계정별 사전 계산 재활용을 어렵게 하며 보통 해시와 함께 저장합니다. HKDF의 salt는 비밀 추출 단계의 입력입니다. 같은 salt라는 이름이라도 요구되는 생성·보관 규칙은 사용하는 알고리즘과 프로토콜에서 확인해야 합니다.'))
    terms('basic-random', CSPRNG='Cryptographically Secure Pseudorandom Number Generator. 암호학적 용도의 예측 불가능한 난수 바이트를 제공하는 생성기입니다. OpenSSL에서는 RAND API와 키 생성 API를 통해 사용합니다.')

    after('basic-mac', section('HMAC과 HKDF는 입력과 출력의 쓰임이 다르다',
        'SHA256(메시지) → 공개 비교용 digest, HMAC(비밀키, 메시지) → 검증용 태그입니다. 수신자는 같은 비밀키로 태그를 다시 계산합니다. 태그는 전송할 수 있지만 태그를 만든 키를 함께 보내면 인증 목적을 잃습니다.',
        '다음 레슨의 HKDF도 내부에서 HMAC을 사용하지만 결과의 목적은 새 키 재료를 유도하는 것입니다. 그 출력은 비밀로 관리해야 합니다. 같은 HMAC 연산을 포함한다는 이유로 HKDF의 출력 키를 메시지 옆에 공개하는 태그처럼 취급하면 안 됩니다.',
        'Tag는 인증값이라는 역할의 이름이고 HMAC은 계산 방식의 이름입니다. AES-GCM의 태그도 변조 검증에 쓰이지만 HMAC-SHA256으로 계산한 값은 아닙니다.'))

    before('basic-kdf', section('Extract와 Expand의 입력을 분리해서 읽기',
        'IKM은 input keying material, 즉 입력 키 재료입니다. 키 합의에서 얻은 공유 비밀이 그 예입니다. HKDF-Extract(salt, IKM) → PRK에서 PRK는 중간 비밀값이고, HKDF-Expand(PRK, info, L) → L바이트의 출력 키 재료가 됩니다.',
        'salt는 Extract에, info는 Expand에 들어갑니다. 일반적인 HKDF의 salt는 공개 가능한 값이며 생략 시 해시 출력 길이만큼의 0바이트를 사용합니다. 공개 가능하다는 말은 공격자가 임의로 바꾸어도 된다는 뜻이 아닙니다. 프로토콜이 정한 값과 문맥을 양쪽에서 일치시켜야 합니다.',
        'info는 client key나 server key처럼 용도를 구분하는 바이트열입니다. 함수가 영어 문장의 의미를 해석하지는 않습니다. 같은 비밀·salt에서도 다른 info를 넣으면 서로 다른 키를 유도할 수 있습니다. 같은 입력을 넣으면 같은 결과를 얻으며, 출력 길이 L을 늘린다고 새로운 불확실성이 생기지는 않습니다.'),
        section('비밀번호를 넣으면 강한 키가 되는가?',
        '이 예제의 shared-secret-for-demo는 재현을 위한 상수입니다. 실제 키 합의 비밀이나 운영 키가 아닙니다. 출력이 32바이트여도 입력이 추측 가능한 문자열이면 공격자는 그 문자열 후보들을 넣어 같은 출력을 계산할 수 있습니다.',
        'HKDF는 빠른 키 유도 도구입니다. 비밀번호 저장에는 후보 하나를 시험하는 비용을 높이는 별도 설계가 필요합니다. 비밀번호용 salt가 공개되어도 되는 이유와 HKDF가 약한 입력을 강하게 만들지 않는 이유를 연결해서 생각하세요.'))
    terms('basic-kdf', IKM='Input Keying Material. Extract에 넣는 원래 비밀 재료로, ECDHE 공유 비밀 등이 해당합니다.',
          PRK='Pseudorandom Key. HKDF-Extract의 출력이자 HKDF-Expand의 비밀 입력입니다.',
          Extract='salt와 입력 키 재료에서 고정 길이 중간 비밀 PRK를 추출하는 단계입니다.',
          Expand='PRK와 용도 정보 info에서 요청한 길이의 키 재료를 유도하는 단계입니다.')
    docs('basic-kdf', 'https://www.rfc-editor.org/rfc/rfc5869.html#section-2')

    target = by['basic-aead']['sections'][0]
    target.update(section('평문·키·nonce·AAD·암호문·태그의 위치',
        '보내는 쪽의 입력은 비밀키 K, nonce N, 평문 M, 추가 인증 데이터 AAD입니다. 출력은 암호문 C와 태그 T입니다. 받는 쪽은 같은 K·N·AAD와 받은 C·T를 넣어 평문을 얻거나 인증 실패로 거부합니다.',
        'AAD는 숨기지 않아도 되지만 바뀌면 안 되는 데이터입니다. 예를 들어 헤더를 암호화하지 않고 인증하려면 양쪽의 AAD 입력이 일치해야 합니다. OpenSSL은 AAD를 자동으로 전송하지 않습니다. 애플리케이션이나 프로토콜이 전달하거나 양쪽에서 동일하게 구성해야 합니다.',
        '암호문과 태그는 전송할 수 있습니다. nonce도 공개 가능하지만 프로토콜에 따라 전송하거나 양쪽에서 계산합니다. 비밀키는 데이터에 붙여 보내지 않습니다. 이 예제는 기본 IV 길이 12바이트와 AES-256 키 32바이트를 사용합니다. 다른 모드에 이 길이를 일반화하지 마세요.'))
    after('basic-aead', section('GCM 태그가 있는데 HMAC도 따로 필요한가?',
        'AES-GCM은 본문 암호화와 인증을 함께 제공합니다. 동일한 데이터 보호 목적을 위해 별도의 HMAC을 추가해야 하는 구조는 아닙니다. GCM의 태그는 암호문과 AAD 등을 인증하지만 내부 계산법은 HMAC과 다릅니다.',
        'DecryptUpdate가 1을 반환했다는 것은 그 단계의 처리가 성공했다는 뜻입니다. 후보 평문을 받았더라도 GCM 태그 검증이 끝난 것은 아닙니다. DecryptFinal_ex가 성공한 뒤에만 평문을 해석·저장·전달합니다. 실패하면 앞서 출력된 후보도 함께 폐기합니다.'))

    before('basic-kex', section('DH·ECDHE·X25519의 이름을 나눠 읽기',
        'DH는 Diffie–Hellman 키 합의입니다. ECDH의 EC는 elliptic curve, 즉 타원곡선을 뜻합니다. DHE와 ECDHE의 마지막 E는 ephemeral, 즉 임시 키를 쓴다는 뜻입니다. 임시 키 사용은 키의 수명에 관한 선택이며 별도의 암호화 연산 이름은 아닙니다.',
        'X25519는 구체적인 키 합의 연산입니다. 이름 자체가 연결마다 새 키를 생성한다는 뜻은 아닙니다. P-256(secp256r1, OpenSSL의 prime256v1)은 곡선 그룹의 이름입니다. P-256 위에서 ECDH 키 합의나 ECDSA 서명을 할 수 있지만 두 연산의 목적은 다릅니다.'),
        section('G, a, A 중 무엇을 보내는가?',
        '개념적으로 공개 생성점 G와 비밀 정수 a에서 공개값 A = aG를 만듭니다. aG는 타원곡선 점에 대한 스칼라 곱 표기이며 일반 정수 곱셈이 아닙니다. 상대도 자신의 비밀 b로 B = bG를 만듭니다. a와 b는 보관하고 A와 B를 교환합니다.',
        '클라이언트는 aB, 서버는 bA를 계산하여 같은 공유 결과를 얻습니다. 자신의 공개값 A를 만드는 데에는 상대가 필요 없지만, 공유 결과를 구하려면 상대 공개값 B가 필요합니다. G는 그룹 정의에 들어 있는 공개 파라미터이므로 비밀로 교환할 값이 아닙니다.',
        'X25519에서 실제 OpenSSL API가 주고받는 것은 정해진 인코딩의 바이트입니다. X25519는 u좌표를 사용하는 연산이며 기준점의 u좌표는 9입니다. 위 aG는 원리 설명이고, API 입력을 정수나 전체 점 구조체로 직접 바꾸어 넣으라는 뜻은 아닙니다.'),
        section('임시 키가 보호하는 것과 보호하지 않는 것',
        '연결마다 새 임시 키를 사용하고 사용 후 폐기하면, 나중에 장기 인증용 개인키가 유출되더라도 녹화해 둔 과거 연결의 공유 비밀을 그 키만으로 계산하기 어렵습니다. 이를 forward secrecy, 순방향 비밀성이라고 합니다.',
        '실제 임시 개인키나 세션 비밀이 유출된 경우까지 보호하는 뜻은 아닙니다. 또 임시 키 합의 자체에는 상대 신원 인증이 없습니다. 공격자도 자신의 키로 양쪽과 별개로 합의할 수 있으므로, TLS에서는 인증을 현재 핸드셰이크에 연결해야 합니다.'))
    terms('basic-kex', ECDHE='Elliptic Curve Diffie–Hellman Ephemeral. 타원곡선 키 합의에 임시 키를 사용하는 방식입니다.',
          생성점='그룹 정의에 포함된 공개 기준점입니다. 개인키와 이 점으로 자신의 공개값을 계산합니다.',
          스칼라_곱='정수와 타원곡선 점으로 새로운 점을 계산하는 연산입니다. aG의 G는 점, a는 정수입니다.',
          P_256='secp256r1이라고도 부르는 곡선 그룹입니다. OpenSSL의 prime256v1은 같은 곡선의 별칭입니다.')
    docs('basic-kex', 'https://www.rfc-editor.org/rfc/rfc7748.html#section-6.1')
    by['basic-kex']['steps'].insert(0, {
        'title':'작은 수로 공개값과 공유 비밀 구별하기',
        'text':'유한체 DH의 원리를 보는 장난감 계산입니다. 이 작은 수와 고정 개인값은 안전하지 않으며 실제 키 생성에 사용하지 않습니다. X25519의 내부 구현을 재현하는 코드도 아닙니다.',
        'command':"python - <<'PY'\np, g = 23, 5\na, b = 6, 15\nA, B = pow(g, a, p), pow(g, b, p)\nprint('public parameters:', p, g)\nprint('public contributions:', A, B)\nprint('Alice secret:', pow(B, a, p))\nprint('Bob secret:', pow(A, b, p))\nPY",
        'expect':'공개 기여값 A=8, B=19이며 양쪽 공유 비밀은 2입니다. 보내는 A/B와 보관하는 a/b를 구분하세요.'})

    after('tls-1', section('한 연결 안에 있는 서로 다른 키 세 가지',
        '① 인증서에 들어 있는 서버 공개키는 서버의 서명을 검증하는 데 씁니다. ② key_share의 공개값은 이번 연결의 키 합의에 씁니다. ③ 키 스케줄이 만든 대칭키는 TLS 레코드 보호에 씁니다. 셋을 모두 서버 키라는 한 이름으로 부르면 어느 값이 언제 필요한지 놓치기 쉽습니다.',
        '인증서 기반 TLS 1.3 전체 핸드셰이크의 흐름은 ClientHello/ServerHello의 공개 기여값 → 공유 비밀 → 핸드셰이크 보호 키 → 인증서·CertificateVerify·Finished 검증 → 애플리케이션 데이터 보호입니다. 클라이언트 Finished도 포함하며 실제 프로토콜의 계산·전송 시점은 이 개념도보다 세밀합니다.',
        'TLS_AES_128_GCM_SHA256의 AES_128_GCM은 레코드 보호 방식, SHA256은 HKDF와 transcript에 사용하는 해시를 뜻합니다. 이 이름만으로 X25519인지 P-256인지, 서버 서명이 RSA인지 ECDSA인지 알 수 없습니다. 그룹과 서명 방식은 따로 협상됩니다.'))
    by['tls-1']['steps'].append({
        'title':'암호 스위트와 키 합의 그룹을 따로 지정하기',
        'text':'기존 로컬 서버에 연결합니다. 인증 검증을 켠 채 레코드 암호와 그룹을 각각 지정하고 출력의 서로 다른 항목을 찾으세요.',
        'command':'timeout 8 openssl s_client -connect 127.0.0.1:4433 -servername localhost -CAfile ~/lab/tls/ca.pem -verify_hostname localhost -verify_return_error -tls1_3 -groups X25519 -ciphersuites TLS_AES_128_GCM_SHA256 -brief </dev/null',
        'expect':'TLSv1.3, TLS_AES_128_GCM_SHA256, X25519와 인증서 검증 성공을 확인합니다. 출력 라벨은 버전에 따라 달라질 수 있습니다.'})

    before('tls-2', section('supported_groups와 key_share는 같은 목록이 아니다',
        'supported_groups는 사용할 수 있는 그룹 목록이고, key_share는 이미 계산해 보낸 공개 기여값 목록입니다. 예를 들어 지원 목록은 [X25519, P-256]인데 실제 share는 X25519 하나만 보낼 수 있습니다. 모든 후보의 키를 미리 계산하고 전송하는 비용을 줄이는 선택입니다.',
        'ECDHE의 KeyShareEntry는 그룹 식별자와 공개 기여값 바이트를 포함합니다. 여기 들어가는 것은 G가 아니라 A = aG에 해당하는 값입니다. 서버는 선택한 그룹에서 자신의 공개 기여값 B를 보내고 양쪽은 보관한 개인값과 상대 기여값으로 공유 비밀을 계산합니다.',
        '서버가 클라이언트 지원 목록에 있지만 처음 share에는 없는 그룹을 요구하면 HelloRetryRequest(HRR)로 그 그룹의 share를 요청할 수 있습니다. HRR은 쿠키 요청에도 쓰이므로 HRR이 보였다는 사실만으로 인증 실패라고 판단하지 마세요. 이 설명은 ECDHE를 기준으로 하며 KEM 그룹의 기여값 형식은 다릅니다.'))
    after('tls-2', section('TLS의 HKDF salt는 어디에서 오는가?',
        '일반 HKDF의 salt가 공개 가능하다고 해서 TLS의 모든 salt가 공개되거나 매번 난수로 전송되는 것은 아닙니다. PSK가 없는 전체 핸드셰이크는 규격이 정한 0 입력으로 Early Secret 계산을 시작합니다. 이 초기 값 자체는 비밀이 아닙니다.',
        '이후 derived 레이블로 유도한 값이 다음 Extract의 salt가 되고, ECDHE 공유 비밀이 그 Extract의 입력 재료가 됩니다. 더 뒤 단계의 salt는 비밀값에서 유도될 수 있으므로 공개한다고 가정하면 안 됩니다. 양쪽이 같은 규칙으로 계산하므로 각 salt를 별도 메시지로 전송할 필요가 없습니다.',
        'HKDF-Expand-Label은 레이블과 문맥을 정해진 형식으로 인코딩합니다. 문맥에는 단계에 따라 transcript 해시가 사용됩니다. kdf.cpp의 단순 info 문자열은 이 원리를 관찰하는 도구이며 TLS 키 스케줄 전체를 대신하지 않습니다.'),
        section('재개는 이전 데이터 암호화 키를 다시 쓰는가?',
        'PSK는 pre-shared key, 즉 양쪽이 이미 가진 비밀입니다. TLS 1.3 세션 재개에서는 이전 연결에서 유도된 재개용 비밀과 티켓 관련 정보를 활용해 새 연결의 키를 계산합니다. 이전 AES 키를 그대로 복사하는 방식으로 이해하면 안 됩니다.',
        'psk_ke는 새 DH 키 합의 없이 PSK를 사용하고, psk_dhe_ke는 PSK에 새 (EC)DHE 공유 비밀을 함께 넣습니다. 새 DH 기여 여부에 따라 순방향 비밀성의 성질이 달라집니다. 0-RTT 데이터는 또 다른 보호 조건을 가지므로 일반 애플리케이션 데이터와 같은 보장을 가정하지 않습니다.'))
    terms('tls-2', supported_groups='사용할 수 있다고 알리는 키 합의 그룹의 목록입니다.',
          key_share='선택한 그룹에서 실제로 계산한 공개 기여값을 담는 TLS 확장입니다. ECDHE에서는 임시 공개값을 담습니다.',
          HRR='HelloRetryRequest. 서버가 필요한 조건을 갖춘 ClientHello를 다시 보내도록 요청하는 메시지입니다.',
          PSK='Pre-Shared Key. 양쪽이 이미 알고 있는 비밀로, TLS 재개 등의 키 스케줄 입력에 사용합니다.')
    docs('tls-2', 'https://www.rfc-editor.org/rfc/rfc8446.html#section-4.2.8',
         'https://www.rfc-editor.org/rfc/rfc8446.html#section-7.1')

    after('tls-record', section('레코드에는 nonce와 HMAC이 어디에 있는가?',
        'TLS 1.3은 방향별 traffic secret에서 쓰기 키와 static IV를 유도합니다. 각 방향의 레코드 순서 번호를 IV 길이에 맞게 0으로 패딩하고 static IV와 XOR하여 해당 레코드의 nonce를 만듭니다. nonce 자체를 매번 별도 필드로 보내는 구조가 아닙니다.',
        'TLSCiphertext의 바깥 헤더는 AAD로 인증에 포함됩니다. 레코드의 encrypted_record에는 보호된 내용과 AEAD 태그가 들어갑니다. AES-GCM 태그가 있는 레코드 뒤에 별도 HMAC 태그를 덧붙이는 방식은 아닙니다.',
        '그렇다고 TLS 1.3 전체에서 HMAC을 안 쓰는 것은 아닙니다. HKDF와 Finished에서는 HMAC이 쓰입니다. 레코드 보호, 키 유도, 핸드셰이크 검증이라는 서로 다른 위치를 구분하세요. 애플리케이션은 이 nonce·AAD 처리를 SSL_read/SSL_write가 사용하는 libssl에 맡깁니다.'))
    terms('tls-record', static_IV='현재 방향과 키 세대의 traffic secret에서 유도한 IV입니다. 레코드 순서 번호와 조합해 매 레코드의 nonce를 만듭니다.')
    docs('tls-record', 'https://www.rfc-editor.org/rfc/rfc8446.html#section-5.3')

    before('tls-3', section('서명 확인과 서버 신원 확인 사이의 연결',
        '공격자도 자신의 키 쌍과 올바른 서명을 만들 수 있습니다. 서명 수학이 맞는지만 확인해서는 그 공개키가 접속하려는 서버의 것인지 알 수 없습니다. 공개키와 이름의 연결을 신뢰할 근거가 필요합니다.',
        '클라이언트는 신뢰 앵커부터 인증서 체인과 제약·기간·용도·호스트명을 검증하여 서버 인증서의 공개키를 신뢰할 수 있는지 판단합니다. 이어 현재 핸드셰이크의 CertificateVerify 서명을 그 공개키로 검증합니다. Finished는 키 스케줄에서 얻은 키를 이용한 별도의 대화 검증값입니다.',
        '인증서 사본은 공개 정보입니다. 사본만 복사한 상대는 대응 개인키 없이 현재 핸드셰이크에 대한 유효한 CertificateVerify를 만들 수 없습니다. key_share도 transcript에 포함되어 있으므로 정상적인 인증 검증은 키 합의 값과 현재 상대를 연결하는 역할을 합니다.'))

    after('x509-chain', section('CA 개인키가 클라이언트에게 필요한가?',
        '필요하지 않습니다. CA는 인증서 발급 시 개인키로 서명하고, 클라이언트는 신뢰하는 CA의 공개키로 검증합니다. root → intermediate → leaf 체인에서는 root로 intermediate를, intermediate로 leaf를 검증하며 각 인증서의 제약도 확인합니다.',
        '서버 인증서 안의 공개키는 서버의 현재 핸드셰이크 서명을 확인하는 데 사용합니다. CA가 인증서에 남긴 서명과 서버가 CertificateVerify에 넣은 서명은 서명자·대상·생성 시점이 다릅니다.',
        '루트 인증서가 스스로 서명되어 있다는 사실만으로 신뢰가 생기지는 않습니다. 신뢰 앵커 선택은 클라이언트의 설정·배포 정책에서 시작합니다. 서버가 보내 준 인증서를 모두 신뢰 저장소에 넣는 것으로 체인 검증을 대체하지 마세요.'))

    before('code-2', section('Ed25519와 X25519는 같은 일을 하는가?',
        'X25519는 자신의 개인키와 상대 공개값에서 공유 비밀을 얻는 키 합의 연산입니다. Ed25519는 개인키와 메시지에서 서명을 만들고 공개키로 검증하는 서명 방식입니다. 수학적으로 관련된 곡선 계열을 사용해도 목적과 키 인코딩은 다르며 같은 키 바이트를 그대로 재사용하는 규칙은 아닙니다.',
        'Ed25519의 검증 입력은 메시지, 서명, 서명자의 공개키입니다. 검증자는 개인키나 서명자가 내부에서 사용하는 비밀값을 알 필요가 없습니다. 서명은 원문 암호문이 아니며 개인키로 암호화하고 공개키로 복호화한다는 설명은 이 API에 맞지 않습니다.',
        'Ed25519 서명은 64바이트이며 개념적으로 점을 표현한 R과 스칼라 s의 인코딩으로 구성됩니다. 필요한 공개 중간값은 서명과 메시지·공개키에서 얻습니다. 내부 점·범위 검증은 EVP_DigestVerify에 맡기고, 여기서는 입력을 하나씩 바꾸었을 때 검증 결과가 어떻게 달라지는지 관찰합니다.'))
    docs('code-2', 'https://www.rfc-editor.org/rfc/rfc8032.html#section-5.1')

    after('arch-1', section('보충: ML-KEM은 어느 자리에 들어가는가?',
        'ML-KEM은 공유 비밀을 설정하는 KEM(Key Encapsulation Mechanism)입니다. 수신자가 키 쌍을 만들고, 송신자가 공개키로 encapsulation을 수행하면 공유 비밀과 캡슐화 암호문을 얻습니다. 수신자는 개인키로 그 암호문을 decapsulation하여 같은 비밀을 복원합니다. ECDH의 aB = bA 식을 그대로 적용하는 연산은 아닙니다.',
        'OpenSSL 3.5는 ML-KEM을 지원합니다. 하이브리드 키 설정은 X25519 같은 기존 방식과 KEM의 기여를 프로토콜 규칙대로 결합합니다. 이 결과가 키 유도와 AEAD 보호로 이어지는 것이지, 메시지 암호화용 AES-GCM을 ML-KEM으로 바꾸는 것은 아닙니다.',
        '키 설정의 양자내성과 인증 서명의 양자내성도 별개입니다. 예를 들어 ML-DSA는 서명 쪽 기술입니다. 이 레슨에서는 이름을 libcrypto의 연산 역할에 배치하는 데 집중하고, 실제 그룹 협상과 KEM API 실습은 별도 심화 범위로 남깁니다.'))
    terms('arch-1', KEM='Key Encapsulation Mechanism. 공개키를 이용해 공유 비밀과 캡슐화 암호문을 만들고 개인키로 같은 비밀을 복원하는 방식입니다.',
          ML_KEM='격자 기반의 키 캡슐화 알고리즘입니다. 메시지 보호용 AEAD나 전자서명과 구별합니다.')
    docs('arch-1', 'https://docs.openssl.org/3.5/man7/EVP_KEM-ML-KEM/')

    after('code-3', section('보충: 같은 역할을 SSH 이름에서도 찾아보기',
        'SSH의 curve25519-sha256은 키 교환, ssh-ed25519는 서명 키 형식, aes256-gcm@openssh.com은 데이터 보호 방식입니다. 이들을 서로 대체하는 알고리즘 목록으로 읽지 말고 각기 다른 협상 항목에 배치해 보세요.',
        'SSH의 서버 Host Key 확인과 사용자의 공개키 로그인은 다른 인증 단계입니다. 서버 키의 신뢰는 known_hosts에 기록한 키나 SSH 인증서 등의 정책으로 판단할 수 있습니다. 일반적인 TLS의 X.509 인증서 체인 검증과 같다고 가정하지 않습니다.',
        '역할이 비슷해도 SSH의 키 유도·패킷 형식은 TLS 1.3과 다릅니다. TLS의 HKDF 레이블이나 nonce 구성을 SSH에 그대로 옮기지 마세요. 이 과정에서는 SSH 접속 환경을 추가하지 않고 익힌 개념이 다른 프로토콜에서도 구분되는지만 확인합니다.'))
    docs('code-3', 'https://www.rfc-editor.org/rfc/rfc4253.html#section-7.2',
         'https://www.rfc-editor.org/rfc/rfc8731.html')

    after('arch-ownership', section('main 뒤의 try는 어떤 C++ 문법인가?',
        'int main(...) try { ... } catch (...) { ... }는 function try block입니다. 이 예제에서는 본문에서 발생한 예외를 마지막 catch에서 받아 오류 메시지와 종료 코드로 바꾸는 흐름을 만듭니다. 생성자에서는 멤버·기반 클래스 초기화의 예외까지 다룬다는 별도 규칙도 있습니다.',
        'OpenSSL C API가 자동으로 C++ 예외를 던지는 것은 아닙니다. 예제의 study::require가 API별 성공 조건을 검사한 뒤 예외를 던집니다. 예외로 스택을 빠져나갈 때 이미 만들어진 Handle의 소멸자가 소유한 참조를 해제합니다. WANT_READ처럼 재시도해야 하는 상태까지 require(false)로 처리하면 안 됩니다.'))

    # Repair terminology in the original text to match the renamed readable example.
    for lesson in lessons:
        for term in lesson['terms']:
            term['name'] = term['name'].replace('스칼라_곱', '스칼라 곱').replace('P_256', 'P-256').replace('static_IV', 'static IV').replace('ML_KEM', 'ML-KEM')
    for item in by['basic-hash']['sections']:
        if item['title'] == '예제 코드 읽기':
            item['paragraphs'][0] = 'algorithm은 fetch한 SHA-256 구현, digest_context는 이번 계산의 상태이며 각각 RAII 핸들이 관리합니다. first_chunk_size는 입력을 두 조각으로 나누는 위치입니다. 빈 문자열에서도 길이 0인 Update로 빈 입력을 처리할 수 있습니다.'
    by['basic-kdf']['steps'][0]['text'] += ' 두 실행에서 IKM과 salt는 고정이고 info만 바뀝니다. 출력 차이의 원인을 새 난수 생성으로 설명하지 마세요.'
    by['basic-aead']['steps'][1]['text'] += ' 무엇을 바꾸든 Final에서 거부되는지, 그 전에 나온 후보 평문은 출력되지 않는지 확인하세요.'
