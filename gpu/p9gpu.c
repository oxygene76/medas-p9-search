// SPDX-License-Identifier: GPL-3.0-or-later
// p9gpu: test particles on the GPU, planets on the CPU, for the same jobs as
// p9sim (same input SimulationArchive, same command line, same outputs: a
// SimulationArchive of snapshots and the canonical state hash).
//
//   p9gpu run <in.sa> <t_end> <n_snapshots> <out.sa> [<out.state>]
//
// Environment:
//   P9GPU_MODE=gpu|cpu   gpu (default when built with CUDA): test particles
//                        on the GPU; cpu: the same code on one CPU core (the
//                        reference: it must give the same bits as the GPU)
//   P9GPU_BLOCK=2000     steps per GPU launch (planets computed ahead per block)
//   P9_ENCOUNTER_METHOD=kick|step|substep  close encounters judged at the kick
//                        (kick, the default for jobs without a method), by the
//                        closest approach within the step (step), or followed
//                        with sub-steps where a step is too long (substep;
//                        nothing removed at the planets; the radii are the
//                        trigger radii; whdh.h p9_step_tp_sub), or split
//                        smoothly into a far and a near part (smooth, as
//                        MERCURIUS; the radii are r_out; p9_step_tp_smooth)
//   P9_ENCOUNTER_REMOVE=0  with method step: close encounters are counted, not
//                        removed (only the distance rules remove)
//   P9_FLYBY_OUT=file    with method step: the flyby records per test particle
//                        (tab-separated, see write_flybys)
//   P9_REMOVED_OUT=file  the fate of each test particle of the input: id, then
//                        alive (1), distance rules (0) or the body id of the
//                        planet of its close encounter (any method)
//   P9_COLLISION_RADII="id=au,..."  method smooth: the physical radii of the
//                        planets (by body id; tools/p9job.py sets them); a test
//                        particle closer to a planet than its radius at a
//                        sub-step's kick is removed (fate collision:<id>, the
//                        count per planet in collisions=); without: none
//   P9_CAPPED_OUT=file   method smooth, P9GPU_MODE=cpu, double: one line per
//                        step at P9_SUB_MAX sub-steps (diagnostics, the same
//                        bits: whdh.h p9_capdiag)
//   P9_PLANET_SUBSTEPS=k  the planets take k (even) inner steps of dt/k per step
//                        (kept synchronous); the test particles get their
//                        positions, velocities and accelerations at the middle
//                        of the step and the jump velocity there (default 1:
//                        the planets step with dt, as before)
//   P9_J2="muJ2R2,nx,ny,nz,r_remove"   model "j2" (whdh.h): the central body
//                        has a J2 (tools/p9job.py sets it from params.model);
//                        test particles within r_remove of the Sun are removed
//   P9GPU_REAL=double    number type of the test particles' integrator:
//                        double (default), double-t, float, df64 (gpu/p9gpu_real.h)
//
// Method (docs/gpu-integrator.md): Wisdom-Holman in democratic heliocentric
// coordinates, drift-kick-drift, gpu/whdh.h. The planets (all massive bodies
// but the Sun) are integrated on the CPU with the same splitting; for every
// block of steps their positions at the kicks and the jump velocities are stored
// in a table, which the GPU uses for all test particles while the CPU
// computes the next block. This is not REBOUND's WHFast: the operator order
// differs, so results agree with p9sim statistically, not bit for bit.
//
// Removal of test particles as in p9sim: every 1000 steps (counted over the
// whole run, steps_done), beyond 10,000 au or within 5 au of the Sun.

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "rebound.h"
#include "sha256.h"
#include "p9state.h"
#include "p9encounter.h"
#include "whdh.h"
#include "p9gpu_real.h"
#ifndef P9_NO_CUDA
#include "p9gpu_api.h"
#endif

#define R_OUT 10000.0
#define R_IN 5.0
#define CHECK_EVERY 1000

static double now_s(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + 1e-9 * ts.tv_nsec;
}

// ------------------------------------------------------------------ planets on the CPU

typedef struct {
    int np;            // planets (massive bodies except the Sun)
    double m0, G;      // mass of the Sun, G
    double mu0;        // G m0
    double m[P9_MAX_PLANETS], gm[P9_MAX_PLANETS];
    p9_body b[P9_MAX_PLANETS];  // Q (relative to the Sun) and barycentric velocity
    int j2;                     // model "j2": J2 of the central body (j2v as in whdh.h)
    int ksub;                   // P9_PLANET_SUBSTEPS: inner steps of the planets per step (1: as before)
    double j2v[5];
} planets;

static void planets_kick(planets* P, double h) {
    double a[P9_MAX_PLANETS][3] = {{0}};
    for (int i = 0; i < P->np; i++) {
        for (int j = 0; j < P->np; j++) {
            if (j == i) continue;
            const double dx = P->b[j].x - P->b[i].x, dy = P->b[j].y - P->b[i].y, dz = P->b[j].z - P->b[i].z;
            const double d2 = dx * dx + dy * dy + dz * dz;
            const double d = sqrt(d2);
            const double k = P->gm[j] / (d2 * d);
            a[i][0] += k * dx;
            a[i][1] += k * dy;
            a[i][2] += k * dz;
        }
    }
    if (P->j2)
        for (int i = 0; i < P->np; i++) p9_j2_acc(P->b[i].x, P->b[i].y, P->b[i].z, P->j2v, &a[i][0], &a[i][1], &a[i][2]);
    for (int i = 0; i < P->np; i++) {
        P->b[i].vx += h * a[i][0];
        P->b[i].vy += h * a[i][1];
        P->b[i].vz += h * a[i][2];
    }
}

