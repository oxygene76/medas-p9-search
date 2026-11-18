# Commits and tags for the publication of medas-p9-search (2026-11-18, after entry e6)

Decision of 2026-11-04: published are `main` and every commit and tag that the notary entries refer to. All other
branches stay private. The history stays unchanged, so the notarised documents are published as they were entered.

This list was made with `tools/notary_refs.py` (regenerated on 2026-11-18 after entry e6) from the manifests of
the seven entries of the campaign on chain:
- a3 (entry #2);
- e2 (entry #3);
- e3 (entry #4, block 10723643);
- e4 (entry #5, block 10728476);
- e5 (entry #6, block 10814015);
- r1 (entry #7, block 10829443);
- e6 (entry #9, block 10942017; the criteria of the run BB-A-rin1).

Entry #8 belongs to another project. The data package is now e7 (called e6 in documents up to 2026-11-18; the names
are kept in `docs/notary.md`). This list is to be regenerated after each further entry (r2, r3, e7):

```sh
build/venv/bin/python -I tools/notary_refs.py "a3 (#2)=runs/notary/manifest-a3-validation-status-20261021.json" \
  "e2 (#3)=runs/notary/manifest-e2-equivalence-20261023.json" "e3 (#4)=runs/notary/manifest-e3-production-20261104.json" \
  "e4 (#5)=runs/notary/manifest-e4-bb2021-v2-20261104.json" "e5 (#6)=runs/notary/manifest-e5-paired-tests-20261106.json" \
  "r1 (#7)=runs/notary/manifest-r1-results-20261110-v3.json" "e6 (#9)=runs/notary/manifest-e6-bb-a-rin1-20261118.json"
```

"How":
- `repository`: the commit of the repository in the manifest;
- `files`: the commit of a file with `git`, verified with `git show <commit>:<path>`;
- `named`: a commit id in the text of the manifest, for example in a role, a package name or a statement.

| commit | date | entries (how) | in main | branches | tags | proposed tag |
|---|---|---|---|---|---|---|
| `07e5d2c12de0` | 2026-10-20 | a3 (#2): named | no | feat/arm64-repro, feat/bb2021-setup, feat/c3-bundle, feat/cause-package, feat/equiv-packages, feat/long-runs, feat/new-etnos, feat/own-images, feat/p9sim-cbrt, feat/pilot, feat/plate-pilot, feat/rin-every, feat/run-status, feat/smooth-prefilter | – | `notary-a3-07e5d2c` |
| `47127ba00d94` | 2026-10-20 | a3 (#2): files, named | no | feat/arm64-repro, feat/bb2021-setup, feat/c3-bundle, feat/cause-package, feat/equiv-packages, feat/long-runs, feat/new-etnos, feat/own-images, feat/p9sim-cbrt, feat/pilot, feat/plate-pilot, feat/rin-every, feat/run-status, feat/smooth-prefilter | – | `notary-a3-47127ba` |
| `0e14d7e560eb` | 2026-10-20 | a3 (#2): files | no | feat/arm64-repro, feat/bb2021-setup, feat/c3-bundle, feat/cause-package, feat/equiv-packages, feat/long-runs, feat/new-etnos, feat/own-images, feat/p9sim-cbrt, feat/pilot, feat/plate-pilot, feat/rin-every, feat/run-status, feat/smooth-prefilter | – | `notary-a3-0e14d7e` |
| `79c16e20c01a` | 2026-10-20 | a3 (#2): files, named | no | feat/arm64-repro, feat/bb2021-setup, feat/c3-bundle, feat/cause-package, feat/equiv-packages, feat/long-runs, feat/new-etnos, feat/own-images, feat/p9sim-cbrt, feat/pilot, feat/plate-pilot, feat/rin-every, feat/run-status, feat/smooth-prefilter | – | `notary-a3-79c16e2` |
| `9a084ed45240` | 2026-10-21 | a3 (#2): named; e2 (#3): named; e3 (#4): files, named; r1 (#7): named | no | feat/bb2021-setup, feat/c3-bundle, feat/cause-package, feat/equiv-packages, feat/long-runs, feat/p9sim-cbrt, feat/rin-every, feat/run-status | – | `notary-a3-9a084ed` |
| `c2eef152a2bf` | 2026-10-21 | a3 (#2): files, named, repository medas-p9-search-bb2021 | no | feat/bb2021-setup, feat/c3-bundle, feat/cause-package, feat/equiv-packages, feat/long-runs, feat/p9sim-cbrt, feat/rin-every, feat/run-status | – | `notary-a3-c2eef15` |
| `93059e9a4d80` | 2026-10-21 | a3 (#2): files | no | feat/arm64-repro, feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot | – | `notary-a3-93059e9` |
| `573aca883a5a` | 2026-10-21 | a3 (#2): files, named, repository medas-p9-search | no | feat/arm64-repro, feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot | – | `notary-a3-573aca8` |
| `69b84122c16f` | 2026-10-22 | e2 (#3): files, named, repository medas-p9-search-bb2021 | no | feat/bb2021-setup, feat/rin-every, feat/run-status | – | `notary-e2-69b8412` |
| `47c7381774e2` | 2026-10-22 | e2 (#3): files, named, repository medas-p9-search-equiv | no | feat/c3-bundle, feat/equiv-packages, feat/long-runs, feat/p9sim-cbrt | – | `notary-e2-47c7381` |
| `c45833a6e5ec` | 2026-10-23 | e2 (#3): files, named, repository medas-p9-search; e3 (#4): files, named | no | feat/arm64-repro, feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot | – | `notary-e2-c45833a` |
| `224b7a1fe960` | 2026-11-01 | e3 (#4): named | no | feat/arm64-repro, feat/pilot | bb2021-criteria-draft-1 | `notary-e3-224b7a1` |
| `ae26a3e5b795` | 2026-11-04 | e3 (#4): named | no | feat/bb2021-setup, feat/rin-every, feat/run-status | – | `notary-e3-ae26a3e` |
| `801fb20a295c` | 2026-11-04 | e3 (#4): files, named, repository medas-p9-search-bb2021; e4 (#5): files, named, repository medas-p9-search-bb2021 | no | feat/bb2021-setup, feat/rin-every, feat/run-status | – | `notary-e3-801fb20` |
| `730260738c20` | 2026-11-04 | e3 (#4): files, named, repository medas-p9-search | no | feat/arm64-repro, feat/pilot | – | `notary-e3-7302607` |
| `ac47329bb463` | 2026-11-04 | e3 (#4): files, named, repository medas-p9-search-equiv | no | feat/c3-bundle, feat/long-runs, feat/p9sim-cbrt | – | `notary-e3-ac47329` |
| `1c5f2ba23d57` | 2026-11-04 | e4 (#5): files, named, repository medas-p9-search | no | feat/arm64-repro, feat/pilot | – | `notary-e4-1c5f2ba` |
| `5b05cc3c72b0` | 2026-11-04 | e4 (#5): files, named, repository medas-p9-search-equiv | no | feat/c3-bundle, feat/long-runs, feat/p9sim-cbrt | – | `notary-e4-5b05cc3` |
| `4d42c890f7cf` | 2026-11-06 | e5 (#6): named | no | feat/arm64-repro, feat/pilot | – | `notary-e5-4d42c89` |
| `fed221ad835c` | 2026-11-06 | e5 (#6): files, named, repository medas-p9-search-equiv; e6 (#9): named, repository medas-p9-search-equiv | no | feat/c3-bundle, feat/long-runs, feat/p9sim-cbrt | – | `notary-e5-fed221a` |
| `e83d9609780b` | 2026-11-06 | e5 (#6): files, named, repository medas-p9-search | no | feat/arm64-repro, feat/pilot | – | `notary-e5-e83d960` |
| `d4dadd9263fc` | 2026-11-06 | e5 (#6): files, named, repository medas-p9-search-bb2021 | no | feat/bb2021-setup, feat/run-status | – | `notary-e5-d4dadd9` |
| `0ca95953e343` | 2026-11-06 | r1 (#7): named | no | feat/arm64-repro, feat/pilot | – | `notary-r1-0ca9595` |
| `6a6985476de6` | 2026-11-10 | r1 (#7): named | no | feat/arm64-repro, feat/pilot | – | `notary-r1-6a69854` |
| `af2e058e966d` | 2026-11-10 | r1 (#7): named | no | feat/arm64-repro, feat/pilot | – | `notary-r1-af2e058` |
| `cce5b9212ff1` | 2026-11-10 | r1 (#7): named | no | feat/arm64-repro, feat/pilot | – | `notary-r1-cce5b92` |
| `ea38f05f1fd2` | 2026-11-10 | r1 (#7): named | no | feat/arm64-repro, feat/pilot | – | `notary-r1-ea38f05` |
| `85d4061f441b` | 2026-11-10 | r1 (#7): named | no | feat/arm64-repro, feat/pilot | – | `notary-r1-85d4061` |
| `2e2186449655` | 2026-11-10 | r1 (#7): named | no | feat/arm64-repro, feat/pilot | – | `notary-r1-2e21864` |
| `ea21771860b7` | 2026-11-10 | r1 (#7): files, named, repository medas-p9-search | no | feat/arm64-repro, feat/pilot | – | `notary-r1-ea21771` |
| `0b8971fbf96e` | 2026-11-17 | e6 (#9): files, named | no | feat/rin-every | – | `notary-e6-0b8971f` |
| `22f70fd2f6a7` | 2026-11-18 | e6 (#9): named | no | feat/pilot | – | `notary-e6-22f70fd` |
| `2ee681cd51c8` | 2026-11-18 | e6 (#9): named | no | feat/pilot | – | `notary-e6-2ee681c` |
| `f80681f933aa` | 2026-11-18 | e6 (#9): files, named, repository medas-p9-search | no | feat/pilot | – | `notary-e6-f80681f` |

Tips (each referenced commit is one of these or an ancestor of one):
- `fed221ad835c` 2026-11-06 pair/merc: own scripts for the MERCURIUS half of the paired tests (decision of 2026-11-06
- `d4dadd9263fc` 2026-11-06 chain: the paired packages of fed221a (the MERCURIUS half at nice 19 with idle I/O on the
- `0b8971fbf96e` 2026-11-17 p9gpu: removals counted separately per run: removed_r_in, removed_r_out, removed_collisio
- `f80681f933aa` 2026-11-18 BB-A-rin1 criteria fixed (2026-11-18), for the entry

Closure: main and the referenced commits with all their ancestors are 305 of 361 commits; 56 stay private.
Existing tags in the closure: bb2021-criteria-draft-1, make-ic-v1, prod-eval-v1; outside: etno-tier2-v1, own-images-criteria-v1, own-images-criteria-v2, own-images-v1, p9sim-cbrt-v1, p9sim-cbrt-v2, plates-core-v1, plates-core-v2, plates-core-v3, plates-core-v4, plates-core-v5, plates-core-v6, plates-core-v7, plates-core-v8.

## What this means

- **No referenced commit is on `main`.** `main` holds only the first commit (e38179b). Branches stay private, so the
  referenced commits can only be published as tags. The proposed names are in the last column: one tag per
  referenced commit, after the first entry that refers to it.
  - The four tips alone would make all 34 reachable.
  - One tag each makes them easy to find from the manifests.
- **Since e6 there are four tips:** fed221a, d4dadd9, f80681f (`feat/pilot`) and 0b8971f (`feat/rin-every`, the program
  change of BB-A-rin1).
  - 0b8971f is not an ancestor of any other tip. Without it (or its tag) three files of e6 cannot be checked:
    `gpu/p9gpu.c`, `gpu/kernel.cu`, `gpu/p9gpu_api.h`.
  - A clone without fed221a cannot check e6 either (`medas-p9-search-equiv`).
  - Tested 2026-11-18 on a local clone: all branches 25 of 25; `feat/pilot` alone 18 of 25.
- **A published commit publishes its ancestors.** `main` and the 34 commits with their history are 305 of 361 commits
  (2026-11-18, after e6).
  - That includes parts of the branches that otherwise stay private, as far as they lie before a referenced commit:
    `feat/pilot` up to f80681f, `feat/bb2021-setup` up to d4dadd9, `feat/long-runs` up to fed221a, `feat/rin-every`
    up to 0b8971f.
  - Private stay: the 56 later commits or commits of other branches, among them the plate and own-images tools with
    their Gaia queries and their tags (`plates-core-*`, `own-images-*`, `etno-tier2-v1`, `p9sim-cbrt-*`).
  - Since e5, `tools/export_timelapse.py`, `tools/publish_scan.py`, the proposals of the data package and the first
    version of this list lie before a tip and are published with it.
  - Since r1 (tip ea21771) also the e5 entry in `tools/notary`, `tools/long_eval.py`, the evaluations and result
    reports, the research note skeleton, the data package structure and the publication checklist.
  - **Since e6 (tip f80681f) also the 42 commits ea21771..f80681f:**
    - the paired tests of sets A and B with their reports;
    - the evaluation procedure and results of sets A and B, their reports and the outcome report;
    - the decompositions with addenda 1–4 and their tools;
    - the criteria of BB-A-rin1;
    - the reproduction and README updates, `pack_record.py`, `check_segments.py`;
    - the r1 entry in `tools/notary` and `docs/notary.md` (efd4eca, c5e8b44).
  - Also private: everything after the tips, such as the e6 entry and the backup fix in `tools/notary` (81d7005,
    91b5e53) and this version of the list, until it is published separately.
- **Existing tags in the published part:** `bb2021-criteria-draft-1` (224b7a1, named in e3), `make-ic-v1`,
  `prod-eval-v1`. They are published with it.

## Checks done (2026-11-04)

They covered the tips of 2026-11-04. The tips of e5, r1 and e6 (f80681f, 0b8971f) are not scanned yet; step 4 of the
order below scans the final state anyway.

- **gitleaks** v8.18.4 (built from source through the Go module proxy, checked against sum.golang.org), over the
  whole history (`--log-opts=--all`, 264 commits): **no leaks found**.
  - A control repository with three planted keys gave 2 findings, so the scanner works.
- **`tools/publish_scan.py --history`:** no secrets, no Gaia data.
  - Over the trees of the three tips and of `main`: 0 blocking findings.
  - Reported, and published unchanged by decision: the host name of the GPU server (in the notarised files only; rule of 2026-11-18), the home path in
    `environment.txt` and the GPU UUID in the acceptance report.

## Order of the publication (decision of 2026-11-04)

1. Enter e4, e5 (the criteria of the paired tests), r1 (the results), e6 (the criteria of BB-A-rin1), r2 (the result
   of sets A and B), r3 (the result of BB-A-rin1, proposed), then e7 (the data package; e6 before 2026-11-18). e4, e5,
   r1 and e6 are on chain (#5, #6, #7, #9).
2. Regenerate this list after each entry (`tools/notary_refs.py`; e4 is in it since 2026-11-04, e5 since 2026-11-10,
   r1 since 2026-11-11, e6 since 2026-11-18).
3. **Only right before the push:** `main` is brought to the state of the campaign by a merge commit of the tips. This
   is a new commit, not a rewrite. Then the tags of the list are set.
4. Both scans over exactly the state to be published, that is `main` after the merge plus the tags:
   - gitleaks over their history;
   - `tools/publish_scan.py --git` over each tree, and over the history of that state.
5. Push `main` and the tags; nothing else.

Until then: no merge into `main`, no tags, no push.
