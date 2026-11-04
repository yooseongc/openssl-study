// 메시지나 검증 키를 바꾸면 Ed25519 서명이 어떻게 판정되는지 비교합니다.
// 실행: study-build examples/cpp/sign.cpp ok

#include "study.hpp"

int main(int argc, char **argv) try {
    const std::string mode = argc > 1 ? argv[1] : "ok";
    const std::string message = "hello openssl",
                      candidate = mode == "tamper" ? "changed message" : message;
    study::Key private_key(EVP_PKEY_Q_keygen(nullptr, nullptr, "ED25519"));
    study::require(bool(private_key), "keygen");
    std::array<unsigned char, 32> raw{};
    size_t raw_size = raw.size();
    study::require(EVP_PKEY_get_raw_public_key(private_key.get(), raw.data(), &raw_size) == 1,
                   "export public");
    study::Key pub(
        EVP_PKEY_new_raw_public_key_ex(nullptr, "ED25519", nullptr, raw.data(), raw_size));
    if (mode == "wrong-key")
        pub.reset(EVP_PKEY_Q_keygen(nullptr, nullptr, "ED25519"));
    study::MdCtx sign(EVP_MD_CTX_new()), verify(EVP_MD_CTX_new());
    study::require(pub && sign && verify, "allocate contexts");
    study::require(EVP_DigestSignInit_ex(sign.get(), nullptr, nullptr, nullptr, nullptr,
                                         private_key.get(), nullptr) == 1,
                   "sign init");
    size_t n = 0;
    const auto *data = reinterpret_cast<const unsigned char *>(message.data());
    study::require(EVP_DigestSign(sign.get(), nullptr, &n, data, message.size()) == 1,
                   "signature size");
    std::vector<unsigned char> signature(n);
    study::require(EVP_DigestSign(sign.get(), signature.data(), &n, data, message.size()) == 1,
                   "sign");
    study::require(EVP_DigestVerifyInit_ex(verify.get(), nullptr, nullptr, nullptr, nullptr,
                                           pub.get(), nullptr) == 1,
                   "verify init");
    // 검증 결과 1은 일치, 0은 서명 불일치입니다. 다른 오류는 별도 실패 경로로 전달합니다.
    const int ret = EVP_DigestVerify(verify.get(), signature.data(), n,
                                     reinterpret_cast<const unsigned char *>(candidate.data()),
                                     candidate.size());
    if (ret == 1) {
        std::cout << "signature VERIFIED (public key only in normal/tamper modes)\n";
        return 0;
    }
    if (ret == 0) {
        std::cout << "signature REJECTED\n";
        return 2;
    }
    study::require(false, "verify internal error");
} catch (const std::exception &e) {
    return study::failed(e);
}
