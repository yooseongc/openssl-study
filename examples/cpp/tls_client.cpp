// 연결 방식, 검증할 이름, CA 경로, 포트 순서입니다. TCP 대상은 루프백입니다.
// 실행: study-build examples/cpp/tls_client.cpp blocking localhost

#include "study.hpp"
#include <arpa/inet.h>
#include <cerrno>
#include <chrono>
#include <csignal>
#include <cstring>
#include <fcntl.h>
#include <sys/epoll.h>
#include <sys/socket.h>
#include <unistd.h>

struct Fd {
    int value;
    explicit Fd(int n) : value(n) {
        study::require(n >= 0, "file descriptor allocation");
    }
    ~Fd() {
        ::close(value);
    }
    Fd(const Fd &) = delete;
    Fd &operator=(const Fd &) = delete;
};
int main(int argc, char **argv) try {
    std::signal(SIGPIPE, SIG_IGN);
    const bool nonblock = argc > 1 && std::string(argv[1]) == "nonblock";
    const char *host = argc > 2 ? argv[2] : "localhost";
    const char *ca = argc > 3 ? argv[3] : "/home/student/lab/tls/ca.pem";
    const int port = argc > 4 ? std::stoi(argv[4]) : 4433;
    study::SslCtx ctx(SSL_CTX_new(TLS_client_method()));
    study::require(bool(ctx), "SSL_CTX_new");
    study::require(SSL_CTX_set_min_proto_version(ctx.get(), TLS1_3_VERSION) == 1,
                   "minimum version");
    SSL_CTX_set_verify(ctx.get(), SSL_VERIFY_PEER, nullptr); // void API; no return to check.
    study::require(SSL_CTX_load_verify_locations(ctx.get(), ca, nullptr) == 1, "CA loading");
    Fd fd(::socket(AF_INET, SOCK_STREAM, 0)), ep(::epoll_create1(EPOLL_CLOEXEC));
    if (nonblock)
        study::require(::fcntl(fd.value, F_SETFL, O_NONBLOCK) == 0, "nonblocking socket");
    else {
        const timeval limit{5, 0};
        study::require(::setsockopt(fd.value, SOL_SOCKET, SO_RCVTIMEO, &limit, sizeof limit) == 0,
                       "read timeout");
        study::require(::setsockopt(fd.value, SOL_SOCKET, SO_SNDTIMEO, &limit, sizeof limit) == 0,
                       "write timeout");
    }
    epoll_event event{};
    event.events = EPOLLIN | EPOLLOUT;
    event.data.fd = fd.value;
    study::require(::epoll_ctl(ep.value, EPOLL_CTL_ADD, fd.value, &event) == 0, "epoll add");
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(8);
    auto wait_ready = [&](int error) {
        event.events =
            (error == SSL_ERROR_WANT_READ ? EPOLLIN : EPOLLOUT); // Level-triggered for this lesson.
        study::require(::epoll_ctl(ep.value, EPOLL_CTL_MOD, fd.value, &event) == 0, "epoll modify");
        for (;;) {
            const auto remaining = std::chrono::duration_cast<std::chrono::milliseconds>(
                                       deadline - std::chrono::steady_clock::now())
                                       .count();
            if (remaining <= 0)
                throw std::runtime_error("deadline exceeded");
            const int n = ::epoll_wait(ep.value, &event, 1, static_cast<int>(remaining));
            if (n < 0 && errno == EINTR)
                continue;
            if (n <= 0)
                throw std::runtime_error("epoll deadline/error");
            return; // HUP/ERR also wake us; next SSL call decides the TLS outcome.
        }
    };
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(static_cast<uint16_t>(port));
    study::require(::inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr) == 1, "address");
    if (::connect(fd.value, reinterpret_cast<sockaddr *>(&addr), sizeof addr) != 0) {
        if (!nonblock || errno != EINPROGRESS)
            throw std::runtime_error("TCP connect failed");
        wait_ready(SSL_ERROR_WANT_WRITE);
        int socket_error = 0;
        socklen_t size = sizeof socket_error;
        study::require(::getsockopt(fd.value, SOL_SOCKET, SO_ERROR, &socket_error, &size) == 0 &&
                           socket_error == 0,
                       "TCP connect completion");
    }
    study::Ssl ssl(SSL_new(ctx.get()));
    study::require(bool(ssl), "SSL_new");
    study::require(SSL_set_fd(ssl.get(), fd.value) == 1,
                   "SSL_set_fd"); // socket remains owned by Fd.
    study::require(SSL_set_tlsext_host_name(ssl.get(), host) == 1, "SNI");
    study::require(SSL_set1_host(ssl.get(), host) == 1, "hostname verification");
    // WANT_READ와 WANT_WRITE는 다음에 기다릴 소켓 이벤트입니다. 준비 알림이 오면 중단됐던 SSL
    // 호출을 다시 수행합니다.
    auto retry = [&](int error, const char *operation) {
        if (nonblock && (error == SSL_ERROR_WANT_READ || error == SSL_ERROR_WANT_WRITE)) {
            std::cout << operation << ": "
                      << (error == SSL_ERROR_WANT_READ ? "WANT_READ" : "WANT_WRITE")
                      << " -> epoll\n";
            wait_ready(error);
            return;
        }
        throw std::runtime_error(std::string(operation) + " SSL_get_error=" +
                                 std::to_string(error) + "\n" + study::errors());
    };
    for (;;) {
        ERR_clear_error();
        const int ret = SSL_connect(ssl.get());
        if (ret == 1)
            break;
        const int error =
            SSL_get_error(ssl.get(), ret); // Same thread, immediately, before logging/freeing.
        retry(error, "handshake");
    }
    study::require(SSL_get_verify_result(ssl.get()) == X509_V_OK, "verified chain");
    study::Cert peer(SSL_get1_peer_certificate(ssl.get()));
    study::require(bool(peer), "peer certificate");
    std::cout << "Verified TLS: " << SSL_get_version(ssl.get()) << " / "
              << SSL_get_cipher_name(ssl.get()) << '\n';
    const std::string request = "GET / HTTP/1.0\r\nHost: localhost\r\n\r\n";
    size_t offset = 0;
    while (offset < request.size()) {
        size_t written = 0;
        ERR_clear_error();
        const int ret =
            SSL_write_ex(ssl.get(), request.data() + offset, request.size() - offset, &written);
        if (ret == 1) {
            offset += written;
            continue;
        }
        const int error = SSL_get_error(ssl.get(), ret);
        // On WANT, offset and the original buffer/length stay unchanged until retry succeeds.
        retry(error, "write");
    }
    std::string response;
    std::array<char, 2048> buffer{};
    for (;;) {
        size_t received = 0;
        ERR_clear_error();
        const int ret = SSL_read_ex(ssl.get(), buffer.data(), buffer.size(), &received);
        if (ret == 1) {
            response.append(buffer.data(), received);
            if (response.size() > 1024 * 1024)
                throw std::runtime_error("response limit exceeded");
            continue;
        }
        const int error = SSL_get_error(ssl.get(), ret);
        if (error == SSL_ERROR_ZERO_RETURN) {
            std::cout << "peer close_notify received\n";
            break;
        }
        retry(error,
              "read"); // Unexpected transport EOF is a failure; do not treat it as close_notify.
    }
    for (;;) {
        ERR_clear_error();
        const int ret = SSL_shutdown(ssl.get());
        if (ret == 1) {
            std::cout << "shutdown complete\n";
            break;
        }
        if (ret == 0) {
            std::cout << "close_notify sent; waiting for peer\n";
            if (nonblock)
                wait_ready(SSL_ERROR_WANT_READ);
            continue;
        }
        const int error = SSL_get_error(ssl.get(), ret);
        retry(error, "shutdown");
    }
    std::cout << response.substr(0, response.find('\n'))
              << "\napplication bytes=" << response.size() << '\n';
    // Destruction: peer -> SSL -> epoll fd/socket -> SSL_CTX. Fatal paths skip SSL_shutdown.
} catch (const std::exception &e) {
    return study::failed(e);
}
