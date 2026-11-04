// 첫 인자는 HKDF의 info입니다. 공백을 포함하는 값은 따옴표로 묶습니다.
// 실행: study-build examples/cpp/kdf.cpp 'client traffic'

#include "study.hpp"
#include <openssl/kdf.h>
#include <openssl/core_names.h>

int main(int argc, char **argv) try {
    std::string info = argc > 1 ? argv[1] : "client traffic";
    std::string key = "shared-secret-for-demo", salt = "public-salt";
    char digest[] = "SHA256";
    study::Handle<EVP_KDF, EVP_KDF_free> kdf(EVP_KDF_fetch(nullptr, "HKDF", nullptr));
    study::require(bool(kdf), "KDF fetch");
    study::Handle<EVP_KDF_CTX, EVP_KDF_CTX_free> ctx(EVP_KDF_CTX_new(kdf.get()));
    study::require(bool(ctx), "KDF context");
    // params는 원본 버퍼를 가리킵니다. derive가 끝날 때까지 key, salt, info의 저장 공간이 유효해야
    // 합니다.
    OSSL_PARAM params[] = {
        OSSL_PARAM_construct_utf8_string(OSSL_KDF_PARAM_DIGEST, digest, 0),
        OSSL_PARAM_construct_octet_string(OSSL_KDF_PARAM_KEY, key.data(), key.size()),
        OSSL_PARAM_construct_octet_string(OSSL_KDF_PARAM_SALT, salt.data(), salt.size()),
        OSSL_PARAM_construct_octet_string(OSSL_KDF_PARAM_INFO, info.data(), info.size()),
        OSSL_PARAM_construct_end()};
    std::array<unsigned char, 32> output{};
    study::require(EVP_KDF_derive(ctx.get(), output.data(), output.size(), params) == 1,
                   "HKDF derive");
    std::cout << study::hex(output.data(), output.size()) << '\n';
    // This illustrates domain separation, not TLS 1.3's complete HKDF-Expand-Label encoding.
} catch (const std::exception &e) {
    return study::failed(e);
}
