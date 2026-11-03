#!/bin/sh
# MEDAS p9-search, paired long runs (seeds 110-112), group V5: stops the check or the jobs (running segments are lost and computed again on the next start).
cd "$(dirname "$0")"
[ -f run.pid ] && kill -0 "$(cat run.pid)" 2>/dev/null || { echo "not running"; exit 0; }
p=$(cat run.pid)
# the run is its own process group when started with setsid (start.sh): stop the whole group (the scripts and the
# running programs, also those under xargs or in a lane), else only the main shell
kill -TERM -"$p" 2>/dev/null || kill -TERM "$p"  # dash knows no "--" for kill
for i in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$p" 2>/dev/null || break; sleep 1; done
kill -0 "$p" 2>/dev/null && { echo "still running after 10 s (pid $p)"; exit 1; }
rm -f run.pid
echo "stopped; sh start.sh resumes (done segments are kept)"
