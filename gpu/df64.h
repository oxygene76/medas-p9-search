// SPDX-License-Identifier: GPL-3.0-or-later
// Double-float ("df64"): a number as the unevaluated sum hi + lo of two IEEE
// binary32 values, |lo| <= ulp(hi)/2, about 48 significant bits. For GPUs whose
// float rate is many times their double rate (consumer and L40-class GPUs:
// 1/64). C++ for CUDA and for the host.
//
// Written from the published error-free transformations: Knuth's TwoSum
// (TAOCP vol. 2, 4.2.2), Dekker's FastTwoSum, Split and TwoProduct (Dekker 1971,
// Numer. Math. 18, 224) and the double-double arithmetic built on them
// (Dekker 1971; Hida, Li & Bailey 2001, "Algorithms for quad-double
// precision floating point arithmetic", ARITH-15). No code taken from a library.
//
// No fused multiply-add anywhere: the transformations need every product and
// sum rounded on its own (build with nvcc --fmad=false, host -ffp-contract=off).
// Every step is a correctly rounded binary32 + - * / or sqrt (nvcc's default
// -prec-div=true -prec-sqrt=true, no -ftz), so CPU and GPU give the same bits.
// Range: as binary32 (about 1e-38 .. 3e38); Split overflows above about 1e34.

#ifndef P9_DF64_H
#define P9_DF64_H

#ifdef __CUDACC__
#define P9_DF __host__ __device__ __forceinline__
#else
#include <cmath>
#define P9_DF static inline
#endif

struct df64 {
    float hi, lo;
};

// s + e = a + b exactly (Knuth)
P9_DF df64 df_two_sum(float a, float b) {
    const float s = a + b;
    const float bb = s - a;
    const float e = (a - (s - bb)) + (b - bb);
    return {s, e};
}

// s + e = a + b exactly, if |a| >= |b| or a = 0 (Dekker)
P9_DF df64 df_quick_two_sum(float a, float b) {
    const float s = a + b;
    const float e = b - (s - a);
    return {s, e};
}

// a = hi + lo with 12 significant bits each (Dekker/Veltkamp, 2^12 + 1)
P9_DF void df_split(float a, float* hi, float* lo) {
    const float c = 4097.0f * a;
    const float h = c - (c - a);
    *hi = h;
    *lo = a - h;
}

// p + e = a * b exactly (Dekker, without FMA)
P9_DF df64 df_two_prod(float a, float b) {
    const float p = a * b;
    float ah, al, bh, bl;
    df_split(a, &ah, &al);
    df_split(b, &bh, &bl);
    const float e = (((ah * bh - p) + ah * bl) + al * bh) + al * bl;
    return {p, e};
}

P9_DF df64 df_from_double(double x) {
    const float h = (float)x;
    return {h, (float)(x - (double)h)};
}

P9_DF double df_to_double(df64 a) { return (double)a.hi + (double)a.lo; }

P9_DF df64 operator-(df64 a) { return {-a.hi, -a.lo}; }

// accurate sum (both parts added, Hida, Li & Bailey's "IEEE" addition)
P9_DF df64 operator+(df64 a, df64 b) {
    df64 s = df_two_sum(a.hi, b.hi);
    const df64 t = df_two_sum(a.lo, b.lo);
    s.lo = s.lo + t.hi;
    s = df_quick_two_sum(s.hi, s.lo);
    s.lo = s.lo + t.lo;
    return df_quick_two_sum(s.hi, s.lo);
}

P9_DF df64 operator-(df64 a, df64 b) { return a + (-b); }

P9_DF df64 operator*(df64 a, df64 b) {
    df64 p = df_two_prod(a.hi, b.hi);
    p.lo = p.lo + (a.hi * b.lo + a.lo * b.hi);
    return df_quick_two_sum(p.hi, p.lo);
}

P9_DF df64 df_mul_f(df64 a, float b) {
    df64 p = df_two_prod(a.hi, b);
    p.lo = p.lo + a.lo * b;
    return df_quick_two_sum(p.hi, p.lo);
}

// long division with three quotient digits (Hida, Li & Bailey)
P9_DF df64 operator/(df64 a, df64 b) {
    const float q1 = a.hi / b.hi;
    df64 r = a - df_mul_f(b, q1);
    const float q2 = r.hi / b.hi;
    r = r - df_mul_f(b, q2);
    const float q3 = r.hi / b.hi;
    const df64 q = df_quick_two_sum(q1, q2);
    return q + df64{q3, 0.0f};
}

// one correction of the binary32 root: s + (a - s^2) / (2 s)
P9_DF df64 df_sqrt(df64 a) {
    if (!(a.hi > 0.0f)) return {0.0f, 0.0f};
#ifdef __CUDA_ARCH__
    const float s = sqrtf(a.hi);
#else
    const float s = std::sqrt(a.hi);
#endif
    const df64 r = a - df_two_prod(s, s);
    return df_quick_two_sum(s, r.hi / (2.0f * s));
}

P9_DF bool operator<(df64 a, df64 b) { return a.hi < b.hi || (a.hi == b.hi && a.lo < b.lo); }
P9_DF bool operator>(df64 a, df64 b) { return b < a; }
P9_DF df64& operator+=(df64& a, df64 b) { return a = a + b; }

#endif
