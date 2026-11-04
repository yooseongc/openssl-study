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
// Free functions have different return types (BIO_free returns int).
// A stateless deleter handles either kind; unique_ptr remains move-only.
template <class T, auto Free> struct Deleter {
    void operator()(T *p) const noexcept {
        if (p)
            (void)Free(p);
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
inline void require(bool success, const char *operation) {
    if (!success)
        throw std::runtime_error(std::string(operation) + "\n" + errors());
}
inline std::string hex(const unsigned char *data, size_t size) {
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (size_t i = 0; i < size; ++i)
        out << std::setw(2) << static_cast<unsigned>(data[i]);
    return out.str();
}
inline int failed(const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
}
} // namespace study
