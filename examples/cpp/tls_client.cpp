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

    Fd(const Fd&) = delete;
    Fd& operator=(const Fd&) = delete;
};

int main(int argc, char** argv) try {
    std::signal(SIGPIPE, SIG_IGN);
    const bool use_nonblocking = argc > 1 && std::string(argv[1]) == "nonblock";
    const char* expected_hostname = argc > 2 ? argv[2] : "localhost";
    const char* ca_file = argc > 3 ? argv[3] : "/home/student/lab/tls/ca.pem";
    const int port = argc > 4 ? std::stoi(argv[4]) : 4433;

    // 1. TLS 버전과 인증서 검증 정책을 준비합니다.
    study::SslCtx tls_context(SSL_CTX_new(TLS_client_method()));
    study::require(bool(tls_context), "SSL_CTX_new");

    const int minimum_version_result =
        SSL_CTX_set_min_proto_version(tls_context.get(), TLS1_3_VERSION);
    study::require(minimum_version_result == 1, "minimum version");

    SSL_CTX_set_verify(
        tls_context.get(), SSL_VERIFY_PEER, nullptr); // void API; no return to check.
    const int ca_loading_result =
        SSL_CTX_load_verify_locations(tls_context.get(), ca_file, nullptr);
    study::require(ca_loading_result == 1, "CA loading");

    // 2. TCP 소켓과 epoll을 준비합니다. 두 자원은 Fd가 해제합니다.
    Fd fd(::socket(AF_INET, SOCK_STREAM, 0)), epoll_fd(::epoll_create1(EPOLL_CLOEXEC));
    if (use_nonblocking) {
        study::require(::fcntl(fd.value, F_SETFL, O_NONBLOCK) == 0, "nonblocking socket");
    } else {
        const timeval limit{5, 0};
        study::require(::setsockopt(fd.value, SOL_SOCKET, SO_RCVTIMEO, &limit, sizeof limit) == 0,
                       "read timeout");
        study::require(::setsockopt(fd.value, SOL_SOCKET, SO_SNDTIMEO, &limit, sizeof limit) == 0,
                       "write timeout");
    }
    epoll_event event{};
    event.events = EPOLLIN | EPOLLOUT;
    event.data.fd = fd.value;
    study::require(::epoll_ctl(epoll_fd.value, EPOLL_CTL_ADD, fd.value, &event) == 0, "epoll add");

    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(8);
    auto wait_ready = [&](int error) {
        event.events =
            (error == SSL_ERROR_WANT_READ ? EPOLLIN : EPOLLOUT); // Level-triggered for this lesson.
        study::require(::epoll_ctl(epoll_fd.value, EPOLL_CTL_MOD, fd.value, &event) == 0,
                       "epoll modify");
        for (;;) {
            const auto remaining = std::chrono::duration_cast<std::chrono::milliseconds>(
                                       deadline - std::chrono::steady_clock::now())
                                       .count();
            if (remaining <= 0) {
                throw std::runtime_error("deadline exceeded");
            }
            const int n = ::epoll_wait(epoll_fd.value, &event, 1, static_cast<int>(remaining));
            if (n < 0 && errno == EINTR) {
                continue;
            }
            if (n <= 0) {
                throw std::runtime_error("epoll deadline/error");
            }
            return; // HUP/ERR also wake us; next SSL call decides the TLS outcome.
        }
    };

    // 3. TCP 연결을 완료합니다. EINPROGRESS이면 쓰기 준비 후 SO_ERROR를 확인합니다.
    sockaddr_in server_address{};
    server_address.sin_family = AF_INET;
    server_address.sin_port = htons(static_cast<uint16_t>(port));
    study::require(::inet_pton(AF_INET, "127.0.0.1", &server_address.sin_addr) == 1, "address");

    if (::connect(fd.value, reinterpret_cast<sockaddr*>(&server_address), sizeof server_address) !=
        0) {
        if (!use_nonblocking || errno != EINPROGRESS) {
            throw std::runtime_error("TCP connect failed");
        }
        wait_ready(SSL_ERROR_WANT_WRITE);
        int socket_error = 0;
        socklen_t size = sizeof socket_error;
        study::require(::getsockopt(fd.value, SOL_SOCKET, SO_ERROR, &socket_error, &size) == 0 &&
                           socket_error == 0,
                       "TCP connect completion");
    }

    // 4. SSL 객체를 소켓에 연결하고 SNI와 이름 검증을 설정합니다.
    study::Ssl connection(SSL_new(tls_context.get()));
    study::require(bool(connection), "SSL_new");

    const int ssl_set_fd_result = SSL_set_fd(connection.get(), fd.value);
    study::require(ssl_set_fd_result == 1, "SSL_set_fd"); // socket remains owned by Fd.
    const int sni_result = SSL_set_tlsext_host_name(connection.get(), expected_hostname);
    study::require(sni_result == 1, "SNI");

    const int hostname_verification_result = SSL_set1_host(connection.get(), expected_hostname);
    study::require(hostname_verification_result == 1, "hostname verification");

    // WANT_READ와 WANT_WRITE는 다음에 기다릴 소켓 이벤트입니다. 준비 알림이 오면 중단됐던 SSL
    // 호출을 다시 수행합니다.
    auto retry = [&](int error, const char* operation) {
        if (use_nonblocking && (error == SSL_ERROR_WANT_READ || error == SSL_ERROR_WANT_WRITE)) {
            std::cout << operation << ": "
                      << (error == SSL_ERROR_WANT_READ ? "WANT_READ" : "WANT_WRITE")
                      << " -> epoll\n";
            wait_ready(error);
            return;
        }
        throw std::runtime_error(std::string(operation) + " SSL_get_error=" +
                                 std::to_string(error) + "\n" + study::errors());
    };

    // 5. 핸드셰이크를 진행합니다. 재시도는 같은 SSL 객체에서 계속합니다.
    for (;;) {
        ERR_clear_error();
        const int result = SSL_connect(connection.get());
        if (result == 1) {
            break;
        }
        const int error = SSL_get_error(
            connection.get(), result); // Same thread, immediately, before logging/freeing.
        retry(error, "handshake");
    }
    study::require(SSL_get_verify_result(connection.get()) == X509_V_OK, "verified chain");

    study::Cert peer_certificate(SSL_get1_peer_certificate(connection.get()));
    study::require(bool(peer_certificate), "peer certificate");

    std::cout << "Verified TLS: " << SSL_get_version(connection.get()) << " / "
              << SSL_get_cipher_name(connection.get()) << '\n';

    // 6. HTTP 요청을 보냅니다. WANT 재시도에서는 입력 버퍼를 그대로 유지합니다.
    const std::string request = "GET / HTTP/1.0\r\nHost: localhost\r\n\r\n";
    size_t offset = 0;
    while (offset < request.size()) {
        size_t written = 0;
        ERR_clear_error();
        const int result = SSL_write_ex(
            connection.get(), request.data() + offset, request.size() - offset, &written);
        if (result == 1) {
            offset += written;
            continue;
        }
        const int error = SSL_get_error(connection.get(), result);

        // On WANT, offset and the original buffer/length stay unchanged until retry succeeds.
        retry(error, "write");
    }

    // 7. 응답을 누적하고 정상 close_notify와 갑작스러운 EOF를 구분합니다.
    std::string response;
    std::array<char, 2048> buffer{};
    for (;;) {
        size_t received = 0;
        ERR_clear_error();
        const int result = SSL_read_ex(connection.get(), buffer.data(), buffer.size(), &received);
        if (result == 1) {
            response.append(buffer.data(), received);
            if (response.size() > 1024 * 1024) {
                throw std::runtime_error("response limit exceeded");
            }
            continue;
        }
        const int error = SSL_get_error(connection.get(), result);
        if (error == SSL_ERROR_ZERO_RETURN) {
            std::cout << "peer close_notify received\n";
            break;
        }
        retry(error,
              "read"); // Unexpected transport EOF is a failure; do not treat it as close_notify.
    }

    // 8. 정상 경로에서는 TLS 종료 알림 교환을 마칩니다.
    for (;;) {
        ERR_clear_error();
        const int result = SSL_shutdown(connection.get());
        if (result == 1) {
            std::cout << "shutdown complete\n";
            break;
        }
        if (result == 0) {
            std::cout << "close_notify sent; waiting for peer\n";
            if (use_nonblocking) {
                wait_ready(SSL_ERROR_WANT_READ);
            }
            continue;
        }
        const int error = SSL_get_error(connection.get(), result);
        retry(error, "shutdown");
    }
    std::cout << response.substr(0, response.find('\n'))
              << "\napplication bytes=" << response.size() << '\n';

    // Destruction: peer -> SSL -> epoll fd/socket -> SSL_CTX. Fatal paths skip SSL_shutdown.
} catch (const std::exception& e) {

    return study::failed(e);
}
