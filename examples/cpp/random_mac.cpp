// random은 난수를 출력하고, mac과 tamper는 두 번째 인자를 메시지로 사용합니다.
// 실행: study-build examples/cpp/random_mac.cpp random

#include "study.hpp"
#include <openssl/core_names.h>
#include <openssl/params.h>
#include <openssl/rand.h>

int main(int argc, char** argv) try {
    const std::string operation = argc > 1 ? argv[1] : "random";

    // 1. 난수를 생성하고 random 모드면 바로 출력합니다.
    std::array<unsigned char, 32> random_bytes{};
    const int rand_bytes_ex_result =
        RAND_bytes_ex(nullptr, random_bytes.data(), random_bytes.size(), 0);
    study::require(rand_bytes_ex_result == 1, "RAND_bytes_ex");
    if (operation == "random") {
        std::cout << "random=" << study::hex(random_bytes.data(), random_bytes.size()) << '\n';
        return 0;
    }
    // Deterministic public test key; never use this literal as an application secret.

    // 2. HMAC 계산에 사용할 비밀키와 메시지를 준비합니다.
    const std::string key = "study-only-key", message = argc > 2 ? argv[2] : "hello";
    study::Handle<EVP_MAC, EVP_MAC_free> algorithm(EVP_MAC_fetch(nullptr, "HMAC", nullptr));
    study::require(bool(algorithm), "EVP_MAC_fetch");
    study::Handle<EVP_MAC_CTX, EVP_MAC_CTX_free> mac_context(EVP_MAC_CTX_new(algorithm.get()));
    study::require(bool(mac_context), "EVP_MAC_CTX_new");

    // 3. HMAC 내부 해시를 설정한 뒤 메시지를 넣고 태그를 계산합니다.
    char digest[] = "SHA256";
    OSSL_PARAM params[] = {
        OSSL_PARAM_construct_utf8_string(OSSL_MAC_PARAM_DIGEST, digest, 0),
        OSSL_PARAM_construct_end()};
    const int mac_init_result = EVP_MAC_init(
        mac_context.get(), reinterpret_cast<const unsigned char*>(key.data()), key.size(), params
    );
    study::require(mac_init_result == 1, "MAC init");
    const int mac_update_result = EVP_MAC_update(
        mac_context.get(), reinterpret_cast<const unsigned char*>(message.data()), message.size()
    );
    study::require(mac_update_result == 1, "MAC update");
    std::array<unsigned char, 32> tag{};
    size_t tag_length = 0;
    const int mac_final_result =
        EVP_MAC_final(mac_context.get(), tag.data(), &tag_length, tag.size());
    study::require(mac_final_result == 1, "MAC final");
    std::cout << "hmac=" << study::hex(tag.data(), tag_length) << '\n';
    // 같은 길이의 태그 두 개를 비교합니다. tamper에서는 받은 태그 한 비트만 바꿔 실패 경로를
    // 관찰합니다.

    // 4. 받은 태그와 계산한 태그를 비교합니다.
    auto received = tag;
    if (operation == "tamper") {
        received[0] ^= 1;
    }
    // Equal public lengths are established before CRYPTO_memcmp.
    if (CRYPTO_memcmp(tag.data(), received.data(), tag.size()) != 0) {
        std::cout << "MAC REJECTED\n";
        return 2;
    }
    std::cout << "MAC VERIFIED\n";
} catch (const std::exception& e) {
    return study::failed(e);
}
