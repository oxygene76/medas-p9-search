// SPDX-License-Identifier: GPL-3.0-or-later
// C interface between the host program (p9gpu.c) and the CUDA part (kernel.cu).
#ifndef P9GPU_API_H
#define P9GPU_API_H
#include "whdh.h"
#include "p9gpu_real.h"
#ifdef __cplusplus
extern "C" {
#endif
typedef struct p9g p9g;
// Uploads the test particles; max_nb is the largest block (steps per launch).
// r2enc: squared close-encounter radii of the planets (0: no check).
// real: the number type of the kernel (P9_REAL_*, p9gpu_real.h).
p9g* p9g_create(int ntp, const p9_body* st, const int* alive, int np, const double* gm, const double* r2enc, int max_nb, int real, char* err,
                int errlen);
const char* p9g_name(p9g* g);
// Model "j2" (whdh.h): j2[0] = mu J2 R^2, j2[1..3] = axis, j2[4] = r_remove^2.
int p9g_set_j2(p9g* g, const double* j2, char* err, int errlen);
// Host table to fill for the next launch (pinned memory; waits for its last upload).
double* p9g_next_table(p9g* g);
// Uploads that table and starts the block of nb steps (steps step0+1 .. step0+nb); returns at once.
int p9g_launch(p9g* g, int nb, unsigned long long step0, double dt, double mu0, int check_every, double rin2, double rout2, char* err, int errlen);
// Waits for the GPU and copies the test particles back.
int p9g_download(p9g* g, p9_body* st, int* alive, char* err, int errlen);
void p9g_free(p9g* g);
#ifdef __cplusplus
}
#endif
#endif
