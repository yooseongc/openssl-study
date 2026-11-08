// OCSP 파일 검증과 TLS Stapling 클라이언트가 공유하는 검증 순서입니다.
#pragma once
#include "study.hpp"
#include <openssl/ocsp.h>
#include <openssl/pem.h>
#include <openssl/x509v3.h>
#include <fstream>

namespace revocation {
using Store = study::Handle<X509_STORE, X509_STORE_free>;
using VerifyContext = study::Handle<X509_STORE_CTX, X509_STORE_CTX_free>;
using Response = study::Handle<OCSP_RESPONSE, OCSP_RESPONSE_free>;
using Basic = study::Handle<OCSP_BASICRESP, OCSP_BASICRESP_free>;
using CertId = study::Handle<OCSP_CERTID, OCSP_CERTID_free>;

// 이 종료 코드는 예제의 계약이며 OpenSSL API 반환값이 아닙니다.
struct Result {
    int code; // 0 good, 2 revoked, 3 unknown, 4 unavailable, 5 invalid, 1 처리 오류
    std::string detail;
};

inline study::Cert read_certificate(const std::string& path) {
    study::Bio input(BIO_new_file(path.c_str(), "r"));
    study::require(bool(input), "open certificate");
    study::Cert certificate(PEM_read_bio_X509(input.get(), nullptr, nullptr, nullptr));
    study::require(bool(certificate), "parse certificate");
    return certificate;
}

inline Store trust_store(const std::string& path) {
    Store store(X509_STORE_new());
    study::require(bool(store), "new trust store");
    study::require(X509_STORE_load_locations(store.get(), path.c_str(), nullptr) == 1, "load CA");
    return store;
}

inline Result verify_leaf(X509* leaf, X509_STORE* store) {
    VerifyContext context(X509_STORE_CTX_new());
    study::require(bool(context), "new verify context");
    study::require(X509_STORE_CTX_init(context.get(), store, leaf, nullptr) == 1, "verify init");
    auto* parameters = X509_STORE_CTX_get0_param(context.get()); // context 내부의 빌린 포인터
    study::require(X509_VERIFY_PARAM_set1_host(parameters, "localhost", 0) == 1, "hostname");
    study::require(X509_VERIFY_PARAM_set_purpose(parameters, X509_PURPOSE_SSL_SERVER) == 1,
                   "purpose");
    const int verified = X509_verify_cert(context.get());
    if (verified == 1) {
        return {0, "CHAIN + NAME + PURPOSE OK"};
    }
    const int error = X509_STORE_CTX_get_error(context.get());
    return {verified < 0 ? 1 : 5,
            std::string("CERTIFICATE REJECTED: ") + X509_verify_cert_error_string(error)};
}

inline std::vector<unsigned char> read_der(const std::string& path) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    study::require(bool(input), "open response file");
    const auto size = input.tellg();
    study::require(size > 0 && size <= 1024 * 1024, "response size 1..1048576");
    std::vector<unsigned char> bytes(static_cast<size_t>(size));
    input.seekg(0);
    input.read(reinterpret_cast<char*>(bytes.data()), size);
    study::require(bool(input), "read complete response");
    return bytes;
}

inline Result
verify_ocsp(const unsigned char* bytes, size_t size, X509* leaf, X509* issuer, X509_STORE* store) {
    if (!bytes || size == 0) {
        return {4, "UNAVAILABLE: no OCSP response"};
    }
    if (size > 1024 * 1024) {
        return {5, "INVALID: response too large"};
    }

    // 1. DER 파싱은 신뢰 검증이 아닙니다. 이동한 커서로 뒤에 남은 데이터도 거부합니다.
    const unsigned char* cursor = bytes;
    Response response(d2i_OCSP_RESPONSE(nullptr, &cursor, static_cast<long>(size)));
    if (!response || cursor != bytes + size) {
        return {5, "INVALID: malformed DER"};
    }
    if (OCSP_response_status(response.get()) != OCSP_RESPONSE_STATUS_SUCCESSFUL) {
        return {5, "INVALID: responder did not return successful response"};
    }
    Basic basic(OCSP_response_get1_basic(response.get()));
    if (!basic) {
        return {5, "INVALID: missing BasicOCSPResponse"};
    }

    // 2. 응답 서명과 서명자의 인증 경로·OCSP 권한을 확인합니다. 우회 flags는 0입니다.
    const int signature_verified = OCSP_basic_verify(basic.get(), nullptr, store, 0);
    if (signature_verified != 1) {
        return {signature_verified < 0 ? 1 : 5,
                "INVALID: response signature or signer authorization"};
    }

    // 3. serial만 비교하지 않습니다. 발급자의 이름·키 해시까지 포함한 CertID를 만듭니다.
    // SHA-1은 이 요청/응답의 식별 해시이며, 응답 자체는 별도 SHA-256 서명으로 보호합니다.
    CertId identifier(OCSP_cert_to_id(EVP_sha1(), leaf, issuer));
    study::require(bool(identifier), "certificate ID");
    int status = V_OCSP_CERTSTATUS_UNKNOWN;
    int reason = OCSP_REVOKED_STATUS_NOSTATUS;
    ASN1_GENERALIZEDTIME *revoked_at = nullptr, *this_update = nullptr, *next_update = nullptr;
    if (OCSP_resp_find_status(basic.get(),
                              identifier.get(),
                              &status,
                              &reason,
                              &revoked_at,
                              &this_update,
                              &next_update) != 1) {
        return {5, "INVALID: response is for a different certificate"};
    }

    // 4. 학습 정책: nextUpdate 필수, 시계 오차 30초, thisUpdate 최대 나이 3600초.
    // 시간 포인터들은 basic 내부 값을 빌린 것이므로 별도 해제하지 않습니다.
    if (!this_update || !next_update ||
        OCSP_check_validity(this_update, next_update, 30, 3600) != 1) {
        return {5, "INVALID: stale, future, or missing nextUpdate"};
    }
    if (status == V_OCSP_CERTSTATUS_REVOKED) {
        return {2, "REVOKED: reason=" + std::to_string(reason)};
    }
    if (status == V_OCSP_CERTSTATUS_UNKNOWN) {
        return {3, "UNKNOWN: responder has no status"};
    }
    if (status != V_OCSP_CERTSTATUS_GOOD) {
        return {5, "INVALID: unexpected certificate status"};
    }
    return {0, "GOOD: signature + signer + CertID + freshness verified"};
}
} // namespace revocation
