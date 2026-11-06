MEDAS p9-search: paired tests V5 against MERCURIUS for sets A and B, group V5 (p9gpu v5, CUDA, FP64)
=====================================================================================================

What it is: the V5 half of the paired tests of docs/bb2021-paired-test-proposal.md (medas-p9-search), whose criteria
are entered on chain before any run. 18 jobs, 4,000 test particles each, 0-200 Myr in 10 segments of 20 Myr, a
snapshot every 1 Myr, with the flyby log (flybys.tsv per segment):
  PV5-s331 ... PV5-s339   set A: Planet Nine 7 Earth masses, a 500 au, e 0.33, i 17 deg (invariable plane)
  PV5-s341 ... PV5-s349   set B: Planet Nine 5 Earth masses, a 300 au, e 0.15, i 17 deg (invariable plane)
The method of the 4-Gyr package p9bbsets (p9gpu v5, smooth transition, planets with 8 inner steps, collisions), the
binary of p9prod-9a084ed (sha256 checked), the radii of addendum 13. The start values of each job are those of the
16 slices of the same seed in the package p9pair-merc.

Where: the A100, one job after the other (several at once are not faster in all without MPS), CPUs of socket 1.
start.sh refuses while another compute process is on the A100. Started by hand or by the A100 chain, only once the
criteria are on chain.

Start (as a normal user, in the unpacked directory): sh check.sh (only the check), sh start.sh (the check, then the
jobs, in the background), sh status.sh, sh stop.sh; start.sh again resumes (done segments are kept).
Every start first runs the check: the 32 regression cases and 4 deep Neptune flybys of the production package, and
each job's start values over 10,000 years, alone and as two joined segments; only with ALL SAME do the jobs run.

Results to send back: run.log, start.log, check/report.txt, jobs/*/job.json, jobs/*/segments.tsv,
jobs/*/segments/seg*/{DONE,result.txt,flybys.tsv,output.sa}.
