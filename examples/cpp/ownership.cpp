// 두 소유자가 같은 키를 가리키는 경우와 소유권을 이동하는 경우를 비교합니다.
// 실행: study-build examples/cpp/ownership.cpp

#include "study.hpp"

int main(int argc, char **) try {
    study::Key first(EVP_PKEY_Q_keygen(nullptr, nullptr, "ED25519"));
    study::require(bool(first), "keygen");
    // 두 번째 Handle도 나중에 free를 호출합니다. 먼저 참조 수를 올려 두 번의 해제와 짝을 맞춥니다.
    study::require(EVP_PKEY_up_ref(first.get()) == 1, "up_ref");
    study::Key second(first.get()); // Legal only because up_ref gave us another reference.
    first.reset();
    study::require(EVP_PKEY_is_a(second.get(), "ED25519") == 1, "second remains alive");
    std::cout << "REFERENCE OK after first.reset()\n";
    auto moved = std::move(second);
    study::require(!second && bool(moved), "move ownership");
    std::cout << "MOVE OK; old owner empty\n";
    if (argc > 1)
        throw std::runtime_error("intentional exception; remaining owner released by RAII");
} catch (const std::exception &e) {
    return study::failed(e);
}
