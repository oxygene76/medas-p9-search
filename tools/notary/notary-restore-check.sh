#!/usr/bin/env bash
# Checks that an encrypted backup of notary-backup.sh can be restored, with the private key from the USB drive.
#   bash runs/notary/notary-restore-check.sh ENCRYPTED_FILE SECRET_KEY_FILE
#   ENCRYPTED_FILE   p9-NAME-<date>.tar.gpg (e.g. the copy on the USB drive), or a receipt p9-NAME-receipt-<date>.json.gpg
#   SECRET_KEY_FILE  the exported private key on the USB drive (gpg --export-secret-keys)
# The key is imported into a temporary GNUPGHOME, which is deleted at the end (also on errors); the normal keyring
# is not touched. The passphrase of the key is read by this script from the terminal (without echo; empty if the
# key has none) and handed to gpg only through a pipe on file descriptor 3, never as a file or an argument: in the
# WSL terminal gpg's own loopback prompt loses characters when typing fast ("Bad passphrase" with the right one).
# Up to 3 attempts on "Bad passphrase", then STOP.
# Then: decrypt into a temporary directory, SHA256SUMS, detached worktrees at the manifest's commits from the
# bundle, every listed file with manifest.py of the manifest's own commit, for e2 the WH list. Nothing is kept.
set -euo pipefail
. "$(dirname "$0")/notary-lib.sh"
[ $# = 2 ] || die "usage: $0 ENCRYPTED_FILE SECRET_KEY_FILE"
ENC=$1 KEY=$2
[ -f "$ENC" ] || die "$ENC not found"
[ -f "$KEY" ] || die "$KEY not found"
[ -f "$ENC.sha256" ] && { ( cd "$(dirname "$ENC")" && sha256sum -c --quiet "$(basename "$ENC").sha256" ) || die "$ENC does not match its .sha256"; }
TMP=$(mktemp -d)
GH=$(mktemp -d)
chmod 700 "$GH"
PP=
cleanup() {
  unset PP
  gpgconf --homedir "$GH" --kill all 2>/dev/null || true
  rm -rf "$GH" "$TMP"
}
trap cleanup EXIT
# every gpg call gets /dev/null as standard input: with the terminal there, the first unlock of the imported key
# fails (tested 2026-11-01 in a pseudo-terminal: "Bad passphrase" with the right passphrase on every attempt)
gpg --homedir "$GH" --batch --no-tty --import "$KEY" < /dev/null 2> /dev/null || die "import of $KEY failed"
[ -n "$(gpg --homedir "$GH" --batch --no-tty --list-secret-keys < /dev/null 2>/dev/null)" ] || die "$KEY contains no private key"
say "key imported into a temporary GNUPGHOME"
# warm up the agent before the first unlock, and wait: in the WSL terminal the first 1-2 attempts right after the
# import failed with "Bad passphrase" although the passphrase was right (real run of 2026-11-01)
gpg-connect-agent --homedir "$GH" 'GETINFO version' /bye < /dev/null > /dev/null 2>&1 || true
sleep 2

# A test message to the imported key: decrypting it first unlocks the key once with the passphrase, its result is
# thrown away. In the WSL terminal the first unlock right after the import failed with "Bad passphrase" although the
# passphrase was right (2026-11-01 and 2026-11-02, both receipts), even with the agent warmed up.
KEYFPR=$(gpg --homedir "$GH" --batch --no-tty --with-colons --list-secret-keys < /dev/null 2>/dev/null | awk -F: '/^fpr/ {print $10; exit}')
[ -n "$KEYFPR" ] || die "no fingerprint of the imported key"
printf 'notary-restore-check test message\n' | gpg --homedir "$GH" --batch --no-tty --yes --trust-model always \
  --encrypt --recipient "$KEYFPR" --output "$TMP/test.gpg" 2> /dev/null || die "could not encrypt a test message to the key"

# try_decrypt IN OUT: one decryption with the passphrase in PP (handed over on file descriptor 3 only)
try_decrypt() {
  gpg --homedir "$GH" --batch --yes --pinentry-mode loopback --passphrase-fd 3 --output "$2" --decrypt "$1" \
    < /dev/null 2> "$TMP/gpg.err" 3< <(printf '%s' "$PP")
}

# try_twice IN OUT: try_decrypt, and on "Bad passphrase" once more after a second, without asking again
try_twice() {
  local t
  for t in 1 2; do
    try_decrypt "$1" "$2" && return 0
    rm -f "$2"
    grep -qi 'bad passphrase' "$TMP/gpg.err" || { cat "$TMP/gpg.err" >&2; die "decryption failed"; }
    [ "$t" = 1 ] && sleep 1
  done
  return 1
}

# decrypt_to OUT: decrypt $ENC to OUT (in $TMP); the passphrase is asked here, up to 3 attempts. Each attempt first
# decrypts the test message (silently twice), then $ENC (silently twice); only then it counts as a bad passphrase.
decrypt_to() {
  local out=$1 n
  for n in 1 2 3; do
    IFS= read -r -s -p "Passphrase (empty if the key has none): " PP < /dev/tty; echo > /dev/tty
    if try_twice "$TMP/test.gpg" "$TMP/test.out" && try_twice "$ENC" "$out"; then
      unset PP
      rm -f "$TMP/test.out"
      return 0
    fi
    unset PP
    echo "bad passphrase (attempt $n of 3)" >&2
  done
  die "bad passphrase 3 times"
}
# a receipt (p9-NAME-receipt-<date>.json.gpg): decrypt into the temporary directory, check it is a JSON receipt, delete it
if [[ $ENC == *.json.gpg ]]; then
  decrypt_to "$TMP/receipt.json"
  python3 -I -c 'import json, sys; d = json.load(open(sys.argv[1])); assert isinstance(d, dict) and d' "$TMP/receipt.json" \
    || die "decrypted file is not a JSON receipt"
  say "receipt $(basename "$ENC"): decrypts with the key, a JSON object with $(python3 -I -c 'import json, sys; print(len(json.load(open(sys.argv[1]))))' "$TMP/receipt.json") fields; deleted again"
  exit 0
fi
# decrypted into the temporary directory first (so a wrong passphrase can be retried), then unpacked there
decrypt_to "$TMP/set.tar"
tar xf "$TMP/set.tar" -C "$TMP" || die "$ENC: the decrypted file is not a tar archive"
rm -f "$TMP/set.tar"
SET=$(find "$TMP" -mindepth 1 -maxdepth 1 -type d -name 'p9-*' | head -n 1)
[ -n "$SET" ] || die "no backup set in $ENC"
NAME=$(basename "$SET" | sed -n 's/^p9-\([a-z0-9]*\)-.*/\1/p')
say "set $(basename "$SET") (manifest $NAME)"
verify_set "$SET" "$TMP/restore" "$NAME"
say "restore check of $(basename "$ENC"): ok; the temporary key and all restored files are deleted"
