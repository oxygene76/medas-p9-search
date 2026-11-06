# Publication data package (proposal of 2026-11-04, decisions of the same day)

The decisions of the project lead are in section 6; what is still open is marked there. It covers the structure, the checksums, the link to the notary entries, the licences and
the deposit on Zenodo. It applies to the runs fixed in entry e3: the production run, the paired long runs of seeds
110–112 (V5 and MERCURIUS) and, after entry e4, sets A and B of the comparison with Brown & Batygin (2021).

**When:** no result of these runs is published before its evaluation (decision of 2026-11-04). The package is built
after `tools/prod_eval.py` has evaluated every run over its complete length. The page "Simulations" follows the same
rule: `tools/export_timelapse.py` exports these runs only with a complete `result.json`.

## 1. What goes in

| Part | Content | Why |
|---|---|---|
| notary | per entry (a3, e2, e3, e4, e5 with the paired-test criteria, and the new e6 of §3): the manifest file, the files without `git` it lists (under the same path), the transaction, height, entry number, commitment, the reveal | anyone can check that the criteria and packages existed, unchanged, before the runs |
| timestamps | the OpenTimestamps proofs (`.ots`) of the stamped criteria and lists, upgraded to their Bitcoin block | a second, independent anchor |
| criteria | the criteria documents at the commits named in the manifests | what was fixed before the runs, readable without git |
| code | source archive of medas-p9-search at the evaluation commit; the run packages (`p9prod-9a084ed`, `p9long-v5-ac47329`, `p9long-merc-ac47329`, `p9bbsets-5b05cc3`, `p9bbv2-5b05cc3`) unchanged, with their binaries and sha256 files; REBOUND 5.2.2 as the source tarball already in the packages | rerun any segment and get its result hash |
| runs | per run: `job.json`, `params.env`, `input.sa`, `segments.tsv`, and per segment `output.sa`, `result.txt`, `removed.tsv`, `final.state`, `flybys.tsv`; the check output of the start (`check: ALL SAME`); the run log | the data themselves; every segment can be recomputed from its input |
| evaluation | per run: `result.json`, `timeseries.csv`, `report.txt` of `tools/prod_eval.py`, its version (tag), the outcome of sets A and B (`--outcome`) | the results, reproducible from the runs |
| web | the exports of `tools/export_timelapse.py` (manifest, `data.bin`, `curves.json`, `SOURCES.sha256`) | the pictures and curves of the page, tied to the source data by hash |
| hardware | the speed comparison (report, scripts, results); the acceptance test of the A100 only as its report, without serial number, GPU UUID and process list | context; not needed for checking |

**Flyby logs:** `flybys.tsv` goes in. The equivalence runs give 0.2 MB per segment of 4,000 bodies; the production run
gives about 3 MB per segment and about 0.1 GB in all.
- If a campaign gives more than 1 GB of flyby logs, only a summary goes in: per segment and planet the counts of the
  flybys (near, fast, close) and of the sub-steps.
- The sha256 of every original log is listed in `MANIFEST.sha256` and in entry e6, and the logs are kept.
- The V2 check (`tools/v2_encounter_check.py`) needs only the per-particle flags of 0–60 Myr. Those go in either way.

**No Gaia-derived data.** The package is CC BY 4.0; catalogues derived from Gaia do not go in.
- Checked on 2026-11-04 with `tools/publish_scan.py --history`, which covers every line ever committed, on every
  branch:
  - the repository holds no Gaia data;
  - Gaia appears only as a query in the plate and own-images tools (`tools/plates/fetch.py`, `tools/ownimg`, on their
    branches);
  - the results of those queries are under `runs/plates` and `runs/ownimg`, which git ignores and the package never
    takes.
- None of the parts of section 1 uses Gaia:
  - the start values come from DE440s and `tools/make_ic.py`;
  - the known objects of the page come from SBDB;
  - the IRAS/AKARI track and the Phan/DES check are not part of this package.
- `tools/publish_scan.py` runs over every file of the record before the upload and refuses Gaia columns, Gaia table
  names and files of those directories.

**Left out:** keys, receipts with salts of entries that are not yet revealed, `local.env`, logs with host names or
addresses (a log goes in only after a check for host names, IP addresses and user names; anything found is replaced by
a placeholder, and that is noted in the README), GPU serial numbers, the internal operations documents.

**Size (estimate, to be measured when packing):**
- An `output.sa` holds about 113 bytes per test body and snapshot (equivalence runs: 9.0 MB for 20 snapshots of about
  3,950 bodies).
- With about 60 % of the bodies alive on average and 400 snapshots, the production run and sets A and B take about
  1.7 GB each.
- Seeds 110–112 take about 0.2 GB (V5) and 0.3 GB (MERCURIUS); the packages take about 0.1 GB.
- **About 6 GB in all, up to 8 GB with the flyby logs.**

