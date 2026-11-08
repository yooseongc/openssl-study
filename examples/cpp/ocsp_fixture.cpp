// 실습 전용: 서명이 올바르지만 시간 조건이 잘못된 OCSP 응답을 생성합니다.
// 실행: study-build examples/cpp/ocsp_fixture.cpp revocation stale
#include "revocation.hpp"
#include <ctime>

int main(int argc, char** argv) try {
    const std::string directory = argc > 1 ? argv[1] : "revocation";
    const std::string mode = argc > 2 ? argv[2] : "stale";
    study::require(mode == "stale" || mode == "future" || mode == "no-next", "fixture mode");
    auto leaf = revocation::read_certificate(directory + "/good.pem");
    auto issuer = revocation::read_certificate(directory + "/ca.pem");
    auto signer = revocation::read_certificate(directory + "/responder.pem");
    study::Bio input(BIO_new_file((directory + "/responder.key").c_str(), "r"));
    study::require(bool(input), "signer key file");
    study::Key key(PEM_read_bio_PrivateKey(input.get(), nullptr, nullptr, nullptr));
    study::require(bool(key), "signer key");
    revocation::Basic basic(OCSP_BASICRESP_new());
    revocation::CertId identifier(OCSP_cert_to_id(EVP_sha1(), leaf.get(), issuer.get()));
    study::require(basic && identifier, "response objects");

    const std::time_t now = std::time(nullptr);
    const int start = mode == "stale" ? -7200 : mode == "future" ? 7200 : -60;
    const int end = mode == "stale" ? -3600 : 10800;
    study::Handle<ASN1_TIME, ASN1_TIME_free> this_update(ASN1_TIME_adj(nullptr, now, 0, start));
    study::Handle<ASN1_TIME, ASN1_TIME_free> next_update(ASN1_TIME_adj(nullptr, now, 0, end));
    study::require(this_update && next_update, "time values");
    study::require(OCSP_basic_add1_status(basic.get(),
                                          identifier.get(),
                                          V_OCSP_CERTSTATUS_GOOD,
                                          0,
                                          nullptr,
                                          this_update.get(),
                                          mode == "no-next" ? nullptr : next_update.get()) !=
                       nullptr,
                   "add certificate status");
    study::require(
        OCSP_basic_sign(basic.get(), signer.get(), key.get(), EVP_sha256(), nullptr, 0) == 1,
        "sign test response");
    revocation::Response response(
        OCSP_response_create(OCSP_RESPONSE_STATUS_SUCCESSFUL, basic.get()));
    study::require(bool(response), "wrap response");
    study::Bio output(BIO_new_file((directory + "/" + mode + ".der").c_str(), "wb"));
    study::require(bool(output), "output fixture");
    study::require(i2d_OCSP_RESPONSE_bio(output.get(), response.get()) == 1, "write DER");
    std::cout << "signed test fixture=" << mode << " (system clock unchanged)\n";
} catch (const std::exception& error) {

    return study::failed(error);
}
