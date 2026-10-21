// SPDX-License-Identifier: GPL-3.0-or-later
// Direct comparison of p9gpu's integrator (gpu/whdh.h with the planets of
// gpu/p9gpu.c, fixed step, planets one step per dt) with REBOUND's WHFast
// (democratic heliocentric, safe_mode 1, as p9sim) on the same start values
// and step: docs/cause-analysis.md section 8. Diagnostics only; p9gpu's
// sources are included unchanged.
//
//   direct_wh step0 <in.sa>
//       the state after reading and converting (REBOUND's from_inertial
//       against p9gpu's to_dh), and each operator applied once to the same
//       state (Kepler drift, jump, interaction) in both codes
//   direct_wh pair <A.sa> <codeA> <offA> <B.sa> <codeB> <offB> <nsteps> <cmp_every> <out_every> <from> <to> <prefix>
//       integrates A and B in lockstep (code p9 or wh; test particles with
//       ids off+from .. off+to-1 of each file) and compares the synchronous
//       states every cmp_every steps: <prefix>.planets.tsv, <prefix>.tp.tsv
//       (first separation per test particle) and <prefix>.summary.tsv
//
// Build (make-like flags; tools/direct_wh.sh): -DP9_NO_CUDA -DP9_NO_REAL_T,
// with REBOUND's sources and src/p9state.c src/p9encounter.c src/sha256.c.

#define main p9gpu_main
#include "../gpu/p9gpu.c"
#undef main
#include "integrator_whfast.h"
#include "transformations.h"

#define NTHR 4
static const double THR[NTHR] = {1e-12, 1e-8, 1e-4, 1e-2};

// ------------------------------------------------------------------ one integrator behind a common interface
typedef struct {
    int wh;                     // 1: REBOUND WHFast, 0: p9gpu
    struct reb_simulation* r;   // the loaded simulation (WHFast integrates it)
    planets P;                  // p9: planets half a drift ahead
    com_t com;
    p9_body* tp;                // p9: test particles half a drift ahead
    int ntp;
    double dt;
    double tab[P9_MAX_PLANETS * 9 + 6];
} integ;

// Keeps the massive bodies and the test particles with ids off+from .. off+to-1 (in input order).
static struct reb_simulation* load(const char* path, double off, int from, int to) {
    struct reb_simulation* r = reb_simulation_create_from_file((char*)path, -1);
    if (!r) {
        fprintf(stderr, "%s: can not load\n", path);
        exit(2);
    }
    for (size_t i = r->N; i-- > r->N_active;) {
        const double id = r->particles[i].r - off;
        if (!(id >= from && id < to)) reb_simulation_remove_particle(r, i);
    }
    return r;
}

static void integ_init(integ* I, const char* path, const char* code, double off, int from, int to) {
    memset(I, 0, sizeof *I);
    I->wh = !strcmp(code, "wh");
    I->r = load(path, off, from, to);
    I->ntp = (int)(I->r->N - I->r->N_active);
    I->dt = I->r->dt;
    if (I->wh) {
        struct reb_integrator_whfast_state* w = I->r->integrator.state;
        if (strcmp(I->r->integrator.name, "whfast") || w->coordinates != REB_INTEGRATOR_WHFAST_COORDINATES_DEMOCRATICHELIOCENTRIC || !w->safe_mode ||
            w->corrector) {
            fprintf(stderr, "%s: not WHFast DH safe_mode without corrector\n", path);
            exit(2);
        }
        return;
    }
    I->tp = malloc(sizeof(p9_body) * (I->ntp > 0 ? I->ntp : 1));
    to_dh(I->r, &I->P, I->tp, I->ntp, &I->com);
    I->P.ksub = 1;
    for (int i = 0; i < I->P.np; i++) p9_kepler(&I->P.b[i], I->P.mu0, 0.5 * I->dt);
    for (int i = 0; i < I->ntp; i++) p9_kepler(&I->tp[i], I->P.mu0, 0.5 * I->dt);
}

