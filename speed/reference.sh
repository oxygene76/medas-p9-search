#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Reference results of the speed jobs on the reference machine (the notebook), with the binaries of
# p9prod-9a084ed (build/equiv-bin): the 1-Myr jobs are run once (result.json, run.env); for the four 10-Myr jobs
# the results of the notebook comparison (runs/speed) are the reference and only run.env is written.
# GPU jobs one after the other, the two CPU jobs at the same time: at most 3 cores.
cd "$(dirname "$0")/.."
J=runs/speed2/jobs
echo $$ > runs/pids/speed2-ref.pid
trap 'rm -f runs/pids/speed2-ref.pid' EXIT
run() { # job program
	CAPTURE_REAL=$PWD/build/equiv-bin/$2 nice -n 10 build/venv/bin/python -I tools/p9job.py run "$J/$1" --p9sim speed/capture.sh --any-version > "$J/$1/ref.log" 2>&1
	echo "$1 $(python3 -I -c "import json; r=json.load(open('$J/$1/result.json')); print(r['wall_s'], r['result_sha256'])" 2>/dev/null || echo FAILED) $(date +%T)"
}
echo "== start $(date -Iseconds)"
for j in cpu-whfast-4k-10m:p9sim cpu-merc-4k-10m:p9sim gpu-wh-4k-10m:p9gpu gpu-v5-4k-10m:p9gpu; do
	CAPTURE_ONLY=1 CAPTURE_REAL=$PWD/build/equiv-bin/${j#*:} build/venv/bin/python -I tools/p9job.py run "$J/${j%%:*}" --p9sim speed/capture.sh --any-version > /dev/null 2>&1
	echo "${j%%:*} run.env $(wc -l < "$J/${j%%:*}/run.env") lines"
done
run cpu-whfast-4k-1m p9sim &
run cpu-merc-4k-1m p9sim &
for n in 4k 16k 64k 256k; do run gpu-wh-$n-1m p9gpu; run gpu-v5-$n-1m p9gpu; done
wait
echo "== end $(date -Iseconds)"
