# Comparison with Brown & Batygin (2021) over the long time scale: criteria (draft)

Asked for by the project lead on 2026-11-01, as part of entry 3. **Draft. Nothing is run; computing needs the project
lead's release.**

This file fixes the following before any run:
- the parameter sets;
- the measures;
- the selection and the time window;
- the seeds and the numbers of test particles;
- the tolerances against the values of Brown & Batygin (B&B);
- what follows from each outcome.

The data of the equivalence test were not read for this file, and are not used by it.

Source: M. E. Brown & K. Batygin, *The Orbit of Planet Nine*, AJ 162, 219 (2021), arXiv:2108.09868v1. Page numbers
below are those of the arXiv version (26 pages; sha256 of the PDF
`347753be7daa59e52164c03c73dbbe33271ff2f69ccdfb0458502c06193835f8`). Section, figure and table numbers are the same
in the journal; its page numbers are not checked here.

## 1. What the paper gives, and what it does not

- **Posterior** (abstract, p. 1; §4.5, p. 16): m9 = 6.2 (+2.2 −1.3) Earth masses, a9 = 380 (+140 −80) au,
  i9 = 16 ± 5°, perihelion 300 (+85 −60) au, uniform prior in a9.
  - These are the start values of our test case and of the production run (`tools/make_ic.py`; e = 0.2105).
  - **The paper has no simulation with exactly these values.** The posterior is an MCMC over a Gaussian-process
    emulator of the likelihoods of 121 simulations (§4.4–4.5, pp. 12–16).
  - The nearest simulations in Table 2 (p. 23) list only a likelihood, no distribution:
    | m9 | a9 | i9 | e9 | ϖ9 | Ω9 | ℓ | Δℓ | particles |
    |---|---|---|---|---|---|---|---|---|
    | 6 | 380 | 17° | 0.20 | 242 | 110 | −174.1 | −1.2 | 25,600 |
    | 6 | 380 | 17° | 0.25 | 246 | 92 | −173.3 | −0.3 | 25,600 |
- **Simulations** (§4.1, p. 8):
  - all four giant planets plus Planet Nine;
  - 16,800–64,900 test particles, initially a 150–500 au, perihelion 30–50 au, i 0–25°, the other angles random;
  - mercury6, hybrid symplectic/Bulirsch–Stoer, step 300 days, reduced in close encounters;
  - removal at r < 4.5 au, r > 10,000 au and at collisions;
  - angles first in the initial plane of the giant planets, afterwards rotated to the orbital pole of Jupiter with
    the longitude zero point kept;
  - M9 = 0 at the start; ϖ9 and Ω9 are varied afterwards by rotating the frame.
- **Time window** (§4.2, p. 9): "The early times of the simulations contain a transient state that appears to
  reach something like a steady-state in orbital distribution after ∼1 Gyr. We thus discard these initial time
  steps and only include the final 3 Gyr in our analysis."
- **Selection** (§2, p. 4; recommended for later analyses on p. 7): 150 < a < 1000 au and q > 42 au, for the data
  and the simulations. The 11 observed objects are in Table 1 (p. 4).
- **Quantitative results per simulation** exist only as:
  - the likelihoods ℓ in Table 2 (pp. 22–25). They need B&B's bias function of the 11 objects (§3), which we do not
    have, so we cannot reproduce them;
  - density plots:
    - Fig. 1 (p. 5): a against Δϖ for the maximum-likelihood simulation;
    - Fig. 2 (p. 6): its pole positions;
    - Fig. 3 (p. 10): a against Δϖ for five simulations, with "wall" and cluster "width" marked;
    - Fig. 4 (p. 11): pole positions for i9 = 5–35°.
- **Statements** usable as checks:
  - the cluster lies about 180° from Planet Nine's perihelion (§1, p. 2; Figs. 1, 3);
  - the orbital planes of the distant objects follow that of Planet Nine for small i9 (§4.1, p. 8; Fig. 4);
  - more mass narrows the cluster and moves the wall inwards (Fig. 3 caption, p. 10);
  - "at the lowest masses the cluster appears double-peaked" (Fig. 3 caption).

**Three inconsistencies in the paper** (they matter for set B):
- The maximum-likelihood simulation is given with i9 = 16° in the Fig. 1 caption (p. 5), but with i9 = 17° in §4.3
  (p. 12) and in Table 2 (p. 22: m9 5, a9 300, i9 17, e9 0.15, ϖ9 254, Ω9 108, Δℓ = 0.0).
