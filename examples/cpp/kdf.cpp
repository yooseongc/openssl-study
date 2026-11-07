// 첫 인자는 HKDF의 info입니다. 공백을 포함하는 값은 따옴표로 묶습니다.
// 실행: study-build examples/cpp/kdf.cpp 'client traffic'

#include "study.hpp"
#include <openssl/kdf.h>
#include <openssl/core_names.h>

int main(int argc, char** argv) try {
    // 1. 입력 비밀, salt, 용도를 구분하는 info를 준비합니다.
    std::string info = argc > 1 ? argv[1] : "client traffic";
    std::string input_secret = "shared-secret-for-demo", salt = "public-salt";
    char digest[] = "SHA256";

    // 2. HKDF 알고리즘과 실행 상태를 생성합니다.
    study::Handle<EVP_KDF, EVP_KDF_free> algorithm(EVP_KDF_fetch(nullptr, "HKDF", nullptr));
    study::require(bool(algorithm), "KDF fetch");

    study::Handle<EVP_KDF_CTX, EVP_KDF_CTX_free> derive_context(EVP_KDF_CTX_new(algorithm.get()));
    study::require(bool(derive_context), "KDF context");

    // params는 원본 버퍼를 가리킵니다. derive가 끝날 때까지 key, salt, info의 저장 공간이 유효해야
    // 합니다.
    OSSL_PARAM params[] = {
        OSSL_PARAM_construct_utf8_string(OSSL_KDF_PARAM_DIGEST, digest, 0),
        OSSL_PARAM_construct_octet_string(
            OSSL_KDF_PARAM_KEY, input_secret.data(), input_secret.size()),
        OSSL_PARAM_construct_octet_string(OSSL_KDF_PARAM_SALT, salt.data(), salt.size()),
        OSSL_PARAM_construct_octet_string(OSSL_KDF_PARAM_INFO, info.data(), info.size()),
        OSSL_PARAM_construct_end()};

    // 3. 요청한 길이만큼 키 재료를 유도하고 결과를 비교합니다.
    std::array<unsigned char, 32> derived_key{};
    const int hkdf_derive_result =
        EVP_KDF_derive(derive_context.get(), derived_key.data(), derived_key.size(), params);
    study::require(hkdf_derive_result == 1, "HKDF derive");

    std::cout << study::hex(derived_key.data(), derived_key.size()) << '\n';

    // This illustrates domain separation, not TLS 1.3's complete HKDF-Expand-Label encoding.
} catch (const std::exception& e) {

    return study::failed(e);
}
