#!/usr/bin/env bash
# The check of the publication in a fresh clone (docs/publication-checklist.md, point E): a clone that holds only the
# refs to be published, every manifest verified in it, and publish_scan over every file version of it.
#   bash tools/notary/fresh_clone_check.sh OUT_DIR REF [REF ...] -- ENTRY=MANIFEST [ENTRY=MANIFEST ...]
#   OUT_DIR   a new, empty directory (the clone, the worktrees and the report go there; delete it afterwards)
#   REF       the refs to publish: main and the tips of docs/publication-commits.md (commits or tags)
#   MANIFEST  the manifests of the entries on chain (runs/notary/manifest-*.json)
# The files without git of each manifest come from manifest.py archive of the local repositories, as the reveal
# archive will hold them. The tools (manifest.py, publish_scan.py) are those of the working tree, not of the clone.
# Read only for the repository: temporary refs refs/fresh-check/* are removed at the end. Nothing is pushed.
set -euo pipefail
here=$(cd "$(dirname "$0")/../.." && pwd)
REPOS_DIR=${REPOS_DIR:-$(dirname "$here")}
PY=${PY:-$here/build/venv/bin/python}
out=$1; shift
refs=(); while [ "$1" != "--" ]; do refs+=("$1"); shift; done; shift
[ ! -e "$out" ] || { echo "STOP: $out exists"; exit 1; }
mkdir -p "$out"; out=$(cd "$out" && pwd)
cleanup() { git -C "$here" for-each-ref --format='%(refname)' refs/fresh-check/ | while read -r r; do git -C "$here" update-ref -d "$r"; done; }
trap cleanup EXIT
i=0; for r in "${refs[@]}"; do git -C "$here" update-ref "refs/fresh-check/r$i" "$(git -C "$here" rev-parse "$r^{commit}")"; i=$((i + 1)); done
git -C "$here" bundle create "$out/published.bundle" $(git -C "$here" for-each-ref --format='%(refname)' refs/fresh-check/) 2>/dev/null
git -c init.defaultBranch=main init -q "$out/clone"
git -C "$out/clone" fetch -q "$out/published.bundle" 'refs/fresh-check/*:refs/tags/fresh-*'
echo "== clone: $(git -C "$out/clone" rev-list --all | wc -l) commits from ${#refs[@]} refs" | tee "$out/report.txt"
total=0; bad=0
for spec in "$@"; do
  entry=${spec%%=*}; m=$(cd "$(dirname "${spec#*=}")" && pwd)/$(basename "${spec#*=}")
  w="$out/$entry"; mkdir -p "$w"; args=()
  while read -r line; do
    repo=${line%%=*}; commit=${line#*=}
    if git -C "$out/clone" cat-file -e "$commit^{commit}" 2>/dev/null; then
      git -C "$out/clone" worktree add -q --detach "$w/$repo" "$commit"
    else
      echo "   $entry: repository commit $commit of $repo is not in the clone" | tee -a "$out/report.txt"; mkdir -p "$w/$repo"
    fi
    args+=(--repo "$repo=$w/$repo")
  done < <("$PY" -I -c "import json, sys
for n, r in sorted(json.load(open(sys.argv[1]))['repositories'].items()): print(n + '=' + r['commit'])" "$m")
  locargs=(); while read -r repo; do locargs+=(--repo "$repo=$REPOS_DIR/$repo"); done < <("$PY" -I -c "import json, sys
print('\n'.join(sorted(json.load(open(sys.argv[1]))['repositories'])))" "$m")
  "$PY" -I "$here/tools/manifest.py" archive "$m" "$w/reveal.tar" "${locargs[@]}" > /dev/null
  tar -xf "$w/reveal.tar" -C "$w" --exclude="$(basename "$m")"
  res=$("$PY" -I "$here/tools/manifest.py" verify "$m" "${args[@]}" || true)
  echo "$res" | grep -E 'COMMIT MISSING|MISSING|DIFFERENT|commit missing' | sed "s/^/   $entry: /" | tee -a "$out/report.txt" || true
  last=$(echo "$res" | tail -n 1); echo "== $entry ($(sha256sum "$m" | cut -c1-12)…): $last" | tee -a "$out/report.txt"
  total=$((total + 1)); echo "$last" | grep -qE '^([0-9]+) of \1 files match$' || bad=$((bad + 1))
done
echo "== publish_scan over every file version of the clone:" | tee -a "$out/report.txt"
"$PY" -I "$here/tools/publish_scan.py" --blobs $(git -C "$out/clone" for-each-ref --format='%(refname)' refs/tags/) --repo "$out/clone" \
  | tail -n 1 | tee -a "$out/report.txt"
echo "== manifests: $((total - bad)) of $total complete" | tee -a "$out/report.txt"
[ "$bad" = 0 ]
