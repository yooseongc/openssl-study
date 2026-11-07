"""Additional reading and API contracts for the original twelve lessons."""
def enrich(lessons):
    from advanced import api,section,step,build
    by={l['id']:l for l in lessons}
    def set_(id,sections,apis,challenge):
        by[id].update(sections=sections,apis=apis,challenge=challenge)
    set_('tls-1',[
      section('TLS가 조합하는 기능','먼저 TCP 연결을 만들고 TLS 핸드셰이크로 버전·알고리즘과 키 재료를 합의합니다. 서버 인증서는 서버 신원을 공개키와 연결하고, CertificateVerify는 그 공개키에 대응하는 개인키 보유를 증명합니다. 공유 비밀과 transcript에서 traffic secret을 유도한 뒤 AEAD로 애플리케이션 데이터를 보호합니다.',
       '대칭 암호만 있으면 누가 상대인지 모릅니다. 인증서만 있으면 전송 데이터가 암호화되지 않습니다. 키 교환만 하면 중간에서 다른 공개키로 바꾸는 상대를 식별하지 못합니다. TLS는 이 구성요소들이 하나의 검증된 대화에 묶이도록 합니다.'),
      section('TLS 1.2와 1.3의 차이를 읽는 출발점','1.3에서는 암호 스위트가 AEAD와 HKDF 해시를 정하며 인증·그룹 선택은 별도입니다. 1.2의 cipher suite 이름에 포함된 인증·키 교환 의미를 그대로 1.3에 대입하지 마세요. 1.3은 일반적인 인증서 전체 핸드셰이크에서 ServerHello 이후를 암호화합니다.',
       '이 서버는 TLS 1.3으로 고정했습니다. 이 과정에서는 먼저 1.3의 전체 핸드셰이크를 기준으로 이해하고 재개·PSK·0-RTT가 생략하거나 변경하는 단계를 구분합니다. SSL이라는 API 이름을 쓴다고 구형 SSL 프로토콜로 연결하는 것은 아닙니다.')],
      [api('TLS_client_method() / SSL_CTX_new(method)','method는 TLS 클라이언트 역할을 정합니다. 최소 버전은 별도로 설정합니다.','method는 빌린 method 객체, CTX는 SSL_CTX_free 대상.','method / CTX 포인터. CTX의 nullptr 검사.','method 이름만으로 TLS 1.3으로 고정되었다고 생각하지 않습니다.')],
      'ClientHello부터 HTTP 바이트까지 각 단계에서 해시·키 교환·서명·AEAD 중 무엇이 쓰이는지 표로 적어보세요.')
    set_('tls-2',[
      section('Transcript는 대화의 바이트 기록','핸드셰이크 메시지들은 정해진 인코딩으로 해시에 누적됩니다. CertificateVerify와 Finished는 이 대화 맥락에 연결되어 상대가 다른 협상 내용을 보게 되는 공격을 방지하는 데 기여합니다. 화면에 출력된 메시지 이름 문자열을 해시하는 것이 아닙니다.',
       'CertificateVerify는 개인키 서명을, Finished는 키 스케줄에서 유도한 키를 사용하는 검증값을 제공합니다. 서버 인증서의 서명과 CertificateVerify 서명은 서명 주체와 대상이 다릅니다. CA는 인증서를 서명하고 서버는 현재 핸드셰이크 맥락을 서명합니다.'),
      section('재개와 관찰 도구의 한계','TLS 1.3 NewSessionTicket은 이후 연결의 재개에 사용할 정보를 제공합니다. PSK 재개는 인증서를 매번 보내는 전체 핸드셰이크와 메시지 흐름이 다를 수 있습니다. 0-RTT는 재전송 공격에 대한 별도 고려가 필요합니다.',
       '-msg는 OpenSSL 내부에서 해석한 내용을 보여줍니다. 네트워크에서 보이는 암호문 패킷과 같지 않습니다. key log는 디버깅 시 복호화에 유용하지만 세션 비밀을 포함하므로 실제 운영 트래픽의 로그 취급을 별도로 정해야 합니다.')],
      [api('SSL_connect(ssl)','이미 설정한 client SSL의 핸드셰이크를 진행합니다.','연결 상태를 같은 SSL에 유지합니다.','1 완료, 그 외 SSL_get_error로 분류.','TCP 연결 성공과 TLS 핸드셰이크 완료를 혼동하지 않습니다.')],
      'Certificate, CertificateVerify, Finished 각각의 입력·검증 키·목적을 자신의 말로 설명해 보세요.')
    set_('tls-3',[
      section('검증을 구성하는 독립 조건','신뢰할 CA까지 이어지는지, 서명과 CA 제약이 맞는지, 시간이 유효한지, 용도에 부합하는지, 접속 대상 이름이 맞는지를 따로 생각하세요. 체인 검증이 성공해도 잘못된 호스트의 인증서라면 연결하면 안 됩니다.',
       'SNI는 서버에 어떤 가상 호스트를 원하는지 알려줍니다. 실제 연결 주소는 127.0.0.1이어도 이름 검증은 localhost를 대상으로 수행할 수 있습니다. IP 주소 자체를 인증해야 하는 경우에는 DNS 이름 대신 IP SAN 검증 API를 사용해야 합니다.'),
      section('실패 정책은 애플리케이션 책임','진단 명령 s_client의 기본 동작과 애플리케이션의 인증 정책을 혼동하지 않습니다. 검증 오류를 무시하거나 callback에서 무조건 1을 반환하면 암호화는 되더라도 신뢰할 상대인지 확인하지 못할 수 있습니다.')],
      [api('SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, nullptr)','peer 검증 모드, 기본 검증 동작 사용.','CTX 소유권 변화 없음.','void 반환.','검증 callback으로 실패를 무조건 허용하지 않습니다.'),
       api('SSL_set1_host(ssl, hostname)','검증할 DNS 이름. SNI 설정과는 별도.','이름 설정을 SSL이 보관합니다. SSL은 호출자 소유.','1 성공, 0 실패.','체인 검증 설정·CA 신뢰 로딩도 별도로 필요합니다.')],
      'SNI는 올바르게, verify_hostname은 틀리게 설정했을 때 실패하는 이유를 설명하세요.')
    set_('x509-1',[
      section('인증서의 세 부분','X.509 인증서는 서명 대상인 TBSCertificate, 서명 알고리즘 정보, 서명값으로 구성됩니다. TBSCertificate에는 serial, issuer, validity, subject, subject public key와 확장 필드 등이 들어갑니다.',
       'Public Key Algorithm은 주체 키의 종류이고 Signature Algorithm은 발급자가 그 인증서에 사용한 서명 알고리즘입니다. 서로 같은 알고리즘일 필요는 없습니다. 인증서 안에는 개인키가 없습니다.'),
      section('확장 필드를 읽는 순서','Basic Constraints의 CA 여부와 path length, Key Usage, Extended Key Usage, SAN을 확인하세요. critical 확장을 이해하지 못하는 검증자는 이를 무시하고 성공 처리하면 안 됩니다.',
       'fingerprint는 인증서 바이트의 해시이며 사람이 비교할 식별값으로 유용합니다. 이것만 출력했다고 신뢰 체인이나 서버 이름 검증이 수행된 것은 아닙니다. -checkend는 만료까지 남은 시간 확인이며 전체 인증서 검증 명령이 아닙니다.')],
      [api('X509_get_subject_name(cert)','Subject의 X509_NAME 접근.','반환값은 cert 내부의 빌린 포인터. 별도 X509_NAME_free 금지.','X509_NAME* 조회.','cert를 해제한 뒤 반환 포인터를 사용하지 않습니다.')],
      '서버 공개키 알고리즘, 발급자 서명 알고리즘, SAN을 찾아 각각 다른 질문에 답하는 정보임을 설명하세요.')
    set_('x509-2',[
      section('CSR 서명이 보장하는 범위','CSR의 self-signature 검증은 요청이 해당 개인키로 만들어졌는지 확인합니다. 요청한 DNS 이름을 실제 소유한다거나 신뢰할 CA가 발급을 승인했다는 뜻은 아닙니다.',
       '실제 CA는 인증 정책에 따라 요청자를 검증하고 허용할 확장을 선택합니다. 요청에 CA:TRUE가 들어 있다고 그대로 복사하면 안 됩니다. 이 실습은 서버 인증서 확장을 별도 ext 파일로 명시합니다.'),
      section('학습용 CA와 운영 CA의 차이','x509 -req로 작은 발급 실험을 하지만 발급 DB, serial 관리, 감사, 폐기, 키 보관을 갖춘 CA 운영 도구를 완성한 것은 아닙니다. root.key와 site.key는 역할이 다른 비밀입니다.',
       'CA 키가 노출되면 그 CA를 신뢰하는 검증자에게 가짜 인증서를 발급할 수 있습니다. 이 컨테이너의 키를 외부 서비스에 설치하지 않고, 실험용 CA를 호스트의 전역 신뢰 저장소에 추가하지 않습니다.')],
      [api('EVP_PKEY / X509_REQ / X509','각각 키, 인증서 발급 요청, 인증서 객체.','EVP_PKEY_free / X509_REQ_free / X509_free로 각각 관리.','객체를 만드는 함수의 반환값을 개별 검사.','키·요청·인증서를 같은 파일이나 같은 객체라고 가정하지 않습니다.')],
      'site.csr의 공개키와 site.pem의 공개키가 같은지 openssl req -pubkey와 x509 -pubkey로 비교하세요.')
    set_('x509-3',[
      section('ASN.1, DER, PEM의 층','ASN.1은 데이터 구조를 표현하는 체계이고 DER은 그 구조의 정규 바이너리 인코딩 규칙입니다. PEM은 라벨과 Base64로 바이너리를 감싸는 텍스트 표현입니다. CERTIFICATE와 PRIVATE KEY 라벨은 다른 객체 종류를 나타냅니다.',
       '파일 확장자가 .pem이어도 인증서, 키, CSR 또는 여러 객체 묶음일 수 있습니다. 명령어에서 -inform을 맞추고 입력의 라벨과 구조를 확인해야 합니다.'),
      section('시간 검증 실험','-attime은 검증 기준 시간을 바꿉니다. 2100년을 주면 현재 발급한 인증서가 만료된 것으로 거부됩니다. 시스템 시간을 변경하는 실험이 아닙니다.',
       '인증서 텍스트를 정상 출력할 수 있어도 유효기간 밖일 수 있습니다. 파싱, 형식 변환, 신뢰 검증을 별도 작업으로 구분하세요.')],
      [api('PEM_read_bio_X509 / d2i_X509','PEM 파싱과 DER 디코딩은 입력 표현이 다릅니다.','새 X509 반환 시 호출자가 X509_free. d2i 포인터 진전 규칙은 개별 문서 확인.','포인터 또는 nullptr.','형식 변환이나 파싱 성공을 서명·신뢰 검증으로 해석하지 않습니다.')],
      '두 PEM 파일의 줄바꿈이 달라도 DER 바이트가 같을 수 있는 이유를 설명해 보세요.')
    set_('arch-1',[
      section('CLI에서 라이브러리로','openssl 명령어는 libcrypto와 libssl을 사용하는 애플리케이션입니다. C++ 예제도 같은 라이브러리에 링크합니다. 빌드 시 헤더 버전과 실행 중 로드되는 라이브러리 버전이 맞는지 확인하는 습관이 필요합니다.',
       '프로젝트는 Debian의 OpenSSL 3.5.7 패키지 버전을 고정합니다. 3.5.7과 같은 숫자라도 배포판 패치와 빌드 옵션이 다를 수 있습니다. version -a는 그 환경을 진단하는 출발점입니다.'),
      section('Provider는 프로토콜이 아니다','Provider는 암호 알고리즘 구현을 공급합니다. TLS 상태 머신 전체가 default Provider 파일 하나에 들어 있다는 모델은 맞지 않습니다. libssl은 프로토콜을 처리하고 필요한 암호 연산은 libcrypto API를 통해 수행합니다.',
       'FIPS Provider 이름을 선택했다고 전체 애플리케이션이 자동으로 규정 준수 상태가 되는 것도 아닙니다. 모듈 버전, 설정, 검증 범위와 운영 조건을 함께 확인해야 합니다. 이 학습 환경은 일반 default Provider 환경입니다.')],
      [api('OpenSSL_version(OPENSSL_VERSION)','현재 로드된 라이브러리 버전 문자열 조회.','반환 문자열은 빌린 읽기 전용 데이터. free하지 않습니다.','const char*.','컴파일 시 OPENSSL_VERSION_TEXT와 실행 버전을 혼동하지 않습니다.')],
      'ldd로 예제 바이너리가 어느 libssl.so.3와 libcrypto.so.3를 사용하는지 확인하세요.')
    set_('arch-2',[
      section('명시적 fetch의 수명','provider.cpp는 library_context, provider, algorithm 순서로 객체를 만듭니다. C++ 지역 객체는 선언의 역순으로 파괴되므로 algorithm을 먼저 해제하고 Provider와 라이브러리 컨텍스트를 나중에 정리합니다. 알고리즘 객체가 사용하는 환경을 먼저 정리하지 않도록 구조를 분명히 합니다. get0_provider 결과는 조회를 위한 빌린 포인터입니다.',
       'nullptr libctx는 아무 환경도 없다는 뜻이 아니라 기본 라이브러리 컨텍스트 사용입니다. 별도 OSSL_LIB_CTX는 설정과 Provider 선택을 분리할 때 유용하며 TLS 연결 객체 SSL과 같은 개념이 아닙니다.'),
      section('선택 조건이 실패하는 경우','SHA256이라는 이름이 존재해도 provider=missing 조건을 만족하는 구현은 없습니다. fetch의 nullptr을 확인하지 않고 Init에 넘기는 대신 이 지점에서 원인을 진단합니다.',
       '매 작은 블록마다 같은 구현을 새로 fetch할 필요는 없습니다. 적절한 수명 범위에서 구현 객체를 유지할 수 있습니다. 다만 계산 상태인 EVP_MD_CTX를 여러 동시 연산이 공유하도록 만들지는 마세요.')],
      [api('OSSL_PROVIDER_load(libctx, name)','어느 library context에 어떤 Provider를 로딩할지 지정.','성공한 로드 핸들은 OSSL_PROVIDER_unload로 내려놓음.','핸들 또는 nullptr.','모듈 경로·빌드·이름·설정 오류를 확인합니다.'),
       api('EVP_MD_get0_provider(md)','이 digest 구현의 제공자 조회.','borrowed. 반환 Provider를 별도 owning 핸들에 넣지 않습니다.','const OSSL_PROVIDER*.','get0 결과에 unload 책임을 임의로 부여하지 않습니다.')],
      'provider.cpp에서 명시적 libctx를 nullptr로 바꿀 때 무엇이 공유되는지 설명하세요.')
    set_('arch-3',[
      section('이식에서 확인할 세 층','소스 수준의 deprecated API, 실행 환경의 Provider·설정, 실제 암호 정책을 따로 점검하세요. 컴파일 경고를 숨기는 것만으로 런타임 호환성과 적절한 알고리즘 선택이 해결되지 않습니다.',
       'ENGINE은 오래된 확장 모델입니다. OpenSSL 3에서는 Provider 기반 알고리즘 선택과 상호작용을 검토해야 합니다. 단순히 legacy Provider를 켜는 것은 모든 ENGINE 기반 코드의 이식 방법이 아닙니다.'),
      section('테스트 범위를 명시하기','MD4 실패·성공은 로딩과 알고리즘 가용성을 배우는 실험입니다. 생산 환경에서 구형 알고리즘을 전역으로 허용하라는 권고가 아닙니다. 필요한 호환성 범위와 적용 프로세스를 좁혀야 합니다.')],
      [api('EVP_MD_fetch(ctx, name, properties)','새 코드에서 고수준 API와 명시적 구현 선택을 학습.','fetch 객체와 연산 ctx의 수명을 분리.','nullptr이면 실패.','deprecated 경고를 없애는 변경 후에도 알려진 입력·실패 사례를 테스트합니다.')],
      'legacy를 명시적으로 로딩한 명령 다음에 기본 list -providers를 실행해 프로세스별 상태 차이를 확인하세요.')
    set_('code-1',[
      section('이제 C++ 객체 관점으로 다시 읽기','앞부분에서는 해시의 개념을 배웠습니다. 여기서는 study.hpp의 deleter, unique_ptr, require, 예외 처리와 각 EVP 호출의 인자를 추적합니다. 같은 예제를 다른 질문으로 다시 읽는 레슨입니다.',
       'digest.cpp에서 algorithm.get()과 digest_context.get()은 각각 EVP_MD*와 EVP_MD_CTX*를 반환합니다. 여기서 get()은 소유권을 이전하지 않습니다. API는 호출에 필요한 객체를 사용하고, 해제 책임은 C++ 핸들에 남습니다. API 호출이 실패하면 require가 예외를 던지고 지역 핸들이 역순으로 해제됩니다. main의 catch는 오류를 출력하고 프로세스 종료 코드 1을 반환합니다.'),
      section('문자열과 버퍼의 타입','Update 길이는 size_t, Final 출력 길이는 unsigned int입니다. 함수 원형을 읽고 타입을 맞춥니다. 다른 API의 int 길이 인자에 임의 크기 size_t를 캐스팅하는 습관을 만들지 않습니다.',
       'std::string의 data()와 size()를 함께 쓰면 NUL을 포함하는 데이터도 계산할 수 있습니다. 명령행 인자는 NUL을 직접 포함할 수 없으므로 바이너리 실험은 코드 내부 배열이나 파일 입력으로 확장하세요.')],
      [api('EVP_DigestInit_ex2(ctx, md, params)','이번 계산의 context, fetch한 digest, 추가 params(없으면 nullptr).','ctx/md 소유권은 호출자 유지.','1 성공, 0 실패.','Init 실패 뒤 Update/Final을 이어서 호출하지 않습니다.'),
       api('EVP_DigestFinal_ex(ctx, out, &length)','충분한 out 버퍼와 unsigned int 출력 길이 포인터.','out은 호출자 소유.','1 성공, 0 실패.','결과를 사용한 뒤 다음 메시지는 Init으로 새 계산을 시작합니다.')],
      'digest.cpp를 복사해 직접 입력하고 빈 문자열·abc·UTF-8 문자열을 CLI와 비교하세요.')
    set_('code-2',[
      section('Ed25519에 맞는 API 사용','Ed25519는 이 예제에서 외부 digest 이름을 지정하지 않는 one-shot 서명·검증을 사용합니다. SHA256을 무조건 모든 서명 Init에 넣거나 Update/Final 스트리밍 형태를 모든 알고리즘에 적용하지 않습니다.',
       '먼저 nullptr 출력으로 서명 길이를 질의하고 벡터를 할당한 뒤 실제 서명을 얻습니다. 공개키를 raw 형태로 내보내 별도 객체를 만들므로 검증에 개인키가 필요하지 않다는 사실을 확인할 수 있습니다.'),
      section('키가 다르면 메시지가 같아도 실패','tamper는 메시지가 바뀐 경우, wrong-key는 검증 키가 다른 경우입니다. 두 경우 모두 유효한 서명을 확인하지 못하면 데이터를 거부해야 합니다. 오류 큐가 비어 있어도 0 반환값을 무시해서는 안 됩니다.')],
      [api('EVP_DigestSignInit_ex(ctx, pctx, mdname, libctx, props, key, params)','Ed25519에서는 mdname=nullptr. 이 예제는 pctx 출력이 필요 없어 nullptr.','MD_CTX와 EVP_PKEY를 각각 RAII로 유지.','1 성공, 0 실패.','알고리즘이 요구하는 digest·one-shot 규칙을 확인합니다.'),
       api('EVP_DigestVerify(ctx, sig, siglen, msg, msglen)','검증할 서명 바이트와 원문 바이트.','입력은 호출자 소유.','1 유효, 0 유효하지 않음, 음수 기타 오류.','if(ret)로 검사하면 음수 오류를 성공 처리할 수 있습니다. 반드시 1과 비교합니다.')],
      'wrong-key와 tamper의 차이를 설명하고, 두 경우에 출력 데이터가 신뢰되지 않아야 하는 이유를 적어보세요.')
    set_('code-3',[
      section('세 종류의 상태 객체','SSL_CTX는 설정과 공유 자원의 컨텍스트, SSL은 한 TLS 연결의 상태, socket fd는 OS transport 자원입니다. SSL_new는 CTX에 대한 참조를 유지하지만 학습 코드에서는 CTX를 더 오래 살려 관계를 명확히 합니다.',
       'TLS_client_method는 역할을, set_min_proto_version은 최소 허용 버전을 설정합니다. CA 로딩·verify_peer·set1_host를 모두 확인한 뒤 SSL_connect를 시작합니다. 검증 실패는 HTTP 쓰기 이전에 중단되어야 합니다.'),
      section('호출과 오류 처리 순서','각 I/O 앞에서 처리된 이전 오류 큐를 비우고 호출합니다. 성공하지 않으면 중간 OpenSSL 호출 없이 SSL_get_error를 확인합니다. SSL_read_ex의 0은 그 자체로 정상 EOF가 아닙니다.',
       'peer 인증서를 get1으로 얻어 Cert가 소유합니다. read에서 close_notify를 확인한 뒤 shutdown을 완료하고, 스코프를 나갈 때 peer·SSL·fd·CTX를 정리합니다. 예제는 블로킹 소켓 시간 제한을 두지만 HTTP 파서는 아닙니다.')],
      [api('SSL_new(ctx) / SSL_free(ssl)','공통 CTX에서 새 연결 상태 생성.','SSL은 호출자 소유. new가 CTX 참조를 유지하며 SSL_free가 내려놓습니다.','SSL* 또는 nullptr.','같은 SSL 객체를 여러 연결에 동시에 사용하지 않습니다.'),
       api('SSL_CTX_load_verify_locations(ctx, cafile, capath)','cafile: 신뢰할 CA PEM 파일. capath=nullptr: 디렉터리 소스 없음.','문자열 포인터 소유권 이동 없음.','1 성공, 0 실패.','CA 로딩 실패를 무시하고 연결하지 않습니다.'),
       api('SSL_get_verify_result(ssl)','현재 연결에 저장된 인증서 검증 결과.','조회 API.','X509_V_OK 또는 검증 오류 코드.','검증을 켰는지, peer 인증서가 존재하는지도 확인합니다. 단독 호출로 검증 정책을 대신하지 않습니다.')],
      '실패 지점마다 HTTP 요청이 전송되었는지 추적하세요. SSL_free와 close(fd)가 각각 필요한 이유를 설명하세요.')
    # Original IDs remain; untouched C sources stay available as optional legacy material.
    replacements={
      'arch-2':('provider',[('정상 fetch','선언·해제 순서를 읽어보세요.',build('provider','provider=default'),'provider=default'),('조건 불일치','오류 큐와 exit를 확인합니다.',build('provider','provider=missing')+'\necho "exit=$?"','EVP_MD_fetch 실패, exit=1')]),
      'code-1':('digest',[('C++로 컴파일','-std=c++20, -Wall -Wextra -Werror를 사용합니다.',build('digest','hash abc'),'ba7816bf…'),('빈 입력과 CLI','같은 바이트끼리 비교하세요.',build('digest',"hash ''")+'\nprintf abc | openssl dgst -sha256','빈 입력 해시 e3b0c442… 및 abc 해시')]),
      'code-2':('sign',[('서명·검증','public key 객체를 따로 만듭니다.',build('sign'),'signature VERIFIED'),('변조·다른 키','둘 다 거부되어야 합니다.','cd ~/lab\n./examples/cpp/sign tamper; echo "exit=$?"\n./examples/cpp/sign wrong-key; echo "exit=$?"','둘 다 signature REJECTED, exit=2')]),
      'code-3':('tls_client',[('정상 연결','기본 인자는 blocking localhost입니다.',build('tls_client'),'Verified TLS / HTTP/1.0 200 ok / shutdown complete'),('이름 검증 실패','원래 목적지 주소와 검증 이름을 구분합니다.',build('tls_client','blocking wrong.example')+'\necho "exit=$?"','certificate verify failed, exit=1')])}
    for id,(name,steps) in replacements.items():
        by[id]['file']=f'examples/cpp/{name}.cpp'
        by[id]['steps']=[step(*s) for s in steps]
        by[id]['intro']=by[id]['intro'].replace('provider.c','provider.cpp')
    by['code-3']['concepts']=[
      'SSL_CTX는 공통 설정, SSL은 개별 연결 상태입니다. 예제는 SSL_set_fd를 사용하고 SSL과 socket fd를 각각 RAII로 해제합니다.',
      '체인 검증, CA 신뢰, 호스트 이름 검증을 함께 설정하고 SNI와 구분합니다.',
      'C++20 학습용 단일 연결 클라이언트입니다. 다음 레슨에서 같은 코드를 epoll로 진행합니다.']
