#!/bin/sh
# Runs one pair of tools/direct_wh.c over the 2,000 test particles of member 0 (ids 6..2005) in 16 slices of 125,
# nice, 16 processes: tools/direct_wh_run.sh NAME A_CODE A_OFF B_CODE B_OFF NSTEPS CMP_EVERY OUT_EVERY
# (both from runs/val/ens-gpu/input.sa; offset 100000 = member 1). Output in runs/cause/direct/NAME/.
set -eu
cd "$(dirname "$0")/.."
name=$1 ca=$2 oa=$3 cb=$4 ob=$5 n=$6 ce=$7 oe=$8
d=runs/cause/direct/$name
mkdir -p "$d" runs/pids
echo $$ > runs/pids/direct-$name.pid
in=runs/val/ens-gpu/input.sa
echo "== start $(date -Iseconds)" > "$d/run.log"
seq 0 15 | xargs -P 16 -I{} sh -c 'f=$((6 + {} * 125)); nice -n 10 build/direct/direct_wh pair '"$in $ca $oa $in $cb $ob $n $ce $oe"' $f $((f + 125)) '"$d"'/s{}' >> "$d/run.log" 2>&1
echo "== end $(date -Iseconds)" >> "$d/run.log"
rm -f runs/pids/direct-$name.pid
