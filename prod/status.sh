#!/bin/sh
# MEDAS p9-search: state of the production run (read only).
cd "$(dirname "$0")"
. ./params.env
if [ -f production.pid ] && kill -0 "$(cat production.pid)" 2>/dev/null; then echo "running (pid $(cat production.pid))"; else echo "not running"; fi
[ -f check/report.txt ] && echo "check: $(tail -n 1 check/report.txt)"
done=$(ls segments/seg*/DONE 2>/dev/null | wc -l)
echo "segments done: $done of $SEGMENTS (each $(awk -v s="$SEGMENT_YR" 'BEGIN { printf "%g", s / 1e6 }') Myr)"
if [ -f segments.tsv ]; then
  echo "last done: $(tail -n 1 segments.tsv | awk -F'\t' '{ printf "segment %s to %.0f Myr, %d test particles left, %.0f s", $1, $2 / 1e6, $3 - 6, $4 }')"
  awk -F'\t' -v n="$SEGMENTS" '{ w += $4; k++ } END { if (k) printf "wall so far %.1f h, mean %.1f h per segment; at that pace about %.1f days more (fewer particles: less)\n", w / 3600, w / k / 3600, (n - k) * w / k / 86400 }' segments.tsv
fi
cur=$(ls -d segments/seg* 2>/dev/null | while read -r d; do [ -f "$d/DONE" ] || echo "$d"; done | head -n 1)
[ -n "$cur" ] && [ -f "$cur/stderr.txt" ] && echo "running segment: $cur, $(grep '^snapshot' "$cur/stderr.txt" | tail -n 1)"
command -v nvidia-smi > /dev/null 2>&1 && echo "gpu: $(nvidia-smi --query-gpu=utilization.gpu,clocks.sm,power.draw,temperature.gpu,memory.used --format=csv,noheader | head -n 1) (utilisation, SM clock, power, temperature, memory)"
echo "disk: $(du -sh segments 2>/dev/null | cut -f1) in segments/, $(df -h . | tail -n 1 | awk '{ print $4 }') free"
echo "log (last 3):"; tail -n 3 production.log 2>/dev/null
