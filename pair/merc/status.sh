#!/bin/sh
# MEDAS p9-search, paired tests of sets A and B, group M (MERCURIUS): state of the check and the slices (read only).
cd "$(dirname "$0")"
export LC_ALL=C
if [ -f run.pid ] && kill -0 "$(cat run.pid)" 2>/dev/null; then echo "running (pid $(cat run.pid))"; else echo "not running"; fi
[ -f check/report.txt ] && echo "check: $(tail -n 1 check/report.txt)"
total=0; done_=0
for J in jobs/*/; do
  . "$J/params.env"; total=$((total + SEGMENTS))
  done_=$((done_ + $(ls "$J"segments/seg*/DONE 2>/dev/null | wc -l)))
done
echo "segments done: $done_ of $total ($(ls jobs | wc -l) slices of $SEGMENTS segments of $(awk -v s="$SEGMENT_YR" 'BEGIN { printf "%g", s / 1e6 }') Myr)"
for s in $(ls jobs | sed 's/-part.*//' | sort -u); do
  n=0; c=0
  for J in jobs/$s-part*/; do n=$((n + 1)); [ "$(ls "$J"segments/seg*/DONE 2>/dev/null | wc -l)" -ge "$SEGMENTS" ] && c=$((c + 1)); done
  echo "  $s: $c of $n slices complete"
done
cat jobs/*/segments.tsv 2>/dev/null | awk -F'\t' -v total="$total" -v d="$done_" -v t="${THREADS:-$(cat threads 2>/dev/null || echo 14)}" \
  '{ w += $4; k++ } END { if (k) printf "core time so far %.0f h (%.0f s per segment); at that pace about %.0f h more with %d threads\n", w / 3600, w / k, (total - d) * w / k / t / 3600, t }'
# only the p9sim processes of this package (the MERCURIUS part of 110-112 runs the same command in its own directory)
here=$(pwd -P); n=0; nices=""
for p in $(ps -u "$(id -u)" -o pid=,args= 2>/dev/null | awk '$2 == "bin/p9sim" && $3 == "run" { print $1 }'); do
  [ "$(readlink "/proc/$p/cwd" 2>/dev/null)" = "$here" ] || continue
  n=$((n + 1)); nices="$nices $(ps -o ni= -p "$p" | tr -d ' ')"
done
echo "running p9sim processes of this package: $n$( [ -n "$nices" ] && echo " (nice:$(echo $nices | tr ' ' '\n' | sort -u | tr '\n' ' '| sed 's/ $//'))")"
[ -f run.pid ] && kill -0 "$(cat run.pid)" 2>/dev/null && echo "pinned to CPUs: $(taskset -cp "$(cat run.pid)" 2>/dev/null | sed 's/.*: //'), nice $(ps -o ni= -p "$(cat run.pid)" | tr -d ' '), I/O class $(ionice -p "$(cat run.pid)" 2>/dev/null || echo unknown)"
echo "load: $(cut -d' ' -f1-3 /proc/loadavg)"
echo "disk: $(du -sh jobs 2>/dev/null | cut -f1) in jobs/, $(df -h . | tail -n 1 | awk '{ print $4 }') free"
echo "log (last 4):"; tail -n 4 run.log 2>/dev/null
