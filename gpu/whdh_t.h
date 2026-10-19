// SPDX-License-Identifier: GPL-3.0-or-later
// gpu/whdh.h as a C++ template over the number type T: double, float or df64
// (gpu/df64.h). Every expression is the one of whdh.h, in the same order;
// literals are written L<T>(c) (for double: c itself), so that T = double
// gives the same bits as whdh.h (checked by `p9gpu` with P9GPU_REAL=double-t,
// see docs/gpu-precision.md). float: a probe for the speed of single precision
// (not accurate enough for the runs). df64: the double-float variant.

#ifndef P9_WHDH_T_H
#define P9_WHDH_T_H

#include "df64.h"
#include "whdh.h"

#ifdef __CUDACC__
#define P9_HDT __host__ __device__ __forceinline__
#else
#include <cmath>
#define P9_HDT inline
#endif

template <class T>
struct p9t_body {
    T x, y, z, vx, vy, vz;
};

// constants and conversions
template <class T>
P9_HDT T L(double c);
template <>
P9_HDT double L<double>(double c) { return c; }
template <>
P9_HDT float L<float>(double c) { return (float)c; }
template <>
P9_HDT df64 L<df64>(double c) { return df_from_double(c); }

template <class T>
P9_HDT double to_double(T x) { return (double)x; }
template <>
P9_HDT double to_double<df64>(df64 x) { return df_to_double(x); }

P9_HDT double p9_sqrt(double x) { return sqrt(x); }
P9_HDT float p9_sqrt(float x) {
#ifdef __CUDA_ARCH__
    return sqrtf(x);
#else
    return std::sqrt(x);
#endif
}
P9_HDT df64 p9_sqrt(df64 x) { return df_sqrt(x); }

template <class T>
P9_HDT p9t_body<T> p9t_load(const p9_body& b) {
    return {L<T>(b.x), L<T>(b.y), L<T>(b.z), L<T>(b.vx), L<T>(b.vy), L<T>(b.vz)};
}
template <class T>
P9_HDT p9_body p9t_store(const p9t_body<T>& b) {
    return {to_double(b.x), to_double(b.y), to_double(b.z), to_double(b.vx), to_double(b.vy), to_double(b.vz)};
}

