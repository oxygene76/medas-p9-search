#!/usr/bin/env bash
# Shared functions of notary-backup.sh, notary-restore-check.sh and notary-receipt-backup.sh (sourced, not run).
# Versioned in tools/notary/; runs/notary/ (not in git, it holds the manifests) has symlinks to the scripts, so they are
# called as before (bash runs/notary/notary-....sh). Machine-specific settings, such as the OneDrive folder, are in
# runs/notary/local.env (not in git), e.g. ONEDRIVE_DIR="/mnt/c/Users/.../OneDrive - .../Backup".
# Overridable for tests: REPOS_DIR, BACKUP_DIR, ONEDRIVE_DIR, GNUPGHOME.

REPOS_DIR=${REPOS_DIR:-$HOME/dev/medas}
NOTARY_DIR=$REPOS_DIR/medas-p9-search/runs/notary
if [ -z "${ONEDRIVE_DIR:-}" ] && [ -f "$NOTARY_DIR/local.env" ]; then
  # shellcheck source=/dev/null
  . "$NOTARY_DIR/local.env"
fi
BACKUP_DIR=${BACKUP_DIR:-$HOME/backups}
ONEDRIVE_DIR=${ONEDRIVE_DIR:-"(ONEDRIVE_DIR not set: runs/notary/local.env)"}
GIT_REPO=$REPOS_DIR/medas-p9-search            # the three worktrees share this repository
GPG=(gpg --batch --no-tty --yes)

die() { echo "STOP: $*" >&2; exit 1; }
say() { echo "== $*"; }

# the manifests that can be backed up: name -> manifest file, spec file, expected repository commits, WH data
manifest_of() {
  case "$1" in
    a3) MANIFEST=$NOTARY_DIR/manifest-a3-validation-status-20261021.json; SPEC=$NOTARY_DIR/spec-a3-validation-status.json
        MANIFEST_SHA=a5389a46eaaedd46aa2ad9ab5765a822ae785f076f26398c66d01b45269240c8
        EXPECT="medas-p9-search=573aca883a5ad6d010d1d29a05c433d74a34f295 medas-p9-search-bb2021=c2eef152a2bf2f62be01b5f536d6f553887e63b9"
        WH=0 ;;
    e2) MANIFEST=$NOTARY_DIR/manifest-e2-equivalence-20261023.json; SPEC=$NOTARY_DIR/spec-e2-equivalence-20261023.json
        MANIFEST_SHA=89ddbf2fb75c0c1e38f571a09a17658f4536592c50fe34c936a670a99f8a227e
        EXPECT="medas-p9-search=c45833a6e5ec11c26ee51b4e50ddd5b1adbab84a medas-p9-search-bb2021=69b84122c16f0b91fe14207ea32c742bbdd40942 medas-p9-search-equiv=47c7381774e2d1b7edd91ff4eaa9563bfb2fb8c7"
        WH=1 ;;
    e3) MANIFEST=$NOTARY_DIR/manifest-e3-production-20261103.json; SPEC=$NOTARY_DIR/spec-e3-production-20261103.json
        MANIFEST_SHA=9ade41f9bbd0dffbf89b1c693ec08459ef7d85a82e261a7fd1474436a20bb212
        EXPECT="medas-p9-search=080a54fae9c3f7526b98b19455e8cedf9c4f2107 medas-p9-search-bb2021=f82c10d4739b6cd4f4d0d36ab162b5b02d07d866 medas-p9-search-equiv=cf41eedaa7fc25aa13302159e61b448ff528958a"
        WH=0 ;;
    # the draft of entry 3 of 2026-11-02, replaced on 2026-11-03 before it was entered (for a backup made of it)
    e3-20261102) MANIFEST=$NOTARY_DIR/manifest-e3-production-20261102.json; SPEC=$NOTARY_DIR/spec-e3-production-20261102.json
        MANIFEST_SHA=7ecd6320435a1dd13fc592e900b803c3cb166ff4eb5e57fcdfed693b2576ca15
        EXPECT="medas-p9-search=8debfcf6c8e0e85f1f1e83e9b4d4b456d7bcbf67 medas-p9-search-bb2021=32defaf0e413ca14778391fd3baaec55967e8105"
        WH=0 ;;
    *) die "unknown manifest name '$1' (a3, e2, e3 or e3-20261102)" ;;
  esac
}

# repositories and commits as the manifest names them: "name=commit" per line
manifest_repos() {
  python3 -I -c "import json, sys
for n, r in sorted(json.load(open(sys.argv[1]))['repositories'].items()): print(n + '=' + r['commit'])" "$1"
}