- The note to Table 2 (p. 25) places the maximum at m9 = 5, a9 = 310, i9 = 15, e9 = 0.10. That row has Δℓ = −2.2.
- §6 (p. 19) speaks of "the 200 Myr of our simulations", while §4.2 uses the final 3 Gyr.

This file follows Table 2 and §4.2–4.3.

## 2. The parameter sets

| set | m9 | a9 | i9 | e9 (q9) | ϖ9, Ω9 | source with results | B&B particles |
|---|---|---|---|---|---|---|---|
| **A** | 7 | 500 au | 17° | 0.33 (335 au) | 250°, 100° | Fig. 3, third panel (p. 10); Table 2 (p. 24): ℓ = −175.4, Δℓ = −2.5 | 17,500 |
| **B** | 5 | 300 au | 17° | 0.15 (255 au) | 254°, 108° | maximum-likelihood simulation: Fig. 1 (p. 5), Fig. 2 (p. 6), §4.3 (p. 12), Table 2 (p. 22) | 25,600 |

Why these two and not the posterior values (6.2 / 380 / 16°):
- Only for these sets does the paper show distributions that a long run can be compared with.
- A is the panel of Fig. 3 closest to the posterior in mass and inclination. It is the only set where the wall and
  the width are marked.
- B is B&B's best simulation.
- The posterior set is run anyway as the production run. Its long-term clustering is reported against the general
  statements of §1 and against the observed objects (§8). It is not judged against B&B values, because the paper
  has none for it (decision D1).

### Values read from Fig. 3, third panel (set A)

The page was rendered at 4× (2448 × 3168 pixels; pypdfium2). Positions were measured from the frame and the tick
labels:
- x: 100 au at pixel 589, 1000 au at 1789.5, so 1.333 px per au;
- y: each panel is 352 pixels for 360°.

The reading accuracy is about ±2 au and ±2° (line width).

| panel (m9, a9, i9, e9) | wall | width bar (lower to upper) | bar centre |
|---|---|---|---|
| 4, 500, 20°, 0.33 | 280 au | 99°–268° (169°) | 184° |
| 5, 500, 20°, 0.33 | 265 au | 104°–268° (164°) | 186° |
| **7, 500, 17°, 0.33 (set A)** | **256 au** | **124°–258° (134°)** | **191°** |
| 10, 450, 20°, 0.33 | 238 au | 141°–232° (91°) | 187° |
| 12, 500, 20°, 0.20 | 261 au | 142°–228° (86°) | 185° |

- The width bars sit at a ≈ 856–923 au.
- The paper does not define where a bar ends, or how the wall is placed: both are drawn by eye.
- For set B, Fig. 1 marks neither a wall nor a width.

## 3. Setup of the runs

The setup follows §4.1 of B&B, with three differences:
- the inner planets are added to the Sun;
- the integrator is p9gpu instead of mercury6;
- the elements are barycentric.

- **Massive bodies**:
  - the Sun with the masses of the inner planets, and Jupiter to Neptune from DE440s at JD 2458270.0, as in all
    runs;
  - Planet Nine with m9, a9, e9 of the set, M9 = 0, and ϖ9, Ω9 from Table 2;
  - **i9, Ω9 and ϖ9 refer to the invariable plane of Jupiter to Neptune**, as B&B's initial plane (p. 8), not the
    ecliptic. `tools/make_ic.py` cannot do this yet: prerequisite V1.
- **Test particles**: `make_ic.py --a-range 150 500 --q-range 30 50 --inc-range 0 25`, angles uniform.
- **Removal**: r < 4.5 au, r > 10,000 au, collisions with physical radii (as in the production package).
- **Integrator**: p9gpu FP64, dt = 0.5 yr, with an encounter treatment that has passed acceptance under
  `docs/acceptance-rules.md`. Today none has: the ensemble of `docs/validation-ensemble-200myr.md` did not pass, and
  the cause is still being searched. Prerequisite V2.
- **Output**: a snapshot every 10 Myr, from 0 to 4.0 Gyr (401 snapshots).

### Seeds and numbers of test particles

| set | seed | test particles | subsets for the scatter |
|---|---|---|---|
| A | 311 | 64,000 | 4 × 16,000 (particles 0–15,999, …) |
| B | 312 | 64,000 | 4 × 16,000 |

- The seeds are fixed here and used only for this comparison. Seeds used so far: 1, 2, 9, 21, 101–112, 201.
- 64,000 is 2.5 to 3.7 times B&B's numbers (17,500 and 25,600).
- The subsets do not interact, so they are independent runs for the test particles. Their scatter is the
  statistical error.
- The subsets share the planets' trajectory. Chaos in the planets is therefore not covered. B&B too have one
  realisation per set. The limitation is stated with the result.
