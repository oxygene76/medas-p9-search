// SPDX-License-Identifier: GPL-3.0-or-later
// Close-encounter criterion, the same in p9sim (REBOUND) and p9gpu:
// a test particle is removed when, at the kick of a step (the positions of the
// middle of the step, after the first jump of the democratic heliocentric
// drift-kick-drift step), it is closer to a planet than that planet's
// encounter radius. The radii come from the environment variable
//   P9_ENCOUNTER_RADII="r1,r2,...,rN"   (au, one per massive body but the Sun)
// which tools/p9job.py sets from the job description (exact decimals; nobody
// computes a cube root, so libm differences can not change a decision).
// Unset: no encounter check.
#ifndef P9_ENCOUNTER_H
#define P9_ENCOUNTER_H
#ifndef P9_VERSION
#define P9_VERSION "unknown"
#endif
// Parses the radii into r2 (squared); returns 0, or 1 with a message on stderr.
int p9_encounter_radii(const char* text, int np, double* r2);
#endif
