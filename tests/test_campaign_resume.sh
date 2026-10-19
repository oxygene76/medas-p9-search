#!/bin/sh
# A campaign interrupted in the middle of a segment and started again gives the
# same bits as one without interruption (tools/campaign.py: finished segments
# are kept, the interrupted one is made again). Run by `make test-resume`
# (needs a committed tree: the jobs name the commit; P9SIM built at HEAD).
set -eu
cd "$(dirname "$0")/.."
P9SIM=${P9SIM:-build/test/p9sim}
PY=${PY:-build/venv/bin/python}
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
args() { echo "--root $T/$1 --chains 1 --n-tp 500 --segment 2e5 --snap-every 1e5 --t-end 8e5 --deadline 2099-01-01T00:00 --program p9sim --p9sim $P9SIM"; }
$PY -I tools/campaign.py $(args a) >/dev/null 2>&1
# b: stopped while seg002 runs, then started again
set -m  # job control: the background job gets its own process group (campaign, p9job, p9sim)
$PY -I tools/campaign.py $(args b) >/dev/null 2>&1 &
pid=$!
set +m
until [ -s "$T/b/chain00/seg002/output.sa" ]; do sleep 0.1; done
sleep 0.2
kill -TERM -- "-$pid"
wait "$pid" 2>/dev/null || true
[ -f "$T/b/chain00/seg002/result.json" ] && { echo "seg002 finished before the stop: rerun the test"; exit 2; }
$PY -I tools/campaign.py $(args b) >/dev/null 2>&1
ls -d "$T"/b/chain00/seg002.interrupted-* >/dev/null || { echo "FAIL: no interrupted segment kept aside"; exit 1; }
fail=0
for k in 000 001 002 003; do
  ha=$($PY -I -c "import json,sys;print(json.load(open(sys.argv[1]))['result_sha256'])" "$T/a/chain00/seg$k/result.json")
  hb=$($PY -I -c "import json,sys;print(json.load(open(sys.argv[1]))['result_sha256'])" "$T/b/chain00/seg$k/result.json")
  [ "$ha" = "$hb" ] && echo "seg$k same $ha" || { echo "FAIL seg$k: $ha / $hb"; fail=1; }
done
[ ! -d "$T/a/chain00/seg004" ] && [ ! -d "$T/b/chain00/seg004" ] || { echo "FAIL: --t-end not respected"; fail=1; }
grep -h "resumes at seg002\\|was interrupted" "$T/b/campaign.log"
[ $fail = 0 ] && echo "test_campaign_resume: ok"
exit $fail