- Expected precision: with about 40 % surviving at 4 Gyr (G201: 56 % at 820 Myr, `docs/night-20261024.md`) and
  about half of those in the selection, each subset holds about 3,000 selected particles. That gives a standard
  error of the mean direction of a few degrees per snapshot, far inside the tolerances of section 5.

## 4. Measures

Elements:
- barycentric osculating elements, as in `tools/analyze.py`;
- angles in the frame of Jupiter's orbital plane at the time of each snapshot, with the longitude zero point of the
  start frame, as B&B (p. 8). Prerequisite V3.

Selection S_BB: 150 < a < 1000 au and q > 42 au.

Window: the snapshots from 1.0 to 4.0 Gyr (301 snapshots).

| | measure | definition | judged |
|---|---|---|---|
| M1 | direction of the Δϖ cluster | circular mean of Δϖ = ϖ − ϖ9 over all particles of S_BB in all snapshots of the window (pooled) | A, B |
| M2 | strength of the Δϖ cluster | mean over the snapshots of the window of R, the mean resultant length of Δϖ in S_BB | A, B |
| M3 | direction of the mean pole relative to Planet Nine's | angle ψ of the pooled mean of (sin i cos ΔΩ, sin i sin ΔΩ), as in Fig. 2 (p. 6) | A, B |
| M4 | wall | from a in bins of 10 au (150–600 au), with R of Δϖ pooled over the window, R_plat = median R of the bins 400–700 au: the smallest bin centre from which R ≥ R_plat / 2 holds for it and the next 3 bins | A |
| M5 | width | the Δϖ interval at 850–950 au where the pooled, 10°-smoothed density is above half of its maximum | reported only |

Additionally reported, not judged:
- M1 to M3 per snapshot (the time series, to show swings or libration);
- heliocentric instead of barycentric elements (B&B do not say which they use);
- the ecliptic frame instead of Jupiter's plane;
- for set B: M4 and M5, and the density a × Δϖ as in Fig. 1.

## 5. Tolerances

| measure | B&B value | tolerance | reason |
|---|---|---|---|
| M1 | 180° | 180° ± 20°, for the pooled value and for each of the 4 subsets | see below |
| M2 | cluster clearly present | R̄ ≥ 0.20 | see below |
| M3 | ψ ≈ 0° | ψ within ±30° | see below |
| M4 (A) | 256 au | 226–286 au (±30 au) | see below |
| M5 | 134° (A) | none; reported | see below |

