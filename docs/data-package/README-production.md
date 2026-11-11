# MEDAS Planet Nine search: production run p9prod-9a084ed (draft README of the record)

**Status:** draft for the data package (`docs/data-package-e6.md`), not uploaded. Placeholders in square brackets.

N-body run of the Planet Nine of the posterior of Brown & Batygin (2021) (6.2 Earth masses, a 380 au, q 300 au,
i 16°), with Jupiter–Neptune from JPL DE440s and 64,000 massless test bodies, over 0–4 Gyr. Integrator p9gpu v5
(Wisdom–Holman, democratic heliocentric coordinates, dt 0.5 yr, smooth close-encounter sub-steps, FP64), on an NVIDIA
A100. Not peer-reviewed. Planet Nine is a hypothesis.

## What is in the record

| file | content |
|---|---|
| `MANIFEST.sha256` | sha256 of every file inside every tar, of the tars and of the top files; its own sha256 is in entry e6 |
| `notary.tar` | the manifests of the notary entries a3, e2, e3, e4, e5 and r1, the files without git of r1, and the OpenTimestamps proofs |
| `code.tar` | the source of medas-p9-search at the result commit, and the run package `p9prod-9a084ed.tar.gz` with its sha256 |
| `evaluation.tar` | `result.json`, `timeseries.csv`, `report.txt` and `environment.txt` of the evaluation (`tools/prod_eval.py`) |
| `runs-production.tar` | the run directory as the package wrote it: per segment `input.sa`, `output.sa`, `final.state`, `flybys.tsv`, `removed.tsv`, `result.txt`, `DONE`; `segments.tsv`; logs |
| `checks.tar` | the checksum list of all 517 result files, timestamped before the evaluation, with its `.ots` |

## How to verify (three steps)

1. **The record is the registered one:** `sha256sum MANIFEST.sha256` equals the value in entry e6 ([transaction,
   block]).
2. **The files are complete and unchanged:** `python3 -I tools/pack_record.py verify .` (from `code.tar`) checks every
   line of the manifest, including the files inside the tars.
3. **A segment recomputes to its hash:** unpack the package from `code.tar` and one segment from
   `runs-production.tar`. Run `bin/p9gpu run input.sa <t_end> 10 out.sa out.state` with the settings of `params.env`,
   on a CUDA GPU or with the CPU twin (`P9GPU_MODE=cpu`). The printed `result_sha256` equals the one in `DONE` and
   `segments.tsv`.

## Criteria and results

- **Criteria, fixed before the run:** entry e3 (chain entry #4 on medasdigital-2), `docs/production-criteria.md`.
- **Result:** entry r1 (#7), `docs/production-result-20261110.md` (version 3).
  - Decided (subset scatter 1.41°).
  - Over 1–4 Gyr: M1 154.1°, M2 0.076, M3 1.5°, M4 155 au, M5 135°.
- **Limits:** gravity of the Sun and the planets only (no galactic tide, no passing stars), massless test bodies, no
  observational bias. The comparison with MERCURIUS covers 0–200 Myr, and over 4 Gyr only the strength up to about
  1–2 Gyr (long-run report).

## Methods and tools

[Wording to be agreed with the author: an AI coding assistant (Claude, Anthropic) wrote and revised code, tests,
packages and documents under the direction of the author. The author made the scientific decisions. Every result
rests on deterministic programs and their tests. The criteria were notarised before the runs.]

## Licences and citation

- Data and documents: CC BY 4.0 (`LICENSE-DATA.txt`).
- Code and packages: GPL-3.0-or-later, including REBOUND 5.2.2 in source (`LICENSE-CODE.txt`).
- Planet start states from JPL DE440s (not included).
- Cite as in `CITATION.cff`: Janßen, E. (MEDAS Computers GmbH), [year], [DOI].
