#!/bin/sh
# Builds build/p9cpu2-<commit>.tar.gz: the CPU-2 measurement (cpu2/README.txt) with the jobs gpu-v5-4k-1m,
# gpu-v5-64k-1m and cpu-merc-4k-1m of the speed package (SPEED, their expected result hashes included) and the
# binaries of the production package (PROD, checked by sha256; the same as in the speed package).
#   commit, then: tools/make_cpu2_package.sh
set -eu
cd "$(dirname "$0")/.."
REV=$(git rev-parse --short HEAD)
[ -z "$(git status --porcelain --untracked-files=no -- cpu2 tools/make_cpu2_package.sh)" ] || { echo "commit cpu2/ first" >&2; exit 1; }
PROD=${PROD:-build/p9prod-9a084ed}
SPEED=${SPEED:-build/p9speed-12b5888}
for f in p9gpu p9sim; do
  [ "$(sha256sum "$PROD/bin/$f" | cut -d' ' -f1)" = "$(cut -d' ' -f1 "$PROD/bin/SHA256-$f")" ] || { echo "$PROD/bin/$f does not match its sha256" >&2; exit 1; }
  [ "$(sha256sum "$SPEED/bin/$f" | cut -d' ' -f1)" = "$(sha256sum "$PROD/bin/$f" | cut -d' ' -f1)" ] || { echo "$f differs between $SPEED and $PROD" >&2; exit 1; }
done
out=build/p9cpu2-$REV
rm -rf "$out" && mkdir -p "$out/bin" "$out/jobs"
cp cpu2/measure.sh cpu2/start.sh cpu2/stop.sh cpu2/status.sh cpu2/README.txt "$out/"
cp "$PROD/bin/p9gpu" "$PROD/bin/p9sim" "$PROD/bin/SHA256-p9gpu" "$PROD/bin/SHA256-p9sim" "$out/bin/"
for j in gpu-v5-4k-1m gpu-v5-64k-1m cpu-merc-4k-1m; do
  mkdir -p "$out/jobs/$j"
  cp "$SPEED/jobs/$j/input.sa" "$SPEED/jobs/$j/run.env" "$SPEED/jobs/$j/EXPECTED" "$SPEED/jobs/$j/job.json" "$out/jobs/$j/"
  sha256sum "$SPEED/jobs/$j/input.sa" | cut -d' ' -f1 > "$out/jobs/$j/INPUT-SHA256"
done
echo "$REV ($(git log -1 --format=%cs))" > "$out/PACKAGE-VERSION"
tar --sort=name --owner=0 --group=0 --numeric-owner -C build -czf "build/p9cpu2-$REV.tar.gz" "p9cpu2-$REV"
( cd build && sha256sum "p9cpu2-$REV.tar.gz" > "p9cpu2-$REV.tar.gz.sha256" )
cat "build/p9cpu2-$REV.tar.gz.sha256"
