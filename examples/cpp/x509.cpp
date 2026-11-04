#include "study.hpp"
#include <openssl/pem.h>
#include <openssl/x509v3.h>

int main(int argc,char** argv) try {
    const char* file=argc>1?argv[1]:"/home/student/lab/tls/server.pem";
    const char* ca=argc>2?argv[2]:"/home/student/lab/tls/ca.pem";
    const char* host=argc>3?argv[3]:"localhost";
    study::Bio input(BIO_new_file(file,"r"));study::require(bool(input),"open PEM");
    study::Cert cert(PEM_read_bio_X509(input.get(),nullptr,nullptr,nullptr));study::require(bool(cert),"parse X509");
    study::Bio out(BIO_new_fp(stdout,BIO_NOCLOSE));study::require(bool(out),"stdout BIO");
    // X509_get_subject_name returns a borrowed pointer; never free it separately.
    study::require(X509_NAME_print_ex(out.get(),X509_get_subject_name(cert.get()),0,XN_FLAG_RFC2253)>=0,"print subject");
    std::cout<<'\n';
    study::Handle<X509_STORE,X509_STORE_free> store(X509_STORE_new());
    study::Handle<X509_STORE_CTX,X509_STORE_CTX_free> ctx(X509_STORE_CTX_new());
    study::require(store && ctx,"verification objects");
    study::require(X509_STORE_load_locations(store.get(),ca,nullptr)==1,"load trust anchors");
    study::require(X509_STORE_CTX_init(ctx.get(),store.get(),cert.get(),nullptr)==1,"verify init");
    // These inputs remain alive until verification finishes. Param is borrowed from ctx.
    X509_VERIFY_PARAM* param=X509_STORE_CTX_get0_param(ctx.get());
    study::require(X509_VERIFY_PARAM_set1_host(param,host,0)==1,"set hostname");
    study::require(X509_VERIFY_PARAM_set_purpose(param,X509_PURPOSE_SSL_SERVER)==1,"set server purpose");
    const int ret=X509_verify_cert(ctx.get());
    if(ret==1){std::cout<<"CHAIN + HOST + PURPOSE OK\n";return 0;}
    const int code=X509_STORE_CTX_get_error(ctx.get());
    std::cerr<<"VERIFY REJECTED code="<<code<<" depth="<<X509_STORE_CTX_get_error_depth(ctx.get())
             <<" reason="<<X509_verify_cert_error_string(code)<<'\n';
    return ret==0?2:1;
} catch(const std::exception& e) { return study::failed(e); }
