// SPDX-License-Identifier: GPL-3.0-or-later
// p9sim: orbit integrations for the MEDAS Planet 9 search (pilot), on REBOUND.
//
//   p9sim init <ic.txt> <out.sa>
//       Builds the start state from a text file of exact decimal values (see
//       tools/make_ic.py) and writes it as a REBOUND SimulationArchive. All
//       integration settings live in that file, so a job needs nothing else.
//
//   p9sim run <in.sa> <t_end> <n_snapshots> <out.sa> [<out.state>]
//       Continues the last snapshot of <in.sa> up to <t_end> (years), writes
//       n_snapshots equally spaced snapshots to <out.sa> (SimulationArchive),
//       removes test particles that leave the region of interest (see below)
//       and prints one line of key=value results, among them
//         result_sha256: SHA-256 over the canonical states of all snapshots,
//       the number to compare between machines.
//
//   p9sim state <in.sa> <snapshot>
//       Prints the canonical state hash of one snapshot.
//
//   p9sim last <in.sa> <out.sa>
//       Writes the last snapshot of <in.sa> as a new archive of one snapshot:
//       the input of the next segment of a long run.
//
//   p9sim sha256 <file>
//       Prints the SHA-256 of a file (for machines without sha256sum).
//
//   p9sim dump <in.sa> <snapshot>
//       Prints t, then one line per particle: name id m x y z vx vy vz (%.17g,
//       exact), for the analysis (tools/analyze.py). Snapshot -1: the last.
//
// Canonical state (independent of REBOUND's file layout, wall times and
// random seeds stored in a SimulationArchive): "P9STATE2", t, N, then per
// particle its id (uint64), m, x, y, z, vx, vy, vz; doubles as IEEE-754
// binary64, everything little endian.
//
// Particle ids: `init` numbers the particles of the start file 0, 1, 2, …
// and stores the number in the particle's radius r, which WHFast does not use
// (no collisions). Names are kept for reading, but not hashed: REBOUND 5.2.2
// restores names from a SimulationArchive through stored pointers
// (binarydata.c, REB_CHARP_LIST), which fails when the reading machine has
// another pointer size (WebAssembly is 32-bit): the names come out shifted.
//
// Reproducibility: integration uses only + - * / and sqrt (exact in IEEE-754)
// once the start state exists; build without -ffast-math and with
// -ffp-contract=off (no fused multiply-add), see Makefile.

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "rebound.h"
#include "sha256.h"
#include "p9state.h"
#include "p9encounter.h"


// Test particles are removed when they leave this region (au): beyond
// R_OUT they are effectively lost to the Oort cloud, inside R_IN they reach
// the giant planets' region where WHFast without close-encounter handling is
// not meant to follow them. Checked every CHECK_EVERY steps, so the removal
// happens at the same steps on every machine.
#define R_OUT 10000.0
#define R_IN 5.0
#define CHECK_EVERY 1000

static size_t n_removed = 0;
static size_t n_removed_encounter = 0;
static double enc_r2[16];        // squared encounter radii of the massive bodies 1..N_active-1 (0: no check)
static int* enc_flag = NULL;     // per particle index: planet index + 1 of an encounter at the last kick
static size_t enc_flag_n = 0;

// Called by REBOUND inside every WHFast step, right before the kick, with the
// positions of the middle of the step (after the first jump): the
// close-encounter criterion of p9encounter.h. It only marks particles; the
// heartbeat after the step removes them. Forces are not changed.
static void encounter_check(struct reb_simulation* r) {
    if (enc_flag_n < r->N) {
        enc_flag = realloc(enc_flag, sizeof(int) * r->N);
        enc_flag_n = r->N;
    }
    for (size_t i = r->N_active; i < r->N; i++) {
        const struct reb_particle* p = &r->particles[i];
        int hit = 0;
        for (size_t j = 1; j < r->N_active && !hit; j++) {
            if (enc_r2[j - 1] == 0.0) continue;
            const struct reb_particle* q = &r->particles[j];
            const double dx = q->x - p->x, dy = q->y - p->y, dz = q->z - p->z;
            if (dx * dx + dy * dy + dz * dz < enc_r2[j - 1]) hit = (int)j;
        }
        enc_flag[i] = hit;
    }
}