static void planets_w(const planets* P, double w[3]) {
    double px = 0.0, py = 0.0, pz = 0.0;
    for (int i = 0; i < P->np; i++) {
        px += P->m[i] * P->b[i].vx;
        py += P->m[i] * P->b[i].vy;
        pz += P->m[i] * P->b[i].vz;
    }
    w[0] = px / P->m0;
    w[1] = py / P->m0;
    w[2] = pz / P->m0;
}

static void planets_positions(const planets* P, double* q) {
    for (int i = 0; i < P->np; i++) {
        q[3 * i] = P->b[i].x;
        q[3 * i + 1] = P->b[i].y;
        q[3 * i + 2] = P->b[i].z;
    }
}

// One step of the planets, kept half a drift ahead like the test particles
// (whdh.h); writes the jump velocities (wa, wb) and the planets' positions at
// the kick (q).
static void planets_step(planets* P, double dt, double* wa, double* q, double* wb, double* uq, double* uqb) {
    const double h = 0.5 * dt;
    planets_w(P, wa);
    for (int i = 0; i < P->np; i++) p9_jump(&P->b[i], wa, h);
    planets_positions(P, q);
    for (int i = 0; i < P->np; i++) uq[3 * i] = P->b[i].vx, uq[3 * i + 1] = P->b[i].vy, uq[3 * i + 2] = P->b[i].vz;
    planets_kick(P, dt);
    for (int i = 0; i < P->np; i++) uqb[3 * i] = P->b[i].vx, uqb[3 * i + 1] = P->b[i].vy, uqb[3 * i + 2] = P->b[i].vz;
    planets_w(P, wb);
    for (int i = 0; i < P->np; i++) p9_jump(&P->b[i], wb, h);
    for (int i = 0; i < P->np; i++) p9_kepler(&P->b[i], P->mu0, dt);
}

// Planet-planet (and J2) accelerations at the current positions.
static void planets_acc(const planets* P, double a[][3]) {
    for (int i = 0; i < P->np; i++) a[i][0] = a[i][1] = a[i][2] = 0.0;
    for (int i = 0; i < P->np; i++) {
        for (int j = 0; j < P->np; j++) {
            if (j == i) continue;
            const double dx = P->b[j].x - P->b[i].x, dy = P->b[j].y - P->b[i].y, dz = P->b[j].z - P->b[i].z;
            const double d2 = dx * dx + dy * dy + dz * dz;
            const double d = sqrt(d2);
            const double k = P->gm[j] / (d2 * d);
            a[i][0] += k * dx;
            a[i][1] += k * dy;
            a[i][2] += k * dz;
        }
    }
    if (P->j2)
        for (int i = 0; i < P->np; i++) p9_j2_acc(P->b[i].x, P->b[i].y, P->b[i].z, P->j2v, &a[i][0], &a[i][1], &a[i][2]);
}

// One inner step of the synchronous planets (drift-kick-drift, democratic heliocentric).
static void planets_inner(planets* P, double s) {
    double w[3];
    for (int i = 0; i < P->np; i++) p9_kepler(&P->b[i], P->mu0, 0.5 * s);
    planets_w(P, w);
    for (int i = 0; i < P->np; i++) p9_jump(&P->b[i], w, 0.5 * s);
    planets_kick(P, s);
    planets_w(P, w);
    for (int i = 0; i < P->np; i++) p9_jump(&P->b[i], w, 0.5 * s);
    for (int i = 0; i < P->np; i++) p9_kepler(&P->b[i], P->mu0, 0.5 * s);
}

// One step with inner steps (P9_PLANET_SUBSTEPS): the planets synchronous at
// the step's start, k/2 inner steps to the middle, there the table entries
// (positions; velocities -/+ a dt/2 around the middle, so that the sub-steps'
// interpolation has the mean velocity and the acceleration a; the jump
// velocity at the middle for both of the particle's jumps), k/2 inner steps
// to the end.
static void planets_step_fine(planets* P, double dt, double* wa, double* q, double* wb, double* uq, double* uqb) {
    const int k = P->ksub;
    const double s = dt / k;
    for (int m = 0; m < k / 2; m++) planets_inner(P, s);
    double a[P9_MAX_PLANETS][3];
    planets_acc(P, a);
    planets_positions(P, q);
    planets_w(P, wa);
    for (int c = 0; c < 3; c++) wb[c] = wa[c];
    for (int i = 0; i < P->np; i++) {
        const double v[3] = {P->b[i].vx, P->b[i].vy, P->b[i].vz};
        for (int c = 0; c < 3; c++) uq[3 * i + c] = v[c] - 0.5 * dt * a[i][c], uqb[3 * i + c] = v[c] + 0.5 * dt * a[i][c];
    }
    for (int m = 0; m < k / 2; m++) planets_inner(P, s);
}

