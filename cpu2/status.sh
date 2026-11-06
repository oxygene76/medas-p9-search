#!/bin/sh
# MEDAS p9-search, CPU-2 measurement: state (read only).
cd "$(dirname "$0")"
if [ -f run.pid ] && kill -0 "$(cat run.pid)" 2>/dev/null; then echo "running (pid $(cat run.pid))"; else echo "not running"; fi
[ -f RESULT/RESULTS.tsv ] && echo "runs done: $(($(wc -l < RESULT/RESULTS.tsv) - 1)) (24 with the defaults)"
[ -f RESULT/VERDICT.txt ] && cat RESULT/VERDICT.txt
echo "log (last 4):"; tail -n 4 run.log 2>/dev/null