## 2. Structure

One Zenodo record per campaign, all under one concept (versions), in a community of the project:

```
medas-p9-search-<campaign>-<version>/
  README.md               what is where, how to verify, how to rerun one segment, the limits of the model
  CITATION.cff
  LICENSE-DATA.txt        CC BY 4.0
  LICENSE-CODE.txt        GPL-3.0-or-later (code, packages, REBOUND)
  MANIFEST.sha256         sha256sum lines of every other file of the record (inside the archives too, see below)
  notary.tar              notary/<entry>/..., timestamps/*.ots, criteria/*.md
  code.tar                medas-p9-search-<commit>.tar.gz, packages/*.tar.gz with their .sha256
  evaluation.tar          evaluation/<run>/{result.json,timeseries.csv,report.txt}, outcome.json
  web.tar                 web/<run>/{manifest.json,data.bin,curves.json,SOURCES.sha256}
  runs-production.tar     runs/production/...
  runs-long-110-112.tar   runs/V5-s110 ... runs/M-s112-part07 ...
  runs-set-A.tar, runs-set-B.tar
  hardware.tar
```

- **Uncompressed tar, one per part.** The archives of REBOUND compress poorly. tar keeps the paths of the runs and keeps
  the record below Zenodo's limit on the number of files (100 per record when last checked; the limit on size, 50 GB,
  is far away). Check both limits again at the time of the upload.
- **The paths inside the tar files are those of the run packages.** `runs/production/segments/seg017/output.sa` is the
  file the package wrote; `SOURCES.sha256` of the web exports and `segments.tsv` refer to them directly.
- **`MANIFEST.sha256` lists the files inside the tar files** (`runs-production.tar:runs/production/...`) as well as the tar
  files themselves. `tools/manifest.py` gets a mode `verify-tar` that checks both without unpacking to disk.

## 3. Checksums and the link to the notary entries

The chain, from the criteria to the published data:

1. **Before the runs:** entries a3 and e2 (validation, equivalence test) and **e3** (criteria of the production run and
   of seeds 110–112, the packages by sha256) are on chain, e3 at block 10723643 on 2026-11-04. **e4** (addendum 16, the
   packages of sets A and B) follows before set A. The manifests list every file by sha256; files without `git` are
   published under their path, as each manifest says.
2. **The runs:** every segment has a result hash (the sha256 of the final state) in `segments.tsv`. The packages are
   bit-reproducible, so the same input with the same binary gives the same hash on any machine; the README shows this
   for one segment.
3. **The evaluation:** `result.json` with the version of `tools/prod_eval.py`. Its tag `prod-eval-v1` exists since entry
   e3, which lists `tools/prod_eval.py` by sha256.
4. **A new entry e6 (type job, refers to e3, e4 and e5), before the upload:**
   - Its manifest lists `MANIFEST.sha256` of each record and the `result.json` files.
   - It also lists the sha256 of every `segments.tsv`, so the result hashes of all segments are fixed.
   - From this point the published data cannot be changed without notice.
   - The manifest of e6 is stamped with OpenTimestamps as well.
5. **On Zenodo:**
   - The description of the record gives the sha256 of `MANIFEST.sha256`, the entry e6 (transaction, height) and the
     entries e3 and e4.
   - The README explains the check in three commands: sha256 of the manifest equals the content of the entry; the
     files equal the manifest; one segment rerun gives its result hash.

Order:
1. Reserve the DOI on Zenodo (draft, not published) and write it into README and CITATION.cff.
2. Build `MANIFEST.sha256`.
3. Enter e6.
4. Upload the files unchanged and publish.

Since the DOI is reserved first, the README with the DOI is already in the manifest, and nothing changes after
entry e6.

## 4. Licences

- **Data** (runs, evaluation, web exports, notary files, documents): **CC BY 4.0** (decided).
- **Code and packages:** GPL-3.0-or-later, as the repository and as REBOUND, whose source ships unchanged in the
  packages.
- **Third-party data:**
  - The start values use the planets of JPL DE440s at JD 2458270.0. These are ephemeris values of NASA/JPL; they are
    cited in the README, and the ephemeris file is not included.
  - The four known objects of the page come from JPL SBDB and Horizons, are cited in the same way, and are not part of
    the data package.

## 5. Zenodo record (metadata)