// Fills a table for nb steps: q[nb*np*3], then wa[nb*3], then wb[nb*3], then
// uq[nb*np*3] (the planets' barycentric velocities at the kick, before it; for
// the encounter methods "step" and "substep"), then uqb[nb*np*3] (after it; for
// the sub-steps' interpolation of the planets).
static void planets_block(planets* P, double dt, int nb, double* tab) {
    const int np = P->np;
    double* q = tab;
    double* wa = tab + (size_t)nb * np * 3;
    double* wb = wa + (size_t)nb * 3;
    double* uq = wb + (size_t)nb * 3;
    double* uqb = uq + (size_t)nb * np * 3;
    for (int k = 0; k < nb; k++) {
        if (P->ksub > 1)
            planets_step_fine(P, dt, wa + 3 * k, q + (size_t)k * np * 3, wb + 3 * k, uq + (size_t)k * np * 3, uqb + (size_t)k * np * 3);
        else
            planets_step(P, dt, wa + 3 * k, q + (size_t)k * np * 3, wb + 3 * k, uq + (size_t)k * np * 3, uqb + (size_t)k * np * 3);
    }
}

// ------------------------------------------------------------------ conversions

typedef struct {
    double X[3], V[3];  // centre of mass (moves uniformly)
} com_t;

// From the REBOUND simulation (inertial frame) to Sun-relative positions and barycentric velocities.
static void to_dh(struct reb_simulation* r, planets* P, p9_body* tp, int ntp, com_t* com) {
    const struct reb_particle* s = &r->particles[0];
    double M = 0, X[3] = {0}, V[3] = {0};
    for (size_t i = 0; i < r->N_active; i++) {
        const struct reb_particle* p = &r->particles[i];
        M += p->m;
        X[0] += p->m * p->x, X[1] += p->m * p->y, X[2] += p->m * p->z;
        V[0] += p->m * p->vx, V[1] += p->m * p->vy, V[2] += p->m * p->vz;
    }
    for (int k = 0; k < 3; k++) com->X[k] = X[k] / M, com->V[k] = V[k] / M;
    P->np = (int)r->N_active - 1;
    P->m0 = s->m;
    P->G = r->G;
    P->mu0 = r->G * s->m;
    for (int i = 0; i < P->np; i++) {
        const struct reb_particle* p = &r->particles[i + 1];
        P->m[i] = p->m;
        P->gm[i] = r->G * p->m;
        P->b[i] = (p9_body){p->x - s->x, p->y - s->y, p->z - s->z, p->vx - com->V[0], p->vy - com->V[1], p->vz - com->V[2]};
    }
    for (int i = 0; i < ntp; i++) {
        const struct reb_particle* p = &r->particles[r->N_active + i];
        tp[i] = (p9_body){p->x - s->x, p->y - s->y, p->z - s->z, p->vx - com->V[0], p->vy - com->V[1], p->vz - com->V[2]};
    }
}

// Back to the inertial frame of the input, into r (whose particles are the
// massive bodies and the surviving test particles, in input order).
static void from_dh(struct reb_simulation* r, const planets* P, const p9_body* tp, const int* alive, int ntp, const com_t* com, double dt_since0) {
    double Mt = P->m0, SX = 0, SY = 0, SZ = 0, PX = 0, PY = 0, PZ = 0;
    for (int i = 0; i < P->np; i++) {
        Mt += P->m[i];
        SX += P->m[i] * P->b[i].x, SY += P->m[i] * P->b[i].y, SZ += P->m[i] * P->b[i].z;
        PX += P->m[i] * P->b[i].vx, PY += P->m[i] * P->b[i].vy, PZ += P->m[i] * P->b[i].vz;
    }
    const double cx = com->X[0] + com->V[0] * dt_since0, cy = com->X[1] + com->V[1] * dt_since0, cz = com->X[2] + com->V[2] * dt_since0;
    const double sx = cx - SX / Mt, sy = cy - SY / Mt, sz = cz - SZ / Mt;
    struct reb_particle* ps = r->particles;
    ps[0].x = sx, ps[0].y = sy, ps[0].z = sz;
    ps[0].vx = com->V[0] - PX / P->m0, ps[0].vy = com->V[1] - PY / P->m0, ps[0].vz = com->V[2] - PZ / P->m0;
    for (int i = 0; i < P->np; i++) {
        struct reb_particle* p = &ps[i + 1];
        p->x = P->b[i].x + sx, p->y = P->b[i].y + sy, p->z = P->b[i].z + sz;
        p->vx = P->b[i].vx + com->V[0], p->vy = P->b[i].vy + com->V[1], p->vz = P->b[i].vz + com->V[2];
    }
    size_t k = r->N_active;
    for (int i = 0; i < ntp; i++) {
        if (alive[i] != 1) continue;
        struct reb_particle* p = &ps[k++];
        p->x = tp[i].x + sx, p->y = tp[i].y + sy, p->z = tp[i].z + sz;
        p->vx = tp[i].vx + com->V[0], p->vy = tp[i].vy + com->V[1], p->vz = tp[i].vz + com->V[2];
    }
}

