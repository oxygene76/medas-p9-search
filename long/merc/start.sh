#!/bin/sh
# MEDAS p9-search, paired long runs (seeds 110-112), group M (MERCURIUS): starts (or resumes) the check and the jobs in the background, as the current user.
#   SOCKET=0 (default, "CPU 1"): pinned to the physical cores of that socket (CPUS=... a list instead)
#   THREADS=... slices at the same time (default: one per core of CPUS), one CPU thread each, nice 10
#   sh start.sh     then: sh status.sh   (stop: sh stop.sh; start.sh again resumes)
set -eu
export LC_ALL=C   # numbers with a decimal point (bash printf and mawk follow LC_NUMERIC)
cd "$(dirname "$0")"
if [ -f run.pid ] && kill -0 "$(cat run.pid)" 2>/dev/null; then
  echo "already running (pid $(cat run.pid)); sh status.sh"; exit 1
fi
[ "$(id -u)" != 0 ] || { echo "please run as a normal user, not as root"; exit 1; }
need=$(cat bin/REQUIRES-glibc)
have=$(getconf GNU_LIBC_VERSION 2>/dev/null | awk '{print $2}')
if [ -z "$have" ] || [ "$(printf '%s\n%s\n' "$need" "$have" | sort -V | head -n 1)" != "$need" ]; then
  echo "STOP: the binaries need glibc $need or newer, this system has ${have:-an unknown version}"; exit 3
fi
for j in jobs/*/; do [ "$(sha256sum "$j/input.sa" | cut -d' ' -f1)" = "$(cat "$j/INPUT-SHA256")" ] || { echo "$j/input.sa does not match its sha256"; exit 2; }; done
CPUS=${CPUS:-$(lscpu -p=CPU,CORE,SOCKET | grep -v '^#' | awk -F, -v s="${SOCKET:-0}" '$3 == s && !seen[$2]++ { print $1 }' | paste -sd, -)}
[ -n "$CPUS" ] || { echo "no CPUs on socket ${SOCKET:-0} (lscpu -p=CPU,CORE,SOCKET; SOCKET=... or CPUS=...)"; exit 2; }
THREADS=${THREADS:-$(echo "$CPUS" | tr ',' '\n' | awk -F- '{ c += (NF == 2 ? $2 - $1 + 1 : 1) } END { print c }')}
echo "$THREADS" > threads
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start: CPUs $CPUS, $THREADS slices at once, nice 10" >> start.log
command -v setsid > /dev/null 2>&1 && S=setsid || S=""
THREADS=$THREADS nohup $S taskset -c "$CPUS" sh run-all.sh >> run.out 2>&1 < /dev/null &
echo $! > run.pid
sleep 2
if kill -0 "$(cat run.pid)" 2>/dev/null; then
  echo "started (pid $(cat run.pid)); first the check (a few minutes), then the slices. Status: sh status.sh"
else
  echo "did not stay up; see run.log and run.out"; exit 1
fi
