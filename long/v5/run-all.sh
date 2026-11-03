#!/bin/sh
# MEDAS p9-search, paired long runs (seeds 110-112), group V5: the check, then the jobs (started by start.sh; not meant to be run
# directly). The jobs of JOBS (default: all in jobs/) run in AT_ONCE lanes at the same time on the GPU (default 3:
# the three seeds at once, decision Q3 of docs/long-runs-110-112-criteria.md; without MPS not faster in all, with the
# same result hashes; if the first segment shows a loss, AT_ONCE=1);
# each lane one job after the other, each job a separate p9gpu process with one CPU core).
set -u
cd "$(dirname "$0")"
JOBS=${JOBS:-$(ls jobs)}
AT_ONCE=${AT_ONCE:-3}
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