// Removes from r the test particles that died since the last snapshot (in descending order).
static void drop_dead(struct reb_simulation* r, const int* alive, int* was_alive, int ntp) {
    size_t k = r->N_active;
    int* idx = malloc(sizeof(int) * (ntp > 0 ? ntp : 1));
    int n = 0;
    for (int i = 0; i < ntp; i++) {
        if (was_alive[i] != 1) continue;
        if (alive[i] != 1) idx[n++] = (int)k;
        k++;
    }
    for (int j = n - 1; j >= 0; j--) reb_simulation_remove_particle(r, (size_t)idx[j]);
    for (int i = 0; i < ntp; i++) was_alive[i] = alive[i];
    free(idx);
}

// ------------------------------------------------------------------ test particles on the CPU (reference)

// P9_CAPPED_OUT (diagnostics): the file and the ids of the test particles and planets
static FILE* cap_out;
static const double *cap_tp_ids, *cap_ids;

static void cpu_block(p9_body* tp, int* alive, int ntp, const planets* P, const double* r2enc, const double* r2col, const double* tab, int nb,
                      unsigned long long step0, double dt, int step_method, int enc_remove, p9_flybys* F) {
    const int np = P->np;
    const double* q = tab;
    const double* wa = tab + (size_t)nb * np * 3;
    const double* wb = wa + (size_t)nb * 3;
    const double* uq = wb + (size_t)nb * 3;
    const double* uqb = uq + (size_t)nb * np * 3;
    for (int i = 0; i < ntp; i++) {
        if (alive[i] != 1) continue;
        p9_body p = tp[i];
        int a = 1;
        for (int k = 0; k < nb; k++) {
            int fj = -1, ns = 1;
            double fd = 0.0;
            p9_capdiag cd = {-1, 0, 0.0, 0.0, 0.0, 0.0};
            const int enc = step_method == 3 ? p9_step_tp_smooth_d(&p, q + (size_t)k * np * 3, uq + (size_t)k * np * 3, uqb + (size_t)k * np * 3,
                                                                   wa + 3 * k, wb + 3 * k, P->gm, r2enc, r2col, np, P->mu0, dt, F->near + (size_t)i * np,
                                                                   F->fast + (size_t)i * np, F->close + (size_t)i * np, &fj, &fd, &ns,
                                                                   cap_out ? &cd : 0)
                          : step_method == 2 ? p9_step_tp_sub(&p, q + (size_t)k * np * 3, uq + (size_t)k * np * 3, uqb + (size_t)k * np * 3, wa + 3 * k,
                                                              wb + 3 * k, P->gm, r2enc, np,
                                                              P->mu0, dt, F->near + (size_t)i * np, F->fast + (size_t)i * np, F->close + (size_t)i * np,
                                                              &fj, &fd, &ns)
                          : step_method ? p9_step_tp_step(&p, q + (size_t)k * np * 3, uq + (size_t)k * np * 3, wa + 3 * k, wb + 3 * k, P->gm, r2enc, np,
                                                          P->mu0, dt, F->near + (size_t)i * np, F->fast + (size_t)i * np,
                                                          F->close + (size_t)i * np, &fj, &fd)
                          : P->j2 ? p9_step_tp_j2(&p, q + (size_t)k * np * 3, wa + 3 * k, wb + 3 * k, P->gm, r2enc, np, P->mu0, dt, P->j2v)
                                  : p9_step_tp(&p, q + (size_t)k * np * 3, wa + 3 * k, wb + 3 * k, P->gm, r2enc, np, P->mu0, dt);
            if (fj >= 0) F->last_step[i] = step0 + k + 1, F->last_j[i] = fj + 1, F->last_d[i] = fd;
            if (ns > 1) {
                F->sub_steps[i]++;
                if (ns > F->sub_max[i]) F->sub_max[i] = ns;
                if (ns >= (step_method == 3 ? P9_SMOOTH_MAX : P9_SUB_MAX)) F->sub_capped[i]++;
                if (cap_out && ns >= P9_CAPDIAG_MIN && cd.j >= 0)
                    fprintf(cap_out, "%.0f\t%llu\t%.0f\t%.6g\t%.6g\t%.6g\t%.6g\t%d\n", cap_tp_ids[i], step0 + k + 1, cap_ids[cd.j], cd.q_est, cd.d_min,
                            cd.q_loc, cd.v_est, cd.n_want);
            }
            if (enc >= 0 && (enc_remove || !step_method || step_method == 3)) {  // smooth: a collision
                a = -1 - enc;
                if (step_method) F->rm_step[i] = step0 + k + 1;
                break;
            }
            if ((step0 + k + 1) % CHECK_EVERY == 0) {
                const p9_body x = p9_synchronous(p, P->mu0, dt);
                const double r2 = x.x * x.x + x.y * x.y + x.z * x.z;
                if (r2 > R_OUT * R_OUT || r2 < R_IN * R_IN) {
                    a = 0;
                    if (step_method) F->rm_step[i] = step0 + k + 1;
                    break;
                }
            }
        }
        tp[i] = p;
        alive[i] = a;
    }
}

