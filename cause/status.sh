#!/bin/sh
# MEDAS p9-search, cause search: state of the check and the jobs (read only).
cd "$(dirname "$0")"
if [ -f run.pid ] && kill -0 "$(cat run.pid)" 2>/dev/null; then echo "running (pid $(cat run.pid))"; else echo "not running"; fi
[ -f check/report.txt ] && echo "check: $(tail -n 1 check/report.txt)"
for J in jobs/*/; do
  j=$(basename "$J"); . "$J/params.env"
  n=$(ls "$J"segments/seg*/DONE 2>/dev/null | wc -l)
  echo "$j: $n of $SEGMENTS segments of $(awk -v s="$SEGMENT_YR" 'BEGIN { printf "%g", s / 1e6 }') Myr done"
  [ -f "$J/segments.tsv" ] && awk -F'\t' -v n="$SEGMENTS" '{ w += $4; k++; last = $0 } END { split(last, f, "\t"); printf "   last: to %.0f Myr, %d test particles left; %.1f h so far, about %.1f h more at that pace\n", f[2] / 1e6, f[3] - 6, w / 3600, (n - k) * w / k / 3600 }' "$J/segments.tsv"
  cur=$(ls -d "$J"segments/seg* 2>/dev/null | while read -r d; do [ -f "$d/DONE" ] || echo "$d"; done | head -n 1)
  [ -n "$cur" ] && [ -f "$cur/stderr.txt" ] && echo "   running: $(basename "$cur"), $(grep '^snapshot' "$cur/stderr.txt" | tail -n 1)"
done
command -v nvidia-smi > /dev/null 2>&1 && echo "gpu: $(nvidia-smi --query-gpu=utilization.gpu,clocks.sm,power.draw,temperature.gpu,memory.used --format=csv,noheader | head -n 1)"
echo "disk: $(du -sh jobs 2>/dev/null | cut -f1) in jobs/, $(df -h . | tail -n 1 | awk '{ print $4 }') free"
echo "log (last 4):"; tail -n 4 run.log 2>/dev/null
