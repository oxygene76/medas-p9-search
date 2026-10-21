MEDAS p9-search: production run (p9gpu, CUDA, FP64)
===================================================

What it is: the test case of Brown & Batygin (2021) over 4,000 million
years: the Sun, Jupiter to Neptune, Planet Nine (6.2 Earth masses,
a = 380 au, perihelion 300 au, i = 16 deg) and 64,000 test particles
(a 150-500 au, perihelion 30-50 au, inclination 0-25 deg; seed 21). Test
particles are removed closer than 4.5 au to the Sun, beyond 10,000 au, and
at a collision with a planet. Close encounters with the smooth transition
(sub-steps near the planets). The run is a chain of 40 segments of
100 million years, a snapshot every 10 million years.

Needs: Linux with an NVIDIA GPU and its driver (580 or newer for the
prebuilt binaries), glibc 2.35 or newer (e.g. Ubuntu 22.04), sh, awk,
sha256sum, nohup; about 2 GB of disk. No root, no network, no CUDA toolkit,
no Python. Nothing outside this directory is changed.

Start (as a normal user, in the unpacked directory):
  sh start.sh       starts in the background (nohup) and returns
  sh status.sh      the state: check, segments done, the running segment, GPU
  sh stop.sh        stops; the running segment is lost
  sh start.sh       again: resumes with the first segment not done

Every start first runs the check (check.sh, a few minutes on an L40S): known
jobs whose result hashes were computed on the reference machine (the 32
close-flyby regression cases, 4 very deep Neptune flybys with collisions,
the production start values over 10,000 years, and the same 10,000 years as
two joined segments). Only if all match (ALL SAME, in check/report.txt) do
the segments run; otherwise the run stops with "CHECK FAILED" in
production.log.

Checkpoints: a segment counts as done only when its result is written
(segments/segNNN/DONE). Each segment starts from the last snapshot of the
previous one and is a deterministic function of that input, so a resumed
run gives the same bits as one without interruption.

Expected time on an L40S: about 5-6 days (the first segments about 6-7 hours
each, later ones faster as particles are removed).

Results to send back (or to keep): segments.tsv, production.log,
check/report.txt; the snapshots are in segments/segNNN/output.sa.

Licence: GPL-3.0-or-later (REBOUND and p9gpu); sources included. The prebuilt
binary contains NVIDIA's CUDA runtime (statically linked), which NVIDIA
permits to redistribute with applications.
