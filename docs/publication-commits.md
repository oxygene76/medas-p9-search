# Commits and tags for the publication of medas-p9-search (2026-11-04)

Decision of 2026-11-04: published are `main` and every commit and tag that the notary entries refer to. All other
branches stay private. The history stays unchanged, so the notarised documents are published as they were entered.

This list was made with `tools/notary_refs.py` from the manifests:
- a3 (entry #2), e2 (entry #3) and e3 (block 10723643);
- e4, which is prepared but **not yet on chain**: its commits are published only once it is entered.

It is to be regenerated after e4, and after e5 (the data package):

```sh
build/venv/bin/python -I tools/notary_refs.py "a3 (#2)=runs/notary/manifest-a3-validation-status-20261021.json" \
  "e2 (#3)=runs/notary/manifest-e2-equivalence-20261023.json" "e3=runs/notary/manifest-e3-production-20261104.json" \
  "e4=runs/notary/manifest-e4-bb2021-v2-20261104.json" --pending e4
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
| `9a084ed45240` | 2026-10-21 | a3 (#2): named; e2 (#3): named; e3: files, named | no | feat/bb2021-setup, feat/cause-package, feat/equiv-packages, feat/long-runs | – | `notary-a3-9a084ed` |
| `c2eef152a2bf` | 2026-10-21 | a3 (#2): files, named, repository medas-p9-search-bb2021 | no | feat/bb2021-setup, feat/cause-package, feat/equiv-packages, feat/long-runs | – | `notary-a3-c2eef15` |
| `93059e9a4d80` | 2026-10-21 | a3 (#2): files | no | feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot | – | `notary-a3-93059e9` |
| `573aca883a5a` | 2026-10-21 | a3 (#2): files, named, repository medas-p9-search | no | feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot | – | `notary-a3-573aca8` |
| `69b84122c16f` | 2026-10-22 | e2 (#3): files, named, repository medas-p9-search-bb2021 | no | feat/bb2021-setup | – | `notary-e2-69b8412` |
| `47c7381774e2` | 2026-10-22 | e2 (#3): files, named, repository medas-p9-search-equiv | no | feat/equiv-packages, feat/long-runs | – | `notary-e2-47c7381` |
| `c45833a6e5ec` | 2026-10-23 | e2 (#3): files, named, repository medas-p9-search; e3: files, named | no | feat/new-etnos, feat/own-images, feat/pilot, feat/plate-pilot | – | `notary-e2-c45833a` |
| `224b7a1fe960` | 2026-11-01 | e3: named | no | feat/pilot | bb2021-criteria-draft-1 | `notary-e3-224b7a1` |
| `ae26a3e5b795` | 2026-11-04 | e3: named | no | feat/bb2021-setup | – | `notary-e3-ae26a3e` |
| `801fb20a295c` | 2026-11-04 | e3: files, named, repository medas-p9-search-bb2021; e4 (pending): files, named, repository medas-p9-search-bb2021 | no | feat/bb2021-setup | – | `notary-e3-801fb20` |
| `730260738c20` | 2026-11-04 | e3: files, named, repository medas-p9-search | no | feat/pilot | – | `notary-e3-7302607` |
| `ac47329bb463` | 2026-11-04 | e3: files, named, repository medas-p9-search-equiv | no | feat/long-runs | – | `notary-e3-ac47329` |
| `1c5f2ba23d57` | 2026-11-04 | e4 (pending): files, named, repository medas-p9-search | no | feat/pilot | – | `notary-e4-1c5f2ba` |
| `5b05cc3c72b0` | 2026-11-04 | e4 (pending): files, named, repository medas-p9-search-equiv | no | feat/long-runs | – | `notary-e4-5b05cc3` |

Tips (each referenced commit is one of these or an ancestor of one):
- `801fb20a295c` 2026-11-04 docs/speed-comparison-appmdp-05.md: the speed comparison on appmdp-05 (142 runs, all with
- `1c5f2ba23d57` 2026-11-04 bb2021-comparison-criteria.md addendum 16 (2026-11-04, after entry 3, before any run): th
- `5b05cc3c72b0` 2026-11-04 bb/: the V2 short runs with 16,000 test particles per set (addendum 16), README and expec

Closure: main and the referenced commits with all their ancestors are 216 of 264 commits; 48 stay private.
Existing tags in the closure: bb2021-criteria-draft-1, make-ic-v1, prod-eval-v1; outside: etno-tier2-v1, own-images-criteria-v1, own-images-criteria-v2, own-images-v1, plates-core-v1, plates-core-v2, plates-core-v3, plates-core-v4, plates-core-v5, plates-core-v6, plates-core-v7, plates-core-v8.

## What this means

- **No referenced commit is on `main`.** `main` holds only the first commit (e38179b). Branches stay private, so the
  referenced commits can only be published as tags. The proposed names are in the last column: one tag per
  referenced commit, after the first entry that refers to it.
  - The three tips alone would make all 18 reachable.
  - One tag each makes them easy to find from the manifests.
- **A published commit publishes its ancestors.** `main` and the 18 commits with their history are 216 of 264
  commits. That includes parts of the branches that otherwise stay private, as far as they lie before a referenced
  commit: `feat/pilot` up to 1c5f2ba, `feat/bb2021-setup` up to 801fb20, `feat/long-runs` up to 5b05cc3.
  - Private stay: the 48 later commits or commits of other branches, among them the plate and own-images tools with
    their Gaia queries and their tags (`plates-core-*`, `own-images-*`, `etno-tier2-v1`).
  - Also private: everything after the tips, such as `tools/export_timelapse.py`, `tools/publish_scan.py` and this
    list, until it is published separately.
- **Existing tags in the published part:** `bb2021-criteria-draft-1` (224b7a1, named in e3), `make-ic-v1`,
  `prod-eval-v1`. They are published with it.

## Checks done (2026-11-04)

- **gitleaks** v8.18.4 (built from source through the Go module proxy, checked against sum.golang.org), over the
  whole history (`--log-opts=--all`, 264 commits): **no leaks found**.
  - A control repository with three planted keys gave 2 findings, so the scanner works.
- **`tools/publish_scan.py --history`:** no secrets, no Gaia data.
  - Over the trees of the three tips and of `main`: 0 blocking findings.
  - Reported, and published unchanged by decision: the host name `appmdp-05`, the home path in
    `environment.txt` and the GPU UUID in the acceptance report.

## Still to decide before the publication

- Whether `main` should show the state of the campaign. A merge of the three tips into `main` is a new commit, not a
  rewrite; it would publish nothing beyond the closure above. Without it, `main` stays at the first commit and
  everything is reached through the tags.
- Repeat both scans right before the push: gitleaks over the closure, `publish_scan.py` over the tag trees.
