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
// 64 lower-case hex digits and a terminating zero.
void p9_hex(const uint8_t d[32], char s[65]);
#endif
