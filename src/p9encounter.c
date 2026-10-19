// SPDX-License-Identifier: GPL-3.0-or-later
#include <stdio.h>
#include <stdlib.h>
#include "p9encounter.h"

static int fail(const char* what) {
    fprintf(stderr, "P9_ENCOUNTER_RADII: %s (format: id=radius_au,id=radius_au,..., one per massive body but the Sun)\n", what);
    return 1;
}

int p9_encounter_radii(const char* text, int np, const double* ids, double* r, double* r2) {
    int seen[64] = {0};
    for (int j = 0; j < np; j++) {
        r2[j] = 0.0;
        if (r) r[j] = 0.0;
    }
    if (!text || !*text) return 0;
    if (np > 64) return fail("too many bodies");
    const char* s = text;
    int n = 0;
    while (*s) {
        char* end;
        if (*s < '0' || *s > '9') return fail("each item needs a body id");
        const unsigned long long id = strtoull(s, &end, 10);
        if (*end != '=') return fail("each item needs a body id");
        s = end + 1;
        const double v = strtod(s, &end);  // correctly rounded on every C99 library
        if (end == s || !(v >= 0.0)) return fail("a radius is not a number >= 0");
        s = end;
        int j = 0;
        while (j < np && ids[j] != (double)id) j++;
        if (j == np) {
            fprintf(stderr, "P9_ENCOUNTER_RADII: id %llu is not a massive body but the Sun\n", id);
            return 1;
        }
        if (seen[j]++) {
            fprintf(stderr, "P9_ENCOUNTER_RADII: id %llu given twice\n", id);
            return 1;
        }
        r2[j] = v * v;
        if (r) r[j] = v;
        n++;
        if (*s == ',') {
            if (!*++s) return fail("a comma at the end");
        } else if (*s) {
            return fail("items are separated by commas");
        }
    }
    if (n != np) {
        for (int j = 0; j < np; j++)
            if (!seen[j]) fprintf(stderr, "P9_ENCOUNTER_RADII: no radius for id %.0f\n", ids[j]);
        return 1;
    }
    return 0;
}

void p9_encounter_print(int np, const double* ids, const double* r) {
    for (int j = 0; j < np; j++) printf("encounter_radius id=%.0f au=%.10g\n", ids[j], r[j]);
}
