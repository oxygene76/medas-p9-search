#!/bin/sh
# Samples the GPU memory used (MiB) every 0.2 s while a command runs; prints the maximum.
#   tools/gpu_mem_sample.sh <command...>
base=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
f=$(mktemp)
( while :; do nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1 >> "$f"; sleep 0.2; done ) &
s=$!
"$@"
rc=$?
kill $s 2>/dev/null
wait $s 2>/dev/null
max=$(sort -n "$f" | tail -1)
rm -f "$f"
echo "gpu_mem_peak_mib=$max gpu_mem_before_mib=$base" >&2
exit $rc
