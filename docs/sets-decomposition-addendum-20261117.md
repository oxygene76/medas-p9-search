# Explorative decomposition of sets A and B beyond the wall (addendum, 2026-11-17)

**Status:**
- Fixed and timestamped before any look at the snapshots of sets A and B for this purpose. Since the evaluation of
  2026-11-17 the only look at them was through `tools/prod_eval.py`: M1–M5 and the 10-au bins of M4 in `result.json`.
- Exploratory and after the result: a search for the cause of outcome 4 (`docs/sets-outcome-20261117.md`).
- **It changes nothing:** not the criteria, not the verdicts on sets A and B, not outcome 4, not what section 6 of
  `docs/bb2021-comparison-criteria.md` fixes for it.
- No new run. It is computed only with the project lead's go.

## Data and conventions

- **Snapshots:** those of jobs `BB-A` and `BB-B` in the checked archives: `setsA-p9bbsets-5b05cc3.tar.gz` sha256
  `1c3c9f40…a9e0`, `setsB-p9bbsets-5b05cc3.tar.gz` sha256 `d57179a5…2d8d` (lists in `docs/sets-result-A-20261117/`
  and `docs/sets-result-B-20261117/`).
- **Window:** 1–4 Gyr (the 301 snapshots of the evaluation), unless stated otherwise. For the history of q (item f),
  all snapshots from t = 0 (`jobs/BB-<set>/input.sa` and every snapshot every 10 Myr).
- **Elements and angles** exactly as `tools/prod_eval.py` (= `prod-eval-v1`, entry e3) forms them for M1–M5: function
  `frame_elements`, barycentric osculating elements, angles in the frame of Jupiter's orbital plane at each snapshot,
  dog-leg longitudes; Δϖ = ϖ − ϖ9.
- **S_BB:** 150 < a < 1000 au, q > 42 au.
- **The wall:** 256 au for set A (the mark of the authors in Fig. 3, third panel), 200 au for set B. "Beyond the wall"
  means wall ≤ a < 700 au.
- **R per 10 au:** the mean resultant length of Δϖ of all particle-snapshots of the selection in a bin, pooled over the
  window, as `M4_bins`. Only bins with at least 10 particle-snapshots count. "The mean beyond the wall" is the
  unweighted mean over these bins.
- **Code:** a script of its own under `tools/`, committed before it runs, that imports `frame_elements` from
  `tools/prod_eval.py` unchanged.

## What is computed, per set

**a) Δϖ beyond the wall, per 10-au bin:**
- histogram in 10° classes;
- R, the direction (circular mean), the second harmonic |⟨exp 2iΔϖ⟩|;
- the number of particle-snapshots;
- an image in the format of Fig. 1 of Brown & Batygin (a against Δϖ, normalised at each a, 2 au × 1°, window 1–4 Gyr).

**b) q and i of the particles in S_BB beyond the wall:** distributions, pooled over the window.
- For comparison, from Fig. 4 of Brown & Batygin (m9 = 7, a9 = 500, e9 = 0.33, i9 = 15°; a > 150 au, q > 42 au): 94 % of
  the pole density at i < 30°, below 1 % above 50°.

**c) R per 10 au for subsets of S_BB:**
- 42 < q < 60 au;
- 42 < q < 100 au;
- i < 30°;
- 42 < q < 100 au and i < 30° (the subset of the scale below);
- only particles that survive to 4 Gyr.

**d) Libration and circulation:**
- **Which particles:** those in S_BB beyond the wall in at least 20 snapshots of the window.
- **Classes,** per particle over those snapshots:
  - "librating about 180°" if every Δϖ lies within 90–270°;
  - "circulating" if Δϖ takes values in all four quadrants;
  - "mixed" otherwise.
- **Reported:** the shares of the three classes and R per 10 au per class.

**e) Survival beyond the wall over time:**
- per snapshot of the window, the number of particles in S_BB beyond the wall;
- the same relative to 1 Gyr;
- the share of the 64,000 that are still present.

**f) Preview of the hypothesis "inner removal"** (a conjecture, not a finding):
- **History:** q of each particle from t = 0 at every snapshot.
- **Selection:** R per 10 au beyond the wall (1–4 Gyr, S_BB) only for particle-snapshots whose particle had q ≥ X at
  every snapshot up to that time, for X = 4.5, 10, 20, 30 au. With each, the number of particle-snapshots.
- **Limit:** The 10-Myr cadence of the snapshots misses short passages through small q. The preview therefore tends to
  underestimate the effect of a stricter inner removal.

**g) Density images in the format of Fig. 1** (a against Δϖ, normalised at each a, 1–4 Gyr), shown first and before any
interpretation, for:
1. all of S_BB;
2. 42 < q < 60 au;
3. 60 < q < 100 au;
4. q > 100 au;
5. i < 30°;
6. i > 30°.

**h) Export for an independent recomputation:** per set one file (npz, float32).
- **Times:** t = 0 and t = 1.0, 1.1, …, 4.0 Gyr (31 snapshots).
- **Particles:** all test particles present at each time, not only S_BB.
- **Columns:**
  - particle index (constant over time), t, a, e, i, Ω, ω;
  - per time, ϖ9 and the elements of Planet Nine and of Jupiter.
- **Convention:** as above.
- **Delivered:** with sha256 and a description of the columns.

## The scales, fixed before the look

**For c), the subset 42 < q < 100 au and i < 30°:** the mean of R per 10 au beyond the wall.
- ≥ 0.4: **"core present"**;
- ≤ 0.2: **"no core"**;
- in between: **"unclear"**.

**For f), for each X:** the mean of R per 10 au beyond the wall.
- ≥ 0.4: **"explains"**;
- ≤ 0.2: **"does not explain"**;
- in between: **"unclear"**.

The comparison values from the measurement of the figures (beyond the wall: Fig. 3, third panel, 0.61; Fig. 1, 0.52)
are information, not part of the scales.

## What follows

- **The outcome:** a report of its own, with these quantities and the verdicts of the scales, for independent review.
- **What it may say:** where in the particle population the difference beyond the wall sits.
- **What it must not say:** a judgement on the paper or on Planet Nine.
- **What it decides:** nothing about the consequences of outcome 4. The mercury6 counter-run of set A stays as section 6
  fixes it; its scope is set afterwards. A run with a stricter inner removal needs criteria of its own, entered before
  it starts.