static void heartbeat(struct reb_simulation* r) {
    if (enc_flag) {
        // encounters found at this step's kick (from the end, so indices stay valid)
        for (size_t i = r->N; i-- > r->N_active;) {
            if (i < enc_flag_n && enc_flag[i]) {
                reb_simulation_remove_particle(r, i);
                n_removed++;
                n_removed_encounter++;
            }
        }
        for (size_t i = 0; i < enc_flag_n; i++) enc_flag[i] = 0;
    }
    if (r->steps_done % CHECK_EVERY != 0) return;
    // test particles only (index >= N_active), from the end so indices stay valid
    for (size_t i = r->N; i-- > r->N_active;) {
        const struct reb_particle* p = &r->particles[i];
        const struct reb_particle* s = &r->particles[0];
        const double dx = p->x - s->x, dy = p->y - s->y, dz = p->z - s->z;
        const double d2 = dx * dx + dy * dy + dz * dz;
        if (d2 > R_OUT * R_OUT || d2 < R_IN * R_IN) {
            reb_simulation_remove_particle(r, i);  // keeps the order of the others
            n_removed++;
        }
    }
}

static int cmd_init(const char* ic, const char* out) {
    FILE* f = fopen(ic, "r");
    if (!f) {
        perror(ic);
        return 2;
    }
    struct reb_simulation* r = reb_simulation_create();
    char key[64];
    double G = 0, dt = 0;
    long n_active = -1;
    unsigned corrector = 0;
    char line[512];
    while (fgets(line, sizeof line, f)) {
        if (line[0] == '#' || line[0] == '\n') continue;
        if (sscanf(line, "%63s", key) != 1) continue;
        if (!strcmp(key, "G")) sscanf(line, "%*s %lf", &G);
        else if (!strcmp(key, "dt")) sscanf(line, "%*s %lf", &dt);
        else if (!strcmp(key, "N_active")) sscanf(line, "%*s %ld", &n_active);
        else if (!strcmp(key, "corrector")) sscanf(line, "%*s %u", &corrector);
        else if (!strcmp(key, "p")) {
            char name[32];
            struct reb_particle p = {0};
            // strtod reads %.17g exactly (correctly rounded) on every C99 library
            if (sscanf(line, "%*s %31s %lf %lf %lf %lf %lf %lf %lf", name, &p.m, &p.x, &p.y, &p.z, &p.vx, &p.vy, &p.vz) != 8) {
                fprintf(stderr, "bad particle line: %s", line);
                return 2;
            }
            p.r = (double)r->N;  // particle id: its line number among the particles, 0-based
            reb_simulation_add(r, p);
            reb_particle_set_name(&r->particles[r->N - 1], name);
        }
    }
    fclose(f);
    if (G <= 0 || dt <= 0 || n_active < 1) {
        fprintf(stderr, "%s: G, dt and N_active are required\n", ic);
        return 2;
    }
    r->G = G;
    r->dt = dt;
    r->N_active = (size_t)n_active;
    r->testparticle_type = 0;  // massive bodies do not feel test particles
    r->force_is_velocity_dependent = 0;
    reb_simulation_set_integrator(r, "whfast");
    struct reb_integrator_whfast_state* w = r->integrator.state;
    w->coordinates = REB_INTEGRATOR_WHFAST_COORDINATES_DEMOCRATICHELIOCENTRIC;
    w->safe_mode = 1;
    w->corrector = corrector;
    reb_simulation_save_to_file(r, out);
    printf("init: N=%zu N_active=%zu G=%.17g dt=%.17g -> %s\n", r->N, r->N_active, r->G, r->dt, out);
    reb_simulation_free(r);
    return 0;
}

static double now_s(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + 1e-9 * ts.tv_nsec;
}

static int cmd_run(const char* in, double t_end, long n_snap, const char* out, const char* state_out) {
    struct reb_simulation* r = reb_simulation_create_from_file((char*)in, -1);
    if (!r) {
        fprintf(stderr, "%s: can not load\n", in);
        return 2;
    }
    if (n_snap < 1 || !(t_end > r->t)) {
        fprintf(stderr, "need n_snapshots >= 1 and t_end > t (%.17g)\n", r->t);
        return 2;
    }
    r->heartbeat = heartbeat;
    if (r->N_active - 1 > 16 || p9_encounter_radii(getenv("P9_ENCOUNTER_RADII"), (int)r->N_active - 1, enc_r2)) return 2;
    for (size_t j = 0; j + 1 < r->N_active; j++)
        if (enc_r2[j] > 0.0) r->additional_forces = encounter_check;
    const double e0 = reb_simulation_energy(r);  // test particles are massless: the planets' energy
    remove(out);
    struct sha256_ctx ctx;
    sha256_init(&ctx);
    const double t0 = r->t;
    const double w0 = now_s();
    size_t N0 = r->N;
    for (long k = 1; k <= n_snap; k++) {
        // snapshot times as t0 + k*(t_end-t0)/n: exact for the decimal values used
        const double tk = t0 + (t_end - t0) * (double)k / (double)n_snap;
        r->exact_finish_time = 0;  // WHFast keeps a fixed step: stop at the first step >= tk
        enum REB_STATUS st = reb_simulation_integrate(r, tk);
        if (st != REB_STATUS_SUCCESS && st != REB_STATUS_PAUSED) {
            fprintf(stderr, "integration stopped with status %d at t=%.17g\n", (int)st, r->t);
            return 3;
        }
        reb_simulation_synchronize(r);
        reb_simulation_save_to_file(r, out);
        p9_state_hash(r, &ctx, NULL);
        fprintf(stderr, "snapshot %ld/%ld t=%.6g N=%zu removed=%zu wall=%.1fs\n", k, n_snap, r->t, r->N, n_removed, now_s() - w0);
    }
    uint8_t d[32];
    char h[65];
    sha256_final(&ctx, d);
    p9_hex(d, h);
    char hs[65] = "";
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
    const double e1 = reb_simulation_energy(r);
    printf("result_sha256=%s final_state_sha256=%s t=%.17g steps=%llu N_start=%zu N_end=%zu removed=%zu removed_encounter=%zu wall_s=%.3f "
           "dE_rel=%.3e program=p9sim version=%s\n",
           h, hs, r->t, (unsigned long long)r->steps_done, N0, r->N, n_removed, n_removed_encounter, now_s() - w0, (e1 - e0) / e0, P9_VERSION);
    reb_simulation_free(r);
    return 0;
}

