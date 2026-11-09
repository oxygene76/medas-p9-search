#!/usr/bin/env bash
# Backup of a result archive (e.g. the results of a run, before its evaluation): encrypted to the backup key, to
# OneDrive and the USB drive, each copy checked by sha256. The plain archive is kept.
#   bash runs/notary/notary-archive-backup.sh NAME FINGERPRINT USB_DIR ARCHIVE [EXPECTED_SHA256]
#   NAME             a short name for the file, e.g. prod for the production run
#   FINGERPRINT      the full fingerprint (40 hex digits) of the backup key (public key in the keyring)
#   USB_DIR          a directory on the USB drive (must exist)
#   ARCHIVE          the archive (.tar.gz)
#   EXPECTED_SHA256  optional: its sha256 as reported; the backup stops if it differs
# Written: ~/backups/p9-NAME-<date>.tar.gz.gpg, and next to it p9-NAME-<date>.tar.gz.gpg.plain-sha256 (the sha256 and
# name of the plain archive, which notary-restore-check.sh compares after decrypting), both also on OneDrive and the
# USB drive.
set -euo pipefail
. "$(dirname "$0")/notary-lib.sh"
[ $# = 4 ] || [ $# = 5 ] || die "usage: $0 NAME FINGERPRINT USB_DIR ARCHIVE [EXPECTED_SHA256]"
NAME=$1 FPR=$2 USB=$3 ARCHIVE=$4 WANT=${5:-}
[[ $NAME =~ ^[a-z0-9]+$ ]] || die "NAME: letters and digits only"
[ -f "$ARCHIVE" ] || die "$ARCHIVE not found"
[[ $ARCHIVE == *.tar.gz ]] || die "$ARCHIVE: a .tar.gz archive is expected"
[ -d "$USB" ] || die "USB directory $USB does not exist"
[ -d "$ONEDRIVE_DIR" ] || die "OneDrive directory $ONEDRIVE_DIR does not exist"
HAVE=$(sha256sum "$ARCHIVE" | cut -d' ' -f1)
[ -z "$WANT" ] || [ "$HAVE" = "$WANT" ] || die "$ARCHIVE has sha256 $HAVE, not $WANT"
say "archive $(basename "$ARCHIVE"): sha256 $HAVE"
check_recipient "$FPR"
mkdir -p "$BACKUP_DIR"
OUT=$BACKUP_DIR/p9-$NAME-$(date +%F_%H%M).tar.gz.gpg
trap 'rm -f -- "$OUT.part"' EXIT
encrypt "$ARCHIVE" "$OUT.part"
mv "$OUT.part" "$OUT"
printf '%s  %s\n' "$HAVE" "$(basename "$ARCHIVE")" > "$OUT.plain-sha256"
for d in "$ONEDRIVE_DIR" "$USB"; do
  copy_checked "$OUT" "$d"
  cp "$OUT.plain-sha256" "$d/" && cmp -s "$OUT.plain-sha256" "$d/$(basename "$OUT").plain-sha256" || die "copy of the plain sha256 to $d failed"
done
say "done: $OUT ($(du -h "$OUT" | cut -f1)) on OneDrive and $USB; the plain archive $ARCHIVE is kept"
say "check it: bash runs/notary/notary-restore-check.sh $USB/$(basename "$OUT") <key file on the USB drive>"
