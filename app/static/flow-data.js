// Ordered educational models. Labels explicitly distinguish local computation and transmission.
const flowTopics = [
  {id:'overview', title:'전체 연결 지도', intro:'암호 기법은 서로 다른 문제를 해결합니다. 하나의 알고리즘이 모든 보장을 제공하지 않습니다.', scope:'개념 의존 관계입니다. 이 순서가 모든 프로토콜의 실제 메시지 순서를 뜻하지는 않습니다.', lesson:'basic-bytes', docs:['https://docs.openssl.org/3.5/man7/crypto/'],
   steps:[
    ['목표 정하기','설계 · 로컬','기밀성 / 무결성 / 상대 인증','어떤 공격을 막으려는지 먼저 구분합니다. 해시만 붙여서는 공격자가 데이터와 해시를 함께 바꾸는 것을 막을 수 없습니다.','EVP_Digest'],
    ['공유 비밀 만들기','키 교환','개인키 + 상대 공개키 → 공유 비밀','ECDH는 같은 비밀을 계산하게 하지만 상대의 신원을 자동으로 확인하지 않습니다. 인증된 공개키와 프로토콜이 필요합니다.','EVP_PKEY_derive'],
    ['용도별 키 유도','로컬 계산','공유 비밀 + 문맥 → 여러 키','HKDF로 송신·수신 등 용도에 따라 키를 분리합니다. 입력에 없던 엔트로피를 만들어 주는 것은 아닙니다.','EVP_KDF'],
    ['상대 인증','검증','신뢰 정책 + 인증서 + 서명 → 수락/거부','인증서 체인과 이름을 확인하고, 핸드셰이크 서명으로 개인키 보유를 확인합니다. 인증서의 존재만으로 충분하지 않습니다.','X509_verify_cert'],
    ['데이터 보호','전송','키 + nonce + 평문 + AAD → 암호문·태그','AEAD는 기밀성과 무결성을 결합합니다. 인증 성공 뒤에만 복호화 결과를 사용합니다.','EVP_Decrypt'] ],
   columns:['도구','입력 / 출력','제공하는 것','단독으로 제공하지 않는 것'], rows:[['해시','메시지 → digest','고정 길이 요약','비밀성·발신자 인증'],['HMAC','비밀키 + 메시지 → 태그','공유키 기반 무결성','암호화·제3자에게 서명 증명'],['서명','개인키 + 메시지 → 서명','공개키로 검증 가능','메시지 암호화·공개키의 신뢰'],['ECDH','내 개인키 + 상대 공개키 → 비밀','공유 비밀 합의','상대 신원 인증'],['HKDF','입력 키 재료 + salt/info → 키','키 재료 정리·용도 분리','비밀번호 추측 비용 강화'],['AEAD','키·nonce·평문·AAD → 암호문·태그','기밀성 + 무결성','키 소유자의 현실 신원']]},
  {id:'mac',title:'해시와 HMAC',intro:'같은 해시 계열을 사용하더라도 비밀키의 유무에 따라 의미가 달라집니다.',scope:'공유 비밀키 K가 안전하게 준비된 두 참여자의 메시지 인증 모델입니다.',lesson:'basic-mac',docs:['https://docs.openssl.org/3.5/man7/EVP_MAC-HMAC/'],
   steps:[['송신자: 태그 계산','송신자 내부','K + M → HMAC(K, M) = T','K는 비밀키, M은 메시지, T는 인증 태그입니다. HMAC은 암호화가 아니므로 M을 숨기지 않습니다.','EVP_MAC'],['메시지와 태그 전달','송신자 → 수신자','M, T 전송 / K는 전송하지 않음','통신 상대가 이미 같은 K를 알고 있다고 가정합니다. K를 메시지와 함께 공개하면 인증의 근거가 사라집니다.','EVP_MAC'],['수신자: 재계산','수신자 내부','K + 받은 M → T′','같은 키와 정확히 같은 바이트가 필요합니다. 문자 인코딩이나 개행도 결과를 바꿉니다.','EVP_MAC'],['태그 비교','수신자 검증','T와 T′ 일치 → 수락','길이를 확인하고 타이밍 정보가 새지 않는 비교 방식을 사용합니다. 검증 성공도 재전송 공격 방지를 자동 제공하지는 않습니다.','CRYPTO_memcmp']],
   columns:['조건','해시','HMAC'],rows:[['비밀키','없음','있음'],['공격자가 메시지와 결과를 함께 수정','새 해시 계산 가능','키 없이 유효 태그 생성은 어려워야 함'],['누가 만들었는가','판단 불가','공유키를 아는 주체 중 하나'],['재전송 방지','별도 설계','counter/nonce 등의 인증과 상태 관리 필요']]},
  {id:'signature',title:'서명과 신뢰',intro:'서명 검증의 수학적 성공과 “그 공개키가 누구 것인가”는 별개의 질문입니다.',scope:'일반적인 공개키 서명 모델입니다. 알고리즘별 digest 처리와 API 제약은 다릅니다.',lesson:'code-2',docs:['https://docs.openssl.org/3.5/man3/EVP_DigestSignInit/'],
   steps:[['서명 생성','서명자 내부','개인키 + 메시지 → 서명','개인키는 외부로 보내지 않습니다. Ed25519 같은 알고리즘에 임의로 사전 해시를 추가하면 다른 서명 체계가 될 수 있습니다.','EVP_DigestSign'],['검증 자료 전달','서명자 → 검증자','메시지 + 서명 + 공개키/인증서','메시지는 일반적으로 비밀이 아닙니다. 공개키를 공격자가 바꿔치기할 수 없도록 신뢰 근거를 확인해야 합니다.','EVP_DigestVerify'],['공개키 신뢰 확인','검증 정책','체인·이름·용도·시간 → 허용 여부','신뢰 저장소의 루트가 정책의 출발점입니다. 자기서명이라는 사실만으로 신뢰하지 않습니다.','X509_verify_cert'],['서명 검증','검증자 내부','공개키 + 메시지 + 서명 → 성공/거부','메시지 변경이나 잘못된 공개키는 검증을 실패시킵니다. 검증 실패와 내부 오류의 반환값도 구분합니다.','EVP_DigestVerify']],columns:['보관 / 전송','내용','주의'],rows:[['비공개 보관','개인키','서명자가 보호'],['공개 가능','공개키·서명','공개 가능과 신뢰 가능은 다름'],['인증서','신원 정보와 공개키의 결합','체인 및 정책 검증 필요']]},
  {id:'kdf',title:'ECDH → HKDF',intro:'키 교환의 출력은 보통 곧바로 모든 용도의 암호키로 쓰지 않습니다.',scope:'인증은 별도로 이루어진다고 가정한 ECDH와 일반 HKDF 모델입니다. TLS의 전체 키 스케줄은 더 복잡합니다.',lesson:'basic-kdf',docs:['https://www.rfc-editor.org/rfc/rfc5869','https://docs.openssl.org/3.5/man3/EVP_PKEY_derive/'],
   steps:[['키 쌍 준비','양쪽 로컬','Alice: a,A / Bob: b,B','소문자는 개인키, 대문자는 공개키를 나타내는 개념 표기입니다. 실제 X25519 인코딩은 정수 거듭제곱 모형과 다릅니다.','EVP_PKEY_Q_keygen'],['공개키 교환','Alice ↔ Bob','A와 B만 전달','개인키 a,b와 공유 비밀을 보내지 않습니다. 이 교환만으로 중간자 공격을 막지는 못합니다.','EVP_PKEY_derive_set_peer'],['같은 비밀 계산','양쪽 로컬','derive(a,B) = derive(b,A) = Z','서로 다른 개인키로 같은 공유 비밀 Z를 계산합니다. Z 자체의 공개 전송은 필요하지 않습니다.','EVP_PKEY_derive'],['Extract','로컬 계산','salt + IKM(Z) → PRK','HKDF-Extract는 입력 키 재료를 PRK로 정리합니다. 일반 HKDF salt는 비밀일 필요가 없지만 프로토콜에서 salt 자리에 쓰는 값은 다를 수 있습니다.','EVP_KDF'],['Expand','로컬 계산','PRK + info + 길이 L → OKM','info에 용도를 구분하는 문맥을 넣어 필요한 길이의 키 재료를 얻습니다. TLS에서는 단계별 비밀과 transcript를 결합합니다.','EVP_KDF']],columns:['값','공개 여부','역할'],rows:[['a,b','비공개','개인키'],['A,B','공개 가능','교환할 공개키'],['Z, PRK, 결과 키','비공개','공유 비밀과 유도된 비밀'],['일반 HKDF salt/info','비밀일 필요 없음','추출 입력 / 용도 구분'],['TLS에서의 salt 역할 값','단계별로 다름','유도된 비밀을 쓸 수도 있음']]},
  {id:'aead',title:'AEAD 암호화·검증',intro:'평문, 암호문, nonce, AAD, 태그를 서로 다른 입력과 출력으로 구분합니다.',scope:'AES-GCM을 떠올릴 수 있는 개념 모델입니다. nonce 길이·태그 길이·호출 순서는 알고리즘과 API에 따릅니다.',lesson:'basic-aead',docs:['https://www.rfc-editor.org/rfc/rfc5116','https://docs.openssl.org/3.5/man3/EVP_EncryptInit/'],
   steps:[['입력 준비','송신자 내부','K + nonce N + 평문 P + AAD A','키 K와 nonce N을 구분합니다. AES-GCM에서는 같은 키로 nonce를 재사용하면 보안이 무너질 수 있습니다.','EVP_EncryptInit'],['인증 암호화','송신자 내부','Encrypt(K,N,P,A) → C,T','C는 암호문, T는 인증 태그입니다. AAD는 인증되지만 암호화되지 않습니다.','EVP_EncryptUpdate'],['전달·재구성','송신자 → 수신자','C,T 및 N,A를 알 수 있는 정보','nonce와 AAD를 명시적으로 보낼지 문맥으로 재구성할지는 프로토콜이 정합니다. AEAD API가 AAD를 자동 전송하지 않습니다.','EVP_DecryptInit'],['복호화와 인증','수신자 내부','Decrypt(K,N,C,A,T) → P 또는 실패','Update에서 평문 후보가 나와도 최종 인증 성공 전에는 사용하지 않습니다. 실패하면 후보를 폐기합니다.','EVP_DecryptFinal']],columns:['값','비밀인가?','암호문인가?'],rows:[['키 K','예','아니요'],['nonce N','보통 공개 가능','아니요'],['AAD A','비밀성 제공 안 함','아니요'],['평문 P','보호할 대상','아니요'],['암호문 C / 태그 T','전송 가능','C만 암호문, T는 인증값']]},
  {id:'tls',title:'TLS 1.3 시퀀스',intro:'메시지별로 무엇을 합의하고 무엇을 증명하는지 따라갑니다.',scope:'서버 인증서 + (EC)DHE의 일반적인 전체 핸드셰이크입니다. PSK 재개·0-RTT·HRR·클라이언트 인증은 생략했습니다.',lesson:'tls-2',docs:['https://www.rfc-editor.org/rfc/rfc8446#section-2','https://docs.openssl.org/3.5/man7/ossl-guide-tls-introduction/'],
   steps:[['ClientHello','클라이언트 → 서버 · 평문','지원 버전·암호 스위트·그룹·key_share','서로 다른 협상 항목입니다. TLS 1.3 cipher suite는 AEAD와 해시를 지정하며, 키 교환 그룹이나 인증서 서명 알고리즘을 함께 지정하지 않습니다.','SSL_connect'],['ServerHello','서버 → 클라이언트 · 평문','선택한 파라미터 + 서버 key_share','양쪽이 공유 비밀과 handshake traffic key를 유도할 수 있습니다. 개인키나 최종 대칭키를 그대로 보내는 단계가 아닙니다.','SSL_connect'],['EncryptedExtensions + Certificate','서버 → 클라이언트 · 암호화','협상 결과 + 서버 인증서 체인','ALPN 등의 결과와 인증서를 전달합니다. 클라이언트는 신뢰 체인·이름·용도 등을 검사합니다.','SSL_set1_host'],['CertificateVerify','서버 → 클라이언트 · 암호화','문맥과 핸드셰이크 transcript를 포함한 서명','서버가 인증서 공개키에 대응하는 개인키를 보유함을 증명합니다. 인증서 파일을 보냈다는 사실과 다릅니다.','SSL_get1_peer_certificate'],['서버 Finished','서버 → 클라이언트 · 암호화','finished_key 기반 검증값','핸드셰이크 내용과 키 보유를 확인합니다. CertificateVerify의 공개키 서명과는 다른 계산입니다.','SSL_connect'],['클라이언트 Finished','클라이언트 → 서버 · 암호화','클라이언트의 Finished 검증값','서버가 이를 검증합니다. 양방향 애플리케이션 데이터 키는 역할별로 분리됩니다. 서버는 자신의 Finished 이후 먼저 데이터를 보낼 수도 있습니다.','SSL_accept'],['Application Data','양방향 · 암호화','AEAD로 보호한 TLS 레코드','TCP 연결, TLS 레코드, 애플리케이션 메시지는 서로 다른 경계입니다. read 한 번이 메시지 하나라는 가정을 하지 않습니다.','SSL_read_ex']],columns:['요소','역할','혼동하지 않기'],rows:[['인증서 공개키','서명 검증','ECDHE 임시 공개키와 다름'],['ECDHE key_share','공유 비밀 확립','서버 신원을 단독 인증하지 않음'],['CertificateVerify','개인키 보유와 transcript 서명','Finished와 다른 계산'],['Finished','transcript 무결성 및 키 확인','인증서 파일이 아님']]},
  {id:'x509',title:'인증서 신뢰 경로',intro:'인증서 파싱, 서명 확인, 신뢰 정책을 한 덩어리로 생각하지 않습니다.',scope:'일반적인 서버 인증 경로입니다. 폐기 확인 등 추가 정책은 배포 환경에 맞게 구성해야 합니다.',lesson:'x509-chain',docs:['https://docs.openssl.org/3.5/man3/X509_verify_cert/'],
   steps:[['인증서 파싱','로컬 처리','PEM/DER → X509 객체','형식이 올바르다는 뜻이지 신뢰된다는 뜻이 아닙니다.','PEM_read_bio_X509'],['경로 구성','검증자 내부','leaf + intermediate 후보 → 신뢰 루트','서버가 보낸 모든 인증서가 신뢰 루트가 되는 것은 아닙니다. 루트는 검증자 신뢰 저장소에서 선택합니다.','X509_STORE_CTX_init'],['체인·제약 검사','검증자 내부','서명·유효기간·CA 제약·용도','단순히 서명 하나가 맞는지만 검사하는 작업이 아닙니다. 적절한 목적과 정책을 설정해야 합니다.','X509_verify_cert'],['기대 이름 확인','검증자 정책','접속하려는 이름 ↔ SAN','SNI를 보낸 것만으로 이름 검증이 켜지는 것은 아닙니다. TLS에서는 SSL_set1_host로 기대 이름을 설정합니다.','SSL_set1_host'],['개인키 보유 확인','TLS 핸드셰이크','CertificateVerify 검증','인증서는 공개 자료입니다. 실제 연결 상대가 대응 개인키를 갖고 있는지 핸드셰이크에서 확인합니다.','SSL_connect']],columns:['질문','확인 방법'],rows:[['읽을 수 있는 인증서인가?','파싱 반환값'],['신뢰 경로가 성립하는가?','store와 체인 검증'],['원하는 서버인가?','호스트 이름·용도 정책'],['상대가 개인키를 갖고 있는가?','핸드셰이크 서명 검증']]},
  {id:'quic',title:'QUIC 연결과 스트림',intro:'같은 SSL* 타입을 사용하는 세 객체의 역할과 이벤트 처리를 구분합니다.',scope:'OpenSSL 3.5.7 내장 QUIC의 명시적 스트림 사용 모델입니다. HTTP/3 계층은 포함하지 않습니다.',lesson:'quic-events',docs:['https://docs.openssl.org/3.5/man7/openssl-quic/','https://docs.openssl.org/3.5/man3/SSL_handle_events/'],
   steps:[['Listener 준비','서버 로컬','UDP fd + context → listener','한 수신 지점에서 새 연결을 받습니다. TCP accept처럼 연결마다 별도 TCP fd가 생기는 모델과 구분합니다.','SSL_new_listener'],['연결과 인증','클라이언트 ↔ 서버','TLS 1.3 핸드셰이크 + QUIC 전송','TLS 메시지는 CRYPTO 프레임으로 전달되고 QUIC이 패킷을 보호합니다. TLS 레코드를 UDP에 그대로 넣는 것이 아닙니다.','SSL_accept_connection'],['스트림 생성','한 연결 안','connection → stream 0,4,8…','클라이언트 시작 양방향 스트림 ID의 예입니다. 각 스트림의 바이트 순서는 보장되지만 서로 다른 스트림 사이 전역 순서는 보장되지 않습니다.','SSL_new_stream'],['데이터와 이벤트','readiness / 타이머 → 처리','stream I/O + connection 이벤트 처리','재시도 요구와 UDP 준비 상태는 동일하지 않습니다. 다음 내부 타이머도 고려하여 SSL_handle_events를 호출해야 합니다.','SSL_handle_events'],['송신 종료와 연결 종료','범위를 구분','stream FIN ≠ connection close','FIN은 한 스트림의 한 방향을 끝냅니다. 연결 종료 완료와 SSL_free도 서로 다른 사건입니다.','SSL_stream_conclude']],columns:['객체 / 계층','담당','주요 API'],rows:[['listener','연결 수락','SSL_accept_connection'],['connection','UDP 전송·핸드셰이크·타이머','SSL_connect / SSL_handle_events'],['stream','개별 바이트 흐름','SSL_read_ex / SSL_write_ex'],['HTTP/3','요청·응답·QPACK','OpenSSL 내장 QUIC만으로 제공되지 않음']]}
];

