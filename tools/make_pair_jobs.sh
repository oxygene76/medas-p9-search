#!/bin/sh
# Jobs of the paired tests V5 against MERCURIUS for sets A and B (docs/bb2021-paired-test-proposal.md in
# medas-p9-search) into runs/pair, with the settings of the equivalence jobs (checked: p9job make gives the same
# params and start values as runs/equiv for seed 101) except Planet Nine (the set's, relative to the invariable
# plane, make-ic-v1) and the seeds: set A 331-339, set B 341-349; 4,000 test particles, 0-200 Myr, a snapshot every
# 1 Myr.
#   runs/pair/v5/s331 ... s349           p9gpu v5 (smooth, 8 planet sub-steps, collisions; the radii of addendum 13,
#                                        as the jobs of sets A and B)
#   runs/pair/m/s331/part00 ... part15   MERCURIUS (no encounter removal), slices of 250 test particles
# The binaries recorded in the jobs are those of the production package (PROD).
set -eu
cd "$(dirname "$0")/.."
PROD=${PROD:-build/p9prod-9a084ed}
PY=build/venv/bin/python
B="--a-range 150 500 --q-range 30 50 --inc-range 0 25 --r-in 4.5 --t-end 2e8 --snapshots 200 --n-tp 4000 --p9-plane invariable"
A_P9="m_earth=7,a=500,e=0.33,inc=17,varpi=250,Omega=100,M=0"
B_P9="m_earth=5,a=300,e=0.15,inc=17,varpi=254,Omega=108,M=0"
# the radii of addendum 13, as in the jobs of sets A and B (runs/bb2021/sets/*/job.json "overrides"): Jupiter-Neptune
# as in the production package, Planet Nine's from the rule with the cube root of its mass
R="--radius Jupiter=1.8575 --radius Saturn=1.2427 --radius Uranus=0.6643 --radius Neptune=0.7759"
A_R="$R --radius P9=0.5206"
B_R="$R --radius P9=0.4654"
for s in 331 332 333 334 335 336 337 338 339 341 342 343 344 345 346 347 348 349; do
  if [ "$s" -lt 340 ]; then P9=$A_P9; RAD=$A_R; else P9=$B_P9; RAD=$B_R; fi
  [ -d runs/pair/v5/s$s ] || $PY -I tools/p9job.py make --out runs/pair/v5/s$s --seed $s $B --p9 "$P9" --program p9gpu \
    --p9sim "$PROD/bin/p9gpu" --encounter-method smooth --planet-substeps 8 $RAD > /dev/null
  k=0
  while [ $k -lt 16 ]; do
    d=runs/pair/m/s$s/part$(printf %02d $k)
    [ -d "$d" ] || $PY -I tools/p9job.py make --out "$d" --seed $s $B --p9 "$P9" --tp-from $((250 * k)) --tp-to $((250 * (k + 1))) \
      --no-encounters --integrator mercurius --p9sim "$PROD/bin/p9sim" > /dev/null
    k=$((k + 1))
  done
done
echo "jobs: $(ls runs/pair/v5 | wc -l) V5, $(ls -d runs/pair/m/*/part* | wc -l) M slices"
