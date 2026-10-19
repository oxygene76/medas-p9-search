// SPDX-License-Identifier: GPL-3.0-or-later
// The J2 acceleration of gpu/whdh.h (model "j2") against the numerical
// gradient of its potential Phi = mu J2 R^2 (3 s^2 - r^2) / (2 r^5), s = r . n,
// for random positions and axes, and against the textbook form for n = z.
// Run by `make test`.
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "whdh.h"

static double phi(const double* j2, double x, double y, double z) {
    const double r2 = x * x + y * y + z * z, s = x * j2[1] + y * j2[2] + z * j2[3];
    return j2[0] * (3 * s * s - r2) / (2 * r2 * r2 * sqrt(r2));
}

int main(void) {
    int fail = 0;
    srand(7);
    for (int k = 0; k < 1000; k++) {
        double n[3] = {rand() / (double)RAND_MAX - 0.5, rand() / (double)RAND_MAX - 0.5, rand() / (double)RAND_MAX - 0.5};
        const double nn = sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]);
        const double j2[5] = {1.34, n[0] / nn, n[1] / nn, n[2] / nn, 0};
        const double x = 600 * (rand() / (double)RAND_MAX - 0.5), y = 600 * (rand() / (double)RAND_MAX - 0.5), z = 100 * (rand() / (double)RAND_MAX - 0.5);
        if (x * x + y * y + z * z < 400) continue;
        double a[3] = {0, 0, 0};
        p9_j2_acc(x, y, z, j2, &a[0], &a[1], &a[2]);
        const double h = 1e-4 * sqrt(x * x + y * y + z * z);
        const double g[3] = {-(phi(j2, x + h, y, z) - phi(j2, x - h, y, z)) / (2 * h), -(phi(j2, x, y + h, z) - phi(j2, x, y - h, z)) / (2 * h),
                             -(phi(j2, x, y, z + h) - phi(j2, x, y, z - h)) / (2 * h)};
        const double scale = fabs(g[0]) + fabs(g[1]) + fabs(g[2]);
        for (int c = 0; c < 3; c++)
            if (fabs(a[c] - g[c]) > 1e-6 * scale) {
                fail++;
                fprintf(stderr, "FAIL point %d component %d: %.10g vs gradient %.10g\n", k, c, a[c], g[c]);
            }
    }
    // n = z: a_x = 3/2 mu J2R2 x / r^5 (5 z^2/r^2 - 1), a_z = 3/2 mu J2R2 z / r^5 (5 z^2/r^2 - 3)
    const double j2z[5] = {2.0, 0, 0, 1, 0}, x = 30, y = -40, z = 12, r = sqrt(x * x + y * y + z * z);
    double a[3] = {0, 0, 0};
    p9_j2_acc(x, y, z, j2z, &a[0], &a[1], &a[2]);
    const double kx = 1.5 * 2.0 * x / pow(r, 5) * (5 * z * z / (r * r) - 1), kz = 1.5 * 2.0 * z / pow(r, 5) * (5 * z * z / (r * r) - 3);
    if (fabs(a[0] - kx) > 1e-12 * fabs(kx) || fabs(a[2] - kz) > 1e-12 * fabs(kz)) {
        fail++;
        fprintf(stderr, "FAIL n = z: %.17g %.17g vs %.17g %.17g\n", a[0], a[2], kx, kz);
    }
    if (fail) return 1;
    printf("test_j2: ok\n");
    return 0;
}
