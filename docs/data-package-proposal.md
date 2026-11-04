# Publication data package: proposal (2026-11-04)

A proposal, not yet decided. It covers the structure, the checksums, the link to the notary entries, the licences and
the deposit on Zenodo. It applies to the runs fixed in entry e3: the production run, the paired long runs of seeds
110–112 (V5 and MERCURIUS) and, after entry e4, sets A and B of the comparison with Brown & Batygin (2021).

**When:** no result of these runs is published before its evaluation (decision of 2026-11-04). The package is built
after `tools/prod_eval.py` has evaluated every run over its complete length. The page "Simulations" follows the same
rule: `tools/export_timelapse.py` exports these runs only with a complete `result.json`.

## 1. What goes in

| Part | Content | Why |
|---|---|---|
| notary | per entry (a3, e2, e3, e4, and the new e5 of §3): the manifest file, the files without `git` it lists (under the same path), the transaction, height, entry number, commitment, the reveal | anyone can check that the criteria and packages existed, unchanged, before the runs |
| timestamps | the OpenTimestamps proofs (`.ots`) of the stamped criteria and lists, upgraded to their Bitcoin block | a second, independent anchor |
| criteria | the criteria documents at the commits named in the manifests | what was fixed before the runs, readable without git |
| code | source archive of medas-p9-search at the evaluation commit; the run packages (`p9prod-9a084ed`, `p9long-v5-ac47329`, `p9long-merc-ac47329`, `p9bbsets-5b05cc3`, `p9bbv2-5b05cc3`) unchanged, with their binaries and sha256 files; REBOUND 5.2.2 as the source tarball already in the packages | rerun any segment and get its result hash |
| runs | per run: `job.json`, `params.env`, `input.sa`, `segments.tsv`, and per segment `output.sa`, `result.txt`, `removed.tsv`, `flybys.tsv`, `final.state`; the check output of the start (`check: ALL SAME`); the run log | the data themselves; every segment can be recomputed from its input |
| evaluation | per run: `result.json`, `timeseries.csv`, `report.txt` of `tools/prod_eval.py`, its version (tag), the outcome of sets A and B (`--outcome`) | the results, reproducible from the runs |
| web | the exports of `tools/export_timelapse.py` (manifest, `data.bin`, `curves.json`, `SOURCES.sha256`) | the pictures and curves of the page, tied to the source data by hash |
| hardware | the acceptance report of the A100 and the speed comparison, without serial numbers, host names and addresses | context; not needed for checking |

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
4. **A new entry e5 (type job, refers to e3 and e4), before the upload:**
   - Its manifest lists `MANIFEST.sha256` of each record and the `result.json` files.
   - It also lists the sha256 of every `segments.tsv`, so the result hashes of all segments are fixed.
   - From this point the published data cannot be changed without notice.
   - The manifest of e5 is stamped with OpenTimestamps as well.
5. **On Zenodo:**
   - The description of the record gives the sha256 of `MANIFEST.sha256`, the entry e5 (transaction, height) and the
     entries e3 and e4.
   - The README explains the check in three commands: sha256 of the manifest equals the content of the entry; the
     files equal the manifest; one segment rerun gives its result hash.

Order:
1. Reserve the DOI on Zenodo (draft, not published) and write it into README and CITATION.cff.
2. Build `MANIFEST.sha256`.
3. Enter e5.
4. Upload the files unchanged and publish.

Since the DOI is reserved first, the README with the DOI is already in the manifest, and nothing changes after
entry e5.

## 4. Licences

- **Data** (runs, evaluation, web exports, notary files, documents): **CC BY 4.0**. It is the Zenodo default and
  permits any reuse with attribution. CC0 would be the alternative if attribution should not be a condition; the
  recommendation is CC BY 4.0.
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
| Creators | the project lead (with ORCID, if there is one); MEDAS as the affiliation |
| Description | what was computed and why; the model and its limits (no galactic tide, no passing stars, massless test bodies, no observational bias); status "not peer-reviewed"; how to verify; the notary entries |
| Version | 1.0.0; later corrections as new versions of the same concept, never by changing files |
| Related identifiers | "is supplemented by": the software record of medas-p9-search (a separate Zenodo software record at the evaluation commit, if the repository is published); "references": Brown & Batygin 2021 (AJ 162, 219), REBOUND (Rein & Liu 2012), DE440 (Park et al. 2021) |
| Keywords | Planet Nine; trans-Neptunian objects; N-body simulation; orbital clustering; reproducibility |
| Access | open; no embargo (publication only after the evaluation anyway) |
| Community | one community of the project for all records |

## 6. Open points (decisions)

1. CC BY 4.0 or CC0 for the data.
2. Whether the repository medas-p9-search becomes public with its own software record, or only the source archive goes
   into the data record.
3. One record per campaign (proposed) or one record for all.
4. Whether the flyby logs (`flybys.tsv`, about 0.2 MB per segment of 4,000 bodies) go in. Proposed: yes, they are the
   basis of the V2 check.
5. Whether the A100 acceptance and the speed comparison go in at all (proposed: yes, without identifying details).
6. The author list and the ORCID.
