// SPDX-License-Identifier: GPL-3.0-or-later
// GPU part of p9gpu: advances test particles over a block of steps whose
// planet positions and jump velocities the CPU computed beforehand.
// One thread per test particle; threads never interact (no atomics, no
// reductions), so the result does not depend on scheduling. Build with
// --fmad=false (see Makefile): with the same order of operations the GPU then
// rounds exactly as the CPU code in whdh.h.

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cuda_runtime.h>
#include "whdh.h"
#include "p9gpu_api.h"

__constant__ double c_gm[P9_MAX_PLANETS];

// Table of a block of nb steps (layout shared with p9gpu.c):
//   q[(nb+1) * np * 3]  planets' positions relative to the Sun at the step boundaries
//   wa[nb * 3], wb[nb * 3]  jump velocities before and after the Kepler step
__global__ void p9_advance(p9_body* __restrict__ st, int* __restrict__ alive, int ntp, const double* __restrict__ tab, int np, int nb,
                           unsigned long long step0, double dt, double mu0, int check_every, double rin2, double rout2) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= ntp || !alive[i]) return;
    const double* q = tab;
    const double* wa = tab + (size_t)(nb + 1) * np * 3;
    const double* wb = wa + (size_t)nb * 3;
    p9_body p = st[i];
    int a = 1;
    for (int k = 0; k < nb; k++) {
        p9_step_tp(&p, q + (size_t)k * np * 3, q + (size_t)(k + 1) * np * 3, wa + 3 * k, wb + 3 * k, c_gm, np, mu0, dt);
        if ((step0 + k + 1) % (unsigned long long)check_every == 0) {
            const double r2 = p.x * p.x + p.y * p.y + p.z * p.z;
            if (r2 > rout2 || r2 < rin2) {
                a = 0;
                break;
            }
        }
    }
    st[i] = p;
    alive[i] = a;
}

struct p9g {
    int ntp, np, max_nb, cur;
    p9_body* d_st;
    int* d_alive;
    double* d_tab[2];
    double* h_tab[2];  // pinned
    size_t tab_doubles;
    cudaStream_t stream;
    cudaEvent_t copied[2];
    char name[300];
};

static int fail(cudaError_t e, const char* what, char* err, int errlen) {
    if (e == cudaSuccess) return 0;
    if (err) snprintf(err, errlen, "%s: %s", what, cudaGetErrorString(e));
    return 1;
}

extern "C" p9g* p9g_create(int ntp, const p9_body* st, const int* alive, int np, const double* gm, int max_nb, char* err, int errlen) {
    p9g* g = (p9g*)calloc(1, sizeof(p9g));
    g->ntp = ntp;
    g->np = np;
    g->max_nb = max_nb;
    g->tab_doubles = (size_t)(max_nb + 1) * np * 3 + (size_t)max_nb * 6;
    // The host thread sleeps while it waits for the GPU (no busy-waiting on a CPU core).
    if (fail(cudaSetDeviceFlags(cudaDeviceScheduleBlockingSync), "device flags", err, errlen)) return NULL;
    cudaDeviceProp prop;
    if (fail(cudaGetDeviceProperties(&prop, 0), "device", err, errlen)) return NULL;
    snprintf(g->name, sizeof g->name, "%s sm_%d%d", prop.name, prop.major, prop.minor);
    if (fail(cudaStreamCreate(&g->stream), "stream", err, errlen)) return NULL;
    if (fail(cudaMalloc(&g->d_st, sizeof(p9_body) * (ntp > 0 ? ntp : 1)), "malloc st", err, errlen)) return NULL;
    if (fail(cudaMalloc(&g->d_alive, sizeof(int) * (ntp > 0 ? ntp : 1)), "malloc alive", err, errlen)) return NULL;
    for (int b = 0; b < 2; b++) {
        if (fail(cudaMalloc(&g->d_tab[b], sizeof(double) * g->tab_doubles), "malloc table", err, errlen)) return NULL;
        if (fail(cudaMallocHost(&g->h_tab[b], sizeof(double) * g->tab_doubles), "pinned table", err, errlen)) return NULL;
        if (fail(cudaEventCreateWithFlags(&g->copied[b], cudaEventDisableTiming), "event", err, errlen)) return NULL;
        if (fail(cudaEventRecord(g->copied[b], g->stream), "event", err, errlen)) return NULL;
    }
    if (fail(cudaMemcpyToSymbol(c_gm, gm, sizeof(double) * np), "gm", err, errlen)) return NULL;
    if (ntp > 0) {
        if (fail(cudaMemcpy(g->d_st, st, sizeof(p9_body) * ntp, cudaMemcpyHostToDevice), "upload", err, errlen)) return NULL;
        if (fail(cudaMemcpy(g->d_alive, alive, sizeof(int) * ntp, cudaMemcpyHostToDevice), "upload", err, errlen)) return NULL;
    }
    return g;
}

extern "C" const char* p9g_name(p9g* g) { return g->name; }

// The host table to fill next; waits until its previous upload is done.
extern "C" double* p9g_next_table(p9g* g) {
    cudaEventSynchronize(g->copied[g->cur]);
    return g->h_tab[g->cur];
}

// Uploads the table filled last and launches the kernel; returns at once.
extern "C" int p9g_launch(p9g* g, int nb, unsigned long long step0, double dt, double mu0, int check_every, double rin2, double rout2, char* err,
                          int errlen) {
    const int b = g->cur;
    const size_t n = (size_t)(nb + 1) * g->np * 3 + (size_t)nb * 6;
    // the table is packed for nb steps: q, then wa, then wb (p9gpu.c writes it that way)
    if (fail(cudaMemcpyAsync(g->d_tab[b], g->h_tab[b], sizeof(double) * n, cudaMemcpyHostToDevice, g->stream), "upload table", err, errlen)) return 1;
    if (fail(cudaEventRecord(g->copied[b], g->stream), "event", err, errlen)) return 1;
    if (g->ntp > 0) {
        const int threads = 128;
        p9_advance<<<(g->ntp + threads - 1) / threads, threads, 0, g->stream>>>(g->d_st, g->d_alive, g->ntp, g->d_tab[b], g->np, nb, step0, dt, mu0,
                                                                                 check_every, rin2, rout2);
        if (fail(cudaGetLastError(), "launch", err, errlen)) return 1;
    }
    g->cur ^= 1;
    return 0;
}

extern "C" int p9g_download(p9g* g, p9_body* st, int* alive, char* err, int errlen) {
    if (fail(cudaStreamSynchronize(g->stream), "kernel", err, errlen)) return 1;
    if (g->ntp == 0) return 0;
    if (fail(cudaMemcpy(st, g->d_st, sizeof(p9_body) * g->ntp, cudaMemcpyDeviceToHost), "download", err, errlen)) return 1;
    if (fail(cudaMemcpy(alive, g->d_alive, sizeof(int) * g->ntp, cudaMemcpyDeviceToHost), "download", err, errlen)) return 1;
    return 0;
}

extern "C" void p9g_free(p9g* g) {
    if (!g) return;
    cudaStreamSynchronize(g->stream);
    for (int b = 0; b < 2; b++) {
        cudaFree(g->d_tab[b]);
        cudaFreeHost(g->h_tab[b]);
        cudaEventDestroy(g->copied[b]);
    }
    cudaFree(g->d_st);
    cudaFree(g->d_alive);
    cudaStreamDestroy(g->stream);
    free(g);
}