**M1 (direction).**
- The paper gives no number with an error.
- The centres of the width bars in Fig. 3 lie 4–11° from 180°.
- Frame and element type (barycentric against heliocentric, ecliptic against Jupiter's plane) change Δϖ by a few
  degrees.
- Our runs up to 820 Myr swing between about 130° and 265° (`docs/night-20261024.md`), so the 3-Gyr mean must not
  be judged more finely than the paper itself shows.
- The tolerance must also hold in every subset, so that one subset cannot decide alone.

**M2 (strength).**
- Fig. 3 normalises the density at each a. The band of the m9 = 7 panel is bright, and the rest nearly black: a
  contrast of at least about 5.
- For a von Mises distribution that means κ ≳ 0.8, R ≳ 0.37.
- R̄ = 0.20 (κ ≈ 0.41, contrast about 2.3) is therefore a conservative lower limit for "a cluster as in B&B".
- With about 3,000 selected particles per subset, R̄ = 0.20 is far beyond noise (R of an isotropic sample ≈ 0.02).

**M3 (pole).**
- In Fig. 2 and Fig. 4 (i9 = 15°) the pole density lies around Planet Nine's pole, but it is drawn without numbers.
- ΔΩ of particles with small i is poorly defined; the pole vector weights by sin i.
- Hence a wider tolerance than for M1.

**M4 (wall).**
- Across the panels of Fig. 3 the wall moves by 42 au (238–280 au) as m9 goes from 4 to 10.
- B&B smooth a by 5–30 % (§4.2, p. 9), which softens the wall.
- The line is placed by eye. ±30 au still separates the extremes of Fig. 3.

**M5 (width).** The paper does not define where a bar ends. A definition of our own would be judged against a
quantity of unknown definition.

A set **agrees with B&B** if M1, M2 and M3 are within tolerance, and for A also M4. A single deviation is not
balanced by the other measures.

## 6. What follows from each outcome

| outcome | condition | consequence |
|---|---|---|
| 1. Agreement | A and B agree | Our setup reproduces B&B's long-term clustering for both sets; the production run's 1–4-Gyr result can be compared with B&B. Entry 3 states this together with the limits (one realisation of the planets, values read from figures). |
| 2. One set agrees | only A or only B agrees | The difference depends on the set. First, the reported variants are checked (heliocentric elements, ecliptic frame, which could explain a deviation without a dynamical cause). If the deviation remains, it is reported as such; no general statement. |
| 3. Cluster in the wrong direction | M2 ≥ 0.20, but M1 outside 160–200° in at least one set | A difference in dynamics or setup (inner planets merged into the Sun, removal, frame). Before any further claim: mercury6 counter-run of set A (section 9). |
| 4. No cluster | M2 < 0.20 in at least one set | Contradicts Fig. 1 or Fig. 3 for that set. mercury6 counter-run of set A: does mercury6 show a cluster, it is a problem of p9gpu or of our setup, and the production run is held; does it show none either, it is a discrepancy with the published results. It is reported with this file and B&B are asked about the details of their runs. |
| 5. Not decided | the 4 subsets disagree among themselves (scatter of M1 over the subsets > 10°), the run is not complete to 4 Gyr, or a prerequisite (V1–V3) is not met | No statement. More test particles, or a second seed, need a new criteria file. |

- After a run, nothing in this file is changed. Anything that turns out to be missing goes into a dated addendum,
  marked as written after the result.
- The outcome is entered as `result` referring to the entry that fixes this file (when it has been entered).

## 7. Prerequisites (before the release to compute)

- V1: `make_ic.py` can give Planet Nine's elements relative to the invariable plane of Jupiter to Neptune. Its
  output for the existing cases stays unchanged (test hashes).
- V2: an encounter treatment of p9gpu has passed acceptance (`docs/acceptance-rules.md`).
- V3: the evaluation tool computes M1–M5 in Jupiter's plane and in the ecliptic, tested on a run of known
  orientation.
- V4: this file is committed, tagged and entered in the notary before the start.

## 8. The observed objects (reported, not judged)

- With ϖ9 = 254° (Fig. 1), the 11 objects of Table 1 (p. 4) have Δϖ from 113.5° (2013 RA109) to 224.2°
  (2010 GB174) without 2013 FT28 (4.3°). The cluster is 111° wide (p. 19).
- How the long-term distributions of A, B and the production run lie relative to these 10 values is reported
  without a test. B&B's likelihood needs their bias function (§3), which we do not have.

## 9. Compute time (estimate)

**Particle-steps per set:**
- 64,000 test particles × 8.0·10⁹ steps (4 Gyr / 0.5 yr) × the mean fraction alive;
- with 0.4–0.6 (G201: 56 % at 820 Myr; slower loss later), that is **2.0–3.1·10¹⁴**, central value 2.56·10¹⁴;
- set B (closer Planet Nine) may lose particles faster.

Throughput (`docs/gpu-performance.md`, `docs/production-proposal.md`):
- **L40S**:
  - measured 9.0·10⁸ particle-steps/s with the fixed step at 64,000 test particles (saturated);
  - smooth v5 estimated at ÷1.70 = 5.3·10⁸ /s, and v6 at ÷1.30 = 6.9·10⁸ /s, from counted FP64 operations.
- **A100**:
  - not measured; FP64 9.7 TFLOPS, about 17 times the laptop GPU, i.e. 7.8·10⁹ /s with the fixed step, if
    saturated;
  - v5 4.6·10⁹, v6 6.0·10⁹ /s;
  - saturation needs about 250,000–500,000 test particles; with 64,000 an A100 runs far below it (assumed here:
    25–50 %).

| where | how | sets A + B (2 × 2.56·10¹⁴) |
|---|---|---|
| L40S, v5 | two jobs one after the other (64,000 saturate the L40S) | 2 × 5.6 days = **11 days** (9–13) |
| L40S, v6 | the same | 2 × 4.3 days = **8.6 days** (7–10) |
| A100, v5 | two jobs of 64,000 at the same time (MPS), 25–50 % of saturation | **2.6–5.1 days** |
| A100, v5 | bundled: both sets in one job (128,000), or both sets × 2 seeds (256,000) | **1.3 days** if saturated (for 256,000: 2.6 days, twice the particles) |

- Bundling different planetary systems in one p9gpu job does not exist yet. The same extension is wanted for the
  second tier of 2025 LS2.
- On an A100 a benchmark comes first: 10 Myr with 64,000, 128,000 and 256,000 test particles.
- df64 is not an option on an A100: there it is slower than FP64.
- Output: about 110 bytes per particle and snapshot (G201: 276 MB for 820 snapshots of on average 3,100
  particles), so about 1.4 GB per set at one snapshot per 10 Myr.

### Optional: mercury6 as a counter-run (one set)

- **Source and licence:**
  - The original mercury6 (J. E. Chambers, Fortran 77, MERCURY6_1.FOR "ErikSoft 3 May 2002", later 6.2) carries no
    licence in the code or in the manual. The manual only asks to cite Chambers (1999, MNRAS 304, 793).
  - The mirror github.com/smirik/mercury is labelled GPL-3.0 by its maintainer. That this is Chambers' own grant is
    not verified.
  - Consequence: running it internally is unproblematic; the source is not redistributed, and the version used is
    named with its URL and sha256. Whether modified sources (e.g. a raised NMAX) may be published stays open (P1).
- **Work** (estimate, 1–2 days):
  - gfortran build (`-std=legacy` as needed);
  - a converter from `make_ic.py` to `big.in` (Sun with the inner planets as the central body, Jupiter to Planet
    Nine; heliocentric Cartesian) and `small.in` (test particles with mass 0);
  - `param.in`: hybrid, 300 days, accuracy 1e-12, changeover 3 Hill radii, central body radius 4.5 au, ejection
    10,000 au, output every 10 Myr;
  - test particles in chains of 250 per core, below NMAX in `mercury.inc` (2000 as far as known; to be checked in
    the source), so no change to the source;
  - conversion of the output (x, y, z, u, v, w via element6) to the same barycentric evaluation.
- **Run time:**
  - set A with the first 4,000 test particles of seed 311 (the same start states as subset 0, so the comparison is
    on the same particles): 4,000 × 4.87·10⁹ steps × 0.5 ≈ 9.7·10¹² particle-steps;
  - at an assumed 0.2–0.6 µs per particle-step (REBOUND WHFast here: 0.11–0.20 µs; the hybrid integrator adds
    encounter checks and conversions) that is 540–1,620 core-hours, i.e. **1.4–4.2 days on 16 cores** of the
    notebook. A 10-Myr benchmark first.
  - With B&B's 17,500 test particles: 6–18 days.
- Statistically, 4,000 are enough for M1–M3 within the tolerances (about 1,800 selected particles at 640 Myr in the
  4,000-particle runs). For M4 they are tight (few particles per 10-au bin), so with 4,000 M4 is reported only.

## 10. Open decisions for the project lead

- D1: sets A and B as proposed, or the posterior set (6.2 / 380 / 16° / q 300, the production run) as one of the
  two? Against it: the paper shows no distribution for it.
- D2: tolerances as in section 5.
- D3: where to compute (L40S or A100) and when. Not on appmdp-05 before the speed benchmark and the main run there.
- D4: mercury6 counter-run: always, or only for outcomes 3 and 4; and the licence question P1.
- D5: entry type and order in the notary (this file before the start, with entry 3).

## 11. Decisions of the project lead (2026-11-02)

- **The text above:** sections 1-10 are the draft of 224b7a1 (tag `bb2021-criteria-draft-1`), unchanged.
  - That file was stamped with OpenTimestamps on 2026-11-02, as `runs/notary/bb2021-comparison-criteria-224b7a1.md`.
  - SHA-256 `6a08d162339513d6d92014d50eef041524cc1e39de6c005c1d45ed50aa40c3af`, git blob
    `99b646d8e19ac9d1c9014d9cd27992569ee343ce`.
- **D1:** sets A and B as proposed (section 2).
- **D2:** tolerances as proposed (section 5).
- **D3:** computed on the A100, after its acceptance test. Not on appmdp-05's L40S, and not before the speed
  benchmark.
- **D4:** no mercury6 counter-run for now.
  - Only for outcome 3 (cluster in the wrong direction) or 4 (no cluster) of section 6.
  - Before that, the licence question P1 has to be settled.
- **D5:** these criteria go into entry 3, together with the result of the equivalence test and the package of the
  production run.
- **Before the runs:** the prerequisites V1-V3 of section 7.

## 12. Addendum of 2026-11-03 (decision of the project lead, before any run)

- **D3, changed:** sets A and B may also be computed on the L40S of appmdp-05, while the AI services there keep
  running.
  - Reason: the results are bit-identical on every GPU that passes the check of p9prod-9a084ed (the L40S and the
    A100 both gave ALL SAME on the 38 check cases); another GPU or a shared GPU changes only the run time.
  - Order: the production run first on the A100. Sets A and B start as soon as V1–V3 are done and checked: on the
    L40S if possible, otherwise on the A100 after the production run.
  - Every run first passes `check.sh` of the package on its GPU, as before.
- Nothing else in this file changes.

