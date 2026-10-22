MEDAS p9-search: equivalence test, group M (MERCURIUS, CPU only)
================================================================

What it is: the reference of the equivalence test: REBOUND's MERCURIUS
(r_crit 3 Hill radii, dt 0.5 yr, no encounter removal) for the same start
values as the V5 package and the plain Wisdom-Holman runs: Brown & Batygin
2021 start conditions (a 150-500 au, q 30-50 au, i 0-25 deg, inner removal at
4.5 au), seeds 101 to 109 with 4,000 test particles each, 0 to 200 million
years. MERCURIUS needs one CPU thread per process and is slow, so every seed
is split into 16 slices of 250 test particles (the test particles do not
interact, the slices are independent): 144 slices, each a chain of 10
segments of 20 million years, a snapshot every million years. The criteria
are fixed in docs/equivalence-criteria.md of medas-p9-search (accepted
2026-10-22).

Needs: Linux, glibc 2.35 or newer, sh, awk, xargs, sha256sum, nohup; about
2 GB of disk. No GPU, no root, no network. Nothing outside this directory is
changed.

Start (as a normal user, in the unpacked directory):
  sh check.sh       only the check (about 2 minutes), nothing else
  sh start.sh       the check, then the slices, 14 at the same time, in the background
  sh status.sh      state of the check and the slices
  sh stop.sh        stops; running segments are computed again on the next start
  sh start.sh       again: resumes with the first segments not done
  THREADS=12 sh start.sh    12 slices at the same time instead of 14

Each slice is one single-threaded p9sim process with nice 10. Every start
first runs the check (check.sh): the first slice of every seed over 10,000
years, alone and as two joined segments, and the first slice of seed 101 over
1 million years, each against the hash computed with the same binary on the
reference machine; only if all match (ALL SAME in check/report.txt) do the
slices run.

Expected time: see EXPECTED-TIME.

Results to send back: run.log, check/report.txt, jobs/*/segments.tsv, and
jobs/*/segments/seg*/output.sa (the snapshots).

Licence: GPL-3.0-or-later (REBOUND and p9sim); sources included.
