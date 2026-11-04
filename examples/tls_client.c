#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <openssl/ssl.h>
#include <openssl/err.h>

int main(int argc, char **argv) {
    const char *hostname = argc > 1 ? argv[1] : "localhost";
    const char *cafile = argc > 2 ? argv[2] : "/home/student/lab/tls/ca.pem";
    int rc = 1;
    SSL_CTX *ctx = NULL;
    BIO *connection = NULL;
    SSL *ssl = NULL; /* Borrowed from BIO: do not SSL_free it. */
    signal(SIGPIPE, SIG_IGN);
    ctx = SSL_CTX_new(TLS_client_method());
    if (!ctx || SSL_CTX_set_min_proto_version(ctx, TLS1_3_VERSION) != 1) goto end;
    SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, NULL);
    if (SSL_CTX_load_verify_locations(ctx, cafile, NULL) != 1) goto end;
    connection = BIO_new_ssl_connect(ctx);
    if (!connection || BIO_get_ssl(connection, &ssl) != 1 || !ssl) goto end;
    /* SNI selects a virtual host; SSL_set1_host verifies the certificate name. */
    if (SSL_set_tlsext_host_name(ssl, hostname) != 1 || SSL_set1_host(ssl, hostname) != 1) goto end;
    if (BIO_set_conn_hostname(connection, "127.0.0.1:4433") != 1 ||
        BIO_do_connect(connection) <= 0 || BIO_do_handshake(connection) <= 0) goto end;
    if (SSL_get_verify_result(ssl) != X509_V_OK) goto end;
    printf("Verified TLS: %s / %s / hostname=%s\n", SSL_get_version(ssl), SSL_get_cipher_name(ssl), hostname);
    const char request[] = "GET / HTTP/1.0\r\nHost: localhost\r\n\r\n";
    size_t written = 0, received = 0;
    if (SSL_write_ex(ssl, request, strlen(request), &written) != 1) goto end;
    char buffer[4096];
    while (SSL_read_ex(ssl, buffer, sizeof(buffer), &received) == 1) fwrite(buffer, 1, received, stdout);
    if (SSL_get_error(ssl, 0) != SSL_ERROR_ZERO_RETURN) goto end;
    SSL_shutdown(ssl);
    rc = 0;
end:
    if (rc) ERR_print_errors_fp(stderr);
    BIO_free_all(connection);
    SSL_CTX_free(ctx);
    return rc;
}
