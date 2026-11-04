const exampleGuides = {
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
