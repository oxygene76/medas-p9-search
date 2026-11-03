#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Starts (or resumes) the production run of p9prod-9a084ed on the A100 (docs/production-criteria.md of
# medas-p9-search; decision P2 of 2026-11-03). The package itself stays unchanged; this wrapper only sets what it
# leaves to the environment:
#   - CUDA_VISIBLE_DEVICES = the UUID of the A100, found by name (GPU_NAME, default A100). Without it CUDA picks
#     its own order, and check.sh's header line names the first card of nvidia-smi whatever is used (A100
#     acceptance report 2026-11-03).
#   - the run pinned to the cores of CPU 2 (socket SOCKET, default 1; CPU 1 = socket 0 is for the M runs of
#     seeds 110-112 and later LS2), nice 10. start.sh starts with nohup and setsid: its children inherit all three.
# Refuses if any compute process is on the A100. Run as p9sim:
#   sh start-a100.sh ../p9prod-9a084ed          then: sh status-a100.sh ../p9prod-9a084ed
set -eu
PROD=$(cd "${1:?the unpacked package p9prod-9a084ed}" && pwd)
NAME=${GPU_NAME:-A100}
SOCKET=${SOCKET:-1}
[ -f "$PROD/start.sh" ] && [ "$(cat "$PROD/PACKAGE-VERSION" | cut -d' ' -f1)" = 9a084ed ] || { echo "$PROD is not p9prod-9a084ed"; exit 2; }
for f in p9gpu p9sim; do
	[ "$(sha256sum "$PROD/bin/$f" | cut -d' ' -f1)" = "$(cut -d' ' -f1 "$PROD/bin/SHA256-$f")" ] || { echo "bin/$f does not match its sha256"; exit 2; }
done
uuid=$(nvidia-smi --query-gpu=uuid,name --format=csv,noheader | awk -F', ' -v n="$NAME" 'index($2, n) { print $1; exit }')
[ -n "$uuid" ] || { echo "no GPU named $NAME"; nvidia-smi -L; exit 2; }
apps=$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name --format=csv,noheader | awk -F', ' -v u="$uuid" '$1 == u')
[ -z "$apps" ] || { echo "STOP: compute processes on the $NAME ($uuid): $apps"; exit 1; }
cpus=$(lscpu -p=CPU,CORE,SOCKET | grep -v '^#' | awk -F, -v s="$SOCKET" '$3 == s && !seen[$2]++ { print $1 }' | paste -sd, -)
[ -n "$cpus" ] || { echo "no CPUs on socket $SOCKET (lscpu -p=CPU,CORE,SOCKET)"; exit 2; }
echo "$(date -u +%FT%TZ) start: $NAME $uuid ($(nvidia-smi -i "$uuid" --query-gpu=name,pci.bus_id --format=csv,noheader)), CPUs $cpus (socket $SOCKET), nice 10" | tee -a "$PROD/a100-start.log"
cd "$PROD"
CUDA_VISIBLE_DEVICES=$uuid taskset -c "$cpus" nice -n 10 sh start.sh
