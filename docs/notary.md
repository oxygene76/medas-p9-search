# Notary entries for the Planet Nine search

How states of this project (criteria, configurations, results) are fixed in
the MEDAS notary on medasdigital-2 without being disclosed, and later
revealed so that anyone can check them. The protocol: `docs/notary-spec.md`
and `docs/notary-contract-spec.md` in medasdigital-2; the web application
notary.medas-digital.io (repository medas-notary-web).

## What is entered: a manifest

`tools/manifest.py make SPEC.json OUT.json` writes a manifest: one JSON file
with the SHA-256 and size of every file of the statement.
- Files in git: the full commit and the git blob id (`git show
  <commit>:<path>` gives the file), e.g. a criteria file as committed before
  its run.
- Other files (results, binaries, packages, reports): their hash; they are
  published as an archive under the same paths at the reveal.
- No local paths, user or host names. JSON with sorted keys, written once;
  any change, even re-saving it, changes its hash.

The SHA-256 of the manifest file is the content of the notary entry. After
the reveal anyone checks each file on its own: `tools/manifest.py verify
MANIFEST.json --repo NAME=DIR` (or `sha256sum` of a single file against the
manifest), and the manifest itself against the revealed content digest.

Manifests and their specifications stay private until the reveal: they are
kept in `runs/notary/` (not in git) and never committed before the reveal.

## Entering (web application, Submit)

With the researcher address in Keplr (for real entries only the registered
researcher address of the project lead; never the test address):
1. **Submit**, "A file (paper, data set, prediction)": choose the manifest
   file. The browser computes its SHA-256 locally; the file is not uploaded.
2. Entry type: `note` for a state of work (manifest a); `job` for the
   configuration of a run fixed before its start (manifest b), so that its
   results can later be entered as `result` referring to it. Title and
   description are optional and stay in the receipt, private.
3. **Save the receipt** (it holds the secret salt) and load it again as asked:
   without the receipt the entry can never be revealed. Keep receipt and
   manifest together, with a backup, offline.
4. **Sign** in the wallet. The entry fee is burnt (the trial run of the
   operations used 1,000 MEDAS); the network fee comes on top. The block time
   becomes the time of the entry. Note the entry number and the transaction.

Until the reveal the chain shows only the commitment hash, the entry type and
the time.

## Revealing (web application, Reveal and Verify)

1. Publish first what the manifest lists: the repository at the commits named
   in it, the archive of the other files, and the manifest itself.
