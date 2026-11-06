// 원문과 변조된 메시지의 서명 검증 결과를 비교합니다.
// 실행: study-build examples/sign.c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/err.h>

int main(int argc, char** argv) {
    const unsigned char message[] = "hello openssl";
    const unsigned char changed[] = "hello attacker";
    const unsigned char* verify_message =
        argc > 1 && strcmp(argv[1], "tamper") == 0 ? changed : message;
    // 기본 종료 코드는 실패입니다. 모든 단계가 성공한 뒤에만 0으로 바꿉니다.
    int exit_code = 1;

    size_t signature_length = 0, public_key_length = 32;
    unsigned char public_key_bytes[32], *signature = NULL;
    EVP_PKEY* key = EVP_PKEY_Q_keygen(NULL, NULL, "ED25519");
    EVP_PKEY* public_key = NULL;
    EVP_MD_CTX *sign_context = EVP_MD_CTX_new(), *verify_context = EVP_MD_CTX_new();
    if (!key || !sign_context || !verify_context) {
        goto end;
    }
    /* Verification uses a separate object containing only the public key. */
    if (EVP_PKEY_get_raw_public_key(key, public_key_bytes, &public_key_length) != 1) {
        goto end;
    }
    public_key =
        EVP_PKEY_new_raw_public_key_ex(NULL, "ED25519", NULL, public_key_bytes, public_key_length);
    if (!public_key) {
        goto end;
    }
    /* Ed25519 uses one-shot signing, without a separate digest argument. */
    if (EVP_DigestSignInit(sign_context, NULL, NULL, NULL, key) != 1 ||
        EVP_DigestSign(sign_context, NULL, &signature_length, message, sizeof(message) - 1) != 1) {
        goto end;
    }
    // 먼저 얻은 siglen 바이트를 할당하고 두 번째 호출에서 실제 서명을 씁니다.
    signature = malloc(signature_length);
    if (!signature ||
        EVP_DigestSign(sign_context, signature, &signature_length, message, sizeof(message) - 1) !=
            1) {
        goto end;
    }
    if (EVP_DigestVerifyInit(verify_context, NULL, NULL, NULL, public_key) != 1) {
        goto end;
    }
    int result = EVP_DigestVerify(
        verify_context,
        signature,
        signature_length,
        verify_message,
        strlen((const char*)verify_message)
    );
    if (result == 1) {
        puts("signature VERIFIED (public key only)");
        exit_code = 0;
    } else if (result == 0) {
        puts("signature REJECTED: message changed");
        exit_code = 2;
    }

// 실패한 위치와 관계없이 이미 생성한 자원을 역순으로 정리합니다.
end:
    if (exit_code == 1) {
        ERR_print_errors_fp(stderr);
    }
    free(signature);
    EVP_MD_CTX_free(sign_context);
    EVP_MD_CTX_free(verify_context);
    EVP_PKEY_free(public_key);
    EVP_PKEY_free(key);
    return exit_code;
}
