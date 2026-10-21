MEDAS p9-search: cause search, two p9gpu runs (CUDA, FP64)
==========================================================

What it is: two repetitions of the ensemble of the validation (2,000 test
particles of Brown & Batygin 2021 as four ensemble members, 8,000 in all,
0 to 200 million years) with the unchanged integrator p9gpu v5 (the binary of
the production package p9prod-9a084ed, its sha256 is checked), each with one
setting changed:
  J1-dt025      half the time step: 0.25 yr instead of 0.5 yr (the transition
                radii unchanged)
  J2-p9zone21   the transition zone around Planet Nine 20.95 au (3 Hill radii,
                as the IAS15 zone of MERCURIUS) instead of 2 au
They show whether the difference to MERCURIUS in the clustering of the
distant bodies comes from the time step or from the encounters with Planet
Nine. Each job is a chain of 10 segments of 20 million years, a snapshot every
million years.

Needs: Linux with an NVIDIA GPU and its driver (580 or newer), glibc 2.35 or
newer, sh, awk, sha256sum, nohup; about 1 GB of disk. No root, no network.
Nothing outside this directory is changed. The production package is not
touched (a separate directory).

Start (as a normal user, in the unpacked directory):
  sh start.sh       the check, then both jobs at the same time, in the background
  sh status.sh      state of the check and the jobs
  sh stop.sh        stops; running segments are computed again on the next start
  sh start.sh       again: resumes with the first segments not done
  JOBS="J1-dt025" sh start.sh    only one job;  PARALLEL=0 sh start.sh   one after the other

The p9gpu processes run with nice (5) and use one CPU core each besides the
GPU. Every start first runs the check (check.sh, a few minutes): the 32
regression cases, 4 deep Neptune flybys, and both jobs' start values over
10,000 years, alone and as two joined segments; only if all match (ALL SAME
in check/report.txt) do the jobs run.

Expected time on the L40S: see EXPECTED-TIME (measured on the reference
laptop, scaled with the measured L40S/laptop factor 2.0 for FP64).

Results to send back: run.log, check/report.txt, jobs/*/segments.tsv, and
jobs/*/segments/seg*/output.sa (the snapshots).

Licence: GPL-3.0-or-later (REBOUND and p9gpu); sources included. The prebuilt
binary contains NVIDIA's CUDA runtime (statically linked), which NVIDIA
permits to redistribute with applications.