# the full fingerprint of a primary key in the keyring that can encrypt, not revoked or expired;
# sets ENC_KEYIDS (long key ids of the keys that can encrypt)
check_recipient() {
  local fpr=$1 out
  [[ $fpr =~ ^[0-9A-F]{40}$ ]] || die "recipient must be the full 40-digit fingerprint in capitals, got '$fpr'"
  out=$("${GPG[@]}" --with-colons --fingerprint --list-keys "$fpr" 2>/dev/null) || die "no public key $fpr in the keyring"
  [ "$(awk -F: '$1=="pub"' <<<"$out" | wc -l)" = 1 ] || die "$fpr does not name exactly one key"
  [ "$(awk -F: '$1=="fpr"{print $10; exit}' <<<"$out")" = "$fpr" ] || die "$fpr is not the fingerprint of the primary key"
  case "$(awk -F: '$1=="pub"{print $2}' <<<"$out")" in r|e|d|i) die "key $fpr is revoked, expired, disabled or invalid" ;; esac
  ENC_KEYIDS=$(awk -F: '($1=="pub" || $1=="sub") && $12 ~ /e/ && $2 !~ /[redi]/ {print $5}' <<<"$out")
  [ -n "$ENC_KEYIDS" ] || die "key $fpr has no usable encryption key"
}

# after encrypting: every recipient of the file is one of ENC_KEYIDS, and there is at least one
check_packets() {
  local f=$1 ids
  ids=$("${GPG[@]}" --list-only --list-packets "$f" 2>/dev/null | sed -n 's/^:pubkey enc packet:.* keyid \([0-9A-F]*\).*/\1/p' || true)
  [ -n "$ids" ] || die "$f: no recipient found by gpg --list-packets"
  for id in $ids; do grep -qx "$id" <<<"$ENC_KEYIDS" || die "$f: encrypted to $id, not to the expected key"; done
  say "encrypted to $(echo $ids) (key $FPR): ok"
}

encrypt() {  # in out
  "${GPG[@]}" --trust-model always --cipher-algo AES256 --encrypt --recipient "$FPR" -o "$2" "$1"
  check_packets "$2"
}

copy_checked() {  # file dir
  local f=$1 d=$2
  [ -d "$d" ] || die "target directory $d does not exist"
  ( cd "$(dirname "$f")" && sha256sum "$(basename "$f")" > "$(basename "$f").sha256" )
  cp "$f" "$f.sha256" "$d/"
  ( cd "$d" && sha256sum -c --quiet "$(basename "$f").sha256" ) || die "copy to $d does not match"
  say "copied and checked: $d/$(basename "$f")"
}

# restore a backup set (directory with SHA256SUMS, p9-NAME-files.tar, p9-NAME-git.bundle [, p9-NAME-wh-runs.tar])
# into WORK and verify it: the repositories as detached worktrees at the manifest's commits (not branch tips),
# manifest.py of the manifest's own commit of medas-p9-search, every listed file, and for e2 the WH list
verify_set() {
  local set=$1 work=$2 name=$3 m repos line r c first=""
  manifest_of "$name"
  ( cd "$set" && sha256sum -c --quiet SHA256SUMS ) || die "$set: SHA256SUMS do not match"
  mkdir -p "$work"
  tar xf "$set/p9-$name-files.tar" -C "$work" "$(basename "$MANIFEST")"    # first only the manifest
  m=$work/$(basename "$MANIFEST")
  [ "$(sha256sum "$m" | cut -d' ' -f1)" = "$MANIFEST_SHA" ] || die "manifest in the set is not $MANIFEST_SHA"
  repos=$(manifest_repos "$m")
  [ "$(echo $repos)" = "$EXPECT" ] || die "manifest names other commits: $(echo $repos)"
  git -c init.defaultBranch=main init -q "$work/.repo"
  git -C "$work/.repo" fetch -q "$set/p9-$name-git.bundle" "refs/notary-backup/*:refs/notary-backup/*" || die "bundle cannot be fetched"
  for line in $repos; do
    r=${line%%=*}; c=${line#*=}
    git -C "$work/.repo" worktree add -q --detach "$work/$r" "$c" || die "commit $c of $r not in the bundle"
    [ -z "$(git -C "$work/$r" status --porcelain)" ] || die "$work/$r is not clean"
  done
  tar xf "$set/p9-$name-files.tar" -C "$work" --exclude="$(basename "$MANIFEST")"   # REPO/PATH of the files without git
  local args=()
  for line in $repos; do args+=(--repo "${line%%=*}=$work/${line%%=*}"); done
  python3 -I "$work/medas-p9-search/tools/manifest.py" verify "$m" "${args[@]}" | tail -n 1 | tee "$work/verify.txt"
  grep -q "^\([0-9]*\) of \1 files match$" "$work/verify.txt" || die "verify: not all files match"
  if [ "$WH" = 1 ]; then
    tar xf "$set/p9-$name-wh-runs.tar" -C "$work/medas-p9-search-bb2021"
    ( cd "$work/medas-p9-search-bb2021" && grep -v '^#' ../medas-p9-search/docs/equivalence-wh-sha256.txt | sha256sum -c --quiet ) \
      || die "WH files do not match docs/equivalence-wh-sha256.txt"
    say "WH: $(grep -vc '^#' "$work/medas-p9-search/docs/equivalence-wh-sha256.txt") files match the list"
  fi
}
