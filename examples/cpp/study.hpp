// OpenSSL 포인터를 받으면 소유 여부부터 구분합니다. Handle은 소유한 참조 하나를 스코프 끝에서
// 해제합니다.
#pragma once
#include <openssl/crypto.h>
#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/ssl.h>
#include <array>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace study {
// 해제 함수의 반환형이 void 또는 int여도 사용할 수 있는 RAII 소유자입니다.
// get()은 빌린 포인터를 반환합니다. 직접 free하지 않습니다.
// 이동하면 소유권을 넘기며, 스코프를 벗어나면 해제 함수가 한 번 호출됩니다.
template <class T, auto Free> struct Deleter {
    void operator()(T* p) const noexcept {
        if (p) {
            (void)Free(p);
        }
    }
};
template <class T, auto Free> using Handle = std::unique_ptr<T, Deleter<T, Free>>;
using Md = Handle<EVP_MD, EVP_MD_free>;
using MdCtx = Handle<EVP_MD_CTX, EVP_MD_CTX_free>;
using Key = Handle<EVP_PKEY, EVP_PKEY_free>;
using KeyCtx = Handle<EVP_PKEY_CTX, EVP_PKEY_CTX_free>;
using SslCtx = Handle<SSL_CTX, SSL_CTX_free>;
using Ssl = Handle<SSL, SSL_free>;
using Bio = Handle<BIO, BIO_free>;
using Cert = Handle<X509, X509_free>;
inline std::string errors() {
    std::ostringstream out;
    for (unsigned long n; (n = ERR_get_error()) != 0;) {
        char text[256];
        ERR_error_string_n(n, text, sizeof text);
        out << text << '\n';
    }
    return out.str(); // Drains the current thread's error queue.
}
// 예제 공통 실패 처리: 호출자가 API별 성공 조건을 판단하여 전달합니다.
// 실패하면 현재 스레드의 오류 큐를 비우며 예외를 던집니다. 소유 객체는 RAII로 정리됩니다.
// SSL_ERROR_WANT_READ/WRITE 같은 재시도 상태에는 이 함수를 사용하지 않습니다.
inline void require(bool success, const char* operation) {
    if (!success) {
        throw std::runtime_error(std::string(operation) + "\n" + errors());
    }
}
inline std::string hex(const unsigned char* data, size_t size) {
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (size_t i = 0; i < size; ++i) {
        out << std::setw(2) << static_cast<unsigned>(data[i]);
    }
    return out.str();
}
inline int failed(const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
}
} // namespace study
