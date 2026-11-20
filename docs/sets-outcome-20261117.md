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
1. **Measurement of the figures of 2021** (2026-11-17: `bb2021-abbildungen-messung.md`, SHA-256
   `ba1a449a5abaec798bb0acd88ec4b1fb338bebfd13c078dc5d6303a4b07926e5`, with `bb2021-abbildungen-messung.csv`, SHA-256
   `007b1e7ef54092cefce5e22ecfcfb1a05aeee107979bd8665bab698bdad88da9`, and `bb2021_abbildungen_messung.py`, SHA-256
   `ab7191f9c3c63d7a3fa2218c504a813d02646dbb0ddb217d3fbfc2f26b234702`; recomputed independently from the PDF):
   - inside the wall the runs equal the figures: 0.074 against 0.086 (set A, 150–230 au), 0.075 against 0.075 (set B,
     150–190 au);
   - beyond the wall the figures show R 0.60–0.61 (Fig. 3, third panel, 270–700 au) and 0.51–0.52 (Fig. 1,
     230–700 au), the runs 0.10 and 0.15 over the same ranges. The two values per figure come from two readings of the
     colour scale (empirical and gamma), not from different ranges.
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

4. **Fig. 4 of 2021** (measurement of 2026-11-17, `bb2021-abb4-messung-20261117.md`, SHA-256
   `6209a499dad91728d46a6d6ad1723a09cf19dc1fc81df529daba1a4c94db94fa`; recomputed independently from the PDF):
   - Its caption states the selection: "pole positions of KBOs with a > 150 AU and q > 42 AU", with no cut in
     inclination and no upper limit in q.
   - **The panel i9 = 15°** (m9 7, a9 500, e9 0.33) holds about 0.92–0.94 of the pole density below 30° (prograde, up
     to 72°), with a smooth profile through 40°.
   - **Set A** (i9 = 17°) holds 0.57–0.62 below 30° for all of q > 42 au, and 0.77–0.79 for 42 ≤ q ≤ 100 au (the range:
     with or without folding retrograde poles onto the disk).
   - The runs therefore contain clearly more highly inclined particles than Fig. 4.
   - **What this weakens:** the explanation "only the selection of the particles drawn" is not shown. Whether the
     simulated populations themselves differ is open.