static void integ_step(integ* I) {
    if (I->wh) {
        reb_simulation_steps(I->r, 1);
        return;
    }
    const int np = I->P.np;
    double *q = I->tab, *wa = q + np * 3, *wb = wa + 3, *uq = wb + 3, *uqb = uq + np * 3;
    planets_step(&I->P, I->dt, wa, q, wb, uq, uqb);
    static const double zero[P9_MAX_PLANETS] = {0};
    for (int i = 0; i < I->ntp; i++) p9_step_tp(&I->tp[i], q, wa, wb, I->P.gm, zero, np, I->P.mu0, I->dt);
}

// Synchronous democratic heliocentric state: s[0..np-1] planets, s[np..] test particles (Q, u).
static void integ_sync(integ* I, p9_body* s, int* np_out, double* m0, double* m, double* G) {
    if (I->wh) {
        struct reb_integrator_whfast_state* w = I->r->integrator.state;
        struct reb_simulation* r = I->r;
        // after a step with safe_mode the inertial particles are synchronous; convert as WHFast does
        struct reb_particle* ph = malloc(sizeof(struct reb_particle) * r->N);
        reb_transformations_inertial_to_democraticheliocentric_posvel(r->particles, ph, r->N, r->N_active);
        for (size_t i = 1; i < r->N; i++) s[i - 1] = (p9_body){ph[i].x, ph[i].y, ph[i].z, ph[i].vx, ph[i].vy, ph[i].vz};
        free(ph);
        (void)w;
        *np_out = (int)r->N_active - 1;
        *m0 = r->particles[0].m;
        for (size_t i = 1; i < r->N_active; i++) m[i - 1] = r->particles[i].m;
        *G = r->G;
        return;
    }
    for (int i = 0; i < I->P.np; i++) s[i] = p9_synchronous(I->P.b[i], I->P.mu0, I->dt);
    for (int i = 0; i < I->ntp; i++) s[I->P.np + i] = p9_synchronous(I->tp[i], I->P.mu0, I->dt);
    *np_out = I->P.np;
    *m0 = I->P.m0;
    for (int i = 0; i < I->P.np; i++) m[i] = I->P.m[i];
    *G = I->P.G;
}

// ------------------------------------------------------------------ elements (heliocentric, from Q and u)
typedef struct {
    double a, e, inc, Om, varpi, q;
} elem;

static elem elements_of(double mu, const double* r, const double* v) {
    elem E;
    const double rr = sqrt(r[0] * r[0] + r[1] * r[1] + r[2] * r[2]);
    const double v2 = v[0] * v[0] + v[1] * v[1] + v[2] * v[2];
    const double h[3] = {r[1] * v[2] - r[2] * v[1], r[2] * v[0] - r[0] * v[2], r[0] * v[1] - r[1] * v[0]};
    const double hn = sqrt(h[0] * h[0] + h[1] * h[1] + h[2] * h[2]);
    E.a = 1.0 / (2.0 / rr - v2 / mu);
    const double ev[3] = {(v[1] * h[2] - v[2] * h[1]) / mu - r[0] / rr, (v[2] * h[0] - v[0] * h[2]) / mu - r[1] / rr,
                          (v[0] * h[1] - v[1] * h[0]) / mu - r[2] / rr};
    E.e = sqrt(ev[0] * ev[0] + ev[1] * ev[1] + ev[2] * ev[2]);
    E.inc = acos(fmax(-1.0, fmin(1.0, h[2] / hn))) * 180.0 / M_PI;
    E.Om = fmod(atan2(h[0], -h[1]) * 180.0 / M_PI + 360.0, 360.0);
    E.varpi = fmod(atan2(ev[1], ev[0]) * 180.0 / M_PI + 360.0, 360.0);
    E.q = E.a * (1.0 - E.e);
    return E;
}

