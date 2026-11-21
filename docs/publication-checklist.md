# Checklist for publishing the repository (2026-11-10, updated 2026-11-18 after entry e6)

Builds on `docs/publication-commits.md` (what is published, and in which order) and `docs/data-package-proposal.md`
section 7 (secret scan, private details, history unchanged). Each point is ticked off with its date. Nothing of this
has been done yet, except where a date is given.

**Rule:** no merge into `main`, no tag and no push until point E. The repository has no remote yet.

## Decisions of 2026-11-18 (project lead, after the check of the published history and the reveal archives)

The check covered the 305 commits of `main` and the four tips after e6, all 796 file versions and the commit
messages, and the 233 files without git of the seven manifests, tars inside tars included. It found no obstacle.
Decided:
1. **Author and committer** (`Eike <e.janssen@medas-computers.de>`, all 305 commits) and the time zones of the
   timestamps are published.
2. **The home path in `runs/accept-v5/maketest.log`** (a3, notarised) is published, as the one in `environment.txt`.
3. **Point B below:** the files under `runs/` and the `defaults.env` that are in the published trees are explicit
   exceptions.
4. **GPU UUID in the run logs unchanged**, no placeholder. The checksum lists of sets A and B, among others, are
   stamped. `docs/data-package-e6.md` is adjusted.
5. **The researcher address** stays named in `docs/notary.md`.

**New rule: no host names are published any more.**
- Notarised files stay unchanged; the exception of 2026-11-04 holds only for them, and for the published history that
  cannot change without a rewrite. Both are listed with entry and path in `docs/publication-host-exceptions.tsv`.
- **Notarised versions against newer versions** (decision of 2026-11-18): package sources that are notarised at an older commit (`EXPECTED-TIME`, `select-gpu.sh`, `docs/gpu-check.md`, `docs/production-package.md`, the speed comparison) get neutral newer versions by new commits, so that future packages hold no host name, while the notarised versions stay unchanged and verifiable at their commits; a finished notarised document such as the A100 acceptance report of 2026-11-03 gets no newer version and stays as it is.
- **New documents, reports, commit messages, file names, packages and scripts:** only neutral names ("GPU server",
  "notebook"). No host name in `EXPECTED-TIME`, `select-gpu.sh`, templates or log headers of future packages.
- **`tools/publish_scan.py`:** the known host names are a blocking class. A finding outside the exception list blocks.
- **For r2, e7 and r3:** before the manifest is made, `tools/publish_scan.py` over every file to be added. Files taken
  unchanged from notarised packages are in the exception list.


## Decisions of 2026-11-20 (project lead)

1. **Sources named by file and SHA-256** instead of "the Claude chat" (outcome report, c1866b0).
2. **The account name of the GPU server** stays in notarised files and in the published history; these are in
   `docs/publication-host-exceptions.tsv`. `tools/publish_scan.py` blocks it in account contexts elsewhere (f7c4081;
   its message should read 87 files and 8 tests). Newer versions of package sources avoid it (`a100/` on
   feat/bb2021-setup f9743be, feat/rin-every e0f2744, feat/run-status 731ae59).
3. **Entry #9** goes into section 5 of the website and into the register as "Criteria, check run" / "Kriterien
   Prüflauf", shown as sealed on 2026-11-24. r2, e7 and r3 are added later, each as a new delivery of section 5 with
   the register.
4. **Section 6 of the website** is final in the version of 2026-11-20; it is not shortened further.

## Decisions of 2026-11-21 (project lead)

1. **Everything is prepared on 2026-11-22;** the state is frozen on 2026-11-22 in the evening. The push goes into the
   private repository `https://github.com/oxygene76/medas-p9-search` on 2026-11-22 in the evening, by the project lead
   after the fresh-clone check. The repository becomes public on 2026-11-24 shortly before 09:00 UTC.
2. **The reveals on the chain** (#3, #5, #6, #7, #11, #12) are made by the project lead on 2026-11-22 in the evening,
   together with `verify_commitments.py`, so the receipts are decrypted only once. **This lifts the earlier rule "from
   09:00, not before" for the reveals on the chain.** A reveal stores only the salt and the SHA-256 of the manifest
   (`medas-notary-contract` 0.2.0, `reveal`); nothing of the result can be read from it before the documents are
   public. The documents become public only on 2026-11-24.
3. **Before anything is made public on 2026-11-24:**
   - proof that the repository and its whole history hold nothing of #2, #4, #9, #10 (salt, receipt, also
     encrypted, manifests, documents);
   - a secret scan of the whole history (keys, tokens, passphrases, host names, internal addresses).
   - The documents under version control are part of the history by design. The weighing of "whole repository"
     against "a separate public repository with the release only" is left to the project lead
     (`runs/notary/NACHWEIS-veroeffentlichung-20261121.md`, not in git).
