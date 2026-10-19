// SPDX-License-Identifier: GPL-3.0-or-later
#include <stdio.h>
#include <stdlib.h>
#include "p9encounter.h"

int p9_encounter_radii(const char* text, int np, double* r2) {
    for (int j = 0; j < np; j++) r2[j] = 0.0;
    if (!text || !*text) return 0;
    const char* s = text;
    for (int j = 0; j < np; j++) {
        char* end;
        const double v = strtod(s, &end);  // correctly rounded on every C99 library
        if (end == s || !(v >= 0.0)) {
            fprintf(stderr, "P9_ENCOUNTER_RADII: need %d radii (au), separated by commas\n", np);
            return 1;
        }
        r2[j] = v * v;
        s = end;
        if (j < np - 1) {
            if (*s != ',') {
                fprintf(stderr, "P9_ENCOUNTER_RADII: need %d radii (au), separated by commas\n", np);
                return 1;
            }
            s++;
        }
    }
    if (*s) {
        fprintf(stderr, "P9_ENCOUNTER_RADII: more than %d radii\n", np);
        return 1;
    }
    return 0;
}
