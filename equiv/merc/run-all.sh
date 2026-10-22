#!/bin/sh
# MEDAS p9-search, equivalence test, group M (MERCURIUS): the check, then the slices (started by start.sh; not
# meant to be run directly). THREADS slices at the same time (default 14), each one single-threaded p9sim process
# with nice 10; the slices of seed 101 first, then 102, ...
set -u
cd "$(dirname "$0")"
THREADS=${THREADS:-14}
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> run.log; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
pids=""
finish() { rm -f run.pid; }
trap finish EXIT
trap 'log "stopped (signal)"; for p in $pids; do kill -TERM "$p" 2>/dev/null; done; wait; exit 130' INT TERM HUP

log "start, package $(cat PACKAGE-VERSION), p9sim sha256 $(sha bin/p9sim), $THREADS threads"
sh check.sh > check/report.txt 2>&1 &
pids=$!
wait $pids || { log "CHECK FAILED: the slices are not started (see check/report.txt)"; exit 3; }
log "check: ALL SAME"
ls jobs | xargs -P "$THREADS" -I{} sh run-job.sh {} &
pids=$!
wait
log "all slices ended"