// Heliocentric velocity from the barycentric one: v_h = u + sum_j m_j u_j / m0.
static void helio(const p9_body* s, int np, double m0, const double* m, int k, double* r, double* v) {
    double W[3] = {0, 0, 0};
    for (int j = 0; j < np; j++) W[0] += m[j] * s[j].vx, W[1] += m[j] * s[j].vy, W[2] += m[j] * s[j].vz;
    r[0] = s[k].x, r[1] = s[k].y, r[2] = s[k].z;
    v[0] = s[k].vx + W[0] / m0, v[1] = s[k].vy + W[1] / m0, v[2] = s[k].vz + W[2] / m0;
}

static double angdiff(double a, double b) {
    double d = fmod(a - b + 540.0, 360.0) - 180.0;
    return d;
}

static double reldiff(const p9_body* a, const p9_body* b) {
    const double dx = a->x - b->x, dy = a->y - b->y, dz = a->z - b->z;
    return sqrt((dx * dx + dy * dy + dz * dz) / (a->x * a->x + a->y * a->y + a->z * a->z));
}
static double reldiffv(const p9_body* a, const p9_body* b) {
    const double dx = a->vx - b->vx, dy = a->vy - b->vy, dz = a->vz - b->vz;
    return sqrt((dx * dx + dy * dy + dz * dz) / (a->vx * a->vx + a->vy * a->vy + a->vz * a->vz));
}

