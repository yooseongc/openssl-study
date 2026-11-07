// 순서대로 인증서 경로, 신뢰할 CA 경로, 기대하는 호스트 이름을 받습니다.
// 실행: study-build examples/cpp/x509.cpp

#include "study.hpp"
#include <openssl/pem.h>
#include <openssl/x509v3.h>

int main(int argc, char** argv) try {
    // 1. 인증서와 신뢰 CA, 기대 이름을 입력받습니다.
    const char* certificate_file = argc > 1 ? argv[1] : "/home/student/lab/tls/server.pem";
    const char* ca_file = argc > 2 ? argv[2] : "/home/student/lab/tls/ca.pem";
    const char* expected_hostname = argc > 3 ? argv[3] : "localhost";

    // 2. PEM을 파싱하고 Subject를 표시합니다. 이 단계는 신뢰 검증이 아닙니다.
    study::Bio input(BIO_new_file(certificate_file, "r"));
    study::require(bool(input), "open PEM");

    study::Cert certificate(PEM_read_bio_X509(input.get(), nullptr, nullptr, nullptr));
    study::require(bool(certificate), "parse X509");

    study::Bio output(BIO_new_fp(stdout, BIO_NOCLOSE));
    study::require(bool(output), "stdout BIO");

    // X509_get_subject_name returns a borrowed pointer; never free it separately.
    study::require(
        X509_NAME_print_ex(
            output.get(), X509_get_subject_name(certificate.get()), 0, XN_FLAG_RFC2253) >= 0,
        "print subject");
    std::cout << '\n';

    // store에는 신뢰할 CA를 넣고 ctx에는 이번 검증의 대상과 조건을 설정합니다. PEM 파싱 성공만으로
    // 신뢰가 결정되지는 않습니다.

    // 3. 신뢰 저장소와 이번 검증 상태를 준비합니다.
    study::Handle<X509_STORE, X509_STORE_free> store(X509_STORE_new());
    study::Handle<X509_STORE_CTX, X509_STORE_CTX_free> verify_context(X509_STORE_CTX_new());
    study::require(store && verify_context, "verification objects");

    const int load_trust_anchors_result = X509_STORE_load_locations(store.get(), ca_file, nullptr);
    study::require(load_trust_anchors_result == 1, "load trust anchors");

    const int verify_init_result =
        X509_STORE_CTX_init(verify_context.get(), store.get(), certificate.get(), nullptr);
    study::require(verify_init_result == 1, "verify init");

    // These inputs remain alive until verification finishes. Param is borrowed from ctx.
    X509_VERIFY_PARAM* verify_parameters = X509_STORE_CTX_get0_param(verify_context.get());
    const int set_hostname_result =
        X509_VERIFY_PARAM_set1_host(verify_parameters, expected_hostname, 0);
    study::require(set_hostname_result == 1, "set hostname");

    const int set_server_purpose_result =
        X509_VERIFY_PARAM_set_purpose(verify_parameters, X509_PURPOSE_SSL_SERVER);
    study::require(set_server_purpose_result == 1, "set server purpose");

    // 4. 체인·이름·용도 검증을 수행하고 실패 이유를 확인합니다.
    const int verify_result = X509_verify_cert(verify_context.get());
    if (verify_result == 1) {
        std::cout << "CHAIN + HOST + PURPOSE OK\n";
        return 0;
    }
    const int code = X509_STORE_CTX_get_error(verify_context.get());
    std::cerr << "VERIFY REJECTED code=" << code
              << " depth=" << X509_STORE_CTX_get_error_depth(verify_context.get())
              << " reason=" << X509_verify_cert_error_string(code) << '\n';
    return verify_result == 0 ? 2 : 1;
} catch (const std::exception& e) {

    return study::failed(e);
}