5. **Spread over the four subsets of set A** (`docs/sets-decomposition-addendum-3-20261117.md`, 03fcad1; written
   after its computation, said so there):
   - M2 per subset 0.046–0.056 (whole set 0.0496); the inclination shares agree within 0.004.
   - This is the basis of the tolerance band of the run BB-A-rin1 (`docs/bb-a-rin1-criteria.md`, entry e6, #9):
     twice the largest deviation of a subset, M2 ± 0.012, each share ± 0.008, retrograde ± 0.022 (q > 42 au) and
     ± 0.011 (42 ≤ q ≤ 100 au).
6. **Weighted reading of Fig. 4, and bounds for BB-A-rin1** (`docs/sets-decomposition-addendum-4-20261118.md`,
   22f70fd, timestamped before the computation; result `docs/sets-decomposition-4-20261118.md`, 2ee681c):
   - **The method:** the particles weighted as the likelihood of the paper selects simulated objects (pp. 9–10:
     a and q kernels around the 10 objects of Table 1, q ≥ 42 au).
   - **Set A gives 0.761 below 30°, against 0.92–0.94 in Fig. 4** (panel i9 = 15°). By the scale fixed before:
     **"the reading does not fit"**. Set B gives 0.844, for information.
   - **R beyond the wall with the q weighting:** 0.274 (A, 260–700 au) against 0.60–0.61 (Fig. 3, third panel,
     270–700 au); 0.467 (B, 200–700 au) against 0.51–0.52 (Fig. 1, 230–700 au). The runs use the ranges of addendum 2,
     the figure values those of their measurement (observation 1).
   - **The removal cadence:** MERCURIUS (p9sim) removed with the same rule and cadence as p9gpu (r < 4.5 au and
     r > 10,000 au every 1000 steps). The comparisons of V5 with MERCURIUS therefore say nothing about the cadence.
   - **Bounds for BB-A-rin1** (set A without the particles whose q was ever below X at a snapshot):
     - X = 10 au leaves M2 0.051 and R beyond the wall 0.098;
     - X = 30 au gives M2 0.131, M1 154.5° and R 0.166, still below M2 0.20 and outside 160–200°.
     - The bound holds under one stated assumption: a dip below 4.5 au between two snapshots shows q < X at one of them.
   - **The prediction fixed in the criteria before the run:** most likely "the removal rule is not the cause".

**The literature:**
- **The groups at high q and high inclination are described:**
  - Batygin et al. 2019 (section 5.1, Fig. 14) keep them apart and compute the confined fraction only from the observable
    group;
  - Khain et al. 2018, Shankman et al. 2017 and Clement & Kaib 2020 report surviving high-inclination, circulating or
    high-perihelion particles.
- **Bansal, Brunton, Batygin, Pichierri & Nesvorný 2026** (Icarus 460, 117248, doi:10.1016/j.icarus.2026.117248,
  peer-reviewed; read from the arXiv version 2607.15646v1 on 2026-11-18, the pages below are those of that version):
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
  - **Selection (b) of addendum 2** (42 ≤ q ≤ 100 au, i < 40°) is a similar selection, not the same: a beyond the
    wall up to 700 au instead of a ≥ 250 AU, R per 10-au bin instead of κ of the whole selection, 1–4 Gyr instead of
    the last Gyr.
- **Highly inclined and retrograde particles in the authors' own work** (read from the PDFs on 2026-11-18):
  - **Batygin & Morbidelli 2017** (section 5.2, p. 13): "in our simulation, 38% of all stable objects experience at
    least one such excursion" to high inclination.
    - Their model: m9 10 M⊕, a9 700 AU, e9 0.6.
    - All four giant planets, Neptune included, are only a J2 moment of the Sun, with an absorbing radius of 20 AU.
    - Particles start with q 30–36 AU, a half-normal of σi = 5°.
  - **Batygin et al. 2019** (section 5.4, p. 57): the solution with e9 = 0.25 "produces retrograde TNOs in much greater
    proportions than its lower eccentricity counterpart". Fig. 23 shows this for m9 5 M⊕. The text attributes it to
    an octupolar term, which needs a significant eccentricity.
  - **Clement & Kaib 2020** (Table 4, p. 6; Planet Nine of 2019, 5 M⊕, 500 au, e 0.25, i 20°): only 0.06–0.24 of the
    particles are still "detectable" (q < 100 au) after 4 Gyr.
  - **Bansal et al. 2026** (above): inclination pumping is essential to the mechanism.
- **What is open:**
  - These papers describe a considerable share of highly inclined and retrograde particles, growing with e9.
  - Fig. 4 of 2021 (e9 0.33) shows hardly any at q > 42 au: 0.92–0.94 of the pole density below 30° in the panel
    i9 = 15°.
  - How the two fit together is open.
  - **What the paper says about Fig. 4:** Its caption names no weighting and does not say how retrograde poles are
    drawn. The text (p. 12) weights the pole distributions of the likelihood with a and q, but does not say whether
    Fig. 4 shows these.
  - The weighted reading, tried in addendum 4, does not fit for set A (observation 6).
  - No judgement on the paper.
- **Not shown:** that the figures of 2021 were built with the cuts of 2019. The text of 2021 states a > 150 au and
  q > 42 au "for both the data and for the simulations", and the captions of Figs. 1 and 3 give no further selection.
- **Fig. 4 speaks against an inclination cut:** It names q > 42 au and shows no cut. The research note
  `recherche-population-jenseits-der-wand-20261117-v2.md` (SHA-256
  `5cdf46647ab3c31af53cf8b4c46a06c3a4c80d1318aaf57fd093002c173a73b7`), which read Fig. 4 as a hint at cuts, is
  superseded on this point.

**What this means:**
- Outcome 4 stays as fixed: no judgement on the paper and none on Planet Nine.
- The consequences of section 6 (mercury6 counter-run of set A, the production run not compared with B&B) are unchanged.
  The scope of the counter-run is set after these observations.

**Limits that still apply:**
- one realisation of each set;
- the B&B values read from figures;
- the model without galactic tide, passing stars or observational bias (B&B likewise name no tide);
- the late clustering strength cannot be checked conclusively against MERCURIUS over 4 Gyr;
- the package differs from the paper in some points: set B with i9 = 17° (Table 2 and section 4.3 of the paper; the
  caption of Fig. 1 says 16°), 64,000 test particles instead of 17,500 and 25,600, the test particles in the ecliptic
  frame instead of the plane of the giant planets (up to 1.6°), the integrator and time step, the cadence of the
  inner removal. All rows: `docs/bb2021-article-vs-package.md`.

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
5. **The run BB-A-rin1** (set A with the inner removal in every step):
   - its criteria are entered as e6: entry #9, block 10942017, 2026-11-18 16:12:49 UTC;
   - it runs since 2026-11-18;
   - it is evaluated by the entered criteria after its end, and the result is entered as r3. No date is set.
   - It changes nothing of outcome 4.
6. **Sources named by file and SHA-256** (decision of the project lead, 2026-11-20): the measurements and the research
   note above are named by file and SHA-256. They are not in this repository; they go into the data package.
