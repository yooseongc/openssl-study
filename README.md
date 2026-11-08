# OpenSSL Study — C++ 개발자를 위한 기초부터 API까지

암호학·TLS·OpenSSL API를 기초부터 배우되 실제 C++ 코드의 인자, 소유권, 반환값, 실패 경로까지 이해하는 로컬 학습실입니다. **OpenSSL 3.5.7 + C++20**, 6개 영역의 **37개 한국어 레슨**, **69개 API 계약 설명**, **16개 C++ 예제**가 있습니다. 안내 시간 합계는 약 18시간이며 직접 입력·변형 실험에 따라 더 걸릴 수 있습니다.

TPROXY나 프록시 구현을 가르치는 프로젝트는 아닙니다. 일반 OpenSSL의 기초를 익힌 뒤 마지막에 epoll과 Boost.Asio를 연결합니다.

## 접속과 실행

Docker Desktop을 Linux containers 모드로 실행한 후 PowerShell에서:

```powershell
git clone https://github.com/yooseongc/openssl-study.git
cd openssl-study
docker compose up -d --build
```

http://localhost:8440 에 접속합니다. 첫 빌드에는 인터넷이 필요하며, 빌드 후 교재·터미널·편집기·TLS 실습은 외부 CDN 없이 동작합니다.

## 학습 순서

| 영역 | 레슨 | 내용 |
| --- | --- | --- |
| 암호학 기초와 TLS | 12개 | 바이트·인코딩, 해시, 난수, HMAC, HKDF, AES-GCM, X25519, TLS 연결·핸드셰이크·인증 실패·record·종료 |
| X.509 인증서 | 5개 | 필드, CA·CSR·발급, PEM/DER, 중간 인증서·신뢰 앵커, C++ 파싱·검증 |
| OpenSSL 3 구조 | 6개 | 라이브러리, Provider·Fetch·Property, legacy, 참조 수·RAII, BIO, 오류 큐 |
| C++ 프로그래밍 | 5개 | EVP API 다시 읽기, Ed25519, 동기 TLS, epoll 재시도, Asio 비동기 TLS |
| QUIC | 5개 | UDP·TLS 1.3, 연결, 스트림, 실패, 이벤트 타이머 |
| QAT | 4개 | HW/SW 가속, Provider 선택과 정확성, ASYNC 중단·재개, 성능 기준선 |

처음에는 **출발점: 바이트와 암호 도구의 역할**부터 진행하세요. C++ 경험은 전제하지만 암호학 지식은 전제하지 않습니다. 초반 예제의 `study.hpp`는 소유권 관리를 돕는 공통 헤더입니다. 먼저 동작을 관찰하고 3영역에서 해제 규칙과 구현을 다시 읽습니다.

각 레슨은 용어를 풀어 설명하는 개념·상세 해설 → 용어 다시 찾기 → API 역할과 호출 방법 → 정상·실패 실험 → 변경 과제 → 퀴즈 순서입니다. 검색창에서 레슨·용어·API를 검색하고 이동 버튼으로 해당 영역을 바로 찾을 수 있습니다.

**터미널에 입력**은 붙여 넣기만 하며 Enter로 실행합니다. 레슨 아래의 **학습 완료로 표시** 버튼으로 진행 상태를 직접 기록하거나 해제합니다. 기존에 완료한 기록도 이어집니다.

## C++ 편집과 실행

오른쪽 **VS Code** 탭에서 code-server를 사용합니다. 교재의 **편집기에서 열기**와 **공통 헤더** 버튼은 IDE를 다시 로드하지 않고 해당 파일을 탭으로 엽니다. **새 파일**을 선택하면 C++ 문서를 만들며 Ctrl+S로 실습 폴더에 저장할 수 있습니다.

clangd가 C++ 자동완성·선언 이동·진단을 제공합니다. **실행 인자**에는 `nonblock wrong.example`, `hash 'hello openssl'`, `tag` 등을 입력합니다. 공백과 따옴표를 해석해 인자 배열로 전달하며 쉘 확장·리다이렉션을 하지 않습니다. 파일별 인자는 페이지가 열려 있는 동안 기억합니다.

**이 파일의 실행 인자**에서 시나리오를 고른 뒤 **저장 · 빌드 · 실행**을 누르세요. IDE의 현재 소스를 저장하고 `study-build` Task를 실행합니다. 결과는 VS Code 내장 터미널에 남습니다. 컴파일 오류는 Problems 패널과 터미널에서 확인하며 패널 경계를 드래그해 높이를 조절합니다. **최대화 / 원래 크기**는 열린 파일과 터미널을 유지합니다.

