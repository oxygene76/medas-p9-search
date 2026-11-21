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
    e3) MANIFEST=$NOTARY_DIR/manifest-e3-production-20261104.json; SPEC=$NOTARY_DIR/spec-e3-production-20261104.json
        MANIFEST_SHA=fa4d84fb5619cf7746f26cbfd0d9102a1961db8f26c7fc88e0f0e69208b03c60
        EXPECT="medas-p9-search=730260738c203f99de27f123220431e5eb7d186b medas-p9-search-bb2021=801fb20a295c69edbec34e0461883302e9eb1268 medas-p9-search-equiv=ac47329bb46308b0f05ff7d78cf23353529233dd"
        WH=0 ;;
    e4) MANIFEST=$NOTARY_DIR/manifest-e4-bb2021-v2-20261104.json; SPEC=$NOTARY_DIR/spec-e4-bb2021-v2-20261104.json
        MANIFEST_SHA=5e5829b7461ff56a42518190b0fc2cdbfcdaa695f761b0663dad3c0bf61b22cc
        EXPECT="medas-p9-search=1c5f2ba23d5758a28de47e4384448e4936413482 medas-p9-search-bb2021=801fb20a295c69edbec34e0461883302e9eb1268 medas-p9-search-equiv=5b05cc3c72b0576d3c40581310822964567b0258"
        WH=0 ;;
    e5) MANIFEST=$NOTARY_DIR/manifest-e5-paired-tests-20261106.json; SPEC=$NOTARY_DIR/spec-e5-paired-tests-20261106.json
        MANIFEST_SHA=a3dc42d8fc6b91c98f76effd49cca637a54788e7732b367d1a5f3b5e0aa6b037
        EXPECT="medas-p9-search=e83d9609780b8259afb5e2923141a894c74c5fd9 medas-p9-search-bb2021=d4dadd9263fcdef639b2b3828787f8f2c31aa80f medas-p9-search-equiv=fed221ad835c82b1ca255e268fb51d76d3cbebb4"
        WH=0 ;;
    e6) MANIFEST=$NOTARY_DIR/manifest-e6-bb-a-rin1-20261118.json; SPEC=$NOTARY_DIR/spec-e6-bb-a-rin1-20261118.json
        MANIFEST_SHA=e25436425b6634bf6ca4079644e5e18a6f3cc99b71d505438f00be30e28257c5
        EXPECT="medas-p9-search=f80681f933aa6642bab05d867d85ce446ddcb3ad medas-p9-search-equiv=fed221ad835c82b1ca255e268fb51d76d3cbebb4"
        WH=0 ;;
    e9) MANIFEST=$NOTARY_DIR/manifest-e9-bb-a2-20261121.json; SPEC=$NOTARY_DIR/spec-e9-bb-a2-20261121.json
        MANIFEST_SHA=ee2ff1003c0b37a12381bbf0762179e98646d2f8b54f2eb5a9a00d9842d04be1
        EXPECT="medas-p9-search=0003408b1591464a82733fafe00709f8b000694f"
        WH=0 ;;
    r1) MANIFEST=$NOTARY_DIR/manifest-r1-results-20261110-v3.json; SPEC=$NOTARY_DIR/spec-r1-results-20261110-v3.json
        MANIFEST_SHA=eae0cae31e560320cc338025a97b4da29e1e8dee63c582d9ab9f5c52ec52992d
        EXPECT="medas-p9-search=ea21771860b76732e263b4d3eb40c9255c693116"
        WH=0 ;;
    # the superseded r1 manifest with the reports in version 2 (for the backup of 2026-11-10 11:14 made of it)
    r1-v2) MANIFEST=$NOTARY_DIR/manifest-r1-results-20261110.json; SPEC=$NOTARY_DIR/spec-r1-results-20261110.json
        MANIFEST_SHA=6f5de6de30a45905179e1d3352c91020f692dcb06bdcafed2ab30ede75c47a6e
        EXPECT="medas-p9-search=85d4061f441b636455f232ab48dcc29ec1fbc64b"
        WH=0 ;;
    # the replaced, not entered drafts of entry 3 (for a backup made of them)
    e3-20261103) MANIFEST=$NOTARY_DIR/manifest-e3-production-20261103.json; SPEC=$NOTARY_DIR/spec-e3-production-20261103.json
        MANIFEST_SHA=9ade41f9bbd0dffbf89b1c693ec08459ef7d85a82e261a7fd1474436a20bb212
        EXPECT="medas-p9-search=080a54fae9c3f7526b98b19455e8cedf9c4f2107 medas-p9-search-bb2021=f82c10d4739b6cd4f4d0d36ab162b5b02d07d866 medas-p9-search-equiv=cf41eedaa7fc25aa13302159e61b448ff528958a"
        WH=0 ;;
    e3-20261102) MANIFEST=$NOTARY_DIR/manifest-e3-production-20261102.json; SPEC=$NOTARY_DIR/spec-e3-production-20261102.json
        MANIFEST_SHA=7ecd6320435a1dd13fc592e900b803c3cb166ff4eb5e57fcdfed693b2576ca15
        EXPECT="medas-p9-search=8debfcf6c8e0e85f1f1e83e9b4d4b456d7bcbf67 medas-p9-search-bb2021=32defaf0e413ca14778391fd3baaec55967e8105"
        WH=0 ;;
    *) die "unknown manifest name '$1' (a3, e2, e3, e4, e5, e6, e9, r1, r1-v2, e3-20261103 or e3-20261102)" ;;
  esac
}

# repositories and commits as the manifest names them: "name=commit" per line
manifest_repos() {
  python3 -I -c "import json, sys
for n, r in sorted(json.load(open(sys.argv[1]))['repositories'].items()): print(n + '=' + r['commit'])" "$1"
}

# the refs of the git bundle of a backup, one "REF COMMIT" per line: the repository commits of the manifest
# (refs/notary-backup/NAME/REPO), and every other commit of a file listed with git ("at" in the spec, e.g. a program
# change on another branch; refs/notary-backup/NAME/REPO-at-COMMIT). Without the latter the restored repository lacks
# such a commit; manifest.py verify then fell back to the file of the checked-out commit (e6, 2026-11-18), and since
# 2026-11-18 it reports "COMMIT MISSING". The manifest's own manifest.py is used, so older ones still fall back.
bundle_refs() {
  python3 -I -c "import json, sys
m = json.load(open(sys.argv[1])); name = sys.argv[2]
heads = {n: r['commit'] for n, r in m['repositories'].items()}
for n, c in sorted(heads.items()): print(f'refs/notary-backup/{name}/{n} {c}')
extra = sorted({(f['repo'], f['git']['commit']) for f in m['files'] if f.get('git') and f['git']['commit'] != heads[f['repo']]})
for n, c in extra: print(f'refs/notary-backup/{name}/{n}-at-{c} {c}')" "$1" "$2"
}

# every commit of a file listed with git, as "REPO COMMIT" (for the check that the restored repository has them)
manifest_file_commits() {
  python3 -I -c "import json, sys
m = json.load(open(sys.argv[1]))
for n, c in sorted({(f['repo'], f['git']['commit']) for f in m['files'] if f.get('git')}): print(n, c)" "$1"
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
  while read -r r c; do
    git -C "$work/.repo" cat-file -e "$c^{commit}" 2>/dev/null || die "commit $c (files of $r) not in the bundle"
  done < <(manifest_file_commits "$m")
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
