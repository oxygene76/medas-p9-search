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
| (b) production run, before its start | `runs/notary/spec-b-production-TEMPLATE.json` (criteria file to be written) | not yet |
| trial | `runs/notary/spec-trial.json` | not yet |
