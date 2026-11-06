// 같은 키로 암호화·복호화한 뒤 지정한 부분의 한 비트를 뒤집어 인증을 시험합니다.
// 실행: study-build examples/cpp/aead.cpp ok

#include "study.hpp"
#include <openssl/rand.h>

int main(int argc, char** argv) try {
    // 1. 실험 입력과 키를 준비합니다. 같은 키에서 nonce를 재사용하지 않습니다.
    const std::string scenario = argc > 1 ? argv[1] : "ok";
    const std::string plaintext = "authenticated message";
    std::string aad = "record-header";
    std::array<unsigned char, 32> key{};
    std::array<unsigned char, 12> nonce{};
    std::array<unsigned char, 16> tag{};
    const int random_key_result = RAND_priv_bytes(key.data(), key.size());
    study::require(random_key_result == 1, "random key");
    const int random_nonce_result = RAND_bytes(nonce.data(), nonce.size());
    study::require(random_nonce_result == 1, "random nonce");

    // 2. 알고리즘 구현과 암호화·복호화의 독립된 상태를 준비합니다.
    study::Handle<EVP_CIPHER, EVP_CIPHER_free> algorithm(
        EVP_CIPHER_fetch(nullptr, "AES-256-GCM", nullptr)
    );
    study::Handle<EVP_CIPHER_CTX, EVP_CIPHER_CTX_free> encrypt_context(EVP_CIPHER_CTX_new());
    study::Handle<EVP_CIPHER_CTX, EVP_CIPHER_CTX_free> decrypt_context(EVP_CIPHER_CTX_new());
    study::require(algorithm && encrypt_context && decrypt_context, "cipher/context allocation");
    std::vector<unsigned char> ciphertext(plaintext.size() + 16);
    std::vector<unsigned char> plaintext_candidate(ciphertext.size());
    int bytes_written = 0;
    int ciphertext_length = 0;

    // 3. 암호화를 시작하고 AAD, 평문 순서로 처리합니다.
    const int encrypt_init_result = EVP_EncryptInit_ex2(
        encrypt_context.get(), algorithm.get(), key.data(), nonce.data(), nullptr
    );
    study::require(encrypt_init_result == 1, "encrypt init");
    // 출력 포인터가 nullptr인 첫 Update는 AAD를 인증에만 포함합니다. 다음 Update가 평문을
    // 암호문으로 바꿉니다.
    const int encrypt_aad_result = EVP_EncryptUpdate(
        encrypt_context.get(),
        nullptr,
        &bytes_written,
        reinterpret_cast<const unsigned char*>(aad.data()),
        aad.size()
    );
    study::require(encrypt_aad_result == 1, "encrypt AAD");
    const int encrypt_data_result = EVP_EncryptUpdate(
        encrypt_context.get(),
        ciphertext.data(),
        &bytes_written,
        reinterpret_cast<const unsigned char*>(plaintext.data()),
        plaintext.size()
    );
    study::require(encrypt_data_result == 1, "encrypt data");
    ciphertext_length = bytes_written;
    const int encrypt_final_result = EVP_EncryptFinal_ex(
        encrypt_context.get(), ciphertext.data() + ciphertext_length, &bytes_written
    );
    study::require(encrypt_final_result == 1, "encrypt final");
    ciphertext_length += bytes_written;
    const int get_tag_result =
        EVP_CIPHER_CTX_ctrl(encrypt_context.get(), EVP_CTRL_AEAD_GET_TAG, tag.size(), tag.data());
    study::require(get_tag_result == 1, "get tag");

    // 4. 선택한 입력만 변조하여 인증 실패를 재현합니다.
    if (scenario == "tag") {
        tag[0] ^= 1;
    }
    if (scenario == "ciphertext") {
        ciphertext[0] ^= 1;
    }
    if (scenario == "aad") {
        aad[0] ^= 1;
    }

    // 5. 같은 키와 nonce로 복호화하고 받은 태그를 검증합니다.
    const int decrypt_init_result = EVP_DecryptInit_ex2(
        decrypt_context.get(), algorithm.get(), key.data(), nonce.data(), nullptr
    );
    study::require(decrypt_init_result == 1, "decrypt init");
    const int decrypt_aad_result = EVP_DecryptUpdate(
        decrypt_context.get(),
        nullptr,
        &bytes_written,
        reinterpret_cast<const unsigned char*>(aad.data()),
        aad.size()
    );
    study::require(decrypt_aad_result == 1, "decrypt AAD");
    const int decrypt_data_result = EVP_DecryptUpdate(
        decrypt_context.get(),
        plaintext_candidate.data(),
        &bytes_written,
        ciphertext.data(),
        ciphertext_length
    );
    study::require(decrypt_data_result == 1, "decrypt data");
    const int candidate_length = bytes_written;
    const int set_expected_tag_result =
        EVP_CIPHER_CTX_ctrl(decrypt_context.get(), EVP_CTRL_AEAD_SET_TAG, tag.size(), tag.data());
    study::require(set_expected_tag_result == 1, "set expected tag");
    // GCM의 Final에서 태그 검증에 성공하기 전까지 후보 평문을 출력하거나 사용하지 않습니다.
    if (EVP_DecryptFinal_ex(
            decrypt_context.get(), plaintext_candidate.data() + candidate_length, &bytes_written
        ) != 1) {
        OPENSSL_cleanse(plaintext_candidate.data(), plaintext_candidate.size());
        std::cout << "AUTH REJECTED; candidate plaintext discarded\n";
        return 2;
    }

    // 6. 인증을 통과한 평문만 애플리케이션에 전달합니다.
    std::cout << "AUTH OK: "
              << std::string(
                     reinterpret_cast<char*>(plaintext_candidate.data()),
                     candidate_length + bytes_written
                 )
              << '\n';
} catch (const std::exception& e) {
    return study::failed(e);
}