F9로 중단점을 걸고 F5로 현재 소스를 빌드·디버깅합니다. CodeLLDB를 미리 설치하며, `.vscode/launch.json`의 `args` 배열에서 디버깅 인자를 지정합니다. 아래의 실행 인자 입력란은 **저장 · 빌드 · 실행**에 적용됩니다. Shift+F5로 디버깅을 종료합니다. 기본 Task·디버깅 설정은 없는 경우에만 생성합니다.

기존 **터미널** 탭은 교재 명령을 붙여 넣는 용도로 유지합니다. 두 터미널은 같은 컨테이너·파일·OpenSSL 3.5.7·TLS 서버를 사용하지만 셸 프로세스는 별개입니다.

```bash
cd ~/lab
study-build examples/cpp/digest.cpp hash abc
study-build examples/cpp/aead.cpp tag
study-build examples/cpp/tls_client.cpp nonblock localhost
study-build examples/cpp/asio_client.cpp localhost
```

`study-build`는 C++에 `g++ -std=c++20 -Wall -Wextra -Werror -g -O0 -pthread`, 공통 헤더 include 경로, OpenSSL 링크 옵션을 적용합니다. 빌드 후 실행은 15초 timeout입니다. `.c`는 gcc와 C11로 처리합니다. 컴파일 실패 시 실행하지 않습니다.

## C++ 예제 지도

| 파일 (`examples/cpp/`) | 실험 |
| --- | --- |
| `digest.cpp` | `bytes`, `hash abc`, `hash ''`, Update 분할 |
| `random_mac.cpp` | `random`, `mac hello`, `tamper hello` |
| `kdf.cpp` | `'client traffic'`와 `'server traffic'`의 결과 비교 |
| `aead.cpp` | 정상 인증, `tag`·`aad`·`ciphertext` 변조 거부 |
| `kex.cpp` | X25519 합의, `bad-peer` 키 타입 오류 |
| `sign.cpp` | Ed25519, `tamper`·`wrong-key` 검증 거부 |
| `provider.cpp` | `provider=default`·`provider=missing` |
| `ownership.cpp` | up_ref, reset, move, `throw` 예외 정리 |
| `bio.cpp` | 바이너리 왕복, `empty` 재시도 |
| `errors.cpp` | 오류 생성·peek·drain·복구 |
| `x509.cpp` | `[인증서] [CA] [호스트 이름]` 파싱·검증 |
| `tls_client.cpp` | `[blocking 또는 nonblock] [호스트] [CA] [포트]` |
| `asio_client.cpp` | `[호스트]` 비동기 연결·인증·종료 |

예제의 프로세스 종료 코드와 OpenSSL API 반환값은 다릅니다. 예제는 보통 정상 0, 일반 오류 1, 의도적인 인증·서명·MAC 거부 2를 사용합니다. 정확한 기대값은 레슨에서 확인하세요.

## 버전과 범위

- Debian trixie의 `openssl`, `libssl-dev`, `libssl3t64`를 **3.5.7-1~deb13u3**으로 고정하고 Docker 빌드에서도 버전을 검사합니다. 배포판 패치가 포함된 3.5.7이며 upstream 원본 빌드와 옵션까지 동일하다는 뜻은 아닙니다.
- 저장소에서 고정 버전을 더 이상 제공하지 않으면 빌드는 실패합니다. 다른 버전으로 자동 전환하지 않으므로 그때 패키지 소스·고정 정책을 명시적으로 갱신해야 합니다.
- C++20, g++, 배포판 Boost.Asio, Python 3.13, aiohttp, xterm.js를 사용합니다. Boost 버전은 `dpkg-query -W libboost-dev libboost-system-dev`로 확인할 수 있습니다.
- 준비된 TLS 1.3 서버는 컨테이너 내부 `127.0.0.1:4433`입니다. CA를 호스트 신뢰 저장소에 설치하지 않습니다.
- epoll은 level-triggered 단일 연결, Asio는 단일 스레드 io_context와 순차 작업 예제입니다. 생산용 HTTP 파서·다중 연결 프록시·일반적인 양방향 종료 상태 머신은 아닙니다.
- HKDF 예제는 개념 실험이며 TLS 전체 키 스케줄 구현이 아닙니다. FIPS 인증 환경도 아닙니다.
- 실습용 상수 HMAC 키와 생성된 CA 키를 실서비스에 사용하지 않습니다.

## 데이터 보존