static int cmd_state(const char* in, long snap) {
    struct reb_simulation* r = reb_simulation_create_from_file((char*)in, snap);
    if (!r) return 2;
    struct sha256_ctx ctx;
    sha256_init(&ctx);
    p9_state_hash(r, &ctx, NULL);
    uint8_t d[32];
    char h[65];
    sha256_final(&ctx, d);
    p9_hex(d, h);
    printf("state_sha256=%s t=%.17g N=%zu\n", h, r->t, r->N);
    reb_simulation_free(r);
    return 0;
}

static int cmd_last(const char* in, const char* out) {
    struct reb_simulation* r = reb_simulation_create_from_file((char*)in, -1);
    if (!r) return 2;
    remove(out);
    reb_simulation_save_to_file(r, out);
    reb_simulation_free(r);
    return 0;
}

static int cmd_sha256(const char* path) {
    FILE* f = fopen(path, "rb");
    if (!f) {
        perror(path);
        return 2;
    }
    struct sha256_ctx ctx;
    sha256_init(&ctx);
    uint8_t buf[65536];
    size_t n;
    while ((n = fread(buf, 1, sizeof buf, f)) > 0) sha256_update(&ctx, buf, n);
    fclose(f);
    uint8_t d[32];
    char h[65];
    sha256_final(&ctx, d);
    p9_hex(d, h);
    printf("%s  %s\n", h, path);
    return 0;
}

static int cmd_dump(const char* in, long snap) {
    struct reb_simulation* r = reb_simulation_create_from_file((char*)in, snap);
    if (!r) return 2;
    printf("t %.17g\n", r->t);
    for (size_t i = 0; i < r->N; i++) {
        const struct reb_particle* p = &r->particles[i];
        printf("%s %.0f %.17g %.17g %.17g %.17g %.17g %.17g %.17g\n", p->name ? p->name : "-", p->r, p->m, p->x, p->y, p->z, p->vx, p->vy, p->vz);
    }
    reb_simulation_free(r);
    return 0;
}

int main(int argc, char* argv[]) {
    if (argc == 4 && !strcmp(argv[1], "init")) return cmd_init(argv[2], argv[3]);
    if ((argc == 6 || argc == 7) && !strcmp(argv[1], "run")) return cmd_run(argv[2], strtod(argv[3], NULL), strtol(argv[4], NULL, 10), argv[5], argc == 7 ? argv[6] : NULL);
    if (argc == 4 && !strcmp(argv[1], "state")) return cmd_state(argv[2], strtol(argv[3], NULL, 10));
    if (argc == 2 && !strcmp(argv[1], "version")) return printf("program=p9sim version=%s\n", P9_VERSION) < 0;
    if (argc == 4 && !strcmp(argv[1], "last")) return cmd_last(argv[2], argv[3]);
    if (argc == 3 && !strcmp(argv[1], "sha256")) return cmd_sha256(argv[2]);
    if (argc == 4 && !strcmp(argv[1], "dump")) return cmd_dump(argv[2], strtol(argv[3], NULL, 10));
    fprintf(stderr, "usage: p9sim init <ic.txt> <out.sa> | run <in.sa> <t_end> <n_snapshots> <out.sa> [<out.state>] | last <in.sa> <out.sa> | sha256 <file> | state <in.sa> <snapshot> | dump <in.sa> <snapshot>\n");
    return 1;
}
