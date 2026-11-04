// 원문과 변조된 메시지의 서명 검증 결과를 비교합니다.
// 실행: study-build examples/sign.c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/err.h>

int main(int argc, char **argv) {
    const unsigned char message[] = "hello openssl";
    const unsigned char changed[] = "hello attacker";
    const unsigned char *verify_message =
        argc > 1 && strcmp(argv[1], "tamper") == 0 ? changed : message;
    int rc = 1;
    size_t siglen = 0, publen = 32;
    unsigned char pub[32], *signature = NULL;
    EVP_PKEY *key = EVP_PKEY_Q_keygen(NULL, NULL, "ED25519");
    EVP_PKEY *public_key = NULL;
    EVP_MD_CTX *signctx = EVP_MD_CTX_new(), *verifyctx = EVP_MD_CTX_new();
    if (!key || !signctx || !verifyctx)
        goto end;
    /* Verification uses a separate object containing only the public key. */
    if (EVP_PKEY_get_raw_public_key(key, pub, &publen) != 1)
        goto end;
    public_key = EVP_PKEY_new_raw_public_key_ex(NULL, "ED25519", NULL, pub, publen);
    if (!public_key)
        goto end;
    /* Ed25519 uses one-shot signing, without a separate digest argument. */
    if (EVP_DigestSignInit(signctx, NULL, NULL, NULL, key) != 1 ||
        EVP_DigestSign(signctx, NULL, &siglen, message, sizeof(message) - 1) != 1)
        goto end;
    // 먼저 얻은 siglen 바이트를 할당하고 두 번째 호출에서 실제 서명을 씁니다.
    signature = malloc(siglen);
    if (!signature ||
        EVP_DigestSign(signctx, signature, &siglen, message, sizeof(message) - 1) != 1)
        goto end;
    if (EVP_DigestVerifyInit(verifyctx, NULL, NULL, NULL, public_key) != 1)
        goto end;
    int result = EVP_DigestVerify(verifyctx, signature, siglen, verify_message,
                                  strlen((const char *)verify_message));
    if (result == 1) {
        puts("signature VERIFIED (public key only)");
        rc = 0;
    } else if (result == 0) {
        puts("signature REJECTED: message changed");
        rc = 2;
    }
end:
    if (rc == 1)
        ERR_print_errors_fp(stderr);
    free(signature);
    EVP_MD_CTX_free(signctx);
    EVP_MD_CTX_free(verifyctx);
    EVP_PKEY_free(public_key);
    EVP_PKEY_free(key);
    return rc;
}