- 기존 `openssl-study_lab-data` Docker 볼륨의 `/home/student/lab`을 계속 사용합니다.
- 시작 시 없는 예제를 복사하고, 최초 배포본과 내용이 일치하는 기존 예제만 주석판으로 갱신합니다. 수정한 파일은 보존합니다. 새 C++ 예제는 `examples/cpp`에 추가됩니다.
- 기존 C 예제는 남아 있고 기본 프로그래밍 레슨은 C++로 연결됩니다.
- 기존 레슨 ID 12개와 localStorage 키를 유지합니다. 완료 표시는 보존되고 새 레슨 16개가 더해져 분모가 28이 됩니다. 완료 표시는 각 레슨에서 직접 변경할 수 있습니다.
- 새로고침 시 새 셸을 엽니다. 저장 파일은 유지되지만 미저장 코드·셸 내부 상태는 유지되지 않습니다. localhost와 127.0.0.1의 브라우저 진행 기록은 별개입니다.

웹은 호스트 `127.0.0.1:8440`에만 바인딩합니다. 컨테이너는 student 계정이며 Docker 소켓·호스트 폴더를 마운트하지 않습니다. 실제 셸을 제공하는 로컬 단일 사용자 도구이므로 LAN/인터넷 공개용 인증 서비스로 사용하지 않습니다.

## 관리

```powershell
docker compose ps
docker compose logs --tail 100
docker compose stop
docker compose start
docker compose down           # 컨테이너 제거, 볼륨 유지
docker compose up -d --build   # 변경 반영
docker compose exec study bash
docker compose cp study:/home/student/lab ./lab-backup
```

`docker compose down -v`는 실습 파일을 삭제합니다. 완전 초기화할 때만 사용하세요. 브라우저 기록은 별도입니다. TLS 서버는 웹 터미널의 `lab-server start|stop|status`로 관리합니다. 준비된 서버 인증서는 1년 유효하므로 장기 사용 시 재발급해야 합니다.

예제 원본 복원은 파일 하나를 선택합니다. `cp /opt/examples/cpp/aead.cpp ~/lab/examples/cpp/aead.cpp`는 해당 파일의 편집 내용을 덮어씁니다.

## 검증

```powershell
docker compose exec -T study python /opt/scripts/cpp_test.py
docker compose exec -T study python /opt/scripts/curriculum_test.py
docker compose exec -T study python /opt/scripts/web_test.py
```

- `cpp_test.py`: 임시 폴더에서 13개 C++ 예제 빌드, SHA-256/HMAC/HKDF 독립 계산 비교, AEAD 3종 변조, 서명·키 타입 오류, 인증서 검증, 동기·epoll·Asio TLS, 갑작스러운 EOF, deadline, RAII ASan/UBSan 정상·예외 경로.
- `curriculum_test.py`: 임시 폴더에서 화면의 37개 레슨 명령과 체크포인트를 순서대로 실행.
- `web_test.py`: 세션/Origin/Host, 경로 제한, 저장·읽기, WebSocket PTY, 교재 API.

학습자가 편집한 파일을 바꾸지 않습니다. 전체 검사에는 수십 초 이상 걸릴 수 있고 실습 서버가 실행 중이어야 합니다. 기존 `smoke_test.py`는 보존된 C 예제용입니다.

## 소스 구조

- `app/curriculum.py`: 기존 레슨과 확장 로딩
- `app/advanced.py`: 추가 레슨·상세 해설·API 계약
- `app/enrichment.py`: 기존 레슨 보강
- `app/checks.py`, `scripts/check_cpp.py`: 결과 검사
- `app/static/`: 웹 UI·편집기
- `examples/cpp/`: C++20 예제·RAII 헤더
- `scripts/failure_lab.py`, `scripts/make-chain.sh`: 종료 실패·인증서 체인 실험

레슨마다 OpenSSL 3.5 공식 문서, TLS RFC, Boost 공식 문서 링크가 있습니다. 실행 결과와 문서를 함께 읽고 실패 원인을 설명할 수 있는지를 기준으로 다음 단계로 진행하세요.

## 내장 IDE 구성

