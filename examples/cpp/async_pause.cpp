// 실행: study-build examples/cpp/async_pause.cpp [ok|fail]
// OpenSSL의 실제 ASYNC API를 쓰지만 장치나 완료 이벤트는 없는 제어 흐름 실험입니다.
#include "study.hpp"
#include <openssl/async.h>
#include <cstdlib>

struct Input {
    int result;
};

int operation(void* raw) {
    // args는 바이트 복사됩니다. 포인터 멤버가 있다면 가리키는 데이터까지 복사되지는 않습니다.
    const auto* input = static_cast<const Input*>(raw);
    std::cout << "job: before pause\n";
    if (ASYNC_pause_job() != 1) {
        return -1;
    }
    std::cout << "job: resumed on the same thread\n";
    return input->result;
}

int main(int argc, char** argv) try {
    const std::string mode = argc > 1 ? argv[1] : "ok";
    study::require(mode == "ok" || mode == "fail", "mode: ok or fail");
    if (ASYNC_is_capable() != 1) {
        std::cout << "UNAVAILABLE OpenSSL ASYNC\n";
        return 77;
    }
    study::require(ASYNC_init_thread(1, 1) == 1, "init job pool");
    study::Handle<ASYNC_WAIT_CTX, ASYNC_WAIT_CTX_free> wait_context(ASYNC_WAIT_CTX_new());
    study::require(bool(wait_context), "wait context");

    ASYNC_JOB* job = nullptr; // 풀 관리 객체입니다. delete/free하지 않습니다.
    Input input{mode == "ok" ? 42 : -1};
    int operation_result = 0;
    int state = ASYNC_start_job(
        &job, wait_context.get(), &operation_result, operation, &input, sizeof(input));
    if (state == ASYNC_PAUSE) {
        std::cout << "caller: PAUSE; demo resumes explicitly (no QAT device)\n";
        // 실제 가속에서는 완료 통지를 기다립니다. 여기서는 중단 위치 재개만 관찰합니다.
        state = ASYNC_start_job(
            &job, wait_context.get(), &operation_result, operation, &input, sizeof(input));
    }
    if (state != ASYNC_FINISH) {
        std::cerr << "job framework error, state=" << state << '\n' << study::errors();
        // 이 작은 데모에는 미완료 작업의 취소 프로토콜이 없습니다.
        // 남은 작업이 있다면 그 스택이 참조하는 wait_context를 해제하며 계속하지 않습니다.
        if (job != nullptr) {
            std::cerr << "unfinished job: terminating demo process\n" << std::flush;
            std::_Exit(1);
        }
        wait_context.reset();
        ASYNC_cleanup_thread();
        return 1;
    }
    study::require(job == nullptr, "finished job returned to pool");
    std::cout << "caller: FINISH; operation_result=" << operation_result << '\n';
    wait_context.reset();
    ASYNC_cleanup_thread(); // 모든 작업이 끝난 뒤 이 스레드의 풀을 정리합니다.
    return operation_result == 42 ? 0 : 2;
} catch (const std::exception& error) {

    return study::failed(error);
}
