#!/bin/sh
# CPU half of runs/speed/run.sh, restarted: the first start (20:31) was stopped after 3 minutes so that the notebook
# could cool down (GPU half done before). Waits PAUSE_S seconds, then the six single-core runs at once, as in run.sh.
cd "$(dirname "$0")/../.."
echo $$ > runs/pids/speed.pid
trap 'rm -f runs/pids/speed.pid' EXIT
echo "== cpu half stopped at 20:34 for cooling; restart after ${PAUSE_S:-1800} s pause" >> runs/speed/run.log
sleep "${PAUSE_S:-1800}"
echo "== cpu start $(date -Iseconds)" >> runs/speed/run.log
for j in whfast-cpu merc-cpu; do
  for k in 1 2 3; do
    rm -rf runs/speed/$j-r$k
    cp -a runs/speed/$j runs/speed/$j-r$k
    build/venv/bin/python -I tools/p9job.py run runs/speed/$j-r$k --p9sim build/equiv-bin/p9sim --any-version > /dev/null 2>&1 &
  done
done
wait
for j in whfast-cpu merc-cpu; do
  for k in 1 2 3; do
    echo "$j $k $(python3 -I -c "import json; r=json.load(open('runs/speed/$j-r$k/result.json')); print(r['wall_s'], r['result_sha256'][:16])")" >> runs/speed/run.log
  done
done
echo "== end $(date -Iseconds)" >> runs/speed/run.log
