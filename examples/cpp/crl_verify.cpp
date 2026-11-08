// 실행: study-build examples/cpp/crl_verify.cpp revocation good current
// 인증서: good|revoked|unknown, CRL: current|stale|missing
#include "revocation.hpp"

int main(int argc, char** argv) try {
    const std::string directory = argc > 1 ? argv[1] : "revocation";
    const std::string name = argc > 2 ? argv[2] : "good";
    const std::string mode = argc > 3 ? argv[3] : "current";
    study::require(mode == "current" || mode == "stale" || mode == "missing", "CRL mode");
    auto certificate = revocation::read_certificate(directory + "/" + name + ".pem");
    auto store = revocation::trust_store(directory + "/ca.pem");

    // CRL을 제공하지 않는 경우에도 검사 플래그는 유지하여 '확인 불가'를 관찰합니다.
    study::Handle<X509_CRL, X509_CRL_free> crl;
    if (mode != "missing") {
        const std::string file =
            directory + (mode == "stale" ? "/stale.crl.pem" : "/current.crl.pem");
        study::Bio input(BIO_new_file(file.c_str(), "r"));
        study::require(bool(input), "open CRL");
        crl.reset(PEM_read_bio_X509_CRL(input.get(), nullptr, nullptr, nullptr));
        study::require(bool(crl), "parse CRL");
        // store가 자기 참조를 얻습니다. 호출자는 원래 crl 참조를 계속 소유합니다.
        study::require(X509_STORE_add_crl(store.get(), crl.get()) == 1, "add CRL");
    }
    study::require(X509_STORE_set_flags(store.get(), X509_V_FLAG_CRL_CHECK) == 1,
                   "enable leaf CRL check");
    const auto result = revocation::verify_leaf(certificate.get(), store.get());
    std::cout << result.detail << '\n';
    return result.code;
} catch (const std::exception& error) {

    return study::failed(error);
}
