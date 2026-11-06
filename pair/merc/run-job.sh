#!/bin/sh
# MEDAS p9-search, paired tests of sets A and B, group M (MERCURIUS): one slice as a chain of segments (started by run-all.sh), at nice 19.
#   sh run-job.sh JOB      jobs/JOB/input.sa, jobs/JOB/params.env -> jobs/JOB/segments/segNNN
# Segment k runs from k * SEGMENT_YR to (k + 1) * SEGMENT_YR: segment 0 from jobs/JOB/input.sa, segment k
# from the last snapshot of segment k - 1 (bin/p9sim last). A segment counts as done only when its result is
# written (DONE). After an interruption the next start skips the done segments and computes the interrupted
# one again from its input: the same bits with or without interruptions.
set -u
export LC_ALL=C   # numbers with a decimal point (bash printf and mawk follow LC_NUMERIC)
cd "$(dirname "$0")"
JOB=$1
J=jobs/$JOB
. "$J/params.env"
export P9_R_IN P9_ENCOUNTER_METHOD P9_ENCOUNTER_REMOVE
unset P9_ENCOUNTER_RADII P9_COLLISION_RADII P9_PLANET_SUBSTEPS P9_J2 P9_FLYBY_OUT P9_REMOVED_OUT P9_CAPPED_OUT P9_SUBSTEPS_OUT
SIM=bin/p9sim
log() { printf '%s %s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$JOB" "$*" >> run.log; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
child=""
trap '[ -n "$child" ] && kill -TERM "$child" 2>/dev/null; log "stopped (signal)"; exit 130' INT TERM HUP
runbg() { "$@" & child=$!; wait "$child"; rc=$?; child=""; return $rc; }

mkdir -p "$J/segments"
k=0
while [ "$k" -lt "$SEGMENTS" ]; do
  d=$J/segments/seg$(printf %03d "$k")
  if [ -f "$d/DONE" ]; then k=$((k + 1)); continue; fi
  mkdir -p "$d"
  rm -f "$d/output.sa" "$d/final.state" "$d/result.txt" "$d/stderr.txt"
  if [ "$k" -eq 0 ]; then
    cp "$J/input.sa" "$d/input.sa"
  else
    prev=$J/segments/seg$(printf %03d $((k - 1)))
    runbg "$SIM" last "$prev/output.sa" "$d/input.tmp" > /dev/null || { log "segment $k: no input from $prev"; exit 4; }
    mv "$d/input.tmp" "$d/input.sa"
  fi
  t_end=$(awk -v k="$k" -v s="$SEGMENT_YR" 'BEGIN { printf "%.17g", (k + 1) * s }')
  runbg nice -n 19 "$SIM" run "$d/input.sa" "$t_end" "$SNAPSHOTS_PER_SEGMENT" "$d/output.sa" "$d/final.state" \
    > "$d/result.txt" 2> "$d/stderr.txt" || { log "segment $k: p9sim FAILED (see $d/stderr.txt)"; exit 4; }
  line=$(grep '^result_sha256=' "$d/result.txt") || { log "segment $k: no result line"; exit 4; }
  { echo "input_sha256=$(sha "$d/input.sa")"; echo "output_sha256=$(sha "$d/output.sa")"; echo "$line"; } > "$d/DONE.tmp"
  mv "$d/DONE.tmp" "$d/DONE"
  get() { printf '%s\n' "$line" | tr ' ' '\n' | sed -n "s/^$1=//p"; }
  printf '%s\t%s\t%s\t%s\t%s\n' "$k" "$t_end" "$(get N_end)" "$(get wall_s)" "$(get result_sha256)" >> "$J/segments.tsv"
  log "segment $k: done, N_end $(get N_end), wall $(get wall_s) s"
  k=$((k + 1))
done
log "complete: $SEGMENTS segments"
