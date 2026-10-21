#!/bin/sh
# MEDAS p9-search: the production run, as a chain of segments (started by start.sh; not meant to be run directly).
#
# First the check (check.sh: known jobs whose result hashes were computed on the reference machine); only if
# every hash matches, the segments. Segment k runs from k * SEGMENT_YR to (k + 1) * SEGMENT_YR: segment 0 from
# run/input.sa, segment k from the last snapshot of segment k - 1 (bin/p9sim last). A segment counts as done only
# when its result is written (segments/segNNN/DONE). After an interruption (stop.sh, reboot, crash) the next start
# skips the done segments and computes the interrupted one again from its input: the run gives the same bits
# with or without interruptions (each segment is a deterministic function of its input).
set -u
cd "$(dirname "$0")"
. ./params.env
export P9_ENCOUNTER_METHOD P9_ENCOUNTER_RADII P9_COLLISION_RADII P9_PLANET_SUBSTEPS P9_R_IN P9GPU_REAL
unset P9_ENCOUNTER_REMOVE P9_J2 P9_CAPPED_OUT P9_SUBSTEPS_OUT
export P9GPU_MODE=${P9PROD_MODE:-gpu}  # P9PROD_MODE=cpu: the CPU twin, for testing the package only
GPU=bin/p9gpu
SIM=bin/p9sim
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> production.log; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
finish() { rm -f production.pid; }
trap finish EXIT
trap 'log "stopped (signal)"; exit 130' INT TERM HUP

log "start, package $(cat PACKAGE-VERSION), p9gpu sha256 $(sha $GPU)"
if ! sh check.sh > check/report.txt 2>&1; then
  log "CHECK FAILED: the production run is not started (see check/report.txt)"
  exit 3
fi
log "check: ALL SAME"

mkdir -p segments
k=0
while [ "$k" -lt "$SEGMENTS" ]; do
  d=segments/seg$(printf %03d "$k")
  if [ -f "$d/DONE" ]; then k=$((k + 1)); continue; fi
  mkdir -p "$d"
  rm -f "$d/output.sa" "$d/final.state" "$d/flybys.tsv" "$d/removed.tsv" "$d/result.txt" "$d/stderr.txt"
  if [ "$k" -eq 0 ]; then
    cp run/input.sa "$d/input.sa"
  else
    prev=segments/seg$(printf %03d $((k - 1)))
    "$SIM" last "$prev/output.sa" "$d/input.tmp" > /dev/null || { log "segment $k: no input from $prev"; exit 4; }
    mv "$d/input.tmp" "$d/input.sa"
  fi
  t_end=$(awk -v k="$k" -v s="$SEGMENT_YR" 'BEGIN { printf "%.17g", (k + 1) * s }')
  log "segment $k: start ($d, input sha256 $(sha "$d/input.sa"), to t = $t_end yr)"
  P9_FLYBY_OUT=$d/flybys.tsv P9_REMOVED_OUT=$d/removed.tsv "$GPU" run "$d/input.sa" "$t_end" "$SNAPSHOTS_PER_SEGMENT" "$d/output.sa" "$d/final.state" \
    > "$d/result.txt" 2> "$d/stderr.txt" || { log "segment $k: p9gpu FAILED (see $d/stderr.txt)"; exit 4; }
  line=$(grep '^result_sha256=' "$d/result.txt") || { log "segment $k: no result line"; exit 4; }
  { echo "input_sha256=$(sha "$d/input.sa")"; echo "output_sha256=$(sha "$d/output.sa")"; echo "$line"; } > "$d/DONE.tmp"
  mv "$d/DONE.tmp" "$d/DONE"
  get() { printf '%s\n' "$line" | tr ' ' '\n' | sed -n "s/^$1=//p"; }
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$k" "$t_end" "$(get N_end)" "$(get wall_s)" "$(get result_sha256)" "$(get collisions)" >> segments.tsv
  log "segment $k: done, N_end $(get N_end), wall $(get wall_s) s, result $(get result_sha256), collisions $(get collisions)"
  k=$((k + 1))
done
log "production run complete: $SEGMENTS segments"
