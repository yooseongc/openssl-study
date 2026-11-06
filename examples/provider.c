// 첫 인자로 provider 속성 조건을 지정합니다.
// 실행: study-build examples/provider.c provider=default

#include <stdio.h>
#include <openssl/evp.h>
#include <openssl/provider.h>
#include <openssl/err.h>

int main(int argc, char** argv) {
    const char* property = argc > 1 ? argv[1] : "provider=default";
    // 기본 종료 코드는 실패입니다. 모든 단계가 성공한 뒤에만 0으로 바꿉니다.
    int exit_code = 1;

    OSSL_LIB_CTX* library_context = OSSL_LIB_CTX_new();
    OSSL_PROVIDER* provider = NULL;
    EVP_MD* algorithm = NULL;
    if (!library_context) {
        goto end;
    }
    provider = OSSL_PROVIDER_load(library_context, "default");
    if (!provider) {
        goto end;
    }
    // libctx에 로드된 구현 중 property 조건을 만족하는 SHA256을 찾습니다. 성공한 md는 정리할 책임이
    // 있습니다.
    algorithm = EVP_MD_fetch(library_context, "SHA256", property);
    if (!algorithm) {
        goto end;
    }
    printf(
        "algorithm=%s provider=%s property=%s\n",
        EVP_MD_get0_name(algorithm),
        OSSL_PROVIDER_get0_name(EVP_MD_get0_provider(algorithm)),
        property
    );
    exit_code = 0;

// 실패한 위치와 관계없이 이미 생성한 자원을 역순으로 정리합니다.
end:
    if (exit_code) {
        ERR_print_errors_fp(stderr);
    }
    EVP_MD_free(algorithm);
    OSSL_PROVIDER_unload(provider);
    OSSL_LIB_CTX_free(library_context);
    return exit_code;
}
