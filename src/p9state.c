// SPDX-License-Identifier: GPL-3.0-or-later
#include <math.h>
#include <string.h>
#include "p9state.h"

static void put_le64(uint8_t* b, uint64_t v) {
    for (int i = 0; i < 8; i++) b[i] = (uint8_t)(v >> (8 * i));
}
static void put_double(uint8_t* b, double d) {
    uint64_t v;
    memcpy(&v, &d, 8);
    put_le64(b, v);
}

void p9_state_hash(struct reb_simulation* r, struct sha256_ctx* ctx, FILE* out) {
    uint8_t buf[8 + 7 * 8];
    sha256_update(ctx, (const uint8_t*)STATE_MAGIC, 8);
    if (out) fwrite(STATE_MAGIC, 1, 8, out);
    uint8_t head[16];
    put_double(head, r->t);
    put_le64(head + 8, (uint64_t)r->N);
    sha256_update(ctx, head, 16);
    if (out) fwrite(head, 1, 16, out);
    for (size_t i = 0; i < r->N; i++) {
        const struct reb_particle* p = &r->particles[i];
        put_le64(buf, (uint64_t)p->r);  // the particle id (stored in the radius, see p9sim.c)
        const double v[7] = {p->m, p->x, p->y, p->z, p->vx, p->vy, p->vz};
        for (int k = 0; k < 7; k++) put_double(buf + 8 + 8 * k, v[k]);
        sha256_update(ctx, buf, sizeof buf);
        if (out) fwrite(buf, 1, sizeof buf, out);
    }
}

double p9_energy_massive(struct reb_simulation* r) {
    const size_t n = r->N_active < r->N ? r->N_active : r->N;
    double e = 0.0;
    for (size_t i = 0; i < n; i++) {
        const struct reb_particle* p = &r->particles[i];
        e += 0.5 * p->m * (p->vx * p->vx + p->vy * p->vy + p->vz * p->vz);
        for (size_t j = i + 1; j < n; j++) {
            const struct reb_particle* q = &r->particles[j];
            const double dx = p->x - q->x, dy = p->y - q->y, dz = p->z - q->z;
            e -= r->G * p->m * q->m / sqrt(dx * dx + dy * dy + dz * dz);
        }
    }
    return e;
}

void p9_hex(const uint8_t d[32], char s[65]) {
    for (int i = 0; i < 32; i++) sprintf(s + 2 * i, "%02x", d[i]);
    s[64] = 0;
}
