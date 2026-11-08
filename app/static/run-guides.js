const exampleGuides = {

  "examples/cpp/crl_verify.cpp": {
    "desc": "먼저 폐기 섹션의 setup을 실행하세요. 폴더 인증서이름 CRL종류 순서입니다. CRL 검증 거부는 exit=5이며 이유를 별도 출력합니다.",
    "choices": [
      [
        "revocation good current",
        "정상 인증서 + 현재 CRL"
      ],
      [
        "revocation revoked current",
        "폐기 거부"
      ],
      [
        "revocation good missing",
        "CRL 누락"
      ],
      [
        "revocation good stale",
        "CRL 만료"
      ]
    ]
  },
  "examples/cpp/ocsp_verify.cpp": {
    "desc": "폴더 인증서이름 응답이름 순서입니다. 확장자는 자동으로 붙입니다. 공유 검증은 revocation.hpp에 있습니다.",
    "choices": [
      [
        "revocation good good",
        "정상: exit=0"
      ],
      [
        "revocation revoked revoked",
        "폐기: exit=2"
      ],
      [
        "revocation unknown unknown",
        "상태 모름: exit=3"
      ],
      [
        "revocation good revoked",
        "다른 대상: exit=5"
      ],
      [
        "revocation good stale",
        "시간 실패: exit=5"
      ],
      [
        "revocation good unauthorized",
        "서명 권한 부족: exit=5"
      ]
    ]
  },
  "examples/cpp/ocsp_fixture.cpp": {
    "desc": "setup이 호출하는 실패 자료 생성 도구입니다. 학습용 responder 개인키로 잘못된 시각의 응답을 서명하며 해당 DER 파일을 덮어씁니다.",
    "choices": [
      [
        "revocation stale",
        "만료 자료 생성"
      ],
      [
        "revocation future",
        "미래 자료 생성"
      ],
      [
        "revocation no-next",
        "nextUpdate 없는 자료 생성"
      ]
    ]
  },
  "examples/cpp/staple_client.cpp": {
    "desc": "교재의 revocation_lab.py staple 명령이 이 파일을 컴파일하고 임시 서버까지 관리합니다. 편집기에서 직접 실행하려면 먼저 별도 터미널에서 s_server를 띄우고 그 포트를 인자로 넣으세요.",
    "choices": [
      [
        "revocation 4444 strict",
        "별도 4444 TLS 서버가 실행 중일 때"
      ],
      [
        "revocation 4444 soft-missing",
        "별도 서버에서 누락 허용 정책 비교"
      ]
    ]
  }
,

  "examples/cpp/qat_probe.cpp": {
    "desc": "Provider 로딩·필수 조건 선택·AES-GCM 결과를 확인합니다. 실제 HW 실행 여부는 별도 확인이 필요합니다.",
    "choices": [
      [
        "default",
        "default 결과 검사: exit=0"
      ],
      [
        "missing",
        "없는 Provider: exit=77"
      ],
      [
        "qatprovider",
        "QAT 가용성: 미설치 시 exit=77"
      ]
    ]
  },
  "examples/cpp/async_pause.cpp": {
    "desc": "장치 없이 실제 ASYNC API의 중단·재개를 실험합니다. QAT 가속이나 완료 이벤트 대기는 수행하지 않습니다.",
    "choices": [
      [
        "ok",
        "FINISH + 작업 결과 42: exit=0"
      ],
      [
        "fail",
        "FINISH + 작업 결과 -1: exit=2"
      ]
    ]
  }
,
  "examples/cpp/quic_local.cpp": {
  "desc": "로컬 서버를 자동 실행·정리합니다. ~/lab에서 실행하며 tls 인증서를 사용합니다. HTTP/3가 아닌 study/1 echo 프로토콜입니다.",
  "choices": [
    [
      "ok",
      "인증 + 스트림 echo"
    ],
    [
      "multi",
      "한 연결에서 스트림 0·4·8"
    ],
    [
      "bad-host",
      "이름 검증 실패: exit=1"
    ],
    [
      "bad-alpn",
      "ALPN 불일치: exit=1"
    ],
    [
      "epoll",
      "비동기 클라이언트 + QUIC 타이머"
    ]
  ]
},
  "examples/cpp/digest.cpp": {
    "desc": "첫 인자는 bytes 또는 hash이고, hash 뒤에는 메시지 하나를 넣습니다.",
    "choices": [
      [
        "bytes",
        "NUL이 든 배열의 길이와 strlen 비교"
      ],
      [
        "hash abc",
        "SHA-256 계산"
      ],
      [
        "hash ''",
        "빈 입력의 해시"
      ]
    ]
  },
  "examples/cpp/aead.cpp": {
    "desc": "같은 키로 암호화·복호화한 뒤 지정한 부분의 한 비트를 뒤집어 인증을 시험합니다.",
    "choices": [
      [
        "ok",
        "인증 성공"
      ],
      [
        "tag",
        "태그 변조 → 거부"
      ],
      [
        "aad",
        "헤더 변조 → 거부"
      ],
      [
        "ciphertext",
        "암호문 변조 → 거부"
      ]
    ]
  },
  "examples/cpp/random_mac.cpp": {
    "desc": "random은 난수를 출력하고, mac과 tamper는 두 번째 인자를 메시지로 사용합니다.",
    "choices": [
      [
        "random",
        "32바이트 난수"
      ],
      [
        "mac hello",
        "태그 일치"
      ],
      [
        "tamper hello",
        "태그 불일치"
      ]
    ]
  },
  "examples/cpp/kdf.cpp": {
    "desc": "첫 인자는 HKDF의 info입니다. 공백을 포함하는 값은 따옴표로 묶습니다.",
    "choices": [
      [
        "'client traffic'",
        "클라이언트 용도"
      ],
      [
        "'server traffic'",
        "서버 용도"
      ]
    ]
  },
  "examples/cpp/kex.cpp": {
    "desc": "인자가 없으면 X25519 키 쌍으로 양쪽에서 같은 비밀을 계산합니다.",
    "choices": [
      [
        "",
        "정상 합의"
      ],
      [
        "bad-peer",
        "Ed25519 키로 합의 시도 → 실패"
      ]
    ]
  },
  "examples/cpp/sign.cpp": {
    "desc": "메시지나 검증 키를 바꾸면 Ed25519 서명이 어떻게 판정되는지 비교합니다.",
    "choices": [
      [
        "ok",
        "서명 검증 성공"
      ],
      [
        "tamper",
        "메시지 변경 → 거부"
      ],
      [
        "wrong-key",
        "다른 검증 키 → 거부"
      ]
    ]
  },
  "examples/cpp/provider.cpp": {
    "desc": "첫 인자는 SHA256 구현을 선택할 때 적용할 속성 조건입니다.",
    "choices": [
      [
        "provider=default",
        "구현 찾기"
      ],
      [
        "provider=missing",
        "조건을 만족하는 구현 없음"
      ]
    ]
  },
  "examples/cpp/ownership.cpp": {
    "desc": "두 소유자가 같은 키를 가리키는 경우와 소유권을 이동하는 경우를 비교합니다.",
    "choices": [
      [
        "",
        "참조 수와 move 관찰"
      ],
      [
        "throw",
        "예외로 스코프 빠져나가기"
      ]
    ]
  },
  "examples/cpp/bio.cpp": {
    "desc": "메모리 BIO에 바이너리를 쓰거나 빈 BIO를 먼저 읽습니다.",
    "choices": [
      [
        "",
        "바이너리 왕복"
      ],
      [
        "empty",
        "빈 BIO 읽기와 retry 확인"
      ]
    ]
  },
  "examples/cpp/errors.cpp": {
    "desc": "인자 없이 실패한 fetch의 오류 큐를 관찰합니다.",
    "choices": [
      [
        "",
        "peek 후 drain, 정상 fetch로 복구"
      ]
    ]
  },
  "examples/cpp/x509.cpp": {
    "desc": "순서대로 인증서 경로, 신뢰할 CA 경로, 기대하는 호스트 이름을 받습니다.",
    "choices": [
      [
        "",
        "기본 실습 서버 인증서 검증"
      ],
      [
        "tls/server.pem tls/ca.pem wrong.example",
        "호스트 이름 불일치"
      ]
    ]
  },
  "examples/cpp/tls_client.cpp": {
    "desc": "연결 방식, 검증할 이름, CA 경로, 포트 순서입니다. TCP 대상은 루프백입니다.",
    "choices": [
      [
        "blocking localhost",
        "동기 TLS"
      ],
      [
        "nonblock localhost",
        "epoll로 재시도"
      ],
      [
        "nonblock wrong.example",
        "호스트 이름 불일치"
      ]
    ]
  },
  "examples/cpp/asio_client.cpp": {
    "desc": "첫 인자는 인증서에서 검증할 이름입니다. TCP는 실습 서버 127.0.0.1:4433으로 연결합니다.",
    "choices": [
      [
        "localhost",
        "인증 성공"
      ],
      [
        "wrong.example",
        "인증 실패"
      ]
    ]
  },
  "examples/digest.c": {
    "desc": "첫 인자는 해시할 문자열입니다.",
    "choices": [
      [
        "abc",
        "문자열 해시"
      ],
      [
        "''",
        "빈 문자열 해시"
      ]
    ]
  },
  "examples/provider.c": {
    "desc": "첫 인자로 provider 속성 조건을 지정합니다.",
    "choices": [
      [
        "provider=default",
        "정상 조회"
      ],
      [
        "provider=missing",
        "조회 실패"
      ]
    ]
  },
  "examples/sign.c": {
    "desc": "원문과 변조된 메시지의 서명 검증 결과를 비교합니다.",
    "choices": [
      [
        "",
        "원문 검증"
      ],
      [
        "tamper",
        "메시지 변경 → 거부"
      ]
    ]
  },
  "examples/tls_client.c": {
    "desc": "검증할 호스트 이름과 CA 파일 경로를 순서대로 받습니다.",
    "choices": [
      [
        "localhost",
        "정상 연결"
      ],
      [
        "wrong.example",
        "호스트 이름 불일치"
      ]
    ]
  }
};
