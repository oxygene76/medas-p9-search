MEDAS p9-search: equivalence test, group V5 (p9gpu v5, CUDA, FP64)
==================================================================

What it is: 9 runs of the production method (p9gpu v5, smooth transition,
planets with 8 inner steps, collisions at the planets' radii; the unchanged
binary of the production package p9prod-9a084ed, its sha256 is checked) in the
production configuration (Brown & Batygin 2021 start conditions, a 150-500 au,
q 30-50 au, i 0-25 deg, inner removal at 4.5 au, dt 0.5 yr), each with 4,000
test particles of its own seed (101 to 109), 0 to 200 million years. The same
start values are computed with plain Wisdom-Holman (laptop) and MERCURIUS
(CPU package); the criteria are fixed in docs/equivalence-criteria.md of
medas-p9-search (accepted 2026-10-22). Each job is a chain of 10 segments of
20 million years, a snapshot every million years.

Needs: Linux with an NVIDIA GPU and its driver (580 or newer), glibc 2.35 or
newer, sh, awk, sha256sum, nohup; about 2 GB of disk. No root, no network.
Nothing outside this directory is changed. The production package is not
touched (a separate directory).

Start (as a normal user, in the unpacked directory):
  sh check.sh       only the check (a few minutes), nothing else
  sh start.sh       the check, then the jobs, 3 at the same time, in the background
  sh status.sh      state of the check and the jobs
  sh stop.sh        stops; running segments are computed again on the next start
  sh start.sh       again: resumes with the first segments not done
  AT_ONCE=2 sh start.sh          2 jobs at the same time instead of 3
  JOBS="V5-s101 V5-s102" sh start.sh    only these jobs

The p9gpu processes run with nice (5) and use one CPU core each besides the
GPU (3 with the default AT_ONCE=3). Every start first runs the check
(check.sh): the 32 regression cases and 4 deep Neptune flybys of the
production package, and every job's start values over 10,000 years, alone
and as two joined segments; only if all match (ALL SAME in check/report.txt)
do the jobs run.

Expected time on the L40S: see EXPECTED-TIME.

Results to send back: run.log, check/report.txt, jobs/*/segments.tsv, and
jobs/*/segments/seg*/output.sa (the snapshots).

Licence: GPL-3.0-or-later (REBOUND and p9gpu); sources included. The prebuilt
binary contains NVIDIA's CUDA runtime (statically linked), which NVIDIA
permits to redistribute with applications.