// ------------------------------------------------------------------ step0
static int cmd_step0(const char* path) {
    struct reb_simulation* r = load(path, 0, 0, 1 << 30);
    const size_t N = r->N;
    struct reb_particle* ph = malloc(sizeof(struct reb_particle) * N);
    reb_integrator_whfast_from_inertial(r, ph, REB_INTEGRATOR_WHFAST_COORDINATES_DEMOCRATICHELIOCENTRIC);
    planets P;
    memset(&P, 0, sizeof P);  // no J2 (to_dh leaves it unset)
    com_t com;
    const int ntp = (int)(N - r->N_active);
    p9_body* tp = malloc(sizeof(p9_body) * (ntp > 0 ? ntp : 1));
    to_dh(r, &P, tp, ntp, &com);
    printf("step0: N=%zu N_active=%zu G=%.17g dt=%.17g m0=%.17g (REBOUND p_jh[0].m = %.17g = total mass)\n", N, r->N_active, r->G, r->dt, r->particles[0].m,
           ph[0].m);
    printf("p9gpu: m0=%.17g mu0=G*m0=%.17g; WHFast Kepler mu = eta*G with eta=m0: %.17g\n", P.m0, P.mu0, r->particles[0].m * r->G);
    long nbit_diff = 0;
    double maxq = 0, maxu = 0;
    for (size_t i = 1; i < N; i++) {
        const p9_body a = i < r->N_active ? P.b[i - 1] : tp[i - r->N_active];
        const p9_body b = {ph[i].x, ph[i].y, ph[i].z, ph[i].vx, ph[i].vy, ph[i].vz};
        if (memcmp(&a, &b, sizeof a)) nbit_diff++;
        maxq = fmax(maxq, reldiff(&a, &b));
        maxu = fmax(maxu, reldiffv(&a, &b));
        if (i < r->N_active) printf("  body %zu (%s): m %.17g (p9 %.17g) Q,u %s\n", i, r->particles[i].name ? r->particles[i].name : "-", ph[i].m, P.m[i - 1],
                                    memcmp(&a, &b, sizeof a) ? "DIFFER" : "bit-identical");
    }
    printf("state after conversion: %ld of %zu bodies differ in any bit; max |dQ|/|Q| %.3g, max |du|/|u| %.3g\n", nbit_diff, N - 1, maxq, maxu);
    // the centre of mass: REBOUND p_jh[0] against p9gpu com
    printf("centre of mass velocity: REBOUND %.17g %.17g %.17g, p9gpu %.17g %.17g %.17g\n", ph[0].vx, ph[0].vy, ph[0].vz, com.V[0], com.V[1], com.V[2]);

    // each operator once on the same state (REBOUND's), both codes
    const double h = 0.5 * r->dt;
    double mk = 0, mkv = 0;
    long nk = 0;
    for (size_t i = 1; i < N; i++) {
        struct reb_particle p = ph[i];
        reb_integrator_whfast_kepler_solver(&p, r->G * r->particles[0].m, h, r);
        p9_body b = {ph[i].x, ph[i].y, ph[i].z, ph[i].vx, ph[i].vy, ph[i].vz};
        p9_kepler(&b, P.mu0, h);
        const p9_body a = {p.x, p.y, p.z, p.vx, p.vy, p.vz};
        if (memcmp(&a, &b, sizeof a)) nk++;
        mk = fmax(mk, reldiff(&a, &b));
        mkv = fmax(mkv, reldiffv(&a, &b));
    }
    printf("operator kepler(dt/2): %ld of %zu bodies differ in any bit; max |dQ|/|Q| %.3g, max |du|/|u| %.3g\n", nk, N - 1, mk, mkv);
    // Kepler over a full step dt too (p9gpu's combined drift)
    mk = mkv = 0;
    for (size_t i = 1; i < N; i++) {
        struct reb_particle p = ph[i];
        reb_integrator_whfast_kepler_solver(&p, r->G * r->particles[0].m, r->dt, r);
        p9_body b = {ph[i].x, ph[i].y, ph[i].z, ph[i].vx, ph[i].vy, ph[i].vz};
        p9_kepler(&b, P.mu0, r->dt);
        const p9_body a = {p.x, p.y, p.z, p.vx, p.vy, p.vz};
        mk = fmax(mk, reldiff(&a, &b));
        mkv = fmax(mkv, reldiffv(&a, &b));
    }
    printf("operator kepler(dt): max |dQ|/|Q| %.3g, max |du|/|u| %.3g\n", mk, mkv);
    // jump: REBOUND's formula (integrator_whfast.c, DH) against p9gpu's planets_w + p9_jump
    {
        double px = 0, py = 0, pz = 0;
        for (size_t i = 1; i < r->N_active; i++) px += r->particles[i].m * ph[i].vx, py += r->particles[i].m * ph[i].vy, pz += r->particles[i].m * ph[i].vz;
        planets Pj = P;
        for (int i = 0; i < Pj.np; i++) Pj.b[i] = (p9_body){ph[i + 1].x, ph[i + 1].y, ph[i + 1].z, ph[i + 1].vx, ph[i + 1].vy, ph[i + 1].vz};
        double w[3];
        planets_w(&Pj, w);
        const double m0 = r->particles[0].m;
        printf("operator jump: REBOUND P/m0 = %.17g %.17g %.17g, p9gpu w = %.17g %.17g %.17g (%s)\n", px / m0, py / m0, pz / m0, w[0], w[1], w[2],
               (px / m0 == w[0] && py / m0 == w[1] && pz / m0 == w[2]) ? "bit-identical" : "DIFFER");
    }
    // interaction: REBOUND (to_inertial, gravity without the Sun, kick) against p9gpu (planets_kick, p9_kick_tp)
    {
        struct reb_particle* pr = malloc(sizeof(struct reb_particle) * N);
        memcpy(pr, ph, sizeof(struct reb_particle) * N);
        reb_integrator_whfast_to_inertial(r, pr, REB_INTEGRATOR_WHFAST_COORDINATES_DEMOCRATICHELIOCENTRIC);
        r->gravity_ignore_terms = REB_GRAVITY_IGNORE_TERMS_INVOLVING_0;
        reb_simulation_update_acceleration(r);
        reb_integrator_whfast_interaction_step(r, pr, REB_INTEGRATOR_WHFAST_COORDINATES_DEMOCRATICHELIOCENTRIC, r->dt);
        planets Pk = P;
        for (int i = 0; i < Pk.np; i++) Pk.b[i] = (p9_body){ph[i + 1].x, ph[i + 1].y, ph[i + 1].z, ph[i + 1].vx, ph[i + 1].vy, ph[i + 1].vz};
        double q[3 * P9_MAX_PLANETS];
        planets_positions(&Pk, q);
        planets_kick(&Pk, r->dt);
        static const double zero[P9_MAX_PLANETS] = {0};
        double mp = 0, mt = 0, mta = 0;
        long nd = 0;
        for (size_t i = 1; i < N; i++) {
            p9_body b;
            if (i < r->N_active) b = Pk.b[i - 1];
            else {
                b = (p9_body){ph[i].x, ph[i].y, ph[i].z, ph[i].vx, ph[i].vy, ph[i].vz};
                p9_kick_tp(&b, q, P.gm, zero, P.np, r->dt);
            }
            // compare the velocity change (kick) relative to its size
            const double dkx = (pr[i].vx - ph[i].vx) - (b.vx - ph[i].vx), dky = (pr[i].vy - ph[i].vy) - (b.vy - ph[i].vy),
                         dkz = (pr[i].vz - ph[i].vz) - (b.vz - ph[i].vz);
            const double kx = b.vx - ph[i].vx, ky = b.vy - ph[i].vy, kz = b.vz - ph[i].vz;
            const double rel = sqrt((dkx * dkx + dky * dky + dkz * dkz) / (kx * kx + ky * ky + kz * kz));
            if (pr[i].vx != b.vx || pr[i].vy != b.vy || pr[i].vz != b.vz) nd++;
            if (i < r->N_active && getenv("DIRECT_DEBUG")) fprintf(stderr, "planet %zu kick REBOUND %.17g %.17g %.17g p9 %.17g %.17g %.17g\n", i, pr[i].vx - ph[i].vx, pr[i].vy - ph[i].vy, pr[i].vz - ph[i].vz, kx, ky, kz);
            if (i < r->N_active) mp = fmax(mp, rel);
            else mt = fmax(mt, rel), mta = fmax(mta, sqrt(dkx * dkx + dky * dky + dkz * dkz) / sqrt(b.vx * b.vx + b.vy * b.vy + b.vz * b.vz));
        }
        printf("operator interaction(dt): %ld of %zu bodies differ in any bit; kick relative to its size: planets max %.3g, test particles max %.3g; "
               "relative to |u|: %.3g\n",
               nd, N - 1, mp, mt, mta);
        free(pr);
    }
    return 0;
}