4. **No transaction and no push by the working session;** the project lead makes the reveals, the push and the
   publication himself.

## A. Before anything else

- [ ] All evaluations covered by the publication are done, with their result reports committed and stamped:
  - production run;
  - long runs 110–112;
  - paired tests A and B;
  - sets A and B, if released (or a later e8, called e7 in `docs/data-package-e6.md` section 2);
  - BB-A-rin1 (r3, proposed), if it is to be in the publication.
- **Names:** kept in `docs/notary.md` (2026-11-18). e6 is the criteria of BB-A-rin1; the data package is e7, called e6
  in documents written up to 2026-11-18, among them this list before 2026-11-18 and `docs/data-package-e6.md`.
- [x] Entry e6 (criteria of BB-A-rin1) is on chain, entry #9 (2026-11-18, block 10942017), and `docs/notary.md` is
      updated (01a6d6a).
- [ ] Entries r2 (result of sets A and B) and, if wanted, r3 (result of BB-A-rin1) are on chain, and `docs/notary.md`
      is updated.
- [ ] Entry e7 (the data package) is on chain, and `docs/notary.md` is updated.
- [x] `docs/publication-commits.md` is regenerated with e6 (2026-11-18, 01a6d6a). Four tips: fed221a, d4dadd9,
      f80681f and 0b8971f; closure 305 of 361.
- [ ] It is regenerated again after each further entry (r2, r3, e7); the tips and the closure are known.
- [ ] All pending OTS stamps are upgraded and checked against two block explorers (only block heights sent).
- [ ] The decisions still open in `docs/data-package-proposal.md` are made: ORCID, wording of the methods section.

## B. Content of the published state

- [ ] **README.md rewritten.** Today it still says "Pilot, local only … no chain entries", which is no longer true.
      New content:
  - what the project is;
  - the status ("not peer-reviewed", the research note);
  - how to build, the run packages, and how to verify one segment;
  - the notary entries with links to `docs/notary.md`;
  - the data records (DOIs);
  - the licence;
  - the use of AI tools (wording as in the methods section).
- [ ] `CITATION.cff` of the software (author Eike Janßen, MEDAS Computers GmbH, ORCID).
- [ ] `LICENSE` (GPL-3.0-or-later) and `third_party/README.md` (REBOUND 5.2.2, checksum, licence) present in the
      published tree.
- [ ] New documents name no host names, home paths or GPU UUIDs ("the GPU server", relative paths). Notarised files
      stay unchanged (option 7.1); the README says so.
- [ ] `runs/`, `build/` and `.env`-like files are ignored and appear in no published tree: `git ls-tree -r` of the
      state to be published, checked for `runs/`, `build/`, `*.env` and `*receipt*`.
  - **Explicit exceptions** (decision of 2026-11-18), committed on purpose and checked: no secrets, no paths, no UUID.
    - `runs/compare-rebound-p9gpu-dkd.txt` and `runs/compare-rebound-p9gpu-kdk-late.txt`, at all tips;
    - `runs/speed/RESULT.md`, `runs/speed/run.sh`, `runs/speed/run-cpu.sh` and `runs/speed/run.log`, at 0b8971f and
      d4dadd9. `RESULT.md` holds the host name; it is in the published history and in the exception list.
    - `bb/sets/defaults.env`, `bb/v2short/defaults.env` and `pair/v5/defaults.env` (package defaults: GPU name, socket,
      card check), at fed221a.
    - `tools/notary/notary-receipt-backup.sh` matches `*receipt*`. It is a script, not a receipt.
  - Any other match blocks.

## C. Branches and tags

- [ ] **Published:** only `main` and the tags of the list (`notary-<entry>-<commit>`, one per referenced commit). The
      existing tags inside the closure, `bb2021-criteria-draft-1`, `make-ic-v1` and `prod-eval-v1`, are published
      with them.
