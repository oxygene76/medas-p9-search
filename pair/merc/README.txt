MEDAS p9-search: paired tests V5 against MERCURIUS for sets A and B, group M (MERCURIUS, CPU)
==============================================================================================

What it is: the MERCURIUS half of the paired tests of docs/bb2021-paired-test-proposal.md (medas-p9-search), whose
criteria are entered on chain before any run. 18 seeds x 16 slices of 250 test particles (288 slices), 0-200 Myr in
10 segments of 20 Myr, a snapshot every 1 Myr:
  PM-s331-part00 ... PM-s339-part15   set A (Planet Nine 7 Earth masses, a 500 au, e 0.33, i 17 deg)
  PM-s341-part00 ... PM-s349-part15   set B (Planet Nine 5 Earth masses, a 300 au, e 0.15, i 17 deg)
MERCURIUS as the M group of the equivalence test (r_crit 3 Hill radii, no encounter removal, inner removal 4.5 au,
dt 0.5 yr), the p9sim binary of p9prod-9a084ed (sha256 checked). The slices of a seed hold the same start values as
the job of that seed in p9pair-v5.

Where: CPU 1, the physical cores of socket 0 (on the GPU server CPUs 0-15), never socket 1 where the A100 runs are
pinned, unless the CPU-2 measurement allows cores there and they are given with CPUS=... . THREADS slices at the same
time, one core each, the slices of set A first. Everything runs at nice 19 and with the idle I/O class (decision of
2026-11-06): the AI services on CPU 1 and the MERCURIUS part of seeds 110-112 (nice 10) come first; when they need the
cores, these slices wait and the half takes longer. status.sh shows the CPUs it is pinned to, its nice value and I/O
class, and counts only the p9sim processes of this package.
Decision of 2026-11-06: start with THREADS=8 once the criteria are on chain (CPU 1 is shared with the second round
of the MERCURIUS part of seeds 110-112), then, when that has ended: sh stop.sh, THREADS=16 sh start.sh (done
segments are kept; a running segment is computed again; the bits do not depend on the number of threads).

Start (as a normal user, in the unpacked directory): THREADS=8 sh start.sh, sh status.sh, sh stop.sh; start.sh
again resumes. Every start first runs the check (start values of the first slice of each seed over 10,000 years,
alone and as two joined segments, and one slice over 1 million years); only with ALL SAME do the slices run.

Results to send back: run.log, start.log, check/report.txt, jobs/*/job.json, jobs/*/segments.tsv,
jobs/*/segments/seg*/{DONE,result.txt,output.sa}.
