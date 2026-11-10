# Data package and entry e6: structure and metadata (draft, 2026-11-10)

This file builds on `docs/data-package-proposal.md`, whose decisions of 2026-11-04 apply unchanged: CC BY 4.0, one
record per campaign, flyby logs, no Gaia data, history unchanged. It adds three things:
- the concrete records, with the sizes measured on the verified result archives;
- the content of entry e6;
- drafts of the metadata files.

Nothing is uploaded and nothing is entered. The package is built only after the evaluations (no result before its
evaluation).

## 1. Records

One Zenodo concept per campaign. Sizes are the unpacked result directories as checked on the laptop.

| record | content | state | size (data) |
|---|---|---|---|
| `production` | p9prod-9a084ed: 40 segments, 517 files, evaluation of `prod_eval.py` | complete, evaluation pending | 1.6 GB, of it 0.06 GB flyby logs |
| `long-110-112` | p9long-v5-ac47329 (3 jobs × 40 segments) and p9long-merc-ac47329 (24 slices × 200 segments), evaluation of `long_eval.py` | complete, evaluation pending | 0.16 GB + 0.38 GB, 1,188 + 28,987 files |
| `bb2021-sets` | V2 short runs (p9bbv2-5b05cc3), the paired tests of sets A and B (p9pair-v5, p9pair-merc), sets A and B (p9bbsets-5b05cc3) if released | V2 done; paired tests running; sets open | V2 0.015 GB; the rest to be measured |
| `equivalence` (proposed) | the equivalence runs WH, V5 and M of 2026-10-22 with the result of entry e3 | evaluated | 1.7 GB |
| software | medas-p9-search at the evaluation commit (a separate Zenodo software record, GPL-3.0-or-later) | after the repository is public | small |

- **The equivalence record is new here** (decision needed, section 5). The proposal of 2026-11-04 covers only the runs
  of e3 and e4. The equivalence runs are what the choice of v5 rests on, and their checksum list is anchored in
  Bitcoin block 974272.
- **Many files per record.** MERCURIUS has 28,987 files. Each record keeps the uncompressed tar per part (proposal
  section 2), so Zenodo sees about 10 files per record.

**Layout of a record** (as the proposal, section 2, with the parts that exist now):
```
medas-p9-search-<campaign>-1.0.0/
  README.md  CITATION.cff  LICENSE-DATA.txt  LICENSE-CODE.txt  MANIFEST.sha256
  notary.tar        notary/<entry>/{manifest.json, files without git, receipt-public.json}, timestamps/*.ots, criteria/*.md
  code.tar          medas-p9-search-<commit>.tar.gz, packages/<package>.tar.gz + .sha256
  evaluation.tar    evaluation/<run>/{result.json, timeseries.csv, report.txt, environment.txt}
  runs-<run>.tar    the run directory as the package wrote it (paths unchanged)
  checks.tar        checksum lists of the results with their .ots; the reproduction p9repro (RESULT/, run.log)
  web.tar           exports of export_timelapse.py (only with a complete result.json)
  hardware.tar      speed comparison; A100 acceptance report without serial number, UUID and process list
```
- **`receipt-public.json`** holds the parts of a receipt that are public after the reveal: entry number, height, tx,
  commitment and the reveal. It never contains a salt of an entry that is not revealed.
- **Logs** go in only after `tools/publish_scan.py`: host names, addresses and user names are replaced by placeholders,
  and the README notes it. The V5 run directory holds the GPU UUID in the file `gpu-uuid` (its `run.log` does not);
  that file is replaced by a placeholder too.

## 2. Entry e6

- **Type and reference:** type `job`, refers to e5 (#6). Its text names e3 (#4) and e4 (#5), whose runs it covers.
- **When:** after all evaluations of the records it covers, after the DOIs are reserved, and before the upload.
- **Manifest** (`tools/manifest.py`), listing by sha256:
  - `MANIFEST.sha256` of each record;
  - every `segments.tsv` (the result hashes of all segments);
  - every `result.json` of the evaluations;
  - the checksum lists of the results and the reproduction verdict;
  - the README and `CITATION.cff` of each record, which contain the DOI.
- **Commits:** the evaluation commit of medas-p9-search, plus those of medas-p9-search-bb2021 and -equiv at which the
  packages were built.
- **Also:** OTS stamp of the manifest. The publication list is regenerated with e6 (`docs/publication-commits.md`
  step 2).

**If the paired tests or sets A and B take longer:** e6 can cover the production run and the long runs first. A
later e7 then covers `bb2021-sets` in the same way. Decision needed (section 5).

## 3. Metadata drafts

In `docs/data-package/`:
- **`zenodo-production.json`:** the Zenodo deposit metadata of the production record, with placeholders. It has:
  - creator Eike Janßen, MEDAS Computers GmbH, ORCID to follow;
  - CC BY 4.0, version 1.0.0;
  - the model limits, the three-step verification and the methods section with the use of AI tools (wording to be
    agreed);
  - related identifiers: the software record, the long-run record, Brown & Batygin 2021, REBOUND and DE440. Their
    DOIs are to be checked before the upload.
- **`CITATION.cff`:** the template for every record.

The other records follow the production one: title and description of their campaign, and the related identifiers
pointing at each other.

## 4. Steps (as the proposal, section 3)

1. Evaluations done and committed with their result reports.
2. Reserve the DOIs (Zenodo drafts, not published) and write them into README and `CITATION.cff`.
3. Pack each record; `tools/publish_scan.py` over every file; `MANIFEST.sha256`; `tools/manifest.py verify-tar`
   (still to be written).
4. Enter e6, stamp its manifest, and regenerate the publication list.
5. Publish the repository (`docs/publication-checklist.md`), then make the software record.
6. Upload the files unchanged and publish the records. Reveal of the entries after the publication.

## 5. Decisions needed

1. An `equivalence` record: yes or no.
2. One e6 for everything, or e6 for the production run and the long runs and a later e7 for sets A and B.
3. The ORCID, and the wording of the methods section (AI tools).
4. A Zenodo community for the project (name).
5. The reveal of entries a3–e6: right after the publication, or with the research note.