- [ ] **Among them, explicitly, the tips outside `feat/pilot`.** A third party can check e6 only with them; tested on
      2026-11-18: a clone of `feat/pilot` alone gives 18 of 25.
  - `notary-e6-0b8971f` on 0b8971f, the program change of BB-A-rin1 (`gpu/p9gpu.c`, `gpu/kernel.cu`,
    `gpu/p9gpu_api.h`). The branch `feat/rin-every` itself stays private; the tag is enough.
  - `notary-e5-fed221a` on fed221a, the commit of `medas-p9-search-equiv` named by e5 and e6.
  - `notary-e5-d4dadd9` on d4dadd9 (`medas-p9-search-bb2021`).
  - After D all of them are also ancestors of `main`. The tags are still set, so each commit can be found from its
    manifest.
- [ ] **Not published:**
  - all other branches, among them the worktree branches (`feat/plate-pilot`, `feat/own-images`, `feat/new-etnos`,
    `feat/c3-bundle`, `run/*` …);
  - the tags outside the closure (`plates-core-*`, `own-images-*`, `etno-tier2-v1`).
- [ ] The medas-p9-search worktrees share **one** repository with all branches. A push therefore names every ref
      explicitly, and never uses `--all`, `--tags` or `--mirror`.

## D. Merge into `main`, only right before the push

- [ ] **Dry run, done 2026-11-10 for the tips after e5** (`e83d960`, `d4dadd9`, `fed221a`): `git merge-tree
      --write-tree`, pairwise and all three together, gives no conflict.
- [x] **Dry run with the four tips after e6, done 2026-11-18** (`fed221a`, `d4dadd9`, `f80681f`, `0b8971f`):
      pairwise (6 pairs) and all four in sequence, no conflict. Objects only, no refs. Repeat it with the tips after
      the last entry.
- [ ] **Merge commit** on `main` of the tips: a new commit, no rebase and no rewrite. Message: "Publication: the state
      of the campaign (tips …)".
- [ ] Afterwards, every referenced commit is an ancestor of `main` or of a tag:
      `git merge-base --is-ancestor <commit> main` for each line of the list.
- [ ] Set the tags of the list (lightweight or annotated, decided at that time) on exactly the referenced commits.

## E. Scans over exactly the state to be published

Run after D, and before the push:
- [ ] **gitleaks** (v8.18.4, built from source as on 2026-11-04, checked against sum.golang.org) over the history of
      `main` and the tags. Expected: no leaks. A control repository with planted keys proves the scanner works.
- [ ] **`tools/publish_scan.py --git <rev>`** over the tree of `main` and of every tag. Expected: 0 blocking findings
      (secrets, Gaia data).
- [ ] **`tools/publish_scan.py --blobs main <tags>`** over every file version of the published state. Expected: 0
      blocking findings; host names only in the exception list (`docs/publication-host-exceptions.tsv`).
- [ ] **`tools/publish_scan.py --history`** over the published state. Reported private details are compared with the
      known list (data package proposal section 7: host name, home path, GPU UUID, author address), and anything new
      is decided before the push.
- [ ] `git count-objects` and the size of a fresh `git clone --mirror` of only the published refs (in a temporary
      directory), as a check that nothing large or private comes along.
- [ ] **Probe "fresh clone, verify", before 2026-11-24, before the push:**
  - In a temporary directory, make a fresh clone that holds only the published refs: `main` and the tags of the list,
    each named, from a `--no-local` clone.
  - Check out each repository commit of a manifest as a detached worktree (e6: f80681f and fed221a).
  - Unpack the files without git from the archive of the reveal (`manifest.py archive`).
  - Run `manifest.py verify` (version of 0ee3dc9 or later, which reports a missing commit as COMMIT MISSING) for every
    manifest on chain.
  - **Expected:** every one complete, e6 **25 of 25**, no COMMIT MISSING.
  - The same done by hand on 2026-11-18 with a local clone of all branches gave 25 of 25.

## F. Push

- [ ] Create the remote (host and organisation are decided at that time) and set it, without a push.
- [ ] `git push <remote> main` and then `git push <remote> refs/tags/<tag> …` for every tag of the list, each named.
- [ ] Clone it fresh from the remote, then check:
  - `git log --oneline main | wc -l` equals the closure of the list;
  - the tags are present;
  - `git show <commit>:<path>` of three manifest lines (a3, e3, e5) works, and their sha256 equals the manifest;
  - `manifest.py verify` of e6 from this clone, with the reveal archive, gives 25 of 25 (the p9gpu files at 0b8971f
    included).
- [ ] Software record on Zenodo (GitHub integration or upload of `git archive`) at the published commit.

## G. Afterwards

- [ ] Upload the data records (`docs/data-package-e6.md` section 4) and reveal the entries.
- [ ] The research note gets the DOIs and links.
- [ ] Any later change comes as new commits and new versions of the records, never as rewrites.