| Field | Value |
|---|---|
| Resource type | Dataset |
| Title | MEDAS Planet Nine search: <campaign> (N-body runs, 0–4 Gyr), data and evaluation |
| Creators | Eike Janßen (ORCID to follow), affiliation MEDAS Computers GmbH |
| Description | what was computed and why; the model and its limits (no galactic tide, no passing stars, massless test bodies, no observational bias); status "not peer-reviewed"; how to verify; the notary entries; the methods, including the use of AI tools (see below) |
| Version | 1.0.0; later corrections as new versions of the same concept, never by changing files |
| Related identifiers | "is supplemented by": the software record of medas-p9-search (a separate Zenodo software record at the evaluation commit; the repository becomes public, section 7); "references": Brown & Batygin 2021 (AJ 162, 219), REBOUND (Rein & Liu 2012), DE440 (Park et al. 2021) |
| Keywords | Planet Nine; trans-Neptunian objects; N-body simulation; orbital clustering; reproducibility |
| Access | open; no embargo (publication only after the evaluation anyway) |
| Community | one community of the project for all records |

**AI tools in the description of the methods.** The README and the Zenodo description say how AI tools were used, in
a section "Methods and tools":
- an AI coding assistant (Claude, Anthropic) wrote and revised code, tests, packages and documents under the
  direction of the author;
- the author made the scientific decisions: criteria, thresholds, the order of the runs, evaluations;
- every result rests on the deterministic programs and their tests, not on the assistant;
- the criteria were fixed and notarised before the runs.

The wording is to be agreed with the author before the upload.

## 6. Decisions (2026-11-04)

1. Licence of the data: **CC BY 4.0**.
2. **medas-p9-search becomes public** for the publication, after a secret scan of the whole history and with private
   paths removed (section 7).
3. **One record per campaign.**
4. Flyby logs: **yes**; if large, only a summary and checksums (section 1).
5. Speed comparison: **yes**. The A100 acceptance test only as its report, without serial number and process list.
6. Author **Eike Janßen** (ORCID to follow), affiliation **MEDAS Computers GmbH**; AI tools in the description of the
   methods.
7. No Gaia-derived data in the package (checked, section 1).

8. **History unchanged** (option 7.1): the notarised documents stay as they were entered, and the publication says so.
   Before it, gitleaks also runs over the whole history (done 2026-11-04: no leaks).
9. **Published:** `main` and every commit and tag the notary entries refer to; the other branches stay private. The
   list: `docs/publication-commits.md`.

Still open: the ORCID; the wording of the methods section; whether `main` shows the state of the campaign
(`docs/publication-commits.md`).

## 7. Making the repository public

**Secret scan of the whole history (2026-11-04)**, `tools/publish_scan.py --history`: 262 commits, 15 branches,
every line ever added or removed.
- **Secrets: none.** No key blocks, service tokens, password or token assignments, mnemonics or salts.
- No file was ever committed that is named like a key, an `.env` or a receipt; `runs/` (with `runs/notary/local.env`)
  is ignored.
- A second, independent scanner (gitleaks over the history) is still to be run before publication; it is not
  installed here.

**Private details found** (reported, not secret):

| What | Where | Count |
|---|---|---|
| the internal host name `appmdp-05` | criteria, package and run documents, `a100/`, `speed/`, `long/*/EXPECTED-TIME.txt` | 51 lines in the history, 18 in `feat/pilot` |
| the home path `/home/medas/dev/medas/...` | `docs/equivalence-result-20261102/environment.txt` | 3 |
| the GPU UUID of the A100 | `docs/a100-acceptance-20261103.md` | 1 |
| the author's e-mail address | commit metadata | every commit |
| the words Proxmox / PBS, ollama | `docs/a100-acceptance-20261103.md` | 3 |

**The catch: many of these files are notarised.**
- Entry e3 lists by sha256 and git commit, among others:
  - `production-criteria.md`, `bb2021-comparison-criteria.md`, `equivalence-criteria.md`,
    `equivalence-evaluation-procedure.md`, `long-runs-110-112-criteria.md` and `production-package.md`;
  - `docs/equivalence-result-20261102/environment.txt`;
  - `docs/a100-acceptance-20261103.md`;
  - the run packages, whose `EXPECTED-TIME` names the host.
- Rewriting the history (git filter-repo) would change those files, so their sha256 would no longer match the entry.
  It would also change every commit id, so the `git show <commit>:<path>` of the manifests would fail.
- The entries would then be verifiable only from archived copies.

Options:
- **7.1 (recommended): keep the history unchanged.** Clean the files only from now on, in new commits: names replaced
  by "the GPU server", paths made relative, the UUID removed.
  - The notarised versions stay in the history as they are.
  - What they show is a host name inside the company network, a local user name and a GPU UUID: no access data and
    nothing reachable from outside.
  - The publication says so: the notarised documents are published unchanged by design.
- **7.2: rewrite the history.** This removes the details but breaks the notary chain from git, as above. Not
  recommended.
- **7.3 (open):** whether to publish all 15 branches or only `main` plus the branches that notarised commits lie on.
  Every commit named in a manifest must stay reachable.
  - Branches such as `feat/plate-pilot` and `feat/own-images` hold the Gaia query code (not data) and their own
    criteria.
  - Merging what belongs together into `main` and publishing `main` plus the notarised commits as tags would be
    tidier.

