# Commits and tags for the publication of medas-p9-search (2026-11-10, after entry e5)

Decision of 2026-11-04: published are `main` and every commit and tag that the notary entries refer to. All other
branches stay private. The history stays unchanged, so the notarised documents are published as they were entered.

This list was made with `tools/notary_refs.py` (regenerated on 2026-11-10 after entry e5) from the manifests of
the five entries on chain:
- a3 (entry #2);
- e2 (entry #3);
- e3 (entry #4, block 10723643);
- e4 (entry #5, block 10728476);
- e5 (entry #6, block 10814015).

It is to be regenerated after e6 (the data package):

```sh
build/venv/bin/python -I tools/notary_refs.py "a3 (#2)=runs/notary/manifest-a3-validation-status-20261021.json" \
  "e2 (#3)=runs/notary/manifest-e2-equivalence-20261023.json" "e3 (#4)=runs/notary/manifest-e3-production-20261104.json" \
  "e4 (#5)=runs/notary/manifest-e4-bb2021-v2-20261104.json" "e5 (#6)=runs/notary/manifest-e5-paired-tests-20261106.json"
```

"How":
- `repository`: the commit of the repository in the manifest;
- `files`: the commit of a file with `git`, verified with `git show <commit>:<path>`;
- `named`: a commit id in the text of the manifest, for example in a role, a package name or a statement.

| commit | date | entries (how) | in main | branches | tags | proposed tag |
|---|---|---|---|---|---|---|
| `07e5d2c12de0` | 2026-10-20 | a3 (#2): named | no | feat/bb2021-setup, feat/cause-package, feat/equiv-packages, feat/long-runs, feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot, feat/smooth-prefilter | – | `notary-a3-07e5d2c` |
| `47127ba00d94` | 2026-10-20 | a3 (#2): files, named | no | feat/bb2021-setup, feat/cause-package, feat/equiv-packages, feat/long-runs, feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot, feat/smooth-prefilter | – | `notary-a3-47127ba` |
| `0e14d7e560eb` | 2026-10-20 | a3 (#2): files | no | feat/bb2021-setup, feat/cause-package, feat/equiv-packages, feat/long-runs, feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot, feat/smooth-prefilter | – | `notary-a3-0e14d7e` |
| `79c16e20c01a` | 2026-10-20 | a3 (#2): files, named | no | feat/bb2021-setup, feat/cause-package, feat/equiv-packages, feat/long-runs, feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot, feat/smooth-prefilter | – | `notary-a3-79c16e2` |
| `9a084ed45240` | 2026-10-21 | a3 (#2): named; e2 (#3): named; e3 (#4): files, named | no | feat/bb2021-setup, feat/cause-package, feat/equiv-packages, feat/long-runs | – | `notary-a3-9a084ed` |
| `c2eef152a2bf` | 2026-10-21 | a3 (#2): files, named, repository medas-p9-search-bb2021 | no | feat/bb2021-setup, feat/cause-package, feat/equiv-packages, feat/long-runs | – | `notary-a3-c2eef15` |
| `93059e9a4d80` | 2026-10-21 | a3 (#2): files | no | feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot | – | `notary-a3-93059e9` |
| `573aca883a5a` | 2026-10-21 | a3 (#2): files, named, repository medas-p9-search | no | feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot | – | `notary-a3-573aca8` |
| `69b84122c16f` | 2026-10-22 | e2 (#3): files, named, repository medas-p9-search-bb2021 | no | feat/bb2021-setup | – | `notary-e2-69b8412` |
| `47c7381774e2` | 2026-10-22 | e2 (#3): files, named, repository medas-p9-search-equiv | no | feat/equiv-packages, feat/long-runs | – | `notary-e2-47c7381` |
| `c45833a6e5ec` | 2026-10-23 | e2 (#3): files, named, repository medas-p9-search; e3 (#4): files, named | no | feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot | – | `notary-e2-c45833a` |
| `224b7a1fe960` | 2026-11-01 | e3 (#4): named | no | feat/pilot | bb2021-criteria-draft-1 | `notary-e3-224b7a1` |
| `ae26a3e5b795` | 2026-11-04 | e3 (#4): named | no | feat/bb2021-setup | – | `notary-e3-ae26a3e` |
| `801fb20a295c` | 2026-11-04 | e3 (#4): files, named, repository medas-p9-search-bb2021; e4 (#5): files, named, repository medas-p9-search-bb2021 | no | feat/bb2021-setup | – | `notary-e3-801fb20` |
| `730260738c20` | 2026-11-04 | e3 (#4): files, named, repository medas-p9-search | no | feat/pilot | – | `notary-e3-7302607` |
| `ac47329bb463` | 2026-11-04 | e3 (#4): files, named, repository medas-p9-search-equiv | no | feat/long-runs | – | `notary-e3-ac47329` |
| `1c5f2ba23d57` | 2026-11-04 | e4 (#5): files, named, repository medas-p9-search | no | feat/pilot | – | `notary-e4-1c5f2ba` |
| `5b05cc3c72b0` | 2026-11-04 | e4 (#5): files, named, repository medas-p9-search-equiv | no | feat/long-runs | – | `notary-e4-5b05cc3` |
| `4d42c890f7cf` | 2026-11-06 | e5 (#6): named | no | feat/pilot | – | `notary-e5-4d42c89` |
| `fed221ad835c` | 2026-11-06 | e5 (#6): files, named, repository medas-p9-search-equiv | no | feat/long-runs | – | `notary-e5-fed221a` |
| `e83d9609780b` | 2026-11-06 | e5 (#6): files, named, repository medas-p9-search | no | feat/pilot | – | `notary-e5-e83d960` |
| `d4dadd9263fc` | 2026-11-06 | e5 (#6): files, named, repository medas-p9-search-bb2021 | no | feat/bb2021-setup | – | `notary-e5-d4dadd9` |

Tips (each referenced commit is one of these or an ancestor of one):
- `fed221ad835c` 2026-11-06 pair/merc: own scripts for the MERCURIUS half of the paired tests (decision of 2026-11-06
- `e83d9609780b` 2026-11-06 Paired-test criteria with the decisions of 2026-11-06 (section 8): seeds as proposed, one
- `d4dadd9263fc` 2026-11-06 chain: the paired packages of fed221a (the MERCURIUS half at nice 19 with idle I/O on the

Closure: main and the referenced commits with all their ancestors are 243 of 290 commits; 47 stay private.
Existing tags in the closure: bb2021-criteria-draft-1, make-ic-v1, prod-eval-v1; outside: etno-tier2-v1, own-images-criteria-v1, own-images-criteria-v2, own-images-v1, plates-core-v1, plates-core-v2, plates-core-v3, plates-core-v4, plates-core-v5, plates-core-v6, plates-core-v7, plates-core-v8.

## What this means

- **No referenced commit is on `main`.** `main` holds only the first commit (e38179b). Branches stay private, so the
  referenced commits can only be published as tags. The proposed names are in the last column: one tag per
  referenced commit, after the first entry that refers to it.
  - The three tips alone would make all 22 reachable.
  - One tag each makes them easy to find from the manifests.
- **A published commit publishes its ancestors.** `main` and the 22 commits with their history are 243 of 290 (2026-11-10, after e5)
  commits. That includes parts of the branches that otherwise stay private, as far as they lie before a referenced
  commit: `feat/pilot` up to e83d960, `feat/bb2021-setup` up to d4dadd9, `feat/long-runs` up to fed221a.
  - Private stay: the 47 later commits or commits of other branches, among them the plate and own-images tools with
    their Gaia queries and their tags (`plates-core-*`, `own-images-*`, `etno-tier2-v1`).
  - Since e5, `tools/export_timelapse.py`, `tools/publish_scan.py`, the proposals of the data package and the first
    version of this list lie before the tip e83d960 and are published with it.
  - Also private: everything after the tips, such as the e5 entry in `tools/notary`, `tools/long_eval.py` and this
    version of the list, until it is published separately.
- **Existing tags in the published part:** `bb2021-criteria-draft-1` (224b7a1, named in e3), `make-ic-v1`,
  `prod-eval-v1`. They are published with it.

## Checks done (2026-11-04)

They covered the tips of 2026-11-04. The tips of e5 are not scanned yet; step 4 of the order below scans the
final state anyway.

- **gitleaks** v8.18.4 (built from source through the Go module proxy, checked against sum.golang.org), over the
  whole history (`--log-opts=--all`, 264 commits): **no leaks found**.
  - A control repository with three planted keys gave 2 findings, so the scanner works.
- **`tools/publish_scan.py --history`:** no secrets, no Gaia data.
  - Over the trees of the three tips and of `main`: 0 blocking findings.
  - Reported, and published unchanged by decision: the host name `appmdp-05`, the home path in
    `environment.txt` and the GPU UUID in the acceptance report.

## Order of the publication (decision of 2026-11-04)

1. Enter e4, e5 (the criteria of the paired tests), then e6 (the data package). e4 and e5 are on chain (#5, #6).
2. Regenerate this list with e6 (`tools/notary_refs.py`; e4 is in it since 2026-11-04, e5 since 2026-11-10).
3. **Only right before the push:** `main` is brought to the state of the campaign by a merge commit of the tips. This
   is a new commit, not a rewrite. Then the tags of the list are set.
4. Both scans over exactly the state to be published, that is `main` after the merge plus the tags:
   - gitleaks over their history;
   - `tools/publish_scan.py --git` over each tree, and over the history of that state.
5. Push `main` and the tags; nothing else.

Until then: no merge into `main`, no tags, no push.
