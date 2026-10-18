// SPDX-License-Identifier: GPL-3.0-or-later
// REBOUND's registry lists the WHFast512 integrator, whose x86 build needs an
// AVX-512 assembly file. p9sim never uses it (at most 8 planets, no test
// particles), and the ARM64 and WebAssembly builds can not assemble it, so it
// is replaced by an entry that can not be selected: selecting it fails.
#include <stddef.h>
#include "rebound.h"

static void* create_unavailable(void) { return NULL; }
static void step_unavailable(struct reb_simulation* r, void* p) {
    (void)p;
    reb_simulation_error(r, "WHFast512 is not part of this build (p9sim).");
    r->status = REB_STATUS_GENERIC_ERROR;
}

const struct reb_integrator reb_integrator_whfast512 = {
    .documentation = "Not available in p9sim.",
    .step = step_unavailable,
    .create = create_unavailable,
};