- Linux amd64용 code-server 4.145.2, clangd 확장 0.6.0, CodeLLDB 1.12.3을 이미지에 설치합니다. code-server와 디버거 배포 파일의 SHA-256을 빌드 시 검증합니다.
- `study` 컨테이너 하나에서 웹 서버와 code-server를 student 권한으로 실행합니다. 어느 서비스가 종료되면 supervisor가 나머지도 정리합니다.
- 공개 포트는 기존 `127.0.0.1:8440` 하나입니다. `/ide/`는 학습 세션과 Host/Origin 검사를 거쳐 내부 `127.0.0.1:8090`으로 HTTP·WebSocket을 전달합니다. IDE에만 동일 출처 프레임을 허용합니다.
- `ide-extension/`은 파일 열기·저장·실행을 VS Code API로 연결합니다. 내부 연결은 프로세스별 임시 포트와 시작 시 생성하는 인증 토큰을 사용합니다. 단일 사용자 환경에서 최근 활성화한 IDE 창을 대상으로 하므로 학습실 한 탭 사용을 권장합니다.
- 기존 `lab-data`를 유지하고 IDE 설정·세션 저장용 `ide-data` 볼륨을 추가합니다. 초기 설정은 사용자가 수정한 설정 파일을 덮어쓰지 않습니다. 컨테이너 메모리 한도는 2GB입니다.
- IDE 확장은 이미지에 포함됩니다. 추가 설치한 확장은 컨테이너 재생성 시 유지되지 않으므로 필요한 확장은 Dockerfile에 고정해 추가합니다.
- IDE 접속 검사는 `docker compose exec -T study python /opt/scripts/ide_test.py`로 실행합니다.

## QUIC 전용 섹션 (OpenSSL 3.5.7)

목차의 다섯 번째 영역에서 QUIC/TLS/HTTP3 구분, 연결·인증·ALPN, 스트림·FIN·종료, 실패 진단, epoll과 타이머를 순서대로 학습합니다. 기존 학습 완료 기록은 유지되고 전체 레슨 수는 37개입니다.

`cd ~/lab && study-build examples/cpp/quic_local.cpp ok`로 시작합니다. `multi`, `bad-host`, `bad-alpn`, `epoll` 실행인자를 IDE에서도 선택할 수 있습니다. 서버는 실행마다 loopback 임의 UDP 포트에서 자동으로 생성·정리됩니다. 외부 서버나 추가 포트 공개가 필요하지 않습니다. 이름·ALPN 실패는 exit=1이 예상 결과입니다.

이 예제는 study/1 echo 프로토콜이며 HTTP/3 구현이 아닙니다. multi는 스트림을 순서대로 교환하고, epoll 모드는 클라이언트 I/O만 비동기입니다. 종료는 blocking rapid shutdown으로 단순화했습니다. 연결 이동·0-RTT·손실 주입·부하 테스트는 포함하지 않습니다. 일반적인 API 계약과 실습의 제한을 레슨에 구분해 설명합니다.

`docker compose exec -T study python /opt/scripts/quic_test.py`는 임시 작업 공간에서 컴파일, 정상 echo, 세 스트림 ID, epoll, 두 가지 거부 경로를 검증합니다. 기존 학생 파일은 수정하지 않습니다.

## 흐름 지도와 API 사전

상단의 **흐름 지도·API 사전**에서 별도 시각 학습 페이지를 엽니다. 전체 연결 지도, HMAC, 서명, ECDH/HKDF, AEAD, TLS 1.3, 인증서 신뢰 경로, QUIC, QAT의 9개 흐름을 단계별 설명·비교표로 확인합니다. 각 단계는 관련 API 검색과 교재로 연결됩니다.

API 사전은 기존 교재 데이터를 읽어 이름·기능·인자와 분야로 검색합니다. 일반 계약이 동일한 항목만 합치고 설명이 다른 항목은 유지합니다. OpenSSL 전체 API를 망라하는 사전은 아닙니다. 학습 완료 기록을 변경하지 않습니다.

교재는 각 레슨의 배경·핵심 질문·관찰 목표를 제시하고 흐름 지도와 API 사전으로 연결합니다. 코드 설명과 API 카드의 발췌는 배포 예제에서 생성되며 파일·행·검색할 표현을 표시합니다. 직접 수정한 IDE 파일과는 달라질 수 있습니다. `python /opt/scripts/teaching_test.py`로 설명의 코드 위치가 실제 배포 소스와 일치하는지 검사합니다.

## QAT 학습 범위

QAT 섹션은 하드웨어 없이 Provider 선택·실패 처리와 실제 OpenSSL ASYNC API를 실험할 수 있습니다. `qat_probe.cpp`는 선택한 Provider로 AES-GCM 결과를 확인하고, `async_pause.cpp`는 작업 완료와 작업 성공의 차이를 보여 줍니다. QAT 모듈이 없으면 명시적으로 exit=77을 출력합니다. 기본 이미지에는 Intel QAT Provider·드라이버를 설치하지 않으며 하드웨어 가속을 제공한다고 주장하지 않습니다. 실제 장치 실행은 지원 호스트·드라이버·Provider 조합과 별도 계측이 필요합니다.

검증: `docker compose exec -T study python /opt/scripts/qat_test.py`. 기존 학습 파일을 건드리지 않고 임시 폴더에서 컴파일·실행합니다.
