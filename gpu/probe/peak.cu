// SPDX-License-Identifier: GPL-3.0-or-later
// Throughput of the GPU for the operations of the integrator, separately:
// add, mul (not fused: built with --fmad=false like p9gpu), div, sqrt, in
// double and in float. Many threads, 8 independent chains per thread.
//
//   build/probe/peak        -> operations per second
#include <cstdio>
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

template <class T, int OP>
static double rate(int blocks, int threads, const char* name) {
    T* out;
    cudaMalloc(&out, sizeof(T) * blocks * threads);
    const T a = (T)(OP == 1 ? 1.0000001 : 1e-9), b = (T)1.0;
    k<T, OP><<<blocks, threads>>>(out, a, b);  // warm-up
    cudaEvent_t e0, e1;
    cudaEventCreate(&e0), cudaEventCreate(&e1);
    cudaEventRecord(e0);
    const int reps = 5;
    for (int r = 0; r < reps; r++) k<T, OP><<<blocks, threads>>>(out, a, b);
    cudaEventRecord(e1);
    cudaEventSynchronize(e1);
    float ms;
    cudaEventElapsedTime(&ms, e0, e1);
    cudaFree(out);
    const double ops = (double)reps * blocks * threads * ITER * CHAINS;
    printf("%-14s %10.3e ops/s\n", name, ops / (ms * 1e-3));
    return ops / (ms * 1e-3);
}

int main() {
    cudaDeviceProp p;
    cudaGetDeviceProperties(&p, 0);
    const int threads = 256, blocks = p.multiProcessorCount * 32;
    printf("device: %s sm_%d%d, %d SMs\n", p.name, p.major, p.minor, p.multiProcessorCount);
    rate<double, 0>(blocks, threads, "double add");
    rate<double, 1>(blocks, threads, "double mul");
    rate<double, 2>(blocks, threads, "double div");
    rate<double, 3>(blocks, threads, "double sqrt+add");
    rate<float, 0>(blocks, threads, "float add");
    rate<float, 1>(blocks, threads, "float mul");
    rate<float, 2>(blocks, threads, "float div");
    rate<float, 3>(blocks, threads, "float sqrt+add");
    return 0;
}
