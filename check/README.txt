MEDAS p9-search: reproducibility check for a second machine
===========================================================

What it does: builds the orbit integration program p9sim (REBOUND 5.2.2,
included as source) on this machine, computes the jobs in jobs/ and compares
each result with the hash computed on the reference machine (EXPECTED).
Nothing is sent anywhere; nothing outside this directory is changed.

Run, either
  a) directly (needs sh, make, a C compiler, tar; Linux or macOS):
       sh run-check.sh
     other compiler or level:  CC=clang OPT=-O2 sh run-check.sh
  b) in a container (needs Docker):
       docker build -t p9check . && docker run --rm p9check

Send back: the file report.txt (or the printed report). It contains the
system, CPU model, compiler version, the hashes and the run times; no user
names, no paths, no network data.

Jobs:
  control   20 test particles, 100,000 years: a control job whose result is
            known in advance (seconds)
  repro     100 test particles, 1 million years: the reproducibility job
            (about 40 s on a current desktop CPU)
  bench     250 test particles, 5 million years: measures the speed
            (a few minutes); skip with: grep -v '^bench' EXPECTED > E && mv E EXPECTED

Licence: GPL-3.0-or-later (REBOUND and p9sim); sources included.
