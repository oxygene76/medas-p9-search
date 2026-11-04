#!/bin/sh
# MEDAS p9-search, comparison with Brown & Batygin 2021 (sets A and B), p9gpu v5: starts (or resumes) the check and the jobs in the background, as the current user.
#   The defaults of this package are in defaults.env (card, jobs at once, socket, whether other processes on the
#   card are allowed); each can be overridden: AT_ONCE=..., JOBS="...", GPU_NAME=... or CUDA_VISIBLE_DEVICES=<UUID>,
#   SOCKET=... or CPUS=..., FORCE=1 (start although other processes are on a card that must be free).
#   sh start.sh     then: sh status.sh   (stop: sh stop.sh; start.sh again resumes)
set -eu
export LC_ALL=C   # numbers with a decimal point (bash printf and mawk follow LC_NUMERIC)
cd "$(dirname "$0")"
if [ -f run.pid ] && kill -0 "$(cat run.pid)" 2>/dev/null; then
  echo "already running (pid $(cat run.pid)); sh status.sh"; exit 1
fi
[ "$(id -u)" != 0 ] || { echo "please run as a normal user, not as root"; exit 1; }
[ "${P9EQUIV_MODE:-gpu}" = cpu ] || command -v nvidia-smi > /dev/null 2>&1 || { echo "no nvidia-smi: is the NVIDIA driver installed?"; exit 2; }
need=$(cat bin/REQUIRES-glibc)
have=$(getconf GNU_LIBC_VERSION 2>/dev/null | awk '{print $2}')
if [ -z "$have" ] || [ "$(printf '%s\n%s\n' "$need" "$have" | sort -V | head -n 1)" != "$need" ]; then
  echo "STOP: the binaries need glibc $need or newer, this system has ${have:-an unknown version}"; exit 3
fi
for j in jobs/*/; do [ "$(sha256sum "$j/input.sa" | cut -d' ' -f1)" = "$(cat "$j/INPUT-SHA256")" ] || { echo "$j/input.sa does not match its sha256"; exit 2; }; done
. ./select-gpu.sh
SOCKET=${SOCKET:-$SOCKET_DEFAULT}
CPUS=${CPUS:-$(lscpu -p=CPU,CORE,SOCKET | grep -v '^#' | awk -F, -v s="$SOCKET" '$3 == s && !seen[$2]++ { print $1 }' | paste -sd, -)}
[ -n "$CPUS" ] || { echo "no CPUs on socket $SOCKET (lscpu -p=CPU,CORE,SOCKET; SOCKET=... or CPUS=...)"; exit 2; }
AT_ONCE=${AT_ONCE:-$AT_ONCE_DEFAULT}
export AT_ONCE
# sets A and B (REQUIRE_V2=1): a job starts only with its V2 verdict "within the limits" recorded in v2/<job>.ok
# (docs/bb2021-comparison-criteria.md addendum 16 of medas-p9-search; tools/v2_encounter_check.py writes the verdict)
if [ "${REQUIRE_V2:-0}" = 1 ]; then
  for j in ${JOBS:-$(ls jobs)}; do
    grep -qx "within the limits" "v2/$j.ok" 2>/dev/null || { echo "STOP: no V2 verdict 'within the limits' in v2/$j.ok for $j"; exit 1; }
  done
fi
echo "${CUDA_VISIBLE_DEVICES:-cpu mode}" > gpu-uuid
others=$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name --format=csv,noheader 2>/dev/null | awk -F', ' -v u="${CUDA_VISIBLE_DEVICES:-}" '$1 == u' | tr '\n' ';')
if [ -n "$others" ] && [ "${ALLOW_BUSY_CARD:-0}" != 1 ] && [ "${FORCE:-0}" != 1 ]; then
  echo "STOP: compute processes on the card ${CUDA_VISIBLE_DEVICES}: $others (the production run? FORCE=1 starts anyway)"; exit 1
fi
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start: GPU ${CUDA_VISIBLE_DEVICES:-cpu mode} ($(nvidia-smi -i "${CUDA_VISIBLE_DEVICES:-0}" --query-gpu=name --format=csv,noheader 2>/dev/null)), CPUs $CPUS, AT_ONCE $AT_ONCE; other processes on the card: ${others:-none}" >> start.log
command -v setsid > /dev/null 2>&1 && S=setsid || S=""
nohup $S taskset -c "$CPUS" sh run-all.sh >> run.out 2>&1 < /dev/null &
echo $! > run.pid
sleep 2
if kill -0 "$(cat run.pid)" 2>/dev/null; then
  echo "started (pid $(cat run.pid)); first the check (a few minutes), then the jobs. Status: sh status.sh"
else
  echo "did not stay up; see run.log and run.out"; exit 1
fi
