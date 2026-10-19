// SPDX-License-Identifier: GPL-3.0-or-later
// The encounter method "step" (gpu/whdh.h p9_kick_tp_step): closest approach
// within the step from relative position and velocity at the kick, and the
// flyby counters. Run by `make test`.
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "whdh.h"

static int failures = 0;
#define CHECK(c, msg)                                            \
    do {                                                         \
        if (!(c)) failures++, fprintf(stderr, "FAIL: %s\n", msg); \
    } while (0)

// one planet at the origin with velocity uq; particle at x, v; dt = 1; radius 0.1
static int kick(double x, double y, double vx, double vy, double uqx, int* near, int* fast) {
    p9_body p = {x, y, 0, vx, vy, 0};
    const double q[3] = {0, 0, 0}, uq[3] = {uqx, 0, 0}, gm[1] = {1e-12}, r2[1] = {0.01};
    near[0] = fast[0] = 0;
    return p9_kick_tp_step(&p, q, uq, gm, r2, 1, 1.0, 1.0, near, fast);
}

int main(void) {
    int near[1], fast[1];
    // passes through the sphere between two kicks: 0.60 au away at the kick, closest 0.05 au half a step later
    CHECK(kick(0.6, 0.05, -1.2, 0, 0, near, fast) == 0, "fast pass through the sphere not removed");
    CHECK(near[0] == 1 && fast[0] == 1, "fast pass not counted as a flyby shorter than 1.5 steps");
    {
        p9_body p = {0.6, 0.05, 0, -1.2, 0, 0};
        const double q[3] = {0, 0, 0}, gm[1] = {1e-12}, r2[1] = {0.01};
        CHECK(p9_kick_tp(&p, q, gm, r2, 1, 1.0) == -1, "the method at the kick should miss it (that is the point)");
    }
    // the same pass seen from a moving planet: only the relative velocity counts
    CHECK(kick(0.6, 0.05, -0.2, 0, 1.0, near, fast) == 0, "relative velocity: planet moving");
    // slow flyby at 0.05 au: removed, counted, not fast (0.05 / (0.01 * 1) = 5 steps)
    CHECK(kick(0.001, 0.05, -0.01, 0, 0, near, fast) == 0 && near[0] == 1 && fast[0] == 0, "slow close flyby");
    // closest approach outside this step: no removal, no count
    CHECK(kick(10.0, 0.05, -0.1, 0, 0, near, fast) == -1 && near[0] == 0, "approach in a later step counted");
    // flyby at 0.25 au (within 3 radii, not removed), 0.25 / (1.0 * 1) < 1.5: counted as fast
    CHECK(kick(0.3, 0.25, -1.0, 0, 0, near, fast) == -1 && near[0] == 1 && fast[0] == 1, "fast flyby within three radii");
    // beyond three radii: not counted
    CHECK(kick(0.3, 0.35, -1.0, 0, 0, near, fast) == -1 && near[0] == 0, "flyby beyond three radii counted");
    // closest distance within the step never exceeds the distance at the kick
    srand(3);
    for (int k = 0; k < 10000; k++) {
        const double x = 4 * (rand() / (double)RAND_MAX - 0.5), y = 4 * (rand() / (double)RAND_MAX - 0.5);
        const double vx = 4 * (rand() / (double)RAND_MAX - 0.5), vy = 4 * (rand() / (double)RAND_MAX - 0.5);
        const int e = kick(x, y, vx, vy, 0, near, fast);
        if (x * x + y * y < 0.01 && e != 0) {
            failures++;
            fprintf(stderr, "FAIL: inside at the kick but not removed (%g, %g)\n", x, y);
            break;
        }
    }
    // no radius: no check, no count
    {
        p9_body p = {0.6, 0.05, 0, -1.2, 0, 0};
        const double q[3] = {0, 0, 0}, uq[3] = {0, 0, 0}, gm[1] = {1e-12}, r2[1] = {0.0};
        near[0] = fast[0] = 0;
        CHECK(p9_kick_tp_step(&p, q, uq, gm, r2, 1, 1.0, 1.0, near, fast) == -1 && near[0] == 0, "radius 0 must disable the check");
    }
    if (failures) return 1;
    printf("test_step_encounter: ok\n");
    return 0;
}
