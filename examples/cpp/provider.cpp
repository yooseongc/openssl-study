// 첫 인자는 SHA256 구현을 선택할 때 적용할 속성 조건입니다.
// 실행: study-build examples/cpp/provider.cpp provider=default

#include "study.hpp"
#include <openssl/provider.h>

int main(int argc, char **argv) try {
    // Declaration order is deliberate: destruction reverses it (md, provider, context).
    study::Handle<OSSL_LIB_CTX, OSSL_LIB_CTX_free> libctx(OSSL_LIB_CTX_new());
    study::require(bool(libctx), "library context");
    study::Handle<OSSL_PROVIDER, OSSL_PROVIDER_unload> provider(
        OSSL_PROVIDER_load(libctx.get(), "default"));
    study::require(bool(provider), "provider load");
    study::Md md(EVP_MD_fetch(libctx.get(), "SHA256", argc > 1 ? argv[1] : "provider=default"));
    study::require(bool(md), "EVP_MD_fetch");
    // get0가 돌려준 포인터는 md가 제공하는 참조입니다. 여기서 소유권을 얻거나 unload하지 않습니다.
    const OSSL_PROVIDER *borrowed = EVP_MD_get0_provider(md.get());
    std::cout << "algorithm=" << EVP_MD_get0_name(md.get())
              << " provider=" << OSSL_PROVIDER_get0_name(borrowed) << '\n';
    // borrowed is not ours to unload or put in an owning unique_ptr.
} catch (const std::exception &e) {
    return study::failed(e);
}
