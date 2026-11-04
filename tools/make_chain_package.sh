#!/bin/sh
# Builds build/p9chain-<commit>.tar.gz from chain/ (the A100 chain and the run watcher), after its test.
#   commit, then: tools/make_chain_package.sh
set -eu
cd "$(dirname "$0")/.."
REV=$(git rev-parse --short HEAD)
[ -z "$(git status --porcelain --untracked-files=no -- chain tools/make_chain_package.sh)" ] || { echo "commit chain/ first" >&2; exit 1; }
sh chain/test/test-chain.sh > /dev/null || { echo "chain/test/test-chain.sh failed" >&2; exit 1; }
out=build/p9chain-$REV
rm -rf "$out" && mkdir -p "$out/systemd" "$out/test"
cp chain/chain-a100.sh chain/run-watch.sh chain/lib.sh chain/chain.env.example chain/README.txt chain/ANLEITUNG.md "$out/"
cp chain/systemd/* "$out/systemd/"; cp chain/test/test-chain.sh "$out/test/"
echo "$REV ($(git log -1 --format=%cs))" > "$out/PACKAGE-VERSION"
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime="$(git log -1 --format=%cI)" -C build -czf "build/p9chain-$REV.tar.gz" "p9chain-$REV"
( cd build && sha256sum "p9chain-$REV.tar.gz" > "p9chain-$REV.tar.gz.sha256" )
cat "build/p9chain-$REV.tar.gz.sha256"
