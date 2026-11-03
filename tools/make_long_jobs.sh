#!/bin/sh
# Jobs of the paired long runs, seeds 110-112 (docs/long-runs-110-112-criteria.md in medas-p9-search), into
# runs/long, with the settings of the equivalence jobs (runs/equiv; checked: the same params for seed 101) except
# the seeds, 2,000 test particles, 0-4 Gyr and a snapshot every 10 Myr:
#   runs/long/v5/s110 ... s112           p9gpu v5 (smooth, 8 planet sub-steps, collisions; the rule's radii, which at
#                                        6.2 Earth masses are those of the production package)
#   runs/long/m/s110/part00 ... part07   MERCURIUS (no encounter removal), slices of 250 test particles
# The binaries recorded in the jobs are those of the production package (PROD).
set -eu
cd "$(dirname "$0")/.."
PROD=${PROD:-../medas-p9-search-bb2021/build/p9prod-9a084ed}
PY=build/venv/bin/python
B="--a-range 150 500 --q-range 30 50 --inc-range 0 25 --r-in 4.5 --t-end 4e9 --snapshots 400 --n-tp 2000"
for s in 110 111 112; do
  [ -d runs/long/v5/s$s ] || $PY -I tools/p9job.py make --out runs/long/v5/s$s --seed $s $B --program p9gpu --p9sim "$PROD/bin/p9gpu" \
    --encounter-method smooth --planet-substeps 8
  k=0
  while [ $k -lt 8 ]; do
    d=runs/long/m/s$s/part$(printf %02d $k)
    [ -d "$d" ] || $PY -I tools/p9job.py make --out "$d" --seed $s $B --tp-from $((250 * k)) --tp-to $((250 * (k + 1))) \
      --no-encounters --integrator mercurius --p9sim "$PROD/bin/p9sim"
    k=$((k + 1))
  done
done
