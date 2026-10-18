#!/bin/sh
# Builds the check package for a second machine from the jobs in runs/pkg/
# (control, repro, bench; each with job.json incl. "control" and input.sa):
#   tools/make_check_package.sh  ->  build/p9check-<commit>.tar.gz (+ .sha256)
set -eu
cd "$(dirname "$0")/.."
REV=$(git rev-parse --short HEAD)
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "commit first" >&2; exit 1; }
OUT=build/p9check-$REV
rm -rf "$OUT" && mkdir -p "$OUT/src" "$OUT/third_party-src" "$OUT/jobs"
cp Makefile LICENSE "$OUT/"
cp src/*.c src/*.h "$OUT/src/"
cp check/run-check.sh check/Dockerfile check/README.txt "$OUT/"
cp third_party/README.md "$OUT/third_party-src/README.md"
cp third_party/rebound-5.2.2.tar.gz "$OUT/third_party-src/"
echo "$REV ($(git log -1 --format=%cs))" > "$OUT/PACKAGE-VERSION"
{
  echo "# name t_end snapshots input_sha256 expected_result_sha256 (computed with: see jobs/<name>/job.json, control)"
  for j in control repro bench; do
    mkdir -p "$OUT/jobs/$j"
    cp "runs/pkg/$j/job.json" "runs/pkg/$j/input.sa" "$OUT/jobs/$j/"
    python3 - "runs/pkg/$j/job.json" "$j" <<'PY'
import json, sys
j = json.load(open(sys.argv[1]))
p = j["params"]
print(sys.argv[2], repr(float(p["t_end_yr"])), p["snapshots"], j["input"]["sha256"], j["control"]["expected_result_sha256"])
PY
  done
} > "$OUT/EXPECTED"
tar --sort=name --owner=0 --group=0 --numeric-owner -C build -czf "$OUT.tar.gz" "p9check-$REV"
( cd build && sha256sum "p9check-$REV.tar.gz" > "p9check-$REV.tar.gz.sha256" )
cat "$OUT.tar.gz.sha256"
ls -la "$OUT.tar.gz"
