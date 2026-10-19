// SPDX-License-Identifier: GPL-3.0-or-later
// Close-encounter criterion, the same in p9sim (REBOUND) and p9gpu:
// a test particle is removed when, at the kick of a step (the positions of the
// middle of the step, after the first jump of the democratic heliocentric
// drift-kick-drift step), it is closer to a planet than that planet's
// encounter radius. The radii come from the environment variable
//   P9_ENCOUNTER_RADII="id=r,id=r,..."   (au; one per massive body but the Sun)
// where id is the body's id (stored in its radius field, see p9sim.c), in any
// order. tools/p9job.py sets it from the job description, which names the
// bodies (radii and ids by name, from the start file), so no order is
// assumed anywhere. Exact decimals; nobody computes a cube root, so libm
// differences can not change a decision. Unset: no encounter check.
// Rejected: an item without an id (the positional list used before
// 2026-10-19, whose order was wrong), an id that is not a massive body but the
// Sun, a body named twice, a body left out.
#ifndef P9_ENCOUNTER_H
#define P9_ENCOUNTER_H
#ifndef P9_VERSION
#define P9_VERSION "unknown"
#endif
// Parses the radii for the np massive bodies after the Sun, whose ids are
// ids[0..np-1], into r[j] (au; may be NULL) and r2[j] (squared); returns 0, or
// 1 with a message on stderr.
int p9_encounter_radii(const char* text, int np, const double* ids, double* r, double* r2);
// Prints the radii in use, one line per body: "encounter_radius id=<id> au=<r>"
// (stdout; tools/p9job.py checks them against the job by name).
void p9_encounter_print(int np, const double* ids, const double* r);
#endif
