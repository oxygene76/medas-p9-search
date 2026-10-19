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
#include <ctime>
#include <cuda_runtime.h>
#include "whdh.h"
#include "whdh_t.h"
#include "p9gpu_api.h"

__constant__ double c_gm[P9_MAX_PLANETS];
__constant__ double c_r2enc[P9_MAX_PLANETS];  // squared encounter radii (0: no check)
__constant__ double c_j2[5];                   // model "j2": mu J2 R^2, axis n, r_remove^2 (whdh.h)

// Table of a block of nb steps (layout shared with p9gpu.c):
//   q[nb * np * 3]          planets' positions relative to the Sun at the kick of each step
//   wa[nb * 3], wb[nb * 3]  jump velocities before and after the kick
// Particles are kept half a drift ahead (whdh.h). Status per particle: 1
// alive; 0 removed beyond R_OUT or within R_IN (checked every check_every
// steps on the synchronous state); -1-j removed at a close encounter with
// planet j (checked at every kick, see whdh.h).
__global__ void p9_advance(p9_body* __restrict__ st, int* __restrict__ alive, int ntp, const double* __restrict__ tab, int np, int nb,
                           unsigned long long step0, double dt, double mu0, int check_every, double rin2, double rout2) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= ntp || alive[i] != 1) return;
    const double* q = tab;
    const double* wa = tab + (size_t)nb * np * 3;
    const double* wb = wa + (size_t)nb * 3;
    p9_body p = st[i];
    int a = 1;
    for (int k = 0; k < nb; k++) {
        const int enc = p9_step_tp(&p, q + (size_t)k * np * 3, wa + 3 * k, wb + 3 * k, c_gm, c_r2enc, np, mu0, dt);
        if (enc >= 0) {
            a = -1 - enc;
            break;
        }
        if ((step0 + k + 1) % (unsigned long long)check_every == 0) {
            const p9_body x = p9_synchronous(p, mu0, dt);
            const double r2 = x.x * x.x + x.y * x.y + x.z * x.z;
            if (r2 > rout2 || r2 < rin2) {
                a = 0;
                break;
            }
        }
    }
    st[i] = p;
    alive[i] = a;
}

// The same kernel over the number type T (gpu/whdh_t.h; P9GPU_REAL, see
// p9gpu.c): the state stays double in memory and is converted at the start
// and end of a block (exact for df64), the table is converted once per block.
template <class T>
struct p9t_consts {
    T gm[P9_MAX_PLANETS], r2enc[P9_MAX_PLANETS];
};

template <class T>
__global__ void p9_convert(const double* __restrict__ src, T* __restrict__ dst, size_t n) {
    const size_t i = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) dst[i] = L<T>(src[i]);
}

template <class T>
__global__ void p9_advance_t(p9_body* __restrict__ st, int* __restrict__ alive, int ntp, const T* __restrict__ tab, int np, int nb,
                             unsigned long long step0, T dt, T mu0, int check_every, T rin2, T rout2, p9t_consts<T> c) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= ntp || alive[i] != 1) return;
    const T* q = tab;
    const T* wa = tab + (size_t)nb * np * 3;
    const T* wb = wa + (size_t)nb * 3;
    p9t_body<T> p = p9t_load<T>(st[i]);
    int a = 1;
    for (int k = 0; k < nb; k++) {
        const int enc = p9t_step_tp(&p, q + (size_t)k * np * 3, wa + 3 * k, wb + 3 * k, c.gm, c.r2enc, np, mu0, dt);
        if (enc >= 0) {
            a = -1 - enc;
            break;
        }
        if ((step0 + k + 1) % (unsigned long long)check_every == 0) {
            const p9t_body<T> x = p9t_synchronous(p, mu0, dt);
            const T r2 = x.x * x.x + x.y * x.y + x.z * x.z;
            if (r2 > rout2 || r2 < rin2) {
                a = 0;
                break;
            }
        }
    }
    st[i] = p9t_store(p);
    alive[i] = a;
}

