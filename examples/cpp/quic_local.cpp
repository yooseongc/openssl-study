// 실행: study-build examples/cpp/quic_local.cpp [ok|multi|bad-host|bad-alpn|epoll]
// 외부 서버 없이 fork한 자식과 UDP loopback으로 통신합니다. HTTP/3 예제가 아닙니다.
#include "study.hpp"
#include <arpa/inet.h>
#include <sys/epoll.h>
#include <sys/wait.h>
#include <unistd.h>
#include <algorithm>
#include <cerrno>
#include <chrono>
#include <csignal>
#include <cstring>

namespace {
constexpr unsigned char protocol[] = {7, 's', 't', 'u', 'd', 'y', '/', '1'};

// SSL_set_fd는 fd를 닫지 않습니다. SSL 객체보다 먼저 선언하여 마지막에 닫습니다.
struct Socket {
    int fd;

    explicit Socket(int value) : fd(value) {
        if (fd < 0) {
            throw std::runtime_error(std::strerror(errno));
        }
    }

    ~Socket() {
        close(fd);
    }

    Socket(const Socket&) = delete;
    Socket& operator=(const Socket&) = delete;
};

// 예외 경로에서도 이번 실습이 만든 자식만 회수합니다.
struct Child {
    pid_t pid;

    ~Child() {
        if (pid > 0) {
            kill(pid, SIGTERM);
            while (waitpid(pid, nullptr, 0) < 0 && errno == EINTR) {
            }
        }
    }
};

int select_protocol(SSL*,
                    const unsigned char** out,
                    unsigned char* length,
                    const unsigned char* offered,
                    unsigned int size,
                    void*) {
    unsigned char* selected = nullptr;
    const int result =
        SSL_select_next_proto(&selected, length, protocol, sizeof(protocol), offered, size);
    if (result != OPENSSL_NPN_NEGOTIATED) {
        return SSL_TLSEXT_ERR_ALERT_FATAL;
    }
    *out = selected; // static protocol 배열을 빌려줍니다. 콜백 밖에서도 살아 있습니다.
    return SSL_TLSEXT_ERR_OK;
}

// WANT_READ/WRITE는 애플리케이션 I/O 상태입니다. UDP 감시 조건과 동일하지 않습니다.
// 연결이 요구하는 네트워크 이벤트와 QUIC 타이머를 따로 조회합니다.
void wait_events(SSL* connection, int fd) {
    Socket poller(epoll_create1(EPOLL_CLOEXEC));
    epoll_event event{};
    event.events = (SSL_net_read_desired(connection) ? static_cast<uint32_t>(EPOLLIN) : 0U) |
        (SSL_net_write_desired(connection) ? static_cast<uint32_t>(EPOLLOUT) : 0U);
    event.data.fd = fd;
    if (epoll_ctl(poller.fd, EPOLL_CTL_ADD, fd, &event) != 0) {
        throw std::runtime_error("epoll_ctl");
    }

    timeval timeout{};
    int infinite = 0;
    const int result = SSL_get_event_timeout(connection, &timeout, &infinite);
    study::require(result == 1, "get event timeout");
    // 최대 100ms는 데모의 전체 deadline을 자주 확인하기 위한 상한입니다.
    const long long milliseconds = timeout.tv_sec * 1000LL + (timeout.tv_usec + 999) / 1000;
    const int delay = infinite ? 100 : static_cast<int>(std::clamp(milliseconds, 0LL, 100LL));
    const int ready = epoll_wait(poller.fd, &event, 1, delay);
    if (ready < 0 && errno != EINTR) {
        throw std::runtime_error("epoll_wait");
    }
    study::require(SSL_handle_events(connection) == 1, "handle QUIC events");
}

// 호출 직전 오류 큐를 비우고, 실패 직후 같은 스레드에서 SSL_get_error를 호출합니다.
// 재시도 시 write의 포인터·길이·내용을 바꾸지 않도록 호출자가 버퍼를 유지합니다.
template <class Operation>
bool transfer(SSL* object, SSL* connection, int fd, const char* name, Operation operation) {
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
    for (;;) {
        ERR_clear_error();
        const int result = operation();
        if (result == 1) {
            return true;
        }
        const int error = SSL_get_error(object, result);
        if (error == SSL_ERROR_ZERO_RETURN) {
            return false; // stream의 수신 FIN
        }
        if (error != SSL_ERROR_WANT_READ && error != SSL_ERROR_WANT_WRITE) {
            throw std::runtime_error(std::string(name) + ": SSL_get_error=" +
                                     std::to_string(error) + "\n" + study::errors());
        }
        if (std::chrono::steady_clock::now() >= deadline) {
            throw std::runtime_error(std::string(name) + ": deadline exceeded");
        }
        wait_events(connection, fd);
    }
}

void send_message(SSL* stream, SSL* connection, int fd, const std::string& message) {
    size_t written = 0;
    const bool ok = transfer(stream, connection, fd, "write", [&] {
        return SSL_write_ex(stream, message.data(), message.size(), &written);
    });
    study::require(ok && written == message.size(), "write full message");
    // FIN은 이 스트림의 송신 방향만 끝냅니다. 연결이나 반대 방향을 닫지 않습니다.
    study::require(SSL_stream_conclude(stream, 0) == 1, "send stream FIN");
}

std::string receive_message(SSL* stream, SSL* connection, int fd) {
    std::string message;
    std::array<char, 128> buffer{};
    for (;;) {
        size_t received = 0;
        const bool data = transfer(stream, connection, fd, "read", [&] {
            return SSL_read_ex(stream, buffer.data(), buffer.size(), &received);
        });
        if (!data) {
            return message;
        }
        message.append(buffer.data(), received);
        study::require(message.size() <= 4096, "demo message limit");
    }
}

void serve(int fd, int streams) {
    study::SslCtx context(SSL_CTX_new(OSSL_QUIC_server_method()));
    study::require(bool(context), "server context");
    study::require(SSL_CTX_use_certificate_chain_file(context.get(), "tls/server.pem") == 1,
                   "server certificate");
    study::require(SSL_CTX_use_PrivateKey_file(context.get(), "tls/server.key", SSL_FILETYPE_PEM) ==
                       1,
                   "server key");
    study::require(SSL_CTX_check_private_key(context.get()) == 1, "key matches certificate");
    SSL_CTX_set_alpn_select_cb(context.get(), select_protocol, nullptr);

    study::Ssl listener(SSL_new_listener(context.get(), 0));
    study::require(bool(listener), "new listener");
    study::require(SSL_set_fd(listener.get(), fd) == 1, "listener UDP fd");
    study::Ssl connection(SSL_accept_connection(listener.get(), 0));
    study::require(bool(connection), "accept QUIC connection");
    study::require(SSL_set_default_stream_mode(connection.get(), SSL_DEFAULT_STREAM_MODE_NONE) == 1,
                   "server explicit streams");

    for (int i = 0; i < streams; ++i) {
        study::Ssl stream(SSL_accept_stream(connection.get(), 0));
        study::require(bool(stream), "accept stream");
        const auto message = receive_message(stream.get(), connection.get(), fd);
        send_message(stream.get(), connection.get(), fd, message);
    }
    // 부모가 종료할 때까지 이벤트를 처리하여 마지막 응답도 재전송할 수 있게 합니다.
    for (;;) {
        study::require(SSL_handle_events(connection.get()) == 1, "server events");
        usleep(10000);
    }
}
} // namespace

