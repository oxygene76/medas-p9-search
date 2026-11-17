# Comparison with Brown & Batygin 2021: the outcome over sets A and B (2026-11-17)

**Status:** result report, for independent review. The outcome is not final before that review. Nothing goes into the
research note, onto the website or into a notary entry before it. Planet Nine is a hypothesis; this file reports
whether our method reproduces the published simulations of that hypothesis, nothing about whether the planet exists.
- **Criteria:** `docs/bb2021-comparison-criteria.md` section 6, as entered with entry e4 (#5).
- **Steps:** `docs/sets-evaluation-procedure.md` (12ab70b).
- **File:** `docs/sets-outcome-20261117/outcome.txt`, written by `tools/prod_eval.py --outcome` from the two
  `result.json` (commit 28bfcc6).
- **The sets:** `docs/sets-result-A-20261117.md`, `docs/sets-result-B-20261117.md`.

## Outcome

**Outcome 4, "No cluster"** (condition: M2 < 0.20 in at least one set). Here it holds in both sets:

| | set A | set B |
|---|---|---|
| verdict (section 5) | does not agree | does not agree |
| M2 strength (≥ 0.20 for a cluster as in B&B) | 0.050 | 0.127 |
| M1 direction (160–200°) | 127.3°, every subset outside | 166.7°, every subset within |
| M3 pole (±30°) | 3.2° | 18.0° |
| M4 wall, A only (226–286 au) | 165 au | – |
| subset scatter of M1 (limit 10°) | 6.5° | 0.4° |

**Why the other outcomes do not apply:**
- **Outcome 1 (agreement)** needs both sets to agree; neither does.
- **Outcome 2 (one set agrees)**: neither does.
- **Outcome 3** needs M2 ≥ 0.20 with M1 outside 160–200°; M2 is below 0.20 in both.
- **Outcome 5 (not decided)**: both runs are complete to 4 Gyr, both subset scatters are below 10°, and the
  prerequisites were met (each set released by its paired test, e5).

The tool writes `4. No cluster (M2 below 0.20 in at least one set)`.

## What section 6 fixes for this outcome

Unchanged from the criteria (row 4):
> Contradicts Fig. 1 or Fig. 3 for that set. mercury6 counter-run of set A: does mercury6 show a cluster, it is a
> problem of p9gpu or of our setup, and the production run is held; does it show none either, it is a discrepancy with
> the published results. It is reported with this file and B&B are asked about the details of their runs.

**Together with the decision of 2026-11-13** (research note, ba5a62f): the mercury6 counter-run follows as an announced
addendum, with its own criteria entry on medasdigital-2 before the run.

**The production run:**
- Its 1–4-Gyr result can be compared with B&B only after outcome 1. That is not reached.
- It is not read as the long-term behaviour of B&B's Planet Nine with our method.
- Whether it is held depends on the mercury6 counter-run: it is held if mercury6 shows a cluster.
- Until then its result stands as computed and reported (`docs/production-result-20261110.md`), with its limits, and
  without the comparison with B&B.

## Assessment (not part of the criteria, decides nothing)

- **What is already checked:** The paired tests showed that p9gpu v5 and MERCURIUS give the same clustering statistic
  for both sets over 0–200 Myr, within ±0.035 (`docs/paired-result-A-20261112.md`, `docs/paired-result-B-20261113.md`).
  The long runs 110–112 found no growing bias up to 1 Gyr clearly, 2 Gyr limitedly; 4 Gyr was not testable.
- **What remains open:** a difference of the integrator over 1–4 Gyr, and the differences of setup that section 6 names
  for outcome 3 and the research note lists: the inner planets merged into the Sun, removal, the frame.
- **The variants** of the frame and of the elements were reported for both sets and do not change the picture.
- **This is exactly what the mercury6 counter-run of set A is to separate.** No further evaluation of these runs was
  made before this outcome, and none is made outside an announced addendum.

**Limits that still apply:**
- one realisation of each set;
- the B&B values read from figures;
- the model without galactic tide, passing stars or observational bias (B&B likewise name no tide);
- the late clustering strength cannot be checked conclusively against MERCURIUS over 4 Gyr.

## What follows, for the project lead's decision

1. **Independent review** of this file and of the two set reports.
2. **Only then, with the project lead's go:**
   - the notary entry r2, `result` referring to e4 (#5), with outcome 4;
   - B&B asked about the details of their runs, as section 6 requires;
   - a dated addendum with the criteria of the mercury6 counter-run of set A, entered before the run.
3. **The environment stays as it is:** libc6/libc-bin stay held on the GPU server, so that a counter-run can compute in
   the same environment (stage 8 of the guide).
4. **Website and research note:** not before the review. The content for 2026-11-24 has to state outcome 4 instead of
   an agreement.
