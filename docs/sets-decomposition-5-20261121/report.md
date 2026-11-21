# Addendum 5: result (2026-11-21)

**Basis:**
- **Addendum:** `docs/sets-decomposition-addendum-5-20261121.md`, fixed and timestamped before the computation
  (3098827).
- **Results:** `A.json` and `B.json` in this directory, unchanged as written by `tools/sets_addendum5.py`, committed
  and timestamped before this report (ede967c).
- **Environment and cross-check:** `environment.txt`.

**It changes nothing:** not the criteria, not the verdicts, not outcome 4.

**Cross-check (a) passed.** The registered definition reproduces the registered values in both sets, largest
difference 5.6 × 10⁻¹⁶: M1, M2, R beyond the wall, and the three unweighted values of part 2.

## Part 1: the definition of ϖ

| | Set A | Set B |
|---|---|---|
| retrograde share of S_BB particle-snapshots | 17.1 % | 0.8 % |
| M2 (a) Ω + ω, registered | 0.0496 | 0.1273 |
| M2 (b) azimuth of the eccentricity vector | 0.0530 | 0.1222 |
| M2 (c) Ω − ω for i > 90° | 0.0522 | 0.1299 |
| M1 (a) / (b) / (c) | 127.3° / 135.9° / 139.4° | 166.7° / 165.6° / 166.8° |
| R beyond the wall of S_BB, (a) / (b) / (c) | 0.097 / 0.092 / 0.087 | 0.154 / 0.149 / 0.157 |
| M2 for i < 90°, (a) / (b) / (c) | 0.073 / 0.077 / 0.073 | 0.131 / 0.124 / 0.131 |
| M2 for i > 90°, (a) / (b) / (c) | 0.153 / 0.116 / 0.093 | 0.358 / 0.246 / 0.203 |
| information: S_BB with i < 40°, (a): M2 / R_pooled / R beyond the wall | 0.207 / 0.210 / 0.270 | 0.279 / 0.282 / 0.340 |

- **M2 stays below 0.20 in both sets under (a), (b) and (c).** By the wording fixed in the addendum, the result does
  not depend on the definition of ϖ.
- M1 of set A stays outside its limit of 160–200° under (b) and (c).
- For set B, M2 for i > 90° rests on 0.8 % of the particle-snapshots, a few per snapshot. The R of such small samples
  is biased upward.
- **Information** (not part of the rules of the addendum): with the registered angle and only the orbits below 40°
  inclination, M2 is above 0.20 in both sets. Beyond the wall these orbits reach 0.27 and 0.34, still well below the
  figures of the paper (0.60–0.61 and 0.51–0.52). The registered criterion counts all inclinations.

## Part 2: R beyond the wall, weighting and particles

| Selection | Set | unweighted | weighted with n | bins with ≥ 100 particles | bootstrap 95 % (of the unweighted mean) | distinct particles per bin |
|---|---|---|---|---|---|---|
| S_BB (q > 42 au) | A | 0.097 | 0.105 | 0.097 (44 of 44) | 0.094–0.105 | 1,371–3,564 |
| | B | 0.154 | 0.118 | 0.154 (50 of 50) | 0.149–0.160 | 2,198–6,022 |
| observable (q 30–100 au, i < 40°) | A | 0.548 | 0.533 | 0.548 (44 of 44) | 0.536–0.559 | 1,412–4,059 |
| | B | 0.482 | 0.450 | 0.482 (50 of 50) | 0.475–0.489 | 3,319–6,999 |
| q 42–100 au, i < 30° | A | 0.628 | 0.612 | 0.628 (44 of 44) | 0.618–0.639 | 668–2,092 |
| | B | 0.500 | 0.472 | 0.500 (50 of 50) | 0.492–0.507 | 1,595–3,927 |

- **Distinct particles:** each bin holds at least 668 distinct particles over the window. The bias of small samples
  is therefore small.
- **Like-for-like comparison:** the values from the figures are simple means over 10-au bins of images normalised at
  each semi-major axis (`runs/notary/bb2021-figures`, the measurement of 2026-11-17). The unweighted mean is the
  comparison formed the same way.

## The predictions

| Prediction (addendum 5) | Result | |
|---|---|---|
| (a) reproduces the registered values | difference ≤ 5.6 × 10⁻¹⁶ | met |
| M2 below 0.20 in both sets under (a), (b), (c) | at most 0.053 (A), 0.130 (B) | met |
| set B, (c): M2 moves by about 0.02 at most | +0.003 | met |
| set B, (b): M2 within ±0.03 of 0.127 | −0.005 | met |
| M1 of set B within ±10° | −1.1° / +0.1° | met |
| M1 of set A may move by more than 10° (a possibility, no firm prediction) | +8.6° (b), +12.1° (c) | – |
| M2 for i > 90° in set A | no prediction | – |
| S_BB with i < 40°: M2 higher than (a) for all of S_BB in both sets | 0.207 against 0.050; 0.279 against 0.127 | met |
| part 2: the unweighted values reproduce the registered ones | equal | met |
| part 2: weighted values lower than unweighted (observable; q 42–100 au, i < 30°) | lower in all four | met |
| part 2: the values from the bins with at least 100 distinct particles lower than unweighted | **not met:** equal, because no bin has fewer than 668 particles | not met |
| part 2: 95 % span of the bootstrap at least ±0.03 | **not met:** ±0.007 to ±0.012 | not met |
| part 2: whether the values stay near the figures | weighted 0.53 / 0.45, unweighted 0.55 / 0.48, against 0.60–0.61 / 0.51–0.52 | open, no prediction |
