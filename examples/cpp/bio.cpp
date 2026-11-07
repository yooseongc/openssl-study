// 메모리 BIO에 바이너리를 쓰거나 빈 BIO를 먼저 읽습니다.
// 실행: study-build examples/cpp/bio.cpp

#include "study.hpp"

int main(int argc, char**) try {
    // 1. 메모리 BIO를 만들고 빈 버퍼를 읽는 실패·재시도 경로를 관찰합니다.
    study::Bio memory_bio(BIO_new(BIO_s_mem()));
    study::require(bool(memory_bio), "BIO_new");

    if (argc > 1) {
        char read_buffer[8];
        const int byte_count = BIO_read(memory_bio.get(), read_buffer, sizeof read_buffer);
        std::cout << "empty read=" << byte_count
                  << " retry=" << (BIO_should_retry(memory_bio.get()) ? 1 : 0) << '\n';
        return 0;
    }

    // 2. NUL을 포함한 바이너리를 명시적인 길이로 씁니다.
    const std::array<unsigned char, 3> bytes{'A', 0, 'B'};
    size_t bytes_written = 0;
    const int bio_write_result =
        BIO_write_ex(memory_bio.get(), bytes.data(), bytes.size(), &bytes_written);
    study::require(bio_write_result == 1, "BIO write");

    // BIO 내부 버퍼 주소를 잠시 빌립니다. 별도로 해제하지 않고 BIO를 다시 읽거나 쓰기 전에 사용을
    // 끝냅니다.
    char* borrowed_data = nullptr;
    const long byte_count = BIO_get_mem_data(memory_bio.get(), &borrowed_data);
    study::require(byte_count >= 0, "memory view");

    std::cout << "borrowed view="
              << study::hex(reinterpret_cast<unsigned char*>(borrowed_data),
                            static_cast<size_t>(byte_count))
              << '\n';

    // No OPENSSL_free(borrowed). Reading/writing/resetting/freeing BIO may invalidate it.

    // 3. BIO에서 복사해 읽고 실제 읽은 바이트 수를 사용합니다.
    std::array<unsigned char, 8> read_buffer{};
    size_t bytes_read = 0;
    const int bio_read_result =
        BIO_read_ex(memory_bio.get(), read_buffer.data(), read_buffer.size(), &bytes_read);
    study::require(bio_read_result == 1, "BIO read");

    std::cout << "read=" << bytes_read << " hex=" << study::hex(read_buffer.data(), bytes_read)
              << '\n';
} catch (const std::exception& e) {

    return study::failed(e);
}
