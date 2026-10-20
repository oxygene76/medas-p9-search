// SPDX-License-Identifier: GPL-3.0-or-later
// The test-particle integrator over the number type T on the CPU: the
// reference for the GPU kernel p9_advance_t (gpu/kernel.cu), the same code
// (gpu/whdh_t.h) in the same order. Build with -ffp-contract=off.
#include <cstring>
#include "p9gpu_real.h"
#include "whdh_t.h"

extern "C" int p9_real_parse(const char* text) {
    if (!text || !*text || !strcmp(text, "double")) return P9_REAL_DOUBLE;
    if (!strcmp(text, "double-t")) return P9_REAL_DOUBLE_T;
    if (!strcmp(text, "float")) return P9_REAL_FLOAT;
    if (!strcmp(text, "df64")) return P9_REAL_DF64;
    return -1;
}

extern "C" const char* p9_real_name(int real) {
    static const char* names[] = {"double", "double-t", "float", "df64"};
    return real >= 0 && real < 4 ? names[real] : "?";
}

template <class T>
static void block(p9_body* tp, int* alive, int ntp, int np, const double* gm, const double* r2enc, const double* r2col, double mu0, const double* tab,
                  int nb, unsigned long long step0, double dt, int check_every, double rin2, double rout2, int smooth) {
    const size_t n = (size_t)nb * np * 9 + (size_t)nb * 6;  // q, wa, wb, uq, uqb (p9gpu.c planets_block)
    T* t = new T[n];
    for (size_t i = 0; i < n; i++) t[i] = L<T>(tab[i]);
    T g[P9_MAX_PLANETS], r2[P9_MAX_PLANETS], rc[P9_MAX_PLANETS];
    for (int j = 0; j < np; j++) g[j] = L<T>(gm[j]), r2[j] = L<T>(r2enc[j]), rc[j] = L<T>(r2col[j]);
    const T* q = t;
    const T* wa = t + (size_t)nb * np * 3;
    const T* wb = wa + (size_t)nb * 3;
    const T* uq = wb + (size_t)nb * 3;
    const T* uqb = uq + (size_t)nb * np * 3;
    const T tdt = L<T>(dt), tmu = L<T>(mu0), tin = L<T>(rin2), tout = L<T>(rout2);
    for (int i = 0; i < ntp; i++) {
        if (alive[i] != 1) continue;
        p9t_body<T> p = p9t_load<T>(tp[i]);
        int a = 1;
        for (int k = 0; k < nb; k++) {
            int ns;
            const int enc = smooth ? p9t_step_tp_smooth(&p, q + (size_t)k * np * 3, uq + (size_t)k * np * 3, uqb + (size_t)k * np * 3, wa + 3 * k,
                                                        wb + 3 * k, g, r2, rc, np, tmu, tdt, &ns)
                                   : p9t_step_tp(&p, q + (size_t)k * np * 3, wa + 3 * k, wb + 3 * k, g, r2, np, tmu, tdt);
            if (enc >= 0) {
                a = -1 - enc;
                break;
            }
            if ((step0 + k + 1) % (unsigned long long)check_every == 0) {
                const p9t_body<T> x = p9t_synchronous(p, tmu, tdt);
                const T rr = x.x * x.x + x.y * x.y + x.z * x.z;
                if (rr > tout || rr < tin) {
                    a = 0;
                    break;
                }
            }
        }
        tp[i] = p9t_store(p);
        alive[i] = a;
    }
    delete[] t;
}

extern "C" void p9_cpu_block_t(int real, p9_body* tp, int* alive, int ntp, int np, const double* gm, const double* r2enc, const double* r2col,
                               double mu0, const double* tab, int nb, unsigned long long step0, double dt, int check_every, double rin2, double rout2,
                               int smooth) {
    switch (real) {
        case P9_REAL_DOUBLE_T: block<double>(tp, alive, ntp, np, gm, r2enc, r2col, mu0, tab, nb, step0, dt, check_every, rin2, rout2, smooth); break;
        case P9_REAL_FLOAT: block<float>(tp, alive, ntp, np, gm, r2enc, r2col, mu0, tab, nb, step0, dt, check_every, rin2, rout2, smooth); break;
        case P9_REAL_DF64: block<df64>(tp, alive, ntp, np, gm, r2enc, r2col, mu0, tab, nb, step0, dt, check_every, rin2, rout2, smooth); break;
    }
}
