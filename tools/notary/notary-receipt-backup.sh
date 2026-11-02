#!/usr/bin/env bash
# Backup of a notary receipt (it holds the secret salt): encrypted to the backup key, to OneDrive and the USB drive,
# then the plain receipt is deleted. For any entry, e.g. the receipt of (a3) or of (e2).
#   bash runs/notary/notary-receipt-backup.sh NAME FINGERPRINT USB_DIR RECEIPT
#   NAME         a short name for the file, e.g. a3 or e2
#   FINGERPRINT  the full fingerprint (40 hex digits) of the backup key (public key in the keyring)
#   USB_DIR      a directory on the USB drive (must exist)
#   RECEIPT      the receipt file saved by the web application
# The plain receipt is removed with rm; on NTFS or an SSD (e.g. the Windows download folder) that does not wipe
# the data blocks. Keep a copy of the receipt until the encrypted one has been checked with notary-restore-check.sh
# (it decrypts a receipt .json.gpg with the private key from the USB drive and checks it is a JSON receipt).
set -euo pipefail
. "$(dirname "$0")/notary-lib.sh"
[ $# = 4 ] || die "usage: $0 NAME FINGERPRINT USB_DIR RECEIPT"
NAME=$1 FPR=$2 USB=$3 RECEIPT=$4
[[ $NAME =~ ^[a-z0-9]+$ ]] || die "NAME: letters and digits only"
[ -f "$RECEIPT" ] || die "$RECEIPT not found"
[ -d "$USB" ] || die "USB directory $USB does not exist"
[ -d "$ONEDRIVE_DIR" ] || die "OneDrive directory $ONEDRIVE_DIR does not exist"
python3 -I -c 'import json, sys; json.load(open(sys.argv[1]))' "$RECEIPT" 2>/dev/null || die "$RECEIPT is not a JSON receipt"
check_recipient "$FPR"
mkdir -p "$BACKUP_DIR"
OUT=$BACKUP_DIR/p9-$NAME-receipt-$(date +%F_%H%M).json.gpg
encrypt "$RECEIPT" "$OUT"
copy_checked "$OUT" "$ONEDRIVE_DIR"
copy_checked "$OUT" "$USB"
rm -f -- "$RECEIPT"
say "done: $OUT on OneDrive and $USB; plain receipt $RECEIPT deleted"
