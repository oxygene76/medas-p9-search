MEDAS p9-search: CPU-2 measurement (does load on the cores of socket 1 slow the A100?)
=========================================================================================

Decision of 2026-11-06 (criteria of the paired tests, section 7): the first point of the A100 window after V5 of
seeds 110-112, before the V5 half of the paired tests; started by the A100 chain (or by hand). Not part of any
preregistered result: performance only. About 20 min on the A100.

p9gpu runs as in the A100 runs (all physical cores of socket 1, nice 10, the A100 by name or UUID). Load: k
MERCURIUS processes (p9sim, job cpu-merc-4k-1m) pinned to the upper k cores of socket 1, nice 19; k = 0, 8, 12.
Jobs gpu-v5-4k-1m and gpu-v5-64k-1m of the speed comparison, 3 rounds, levels 0, 8, 12, 0 in each round. Every
result hash is compared with the speed comparison's (bit check). The binaries are those of p9prod-9a084ed.

Rule: k cores of CPU 2 may be used for MERCURIUS (the M half of the paired tests: CPUS=... with those cores,
nice 19) if the median wall time of gpu-v5-4k-1m with k cores busy is at most 3 % above the median at level 0.
Result: RESULT/VERDICT.txt (and RESULT/RESULTS.tsv, run.log).

sh start.sh (refuses while another compute process is on the A100), sh status.sh, sh stop.sh.
Results to send back: RESULT/, run.log, start.log.
