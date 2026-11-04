// 첫 인자는 해시할 문자열입니다.
// 실행: study-build examples/digest.c abc

#include <stdio.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/err.h>

int main(int argc, char **argv) {
    const char *message = argc > 1 ? argv[1] : "hello openssl";
    int rc = 1;
    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int length = 0;
    /* fetch returns an owned implementation: release with EVP_MD_free. */
    EVP_MD *sha256 = EVP_MD_fetch(NULL, "SHA256", "provider=default");
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    if (!sha256 || !ctx)
        goto cleanup;
    // Init → Update → Final 순서입니다. 실패하면 cleanup에서 이미 할당한 객체를 정리합니다.
    if (EVP_DigestInit_ex2(ctx, sha256, NULL) != 1 ||
        EVP_DigestUpdate(ctx, message, strlen(message)) != 1 ||
        EVP_DigestFinal_ex(ctx, digest, &length) != 1)
        goto cleanup;
    for (unsigned int i = 0; i < length; i++)
        printf("%02x", digest[i]);
    puts("");
    rc = 0;
cleanup:
    if (rc)
        ERR_print_errors_fp(stderr);
    EVP_MD_CTX_free(ctx);
    EVP_MD_free(sha256);
    return rc;
}
