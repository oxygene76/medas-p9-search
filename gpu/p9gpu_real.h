// SPDX-License-Identifier: GPL-3.0-or-later
// Number type of p9gpu's test-particle integrator (environment P9GPU_REAL,
// set by tools/p9job.py from the job's params.real):
//   double     gpu/whdh.h, the production code (default)
//   double-t   gpu/whdh_t.h with double: must give the same bits as "double"
//   float      gpu/whdh_t.h with binary32: a speed probe, not for runs
//   df64       gpu/whdh_t.h with double-float (gpu/df64.h)
// The test particles are integrated in that type; the planets, the
// conversions and the outputs stay double.
#ifndef P9GPU_REAL_H
#define P9GPU_REAL_H
#include "whdh.h"
enum { P9_REAL_DOUBLE = 0, P9_REAL_DOUBLE_T = 1, P9_REAL_FLOAT = 2, P9_REAL_DF64 = 3 };
// Flyby records of the encounter method "step" (p9gpu_api.h p9g_counts, p9gpu.c).
typedef struct {
    int *near, *fast, *close, *last_j;
    unsigned long long *last_step, *rm_step;
    double* last_d;
    int *sub_steps, *sub_max, *sub_capped;  // method substep: steps with sub-steps, largest n, steps at P9_SUB_MAX
} p9_flybys;
#ifdef __cplusplus
extern "C" {
#endif
// The type named by text (NULL or "": double); -1 for an unknown name.
int p9_real_parse(const char* text);
const char* p9_real_name(int real);
// One block of steps on the CPU in the given type (gpu/cpu_t.cpp), as the
// kernel does it: the same bits as the GPU.
void p9_cpu_block_t(int real, p9_body* tp, int* alive, int ntp, int np, const double* gm, const double* r2enc, double mu0, const double* tab, int nb,
                    unsigned long long step0, double dt, int check_every, double rin2, double rout2);
#ifdef __cplusplus
}
#endif
#endif