int main(int argc, char** argv) try {
    const std::string mode = argc > 1 ? argv[1] : "ok";
    if (mode != "ok" && mode != "multi" && mode != "bad-host" && mode != "bad-alpn" &&
        mode != "epoll") {
        throw std::runtime_error("usage: quic_local [ok|multi|bad-host|bad-alpn|epoll]");
    }
    const int streams = mode == "multi" ? 3 : 1;

    // OS가 비어 있는 UDP 포트를 선택합니다. 외부 인터페이스로는 열지 않습니다.
    Socket server_socket(socket(AF_INET, SOCK_DGRAM, 0));
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(server_socket.fd, reinterpret_cast<sockaddr*>(&address), sizeof(address)) != 0) {
        throw std::runtime_error("bind loopback");
    }
    socklen_t address_size = sizeof(address);
    if (getsockname(server_socket.fd, reinterpret_cast<sockaddr*>(&address), &address_size) != 0) {
        throw std::runtime_error("getsockname");
    }

    const pid_t pid = fork();
    if (pid < 0) {
        throw std::runtime_error("fork");
    }
    if (pid == 0) {
        alarm(12); // 부모가 강제 종료되어도 데모 서버가 영구히 남지 않게 합니다.
        try {
            serve(server_socket.fd, streams);
        } catch (const std::exception& error) {
            std::cerr << "server: " << error.what() << '\n';
        }
        _exit(1);
    }
    Child child{pid};
    Socket client_socket(socket(AF_INET, SOCK_DGRAM, 0));
    study::SslCtx context(SSL_CTX_new(OSSL_QUIC_client_method()));
    study::require(bool(context), "client context");
    SSL_CTX_set_verify(context.get(), SSL_VERIFY_PEER, nullptr);
    study::require(SSL_CTX_load_verify_locations(context.get(), "tls/ca.pem", nullptr) == 1,
                   "load CA");
    study::Ssl connection(SSL_new(context.get()));
    study::require(bool(connection), "client connection");
    study::require(SSL_set_fd(connection.get(), client_socket.fd) == 1, "client UDP fd");

    study::Handle<BIO_ADDR, BIO_ADDR_free> peer(BIO_ADDR_new());
    study::require(bool(peer), "peer address");
    study::require(
        BIO_ADDR_rawmake(
            peer.get(), AF_INET, &address.sin_addr, sizeof(address.sin_addr), address.sin_port) ==
            1,
        "make peer address");
    study::require(SSL_set1_initial_peer_addr(connection.get(), peer.get()) == 1,
                   "set peer address");
    study::require(SSL_set_tlsext_host_name(connection.get(), "localhost") == 1, "SNI");
    const char* host = mode == "bad-host" ? "wrong.example" : "localhost";
    study::require(SSL_set1_host(connection.get(), host) == 1, "verification hostname");
    auto offered = std::to_array(protocol);
    if (mode == "bad-alpn") {
        offered.back() = '2';
    }
    study::require(SSL_set_alpn_protos(connection.get(), offered.data(), offered.size()) == 0,
                   "ALPN");
    study::require(SSL_set_default_stream_mode(connection.get(), SSL_DEFAULT_STREAM_MODE_NONE) == 1,
                   "client explicit streams");
    if (mode == "epoll") {
        study::require(SSL_set_blocking_mode(connection.get(), 0) == 1, "nonblocking QUIC");
    }

    try {
        study::require(transfer(connection.get(),
                                connection.get(),
                                client_socket.fd,
                                "connect",
                                [&] { return SSL_connect(connection.get()); }),
                       "connection closed during handshake");
    } catch (...) {
        std::cerr << "verify: "
                  << X509_verify_cert_error_string(SSL_get_verify_result(connection.get())) << '\n';
        throw;
    }
    std::cout << "QUIC connected; ALPN=study/1; certificate verified\n";
    for (int i = 0; i < streams; ++i) {
        study::Ssl stream(SSL_new_stream(connection.get(), 0));
        study::require(bool(stream), "new bidirectional stream");
        const std::string request = "hello stream " + std::to_string(i);
        send_message(stream.get(), connection.get(), client_socket.fd, request);
        const auto reply = receive_message(stream.get(), connection.get(), client_socket.fd);
        study::require(reply == request, "echo matches");
        std::cout << "stream=" << SSL_get_stream_id(stream.get()) << " echo=" << reply
                  << " FIN received\n";
    }
    // 데모 종료는 rapid shutdown입니다. 운영 코드에서는 graceful shutdown과 deadline을 설계합니다.
    study::require(SSL_set_blocking_mode(connection.get(), 1) == 1, "blocking shutdown");
    const int closed = SSL_shutdown_ex(connection.get(), SSL_SHUTDOWN_FLAG_RAPID, nullptr, 0);
    study::require(closed >= 0, "rapid connection shutdown");
    std::cout << "PASS " << mode << '\n';
} catch (const std::exception& error) {

    return study::failed(error);
}
