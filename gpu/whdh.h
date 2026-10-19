// SPDX-License-Identifier: GPL-3.0-or-later
// Wisdom-Holman step in democratic heliocentric coordinates, for test
// particles on the GPU and for the planets and the CPU reference on the host.
// Written from the published methods only (see docs/gpu-integrator.md):
// Wisdom & Holman (1991), Duncan, Levison & Lee (1998) for the democratic
// heliocentric splitting, Rein & Tamayo (2015) for the universal-variable
// Kepler solver with Stumpff functions and Halley iterations, and the method
// description of Zhang & Gladman (2022, GLISSE) for test particles on a GPU
// with planet positions computed ahead in blocks and a Kepler solver with a
// fixed number of iterations.
//
// Coordinates: Q = position relative to the Sun, u = barycentric velocity.
// One step of length dt (h = dt/2), drift-kick-drift with the Kepler parts
// outside (Wisdom & Holman 1991; the default order of WHFast):
//   kepler(h)  Kepler orbit around G m_Sun for (Q, u)
//   jump(h)    Q += h * w_a,  w = (sum_j m_j u_j) / m_Sun     (planets' momentum)
//   kick(dt)   u += dt * sum_j G m_j (Q_j - Q) / |Q_j - Q|^3  (planets j, not the Sun)
//   jump(h)    Q += h * w_b
//   kepler(h)
// The two Kepler halves of consecutive steps are done as one Kepler step of
// dt: the state is kept half a drift ahead ("Y = kepler(h) X") and brought
// back to the synchronous state X with kepler(-h) for outputs and checks.
// (An earlier version used kick-drift-kick; its phase errors were twice as
// large, measured against IAS15.)
//
// Reproducibility: only + - * / and sqrt, all correctly rounded in IEEE-754
// binary64 on the CPU (-ffp-contract=off) and on NVIDIA GPUs (nvcc
// --fmad=false, -prec-div and -prec-sqrt are the default). The same code on
// both gives the same bits. Loops have fixed lengths where the data would
// otherwise make threads diverge (Kepler iterations).

#ifndef P9_WHDH_H
#define P9_WHDH_H

#ifdef __CUDACC__
#define P9_HD __host__ __device__ __forceinline__
#else
#include <math.h>
#define P9_HD static inline
#endif

#define P9_MAX_PLANETS 8
// Halley iterations of the Kepler solver. The start value is accurate to
// about (dt/P)^3; Halley converges cubically, so three iterations reach the
// rounding level for every orbit here (dt/P <= 1/24 for Jupiter, far less
// for the test particles). Fixed, so that threads do not diverge.
#define P9_KEPLER_ITERATIONS 3

typedef struct {
    double x, y, z, vx, vy, vz;
} p9_body;

// Stumpff functions c0..c3 of z = beta s^2. For |z| > 0.1 the argument is
// quartered until it is small, the series evaluated, and the results doubled
// back: c0(4z) = 2 c0^2 - 1, c1(4z) = c0 c1, c2(4z) = c1^2 / 2,
// c3(4z) = (c2 + c0 c3) / 4.
P9_HD void p9_stumpff(double z, double* c0, double* c1, double* c2, double* c3) {
    int n = 0;
    while (z > 0.1 || z < -0.1) {
        z *= 0.25;
        n++;
    }
    // multiplications by the reciprocals (rounded once, at compile time) instead
    // of divisions: a division costs many operations on a GPU
    double s3 = (1.0 / 6.0) * (1.0 - z * (1.0 / 20.0) * (1.0 - z * (1.0 / 42.0) * (1.0 - z * (1.0 / 72.0) * (1.0 - z * (1.0 / 110.0) * (1.0 - z * (1.0 / 156.0) * (1.0 - z * (1.0 / 210.0) * (1.0 - z * (1.0 / 272.0))))))));
    double s2 = 0.5 * (1.0 - z * (1.0 / 12.0) * (1.0 - z * (1.0 / 30.0) * (1.0 - z * (1.0 / 56.0) * (1.0 - z * (1.0 / 90.0) * (1.0 - z * (1.0 / 132.0) * (1.0 - z * (1.0 / 182.0) * (1.0 - z * (1.0 / 240.0))))))));
    double s1 = 1.0 - z * s3;
    double s0 = 1.0 - z * s2;
    for (; n > 0; n--) {
        const double n3 = 0.25 * (s2 + s0 * s3);
        const double n2 = 0.5 * s1 * s1;
        const double n1 = s0 * s1;
        const double n0 = 2.0 * s0 * s0 - 1.0;
        s0 = n0;
        s1 = n1;
        s2 = n2;
        s3 = n3;
    }
    *c0 = s0;
    *c1 = s1;
    *c2 = s2;
    *c3 = s3;
}

