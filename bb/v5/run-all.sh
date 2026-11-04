#!/bin/sh
# MEDAS p9-search, comparison with Brown & Batygin 2021 (sets A and B), p9gpu v5: the check, then the jobs (started by start.sh; not meant to be run
# directly). The jobs of JOBS (default: all in jobs/, in name order) run in AT_ONCE lanes at the same time on the GPU
# (default: AT_ONCE_DEFAULT of defaults.env; without MPS several at once are not faster in all);
# each lane one job after the other, each job a separate p9gpu process with one CPU core).
set -u
export LC_ALL=C   # numbers with a decimal point (bash printf and mawk follow LC_NUMERIC)
cd "$(dirname "$0")"
JOBS=${JOBS:-$(ls jobs)}
[ -f ./defaults.env ] && . ./defaults.env
AT_ONCE=${AT_ONCE:-$AT_ONCE_DEFAULT}
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> run.log; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
pids=""
finish() { rm -f run.pid; }
trap finish EXIT
trap 'log "stopped (signal)"; for p in $pids; do kill -TERM "$p" 2>/dev/null; done; wait; exit 130' INT TERM HUP

log "start, package $(cat PACKAGE-VERSION), p9gpu sha256 $(sha bin/p9gpu), $AT_ONCE at once, jobs: $(echo $JOBS)"
sh check.sh > check/report.txt 2>&1 &
pids=$!
wait $pids || { log "CHECK FAILED: the jobs are not started (see check/report.txt)"; exit 3; }
pids=""
log "check: ALL SAME"
lane() { for j in "$@"; do sh run-job.sh "$j" || log "$j: ended with an error, the lane goes on"; done; }
i=0
while [ "$i" -lt "$AT_ONCE" ]; do
  mine=$(echo $JOBS | tr ' ' '\n' | awk -v i="$i" -v n="$AT_ONCE" 'NF && (NR - 1) % n == i')
  [ -n "$mine" ] && { lane $mine & pids="$pids $!"; }
  i=$((i + 1))
done
wait
log "all jobs ended"