#ifdef P9_NO_REAL_T
// Builds without C++ (WebAssembly): double only.
int p9_real_parse(const char* text) { return !text || !*text || !strcmp(text, "double") ? P9_REAL_DOUBLE : -1; }
const char* p9_real_name(int real) { return real == P9_REAL_DOUBLE ? "double" : "?"; }
void p9_cpu_block_t(int real, p9_body* tp, int* alive, int ntp, int np, const double* gm, const double* r2enc, const double* r2col, double mu0,
                    const double* tab, int nb, unsigned long long step0, double dt, int check_every, double rin2, double rout2, int smooth) {
    (void)real, (void)tp, (void)alive, (void)ntp, (void)np, (void)gm, (void)r2enc, (void)r2col, (void)mu0, (void)tab, (void)nb, (void)step0, (void)dt,
        (void)check_every, (void)rin2, (void)rout2, (void)smooth;
}
#endif

// Flyby records (method step), one line per test particle of the input:
// id, removed_step (0: alive), then per planet near/fast/close (planet ids in
// the header), last_fast_step, last_fast_planet_id (0: none), last_fast_dmin_au.
static int write_flybys(const char* path, const p9_flybys* F, const double* tp_ids, const int* alive, int ntp, int np, const double* ids) {
    FILE* f = fopen(path, "w");
    if (!f) {
        perror(path);
        return 1;
    }
    fprintf(f, "id\tremoved_step");
    for (int j = 0; j < np; j++) fprintf(f, "\tnear_%.0f\tfast_%.0f\tclose_%.0f", ids[j], ids[j], ids[j]);
    fprintf(f, "\tlast_fast_step\tlast_fast_planet\tlast_fast_dmin_au\tsub_steps\tsub_max\tsub_capped\n");
    for (int i = 0; i < ntp; i++) {
        fprintf(f, "%.0f\t%llu", tp_ids[i], alive[i] == 1 ? 0ULL : F->rm_step[i]);
        for (int j = 0; j < np; j++)
            fprintf(f, "\t%d\t%d\t%d", F->near[(size_t)i * np + j], F->fast[(size_t)i * np + j], F->close[(size_t)i * np + j]);
        fprintf(f, "\t%llu\t%.0f\t%.6g\t%d\t%d\t%d\n", F->last_step[i], F->last_j[i] ? ids[F->last_j[i] - 1] : 0.0, F->last_d[i], F->sub_steps[i],
                F->sub_max[i], F->sub_capped[i]);
    }
    return fclose(f) != 0;
}

// ------------------------------------------------------------------ run

