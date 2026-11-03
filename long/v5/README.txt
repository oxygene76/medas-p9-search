MEDAS p9-search: paired long runs, seeds 110-112, group V5 (p9gpu v5, CUDA, FP64)
==================================================================================

What it is: 3 runs of the production method (p9gpu v5, smooth transition,
planets with 8 inner steps, collisions at the planets' radii; the unchanged
binary of the production package p9prod-9a084ed, its sha256 is checked) in the
production configuration (Brown & Batygin 2021 start conditions, a 150-500 au,
q 30-50 au, i 0-25 deg, inner removal at 4.5 au, dt 0.5 yr), each with 2,000
test particles of its own seed (110, 111, 112), 0 to 4,000 million years. The
same start values are computed with MERCURIUS (the CPU package); the criteria
are fixed in docs/long-runs-110-112-criteria.md of medas-p9-search (part of
entry 3). Each job is a chain of 40 segments of 100 million years, a snapshot
every 10 million years.

Needs: Linux with an NVIDIA GPU and its driver (580 or newer), glibc 2.35 or
newer, sh, awk, sha256sum, nohup, lscpu, taskset; about 3 GB of disk. No root,
no network. Nothing outside this directory is changed. The production package
is not touched (a separate directory).

Start (as a normal user, in the unpacked directory):
  sh check.sh       only the check (a few minutes), nothing else
  sh start.sh       the check, then the three jobs at once, in the background
  sh status.sh      state of the check and the jobs, the card in use
  sh stop.sh        stops; running segments are computed again on the next start
  sh start.sh       again: resumes with the first segments not done
  AT_ONCE=1 sh start.sh          one job after the other instead (if the first
                                 segment shows that three at once lose time)
  GPU_NAME=L40S (default)        the card, by name: CUDA_VISIBLE_DEVICES is set
                                 to its UUID (select-gpu.sh), so the A100 of the
                                 production run is not used
  SOCKET=1 (default)             the p9gpu processes pinned to the cores of that
                                 socket ("CPU 2"; CPU 1 = socket 0 is for group M)

The p9gpu processes run with nice (5) and use one CPU core each besides the
GPU. Other processes on the card (the AI services on the L40S) are allowed and
recorded in start.log; they change only the run time, not the bits. Every
start first runs the check (check.sh): the 32 regression cases and 4 deep
Neptune flybys of the production package, and every job's start values over
10,000 years, alone and as two joined segments; only if all match (ALL SAME in
check/report.txt) do the jobs run.

Interim check after about 100 Myr (docs/long-runs-110-112-criteria.md section
5): when every job has finished its first segment, the hashes in
jobs/*/segments.tsv, run.log, the temperature and clock in status.sh, and a
resume test (sh stop.sh during a segment, sh start.sh: the segment is computed
again and its result hash must equal the one it would have had); then on.

Expected time on the L40S: see EXPECTED-TIME.

Results to send back: run.log, start.log, check/report.txt,
jobs/*/segments.tsv, and jobs/*/segments/seg*/output.sa (the snapshots).
