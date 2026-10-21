#!/bin/sh
# MEDAS p9-search, cause search: the check, then the jobs (started by start.sh; not meant to be run directly).
# The jobs of JOBS (default: both) run at the same time on the GPU (each a separate process; 8,000 test
# particles do not fill an L40S); PARALLEL=0 runs them one after the other.
set -u
cd "$(dirname "$0")"
JOBS=${JOBS:-"J1-dt025 J2-p9zone21"}
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> run.log; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
pids=""
finish() { rm -f run.pid; }
trap finish EXIT
trap 'log "stopped (signal)"; for p in $pids; do kill -TERM "$p" 2>/dev/null; done; wait; exit 130' INT TERM HUP

log "start, package $(cat PACKAGE-VERSION), p9gpu sha256 $(sha bin/p9gpu), jobs: $JOBS"
sh check.sh > check/report.txt 2>&1 &
pids=$!
wait $pids || { log "CHECK FAILED: the jobs are not started (see check/report.txt)"; exit 3; }
pids=""
log "check: ALL SAME"
if [ "${PARALLEL:-1}" = 1 ]; then
  for j in $JOBS; do sh run-job.sh "$j" & pids="$pids $!"; done
  wait
else
  for j in $JOBS; do sh run-job.sh "$j" & pids=$!; wait $pids || exit 4; done
fi
log "all jobs ended"