flowTopics.push({
  "id": "qat",
  "title": "QAT: 선택·제출·완료",
  "intro": "Provider 선택과 실제 가속 경로, 작업 완료와 연산 성공을 나누어 봅니다.",
  "scope": "개념 흐름입니다. 현재 컨테이너의 ASYNC 예제에는 장치나 완료 fd가 없으며, 특정 QAT 버전의 이벤트 처리 구현을 재현하지 않습니다.",
  "lesson": "qat-provider",
  "docs": [
    "https://github.com/intel/QAT_Engine",
    "https://docs.openssl.org/3.5/man3/ASYNC_start_job/"
  ],
  "steps": [
    [
      "Provider 로드",
      "프로세스 초기화",
      "모듈 + 의존 라이브러리 → 핸들",
      "로드 성공은 모든 알고리즘의 지원이나 하드웨어 실행을 보장하지 않습니다.",
      "OSSL_PROVIDER_load"
    ],
    [
      "구현 선택",
      "EVP fetch",
      "알고리즘 + 필수 속성 → 구현",
      "get0_provider로 선택 결과를 확인합니다. Provider 내부 HW/SW/fallback 경로는 별도 계측이 필요합니다.",
      "EVP_CIPHER_fetch"
    ],
    [
      "연산 제출",
      "구현 내부",
      "입력·키 → 작업",
      "동기 경로는 호출 안에서 기다릴 수 있습니다. 비동기 경로는 작업을 중단하고 호출자에게 제어를 돌려줄 수 있습니다.",
      "ASYNC_start_job"
    ],
    [
      "완료 조건 대기",
      "이벤트 루프",
      "완료 통지 또는 polling → 재개 가능",
      "소켓의 읽기·쓰기 준비와 가속 연산의 완료는 다릅니다. 실제 대기 방식은 해당 구현·버전의 규칙을 따릅니다.",
      "ASYNC_pause_job"
    ],
    [
      "재개와 결과 검사",
      "원래 스레드",
      "FINISH + 연산 결과 → 사용 또는 오류",
      "FINISH만으로 성공 처리하지 않고 연산의 반환값과 결과를 검사합니다.",
      "ASYNC_start_job"
    ]
  ],
  "columns": [
    "관찰",
    "알 수 있는 것",
    "추가로 확인할 것"
  ],
  "rows": [
    [
      "Provider 로드",
      "모듈 초기화 성공",
      "원하는 구현 선택"
    ],
    [
      "selected=qatprovider",
      "선택한 공급자",
      "내부 HW/SW/fallback"
    ],
    [
      "known-answer 통과",
      "시험 입력 결과 일치",
      "다른 입력·실패 경로·성능"
    ],
    [
      "ASYNC_FINISH",
      "작업 함수 반환",
      "작업 자체의 반환값"
    ],
    [
      "speed 처리량",
      "해당 부하의 암호 연산 처리량",
      "TLS 전체 지연·CPU 비용"
    ]
  ]
});
