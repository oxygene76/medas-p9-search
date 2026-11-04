MEDAS p9-search: comparison with Brown & Batygin 2021, the 4-Gyr runs of sets A and B (p9gpu v5, CUDA, FP64)
===========================================================================================================

What it is: the two runs of docs/bb2021-comparison-criteria.md (medas-p9-search), with its addenda 13-16:
  BB-A  set A: Planet Nine 7 Earth masses, a 500 au, e 0.33, i 17 deg (invariable plane), varpi 250, Omega 100, M 0;
        64,000 test particles, seed 311
  BB-B  set B: Planet Nine 5 Earth masses, a 300 au, e 0.15, i 17 deg, varpi 254, Omega 108, M 0; 64,000, seed 312
Test particles a 150-500 au, q 30-50 au, i 0-25 deg; removal at 4.5 au, beyond 10,000 au and at collisions; 0 to 4
Gyr in 40 segments of 100 Myr, a snapshot every 10 Myr. p9gpu v5 (the binary of p9prod-9a084ed); encounter radii of
Jupiter-Neptune as in the production package, Planet Nine's and its collision radius with the cube root of its mass.

Order on the A100 (decision of 2026-11-04): after the production run and the V5 part of seeds 110-112; set A, then
set B (one at a time). start.sh refuses:
  - while another compute process is on the A100 (FORCE=1 starts anyway);
  - for a job without the V2 verdict: v2/BB-A.ok and v2/BB-B.ok must hold the line "within the limits", written from
    the output of tools/v2_encounter_check.py on the short runs of that set (package p9bbv2). Outside the limits the
    set needs a paired test V5 against MERCURIUS first (addendum 13).
  JOBS="BB-A" sh start.sh   only set A (while B waits for its verdict)

Start (as a normal user, in the unpacked directory): sh check.sh, sh start.sh, sh status.sh, sh stop.sh as in the
other packages. Expected time: see EXPECTED-TIME. Results to send back: run.log, start.log, check/report.txt,
jobs/*/segments.tsv and jobs/*/segments/seg*/output.sa (the snapshots).
