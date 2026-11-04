// 인자가 없으면 X25519 키 쌍으로 양쪽에서 같은 비밀을 계산합니다.
// 실행: study-build examples/cpp/kex.cpp

#include "study.hpp"

std::vector<unsigned char> derive(EVP_PKEY *private_key, EVP_PKEY *peer) {
    study::KeyCtx ctx(EVP_PKEY_CTX_new_from_pkey(nullptr, private_key, nullptr));
    study::require(bool(ctx), "derive context");
    study::require(EVP_PKEY_derive_init(ctx.get()) == 1, "derive init");
    study::require(EVP_PKEY_derive_set_peer(ctx.get(), peer) == 1, "set peer");
    // 출력을 nullptr로 주면 필요한 길이를 얻습니다. 두 번째 호출에서 그 크기의 버퍼에 비밀을
    // 기록합니다.
    size_t size = 0;
    study::require(EVP_PKEY_derive(ctx.get(), nullptr, &size) == 1, "query secret size");
    std::vector<unsigned char> secret(size);
    study::require(EVP_PKEY_derive(ctx.get(), secret.data(), &size) == 1, "derive secret");
    secret.resize(size);
    return secret;
}
study::Key public_only(EVP_PKEY *key) {
    std::array<unsigned char, 32> bytes{};
    size_t size = bytes.size();
    study::require(EVP_PKEY_get_raw_public_key(key, bytes.data(), &size) == 1, "export public key");
    study::Key result(
        EVP_PKEY_new_raw_public_key_ex(nullptr, "X25519", nullptr, bytes.data(), size));
    study::require(bool(result), "import public key");
    return result;
}
int main(int argc, char **argv) try {
    study::Key alice(EVP_PKEY_Q_keygen(nullptr, nullptr, "X25519")),
        bob(EVP_PKEY_Q_keygen(nullptr, nullptr, "X25519"));
    study::require(alice && bob, "keygen");
    auto apub = public_only(alice.get()), bpub = public_only(bob.get());
    if (argc > 1 && std::string(argv[1]) == "bad-peer") {
        study::Key wrong(EVP_PKEY_Q_keygen(nullptr, nullptr, "ED25519"));
        study::require(bool(wrong), "wrong keygen");
        (void)derive(alice.get(), wrong.get());
        return 3;
    }
    auto a = derive(alice.get(), bpub.get()), b = derive(bob.get(), apub.get());
    study::require(a == b, "shared secrets agree");
    std::cout << "SHARED SECRET MATCH; size=" << a.size() << "; peer identity NOT authenticated\n";
    OPENSSL_cleanse(a.data(), a.size());
    OPENSSL_cleanse(b.data(), b.size());
} catch (const std::exception &e) {
    return study::failed(e);
}
