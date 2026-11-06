#!/bin/sh
# MEDAS p9-search, reproduction of stored segments: starts repro.sh in the background, as the current user (about 10-12 h on the A100).
#   GPU_NAME=A100 (default) or CUDA_VISIBLE_DEVICES=<UUID>; refuses while another compute process is on that card. RUNS=... the run directories (default $HOME/runs).
#   sh start.sh, then sh status.sh; sh stop.sh stops (start.sh resumes with the segments not yet done); the result: RESULT/VERDICT.txt
set -eu
export LC_ALL=C
cd "$(dirname "$0")"
if [ -f run.pid ] && kill -0 "$(cat run.pid)" 2>/dev/null; then echo "already running (pid $(cat run.pid))"; exit 1; fi
[ "$(id -u)" != 0 ] || { echo "please run as a normal user, not as root"; exit 1; }
[ -f TARGETS ] || { echo "no TARGETS"; exit 2; }
if [ -z "${CUDA_VISIBLE_DEVICES:-}" ]; then
  CUDA_VISIBLE_DEVICES=$(nvidia-smi --query-gpu=uuid,name --format=csv,noheader | awk -F', ' -v n="${GPU_NAME:-A100}" 'index($2, n) { print $1; exit }')
  [ -n "$CUDA_VISIBLE_DEVICES" ] || { echo "no GPU named ${GPU_NAME:-A100}"; exit 2; }
fi
export CUDA_VISIBLE_DEVICES
others=$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name --format=csv,noheader 2>/dev/null | awk -F', ' -v u="$CUDA_VISIBLE_DEVICES" '$1 == u' | tr '\n' ';')
[ -z "$others" ] || { echo "STOP: compute processes on the card $CUDA_VISIBLE_DEVICES: $others"; exit 1; }
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start: GPU $CUDA_VISIBLE_DEVICES ($(nvidia-smi -i "$CUDA_VISIBLE_DEVICES" --query-gpu=name --format=csv,noheader))" >> start.log
command -v setsid > /dev/null 2>&1 && S=setsid || S=""
nohup $S sh repro.sh >> run.out 2>&1 < /dev/null &
echo $! > run.pid
sleep 2
if kill -0 "$(cat run.pid)" 2>/dev/null; then echo "started (pid $(cat run.pid)); about 10-12 h. Status: sh status.sh"
else echo "did not stay up; see run.log and run.out"; exit 1; fi
