// 첫 인자는 SHA256 구현을 선택할 때 적용할 속성 조건입니다.
// 실행: study-build examples/cpp/provider.cpp provider=default

#include "study.hpp"
#include <openssl/provider.h>

int main(int argc, char** argv) try {
    // Declaration order is deliberate: destruction reverses it (md, provider, context).

    // 1. 알고리즘 선택을 격리할 라이브러리 컨텍스트를 생성합니다.
    study::Handle<OSSL_LIB_CTX, OSSL_LIB_CTX_free> library_context(OSSL_LIB_CTX_new());
    study::require(bool(library_context), "library context");

    // 2. 사용할 구현을 제공하는 default Provider를 로드합니다.
    study::Handle<OSSL_PROVIDER, OSSL_PROVIDER_unload> provider(
        OSSL_PROVIDER_load(library_context.get(), "default"));
    study::require(bool(provider), "provider load");

    // 3. 속성 조건에 맞는 구현을 가져온 뒤 실제 공급자를 조회합니다.
    study::Md algorithm(
        EVP_MD_fetch(library_context.get(), "SHA256", argc > 1 ? argv[1] : "provider=default"));
    study::require(bool(algorithm), "EVP_MD_fetch");

    // get0가 돌려준 포인터는 md가 제공하는 참조입니다. 여기서 소유권을 얻거나 unload하지 않습니다.
    const OSSL_PROVIDER* algorithm_provider = EVP_MD_get0_provider(algorithm.get());
    std::cout << "algorithm=" << EVP_MD_get0_name(algorithm.get())
              << " provider=" << OSSL_PROVIDER_get0_name(algorithm_provider) << '\n';

    // borrowed is not ours to unload or put in an owning unique_ptr.
} catch (const std::exception& e) {

    return study::failed(e);
}
