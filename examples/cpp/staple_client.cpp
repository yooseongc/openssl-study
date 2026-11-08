// 로컬 서버 실행은 python /opt/scripts/revocation_lab.py staple good 명령이 담당합니다.
// 직접 실행 인자: 인증서 폴더 포트 strict|soft-missing
#include "revocation.hpp"
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>

struct Socket {
    int fd;

    ~Socket() {
        if (fd >= 0) {
            close(fd);
        }
    }
};

struct Policy {
    X509* issuer;
    X509_STORE* store;
    bool soft_missing;
    bool called = false;
    revocation::Result result{4, "UNAVAILABLE: callback not called"};
};

int check_staple(SSL* connection, void* argument) noexcept {
    auto& policy = *static_cast<Policy*>(argument);
    policy.called = true;
    try {
        const unsigned char* data = nullptr;
        const long length = SSL_get_tlsext_status_ocsp_resp(connection, &data);
        if (length <= 0 || !data) {
            policy.result = {4, "UNAVAILABLE: missing staple"};
            return policy.soft_missing ? 1 : 0;
        }
        study::Cert peer(SSL_get1_peer_certificate(connection));
        study::require(bool(peer), "peer certificate for staple");
        policy.result = revocation::verify_ocsp(
            data, static_cast<size_t>(length), peer.get(), policy.issuer, policy.store);
        // soft-missing도 revoked/unknown/서명 오류/만료를 허용하지 않습니다.
        return policy.result.code == 0 ? 1 : 0;
    } catch (const std::exception& error) {
        policy.result = {1, error.what()};
        return -1; // C 콜백 경계 밖으로 C++ 예외를 전파하지 않습니다.
    }
}

int main(int argc, char** argv) try {
    study::require(argc == 4, "usage: staple_client directory port strict|soft-missing");
    const std::string directory = argv[1], mode = argv[3];
    study::require(mode == "strict" || mode == "soft-missing", "policy mode");
    const int port = std::stoi(argv[2]);
    study::require(port > 0 && port <= 65535, "port");
    auto issuer = revocation::read_certificate(directory + "/ca.pem");
    auto store = revocation::trust_store(directory + "/ca.pem");
    Policy policy{issuer.get(), store.get(), mode == "soft-missing"};
    study::SslCtx context(SSL_CTX_new(TLS_client_method()));
    study::require(bool(context), "TLS context");
    SSL_CTX_set_verify(context.get(), SSL_VERIFY_PEER, nullptr);
    study::require(SSL_CTX_set_min_proto_version(context.get(), TLS1_3_VERSION) == 1, "TLS 1.3");
    study::require(
        SSL_CTX_load_verify_locations(context.get(), (directory + "/ca.pem").c_str(), nullptr) == 1,
        "TLS CA");
    study::require(SSL_CTX_set_tlsext_status_cb(context.get(), check_staple) == 1,
                   "status callback");
    study::require(SSL_CTX_set_tlsext_status_arg(context.get(), &policy) == 1, "callback argument");

    Socket socket{::socket(AF_INET, SOCK_STREAM, 0)};
    study::require(socket.fd >= 0, "socket");
    timeval timeout{4, 0};
    study::require(setsockopt(socket.fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) == 0,
                   "receive timeout");
    study::require(setsockopt(socket.fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout)) == 0,
                   "send timeout");
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(static_cast<uint16_t>(port));
    study::require(inet_pton(AF_INET, "127.0.0.1", &address.sin_addr) == 1, "loopback address");
    study::require(connect(socket.fd, reinterpret_cast<sockaddr*>(&address), sizeof(address)) == 0,
                   "connect");
    study::Ssl connection(SSL_new(context.get()));
    study::require(bool(connection), "TLS connection");
    study::require(SSL_set_fd(connection.get(), socket.fd) == 1, "fd");
    study::require(SSL_set_tlsext_host_name(connection.get(), "localhost") == 1, "SNI");
    study::require(SSL_set1_host(connection.get(), "localhost") == 1, "hostname");
    study::require(SSL_set_tlsext_status_type(connection.get(), TLSEXT_STATUSTYPE_ocsp) == 1,
                   "request staple");
    ERR_clear_error();
    const int connected = SSL_connect(connection.get());
    if (connected != 1) {
        const int error = SSL_get_error(connection.get(), connected);
        std::cerr << "TLS REJECTED error=" << error << '\n'
                  << policy.result.detail << '\n'
                  << study::errors();
        return policy.called && policy.result.code != 0 ? policy.result.code : 1;
    }
    study::require(SSL_get_verify_result(connection.get()) == X509_V_OK,
                   "TLS certificate verification");
    study::require(!SSL_session_reused(connection.get()) && policy.called,
                   "full handshake with status callback");
    std::cout << policy.result.detail << '\n';
    std::cout << (policy.result.code == 0 ? "ACCEPT verified staple\n"
                                          : "ACCEPT POLICY EXCEPTION: status NOT established\n");
    // 응용 데이터는 보내지 않습니다. 종료 알림 송신을 한 번 시도하고 객체·소켓을 정리합니다.
    (void)SSL_shutdown(connection.get());
    return 0;
} catch (const std::exception& error) {

    return study::failed(error);
}
