// 인자가 없으면 X25519 키 쌍으로 양쪽에서 같은 비밀을 계산합니다.
// 실행: study-build examples/cpp/kex.cpp

#include "study.hpp"

std::vector<unsigned char> derive(EVP_PKEY* private_key, EVP_PKEY* peer) {
    study::KeyCtx derive_context(EVP_PKEY_CTX_new_from_pkey(nullptr, private_key, nullptr));
    study::require(bool(derive_context), "derive context");

    const int derive_init_result = EVP_PKEY_derive_init(derive_context.get());
    study::require(derive_init_result == 1, "derive init");

    const int set_peer_result = EVP_PKEY_derive_set_peer(derive_context.get(), peer);
    study::require(set_peer_result == 1, "set peer");

    // 출력을 nullptr로 주면 필요한 길이를 얻습니다. 두 번째 호출에서 그 크기의 버퍼에 비밀을
    // 기록합니다.
    size_t size = 0;
    const int query_secret_size_result = EVP_PKEY_derive(derive_context.get(), nullptr, &size);
    study::require(query_secret_size_result == 1, "query secret size");

    std::vector<unsigned char> secret(size);
    const int derive_secret_result = EVP_PKEY_derive(derive_context.get(), secret.data(), &size);
    study::require(derive_secret_result == 1, "derive secret");

    secret.resize(size);
    return secret;
}

study::Key public_only(EVP_PKEY* key) {
    std::array<unsigned char, 32> bytes{};
    size_t size = bytes.size();
    const int export_public_key_result = EVP_PKEY_get_raw_public_key(key, bytes.data(), &size);
    study::require(export_public_key_result == 1, "export public key");

    study::Key result(
        EVP_PKEY_new_raw_public_key_ex(nullptr, "X25519", nullptr, bytes.data(), size));
    study::require(bool(result), "import public key");

    return result;
}

int main(int argc, char** argv) try {
    // 1. 서로 독립된 키 쌍을 만들고 교환할 공개키만 분리합니다.
    study::Key alice_private_key(EVP_PKEY_Q_keygen(nullptr, nullptr, "X25519"));
    study::Key bob_private_key(EVP_PKEY_Q_keygen(nullptr, nullptr, "X25519"));
    study::require(alice_private_key && bob_private_key, "keygen");

    auto alice_public_key = public_only(alice_private_key.get());
    auto bob_public_key = public_only(bob_private_key.get());

    // 2. bad-peer는 키 타입이 맞지 않는 경우의 실패 경로입니다.
    if (argc > 1 && std::string(argv[1]) == "bad-peer") {
        study::Key incompatible_key(EVP_PKEY_Q_keygen(nullptr, nullptr, "ED25519"));
        study::require(bool(incompatible_key), "wrong keygen");

        (void)derive(alice_private_key.get(), incompatible_key.get());
        return 3;
    }

    // 3. 각자의 개인키와 상대 공개키로 같은 비밀을 얻는지 확인합니다.
    auto alice_secret = derive(alice_private_key.get(), bob_public_key.get());
    auto bob_secret = derive(bob_private_key.get(), alice_public_key.get());
    study::require(alice_secret == bob_secret, "shared secrets agree");

    std::cout << "SHARED SECRET MATCH; size=" << alice_secret.size()
              << "; peer identity NOT authenticated\n";
    OPENSSL_cleanse(alice_secret.data(), alice_secret.size());
    OPENSSL_cleanse(bob_secret.data(), bob_secret.size());
} catch (const std::exception& e) {

    return study::failed(e);
}
