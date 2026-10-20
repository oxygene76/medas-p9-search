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

// Encounter method "step" (since 2026-10-19 evening, docs/close-encounters.md):
// instead of the distance at the kick, the closest approach within the step,
// from the relative position d (planet minus particle) and relative velocity w
// at the kick: d(tau) = d + w tau for tau in [-dt/2, dt/2] around the kick (in
// democratic heliocentric coordinates the relative velocity is the difference
// of the barycentric velocities; the jump term cancels). Removal when that
// closest distance is below the planet's radius, so that no particle passes
// through the sphere between two kicks. Also counts, per planet, the closest
// approaches that fall into this step (tau* in (-dt/2, dt/2]) within three
// removal radii (near[j]), among them those with d_min / (|w| dt) < 1.5,
// shorter than 1.5 steps (fast[j]), and those closer than 0.1 au (close[j]);
// a flyby shorter than 1.5 steps also sets *fast_j (planet) and *fast_d
// (closest distance). The counters may be NULL (then nothing is counted).
P9_HD int p9_kick_tp_step(p9_body* p, const double* q, const double* uq, const double* gm, const double* r2enc, int np, double h, double dt,
                          int* near, int* fast, int* close, int* fast_j, double* fast_d) {
    double ax = 0.0, ay = 0.0, az = 0.0;
    int enc = -1;
    for (int j = 0; j < np; j++) {
        const double dx = q[3 * j] - p->x, dy = q[3 * j + 1] - p->y, dz = q[3 * j + 2] - p->z;
        const double d2 = dx * dx + dy * dy + dz * dz;
        if (r2enc[j] > 0.0) {
            const double wx = uq[3 * j] - p->vx, wy = uq[3 * j + 1] - p->vy, wz = uq[3 * j + 2] - p->vz;
            const double w2 = wx * wx + wy * wy + wz * wz;
            const double dw = dx * wx + dy * wy + dz * wz;
            double tau = w2 > 0.0 ? -dw / w2 : 0.0;
            const int inside = tau > -0.5 * dt && tau <= 0.5 * dt;
            if (tau < -0.5 * dt) tau = -0.5 * dt;
            if (tau > 0.5 * dt) tau = 0.5 * dt;
            const double ex = dx + wx * tau, ey = dy + wy * tau, ez = dz + wz * tau;
            const double m2 = ex * ex + ey * ey + ez * ez;
            if (m2 < r2enc[j] && enc < 0) enc = j;
            if (inside && near && m2 < 9.0 * r2enc[j]) {
                near[j]++;
                if (m2 < 0.01) close[j]++;
                // d_min / (|w| dt) < 1.5  <=>  m2 < 2.25 w2 dt^2
                if (m2 < 2.25 * w2 * dt * dt) {
                    fast[j]++;
                    *fast_j = j;
                    *fast_d = sqrt(m2);
                }
            }
        }
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

// J2 of the central body (model "j2": the Sun with Jupiter, Saturn and Uranus
// absorbed, Batygin & Brown 2016, AJ 151, 22, sec. 5.2). Potential of the
// quadrupole Phi = mu J2 R^2 (3 s^2 - r^2) / (2 r^5), s = r . n with n the
// unit axis (the absorbed planets' total angular momentum); acceleration
// -grad Phi = 3/2 mu J2 R^2 / r^5 ((5 s^2 / r^2 - 1) r - 2 s n), with r the
// position relative to the Sun (democratic heliocentric: a function of Q only,
// so it belongs to the kick). j2[0] = mu J2 R^2, j2[1..3] = n.
P9_HD void p9_j2_acc(double x, double y, double z, const double* j2, double* ax, double* ay, double* az) {
    const double r2 = x * x + y * y + z * z;
    const double ir2 = 1.0 / r2;
    const double ir5 = ir2 * ir2 / sqrt(r2);
    const double s = x * j2[1] + y * j2[2] + z * j2[3];
    const double k = 1.5 * j2[0] * ir5;
    const double c = 5.0 * s * s * ir2 - 1.0;
    const double t = 2.0 * s;
    *ax += k * (c * x - t * j2[1]);
    *ay += k * (c * y - t * j2[2]);
    *az += k * (c * z - t * j2[3]);
}

// Kick with the J2 of the central body; also returns np (one past the planets)
// when the particle is within r_remove of the Sun (j2[4] = r_remove^2): there,
// among the absorbed planets, the model does not hold (Batygin & Brown 2016
// removed perihelia inside Uranus' orbit).
P9_HD int p9_kick_tp_j2(p9_body* p, const double* q, const double* gm, const double* r2enc, int np, double h, const double* j2) {
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
    if (p->x * p->x + p->y * p->y + p->z * p->z < j2[4] && enc < 0) enc = np;
    p9_j2_acc(p->x, p->y, p->z, j2, &ax, &ay, &az);
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

// p9_step_tp with the J2 of the central body (model "j2").
P9_HD int p9_step_tp_j2(p9_body* p, const double* q, const double* wa, const double* wb, const double* gm, const double* r2enc, int np, double mu0,
                        double dt, const double* j2) {
    const double h = 0.5 * dt;
    p9_jump(p, wa, h);
    const int enc = p9_kick_tp_j2(p, q, gm, r2enc, np, dt, j2);
    p9_jump(p, wb, h);
    p9_kepler(p, mu0, dt);
    return enc;
}

// p9_step_tp with the encounter method "step" (uq: the planets' barycentric velocities at the kick).
P9_HD int p9_step_tp_step(p9_body* p, const double* q, const double* uq, const double* wa, const double* wb, const double* gm, const double* r2enc,
                          int np, double mu0, double dt, int* near, int* fast, int* close, int* fast_j, double* fast_d) {
    const double h = 0.5 * dt;
    p9_jump(p, wa, h);
    const int enc = p9_kick_tp_step(p, q, uq, gm, r2enc, np, dt, dt, near, fast, close, fast_j, fast_d);
    p9_jump(p, wb, h);
    p9_kepler(p, mu0, dt);
    return enc;
}

// ------------------------------------------------------------------ sub-steps (method "substep")
// docs/substeps-plan.md. A step whose predicted closest approach to a planet
// is too close or too short gets n sub-steps of dt/n, for this particle only.
// Trigger (at the start of the step, from the particle's position at the kick
// and the planet's position and velocity there; linear approximation, as a
// comparison of squared distances): closest distance below the planet's
// trigger radius (r2trig[j]) or a flyby shorter than 2 steps. n: the smallest
// power of two (at most P9_SUB_MAX) with which the flyby lasts at least 8
// sub-steps and the orbit around the planet at that distance at least 164
// sub-steps (d^3 >= (164 / (2 pi))^2 (dt/n)^2 G m_j), the accuracy of the
// radius rule; for a slow flyby the distance and speed at the pericentre of
// the two-body orbit around the planet (gravitational focusing), where that is
// closer than the straight line. Only + - * / and sqrt: CPU and GPU decide
// alike. The planets' own accuracy matters as much (docs/substeps-plan.md):
// the method is meant for P9_PLANET_SUBSTEPS=8 (p9gpu.c).
// The sub-steps: the particle back to the synchronous state, then
// drift-kick-drift with dt/n; the planets at each sub-step's kick from their
// state at the step's kick, drifted on two-body orbits around the Sun (as
// RMVS, Levison & Duncan 1994), to second order: from the planet's position q
// at the kick and its mean velocity across the kick (uq before, uqb after it)
// a Kepler drift over t, plus a t^2 / 2 with a = (uqb - uq) / dt (the
// planets' pull on each other), plus the jump term of democratic
// heliocentric coordinates, t w with w = sum m_j u_j / m_0 (the Sun's
// barycentric motion, about 3e-3 au/yr). Each of the last two moves a planet
// by up to 1e-4 to 1e-3 au over half a step, which changes the kick of a slow
// close flyby by per cents. The particle's jump from the planets' velocities
// there (u = Kepler velocity + a t).
#define P9_SUB_MAX 4096
#define P9_SUB_ORBIT 681.3  // (164 / (2 pi))^2, rounded up
// The general form: the flyby lasts at least k sub-steps (k2 = k^2) and the orbit around the planet
// at least 164 sqrt(orb) of them.
P9_HD int p9_sub_n_k(double m2, double w2, double gm, double dt, double k2, double orb) {
    if (!(m2 > 0.0)) return P9_SUB_MAX;
    const double d3 = m2 * sqrt(m2);
    int n = 1;
    for (; n < P9_SUB_MAX; n *= 2) {
        const double s = dt / n;  // dt over a power of two: exact
        if (m2 >= k2 * w2 * s * s && d3 >= orb * P9_SUB_ORBIT * s * s * gm) break;
    }
    return n;
}
P9_HD int p9_sub_n(double m2, double w2, double gm, double dt) { return p9_sub_n_k(m2, w2, gm, dt, 64.0, 1.0); }

// One step with sub-steps where needed. Counts as p9_kick_tp_step (near, fast,
// close, *fast_j, *fast_d; counters may be NULL); *nsub: the sub-steps used (1:
// none). Nothing is removed at the planets. Returns -1.
P9_HD int p9_step_tp_sub(p9_body* p, const double* q, const double* uq, const double* uqb, const double* wa, const double* wb, const double* gm,
                         const double* r2trig,
                         int np, double mu0, double dt, int* near, int* fast, int* close, int* fast_j, double* fast_d, int* nsub) {
    const double h = 0.5 * dt;
    // the particle at the kick (after the first jump), as the step would have it
    const double xk = p->x + h * wa[0], yk = p->y + h * wa[1], zk = p->z + h * wa[2];
    int n = 1;
    for (int j = 0; j < np; j++) {
        if (r2trig[j] <= 0.0) continue;
        const double dx = q[3 * j] - xk, dy = q[3 * j + 1] - yk, dz = q[3 * j + 2] - zk;
        const double wx = uq[3 * j] - p->vx, wy = uq[3 * j + 1] - p->vy, wz = uq[3 * j + 2] - p->vz;
        const double w2 = wx * wx + wy * wy + wz * wz;
        const double dw = dx * wx + dy * wy + dz * wz;
        double tau = w2 > 0.0 ? -dw / w2 : 0.0;
        const int inside = tau > -h && tau <= h;
        if (tau < -h) tau = -h;
        if (tau > h) tau = h;
        const double ex = dx + wx * tau, ey = dy + wy * tau, ez = dz + wz * tau;
        const double m2 = ex * ex + ey * ey + ez * ez;
        if (inside && near && m2 < 9.0 * r2trig[j]) {
            near[j]++;
            if (m2 < 0.01) close[j]++;
            if (m2 < 2.25 * w2 * dt * dt) {
                fast[j]++;
                *fast_j = j;
                *fast_d = sqrt(m2);
            }
        }
        if (m2 < r2trig[j] || m2 < 4.0 * w2 * dt * dt) {
            // gravitational focusing: the pericentre q of the two-body orbit around the planet
            // (from distance and relative velocity at the kick) and the speed there; the
            // straight line overestimates the closest distance of a slow flyby
            const double d2 = dx * dx + dy * dy + dz * dz;
            const double r = sqrt(d2), mu = gm[j];
            const double cx = dy * wz - dz * wy, cy = dz * wx - dx * wz, cz = dx * wy - dy * wx;
            const double L2 = cx * cx + cy * cy + cz * cz;
            const double en = 0.5 * w2 - mu / r;
            double e2 = 1.0 + 2.0 * en * L2 / (mu * mu);
            if (e2 < 0.0) e2 = 0.0;
            const double qp = L2 / mu / (1.0 + sqrt(e2));
            double m2e = m2, w2e = w2;
            if (qp * qp < m2e) {
                m2e = qp * qp;
                w2e = 2.0 * en + 2.0 * mu / qp;  // vis-viva at the pericentre
            }
            const int nj = p9_sub_n(m2e, w2e > w2 ? w2e : w2, gm[j], dt);
            if (nj > n) n = nj;
        }
    }
    *nsub = n;
    double none[P9_MAX_PLANETS];
    for (int j = 0; j < np; j++) none[j] = 0.0;
    if (n == 1) return p9_step_tp(p, q, wa, wb, gm, none, np, mu0, dt);
    // sub-steps: from the synchronous state at the step's start
    p9_body x = *p;
    p9_kepler(&x, mu0, -h);
    const double s = dt / n, hs = 0.5 * s;
    double wk[3] = {0.0, 0.0, 0.0}, um[3 * P9_MAX_PLANETS], ac[3 * P9_MAX_PLANETS];
    for (int c = 0; c < 3 * np; c++) um[c] = 0.5 * (uq[c] + uqb[c]), ac[c] = (uqb[c] - uq[c]) / dt;
    for (int j = 0; j < np; j++) wk[0] += gm[j] * um[3 * j], wk[1] += gm[j] * um[3 * j + 1], wk[2] += gm[j] * um[3 * j + 2];
    wk[0] = wk[0] / mu0, wk[1] = wk[1] / mu0, wk[2] = wk[2] / mu0;  // jump velocity at the step's kick
    p9_kepler(&x, mu0, hs);
    for (int k = 0; k < n; k++) {
        const double t = (k + 0.5) * s - h;  // this sub-step's kick, relative to the step's kick (never 0: n is even)
        double qs[3 * P9_MAX_PLANETS], ws[3];
        double px = 0.0, py = 0.0, pz = 0.0;
        for (int j = 0; j < np; j++) {
            p9_body b = {q[3 * j], q[3 * j + 1], q[3 * j + 2], um[3 * j], um[3 * j + 1], um[3 * j + 2]};
            p9_kepler(&b, mu0, t);
            const double t2 = 0.5 * t * t;
            qs[3 * j] = b.x + t2 * ac[3 * j], qs[3 * j + 1] = b.y + t2 * ac[3 * j + 1], qs[3 * j + 2] = b.z + t2 * ac[3 * j + 2];
            px += gm[j] * (b.vx + t * ac[3 * j]), py += gm[j] * (b.vy + t * ac[3 * j + 1]), pz += gm[j] * (b.vz + t * ac[3 * j + 2]);
        }
        ws[0] = px / mu0, ws[1] = py / mu0, ws[2] = pz / mu0;
        // the jump of the planets' heliocentric positions from the kick to t: trapezoid of w
        for (int j = 0; j < np; j++)
            for (int c = 0; c < 3; c++) qs[3 * j + c] += t * 0.5 * (wk[c] + ws[c]);
        p9_jump(&x, ws, hs);
        p9_kick_tp(&x, qs, gm, none, np, s);
        p9_jump(&x, ws, hs);
        p9_kepler(&x, mu0, k == n - 1 ? hs + h : s);
    }
    *p = x;
    return -1;
}

// ------------------------------------------------------------------ smooth transition (method "smooth")
// docs/substeps-plan.md, decision of 2026-10-20: as in MERCURIUS (Rein et al.
// 2019), each planet's force on a test particle is split with a smooth
// function s(d) of their distance d into a far part s F and a near part
// (1 - s) F. The far part is the usual kick at the middle of the step; the
// near part is added to the Kepler motion around the Sun, which then runs in
// sub-steps (the step: jump(h) far-kick(dt) jump(h) A(dt), A = Kepler + near
// part). Where no planet comes within r_out during a step, A is the Kepler
// drift alone and the step is the production step: no abrupt switch.
// s: 0 for d <= r_in, 1 for d >= r_out, in between the polynomial of degree 11
// with five vanishing derivatives at both ends ("C5", Rein et al. 2019; the
// infinitely smooth one needs exp, which is not reproducible bit for bit).
// r_in = r_out / 10 as in MERCURIUS; r_out = the trigger radius.
P9_HD double p9_far(double d, double rout) {
    const double rin = 0.1 * rout;
    if (d >= rout) return 1.0;
    if (d <= rin) return 0.0;
    const double y = (d - rin) / (rout - rin);
    const double y2 = y * y, y3 = y2 * y, y6 = y3 * y3;
    return (462.0 - 1980.0 * y + 3465.0 * y2 - 3080.0 * y3 + 1386.0 * y2 * y2 - 252.0 * y2 * y3) * y6;
}

// The far part of the kick at the middle of the step (r2out[j] = r_out^2; 0: no split for this planet).
P9_HD void p9_kick_far(p9_body* p, const double* q, const double* gm, const double* r2out, int np, double h) {
    double ax = 0.0, ay = 0.0, az = 0.0;
    for (int j = 0; j < np; j++) {
        const double dx = q[3 * j] - p->x, dy = q[3 * j + 1] - p->y, dz = q[3 * j + 2] - p->z;
        const double d2 = dx * dx + dy * dy + dz * dz;
        const double d = sqrt(d2);
        double k = gm[j] / (d2 * d);
        if (r2out[j] > 0.0 && d2 < r2out[j]) k = k * p9_far(d, sqrt(r2out[j]));
        ax += k * dx;
        ay += k * dy;
        az += k * dz;
    }
    p->vx += h * ax;
    p->vy += h * ay;
    p->vz += h * az;
}

// The near part, as a kick with the planets at qs.
P9_HD void p9_kick_near(p9_body* p, const double* qs, const double* gm, const double* r2out, int np, double h) {
    double ax = 0.0, ay = 0.0, az = 0.0;
    for (int j = 0; j < np; j++) {
        if (!(r2out[j] > 0.0)) continue;
        const double dx = qs[3 * j] - p->x, dy = qs[3 * j + 1] - p->y, dz = qs[3 * j + 2] - p->z;
        const double d2 = dx * dx + dy * dy + dz * dz;
        if (d2 >= r2out[j]) continue;
        const double d = sqrt(d2);
        const double k = gm[j] / (d2 * d) * (1.0 - p9_far(d, sqrt(r2out[j])));
        ax += k * dx;
        ay += k * dy;
        az += k * dz;
    }
    p->vx += h * ax;
    p->vy += h * ay;
    p->vz += h * az;
}

// One step with the smooth transition. q, uq, uqb: the planets at the kick and
// their velocities before and after it (as for p9_step_tp_sub); wb: the jump
// velocity of the step's second jump. In A the jump term moves neither the
// particle nor the planets; relative to the true motion the particle is then
// ahead by h wb (the second jump) less the jump it does not take, so its
// position relative to a planet at time t after the kick is right if the planet
// is taken at Kepler(q, mean velocity; t) + a t^2 / 2 + h wb (the jump integral
// cancels). Counts and *nsub as p9_step_tp_sub; returns -1 (nothing removed).
P9_HD int p9_step_tp_smooth(p9_body* p, const double* q, const double* uq, const double* uqb, const double* wa, const double* wb, const double* gm,
                            const double* r2out, int np, double mu0, double dt, int* near, int* fast, int* close, int* fast_j, double* fast_d, int* nsub) {
    const double h = 0.5 * dt;
    p9_jump(p, wa, h);
    // counters, as p9_kick_tp_step (closest approach within the step around the kick, three r_out / 4 = three rule radii)
    for (int j = 0; j < np; j++) {
        if (!(r2out[j] > 0.0) || !near) continue;
        const double dx = q[3 * j] - p->x, dy = q[3 * j + 1] - p->y, dz = q[3 * j + 2] - p->z;
        const double wx = uq[3 * j] - p->vx, wy = uq[3 * j + 1] - p->vy, wz = uq[3 * j + 2] - p->vz;
        const double w2 = wx * wx + wy * wy + wz * wz;
        double tau = w2 > 0.0 ? -(dx * wx + dy * wy + dz * wz) / w2 : 0.0;
        const int inside = tau > -h && tau <= h;
        if (tau < -h) tau = -h;
        if (tau > h) tau = h;
        const double ex = dx + wx * tau, ey = dy + wy * tau, ez = dz + wz * tau;
        const double m2 = ex * ex + ey * ey + ez * ez;
        if (inside && m2 < 0.5625 * r2out[j]) {
            near[j]++;
            if (m2 < 0.01) close[j]++;
            if (m2 < 2.25 * w2 * dt * dt) {
                fast[j]++;
                *fast_j = j;
                *fast_d = sqrt(m2);
            }
        }
    }
    p9_kick_far(p, q, gm, r2out, np, dt);
    p9_jump(p, wb, h);
    // A over [0, dt] after the kick: Kepler alone unless a planet comes within r_out
    double um[3 * P9_MAX_PLANETS], ac[3 * P9_MAX_PLANETS];
    for (int c = 0; c < 3 * np; c++) um[c] = 0.5 * (uq[c] + uqb[c]), ac[c] = (uqb[c] - uq[c]) / dt;
    int n = 1, any = 0;
    for (int j = 0; j < np; j++) {
        if (!(r2out[j] > 0.0)) continue;
        // planet (as used in A) and particle at t = 0, straight lines over [0, dt]
        const double dx = q[3 * j] + h * wb[0] - p->x, dy = q[3 * j + 1] + h * wb[1] - p->y, dz = q[3 * j + 2] + h * wb[2] - p->z;
        const double wx = um[3 * j] - p->vx, wy = um[3 * j + 1] - p->vy, wz = um[3 * j + 2] - p->vz;
        const double w2 = wx * wx + wy * wy + wz * wz;
        double tau = w2 > 0.0 ? -(dx * wx + dy * wy + dz * wz) / w2 : 0.0;
        if (tau < 0.0) tau = 0.0;
        if (tau > dt) tau = dt;
        const double ex = dx + wx * tau, ey = dy + wy * tau, ez = dz + wz * tau;
        const double m2 = ex * ex + ey * ey + ez * ez;
        if (m2 >= r2out[j]) continue;
        any = 1;
        // focusing: the pericentre of the two-body orbit around the planet
        const double d2 = dx * dx + dy * dy + dz * dz;
        const double r = sqrt(d2), mu = gm[j];
        const double cx = dy * wz - dz * wy, cy = dz * wx - dx * wz, cz = dx * wy - dy * wx;
        const double L2 = cx * cx + cy * cy + cz * cz;
        const double en = 0.5 * w2 - mu / r;
        double e2 = 1.0 + 2.0 * en * L2 / (mu * mu);
        if (e2 < 0.0) e2 = 0.0;
        const double qp = L2 / mu / (1.0 + sqrt(e2));
        double m2e = m2, w2e = w2;
        if (qp * qp < m2e) {
            m2e = qp * qp;
            w2e = 2.0 * en + 2.0 * mu / qp;
        }
        // the near part is integrated in A with a leapfrog whose n changes from step to step: finer than
        // for the hard switch (32 sub-steps per flyby, 656 per orbit), so that its error stays below 1e-3
        // of the kick (docs/substeps-plan.md)
        const int nj = p9_sub_n_k(m2e, w2e > w2 ? w2e : w2, gm[j], dt, 1024.0, 16.0);
        if (nj > n) n = nj;
    }
    *nsub = any ? n : 1;
    if (!any) {
        p9_kepler(p, mu0, dt);
        return -1;
    }
    const double s = dt / n, hs = 0.5 * s;
    p9_kepler(p, mu0, hs);
    for (int k = 0; k < n; k++) {
        const double t = (k + 0.5) * s;
        double qs[3 * P9_MAX_PLANETS];
        for (int j = 0; j < np; j++) {
            p9_body b = {q[3 * j], q[3 * j + 1], q[3 * j + 2], um[3 * j], um[3 * j + 1], um[3 * j + 2]};
            p9_kepler(&b, mu0, t);
            const double t2 = 0.5 * t * t;
            qs[3 * j] = b.x + t2 * ac[3 * j] + h * wb[0], qs[3 * j + 1] = b.y + t2 * ac[3 * j + 1] + h * wb[1],
                  qs[3 * j + 2] = b.z + t2 * ac[3 * j + 2] + h * wb[2];
        }
        p9_kick_near(p, qs, gm, r2out, np, s);
        p9_kepler(p, mu0, k == n - 1 ? hs : s);
    }
    return -1;
}

// The synchronous state of a body kept half a drift ahead.
P9_HD p9_body p9_synchronous(p9_body y, double mu0, double dt) {
    p9_kepler(&y, mu0, -0.5 * dt);
    return y;
}

#endif
