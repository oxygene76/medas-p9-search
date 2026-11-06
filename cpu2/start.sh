#!/bin/sh
# MEDAS p9-search, CPU-2 measurement: starts measure.sh in the background, as the current user (about 20 min).
#   GPU_NAME=A100 (default) or CUDA_VISIBLE_DEVICES=<UUID>; refuses while another compute process is on that card.
#   sh start.sh, then sh status.sh; sh stop.sh stops (the load processes too); the result: RESULT/VERDICT.txt
set -eu
export LC_ALL=C
cd "$(dirname "$0")"
if [ -f run.pid ] && kill -0 "$(cat run.pid)" 2>/dev/null; then echo "already running (pid $(cat run.pid))"; exit 1; fi
[ "$(id -u)" != 0 ] || { echo "please run as a normal user, not as root"; exit 1; }
for f in bin/p9gpu bin/p9sim; do [ "$(sha256sum "$f" | cut -d' ' -f1)" = "$(cut -d' ' -f1 "bin/SHA256-$(basename "$f")")" ] || { echo "$f does not match its sha256"; exit 2; }; done
for j in jobs/*/; do [ "$(sha256sum "$j/input.sa" | cut -d' ' -f1)" = "$(cat "$j/INPUT-SHA256")" ] || { echo "$j/input.sa does not match its sha256"; exit 2; }; done
if [ -z "${CUDA_VISIBLE_DEVICES:-}" ]; then
  CUDA_VISIBLE_DEVICES=$(nvidia-smi --query-gpu=uuid,name --format=csv,noheader | awk -F', ' -v n="${GPU_NAME:-A100}" 'index($2, n) { print $1; exit }')
  [ -n "$CUDA_VISIBLE_DEVICES" ] || { echo "no GPU named ${GPU_NAME:-A100}"; exit 2; }
fi
export CUDA_VISIBLE_DEVICES
others=$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name --format=csv,noheader 2>/dev/null | awk -F', ' -v u="$CUDA_VISIBLE_DEVICES" '$1 == u' | tr '\n' ';')
[ -z "$others" ] || { echo "STOP: compute processes on the card $CUDA_VISIBLE_DEVICES: $others"; exit 1; }
[ ! -f RESULT/VERDICT.txt ] || { echo "already measured: RESULT/VERDICT.txt (remove RESULT/ to measure again)"; exit 1; }
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start: GPU $CUDA_VISIBLE_DEVICES ($(nvidia-smi -i "$CUDA_VISIBLE_DEVICES" --query-gpu=name --format=csv,noheader)), load on the upper cores of socket 1" >> start.log
command -v setsid > /dev/null 2>&1 && S=setsid || S=""
nohup $S sh measure.sh >> run.out 2>&1 < /dev/null &
echo $! > run.pid
sleep 2
if kill -0 "$(cat run.pid)" 2>/dev/null; then echo "started (pid $(cat run.pid)); about 20 min. Status: sh status.sh"
else echo "did not stay up; see run.log and run.out"; exit 1; fi
