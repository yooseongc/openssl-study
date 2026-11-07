// 첫 인자는 인증서에서 검증할 이름입니다. TCP는 실습 서버 127.0.0.1:4433으로 연결합니다.
// 실행: study-build examples/cpp/asio_client.cpp localhost

#include "study.hpp"
#include <utility>
#include <boost/asio.hpp>
#include <boost/asio/ssl.hpp>
#include <csignal>

int main(int argc, char** argv) try {
    std::signal(SIGPIPE, SIG_IGN);
    namespace asio = boost::asio;
    using tcp = asio::ip::tcp;
    const std::string hostname = argc > 1 ? argv[1] : "localhost";

    // 1. 이벤트 루프, TLS 정책, 연결 객체를 준비합니다.
    asio::io_context event_loop;
    asio::ssl::context tls_context(asio::ssl::context::tls_client);
    tls_context.set_verify_mode(asio::ssl::verify_peer);
    tls_context.load_verify_file("/home/student/lab/tls/ca.pem");
    const int min_tls_version_result =
        SSL_CTX_set_min_proto_version(tls_context.native_handle(), TLS1_3_VERSION);
    study::require(min_tls_version_result == 1, "min TLS version");

    asio::ssl::stream<tcp::socket> stream(event_loop, tls_context);

    // native_handle is BORROWED. Do not SSL_free it or drive SSL_read/SSL_write concurrently with
    // Asio.
    const int sni_result = SSL_set_tlsext_host_name(stream.native_handle(), hostname.c_str());
    study::require(sni_result == 1, "SNI");

    const int hostname_verification_result =
        SSL_set1_host(stream.native_handle(), hostname.c_str());
    study::require(hostname_verification_result == 1, "hostname verification");

    // 2. 모든 비동기 callback이 끝날 때까지 요청과 응답 버퍼를 유지합니다.
    const std::string request =
        "GET / HTTP/1.0\r\nHost: localhost\r\n\r\n"; // Alive through callback completion.
    std::array<char, 2048> buffer{};
    std::string response;
    asio::steady_timer deadline_timer(event_loop, std::chrono::seconds(8));
    bool finished = false;
    int exit_code = 1;

    // 타이머와 I/O 완료가 모두 도착할 수 있습니다. 첫 완료만 종료 코드를 정하고 소켓을 닫습니다.

    // 3. 첫 완료만 결과를 확정하고 타이머·소켓을 정리합니다.
    auto finish = [&](int code, const std::string& detail) {
        if (finished) {
            return;
        }
        finished = true;
        exit_code = code;
        std::cout << detail << '\n';
        deadline_timer.cancel();
        boost::system::error_code close_error;
        stream.next_layer().close(close_error);
    };
    deadline_timer.async_wait([&](auto error) {
        if (!error) {
            finish(1, "deadline exceeded; socket cancelled");
        }
    });

    // 4. 읽기 완료 callback에서 다음 읽기 또는 정상 종료를 이어갑니다.
    std::function<void()> read_next_chunk;
    read_next_chunk = [&] {
        stream.async_read_some(asio::buffer(buffer), [&](auto error, size_t bytes_read) {
            if (finished) {
                return;
            }
            response.append(buffer.data(), bytes_read);
            if (response.size() > 1024 * 1024) {
                finish(1, "response limit exceeded");
                return;
            }
            if (!error) {
                read_next_chunk();
                return;
            }
            if (error == asio::error::eof) {
                stream.async_shutdown([&](auto end_ec) {
                    if (end_ec) {
                        finish(1, "shutdown: " + end_ec.message());
                        return;
                    }
                    finish(0,
                           "ASIO VERIFIED; close_notify; " +
                               response.substr(0, response.find('\n')));
                });
                return;
            }
            finish(1, "read: " + error.message()); // stream_truncated is not silently ignored.
        });
    };

    // 5. TCP 연결 → TLS 핸드셰이크 → 요청 전송 → 응답 읽기 순서로 시작합니다.
    stream.next_layer().async_connect(
        tcp::endpoint(asio::ip::make_address("127.0.0.1"), 4433), [&](auto error) {
            if (finished) {
                return;
            }
            if (error) {
                finish(1, "connect: " + error.message());
                return;
            }
            stream.async_handshake(asio::ssl::stream_base::client, [&](auto handshake_ec) {
                if (finished) {
                    return;
                }
                if (handshake_ec) {
                    finish(1, "handshake: " + handshake_ec.message());
                    return;
                }
                asio::async_write(stream, asio::buffer(request), [&](auto write_ec, size_t) {
                    if (finished) {
                        return;
                    }
                    if (write_ec) {
                        finish(1, "write: " + write_ec.message());
                        return;
                    }
                    read_next_chunk();
                });
            });
        });

    // One thread executes callbacks. A multi-threaded io_context requires explicit serialization.

    // 6. 작업이 끝날 때까지 한 스레드에서 callback을 실행합니다.
    event_loop.run();
    return exit_code;
} catch (const std::exception& e) {

    return study::failed(e);
}
