// 실행: study-build examples/cpp/ocsp_verify.cpp revocation good good
// 두 번째 인자: 인증서 이름, 세 번째: DER 응답 이름(good/revoked/unknown/stale/future/no-next/badsig)
#include "revocation.hpp"

int main(int argc, char** argv) try {
    const std::string directory = argc > 1 ? argv[1] : "revocation";
    const std::string certificate_name = argc > 2 ? argv[2] : "good";
    const std::string response_name = argc > 3 ? argv[3] : "good";
    auto certificate = revocation::read_certificate(directory + "/" + certificate_name + ".pem");
    auto issuer = revocation::read_certificate(directory + "/ca.pem");
    auto store = revocation::trust_store(directory + "/ca.pem");

    // 인증서의 체인·이름·용도 검증은 OCSP 응답 검증과 별도입니다.
    const auto chain = revocation::verify_leaf(certificate.get(), store.get());
    std::cout << chain.detail << '\n';
    if (chain.code != 0) {
        return chain.code;
    }
    const auto bytes = revocation::read_der(directory + "/" + response_name + ".der");
    const auto result = revocation::verify_ocsp(
        bytes.data(), bytes.size(), certificate.get(), issuer.get(), store.get());
    std::cout << result.detail << '\n';
    if (result.code != 0) {
        std::cerr << study::errors();
    }
    return result.code;
} catch (const std::exception& error) {

    return study::failed(error);
}
