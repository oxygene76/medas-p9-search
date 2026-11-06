#!/bin/sh
# MEDAS p9-search: segments of finished runs computed again from their stored inputs (A100 window, point 3); only
# hashes are compared, nothing of the content is looked at. Started by start.sh; not meant to be run directly.
#
# For each line of TARGETS: the segment's input (segments/segNNN/input.sa, checked against the input_sha256 of its
# DONE), the settings of the run (params.env of the run or the job), the run's own p9gpu (checked: sha256
# 7666c5ba..., the production binary). The run directories are only read; everything is written under runs/.
# Compared: the result hash with the DONE file and with segments.tsv; for information also the sha256 of flybys.tsv
# and removed.tsv. RESULT/REPRO.tsv, RESULT/VERDICT.txt.
set -u
export LC_ALL=C
cd "$(dirname "$0")"
RUNS=${RUNS:-$HOME/runs}
P9GPU_SHA=7666c5ba4560a8c20437e01ee041194a17579e08efff90f43be9c6068c7d566f
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> run.log; }
child=""
trap '[ -n "$child" ] && kill -TERM "$child" 2>/dev/null; log "stopped (signal)"; rm -f run.pid; exit 130' INT TERM HUP
trap 'rm -f run.pid' EXIT
sha() { sha256sum "$1" | cut -d' ' -f1; }
mkdir -p RESULT runs
TSV=RESULT/REPRO.tsv
[ -f "$TSV" ] || printf 'name\tsegment\twall_s\tresult_sha256\tDONE\tsegments.tsv\tflybys.tsv\tremoved.tsv\tverdict\n' > "$TSV"
CPUS=$(lscpu -p=CPU,CORE,SOCKET | grep -v '^#' | awk -F, -v s="${SOCKET:-1}" '$3 == s && !seen[$2]++ { print $1 }' | paste -sd, -)
log "start, package $(cat PACKAGE-VERSION), GPU $CUDA_VISIBLE_DEVICES, CPUs $CPUS"
grep -v '^#' TARGETS | while read -r name dir job k; do
  [ -n "$name" ] || continue
  if grep -q "^$name	" "$TSV"; then log "$name: done before, skipped"; continue; fi
  R=$RUNS/$dir
  if [ "$job" = - ]; then J=$R; else J=$R/jobs/$job; fi
  S=$J/segments/seg$(printf %03d "$k")
  for f in "$S/DONE" "$S/input.sa" "$J/params.env" "$R/bin/p9gpu"; do
    [ -f "$f" ] || { log "$name: missing $f"; printf '%s\t%s\t-\t-\t-\t-\t-\t-\tMISSING\n' "$name" "$k" >> "$TSV"; continue 2; }
  done
  [ "$(sha "$R/bin/p9gpu")" = "$P9GPU_SHA" ] || { log "$name: $R/bin/p9gpu is not the production binary"; printf '%s\t%s\t-\t-\t-\t-\t-\t-\tWRONG-BINARY\n' "$name" "$k" >> "$TSV"; continue; }
  [ "$(sha "$S/input.sa")" = "$(sed -n 's/^input_sha256=//p' "$S/DONE")" ] || { log "$name: input.sa does not match its DONE"; printf '%s\t%s\t-\t-\t-\t-\t-\t-\tINPUT-MISMATCH\n' "$name" "$k" >> "$TSV"; continue; }
  want=$(grep -o 'result_sha256=[0-9a-f]*' "$S/DONE" | cut -d= -f2)
  tsv=$(awk -F'\t' -v k="$k" '$1 == k { print $5 }' "$J/segments.tsv")
  d=runs/$name; rm -rf "$d"; mkdir -p "$d"; cp "$S/input.sa" "$d/input.sa"
  # the settings exactly as run-production.sh / run-job.sh set them
  ( . "$J/params.env"
    export P9_ENCOUNTER_METHOD P9_ENCOUNTER_RADII P9_COLLISION_RADII P9_PLANET_SUBSTEPS P9_R_IN P9GPU_REAL
    unset P9_ENCOUNTER_REMOVE P9_J2 P9_CAPPED_OUT P9_SUBSTEPS_OUT
    export P9GPU_MODE=gpu
    t_end=$(awk -v k="$k" -v s="$SEGMENT_YR" 'BEGIN { printf "%.17g", (k + 1) * s }')
    log "$name: start ($S, to t = $t_end yr)"
    exec env P9_FLYBY_OUT="$d/flybys.tsv" P9_REMOVED_OUT="$d/removed.tsv" taskset -c "$CPUS" nice -n 10 "$R/bin/p9gpu" run "$d/input.sa" "$t_end" \
      "$SNAPSHOTS_PER_SEGMENT" "$d/output.sa" "$d/final.state" > "$d/result.txt" 2> "$d/stderr.txt" ) &
  child=$!; wait "$child"; rc=$?; child=""
  got=$(grep -o 'result_sha256=[0-9a-f]*' "$d/result.txt" 2>/dev/null | cut -d= -f2)
  wall=$(grep -o 'wall_s=[0-9.]*' "$d/result.txt" 2>/dev/null | cut -d= -f2)
  fb=-; rm_=-
  [ -f "$S/flybys.tsv" ] && [ -f "$d/flybys.tsv" ] && { [ "$(sha "$S/flybys.tsv")" = "$(sha "$d/flybys.tsv")" ] && fb=same || fb=DIFFERENT; }
  [ -f "$S/removed.tsv" ] && [ -f "$d/removed.tsv" ] && { [ "$(sha "$S/removed.tsv")" = "$(sha "$d/removed.tsv")" ] && rm_=same || rm_=DIFFERENT; }
  if [ $rc -ne 0 ] || [ -z "$got" ]; then v=FAILED; elif [ "$got" = "$want" ] && [ "$got" = "$tsv" ]; then v=SAME; else v=DIFFERENT; fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$name" "$k" "${wall:--}" "${got:-none}" "$( [ "$got" = "$want" ] && echo same || echo DIFFERENT)" \
    "$( [ "$got" = "$tsv" ] && echo same || echo DIFFERENT)" "$fb" "$rm_" "$v" >> "$TSV"
  rm -f "$d/output.sa" "$d/input.sa"
  log "$name: $v (result $got, wall ${wall:-?} s)"
done
n=$(($(wc -l < "$TSV") - 1)); same=$(awk -F'\t' 'NR > 1 && $9 == "SAME"' "$TSV" | wc -l)
printf 'VERDICT: %d of %d segments give their stored result hash again%s\n' "$same" "$n" "$( [ "$same" = "$n" ] && echo "" || echo " (see REPRO.tsv)")" > RESULT/VERDICT.txt
cat RESULT/VERDICT.txt >> run.log
log "reproduction complete"
