#include "study.hpp"

int main() try {
    ERR_clear_error();
    study::Md missing(EVP_MD_fetch(nullptr,"NO_SUCH_DIGEST",nullptr));
    study::require(!missing,"expected missing digest");
    study::require(ERR_peek_error()!=0,"error queued");
    std::cout<<"PEEK leaves queue intact\n";
    std::cout<<study::errors();
    study::require(ERR_get_error()==0,"queue drained");
    study::Md sha(EVP_MD_fetch(nullptr,"SHA256",nullptr));study::require(bool(sha),"recovery fetch");
    std::cout<<"DRAINED; recovery OK\n";
} catch(const std::exception& e) { return study::failed(e); }
