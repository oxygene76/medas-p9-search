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

**The outcome and its name:**
- "No cluster" is the name that section 6 of the criteria fixes for outcome 4. It applies to the population the
  criteria measure: S_BB, all particles with 150 < a < 1000 au and q > 42 au, through M2.
- **Set B:** A cluster in the direction 166.7° is present and stable over all four subsets (scatter 0.4°). Its strength,
  0.127, lies below the limit of 0.20.
- **Set A:** strength 0.050, direction 127.3°, wall 165 au. Three of its four judged measures are outside.

**Checked before the result:**
- **The paired tests:** p9gpu v5 and MERCURIUS give the same clustering statistic for both sets over 0–200 Myr, within
  ±0.035 (`docs/paired-result-A-20261112.md`, `docs/paired-result-B-20261113.md`).
- **The long runs 110–112:** no growing bias found; up to 1 Gyr clearly testable, 2 Gyr with limits, 4 Gyr not.

**Observations after the result** (exploratory, fixed and timestamped before each computation, but after the outcome):
1. **Measurement of the figures of 2021** (files of the Claude chat of 2026-11-17, recomputed independently from the
   PDF):
   - inside the wall the runs equal the figures: 0.074 against 0.086 (set A, 150–230 au), 0.075 against 0.075 (set B,
     150–190 au);
   - beyond the wall the figures show R 0.61 (Fig. 3, third panel) and 0.52 (Fig. 1), the runs 0.10 and 0.15.
2. **Decomposition** (`docs/sets-decomposition-20261117.md`, addendum 6130d44): verdict **"core present"** in both sets.
   - For 42 < q < 100 au and i < 30° the runs give R 0.63 (A) and 0.50 (B) beyond the wall.
   - In this subset R rises at about 260–280 au (A) and 190–210 au (B). That is where the figures place the wall: 256 au
     marked in Fig. 3, about 200 au in Fig. 1.
   - The weak clustering of all of S_BB comes with a large share of particles at q > 100 au or i > 30° beyond the wall,
     which show no cluster.
3. **The selection of Batygin et al. 2019** (`docs/sets-decomposition-2-20261117.md`, addendum 843438e):
   - Under their "observable" cut (30 ≤ q ≤ 100 au, i < 40°) the runs give beyond the wall R 0.55 (A) and 0.48 (B), and
     with only the 4-Gyr survivors 0.64 and 0.56. Verdict "cluster as in the figures".
   - Over all of q > 42 au: 0.10 and 0.15, "no cluster".
   - **One difference:** 2019 uses the last 2 Gyr, the addendum 1–4 Gyr, like the criteria.

4. **Fig. 4 of 2021** (measurement of the Claude chat of 2026-11-17, recomputed independently from the PDF):
   - Its caption states the selection: "pole positions of KBOs with a > 150 AU and q > 42 AU", with no cut in
     inclination and no upper limit in q.
   - **The panel i9 = 15°** (m9 7, a9 500, e9 0.33) holds about 0.92–0.94 of the pole density below 30° (prograde, up
     to 72°), with a smooth profile through 40°.
   - **Set A** (i9 = 17°) holds 0.57–0.62 below 30° for all of q > 42 au, and 0.77–0.79 for 42 ≤ q ≤ 100 au (the range:
     with or without folding retrograde poles onto the disk).
   - The runs therefore contain clearly more highly inclined particles than Fig. 4.
   - **What this weakens:** the explanation "only the selection of the particles drawn" is not shown. Whether the
     simulated populations themselves differ is open.

**The literature:**
- **The groups at high q and high inclination are described:**
  - Batygin et al. 2019 (section 5.1, Fig. 14) keep them apart and compute the confined fraction only from the observable
    group;
  - Khain et al. 2018, Shankman et al. 2017 and Clement & Kaib 2020 report surviving high-inclination, circulating or
    high-perihelion particles.
- **Bansal, Brunton, Batygin, Pichierri & Nesvorný 2026** (arXiv:2607.15646v1, preprint, read from the PDF on
  2026-11-18):
  - **Inclination pumping as part of the mechanism:** their introduction calls it "not merely incidental but essential
    to the Planet Nine mechanism". The interaction "acts to lift the perihelia of momentarily-inclined TNOs,
    potentially removing them from the observable domain".
  - **The clustering is measured on an observable selection** (section 3.2): a ≥ 250 AU, q ∈ (40, 100) AU,
    i ≤ 40°, "crude proxies for observability". Section 3.1 uses a ∈ (200, 2000) AU, q ∈ (40, 80) AU and i < 40°
    over the last Gyr, every 10 Myr.
  - **Their runs without cluster perturbations** are those of Batygin et al. 2019 (section 2.3). For the broader set
    they refer to Brown & Batygin 2021.
  - **What this supports:** the authors' group measures the clustering on the observable selection in 2019 and again
    in 2026, and describes the lifted, inclined particles as expected dynamics.
  - **What it does not say:** anything on how Figs. 1, 3 and 4 of 2021 were built.
  - **Selection (b) of addendum 2** (42 ≤ q ≤ 100 au, i < 40°) is close to their selection but not equal: a beyond
    the wall up to 700 au instead of a ≥ 250 AU, R per 10-au bin instead of κ of the whole selection, 1–4 Gyr instead
    of the last Gyr.
- **Not shown:** that the figures of 2021 were built with the cuts of 2019. The text of 2021 states a > 150 au and
  q > 42 au "for both the data and for the simulations", and the captions of Figs. 1 and 3 give no further selection.
- **Fig. 4 speaks against an inclination cut:** It names q > 42 au and shows no cut. The research note of the Claude
  chat (version 2), which read Fig. 4 as a hint at cuts, is superseded on this point.

**What this means:**
- Outcome 4 stays as fixed: no judgement on the paper and none on Planet Nine.
- The consequences of section 6 (mercury6 counter-run of set A, the production run not compared with B&B) are unchanged.
  The scope of the counter-run is set after these observations.

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