template <class T>
P9_HDT void p9t_stumpff(T z, T* c0, T* c1, T* c2, T* c3) {
    int n = 0;
    while (z > L<T>(0.1) || z < L<T>(-0.1)) {
        z = z * L<T>(0.25);
        n++;
    }
    T s3 = L<T>(1.0 / 6.0) * (L<T>(1.0) - z * L<T>(1.0 / 20.0) * (L<T>(1.0) - z * L<T>(1.0 / 42.0) * (L<T>(1.0) - z * L<T>(1.0 / 72.0) * (L<T>(1.0) - z * L<T>(1.0 / 110.0) * (L<T>(1.0) - z * L<T>(1.0 / 156.0) * (L<T>(1.0) - z * L<T>(1.0 / 210.0) * (L<T>(1.0) - z * L<T>(1.0 / 272.0))))))));
    T s2 = L<T>(0.5) * (L<T>(1.0) - z * L<T>(1.0 / 12.0) * (L<T>(1.0) - z * L<T>(1.0 / 30.0) * (L<T>(1.0) - z * L<T>(1.0 / 56.0) * (L<T>(1.0) - z * L<T>(1.0 / 90.0) * (L<T>(1.0) - z * L<T>(1.0 / 132.0) * (L<T>(1.0) - z * L<T>(1.0 / 182.0) * (L<T>(1.0) - z * L<T>(1.0 / 240.0))))))));
    T s1 = L<T>(1.0) - z * s3;
    T s0 = L<T>(1.0) - z * s2;
    for (; n > 0; n--) {
        const T n3 = L<T>(0.25) * (s2 + s0 * s3);
        const T n2 = L<T>(0.5) * s1 * s1;
        const T n1 = s0 * s1;
        const T n0 = L<T>(2.0) * s0 * s0 - L<T>(1.0);
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

template <class T>
P9_HDT void p9t_kepler(p9t_body<T>* p, T mu, T dt) {
    const T x0 = p->x, y0 = p->y, z0 = p->z, vx0 = p->vx, vy0 = p->vy, vz0 = p->vz;
    const T r0 = p9_sqrt(x0 * x0 + y0 * y0 + z0 * z0);
    const T ir0 = L<T>(1.0) / r0;
    const T eta = x0 * vx0 + y0 * vy0 + z0 * vz0;
    const T v2 = vx0 * vx0 + vy0 * vy0 + vz0 * vz0;
    const T beta = L<T>(2.0) * mu * ir0 - v2;
    const T zeta = mu - beta * r0;
    T s = dt * ir0 - L<T>(0.5) * eta * dt * dt * (ir0 * ir0 * ir0);
    T c0, c1, c2, c3;
    for (int it = 0; it < P9_KEPLER_ITERATIONS; it++) {
        p9t_stumpff(beta * s * s, &c0, &c1, &c2, &c3);
        const T G1 = s * c1, G2 = s * s * c2, G3 = s * s * s * c3;
        const T F = r0 * G1 + eta * G2 + mu * G3 - dt;
        const T Fp = r0 * c0 + eta * G1 + mu * G2;
        const T Fpp = eta * c0 + zeta * G1;
        s = s - F * Fp / (Fp * Fp - L<T>(0.5) * F * Fpp);
    }
    p9t_stumpff(beta * s * s, &c0, &c1, &c2, &c3);
    const T G1 = s * c1, G2 = s * s * c2, G3 = s * s * s * c3;
    const T r = r0 * c0 + eta * G1 + mu * G2;
    const T ir = L<T>(1.0) / r;
    const T f = L<T>(1.0) - mu * G2 * ir0;
    const T g = dt - mu * G3;
    const T fd = -mu * G1 * ir * ir0;
    const T gd = L<T>(1.0) - mu * G2 * ir;
    p->x = f * x0 + g * vx0;
    p->y = f * y0 + g * vy0;
    p->z = f * z0 + g * vz0;
    p->vx = fd * x0 + gd * vx0;
    p->vy = fd * y0 + gd * vy0;
    p->vz = fd * z0 + gd * vz0;
}

template <class T>
P9_HDT int p9t_kick_tp(p9t_body<T>* p, const T* q, const T* gm, const T* r2enc, int np, T h) {
    T ax = L<T>(0.0), ay = L<T>(0.0), az = L<T>(0.0);
    int enc = -1;
    for (int j = 0; j < np; j++) {
        const T dx = q[3 * j] - p->x, dy = q[3 * j + 1] - p->y, dz = q[3 * j + 2] - p->z;
        const T d2 = dx * dx + dy * dy + dz * dz;
        if (d2 < r2enc[j] && enc < 0) enc = j;
        const T d = p9_sqrt(d2);
        const T k = gm[j] / (d2 * d);
        ax += k * dx;
        ay += k * dy;
        az += k * dz;
    }
    p->vx += h * ax;
    p->vy += h * ay;
    p->vz += h * az;
    return enc;
}

template <class T>
P9_HDT void p9t_jump(p9t_body<T>* p, const T* w, T h) {
    p->x += h * w[0];
    p->y += h * w[1];
    p->z += h * w[2];
}

template <class T>
P9_HDT int p9t_step_tp(p9t_body<T>* p, const T* q, const T* wa, const T* wb, const T* gm, const T* r2enc, int np, T mu0, T dt) {
    const T h = L<T>(0.5) * dt;
    p9t_jump(p, wa, h);
    const int enc = p9t_kick_tp(p, q, gm, r2enc, np, dt);
    p9t_jump(p, wb, h);
    p9t_kepler(p, mu0, dt);
    return enc;
}

template <class T>
P9_HDT p9t_body<T> p9t_synchronous(p9t_body<T> y, T mu0, T dt) {
    p9t_kepler(&y, mu0, L<T>(-0.5) * dt);
    return y;
}

#endif
