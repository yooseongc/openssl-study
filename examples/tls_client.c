// 검증할 호스트 이름과 CA 파일 경로를 순서대로 받습니다.
// 실행: study-build examples/tls_client.c localhost

#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <openssl/ssl.h>
#include <openssl/err.h>

int main(int argc, char** argv) {
    const char* hostname = argc > 1 ? argv[1] : "localhost";
    const char* cafile = argc > 2 ? argv[2] : "/home/student/lab/tls/ca.pem";
    // 기본 종료 코드는 실패입니다. 모든 단계가 성공한 뒤에만 0으로 바꿉니다.
    int exit_code = 1;

    SSL_CTX* tls_context = NULL;
    BIO* connection = NULL;
    SSL* tls_connection = NULL; /* Borrowed from BIO: do not SSL_free it. */
    signal(SIGPIPE, SIG_IGN);
    tls_context = SSL_CTX_new(TLS_client_method());
    if (!tls_context || SSL_CTX_set_min_proto_version(tls_context, TLS1_3_VERSION) != 1) {
        goto end;
    }
    SSL_CTX_set_verify(tls_context, SSL_VERIFY_PEER, NULL);
    if (SSL_CTX_load_verify_locations(tls_context, cafile, NULL) != 1) {
        goto end;
    }
    // BIO 체인이 SSL 객체를 소유합니다. SSL 포인터는 빌려 쓰고 마지막에 BIO_free_all로 체인을
    // 해제합니다.
    connection = BIO_new_ssl_connect(tls_context);
    if (!connection || BIO_get_ssl(connection, &tls_connection) != 1 || !tls_connection) {
        goto end;
    }
    /* SNI selects a virtual host; SSL_set1_host verifies the certificate name. */
    if (SSL_set_tlsext_host_name(tls_connection, hostname) != 1 ||
        SSL_set1_host(tls_connection, hostname) != 1) {
        goto end;
    }
    if (BIO_set_conn_hostname(connection, "127.0.0.1:4433") != 1 ||
        BIO_do_connect(connection) <= 0 || BIO_do_handshake(connection) <= 0) {
        goto end;
    }
    if (SSL_get_verify_result(tls_connection) != X509_V_OK) {
        goto end;
    }
    printf(
        "Verified TLS: %s / %s / hostname=%s\n",
        SSL_get_version(tls_connection),
        SSL_get_cipher_name(tls_connection),
        hostname
    );
    const char request[] = "GET / HTTP/1.0\r\nHost: localhost\r\n\r\n";
    size_t written = 0, received = 0;
    if (SSL_write_ex(tls_connection, request, strlen(request), &written) != 1) {
        goto end;
    }
    char buffer[4096];
    while (SSL_read_ex(tls_connection, buffer, sizeof(buffer), &received) == 1) {
        fwrite(buffer, 1, received, stdout);
    }
    if (SSL_get_error(tls_connection, 0) != SSL_ERROR_ZERO_RETURN) {
        goto end;
    }
    SSL_shutdown(tls_connection);
    exit_code = 0;

// 실패한 위치와 관계없이 이미 생성한 자원을 역순으로 정리합니다.
end:
    if (exit_code) {
        ERR_print_errors_fp(stderr);
    }
    BIO_free_all(connection);
    SSL_CTX_free(tls_context);
    return exit_code;
}
