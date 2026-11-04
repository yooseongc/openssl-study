// 첫 인자는 bytes 또는 hash이고, hash 뒤에는 메시지 하나를 넣습니다.
// 실행: study-build examples/cpp/digest.cpp bytes

#include "study.hpp"
#include <cstring>

int main(int argc, char **argv) try {
    const std::string mode = argc > 1 ? argv[1] : "hash";
    if (mode == "bytes") {
        const std::array<unsigned char, 3> bytes{'A', 0, 'B'};
        std::cout << "bytes=" << bytes.size() << " hex=" << study::hex(bytes.data(), bytes.size())
                  << " strlen=" << std::strlen(reinterpret_cast<const char *>(bytes.data()))
                  << '\n';
        return 0;
    }
    const std::string message = argc > 2 ? argv[2] : "abc";
    // SHA256 구현과 연산 상태(ctx)는 별개의 소유 객체입니다. Handle이 각 객체의 free 함수를
    // 호출합니다.
    study::Md md(EVP_MD_fetch(nullptr, "SHA256", "provider=default"));
    study::MdCtx ctx(EVP_MD_CTX_new());
    study::require(md && ctx, "allocate digest objects");
    study::require(EVP_DigestInit_ex2(ctx.get(), md.get(), nullptr) == 1, "DigestInit");
    // Explicit lengths: no strlen for arbitrary binary data; split input to show streaming.
    const auto split = message.size() / 2;
    study::require(EVP_DigestUpdate(ctx.get(), message.data(), split) == 1, "Update #1");
    study::require(EVP_DigestUpdate(ctx.get(), message.data() + split, message.size() - split) == 1,
                   "Update #2");
    std::array<unsigned char, EVP_MAX_MD_SIZE> output{};
    unsigned int length = 0;
    study::require(EVP_DigestFinal_ex(ctx.get(), output.data(), &length) == 1, "Final");
    std::cout << study::hex(output.data(), length) << '\n';
} catch (const std::exception &e) {
    return study::failed(e);
}
