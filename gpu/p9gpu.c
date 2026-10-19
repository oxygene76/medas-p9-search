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
static void planets_step(planets* P, double dt, double* wa, double* q, double* wb) {
    const double h = 0.5 * dt;
    planets_w(P, wa);
    for (int i = 0; i < P->np; i++) p9_jump(&P->b[i], wa, h);
    planets_positions(P, q);
    planets_kick(P, dt);
    planets_w(P, wb);
    for (int i = 0; i < P->np; i++) p9_jump(&P->b[i], wb, h);
    for (int i = 0; i < P->np; i++) p9_kepler(&P->b[i], P->mu0, dt);
}

// Fills a table for nb steps: q[nb*np*3], then wa[nb*3], then wb[nb*3].
static void planets_block(planets* P, double dt, int nb, double* tab) {
    const int np = P->np;
    double* q = tab;
    double* wa = tab + (size_t)nb * np * 3;
    double* wb = wa + (size_t)nb * 3;
    for (int k = 0; k < nb; k++) planets_step(P, dt, wa + 3 * k, q + (size_t)k * np * 3, wb + 3 * k);
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

static void cpu_block(p9_body* tp, int* alive, int ntp, const planets* P, const double* r2enc, const double* tab, int nb, unsigned long long step0,
                      double dt) {
    const int np = P->np;
    const double* q = tab;
    const double* wa = tab + (size_t)nb * np * 3;
    const double* wb = wa + (size_t)nb * 3;
    for (int i = 0; i < ntp; i++) {
        if (alive[i] != 1) continue;
        p9_body p = tp[i];
        int a = 1;
        for (int k = 0; k < nb; k++) {
            const int enc = p9_step_tp(&p, q + (size_t)k * np * 3, wa + 3 * k, wb + 3 * k, P->gm, r2enc, np, P->mu0, dt);
            if (enc >= 0) {
                a = -1 - enc;
                break;
            }
            if ((step0 + k + 1) % CHECK_EVERY == 0) {
                const p9_body x = p9_synchronous(p, P->mu0, dt);
                const double r2 = x.x * x.x + x.y * x.y + x.z * x.z;
                if (r2 > R_OUT * R_OUT || r2 < R_IN * R_IN) {
                    a = 0;
                    break;
                }
            }
        }
        tp[i] = p;
        alive[i] = a;
    }
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
    double r2enc[P9_MAX_PLANETS] = {0};
    if (p9_encounter_radii(getenv("P9_ENCOUNTER_RADII"), (int)r->N_active - 1, r2enc)) return 2;
    planets P;
    com_t com;
    p9_body* tp = malloc(sizeof(p9_body) * (ntp > 0 ? ntp : 1));
    int* alive = malloc(sizeof(int) * (ntp > 0 ? ntp : 1));
    int* was_alive = malloc(sizeof(int) * (ntp > 0 ? ntp : 1));
    for (int i = 0; i < ntp; i++) alive[i] = was_alive[i] = 1;
    to_dh(r, &P, tp, ntp, &com);
    const double e0 = p9_energy_massive(r);
    // keep every body half a drift ahead (whdh.h)
    for (int i = 0; i < P.np; i++) p9_kepler(&P.b[i], P.mu0, 0.5 * dt);
    for (int i = 0; i < ntp; i++) p9_kepler(&tp[i], P.mu0, 0.5 * dt);
    p9_body* sync_tp = malloc(sizeof(p9_body) * (ntp > 0 ? ntp : 1));
    const double t0 = r->t;
    unsigned long long steps = r->steps_done;
    const unsigned long long steps0 = steps;
    double t = r->t;
    const size_t tab_doubles = (size_t)max_nb * P.np * 3 + (size_t)max_nb * 6;
    double* cpu_tab = use_gpu ? NULL : malloc(sizeof(double) * tab_doubles);
    char err[256] = "";
#ifndef P9_NO_CUDA
    p9g* g = NULL;
    if (use_gpu) {
        g = p9g_create(ntp, tp, alive, P.np, P.gm, r2enc, max_nb, err, sizeof err);
        if (!g) {
            fprintf(stderr, "GPU: %s\n", err);
            return 3;
        }
        fprintf(stderr, "device: %s\n", p9g_name(g));
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
                cpu_block(tp, alive, ntp, &P, r2enc, cpu_tab, nb, steps, dt);
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
        for (int i = 0; i < P.np; i++) Ps.b[i] = p9_synchronous(P.b[i], P.mu0, dt);
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
    size_t removed = 0, removed_enc = 0;
    for (int i = 0; i < ntp; i++) removed += alive[i] != 1, removed_enc += alive[i] < 0;
    const double e1 = p9_energy_massive(r);
    printf("result_sha256=%s final_state_sha256=%s t=%.17g steps=%llu N_start=%zu N_end=%zu removed=%zu removed_encounter=%zu wall_s=%.3f "
           "dE_rel=%.3e mode=%s planet_s=%.3f program=p9gpu version=%s\n",
           h, hs, r->t, (unsigned long long)steps, (size_t)(P.np + 1 + ntp), r->N, removed, removed_enc, now_s() - w0, (e1 - e0) / e0,
           use_gpu ? "gpu" : "cpu", planet_s, P9_VERSION);
    (void)steps0;
#ifndef P9_NO_CUDA
    if (g) p9g_free(g);
#endif
    free(tp);
    free(sync_tp);
    free(alive);
    free(was_alive);
    free(cpu_tab);
    reb_simulation_free(r);
    return 0;
}

int main(int argc, char* argv[]) {
    if (argc == 2 && !strcmp(argv[1], "version")) return printf("program=p9gpu version=%s\n", P9_VERSION) < 0;
    if ((argc == 6 || argc == 7) && !strcmp(argv[1], "run")) return run(argv[2], strtod(argv[3], NULL), strtol(argv[4], NULL, 10), argv[5], argc == 7 ? argv[6] : NULL);
    fprintf(stderr, "usage: p9gpu run <in.sa> <t_end> <n_snapshots> <out.sa> [<out.state>]   (P9GPU_MODE=gpu|cpu, P9GPU_BLOCK=steps)\n");
    return 1;
}
