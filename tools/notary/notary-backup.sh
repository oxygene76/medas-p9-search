#!/usr/bin/env bash
# Backup of a notary manifest with everything it lists, encrypted, to OneDrive and a USB drive. No push.
#   bash runs/notary/notary-backup.sh NAME FINGERPRINT USB_DIR
#   NAME         a3, e2, e3, e4, or e3-20261103 / e3-20261102 (the replaced drafts of entry 3)
#   FINGERPRINT  the full fingerprint (40 hex digits) of the backup key; its public key must be in the keyring
#   USB_DIR      a directory on the USB drive (must exist)
# Steps: the manifest's sha256; the set (manifest.py archive of the manifest's own commit, a git bundle of the
# manifest's commits, for e2 the WH runs, the spec, SHA256SUMS); the set restored into a temporary directory and
# verified there (detached worktrees at the manifest's commits); encrypted to FINGERPRINT (gpg --list-packets checks
# the recipient); copied to OneDrive and USB_DIR with sha256 checks; the plain set deleted.
set -euo pipefail
. "$(dirname "$0")/notary-lib.sh"
[ $# = 3 ] || die "usage: $0 NAME FINGERPRINT USB_DIR"
NAME=$1 FPR=$2 USB=$3
manifest_of "$NAME"
check_recipient "$FPR"
[ -d "$USB" ] || die "USB directory $USB does not exist"
[ -d "$ONEDRIVE_DIR" ] || die "OneDrive directory $ONEDRIVE_DIR does not exist"
[ "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" = "$MANIFEST_SHA" ] || die "$MANIFEST is not $MANIFEST_SHA"
say "manifest $NAME: $MANIFEST_SHA"

STAMP=$(date +%F_%H%M)
SET=$BACKUP_DIR/p9-$NAME-$STAMP
TMP=$(mktemp -d)
REFS=()
COMPLETE=0
cleanup() {
  [ "$COMPLETE" = 1 ] || { rm -rf "$SET"; rm -f "${OUT:-}"; echo "STOP: nothing kept (no plain set, no partial .gpg)" >&2; }
  for ref in "${REFS[@]}"; do git -C "$GIT_REPO" update-ref -d "$ref" 2>/dev/null || true; done
  [ -d "$TMP/tool" ] && git -C "$GIT_REPO" worktree remove --force "$TMP/tool" 2>/dev/null || true
  git -C "$GIT_REPO" worktree prune
  rm -rf "$TMP"
}
trap cleanup EXIT
mkdir "$SET"

# manifest.py of the manifest's own commit of medas-p9-search (not the working tree)
PCOMMIT=$(manifest_repos "$MANIFEST" | sed -n 's/^medas-p9-search=//p')
git -C "$GIT_REPO" worktree add -q --detach "$TMP/tool" "$PCOMMIT"
ARGS=()
while read -r line; do ARGS+=(--repo "${line%%=*}=$REPOS_DIR/${line%%=*}"); done < <(manifest_repos "$MANIFEST")
python3 -I "$TMP/tool/tools/manifest.py" archive "$MANIFEST" "$SET/p9-$NAME-files.tar" "${ARGS[@]}"

# git bundle of exactly the manifest's commits: those of its repositories and those of files listed at another commit
# (temporary refs, removed afterwards)
while read -r ref c; do
  git -C "$GIT_REPO" update-ref "$ref" "$c"
  REFS+=("$ref")
done < <(bundle_refs "$MANIFEST" "$NAME")
git -C "$GIT_REPO" bundle create "$SET/p9-$NAME-git.bundle" "${REFS[@]}" 2> /dev/null
git -C "$GIT_REPO" bundle verify "$SET/p9-$NAME-git.bundle" > /dev/null 2>&1 || die "bundle does not verify"

if [ "$WH" = 1 ]; then
  tar cf "$SET/p9-$NAME-wh-runs.tar" -C "$REPOS_DIR/medas-p9-search-bb2021" runs/equiv/wh
fi
cp "$SPEC" "$SET/"
( cd "$SET" && sha256sum ./* > SHA256SUMS )

say "restore and verify the set before encrypting it"
verify_set "$SET" "$TMP/restore" "$NAME"

say "encrypt to $FPR"
OUT=$BACKUP_DIR/p9-$NAME-$STAMP.tar.gpg
tar cf - -C "$BACKUP_DIR" "p9-$NAME-$STAMP" | "${GPG[@]}" --trust-model always --cipher-algo AES256 --encrypt --recipient "$FPR" -o "$OUT"
check_packets "$OUT"
copy_checked "$OUT" "$ONEDRIVE_DIR"
copy_checked "$OUT" "$USB"
rm -rf "$SET"
COMPLETE=1
say "done: $OUT ($(du -h "$OUT" | cut -f1)), on OneDrive and $USB; the plain set is deleted"
