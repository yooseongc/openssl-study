// 두 소유자가 같은 키를 가리키는 경우와 소유권을 이동하는 경우를 비교합니다.
// 실행: study-build examples/cpp/ownership.cpp

#include "study.hpp"

int main(int argc, char**) try {
    // 1. 첫 Handle이 키의 소유 참조 하나를 받습니다.
    study::Key first_owner(EVP_PKEY_Q_keygen(nullptr, nullptr, "ED25519"));
    study::require(bool(first_owner), "keygen");

    // 두 번째 Handle도 나중에 free를 호출합니다. 먼저 참조 수를 올려 두 번의 해제와 짝을 맞춥니다.
    const int up_ref_result = EVP_PKEY_up_ref(first_owner.get());
    study::require(up_ref_result == 1, "up_ref");

    study::Key second_owner(
        first_owner.get()); // Legal only because up_ref gave us another reference.

    // 2. 첫 참조를 해제해도 두 번째 참조가 객체를 유지합니다.
    first_owner.reset();
    const int second_remains_alive_result = EVP_PKEY_is_a(second_owner.get(), "ED25519");
    study::require(second_remains_alive_result == 1, "second remains alive");

    std::cout << "REFERENCE OK after first.reset()\n";

    // 3. move는 참조 수를 늘리지 않고 소유권을 옮깁니다.
    auto new_owner = std::move(second_owner);
    study::require(!second_owner && bool(new_owner), "move ownership");

    std::cout << "MOVE OK; old owner empty\n";
    if (argc > 1) {
        throw std::runtime_error("intentional exception; remaining owner released by RAII");
    }
} catch (const std::exception& e) {

    return study::failed(e);
}
