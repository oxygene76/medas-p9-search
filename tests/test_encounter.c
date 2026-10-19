// SPDX-License-Identifier: GPL-3.0-or-later
// Tests of the encounter radii parser (src/p9encounter.c): radii are assigned
// by body id, whatever the order of the items; the positional list of the
// programs before 2026-10-19 and every incomplete or ambiguous list are
// rejected. Run by `make test`.
#include <stdio.h>
#include <string.h>
#include "p9encounter.h"

static int failures = 0;
#define CHECK(c, ...)                                     \
    do {                                                  \
        if (!(c)) {                                       \
            failures++;                                   \
            fprintf(stderr, "FAIL line %d: ", __LINE__);  \
            fprintf(stderr, __VA_ARGS__);                 \
            fputc('\n', stderr);                          \
        }                                                 \
    } while (0)

// The test case: ids 1..5 = Jupiter, Saturn, Uranus, Neptune, P9 (make_ic.py)
static const double IDS[5] = {1, 2, 3, 4, 5};
static const double WANT[5] = {0.3552, 0.4374, 0.4672, 0.7759, 6.9836};

static int parse(const char* text, const double* ids, double* r) {
    double r2[5];
    return p9_encounter_radii(text, 5, ids, r, r2);
}

static void expect_body_order(const char* text, const char* what) {
    double r[5];
    CHECK(parse(text, IDS, r) == 0, "%s: rejected", what);
    for (int j = 0; j < 5; j++) CHECK(r[j] == WANT[j], "%s: body %d got %.10g, want %.10g", what, j + 1, r[j], WANT[j]);
}

int main(void) {
    // in the order of the bodies, in the order of job.json (sorted by name:
    // Jupiter, Neptune, P9, Saturn, Uranus), and reversed: the same radii per body
    expect_body_order("1=0.3552,2=0.4374,3=0.4672,4=0.7759,5=6.9836", "body order");
    expect_body_order("1=0.3552,4=0.7759,5=6.9836,2=0.4374,3=0.4672", "sorted by name");
    expect_body_order("5=6.9836,4=0.7759,3=0.4672,2=0.4374,1=0.3552", "reversed");

    // ids that are not in index order: assigned by id, not by position
    {
        const double ids[5] = {5, 3, 1, 4, 2};
        double r[5];
        CHECK(parse("1=0.3552,2=0.4374,3=0.4672,4=0.7759,5=6.9836", ids, r) == 0, "shuffled ids rejected");
        CHECK(r[0] == 6.9836 && r[1] == 0.4672 && r[2] == 0.3552 && r[3] == 0.7759 && r[4] == 0.4374, "shuffled ids: wrong assignment");
    }

    // the old positional list (in the wrong order that p9job.py produced) is not accepted
    double r[5];
    CHECK(parse("0.3552,0.7759,6.9836,0.4374,0.4672", IDS, r) != 0, "positional list accepted");
    CHECK(parse("1=0.3552,2=0.4374,3=0.4672,4=0.7759", IDS, r) != 0, "missing body accepted");
    CHECK(parse("1=0.3552,2=0.4374,3=0.4672,4=0.7759,4=0.7759", IDS, r) != 0, "body twice accepted");
    CHECK(parse("0=1,1=0.3552,2=0.4374,3=0.4672,4=0.7759,5=6.9836", IDS, r) != 0, "the Sun accepted");
    CHECK(parse("1=0.3552,2=0.4374,3=0.4672,4=0.7759,9=6.9836", IDS, r) != 0, "unknown id accepted");
    CHECK(parse("1=0.3552,2=0.4374,3=0.4672,4=0.7759,5=-1", IDS, r) != 0, "negative radius accepted");
    CHECK(parse("1=0.3552,2=0.4374,3=0.4672,4=0.7759,5=6.9836,", IDS, r) != 0, "trailing comma accepted");
    CHECK(parse("1=0.3552;2=0.4374,3=0.4672,4=0.7759,5=6.9836", IDS, r) != 0, "other separator accepted");
    CHECK(parse("1=x,2=0.4374,3=0.4672,4=0.7759,5=6.9836", IDS, r) != 0, "no number accepted");

    // unset or empty: no check (all zero)
    CHECK(parse(NULL, IDS, r) == 0 && r[0] == 0 && r[4] == 0, "unset");
    CHECK(parse("", IDS, r) == 0 && r[0] == 0 && r[4] == 0, "empty");

    if (failures) {
        fprintf(stderr, "test_encounter: %d failures\n", failures);
        return 1;
    }
    printf("test_encounter: ok\n");
    return 0;
}
