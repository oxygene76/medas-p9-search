#!/bin/sh
# Speed comparison (public statement): the same 4,000 test bodies (seed 101, Brown & Batygin 2021 configuration),
# dt 0.5 yr, 10 Myr, three repetitions each. (a) p9gpu fixed step on the GPU against REBOUND WHFast on one CPU core,
# (b) p9gpu v5 on the GPU against REBOUND MERCURIUS on one CPU core. Starts after the literature checks (their
# frequency analysis) are done. GPU runs one after the other alone; then the six single-core CPU runs at once, each
# on its own core (24 cores, nothing else running).
cd "$(dirname "$0")/../.."
echo $$ > runs/pids/speed.pid
trap 'rm -f runs/pids/speed.pid' EXIT
until [ -s ../medas-p9-search/runs/litcheck/frequencies.json ]; do sleep 30; done
echo "== start $(date -Iseconds)"
for j in wh-gpu v5-gpu; do
  for k in 1 2 3; do
    build/venv/bin/python -I tools/p9job.py run runs/speed/$j --p9sim build/equiv-bin/p9gpu --any-version --result-name result-$k.json > /dev/null 2>&1
    echo "$j $k $(python3 -I -c "import json; r=json.load(open('runs/speed/$j/result-$k.json')); print(r['wall_s'], r['result_sha256'][:16])") $(date +%T)"
  done
done
for j in whfast-cpu merc-cpu; do
  for k in 1 2 3; do
    cp -a runs/speed/$j runs/speed/$j-r$k
    build/venv/bin/python -I tools/p9job.py run runs/speed/$j-r$k --p9sim build/equiv-bin/p9sim --any-version > /dev/null 2>&1 &
  done
done
wait
for j in whfast-cpu merc-cpu; do
  for k in 1 2 3; do
    echo "$j $k $(python3 -I -c "import json; r=json.load(open('runs/speed/$j-r$k/result.json')); print(r['wall_s'], r['result_sha256'][:16])")"
  done
done
echo "== end $(date -Iseconds)"
