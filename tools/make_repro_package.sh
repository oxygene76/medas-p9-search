#!/bin/sh
# Builds build/p9repro-<commit>.tar.gz from repro/ (reproduction of stored segments; no binaries: it uses the runs' own
# p9gpu after checking its sha256).
#   commit, then: tools/make_repro_package.sh
set -eu
cd "$(dirname "$0")/.."
REV=$(git rev-parse --short HEAD)
[ -z "$(git status --porcelain --untracked-files=no -- repro tools/make_repro_package.sh)" ] || { echo "commit repro/ first" >&2; exit 1; }
out=build/p9repro-$REV
rm -rf "$out" && mkdir -p "$out"
cp repro/repro.sh repro/start.sh repro/stop.sh repro/status.sh repro/README.txt repro/TARGETS "$out/"
echo "$REV ($(git log -1 --format=%cs))" > "$out/PACKAGE-VERSION"
tar --sort=name --owner=0 --group=0 --numeric-owner -C build -czf "build/p9repro-$REV.tar.gz" "p9repro-$REV"
( cd build && sha256sum "p9repro-$REV.tar.gz" > "p9repro-$REV.tar.gz.sha256" )
cat "build/p9repro-$REV.tar.gz.sha256"
