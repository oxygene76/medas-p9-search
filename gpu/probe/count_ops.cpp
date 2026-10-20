// SPDX-License-Identifier: GPL-3.0-or-later
// Counts the floating-point operations of one test-particle step of
// gpu/whdh_t.h (the code of the GPU kernel), by running it with a number type
// that counts. Typical test particles of the runs (a 150-550 au, perihelion
// 30-50 au) and the giant planets plus Planet Nine on circular orbits; the
// counts per step do not depend on the orbits except through the Stumpff
// argument reduction, which these orbits never need (|z| < 0.1).
//
//   build/probe/count_ops     -> operations per step and per synchronisation
#include <cmath>
#include <cstdio>
#include "whdh_t.h"

static unsigned long long n_add, n_mul, n_div, n_sqrt, n_cmp, n_neg;

struct C {
    double v;
};
inline C operator+(C a, C b) { return n_add++, C{a.v + b.v}; }
inline C operator-(C a, C b) { return n_add++, C{a.v - b.v}; }
inline C operator*(C a, C b) { return n_mul++, C{a.v * b.v}; }
inline C operator/(C a, C b) { return n_div++, C{a.v / b.v}; }
inline C operator-(C a) { return n_neg++, C{-a.v}; }
inline bool operator<(C a, C b) { return n_cmp++, a.v < b.v; }
inline bool operator>(C a, C b) { return n_cmp++, a.v > b.v; }
inline C& operator+=(C& a, C b) { return a = a + b; }
template <>
inline C L<C>(double c) { return C{c}; }
inline C p9_sqrt(C x) { return n_sqrt++, C{std::sqrt(x.v)}; }

static void reset() { n_add = n_mul = n_div = n_sqrt = n_cmp = n_neg = 0; }

int main() {
    const int np = 5, steps = 1000, ntp = 64;
    const double mu = 39.476926421373015 * 1.000005977, dt = 0.5;
    const double a_pl[np] = {5.2, 9.58, 19.2, 30.07, 380.0}, gm_pl[np] = {0.0377, 0.0113, 0.00172, 0.00203, 0.000735};
    C gm[np], r2[np], tab[np * 3 + 6];
    for (int j = 0; j < np; j++) gm[j] = C{gm_pl[j]}, r2[j] = C{0.25};
    double add = 0, mul = 0, div = 0, sq = 0, cmp = 0, neg = 0;
    for (int i = 0; i < ntp; i++) {
        const double a = 150.0 + 400.0 * i / ntp, q = 30.0 + 20.0 * ((i * 37) % ntp) / ntp, e = 1.0 - q / a, f = 2.399 * i;
        const double r = a * (1 - e * e) / (1 + e * std::cos(f)), v = std::sqrt(mu * (2 / r - 1 / a));
        p9t_body<C> p{C{r * std::cos(f)}, C{r * std::sin(f)}, C{0.1 * r}, C{-v * std::sin(f + 0.3)}, C{v * std::cos(f + 0.3)}, C{0.0}};
        for (int k = 0; k < steps; k++) {
            for (int j = 0; j < np; j++) {
                const double t = k * dt * std::sqrt(mu / std::pow(a_pl[j], 3));
                tab[3 * j] = C{a_pl[j] * std::cos(t + j)}, tab[3 * j + 1] = C{a_pl[j] * std::sin(t + j)}, tab[3 * j + 2] = C{0.0};
            }
            for (int m = 0; m < 6; m++) tab[np * 3 + m] = C{1e-4};
            reset();
            p9t_step_tp(&p, tab, tab + np * 3, tab + np * 3 + 3, gm, r2, np, C{mu}, C{dt});
            add += n_add, mul += n_mul, div += n_div, sq += n_sqrt, cmp += n_cmp, neg += n_neg;
        }
    }
    const double n = (double)ntp * steps;
    printf("per step (np=%d planets): add/sub %.2f mul %.2f div %.2f sqrt %.2f compare %.2f negate %.2f\n", np, add / n, mul / n, div / n, sq / n, cmp / n,
           neg / n);
    reset();
    p9t_body<C> p{C{100}, C{0}, C{0}, C{0}, C{0.6}, C{0}};
    p9t_synchronous(p, C{mu}, C{dt});
    printf("per synchronisation (every 1000 steps): add/sub %llu mul %llu div %llu sqrt %llu compare %llu\n", n_add, n_mul, n_div, n_sqrt, n_cmp);
    return 0;
}
