#include "study.hpp"

int main(int argc,char**) try {
    study::Bio bio(BIO_new(BIO_s_mem()));study::require(bool(bio),"BIO_new");
    if(argc>1) {
        char out[8];const int n=BIO_read(bio.get(),out,sizeof out);
        std::cout<<"empty read="<<n<<" retry="<<(BIO_should_retry(bio.get())?1:0)<<'\n';return 0;
    }
    const std::array<unsigned char,3> bytes{'A',0,'B'};
    size_t written=0;
    study::require(BIO_write_ex(bio.get(),bytes.data(),bytes.size(),&written)==1,"BIO write");
    char* borrowed=nullptr;const long n=BIO_get_mem_data(bio.get(),&borrowed);
    study::require(n>=0,"memory view");
    std::cout<<"borrowed view="<<study::hex(reinterpret_cast<unsigned char*>(borrowed),static_cast<size_t>(n))<<'\n';
    // No OPENSSL_free(borrowed). Reading/writing/resetting/freeing BIO may invalidate it.
    std::array<unsigned char,8> out{};size_t read=0;
    study::require(BIO_read_ex(bio.get(),out.data(),out.size(),&read)==1,"BIO read");
    std::cout<<"read="<<read<<" hex="<<study::hex(out.data(),read)<<'\n';
} catch(const std::exception& e) { return study::failed(e); }
