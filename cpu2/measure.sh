#!/bin/sh
# MEDAS p9-search: does load on the cores of CPU 2 (socket 1) slow the A100? (decision of 2026-11-06, criteria of the
# paired tests section 7). Started by start.sh; not meant to be run directly.
#
# p9gpu runs as in the A100 runs: pinned to all physical cores of socket 1 (taskset), nice 10, CUDA_VISIBLE_DEVICES =
# the A100. The load: k MERCURIUS processes (the job cpu-merc-4k-1m, p9sim) pinned to the upper k cores of socket 1,
# nice 19, k = 0, 8 and 12, started 30 s before each measured job. Jobs: gpu-v5-4k-1m (4,000 test particles,
# latency-bound, the case of the paired V5 runs) and gpu-v5-64k-1m (64,000, GPU-bound, the case of sets A and B).
# REPS rounds (default 3); in each round the levels in the order 0, 8, 12, 0 (the second 0 shows drift).
# Every result hash is compared with the one of the speed comparison (a bit check as well).
# Rule: k cores of CPU 2 may be used for MERCURIUS if the median wall time of gpu-v5-4k-1m with load k is at most
# 3 % above the median of the level 0 runs. Written to RESULT/VERDICT.txt.
set -u
export LC_ALL=C
cd "$(dirname "$0")"
REPS=${REPS:-3}
LIMIT=${LIMIT:-3.0}
LEVELS=${LEVELS:-"8 12"}                     # cores under load besides level 0
JOBS=${JOBS:-"gpu-v5-4k-1m gpu-v5-64k-1m"}   # the first decides
SOCKET=${SOCKET:-1}                          # LEVELS, JOBS, SOCKET other than the defaults: for testing the package only
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> run.log; }
loadpids=""
# each load loop runs in its own session (setsid): its process group id is its pid, and kill -TERM -<pgid> stops the
# loop and the p9sim it runs at once
cleanup() { for p in $loadpids; do kill -TERM -"$p" 2>/dev/null; done; loadpids=""; rm -f runs/load-*.sa; }
trap 'cleanup; log "stopped (signal)"; rm -f run.pid; exit 130' INT TERM HUP
trap 'cleanup; rm -f run.pid' EXIT
mkdir -p RESULT runs
TSV=RESULT/RESULTS.tsv
[ -f "$TSV" ] || printf 'round\tlevel\tjob\tload_cores\twall_s\tresult_sha256\tverdict\n' > "$TSV"
S1=$(lscpu -p=CPU,CORE,SOCKET | grep -v '^#' | awk -F, -v s="$SOCKET" '$3 == s && !seen[$2]++ { print $1 }')
ALL1=$(echo "$S1" | paste -sd, -)
n1=$(echo "$S1" | wc -l)
maxk=$(echo $LEVELS | tr ' ' '\n' | sort -n | tail -n 1)
[ "$n1" -gt "$maxk" ] || { log "socket $SOCKET has $n1 physical cores; need more than $maxk"; exit 2; }
log "start, package $(cat PACKAGE-VERSION), GPU $CUDA_VISIBLE_DEVICES, socket $SOCKET cores $ALL1, load levels 0 $LEVELS, $REPS rounds, jobs $JOBS"

load_start() {   # k: the upper k cores of socket 1
  k=$1; [ "$k" -gt 0 ] || return 0
  LOADCORES=$(echo "$S1" | tail -n "$k" | paste -sd, -)
  for c in $(echo "$S1" | tail -n "$k"); do
    setsid sh -c 'while :; do env P9_R_IN=4.5 P9_ENCOUNTER_METHOD=kick P9_ENCOUNTER_REMOVE=1 taskset -c "$1" nice -n 19 bin/p9sim run \
      jobs/cpu-merc-4k-1m/input.sa 1000000.0 1 "runs/load-$1.sa" > /dev/null 2>&1; done' load "$c" &
    loadpids="$loadpids $!"
  done
  sleep 30
}
load_stop() {
  for p in $loadpids; do kill -TERM -"$p" 2>/dev/null; done
  wait 2>/dev/null; loadpids=""; rm -f runs/load-*.sa
}
run_gpu() {   # round level job
  d=runs/$1-$2-$3; rm -rf "$d"; mkdir -p "$d"
  env $(grep '^P9' "jobs/$3/run.env" | grep -v '^P9_FLYBY_OUT') P9_FLYBY_OUT="$d/flybys.tsv" taskset -c "$ALL1" nice -n 10 bin/p9gpu run \
    "jobs/$3/input.sa" 1000000.0 1 "$d/output.sa" "$d/final.state" > "$d/result.txt" 2> "$d/stderr.txt"
  line=$(grep '^result_sha256=' "$d/result.txt" | tail -n 1)
  got=$(echo "$line" | sed -n 's/^result_sha256=\([0-9a-f]*\).*/\1/p')
  wall=$(echo "$line" | tr ' ' '\n' | sed -n 's/^wall_s=//p')
  [ "$got" = "$(cat "jobs/$3/EXPECTED")" ] && v=SAME || v=DIFFERENT
  rm -f "$d/output.sa"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "${LOADCORES:--}" "${wall:-0}" "${got:-none}" "$v" >> "$TSV"
  log "round $1 level $2 $3: $v, wall ${wall:-?} s"
}

r=1
while [ "$r" -le "$REPS" ]; do
  for level in 0 $LEVELS 0; do
    LOADCORES=""
    load_start "$level"
    for j in $JOBS; do run_gpu "$r" "$level" "$j"; done
    load_stop
  done
  r=$((r + 1))
done

# evaluation (awk): medians per level and job, slowdown against level 0; the first job decides
awk -F'\t' -v lim="$LIMIT" -v levels="$LEVELS" -v jobs="$JOBS" 'NR > 1 { w[$3 "," $2] = w[$3 "," $2] " " $5; if ($7 != "SAME") bad++ }
  function med(s,   a, n, i, j, t) { n = split(s, a, " "); for (i = 1; i <= n; i++) for (j = i + 1; j <= n; j++) if (a[j] + 0 < a[i] + 0) { t = a[i]; a[i] = a[j]; a[j] = t }
    return n % 2 ? a[(n + 1) / 2] : (a[n / 2] + a[n / 2 + 1]) / 2 }
  END {
    nl = split(levels, L, " "); nj = split(jobs, J, " "); allowed = 0; ok = 1
    for (jj = 1; jj <= nj; jj++) {
      job = J[jj]; b = med(w[job ",0"])
      printf "%s: level 0 median %.3f s\n", job, b
      for (i = 1; i <= nl; i++) { k = L[i]; m = med(w[job "," k]); s = 100 * (m / b - 1)
        printf "%s: %d cores busy, median %.3f s, %+.1f %%%s\n", job, k, m, s, (jj == 1 ? (s <= lim ? " (within the limit)" : " (above the limit)") : " (information)")
        if (jj == 1) { if (s <= lim && ok) allowed = k; else ok = 0 } }
    }
    if (bad) { printf "bit check: %d runs DIFFERENT or FAILED: no cores of CPU 2 are allowed\n", bad; allowed = 0 }
    else print "bit check: all runs SAME"
    printf "VERDICT: cores of CPU 2 allowed for MERCURIUS: %d (limit %.1f %% at %s)\n", allowed, lim, J[1]
  }' "$TSV" > RESULT/VERDICT.txt
cat RESULT/VERDICT.txt >> run.log
log "measurement complete"
