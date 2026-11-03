#!/bin/sh
# MEDAS p9-search, paired long runs (seeds 110-112), group V5: starts (or resumes) the check and the jobs in the background, as the current user.
#   AT_ONCE=1 sh start.sh  jobs at the same time on the GPU (default 3: all three); JOBS="V5-s110" only these
#   GPU_NAME=L40S (default): the card, chosen by name (CUDA_VISIBLE_DEVICES = its UUID; select-gpu.sh)
#   SOCKET=1 (default): the p9gpu processes pinned to the cores of that CPU socket (CPUS=... a list instead)
#   sh start.sh     then: sh status.sh   (stop: sh stop.sh; start.sh again resumes)
set -eu
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
CPUS=${CPUS:-$(lscpu -p=CPU,CORE,SOCKET | grep -v '^#' | awk -F, -v s="${SOCKET:-1}" '$3 == s && !seen[$2]++ { print $1 }' | paste -sd, -)}
[ -n "$CPUS" ] || { echo "no CPUs on socket ${SOCKET:-1} (lscpu -p=CPU,CORE,SOCKET; SOCKET=... or CPUS=...)"; exit 2; }
echo "${CUDA_VISIBLE_DEVICES:-cpu mode}" > gpu-uuid
others=$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name --format=csv,noheader 2>/dev/null | awk -F', ' -v u="${CUDA_VISIBLE_DEVICES:-}" '$1 == u' | tr '\n' ';')
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start: GPU ${CUDA_VISIBLE_DEVICES:-cpu mode} ($(nvidia-smi -i "${CUDA_VISIBLE_DEVICES:-0}" --query-gpu=name --format=csv,noheader 2>/dev/null)), CPUs $CPUS, AT_ONCE ${AT_ONCE:-3}; other processes on the card: ${others:-none}" >> start.log
command -v setsid > /dev/null 2>&1 && S=setsid || S=""
nohup $S taskset -c "$CPUS" sh run-all.sh >> run.out 2>&1 < /dev/null &
echo $! > run.pid
sleep 2
if kill -0 "$(cat run.pid)" 2>/dev/null; then
  echo "started (pid $(cat run.pid)); first the check (a few minutes), then the jobs. Status: sh status.sh"
else
  echo "did not stay up; see run.log and run.out"; exit 1
fi
