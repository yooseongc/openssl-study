#include "study.hpp"
#include <utility>
#include <boost/asio.hpp>
#include <boost/asio/ssl.hpp>
#include <csignal>

int main(int argc,char** argv) try {
    std::signal(SIGPIPE,SIG_IGN);
    namespace asio=boost::asio;using tcp=asio::ip::tcp;
    const std::string hostname=argc>1?argv[1]:"localhost";
    asio::io_context io;
    asio::ssl::context ctx(asio::ssl::context::tls_client);
    ctx.set_verify_mode(asio::ssl::verify_peer);
    ctx.load_verify_file("/home/student/lab/tls/ca.pem");
    study::require(SSL_CTX_set_min_proto_version(ctx.native_handle(),TLS1_3_VERSION)==1,"min TLS version");
    asio::ssl::stream<tcp::socket> stream(io,ctx);
    // native_handle is BORROWED. Do not SSL_free it or drive SSL_read/SSL_write concurrently with Asio.
    study::require(SSL_set_tlsext_host_name(stream.native_handle(),hostname.c_str())==1,"SNI");
    study::require(SSL_set1_host(stream.native_handle(),hostname.c_str())==1,"hostname verification");
    const std::string request="GET / HTTP/1.0\r\nHost: localhost\r\n\r\n"; // Alive through callback completion.
    std::array<char,2048> buffer{};std::string response;
    asio::steady_timer timer(io,std::chrono::seconds(8));
    bool finished=false;int exit_code=1;
    auto finish=[&](int code,const std::string& detail){
        if(finished)return;
        finished=true;exit_code=code;std::cout<<detail<<'\n';
        timer.cancel();boost::system::error_code ignored;stream.next_layer().close(ignored);
    };
    timer.async_wait([&](auto ec){if(!ec)finish(1,"deadline exceeded; socket cancelled");});
    std::function<void()> read;
    read=[&]{stream.async_read_some(asio::buffer(buffer),[&](auto ec,size_t n){
        if(finished)return;
        response.append(buffer.data(),n);
        if(response.size()>1024*1024){finish(1,"response limit exceeded");return;}
        if(!ec){read();return;}
        if(ec==asio::error::eof){
            stream.async_shutdown([&](auto end_ec){
                if(end_ec){finish(1,"shutdown: "+end_ec.message());return;}
                finish(0,"ASIO VERIFIED; close_notify; "+response.substr(0,response.find('\n')));
            });return;
        }
        finish(1,"read: "+ec.message()); // stream_truncated is not silently ignored.
    });};
    stream.next_layer().async_connect(tcp::endpoint(asio::ip::make_address("127.0.0.1"),4433),[&](auto ec){
        if(finished)return;
        if(ec){finish(1,"connect: "+ec.message());return;}
        stream.async_handshake(asio::ssl::stream_base::client,[&](auto handshake_ec){
            if(finished)return;
            if(handshake_ec){finish(1,"handshake: "+handshake_ec.message());return;}
            asio::async_write(stream,asio::buffer(request),[&](auto write_ec,size_t){
                if(finished)return;
                if(write_ec){finish(1,"write: "+write_ec.message());return;}
                read();
            });
        });
    });
    // One thread executes callbacks. A multi-threaded io_context requires explicit serialization.
    io.run();return exit_code;
} catch(const std::exception& e) { return study::failed(e); }
