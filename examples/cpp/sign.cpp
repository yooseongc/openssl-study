// 메시지나 검증 키를 바꾸면 Ed25519 서명이 어떻게 판정되는지 비교합니다.
// 실행: study-build examples/cpp/sign.cpp ok

#include "study.hpp"

int main(int argc, char** argv) try {
    // 1. 서명할 원문과 검증할 수신 메시지를 준비합니다.
    const std::string scenario = argc > 1 ? argv[1] : "ok";
    const std::string message = "hello openssl";
    const std::string received_message = scenario == "tamper" ? "changed message" : message;

    // 2. 서명용 개인키와 검증용 공개키를 분리합니다.
    study::Key private_key(EVP_PKEY_Q_keygen(nullptr, nullptr, "ED25519"));
    study::require(bool(private_key), "keygen");
    std::array<unsigned char, 32> public_key_bytes{};
    size_t public_key_length = public_key_bytes.size();
    const int export_public_result =
        EVP_PKEY_get_raw_public_key(private_key.get(), public_key_bytes.data(), &public_key_length);
    study::require(export_public_result == 1, "export public");
    study::Key public_key(EVP_PKEY_new_raw_public_key_ex(
        nullptr, "ED25519", nullptr, public_key_bytes.data(), public_key_length
    ));
    if (scenario == "wrong-key") {
        public_key.reset(EVP_PKEY_Q_keygen(nullptr, nullptr, "ED25519"));
    }

    // 3. Ed25519 서명은 해시 이름 없이 초기화하고 메시지 전체를 전달합니다.
    study::MdCtx sign_context(EVP_MD_CTX_new());
    study::MdCtx verify_context(EVP_MD_CTX_new());
    study::require(public_key && sign_context && verify_context, "allocate contexts");
    const int sign_init_result = EVP_DigestSignInit_ex(
        sign_context.get(), nullptr, nullptr, nullptr, nullptr, private_key.get(), nullptr
    );
    study::require(sign_init_result == 1, "sign init");
    size_t signature_length = 0;
    const auto* data = reinterpret_cast<const unsigned char*>(message.data());
    const int signature_size_result =
        EVP_DigestSign(sign_context.get(), nullptr, &signature_length, data, message.size());
    study::require(signature_size_result == 1, "signature size");
    std::vector<unsigned char> signature(signature_length);
    const int sign_result = EVP_DigestSign(
        sign_context.get(), signature.data(), &signature_length, data, message.size()
    );
    study::require(sign_result == 1, "sign");

    // 4. 검증을 준비하고 일치·불일치·오류를 구분합니다.
    const int verify_init_result = EVP_DigestVerifyInit_ex(
        verify_context.get(), nullptr, nullptr, nullptr, nullptr, public_key.get(), nullptr
    );
    study::require(verify_init_result == 1, "verify init");
    // 검증 결과 1은 일치, 0은 서명 불일치입니다. 다른 오류는 별도 실패 경로로 전달합니다.
    const int verify_result = EVP_DigestVerify(
        verify_context.get(),
        signature.data(),
        signature_length,
        reinterpret_cast<const unsigned char*>(received_message.data()),
        received_message.size()
    );
    if (verify_result == 1) {
        std::cout << "signature VERIFIED (public key only in normal/tamper modes)\n";
        return 0;
    }
    if (verify_result == 0) {
        std::cout << "signature REJECTED\n";
        return 2;
    }
    study::require(false, "verify internal error");
} catch (const std::exception& e) {
    return study::failed(e);
}
