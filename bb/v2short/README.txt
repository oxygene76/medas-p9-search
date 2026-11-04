MEDAS p9-search: comparison with Brown & Batygin 2021, V2 short runs of sets A and B (p9gpu v5, CUDA, FP64)
===========================================================================================================

What it is: the condition of prerequisite V2 (docs/bb2021-comparison-criteria.md of medas-p9-search, addenda 13 and
16): before the 4-Gyr run of a set, a short run of that set shows whether its encounter regime is like that of the
equivalence runs. Two jobs, each 4,000 test particles over 0-60 million years in 3 segments of 20 Myr, with the flyby
log (flybys.tsv per segment):
  V2-A  set A: Planet Nine 7 Earth masses, a 500 au, e 0.33, i 17 deg (invariable plane), seed 321
  V2-B  set B: Planet Nine 5 Earth masses, a 300 au, e 0.15, i 17 deg (invariable plane), seed 322
The method of the production run (p9gpu v5, smooth transition, planets with 8 inner steps, collisions); the binary
of p9prod-9a084ed (sha256 checked). Encounter radii of Jupiter-Neptune as in the production package, Planet Nine's
with the cube root of its mass (A 2.0824, B 1.8616 au), its collision radius likewise (A 17,248.4, B 15,418.4 km).

Where: the L40S, while the AI services keep running there (the bits do not depend on other processes; they are
recorded in start.log). Both jobs at once. Then the evaluation, on the laptop:
  python3 -I tools/v2_encounter_check.py jobs/V2-A jobs/V2-B     (medas-p9-search)
which writes the verdict per set; "within the limits" lets the 4-Gyr run of that set start (package p9bbsets).

Start (as a normal user, in the unpacked directory):
  sh check.sh       only the check (a few minutes), nothing else
  sh start.sh       the check, then both jobs at once, in the background
  sh status.sh      state; sh stop.sh stops; sh start.sh resumes
  GPU_NAME=... / CUDA_VISIBLE_DEVICES=<UUID>, AT_ONCE=1, SOCKET=... : see defaults.env

Every start first runs the check (check.sh): the 32 regression cases and 4 deep Neptune flybys of the production
package, and each job's start values over 10,000 years, alone and as two joined segments; only with ALL SAME do the
jobs run.

Expected time: see EXPECTED-TIME. Results to send back: run.log, start.log, check/report.txt, jobs/*/segments.tsv,
jobs/*/segments/seg*/flybys.tsv (and output.sa).
