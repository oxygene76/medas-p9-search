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

// ------------------------------------------------------------------ smooth transition (whdh.h p9_step_tp_smooth)
// The same expressions in the same order; the flyby counters are left out.
template <class T>
P9_HDT T p9t_far(T d, T rout) {
    const T rin = L<T>(0.1) * rout;
    if (!(d < rout)) return L<T>(1.0);
    if (!(d > rin)) return L<T>(0.0);
    const T y = (d - rin) / (rout - rin);
    const T y2 = y * y, y3 = y2 * y, y6 = y3 * y3;
    return (L<T>(462.0) - L<T>(1980.0) * y + L<T>(3465.0) * y2 - L<T>(3080.0) * y3 + L<T>(1386.0) * y2 * y2 - L<T>(252.0) * y2 * y3) * y6;
}

template <class T>
P9_HDT void p9t_kick_far(p9t_body<T>* p, const T* q, const T* gm, const T* r2out, int np, T h) {
    T ax = L<T>(0.0), ay = L<T>(0.0), az = L<T>(0.0);
    for (int j = 0; j < np; j++) {
        const T dx = q[3 * j] - p->x, dy = q[3 * j + 1] - p->y, dz = q[3 * j + 2] - p->z;
        const T d2 = dx * dx + dy * dy + dz * dz;
        const T d = p9_sqrt(d2);
        T k = gm[j] / (d2 * d);
        if (r2out[j] > L<T>(0.0) && d2 < r2out[j]) k = k * p9t_far(d, p9_sqrt(r2out[j]));
        ax += k * dx;
        ay += k * dy;
        az += k * dz;
    }
    p->vx += h * ax;
    p->vy += h * ay;
    p->vz += h * az;
}

template <class T>
P9_HDT void p9t_kick_near(p9t_body<T>* p, const T* qs, const T* gm, const T* r2out, int np, T h) {
    T ax = L<T>(0.0), ay = L<T>(0.0), az = L<T>(0.0);
    for (int j = 0; j < np; j++) {
        if (!(r2out[j] > L<T>(0.0))) continue;
        const T dx = qs[3 * j] - p->x, dy = qs[3 * j + 1] - p->y, dz = qs[3 * j + 2] - p->z;
        const T d2 = dx * dx + dy * dy + dz * dz;
        if (!(d2 < r2out[j])) continue;
        const T d = p9_sqrt(d2);
        const T k = gm[j] / (d2 * d) * (L<T>(1.0) - p9t_far(d, p9_sqrt(r2out[j])));
        ax += k * dx;
        ay += k * dy;
        az += k * dz;
    }
    p->vx += h * ax;
    p->vy += h * ay;
    p->vz += h * az;
}

template <class T>
P9_HDT int p9t_sub_n_k(T m2, T w2, T gm, T dt, T k2, T orb, int nmax) {
    if (!(m2 > L<T>(0.0))) return nmax;
    const T d3 = m2 * p9_sqrt(m2);
    int n = 1;
    for (; n < nmax; n *= 2) {
        const T s = dt / L<T>((double)n);
        if (!(m2 < k2 * w2 * s * s) && !(d3 < orb * L<T>(P9_SUB_ORBIT) * s * s * gm)) break;
    }
    return n;
}

