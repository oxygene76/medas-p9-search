// SPDX-License-Identifier: GPL-3.0-or-later
// FP64 load with a check of every result: the same deterministic kernel (separate double multiply and add, built
// with --fmad=false like p9gpu; no atomics, so every launch gives the same bits) is launched again and again for
// the given time; the first launch's results are the reference and every later launch is compared with them bit
// for bit. A difference is a computational error of the GPU (or its memory). One line per interval: launches,
// differing results so far, FP64 operations per second.
//
//   fp64burn <seconds> [<report interval s>]     exit 0: no difference; 1: differences; 2: CUDA error
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <cuda_runtime.h>

constexpr int CHAINS = 8, ITER = 8192;

__global__ void burn(double* out, double a, double b) {
    double x[CHAINS];
    const unsigned id = blockIdx.x * blockDim.x + threadIdx.x;
    for (int c = 0; c < CHAINS; c++) x[c] = 1.0 + 1e-7 * (double)((id * CHAINS + c) % 100003);
    for (int it = 0; it < ITER; it++) {
#pragma unroll
        for (int c = 0; c < CHAINS; c++) x[c] = x[c] * a + b;  // stays near b / (1 - a) = 1
    }
    double s = 0;
    for (int c = 0; c < CHAINS; c++) s = s + x[c];
    out[id] = s;
}

#define CK(x) do { cudaError_t e = (x); if (e != cudaSuccess) { fprintf(stderr, "CUDA error: %s (%s)\n", cudaGetErrorString(e), #x); return 2; } } while (0)

int main(int argc, char** argv) {
    if (argc < 2) { fprintf(stderr, "usage: fp64burn <seconds> [<report interval s>]\n"); return 2; }
    const double seconds = atof(argv[1]), every = argc > 2 ? atof(argv[2]) : 60.0;
    cudaDeviceProp p;
    CK(cudaGetDeviceProperties(&p, 0));
    const int threads = 256, blocks = p.multiProcessorCount * 32;
    const size_t n = (size_t)threads * blocks;
    printf("device: %s sm_%d%d, %d SMs, %zu threads, %d s\n", p.name, p.major, p.minor, p.multiProcessorCount, n, (int)seconds);
    double* d;
    CK(cudaMalloc(&d, n * sizeof(double)));
    std::vector<double> ref(n), cur(n);
    const double a = 0.999999, b = 1e-6;
    burn<<<blocks, threads>>>(d, a, b);
    CK(cudaGetLastError());
    CK(cudaMemcpy(ref.data(), d, n * sizeof(double), cudaMemcpyDeviceToHost));
    const double ops_per_launch = 2.0 * (double)n * ITER * CHAINS;  // one multiply and one add per step
    long long launches = 0, bad = 0, bad_launches = 0;
    auto t0 = std::chrono::steady_clock::now(), tr = t0;
    long long launches_r = 0;
    for (;;) {
        burn<<<blocks, threads>>>(d, a, b);
        CK(cudaGetLastError());
        CK(cudaMemcpy(cur.data(), d, n * sizeof(double), cudaMemcpyDeviceToHost));
        launches++; launches_r++;
        if (memcmp(cur.data(), ref.data(), n * sizeof(double)) != 0) {
            long long k = 0;
            for (size_t i = 0; i < n; i++) k += memcmp(&cur[i], &ref[i], sizeof(double)) != 0;
            bad += k; bad_launches++;
        }
        auto now = std::chrono::steady_clock::now();
        const double el = std::chrono::duration<double>(now - t0).count(), er = std::chrono::duration<double>(now - tr).count();
        if (er >= every || el >= seconds) {
            printf("t %7.0f s  launches %8lld  differing results %lld (in %lld launches)  %.3e FP64 ops/s\n", el, launches, bad, bad_launches,
                   ops_per_launch * launches_r / er);
            fflush(stdout);
            tr = now; launches_r = 0;
        }
        if (el >= seconds) break;
    }
    printf("== %s: %lld launches, %lld differing results\n", bad ? "DIFFERENCES" : "NO DIFFERENCE", launches, bad);
    cudaFree(d);
    return bad ? 1 : 0;
}
