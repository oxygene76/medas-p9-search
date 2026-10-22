#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# A resumable chain of p9job segments: DIR/seg00 (made beforehand with p9job make, t_end = SEG) and then
# DIR/seg01, seg02, ... each SEG years longer, made with p9job next, until T_END. Segments with a
# result.json are skipped, so after an interruption the same call continues with the first segment
# not done (a running segment is computed again). PID file runs/pids/<name>.pid, log DIR/run.log.
#
#   tools/chain_run.sh DIR BINARY T_END SEG SNAPSHOTS_PER_SEGMENT
#   e.g. tools/chain_run.sh runs/cause/ensfix build/gpu-v5/p9gpu 2e8 2e7 20
set -eu
cd "$(dirname "$0")/.."
dir=$1 bin=$2 t_end=$3 seg=$4 snaps=$5
name=$(echo "$dir" | tr '/' '-')
mkdir -p runs/pids
echo $$ > "runs/pids/$name.pid"
trap 'rm -f "runs/pids/$name.pid"' EXIT
child=""
# the segment runs in its own process group (setsid), so a stop also ends the program under p9job.py
trap '[ -n "$child" ] && kill -TERM -"$child" 2>/dev/null; rm -f "runs/pids/$name.pid"; exit 130' INT TERM HUP
py=build/venv/bin/python
n=$(python3 -I -c "import math; print(math.ceil($t_end / $seg))")
echo "== start $(date -Iseconds) $n segments of $seg yr" >> "$dir/run.log"
k=0
while [ "$k" -lt "$n" ]; do
  s=$(printf 'seg%02d' "$k")
  if [ "$k" -gt 0 ] && [ ! -f "$dir/$s/job.json" ]; then
    prev=$(printf 'seg%02d' $((k - 1)))
    $py -I tools/p9job.py next --prev "$dir/$prev" --out "$dir/$s" --t-end "$(python3 -I -c "print(min($t_end, ($k + 1) * $seg))")" \
      --snapshots "$snaps" --p9sim "$bin" >> "$dir/run.log" 2>&1
  fi
  if [ ! -f "$dir/$s/result.json" ]; then
    setsid nice -n 10 $py -I tools/p9job.py run "$dir/$s" --p9sim "$bin" --any-version >> "$dir/run.log" 2>&1 &
    child=$!
    wait "$child"
    child=""
    echo "== $s done $(date -Iseconds)" >> "$dir/run.log"
  fi
  k=$((k + 1))
done
echo "== end $(date -Iseconds)" >> "$dir/run.log"
