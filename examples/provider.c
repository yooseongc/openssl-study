// 첫 인자로 provider 속성 조건을 지정합니다.
// 실행: study-build examples/provider.c provider=default

#include <stdio.h>
#include <openssl/evp.h>
#include <openssl/provider.h>
#include <openssl/err.h>

int main(int argc, char **argv) {
    const char *property = argc > 1 ? argv[1] : "provider=default";
    int rc = 1;
    OSSL_LIB_CTX *libctx = OSSL_LIB_CTX_new();
    OSSL_PROVIDER *provider = NULL;
    EVP_MD *md = NULL;
    if (!libctx)
        goto end;
    provider = OSSL_PROVIDER_load(libctx, "default");
    if (!provider)
        goto end;
    // libctx에 로드된 구현 중 property 조건을 만족하는 SHA256을 찾습니다. 성공한 md는 정리할 책임이
    // 있습니다.
    md = EVP_MD_fetch(libctx, "SHA256", property);
    if (!md)
        goto end;
    printf("algorithm=%s provider=%s property=%s\n", EVP_MD_get0_name(md),
           OSSL_PROVIDER_get0_name(EVP_MD_get0_provider(md)), property);
    rc = 0;
end:
    if (rc)
        ERR_print_errors_fp(stderr);
    EVP_MD_free(md);
    OSSL_PROVIDER_unload(provider);
    OSSL_LIB_CTX_free(libctx);
    return rc;
}
