#include <iostream>
#include <vector>
#include <thread>
#include <chrono>
#include <atomic>

void yield() {
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
}

std::atomic<bool> do_run (true);
void background_wait() {
    while (do_run) {

    }
}

static constexpr size_t kBenchIter = 1000000000;
void benchmark_thread() {
    auto start = std::chrono::high_resolution_clock::now();
    for (size_t i=0; i<kBenchIter; ++i) {

    }
    auto elapsed = std::chrono::high_resolution_clock::now() - start;
    std::cout << "> took " << std::chrono::duration_cast<std::chrono::microseconds>(elapsed).count() << " us" << std::endl;
}

static constexpr size_t kNumThreads = 4;
int main() {
    std::vector<std::thread> background_threads;

    for (size_t i=0; i<kNumThreads; ++i) {
        background_threads.push_back(std::thread(background_wait));
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(1000));

    auto b_thread = std::thread(benchmark_thread);
    b_thread.join();

    std::this_thread::sleep_for(std::chrono::milliseconds(1000));

    do_run = false;
    for (size_t i=0; i<kNumThreads; ++i) {
        background_threads[i].join();
    }

    return 0;
}
