// 인자 없이 실패한 fetch의 오류 큐를 관찰합니다.
// 실행: study-build examples/cpp/errors.cpp

#include "study.hpp"

int main() try {
    // 1. 이전 오류를 지우고 의도적으로 지원하지 않는 알고리즘을 요청합니다.
    ERR_clear_error();
    study::Md missing(EVP_MD_fetch(nullptr, "NO_SUCH_DIGEST", nullptr));
    study::require(!missing, "expected missing digest");

    study::require(ERR_peek_error() != 0, "error queued");

    // 2. peek은 오류를 남겨 두며 errors()는 오류를 모두 꺼냅니다.
    std::cout << "PEEK leaves queue intact\n";

    // peek은 첫 오류를 남겨 둡니다. errors()는 ERR_get_error를 반복 호출해 현재 스레드의 오류를
    // 꺼냅니다.
    std::cout << study::errors();
    study::require(ERR_get_error() == 0, "queue drained");

    // 3. 오류를 소비한 뒤 정상 연산을 다시 시도합니다.
    study::Md sha(EVP_MD_fetch(nullptr, "SHA256", nullptr));
    study::require(bool(sha), "recovery fetch");

    std::cout << "DRAINED; recovery OK\n";
} catch (const std::exception& e) {

    return study::failed(e);
}
