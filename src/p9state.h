// SPDX-License-Identifier: GPL-3.0-or-later
// Canonical state of a simulation and its SHA-256 (see p9sim.c): shared by
// p9sim (REBOUND) and p9gpu, so both hash the same way.
#ifndef P9_STATE_H
#define P9_STATE_H
#include <stdint.h>
#include <stdio.h>
#include "rebound.h"
#include "sha256.h"

#define STATE_MAGIC "P9STATE2"

// Adds the canonical state of r to ctx (and writes it to out unless NULL).
void p9_state_hash(struct reb_simulation* r, struct sha256_ctx* ctx, FILE* out);
// Total energy of the massive bodies (particles 0..N_active-1) in the
// simulation's frame. REBOUND's reb_simulation_energy sums over all pairs of
// all particles (O(N^2) with N test particles); massless test particles add
// nothing, so this is the same quantity at O(N_active^2).
double p9_energy_massive(struct reb_simulation* r);
// 64 lower-case hex digits and a terminating zero.
void p9_hex(const uint8_t d[32], char s[65]);
#endif