static int run(const char* in, double t_end, long n_snap, const char* out, const char* state_out) {
    const char* mode_env = getenv("P9GPU_MODE");
#ifdef P9_NO_CUDA
    const int use_gpu = 0;
    if (mode_env && strcmp(mode_env, "cpu") != 0) {
        fprintf(stderr, "this build has no CUDA: only P9GPU_MODE=cpu\n");
        return 2;
    }
#else
    const int use_gpu = !(mode_env && strcmp(mode_env, "cpu") == 0);
#endif
    const int max_nb = getenv("P9GPU_BLOCK") ? atoi(getenv("P9GPU_BLOCK")) : 2000;
    const int real = p9_real_parse(getenv("P9GPU_REAL"));
    const char* method_env = getenv("P9_ENCOUNTER_METHOD");
    if (method_env && *method_env && strcmp(method_env, "kick") && strcmp(method_env, "step") && strcmp(method_env, "substep") &&
        strcmp(method_env, "smooth")) {
        fprintf(stderr, "P9_ENCOUNTER_METHOD: kick, step, substep or smooth\n");
        return 2;
    }
    const int sub_method = !method_env ? 0 : !strcmp(method_env, "substep") ? 1 : !strcmp(method_env, "smooth") ? 2 : 0;
    const int step_method = method_env && (!strcmp(method_env, "step") || sub_method);
    const char* remove_env = getenv("P9_ENCOUNTER_REMOVE");
    const int enc_remove = !(remove_env && !strcmp(remove_env, "0")) && !sub_method;
    if (!enc_remove && !step_method) {
        fprintf(stderr, "P9_ENCOUNTER_REMOVE=0 needs P9_ENCOUNTER_METHOD=step\n");
        return 2;
    }
    if (step_method && ((real != P9_REAL_DOUBLE && sub_method != 2) || getenv("P9_J2"))) {
        fprintf(stderr, "P9_ENCOUNTER_METHOD step and substep: model full, double only; smooth: model full, any number type\n");
        return 2;
    }
    if (real < 0) {
        fprintf(stderr, "P9GPU_REAL: double, double-t, float or df64 (this build: %s)\n", p9_real_parse("df64") < 0 ? "double only" : "all");
        return 2;
    }
    struct reb_simulation* r = reb_simulation_create_from_file((char*)in, -1);
    if (!r) {
        fprintf(stderr, "%s: can not load\n", in);
        return 2;
    }
    if (r->N_active < 2 || r->N_active - 1 > P9_MAX_PLANETS || n_snap < 1 || !(t_end > r->t)) {
        fprintf(stderr, "need 1..%d planets, n_snapshots >= 1 and t_end > t\n", P9_MAX_PLANETS);
        return 2;
    }
    const int ntp = (int)(r->N - r->N_active);
    const double dt = r->dt;
    double r2enc[P9_MAX_PLANETS] = {0}, renc[P9_MAX_PLANETS] = {0}, ids[P9_MAX_PLANETS];
    for (size_t j = 0; j + 1 < r->N_active; j++) ids[j] = r->particles[j + 1].r;  // ids of the massive bodies after the Sun
    if (p9_encounter_radii(getenv("P9_ENCOUNTER_RADII"), (int)r->N_active - 1, ids, renc, r2enc)) return 2;
    if (getenv("P9_ENCOUNTER_RADII") && *getenv("P9_ENCOUNTER_RADII")) p9_encounter_print((int)r->N_active - 1, ids, renc);
    double r2col[P9_MAX_PLANETS] = {0}, rcol[P9_MAX_PLANETS] = {0};
    if (getenv("P9_COLLISION_RADII") && *getenv("P9_COLLISION_RADII")) {
        if (sub_method != 2) {
            fprintf(stderr, "P9_COLLISION_RADII: method smooth only\n");
            return 2;
        }
        if (p9_encounter_radii(getenv("P9_COLLISION_RADII"), (int)r->N_active - 1, ids, rcol, r2col)) return 2;
        for (size_t j = 0; j + 1 < r->N_active; j++) printf("collision_radius id=%.0f au=%.10g\n", ids[j], rcol[j]);
    }
    planets P;
    com_t com;
    p9_body* tp = malloc(sizeof(p9_body) * (ntp > 0 ? ntp : 1));
    int* alive = malloc(sizeof(int) * (ntp > 0 ? ntp : 1));
    int* was_alive = malloc(sizeof(int) * (ntp > 0 ? ntp : 1));
    for (int i = 0; i < ntp; i++) alive[i] = was_alive[i] = 1;
    double* tp_ids = malloc(sizeof(double) * (ntp > 0 ? ntp : 1));  // ids of the test particles in input order
    for (int i = 0; i < ntp; i++) tp_ids[i] = r->particles[r->N_active + i].r;
    to_dh(r, &P, tp, ntp, &com);
    if (getenv("P9_CAPPED_OUT") && *getenv("P9_CAPPED_OUT")) {
        if (use_gpu || real != P9_REAL_DOUBLE || sub_method != 2) {
            fprintf(stderr, "P9_CAPPED_OUT: method smooth, P9GPU_MODE=cpu, double only\n");
            return 2;
        }
        if (!(cap_out = fopen(getenv("P9_CAPPED_OUT"), "w"))) {
            perror(getenv("P9_CAPPED_OUT"));
            return 2;
        }
        fprintf(cap_out, "id\tstep\tplanet\tq_est_au\td_min_au\tq_loc_au\tv_est_au_yr\tn_want\n");
        cap_tp_ids = tp_ids, cap_ids = ids;
    }
    P.j2 = 0;
    const char* j2env = getenv("P9_J2");
    if (j2env && *j2env) {
        char* e = (char*)j2env;
        for (int k = 0; k < 5; k++) {
            char* end;
            P.j2v[k] = strtod(e, &end);
            if (end == e || (k < 4 && *end != ',') || (k == 4 && *end)) {
                fprintf(stderr, "P9_J2: muJ2R2,nx,ny,nz,r_remove\n");
                return 2;
            }
            e = end + 1;
        }
        P.j2v[4] = P.j2v[4] * P.j2v[4];
        P.j2 = 1;
        if (real != P9_REAL_DOUBLE) {
            fprintf(stderr, "P9_J2: double only\n");
            return 2;
        }
        printf("model j2 muJ2R2=%.17g n=%.17g,%.17g,%.17g r_remove2=%.17g\n", P.j2v[0], P.j2v[1], P.j2v[2], P.j2v[3], P.j2v[4]);
    }
    const double e0 = p9_energy_massive(r);
    // keep every body half a drift ahead (whdh.h)
    const char* ks_env = getenv("P9_PLANET_SUBSTEPS");
    P.ksub = ks_env && *ks_env ? atoi(ks_env) : 1;
    if (P.ksub < 1 || (P.ksub > 1 && P.ksub % 2)) {
        fprintf(stderr, "P9_PLANET_SUBSTEPS: 1 or an even number\n");
        return 2;
    }
    if (P.ksub == 1)
        for (int i = 0; i < P.np; i++) p9_kepler(&P.b[i], P.mu0, 0.5 * dt);  // planets half a drift ahead, as the test particles
    for (int i = 0; i < ntp; i++) p9_kepler(&tp[i], P.mu0, 0.5 * dt);
    p9_body* sync_tp = malloc(sizeof(p9_body) * (ntp > 0 ? ntp : 1));
    const double t0 = r->t;
    unsigned long long steps = r->steps_done;
    const unsigned long long steps0 = steps;
    double t = r->t;
    const size_t tab_doubles = (size_t)max_nb * P.np * 9 + (size_t)max_nb * 6;
    const size_t m1 = (size_t)(ntp > 0 ? ntp : 1);
    p9_flybys F = {calloc(m1 * P.np, sizeof(int)), calloc(m1 * P.np, sizeof(int)), calloc(m1 * P.np, sizeof(int)), calloc(m1, sizeof(int)),
                   calloc(m1, sizeof(unsigned long long)), calloc(m1, sizeof(unsigned long long)), calloc(m1, sizeof(double)),
                   calloc(m1, sizeof(int)), calloc(m1, sizeof(int)), calloc(m1, sizeof(int))};
    int *near = F.near, *fast = F.fast;
    double* cpu_tab = use_gpu ? NULL : malloc(sizeof(double) * tab_doubles);
    char err[256] = "";
#ifndef P9_NO_CUDA
    p9g* g = NULL;
    if (use_gpu) {
        g = p9g_create(ntp, tp, alive, P.np, P.gm, r2enc, max_nb, real, err, sizeof err);
        if (!g) {
            fprintf(stderr, "GPU: %s\n", err);
            return 3;
        }
        fprintf(stderr, "device: %s\n", p9g_name(g));
        if (step_method && p9g_set_step_method(g, enc_remove, sub_method, err, sizeof err)) {
            fprintf(stderr, "GPU: %s\n", err);
            return 3;
        }
        if (sub_method == 2 && p9g_set_collision(g, r2col, err, sizeof err)) {
            fprintf(stderr, "GPU: %s\n", err);
            return 3;
        }
        if (P.j2 && p9g_set_j2(g, P.j2v, err, sizeof err)) {
            fprintf(stderr, "GPU: %s\n", err);
            return 3;
        }
    }
#endif
    remove(out);
    struct sha256_ctx ctx;
    sha256_init(&ctx);
    const double w0 = now_s();
    double planet_s = 0;
    for (long k = 1; k <= n_snap; k++) {
        const double tk = t0 + (t_end - t0) * (double)k / (double)n_snap;
        // steps to the first t >= tk, with t advanced by dt per step (as REBOUND does)
        long need = 0;
        while (t < tk) {
            t += dt;
            need++;
        }
        while (need > 0) {
            const int nb = need < max_nb ? (int)need : max_nb;
            const double p0 = now_s();
#ifndef P9_NO_CUDA
            if (use_gpu) {
                double* tab = p9g_next_table(g);
                planets_block(&P, dt, nb, tab);
                planet_s += now_s() - p0;
                if (p9g_launch(g, nb, steps, dt, P.mu0, CHECK_EVERY, R_IN * R_IN, R_OUT * R_OUT, err, sizeof err)) {
                    fprintf(stderr, "GPU: %s\n", err);
                    return 3;
                }
            } else
#endif
            {
                planets_block(&P, dt, nb, cpu_tab);
                planet_s += now_s() - p0;
                if (real == P9_REAL_DOUBLE)
                    cpu_block(tp, alive, ntp, &P, r2enc, r2col, cpu_tab, nb, steps, dt, step_method + sub_method, enc_remove, &F);
                else
                    p9_cpu_block_t(real, tp, alive, ntp, P.np, P.gm, r2enc, r2col, P.mu0, cpu_tab, nb, steps, dt, CHECK_EVERY, R_IN * R_IN, R_OUT * R_OUT,
                                   sub_method == 2);
            }
            steps += (unsigned long long)nb;
            need -= nb;
        }
#ifndef P9_NO_CUDA
        if (use_gpu && p9g_download(g, tp, alive, err, sizeof err)) {
            fprintf(stderr, "GPU: %s\n", err);
            return 3;
        }
#endif
        drop_dead(r, alive, was_alive, ntp);
        // the synchronous states for the output; the integration continues from the others
        planets Ps = P;
        if (P.ksub == 1)
            for (int i = 0; i < P.np; i++) Ps.b[i] = p9_synchronous(P.b[i], P.mu0, dt);  // else they are synchronous already
        for (int i = 0; i < ntp; i++) sync_tp[i] = alive[i] == 1 ? p9_synchronous(tp[i], P.mu0, dt) : tp[i];
        from_dh(r, &Ps, sync_tp, alive, ntp, &com, t - t0);
        r->t = t;
        r->steps_done = steps;
        reb_simulation_save_to_file(r, out);
        p9_state_hash(r, &ctx, NULL);
        fprintf(stderr, "snapshot %ld/%ld t=%.6g N=%zu wall=%.1fs\n", k, n_snap, r->t, r->N, now_s() - w0);
    }
    uint8_t d[32];
    char h[65], hs[65] = "";
    sha256_final(&ctx, d);
    p9_hex(d, h);
    if (state_out) {
        FILE* f = fopen(state_out, "wb");
        struct sha256_ctx c2;
        sha256_init(&c2);
        p9_state_hash(r, &c2, f);
        fclose(f);
        uint8_t d2[32];
        sha256_final(&c2, d2);
        p9_hex(d2, hs);
    }
    size_t removed = 0, removed_enc = 0, removed_inner = 0, by[P9_MAX_PLANETS + 1] = {0};
    for (int i = 0; i < ntp; i++) {
        removed += alive[i] != 1, removed_enc += alive[i] < 0, removed_inner += alive[i] == -1 - P.np;
        if (alive[i] < 0 && -1 - alive[i] < P.np) by[-1 - alive[i]]++;
    }
    // removals by close encounter per planet, by body id
    char by_text[256] = "";
    for (int j = 0; j < P.np; j++)
        snprintf(by_text + strlen(by_text), sizeof by_text - strlen(by_text), "%s%.0f:%zu", j ? "," : "", ids[j], by[j]);
    // method "step": closest approaches within three removal radii, and those shorter than 1.5 steps
#ifndef P9_NO_CUDA
    if (use_gpu && step_method && p9g_counts(g, &F, err, sizeof err)) {
        fprintf(stderr, "GPU: %s\n", err);
        return 3;
    }
#endif
    long long n_sub = 0, n_capped = 0;
    int sub_max = 1;
    for (int i = 0; i < ntp; i++) {
        n_sub += F.sub_steps[i], n_capped += F.sub_capped[i];
        if (F.sub_max[i] > sub_max) sub_max = F.sub_max[i];
    }
    char near_text[256] = "", fast_text[256] = "", close_text[256] = "";
    for (int j = 0; j < P.np; j++) {
        long long sn = 0, sf = 0, sc = 0;
        for (int i = 0; i < ntp; i++) sn += near[(size_t)i * P.np + j], sf += fast[(size_t)i * P.np + j], sc += F.close[(size_t)i * P.np + j];
        snprintf(near_text + strlen(near_text), sizeof near_text - strlen(near_text), "%s%.0f:%lld", j ? "," : "", ids[j], sn);
        snprintf(fast_text + strlen(fast_text), sizeof fast_text - strlen(fast_text), "%s%.0f:%lld", j ? "," : "", ids[j], sf);
        snprintf(close_text + strlen(close_text), sizeof close_text - strlen(close_text), "%s%.0f:%lld", j ? "," : "", ids[j], sc);
    }
    if (step_method && getenv("P9_FLYBY_OUT") && *getenv("P9_FLYBY_OUT") && write_flybys(getenv("P9_FLYBY_OUT"), &F, tp_ids, alive, ntp, P.np, ids))
        return 2;
    if (cap_out && fclose(cap_out)) return 2;
    if (getenv("P9_REMOVED_OUT") && *getenv("P9_REMOVED_OUT")) {
        FILE* f = fopen(getenv("P9_REMOVED_OUT"), "w");
        if (!f) return 2;
        fprintf(f, "id\tfate\n");
        for (int i = 0; i < ntp; i++) {
            if (alive[i] == 1) fprintf(f, "%.0f\talive\n", tp_ids[i]);
            else if (alive[i] == 0) fprintf(f, "%.0f\tdistance\n", tp_ids[i]);
            else if (-1 - alive[i] < P.np) fprintf(f, "%.0f\t%s:%.0f\n", tp_ids[i], sub_method == 2 ? "collision" : "encounter", ids[-1 - alive[i]]);
            else fprintf(f, "%.0f\tinner\n", tp_ids[i]);
        }
        if (fclose(f)) return 2;
    }
    const double e1 = p9_energy_massive(r);
    printf("result_sha256=%s final_state_sha256=%s t=%.17g steps=%llu N_start=%zu N_end=%zu removed=%zu removed_encounter=%zu wall_s=%.3f "
           "dE_rel=%.3e mode=%s real=%s model=%s planet_substeps=%d removed_inner=%zu removed_by=%s collisions=%s encounter_method=%s encounter_remove=%d sub_steps=%lld sub_max=%d sub_capped=%lld flybys=%s fast_flybys=%s close_flybys=%s planet_s=%.3f "
           "program=p9gpu "
           "version=%s\n",
           h, hs, r->t, (unsigned long long)steps, (size_t)(P.np + 1 + ntp), r->N, removed, removed_enc, now_s() - w0, (e1 - e0) / e0,
           use_gpu ? "gpu" : "cpu", p9_real_name(real), P.j2 ? "j2" : "full", P.ksub, removed_inner, by_text, sub_method == 2 ? by_text : "-",
           sub_method == 2 ? "smooth" : sub_method ? "substep" : step_method ? "step" : "kick", enc_remove, n_sub, sub_max, n_capped, step_method ? near_text : "-", step_method ? fast_text : "-", step_method ? close_text : "-", planet_s, P9_VERSION);
    (void)steps0;
#ifndef P9_NO_CUDA
    if (g) p9g_free(g);
#endif
    free(tp);
    free(sync_tp);
    free(alive);
    free(was_alive);
    free(cpu_tab);
    free(F.near), free(F.fast), free(F.close), free(F.last_j), free(F.last_step), free(F.rm_step), free(F.last_d);
    free(F.sub_steps), free(F.sub_max), free(F.sub_capped);
    free(tp_ids);
    reb_simulation_free(r);
    return 0;
}

int main(int argc, char* argv[]) {
    if (argc == 2 && !strcmp(argv[1], "version")) return printf("program=p9gpu version=%s\n", P9_VERSION) < 0;
    if ((argc == 6 || argc == 7) && !strcmp(argv[1], "run")) return run(argv[2], strtod(argv[3], NULL), strtol(argv[4], NULL, 10), argv[5], argc == 7 ? argv[6] : NULL);
    fprintf(stderr, "usage: p9gpu run <in.sa> <t_end> <n_snapshots> <out.sa> [<out.state>]   (P9GPU_MODE=gpu|cpu, P9GPU_BLOCK=steps)\n");
    return 1;
}
