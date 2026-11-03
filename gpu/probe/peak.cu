// SPDX-License-Identifier: GPL-3.0-or-later
// Throughput of the GPU for the operations of the integrator, separately:
// add, mul (not fused: built with --fmad=false like p9gpu), div, sqrt, in
// double and in float. Many threads, 8 independent chains per thread.
//
//   build/probe/peak                    -> operations per second (one warm-up launch, then 5 launches per operation)
//   build/probe/peak <warm-up s> <window s>
//       first the double-add kernel without pause for <warm-up s>, so the clocks are up before the first
//       measurement; then each operation is measured over at least <window s>, and its line ends with the window
//       in Unix time (UTC, ms), so a clock log can be matched to it (added 2026-11-03 for the A100 acceptance test)
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cuda_runtime.h>

constexpr int CHAINS = 8, ITER = 4096;

template <class T, int OP>
__global__ void k(T* out, T a, T b) {
    T x[CHAINS];
    for (int c = 0; c < CHAINS; c++) x[c] = (T)(1.0 + 1e-3 * (threadIdx.x + c));
    for (int it = 0; it < ITER; it++) {
#pragma unroll
        for (int c = 0; c < CHAINS; c++) {
            if (OP == 0) x[c] = x[c] + a;            // add
            if (OP == 1) x[c] = x[c] * a;            // mul
            if (OP == 2) x[c] = b / x[c];            // div (x stays near 1: b = 1)
            if (OP == 3) x[c] = sqrt(x[c] + a) ;     // sqrt and one add
        }
    }
    T s = 0;
    for (int c = 0; c < CHAINS; c++) s = s + x[c];
    out[blockIdx.x * blockDim.x + threadIdx.x] = s;
}

static double now_unix() {
    return std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();
}

template <class T, int OP>
static double rate(int blocks, int threads, const char* name, double window = 0) {
    T* out;
    cudaMalloc(&out, sizeof(T) * blocks * threads);
    const T a = (T)(OP == 1 ? 1.0000001 : 1e-9), b = (T)1.0;
    k<T, OP><<<blocks, threads>>>(out, a, b);  // warm-up
    cudaEvent_t e0, e1;
    cudaEventCreate(&e0), cudaEventCreate(&e1);
    int reps = 5;
    float ms;
    if (window > 0) {  // as many launches as fill the window (one timed launch gives the length)
        cudaEventRecord(e0);
        k<T, OP><<<blocks, threads>>>(out, a, b);
        cudaEventRecord(e1);
        cudaEventSynchronize(e1);
        cudaEventElapsedTime(&ms, e0, e1);
        reps = std::max(5, (int)std::ceil(window / (ms * 1e-3)));
    }
    const double t0 = now_unix();
    cudaEventRecord(e0);
    for (int r = 0; r < reps; r++) k<T, OP><<<blocks, threads>>>(out, a, b);
    cudaEventRecord(e1);
    cudaEventSynchronize(e1);
    const double t1 = now_unix();
    cudaEventElapsedTime(&ms, e0, e1);
    cudaFree(out);
    const double ops = (double)reps * blocks * threads * ITER * CHAINS;
    if (window > 0) printf("%-14s %10.3e ops/s  window %.3f %.3f  launches %d\n", name, ops / (ms * 1e-3), t0, t1, reps);
    else printf("%-14s %10.3e ops/s\n", name, ops / (ms * 1e-3));
    return ops / (ms * 1e-3);
}

int main(int argc, char** argv) {
    const double warmup = argc > 1 ? atof(argv[1]) : 0, w = argc > 2 ? atof(argv[2]) : 0;
    cudaDeviceProp p;
    cudaGetDeviceProperties(&p, 0);
    const int threads = 256, blocks = p.multiProcessorCount * 32;
    printf("device: %s sm_%d%d, %d SMs\n", p.name, p.major, p.minor, p.multiProcessorCount);
    if (warmup > 0) {
        double* out;
        cudaMalloc(&out, sizeof(double) * blocks * threads);
        const double t0 = now_unix();
        long n = 0;
        while (now_unix() - t0 < warmup) {
            k<double, 0><<<blocks, threads>>>(out, 1e-9, 1.0);
            cudaDeviceSynchronize();
            n++;
        }
        cudaFree(out);
        printf("warm-up        %ld launches of double add, window %.3f %.3f\n", n, t0, now_unix());
    }
    rate<double, 0>(blocks, threads, "double add", w);
    rate<double, 1>(blocks, threads, "double mul", w);
    rate<double, 2>(blocks, threads, "double div", w);
    rate<double, 3>(blocks, threads, "double sqrt+add", w);
    rate<float, 0>(blocks, threads, "float add", w);
    rate<float, 1>(blocks, threads, "float mul", w);
    rate<float, 2>(blocks, threads, "float div", w);
    rate<float, 3>(blocks, threads, "float sqrt+add", w);
    return 0;
}
