# Decomposition of sets A and B, addendum 2: the selection of Batygin et al. 2019 (2026-11-17)

**Status:**
- Fixed and timestamped before this computation on the full data.
- **Seen before:**
  - the results of addendum 1 (`docs/sets-decomposition-20261117.md`, f7ae12c);
  - a preliminary recomputation of these quantities by the Claude chat from the exports, 32 snapshots (its message of
    2026-11-17, 21:00).
  - It is therefore no blind addendum. It fixes the quantities and the scale before they are computed on all 301
    snapshots of the window.
- Exploratory, after outcome 4. **It changes nothing:** not the criteria, not the verdicts, not outcome 4. It makes no
  statement about the paper of 2021 or about Planet Nine.
- Computed with the project lead's go of 2026-11-17.

## Why

Batygin, Adams, Brown & Becker 2019 (arXiv:1902.10103, section 5) divide their simulated particles into an "observable"
group (30 ≤ q ≤ 100 au, i < 40°), a group with q ≥ 100 au and one with i ≥ 40°.
- They show only particles that live longer than 4 Gyr.
- They compute the share of apsidally confined particles from the observable group only.

This is not shown to hold for the figures of 2021. The addendum only asks how our runs look under that selection. The
citation is to be checked against the PDF (separately).

## Data and conventions

Unchanged from addendum 1 (6130d44):
- the snapshots of the checked archives, window 1–4 Gyr (301 snapshots);
- elements and angles as `frame_elements` of `tools/prod_eval.py`;
- R per 10 au as `M4_bins`: pooled particle-snapshots, bins with at least 10;
- beyond the wall: 260–700 au (A), 200–700 au (B), bins on the 10-au grid of M4;
- means unweighted over the bins.

**Selections** (each for 150 < a < 1000 au):

| selection | q | i |
|---|---|---|
| (a) | 30 ≤ q ≤ 100 au | i < 40° |
| (b) | 42 ≤ q ≤ 100 au | i < 40° |
| (c) | q > 42 au (all of S_BB) | – |

- Each once for all particles and once only for the particles present at 4 Gyr (4-Gyr survivors).
- Selection (a) reaches below q = 42 au, so outside S_BB. That is intended, as in 2019.

## What is computed, per set and per selection (6 combinations)

1. R per 10 au beyond the wall, and its mean.
2. The share of the particle-snapshots beyond the wall with 90° < Δϖ < 270°.
3. **The inclinations for 150 < a < 1000 au:**
   - with the q cut of the selection and **without** the i cut: the shares i < 30°, i < 40°, i > 50°, i > 90°, and the
     histogram in 5° classes;
   - and the share i < 30° **within** the full selection, with its i cut.
4. **An image in the format of Fig. 1** (a against Δϖ, 2 au × 1°, normalised per a column, 1–4 Gyr) for selection (a)
   with the 4-Gyr survivors only.

## Scale, fixed before the computation

For each of the 6 combinations, the mean of R per 10 au beyond the wall:
- ≥ 0.4: **"cluster as in the figures"**;
- ≤ 0.2: **"no cluster"**;
- in between: **"unclear"**.

For information, not part of the scale: the measured figures give beyond the wall 0.61 (Fig. 3, third panel) and 0.52
(Fig. 1), and anti-aligned shares of 0.87 and 0.83.

## Code

`tools/sets_decompose2.py`, committed before it runs. It imports `frame_elements` and the snapshot readers of
`tools/prod_eval.py` unchanged.
