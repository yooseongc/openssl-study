// random은 난수를 출력하고, mac과 tamper는 두 번째 인자를 메시지로 사용합니다.
// 실행: study-build examples/cpp/random_mac.cpp random

#include "study.hpp"
#include <openssl/core_names.h>
#include <openssl/params.h>
#include <openssl/rand.h>

int main(int argc, char **argv) try {
    const std::string mode = argc > 1 ? argv[1] : "random";
    std::array<unsigned char, 32> random{};
    study::require(RAND_bytes_ex(nullptr, random.data(), random.size(), 0) == 1, "RAND_bytes_ex");
    if (mode == "random") {
        std::cout << "random=" << study::hex(random.data(), random.size()) << '\n';
        return 0;
    }
    // Deterministic public test key; never use this literal as an application secret.
    const std::string key = "study-only-key", message = argc > 2 ? argv[2] : "hello";
    study::Handle<EVP_MAC, EVP_MAC_free> mac(EVP_MAC_fetch(nullptr, "HMAC", nullptr));
    study::require(bool(mac), "EVP_MAC_fetch");
    study::Handle<EVP_MAC_CTX, EVP_MAC_CTX_free> ctx(EVP_MAC_CTX_new(mac.get()));
    study::require(bool(ctx), "EVP_MAC_CTX_new");
    char digest[] = "SHA256";
    OSSL_PARAM params[] = {OSSL_PARAM_construct_utf8_string(OSSL_MAC_PARAM_DIGEST, digest, 0),
                           OSSL_PARAM_construct_end()};
    study::require(EVP_MAC_init(ctx.get(), reinterpret_cast<const unsigned char *>(key.data()),
                                key.size(), params) == 1,
                   "MAC init");
    study::require(EVP_MAC_update(ctx.get(),
                                  reinterpret_cast<const unsigned char *>(message.data()),
                                  message.size()) == 1,
                   "MAC update");
    std::array<unsigned char, 32> tag{};
    size_t length = 0;
    study::require(EVP_MAC_final(ctx.get(), tag.data(), &length, tag.size()) == 1, "MAC final");
    std::cout << "hmac=" << study::hex(tag.data(), length) << '\n';
    // 같은 길이의 태그 두 개를 비교합니다. tamper에서는 받은 태그 한 비트만 바꿔 실패 경로를
    // 관찰합니다.
    auto received = tag;
    if (mode == "tamper")
        received[0] ^= 1;
    // Equal public lengths are established before CRYPTO_memcmp.
    if (CRYPTO_memcmp(tag.data(), received.data(), tag.size()) != 0) {
        std::cout << "MAC REJECTED\n";
        return 2;
    }
    std::cout << "MAC VERIFIED\n";
} catch (const std::exception &e) {
    return study::failed(e);
}