// ------------------------------------------------------------------ pair
static int cmd_pair(char** a) {
    const char *pa = a[0], *ca = a[1], *pb = a[3], *cb = a[4], *prefix = a[11];
    const double offa = atof(a[2]), offb = atof(a[5]);
    const long nsteps = atol(a[6]), cmp_every = atol(a[7]), out_every = atol(a[8]);
    const int from = atoi(a[9]), to = atoi(a[10]);
    integ A, B;
    integ_init(&A, pa, ca, offa, from, to);
    integ_init(&B, pb, cb, offb, from, to);
    if (A.ntp != B.ntp || A.r->N_active != B.r->N_active || A.dt != B.dt) {
        fprintf(stderr, "A and B differ in size or step\n");
        return 2;
    }
    const int np = (int)A.r->N_active - 1, ntp = A.ntp, n = np + ntp;
    double ids[P9_MAX_PLANETS];
    for (int j = 0; j < np; j++) ids[j] = A.r->particles[j + 1].r;
    double* tpid = malloc(sizeof(double) * ntp);
    for (int i = 0; i < ntp; i++) tpid[i] = A.r->particles[A.r->N_active + i].r - offa;
    p9_body *sa = malloc(sizeof(p9_body) * n), *sb = malloc(sizeof(p9_body) * n);
    double ma[P9_MAX_PLANETS], mb[P9_MAX_PLANETS], m0a, m0b, Ga, Gb;
    int npa, npb;
    // per test particle: first step above each threshold, and the state of A then
    long* first = calloc((size_t)ntp * NTHR, sizeof(long));
    double* at = calloc((size_t)ntp * NTHR * 6, sizeof(double));  // r, a, q, inc, dmin Neptune (last 1 kyr), dmin P9 (last 1 kyr)
    double* dmin_cur = malloc(sizeof(double) * ntp * np);
    double* dmin_prev = malloc(sizeof(double) * ntp * np);
    for (long k = 0; k < (long)ntp * np; k++) dmin_cur[k] = dmin_prev[k] = 1e300;
    int* gone = calloc(ntp, sizeof(int));  // 1: beyond the distance rules in A or B (not compared after)
    int jN = -1, jP9 = -1;
    for (int j = 0; j < np; j++) {
        const char* nm = A.r->particles[j + 1].name;
        if (nm && !strcmp(nm, "Neptune")) jN = j;
        if (nm && !strcmp(nm, "P9")) jP9 = j;
    }
    char fn[512];
    snprintf(fn, sizeof fn, "%s.planets.tsv", prefix);
    FILE* fp = fopen(fn, "w");
    snprintf(fn, sizeof fn, "%s.summary.tsv", prefix);
    FILE* fs = fopen(fn, "w");
    fprintf(fp, "step\tt\tbody\trelQ\trelu\tda_rel\tde\tdi_deg\tdvarpi_deg\tdOmega_deg\ta\te\ti\tvarpi\tOmega\n");
    fprintf(fs, "step\tt\tn\tmedian_relQ\tp90_relQ\tmax_relQ\tn_gt_1e-12\tn_gt_1e-8\tn_gt_1e-4\tn_gt_1e-2\n");
    double* rq = malloc(sizeof(double) * ntp);
    const long bin = (long)(1000.0 / A.dt + 0.5);  // 1 kyr
    for (long s = 1; s <= nsteps; s++) {
        integ_step(&A);
        integ_step(&B);
        if (s % cmp_every && s != nsteps) continue;
        integ_sync(&A, sa, &npa, &m0a, ma, &Ga);
        integ_sync(&B, sb, &npb, &m0b, mb, &Gb);
        const double t = s * A.dt;
        if (s % bin < cmp_every) {
            double* tmp = dmin_prev;
            dmin_prev = dmin_cur;
            dmin_cur = tmp;
            for (long k = 0; k < (long)ntp * np; k++) dmin_cur[k] = 1e300;
        }
        const int out = (s % out_every == 0) || s == nsteps;
        if (out)
            for (int j = 0; j < np; j++) {
                double r1[3], v1[3], r2[3], v2[3];
                helio(sa, np, m0a, ma, j, r1, v1);
                helio(sb, np, m0b, mb, j, r2, v2);
                const elem e1 = elements_of(Ga * (m0a + ma[j]), r1, v1), e2 = elements_of(Gb * (m0b + mb[j]), r2, v2);
                fprintf(fp, "%ld\t%.10g\t%.0f\t%.3e\t%.3e\t%.3e\t%.3e\t%.3e\t%.3e\t%.3e\t%.10g\t%.10g\t%.10g\t%.10g\t%.10g\n", s, t, ids[j],
                        reldiff(&sa[j], &sb[j]), reldiffv(&sa[j], &sb[j]), (e2.a - e1.a) / e1.a, e2.e - e1.e, e2.inc - e1.inc,
                        angdiff(e2.varpi, e1.varpi), angdiff(e2.Om, e1.Om), e1.a, e1.e, e1.inc, e1.varpi, e1.Om);
            }
        int nc = 0;
        long cnt[NTHR] = {0};
        for (int i = 0; i < ntp; i++) {
            if (gone[i]) continue;
            const p9_body *x = &sa[np + i], *y = &sb[np + i];
            const double r2a = x->x * x->x + x->y * x->y + x->z * x->z, r2b = y->x * y->x + y->y * y->y + y->z * y->z;
            if (s % 1000 == 0 && (r2a > R_OUT * R_OUT || r2a < R_IN * R_IN || r2b > R_OUT * R_OUT || r2b < R_IN * R_IN)) {
                gone[i] = (int)(s / 1000);
                continue;
            }
            for (int j = 0; j < np; j++) {
                const double dx = sa[j].x - x->x, dy = sa[j].y - x->y, dz = sa[j].z - x->z;
                const double d = sqrt(dx * dx + dy * dy + dz * dz);
                if (d < dmin_cur[(size_t)i * np + j]) dmin_cur[(size_t)i * np + j] = d;
            }
            const double d = reldiff(x, y);
            rq[nc++] = d;
            for (int k = 0; k < NTHR; k++) {
                if (d > THR[k]) cnt[k]++;
                if (d > THR[k] && !first[(size_t)i * NTHR + k]) {
                    first[(size_t)i * NTHR + k] = s;
                    double r1[3], v1[3];
                    helio(sa, np, m0a, ma, np + i, r1, v1);
                    const elem e = elements_of(Ga * m0a, r1, v1);
                    double* o = &at[((size_t)i * NTHR + k) * 6];
                    o[0] = sqrt(r2a), o[1] = e.a, o[2] = e.q, o[3] = e.inc;
                    o[4] = jN >= 0 ? fmin(dmin_cur[(size_t)i * np + jN], dmin_prev[(size_t)i * np + jN]) : -1;
                    o[5] = jP9 >= 0 ? fmin(dmin_cur[(size_t)i * np + jP9], dmin_prev[(size_t)i * np + jP9]) : -1;
                }
            }
        }
        if (out) {
            // median and 90th percentile by sorting a copy
            for (int x = 1; x < nc; x++) {
                const double v = rq[x];
                int y = x - 1;
                while (y >= 0 && rq[y] > v) rq[y + 1] = rq[y], y--;
                rq[y + 1] = v;
            }
            fprintf(fs, "%ld\t%.10g\t%d\t%.3e\t%.3e\t%.3e\t%ld\t%ld\t%ld\t%ld\n", s, t, nc, nc ? rq[nc / 2] : 0, nc ? rq[(int)(0.9 * nc)] : 0,
                    nc ? rq[nc - 1] : 0, cnt[0], cnt[1], cnt[2], cnt[3]);
            fflush(fs);
            fflush(fp);
        }
    }
    snprintf(fn, sizeof fn, "%s.tp.tsv", prefix);
    FILE* ft = fopen(fn, "w");
    fprintf(ft, "id\tgone_kstep");
    for (int k = 0; k < NTHR; k++)
        fprintf(ft, "\tstep_%g\tr_%g\ta_%g\tq_%g\ti_%g\tdminN_%g\tdminP9_%g", THR[k], THR[k], THR[k], THR[k], THR[k], THR[k], THR[k]);
    fprintf(ft, "\n");
    for (int i = 0; i < ntp; i++) {
        fprintf(ft, "%.0f\t%d", tpid[i], gone[i]);
        for (int k = 0; k < NTHR; k++) {
            const double* o = &at[((size_t)i * NTHR + k) * 6];
            fprintf(ft, "\t%ld\t%.6g\t%.6g\t%.6g\t%.4g\t%.4g\t%.4g", first[(size_t)i * NTHR + k], o[0], o[1], o[2], o[3], o[4], o[5]);
        }
        fprintf(ft, "\n");
    }
    fclose(ft);
    fclose(fp);
    fclose(fs);
    return 0;
}

int main(int argc, char* argv[]) {
    if (argc == 3 && !strcmp(argv[1], "step0")) return cmd_step0(argv[2]);
    if (argc == 14 && !strcmp(argv[1], "pair")) return cmd_pair(argv + 2);
    fprintf(stderr, "usage: direct_wh step0 <in.sa> | pair <A.sa> <p9|wh> <offA> <B.sa> <p9|wh> <offB> <nsteps> <cmp_every> <out_every> <from> <to> <prefix>\n");
    return 1;
}