// p9_advance with the J2 of the central body (model "j2", whdh.h; double only).
__global__ void p9_advance_j2(p9_body* __restrict__ st, int* __restrict__ alive, int ntp, const double* __restrict__ tab, int np, int nb,
                              unsigned long long step0, double dt, double mu0, int check_every, double rin2, double rout2) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= ntp || alive[i] != 1) return;
    const double* q = tab;
    const double* wa = tab + (size_t)nb * np * 3;
    const double* wb = wa + (size_t)nb * 3;
    p9_body p = st[i];
    int a = 1;
    for (int k = 0; k < nb; k++) {
        const int enc = p9_step_tp_j2(&p, q + (size_t)k * np * 3, wa + 3 * k, wb + 3 * k, c_gm, c_r2enc, np, mu0, dt, c_j2);
        if (enc >= 0) {
            a = -1 - enc;
            break;
        }
        if ((step0 + k + 1) % (unsigned long long)check_every == 0) {
            const p9_body x = p9_synchronous(p, mu0, dt);
            const double r2 = x.x * x.x + x.y * x.y + x.z * x.z;
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
    int ntp, np, max_nb, cur, real, j2;
    p9_body* d_st;
    int* d_alive;
    double* d_tab[2];
    double* h_tab[2];  // pinned
    void* d_tab_t;     // the table converted to T (P9GPU_REAL other than double)
    double gm[P9_MAX_PLANETS], r2enc[P9_MAX_PLANETS];
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

extern "C" p9g* p9g_create(int ntp, const p9_body* st, const int* alive, int np, const double* gm, const double* r2enc, int max_nb, int real,
                           char* err, int errlen) {
    p9g* g = (p9g*)calloc(1, sizeof(p9g));
    g->ntp = ntp;
    g->np = np;
    g->max_nb = max_nb;
    g->real = real;
    for (int j = 0; j < np; j++) g->gm[j] = gm[j], g->r2enc[j] = r2enc[j];
    g->tab_doubles = (size_t)max_nb * np * 3 + (size_t)max_nb * 6;
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
    if (real != P9_REAL_DOUBLE && fail(cudaMalloc(&g->d_tab_t, sizeof(double) * g->tab_doubles), "malloc table", err, errlen)) return NULL;
    if (fail(cudaMemcpyToSymbol(c_gm, gm, sizeof(double) * np), "gm", err, errlen)) return NULL;
    if (fail(cudaMemcpyToSymbol(c_r2enc, r2enc, sizeof(double) * np), "r2enc", err, errlen)) return NULL;
    if (ntp > 0) {
        if (fail(cudaMemcpy(g->d_st, st, sizeof(p9_body) * ntp, cudaMemcpyHostToDevice), "upload", err, errlen)) return NULL;
        if (fail(cudaMemcpy(g->d_alive, alive, sizeof(int) * ntp, cudaMemcpyHostToDevice), "upload", err, errlen)) return NULL;
    }
    return g;
}

extern "C" const char* p9g_name(p9g* g) { return g->name; }

extern "C" int p9g_set_j2(p9g* g, const double* j2, char* err, int errlen) {
    if (g->real != P9_REAL_DOUBLE) {
        snprintf(err, errlen, "model j2: double only");
        return 1;
    }
    g->j2 = 1;
    return fail(cudaMemcpyToSymbol(c_j2, j2, sizeof(double) * 5), "j2", err, errlen);
}

// Waiting without occupying a CPU core: CUDA's own waits spin, and with
// "blocking sync" the WSL2 driver still keeps a core busy in system calls.
// Polling with a 1 ms sleep costs at most 1 ms per block of steps.
static void nap(void) {
    struct timespec ts = {0, 1000000};
    nanosleep(&ts, NULL);
}
static cudaError_t wait_event(cudaEvent_t e) {
    cudaError_t r;
    while ((r = cudaEventQuery(e)) == cudaErrorNotReady) nap();
    return r;
}
static cudaError_t wait_stream(cudaStream_t s) {
    cudaError_t r;
    while ((r = cudaStreamQuery(s)) == cudaErrorNotReady) nap();
    return r;
}

// The host table to fill next; waits until its previous upload is done.
extern "C" double* p9g_next_table(p9g* g) {
    wait_event(g->copied[g->cur]);
    return g->h_tab[g->cur];
}

template <class T>
static void launch_t(p9g* g, int b, size_t n, int nb, unsigned long long step0, double dt, double mu0, int check_every, double rin2, double rout2) {
    T* tab = (T*)g->d_tab_t;
    p9_convert<T><<<(unsigned)((n + 255) / 256), 256, 0, g->stream>>>(g->d_tab[b], tab, n);
    p9t_consts<T> c;
    for (int j = 0; j < P9_MAX_PLANETS; j++) c.gm[j] = L<T>(g->gm[j]), c.r2enc[j] = L<T>(g->r2enc[j]);
    const int threads = 128;
    p9_advance_t<T><<<(g->ntp + threads - 1) / threads, threads, 0, g->stream>>>(g->d_st, g->d_alive, g->ntp, tab, g->np, nb, step0, L<T>(dt), L<T>(mu0),
                                                                                  check_every, L<T>(rin2), L<T>(rout2), c);
}

// Uploads the table filled last and launches the kernel; returns at once.
extern "C" int p9g_launch(p9g* g, int nb, unsigned long long step0, double dt, double mu0, int check_every, double rin2, double rout2, char* err,
                          int errlen) {
    const int b = g->cur;
    const size_t n = (size_t)nb * g->np * 3 + (size_t)nb * 6;
    // the table is packed for nb steps: q, then wa, then wb (p9gpu.c writes it that way)
    if (fail(cudaMemcpyAsync(g->d_tab[b], g->h_tab[b], sizeof(double) * n, cudaMemcpyHostToDevice, g->stream), "upload table", err, errlen)) return 1;
    if (fail(cudaEventRecord(g->copied[b], g->stream), "event", err, errlen)) return 1;
    if (g->ntp > 0) {
        const int threads = 128, blocks = (g->ntp + threads - 1) / threads;
        if (g->j2) {
            p9_advance_j2<<<blocks, threads, 0, g->stream>>>(g->d_st, g->d_alive, g->ntp, g->d_tab[b], g->np, nb, step0, dt, mu0, check_every, rin2,
                                                             rout2);
        } else switch (g->real) {
            case P9_REAL_DOUBLE:
                p9_advance<<<blocks, threads, 0, g->stream>>>(g->d_st, g->d_alive, g->ntp, g->d_tab[b], g->np, nb, step0, dt, mu0, check_every, rin2,
                                                              rout2);
                break;
            case P9_REAL_DOUBLE_T:
                launch_t<double>(g, b, n, nb, step0, dt, mu0, check_every, rin2, rout2);
                break;
            case P9_REAL_FLOAT:
                launch_t<float>(g, b, n, nb, step0, dt, mu0, check_every, rin2, rout2);
                break;
            case P9_REAL_DF64:
                launch_t<df64>(g, b, n, nb, step0, dt, mu0, check_every, rin2, rout2);
                break;
        }
        if (fail(cudaGetLastError(), "launch", err, errlen)) return 1;
    }
    g->cur ^= 1;
    return 0;
}

extern "C" int p9g_download(p9g* g, p9_body* st, int* alive, char* err, int errlen) {
    if (fail(wait_stream(g->stream), "kernel", err, errlen)) return 1;
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
    if (g->d_tab_t) cudaFree(g->d_tab_t);
    cudaFree(g->d_st);
    cudaFree(g->d_alive);
    cudaStreamDestroy(g->stream);
    free(g);
}
