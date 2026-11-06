// 첫 인자는 bytes 또는 hash이고, hash 뒤에는 메시지 하나를 넣습니다.
// 실행: study-build examples/cpp/digest.cpp bytes

#include "study.hpp"
#include <cstring>

int main(int argc, char** argv) try {
    const std::string operation = argc > 1 ? argv[1] : "hash";
    if (operation == "bytes") {
        const std::array<unsigned char, 3> bytes{'A', 0, 'B'};
        std::cout << "bytes=" << bytes.size() << " hex=" << study::hex(bytes.data(), bytes.size())
                  << " strlen=" << std::strlen(reinterpret_cast<const char*>(bytes.data())) << '\n';
        return 0;
    }

    // 1. 해시할 입력과 알고리즘, 연산 상태를 준비합니다.
    const std::string message = argc > 2 ? argv[2] : "abc";
    // SHA256 구현과 연산 상태(ctx)는 별개의 소유 객체입니다. Handle이 각 객체의 free 함수를
    // 호출합니다.
    study::Md algorithm(EVP_MD_fetch(nullptr, "SHA256", "provider=default"));
    study::MdCtx digest_context(EVP_MD_CTX_new());
    study::require(algorithm && digest_context, "allocate digest objects");

    // 2. SHA-256 계산을 초기화합니다. 반환값 1을 확인한 뒤 입력을 넣습니다.
    const int digest_init_result =
        EVP_DigestInit_ex2(digest_context.get(), algorithm.get(), nullptr);
    study::require(digest_init_result == 1, "DigestInit");
    // 입력은 바이트열로 다룹니다. strlen 대신 실제 바이트 수를 전달합니다.

    // 3. 메시지를 두 조각으로 처리합니다. Update마다 결과를 출력하지 않습니다.
    const auto first_chunk_size = message.size() / 2;
    const int update_1_result =
        EVP_DigestUpdate(digest_context.get(), message.data(), first_chunk_size);
    study::require(update_1_result == 1, "Update #1");
    const int update_2_result = EVP_DigestUpdate(
        digest_context.get(), message.data() + first_chunk_size, message.size() - first_chunk_size
    );
    study::require(update_2_result == 1, "Update #2");

    // 4. 전체 입력에 대한 최종 해시와 실제 길이를 받습니다.
    std::array<unsigned char, EVP_MAX_MD_SIZE> digest{};
    unsigned int digest_length = 0;
    const int final_result =
        EVP_DigestFinal_ex(digest_context.get(), digest.data(), &digest_length);
    study::require(final_result == 1, "Final");
    std::cout << study::hex(digest.data(), digest_length) << '\n';
} catch (const std::exception& e) {
    return study::failed(e);
}
