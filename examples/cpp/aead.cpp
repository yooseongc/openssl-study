#include "study.hpp"
#include <openssl/rand.h>

int main(int argc,char** argv) try {
    const std::string mode=argc>1?argv[1]:"ok";
    const std::string plaintext="authenticated message";
    std::string aad="record-header";
    std::array<unsigned char,32> key{};
    std::array<unsigned char,12> nonce{};
    std::array<unsigned char,16> tag{};
    study::require(RAND_priv_bytes(key.data(),key.size())==1,"random key");
    study::require(RAND_bytes(nonce.data(),nonce.size())==1,"random nonce");
    study::Handle<EVP_CIPHER,EVP_CIPHER_free> cipher(EVP_CIPHER_fetch(nullptr,"AES-256-GCM",nullptr));
    study::Handle<EVP_CIPHER_CTX,EVP_CIPHER_CTX_free> enc(EVP_CIPHER_CTX_new()),dec(EVP_CIPHER_CTX_new());
    study::require(cipher && enc && dec,"cipher/context allocation");
    std::vector<unsigned char> ciphertext(plaintext.size()+16),candidate(ciphertext.size());
    int length=0,total=0;
    study::require(EVP_EncryptInit_ex2(enc.get(),cipher.get(),key.data(),nonce.data(),nullptr)==1,"encrypt init");
    study::require(EVP_EncryptUpdate(enc.get(),nullptr,&length,reinterpret_cast<const unsigned char*>(aad.data()),aad.size())==1,"encrypt AAD");
    study::require(EVP_EncryptUpdate(enc.get(),ciphertext.data(),&length,reinterpret_cast<const unsigned char*>(plaintext.data()),plaintext.size())==1,"encrypt data");
    total=length;
    study::require(EVP_EncryptFinal_ex(enc.get(),ciphertext.data()+total,&length)==1,"encrypt final"); total+=length;
    study::require(EVP_CIPHER_CTX_ctrl(enc.get(),EVP_CTRL_AEAD_GET_TAG,tag.size(),tag.data())==1,"get tag");
    if(mode=="tag")tag[0]^=1;
    if(mode=="ciphertext")ciphertext[0]^=1;
    if(mode=="aad")aad[0]^=1;
    study::require(EVP_DecryptInit_ex2(dec.get(),cipher.get(),key.data(),nonce.data(),nullptr)==1,"decrypt init");
    study::require(EVP_DecryptUpdate(dec.get(),nullptr,&length,reinterpret_cast<const unsigned char*>(aad.data()),aad.size())==1,"decrypt AAD");
    study::require(EVP_DecryptUpdate(dec.get(),candidate.data(),&length,ciphertext.data(),total)==1,"decrypt data");
    const int candidate_length=length;
    study::require(EVP_CIPHER_CTX_ctrl(dec.get(),EVP_CTRL_AEAD_SET_TAG,tag.size(),tag.data())==1,"set expected tag");
    // Update output is untrusted until Final authenticates it. Do not print it early.
    if(EVP_DecryptFinal_ex(dec.get(),candidate.data()+candidate_length,&length)!=1) {
        OPENSSL_cleanse(candidate.data(),candidate.size());
        std::cout<<"AUTH REJECTED; candidate plaintext discarded\n";return 2;
    }
    std::cout<<"AUTH OK: "<<std::string(reinterpret_cast<char*>(candidate.data()),candidate_length+length)<<'\n';
} catch(const std::exception& e) { return study::failed(e); }