template <class T>
P9_HDT int p9t_step_tp_smooth(p9t_body<T>* p, const T* q, const T* uq, const T* uqb, const T* wa, const T* wb, const T* gm, const T* r2out,
                              const T* r2col, int np, T mu0, T dt, int* nsub) {
    const T h = L<T>(0.5) * dt;
    p9t_jump(p, wa, h);
    p9t_kick_far(p, q, gm, r2out, np, dt);
    p9t_jump(p, wb, h);
    T um[3 * P9_MAX_PLANETS], ac[3 * P9_MAX_PLANETS];
    for (int c = 0; c < 3 * np; c++) um[c] = L<T>(0.5) * (uq[c] + uqb[c]), ac[c] = (uqb[c] - uq[c]) / dt;
    int n = 1, any = 0;
    for (int j = 0; j < np; j++) {
        if (!(r2out[j] > L<T>(0.0))) continue;
        const T dx = q[3 * j] + h * wb[0] - p->x, dy = q[3 * j + 1] + h * wb[1] - p->y, dz = q[3 * j + 2] + h * wb[2] - p->z;
        const T wx = um[3 * j] - p->vx, wy = um[3 * j + 1] - p->vy, wz = um[3 * j + 2] - p->vz;
        const T w2 = wx * wx + wy * wy + wz * wz;
        T tau = w2 > L<T>(0.0) ? -(dx * wx + dy * wy + dz * wz) / w2 : L<T>(0.0);
        if (tau < L<T>(0.0)) tau = L<T>(0.0);
        if (tau > dt) tau = dt;
        const T ex = dx + wx * tau, ey = dy + wy * tau, ez = dz + wz * tau;
        const T m2 = ex * ex + ey * ey + ez * ez;
        if (!(m2 < r2out[j])) continue;
        any = 1;
        const T d2 = dx * dx + dy * dy + dz * dz;
        const T r = p9_sqrt(d2), mu = gm[j];
        const T en = L<T>(0.5) * w2 - mu / r;
        const T dw = dx * wx + dy * wy + dz * wz;
        int peri = (!(dw > L<T>(2.0) * dt * w2) && !(-dw > L<T>(2.0) * dt * w2)) || !(d2 * r > L<T>(4.0) * dt * dt * mu);
        if (en < L<T>(0.0)) {
            const T a = -mu / (L<T>(2.0) * en);
            if (!(L<T>(P9_PI2) * a * a * a > L<T>(4.0) * dt * dt * mu)) peri = 1;
        }
        const T cx = dy * wz - dz * wy, cy = dz * wx - dx * wz, cz = dx * wy - dy * wx;
        const T L2 = cx * cx + cy * cy + cz * cz;
        T e2 = L<T>(1.0) + L<T>(2.0) * en * L2 / (mu * mu);
        if (e2 < L<T>(0.0)) e2 = L<T>(0.0);
        const T qp = L2 / mu / (L<T>(1.0) + p9_sqrt(e2));
        T m2e = m2, w2e = w2;
        if (qp * qp < m2e) {
            m2e = qp * qp;
            w2e = L<T>(2.0) * en + L<T>(2.0) * mu / qp;
        }
        const int nj = p9t_sub_n_k(m2e, w2e > w2 ? w2e : w2, gm[j], dt, L<T>(1024.0), L<T>(16.0), peri ? P9_SMOOTH_MAX : P9_SUB_MAX);
        if (nj > n) n = nj;
    }
    *nsub = any ? n : 1;
    if (!any) {
        p9t_kepler(p, mu0, dt);
        return -1;
    }
    const T s = dt / L<T>((double)n), hs = L<T>(0.5) * s;
    p9t_kepler(p, mu0, hs);
    for (int k = 0; k < n; k++) {
        const T t = L<T>(k + 0.5) * s;
        T qs[3 * P9_MAX_PLANETS];
        for (int j = 0; j < np; j++) {
            p9t_body<T> b = {q[3 * j], q[3 * j + 1], q[3 * j + 2], um[3 * j], um[3 * j + 1], um[3 * j + 2]};
            p9t_kepler(&b, mu0, t);
            const T t2 = L<T>(0.5) * t * t;
            qs[3 * j] = b.x + t2 * ac[3 * j] + h * wb[0], qs[3 * j + 1] = b.y + t2 * ac[3 * j + 1] + h * wb[1],
                  qs[3 * j + 2] = b.z + t2 * ac[3 * j + 2] + h * wb[2];
        }
        for (int j = 0; r2col && j < np; j++) {
            if (!(r2col[j] > L<T>(0.0))) continue;
            const T ux = p->x - qs[3 * j], uy = p->y - qs[3 * j + 1], uz = p->z - qs[3 * j + 2];
            if (ux * ux + uy * uy + uz * uz < r2col[j]) return j;
        }
        p9t_kick_near(p, qs, gm, r2out, np, s);
        p9t_kepler(p, mu0, k == n - 1 ? hs : s);
    }
    return -1;
}

template <class T>
P9_HDT p9t_body<T> p9t_synchronous(p9t_body<T> y, T mu0, T dt) {
    p9t_kepler(&y, mu0, L<T>(-0.5) * dt);
    return y;
}

#endif