// Kepler drift of (Q, u) around gravitational parameter mu for time dt, in
// universal variables: solve r0 G1(s) + eta G2(s) + mu G3(s) = dt for s with
// G_n(s) = s^n c_n(beta s^2), then apply the f and g functions.
P9_HD void p9_kepler(p9_body* p, double mu, double dt) {
    const double x0 = p->x, y0 = p->y, z0 = p->z, vx0 = p->vx, vy0 = p->vy, vz0 = p->vz;
    const double r0 = sqrt(x0 * x0 + y0 * y0 + z0 * z0);
    const double ir0 = 1.0 / r0;
    const double eta = x0 * vx0 + y0 * vy0 + z0 * vz0;
    const double v2 = vx0 * vx0 + vy0 * vy0 + vz0 * vz0;
    const double beta = 2.0 * mu * ir0 - v2;
    const double zeta = mu - beta * r0;
    // second-order start value, then a fixed number of Halley iterations
    double s = dt * ir0 - 0.5 * eta * dt * dt * (ir0 * ir0 * ir0);
    double c0, c1, c2, c3;
    for (int it = 0; it < P9_KEPLER_ITERATIONS; it++) {
        p9_stumpff(beta * s * s, &c0, &c1, &c2, &c3);
        const double G1 = s * c1, G2 = s * s * c2, G3 = s * s * s * c3;
        const double F = r0 * G1 + eta * G2 + mu * G3 - dt;
        const double Fp = r0 * c0 + eta * G1 + mu * G2;
        const double Fpp = eta * c0 + zeta * G1;
        // Halley: s -= F / (Fp - F Fpp / (2 Fp)), written with one division
        s = s - F * Fp / (Fp * Fp - 0.5 * F * Fpp);
    }
    p9_stumpff(beta * s * s, &c0, &c1, &c2, &c3);
    const double G1 = s * c1, G2 = s * s * c2, G3 = s * s * s * c3;
    const double r = r0 * c0 + eta * G1 + mu * G2;
    const double ir = 1.0 / r;
    const double f = 1.0 - mu * G2 * ir0;
    const double g = dt - mu * G3;
    const double fd = -mu * G1 * ir * ir0;
    const double gd = 1.0 - mu * G2 * ir;
    p->x = f * x0 + g * vx0;
    p->y = f * y0 + g * vy0;
    p->z = f * z0 + g * vz0;
    p->vx = fd * x0 + gd * vx0;
    p->vy = fd * y0 + gd * vy0;
    p->vz = fd * z0 + gd * vz0;
}

// Kick of a test particle by the planets (positions q[3*j], G m_j in gm[j]).
// Returns the index of a planet closer than its encounter radius (squared in
// r2enc[j]; 0 = no check), or -1: the close-encounter criterion, evaluated at
// the kick, i.e. on the positions of the middle of the step.
P9_HD int p9_kick_tp(p9_body* p, const double* q, const double* gm, const double* r2enc, int np, double h) {
    double ax = 0.0, ay = 0.0, az = 0.0;
    int enc = -1;
    for (int j = 0; j < np; j++) {
        const double dx = q[3 * j] - p->x, dy = q[3 * j + 1] - p->y, dz = q[3 * j + 2] - p->z;
        const double d2 = dx * dx + dy * dy + dz * dz;
        if (d2 < r2enc[j] && enc < 0) enc = j;
        const double d = sqrt(d2);
        const double k = gm[j] / (d2 * d);
        ax += k * dx;
        ay += k * dy;
        az += k * dz;
    }
    p->vx += h * ax;
    p->vy += h * ay;
    p->vz += h * az;
    return enc;
}

P9_HD void p9_jump(p9_body* p, const double* w, double h) {
    p->x += h * w[0];
    p->y += h * w[1];
    p->z += h * w[2];
}

// One step of a test particle in the half-drift-ahead form: Y_k -> Y_{k+1}.
// q are the planets' positions at the kick, wa and wb the jump velocities.
// Returns the planet of a close encounter at the kick, or -1 (the step is completed either way).
P9_HD int p9_step_tp(p9_body* p, const double* q, const double* wa, const double* wb, const double* gm, const double* r2enc, int np, double mu0,
                     double dt) {
    const double h = 0.5 * dt;
    p9_jump(p, wa, h);
    const int enc = p9_kick_tp(p, q, gm, r2enc, np, dt);
    p9_jump(p, wb, h);
    p9_kepler(p, mu0, dt);
    return enc;
}

// The synchronous state of a body kept half a drift ahead.
P9_HD p9_body p9_synchronous(p9_body y, double mu0, double dt) {
    p9_kepler(&y, mu0, -0.5 * dt);
    return y;
}

#endif
