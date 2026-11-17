# Exploratory decomposition of sets A and B beyond the wall: result (2026-11-17)

**Status:**
- Exploratory, after outcome 4, as fixed in advance by the addendum `docs/sets-decomposition-addendum-20261117.md`
  (6130d44, timestamped before any look). Computed with the project lead's go of 2026-11-17.
- **It changes nothing:** not the criteria, not the verdicts, not outcome 4. It makes no statement about the paper or
  about Planet Nine.
- For independent review. The Claude chat recomputes f) and c) from the export.

**How it was computed:**
- `tools/sets_decompose.py`, committed before it ran (2d10dae), from a clean detached checkout of 2d10dae. It imports
  `frame_elements` of `prod_eval.py` (`1ebb2d45…`) unchanged.
- Snapshots of the checked archives of sets A and B: 401 per set (t = 0 to 4 Gyr), of which 301 in the window 1–4 Gyr.
- **Consistency check:** R per 10 au of all of S_BB equals `M4_bins` of the evaluation in all 55 bins of both sets
  (largest difference 0.00000).
- **Beyond the wall:** set A 260–700 au (bins from the wall of 256 au on, on the 10-au grid of M4), set B 200–700 au.
  Means are unweighted over the bins.
- **Files:** `docs/sets-decomposition-20261117/`.

## f) Preview "inner removal": does not explain

R per 10 au beyond the wall, S_BB, 1–4 Gyr, only particle-snapshots whose particle had q ≥ X at every snapshot since
t = 0:

| X | set A: mean R | particle-snapshots | set B: mean R | particle-snapshots |
|---|---|---|---|---|
| (all of S_BB) | 0.097 | 3,513,343 | 0.154 | 5,883,266 |
| 4.5 au | 0.097 | 3,513,343 | 0.154 | 5,883,266 |
| 10 au | 0.098 | 3,490,932 | 0.154 | 5,882,965 |
| 20 au | 0.118 | 2,810,648 | 0.164 | 5,604,718 |
| 30 au | 0.166 | 2,080,752 | 0.189 | 4,901,670 |

**Scale of the addendum:** "does not explain" for every X in both sets (≤ 0.2).
- **Limit, as announced:** the 10-Myr cadence misses short passages through small q. The preview tends to underestimate
  the effect. At X = 4.5 au no particle-snapshot is lost at all.
- The run with an inner removal in every step tests the conjecture directly.

## g) Density images, shown before any interpretation

Files `bilder-satzA.png` and `bilder-satzB.png`.
- **Format:** a against Δϖ, 2 au × 1°, linear in a from 100 to 1000 au, normalised per a column, 1–4 Gyr pooled.
- **Display:** the square root of the density; columns with fewer than 50 particle-snapshots are blank.
- **What the images show, without interpretation:**
  - Beyond the wall, the selections 42 < q < 60 au, 60 < q < 100 au and i < 30° show a clear band around Δϖ ≈ 180°, in
    both sets.
  - The selections q > 100 au and i > 30° show no band around 180° there.
  - All of S_BB lies in between: a faint band.

## c) R per 10 au for subsets (scale: core)

| selection | A: beyond the wall | A: 270–700 au | A: 150–230 au | B: beyond the wall | B: 270–700 au | B: 150–230 au |
|---|---|---|---|---|---|---|
| all of S_BB | 0.097 | 0.096 | 0.074 | 0.154 | 0.154 | 0.143 |
| 42 < q < 60 au | 0.280 | 0.280 | 0.035 | 0.463 | 0.480 | 0.212 |
| 42 < q < 100 au | 0.212 | 0.213 | 0.070 | 0.405 | 0.425 | 0.169 |
| i < 30° | 0.378 | 0.381 | 0.074 | 0.403 | 0.419 | 0.194 |
| **42 < q < 100 au and i < 30°** | **0.628** | 0.637 | 0.069 | **0.500** | 0.518 | 0.216 |
| survivors to 4 Gyr | 0.091 | 0.088 | 0.068 | 0.149 | 0.139 | 0.189 |

**Scale of the addendum:** **"core present"** in both sets (≥ 0.4).

For information, not part of the scale: the measurement of the figures gives beyond the wall 0.61 (Fig. 3, third
panel; 270–700 au) and 0.52 (Fig. 1; 230–700 au) (`nachrechnung` of 2026-11-17).

## b) q and i of the particles in S_BB beyond the wall

| | set A | set B | Fig. 4 of B&B (m9 7, a9 500, e9 0.33, i9 15°) |
|---|---|---|---|
| share i < 30° | 0.339 | 0.514 | 94 % of the pole density |
| share i > 50° | 0.475 | 0.236 | below 1 % |
| median i | 47.1° | 29.2° | – |
| share 42 < q < 60 au | 0.103 | 0.141 | – |
| share 42 < q < 100 au | 0.305 | 0.374 | – |
| median q | 148 au | 129 au | – |

- Pooled over the 301 snapshots: 3,553,817 particle-snapshots (A) and 5,883,266 (B).
- The histograms are in `qi.csv`.
- The comparison with Fig. 4 is information: there the panel and the selection (a > 150 au, q > 42 au) differ slightly
  from set A.

## d) Libration and circulation

Particles in S_BB beyond the wall in at least 20 snapshots of the window:

| class | set A: particles | A: mean R beyond the wall | set B: particles | B: mean R beyond the wall |
|---|---|---|---|---|
| librating about 180° | 4,205 | 0.847 | 5,714 | 0.800 |
| circulating | 12,604 | 0.173 | 19,100 | 0.066 |
| mixed | 3,550 | 0.349 | 2,917 | 0.411 |

## e) Survival beyond the wall

| t | set A: particles present (share of 64,000) | A: in S_BB beyond the wall (relative to 1 Gyr) | set B: present | B: beyond the wall |
|---|---|---|---|---|
| 1 Gyr | 33,492 (0.523) | 18,041 (1.00) | 36,191 (0.566) | 25,302 (1.00) |
| 2 Gyr | 25,514 (0.399) | 12,912 (0.72) | 29,111 (0.455) | 21,059 (0.83) |
| 3 Gyr | 20,836 (0.326) | 10,024 (0.56) | 24,547 (0.384) | 17,751 (0.70) |
| 4 Gyr | 17,616 (0.275) | 8,021 (0.44) | 20,723 (0.324) | 15,118 (0.60) |

## a) Δϖ per 10-au bin

For every selection and bin, `bins.csv` holds: the number, R, the direction, the second harmonic and the histogram in
10° classes.

## What this shows, and what not

**What it shows (the addendum allows this much):** where in the particle population the difference beyond the wall
sits.
- The particles with 42 < q < 100 au and i < 30° cluster beyond the wall about as strongly as the measured figures:
  0.63 against 0.61 (A), 0.50 against 0.52 (B).
- The weak clustering of all of S_BB comes with a large share of particles at q > 100 au or i > 30° beyond the wall.
  These particles show no band around 180°.
- Their share is far above what Fig. 4 shows for the pole density.

**What it does not show:**
- why these particles are there;
- whether they are missing in the runs of Brown & Batygin;
- whether the stricter inner removal would remove them (the preview cannot tell, because of its cadence).

**What it does not change:** outcome 4. It is no judgement on the paper or on Planet Nine. The open questions go into
the request to the authors and into the run with an inner removal in every step.
