#!/bin/sh
# MEDAS p9-search, reproduction: state (read only).
cd "$(dirname "$0")"
if [ -f run.pid ] && kill -0 "$(cat run.pid)" 2>/dev/null; then echo "running (pid $(cat run.pid))"; else echo "not running"; fi
[ -f RESULT/REPRO.tsv ] && { echo "segments done: $(($(wc -l < RESULT/REPRO.tsv) - 1)) of $(grep -vc "^#" TARGETS)"; column -t -s "$(printf "\t")" RESULT/REPRO.tsv 2>/dev/null || cat RESULT/REPRO.tsv; }
[ -f RESULT/VERDICT.txt ] && cat RESULT/VERDICT.txt
echo "log (last 4):"; tail -n 4 run.log 2>/dev/null
