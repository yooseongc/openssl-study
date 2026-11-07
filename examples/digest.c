// 첫 인자는 해시할 문자열입니다.
// 실행: study-build examples/digest.c abc

#include <stdio.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/err.h>

int main(int argc, char** argv) {
    const char* message = argc > 1 ? argv[1] : "hello openssl";

    // 기본 종료 코드는 실패입니다. 모든 단계가 성공한 뒤에만 0으로 바꿉니다.
    int exit_code = 1;

    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int digest_length = 0;

    /* fetch returns an owned implementation: release with EVP_MD_free. */
    EVP_MD* algorithm = EVP_MD_fetch(NULL, "SHA256", "provider=default");
    EVP_MD_CTX* digest_context = EVP_MD_CTX_new();
    if (!algorithm || !digest_context) {
        goto cleanup;
    }

    // Init → Update → Final 순서입니다. 실패하면 cleanup에서 이미 할당한 객체를 정리합니다.
    if (EVP_DigestInit_ex2(digest_context, algorithm, NULL) != 1 ||
        EVP_DigestUpdate(digest_context, message, strlen(message)) != 1 ||
        EVP_DigestFinal_ex(digest_context, digest, &digest_length) != 1) {
        goto cleanup;
    }
    for (unsigned int i = 0; i < digest_length; i++) {
        printf("%02x", digest[i]);
    }
    puts("");
    exit_code = 0;

// 중간 실패에서도 두 OpenSSL 객체를 모두 정리합니다.
cleanup:
    if (exit_code) {
        ERR_print_errors_fp(stderr);
    }
    EVP_MD_CTX_free(digest_context);
    EVP_MD_free(algorithm);
    return exit_code;
}
