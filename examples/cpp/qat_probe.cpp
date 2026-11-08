// 실행: study-build examples/cpp/qat_probe.cpp default
// 인자: default | qatprovider | missing. 77은 Provider를 사용할 수 없어 건너뜀입니다.
#include "study.hpp"
#include <openssl/provider.h>

int main(int argc, char** argv) try {
    const std::string name = argc > 1 ? argv[1] : "default";
    study::require(name == "default" || name == "qatprovider" || name == "missing",
                   "provider argument");

    // 1. 전역 설정에 영향을 주지 않는 컨텍스트에서 Provider를 명시적으로 로드합니다.
    study::Handle<OSSL_LIB_CTX, OSSL_LIB_CTX_free> library_context(OSSL_LIB_CTX_new());
    study::require(bool(library_context), "library context");
    study::Handle<OSSL_PROVIDER, OSSL_PROVIDER_unload> provider(
        OSSL_PROVIDER_load(library_context.get(), name.c_str()));
    if (!provider) {
        std::cout << "UNAVAILABLE provider=" << name << " (not an acceleration success)\n";
        std::cerr << study::errors();
        return 77;
    }

    // 2. 필수 속성 조건으로 다른 Provider의 암호 구현 선택을 막습니다.
    const std::string properties = "provider=" + name;
    study::Handle<EVP_CIPHER, EVP_CIPHER_free> cipher(
        EVP_CIPHER_fetch(library_context.get(), "AES-128-GCM", properties.c_str()));
    if (!cipher) {
        std::cout << "UNAVAILABLE cipher=AES-128-GCM query=" << properties << '\n';
        std::cerr << study::errors();
        return 77;
    }
    const OSSL_PROVIDER* selected = EVP_CIPHER_get0_provider(cipher.get());
    study::require(selected != nullptr, "selected provider");
    std::cout << "selected=" << OSSL_PROVIDER_get0_name(selected) << '\n';

    // 3. 공개된 고정 입력을 한 번 암호화합니다. 이 키·nonce는 테스트 전용입니다.
    std::array<unsigned char, 16> key{}, plaintext{}, ciphertext{}, tag{};
    std::array<unsigned char, 12> nonce{};
    std::array<unsigned char, 16> final_bytes{};
    study::Handle<EVP_CIPHER_CTX, EVP_CIPHER_CTX_free> context(EVP_CIPHER_CTX_new());
    study::require(bool(context), "cipher context");
    study::require(
        EVP_EncryptInit_ex2(context.get(), cipher.get(), key.data(), nonce.data(), nullptr) == 1,
        "encrypt init");
    int written = 0;
    study::require(
        EVP_EncryptUpdate(
            context.get(), ciphertext.data(), &written, plaintext.data(), plaintext.size()) == 1,
        "encrypt update");
    int final_length = 0;
    study::require(EVP_EncryptFinal_ex(context.get(), final_bytes.data(), &final_length) == 1,
                   "encrypt final");
    study::require(written == 16 && final_length == 0, "GCM output length");
    study::require(
        EVP_CIPHER_CTX_ctrl(context.get(), EVP_CTRL_GCM_GET_TAG, tag.size(), tag.data()) == 1,
        "get GCM tag");

    // 4. 결과 정확성과 Provider 선택은 확인하지만 HW/SW 내부 경로는 증명하지 않습니다.
    study::require(study::hex(ciphertext.data(), ciphertext.size()) ==
                       "0388dace60b6a392f328c2b971b2fe78",
                   "known ciphertext");
    study::require(study::hex(tag.data(), tag.size()) == "ab6e47d42cec13bdf53a67b21257bddf",
                   "known tag");
    std::cout << "PASS known-answer; hardware execution NOT established\n";
} catch (const std::exception& error) {

    return study::failed(error);
}