2. **Reveal** with the receipt. This publishes salt and content digest (the
   manifest's SHA-256); the chain checks them against the commitment.
3. **Verify** with the receipt or the manifest file: "Verified." Anyone can do
   this, and `tools/manifest.py verify` for every listed file.

Per the evaluation rules (notary-spec.md section 12) an entry is judged
together with all entries of its address, revealed or not.

## Trial run first

Before the first real entry, the trial run of medas-notary-web
`docs/operations.md` section 6, steps 2 to 5, with the operators' test address
and `runs/notary/manifest-trial.json` (spec `runs/notary/spec-trial.json`, no
scientific content): entry with burn, reveal, revocation, end state. Never
the real manifests with the test address: an entry is bound to its address
for good.

## Manifests

| | specification | entered |
|---|---|---|
| (a) validation up to 2026-10-21 | `runs/notary/spec-a-validation.json` | not yet |
| (a2) (a) plus the status note on the open deviation | `runs/notary/spec-a2-validation-status.json` | never: superseded by (a3) |
| (a3) (a2) plus the addendum on single runs and means | `runs/notary/spec-a3-validation-status.json` | entry #2, 2026-11-02 12:08:31 UTC, block 10694917, commitment `b00d53999d1ca2a8be260c2b84c3e941a4eab52e5843c295c280a1bb968ba2a4` |
| (e2) equivalence test fixed before its evaluation (note, refers to the (a3) entry) | `runs/notary/spec-e2-equivalence-20261023.json` | entry #3 (refers to #2), 2026-11-02 12:14:09 UTC, block 10694977, commitment `795a8c58735ef5fa62a1ad5549b740f04178eaf64b4a1f4f64d3f47ea4fcc343` |
| (e3) result of the equivalence test, the production run, the paired long runs 110–112 and the order on the A100, before their start (job, refers to the (e2) entry) | `runs/notary/spec-e3-production-20261104.json` (manifest sha256 `fa4d84fb5619cf7746f26cbfd0d9102a1961db8f26c7fc88e0f0e69208b03c60`) | entry #4 (refers to #3), 2026-11-04 09:31:02 UTC, block 10723643, tx `C6BEC752F7528F79BBECF89A43899EDF8A7F80169C86455BDB2DAF793432FB98`, commitment `cafc7ebbbdc7d3b0015ae56f1adf4eaab4eb882dc16473f35bf295c3073bdbff` |
| (e4) addendum 16 (V2 short runs on the L40S, 16,000 test particles) and the packages of sets A and B (note, refers to the (e3) entry) | `runs/notary/spec-e4-bb2021-v2-20261104.json` (manifest sha256 `5e5829b7461ff56a42518190b0fc2cdbfcdaa695f761b0663dad3c0bf61b22cc`) | entry #5 (refers to #4), 2026-11-04 17:06:01 UTC, block 10728476, tx `D63E2D39E0B4325743484FA63E852F9D1E6A3FE363FAAB309C2E7037906E92DB`, commitment `5219949b8f6cf5b8e7c08ec065ff316b3a9a6f18fd3252c7f20ce863ba1bff1f` |
| (e5) criteria of the paired tests V5 against MERCURIUS for sets A and B, before any of their runs (job, refers to the (e4) entry #5) | `runs/notary/spec-e5-paired-tests-20261106.json` (spec sha256 `e424cd1ec67f43c7eee50feae4ba12e8e7d49a0d9611b6df11c742ed9693b99f`; manifest sha256 `a3dc42d8fc6b91c98f76effd49cca637a54788e7732b367d1a5f3b5e0aa6b037`) | entry #6 (refers to #5), 2026-11-10 07:18:02 UTC, block 10814015, tx `91273FA27ED2AE101C1C1E3230703F993E809734819784780B6003FD84CC32EB`, commitment `61232c7217024299c5dbee92bbf99bf024b93714fcf920d7711f7adda8108d75` |
| (r1) results of the production run and of the paired long runs 110–112, evaluated by the criteria of entry #4, after the independent review of the reports (result, refers to the (e3) entry #4) | `runs/notary/spec-r1-results-20261110.json` (spec sha256 `f9ab8fd992768afd50bac01fc3c7be7fc6c71ed80f7219b5f0a4d6f2262be742`; manifest sha256 `6f5de6de30a45905179e1d3352c91020f692dcb06bdcafed2ab30ede75c47a6e`) | not yet: prepared 2026-11-10 |
| (b) production run, before its start | superseded by (e3) | – |
| trial | `runs/notary/spec-trial.json` | not yet |

The entries #2 to #6 were made from the researcher address `medas1s7y4lg3y96qfltgs8xx9ezyhvn9hgysu78r6wj` in the notary
contract `medas1ghd753shjuwexxywmgs4xz7x2q732vcnkm6h2pyv9s6ah3hylvrqejyaze`; their receipts are backed up encrypted
and checked with `notary-restore-check.sh` (the receipts of #4 and #5: backed up, as reported by the project lead on
2026-11-04; the backup of e5, checked with 37 of 37 files, on three places, and the receipt of #6 backed up encrypted, as
reported on 2026-11-10).

## Backup scripts

`tools/notary/` (versioned): `notary-backup.sh` (a manifest with everything it lists, encrypted, to OneDrive and a
USB drive), `notary-receipt-backup.sh` (a receipt), `notary-restore-check.sh` (restore check with the private key in
a temporary GNUPGHOME) and `notary-lib.sh`. `runs/notary/` has symlinks to them, so they are called as
`bash runs/notary/notary-....sh`; machine-specific settings (the OneDrive folder) are in `runs/notary/local.env`,
not in git.

