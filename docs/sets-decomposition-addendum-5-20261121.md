# Decomposition of sets A and B, addendum 5: the definition of ϖ, and the weighting of R beyond the wall (2026-11-21)

**Status:**
- **Fixed** on 2026-11-21 after the review of the draft (2263441) with two additions: a variant with i < 40° in
  part 1, and the wording fixed beforehand in "What follows".
- Committed and timestamped **before** any computation; computed only with the project lead's go. No partial
  result was looked at before the stamp.
- Written after outcome 4, after addenda 1–4 and after an independent reading of the code
  (`docs/code-review-20261121.md`, points A1, B8, C2, C3, C5).
- Exploratory, on the existing snapshots; no new run. **It changes nothing:** not the criteria of the sets, not the
  registered tool (`tools/prod_eval.py`, prod-eval-v1), not their verdicts, not outcome 4. The tool was fixed before
  the runs; this addendum measures how far the numbers depend on two choices.

## Part 1: the definition of the longitude of perihelion ϖ

### What is fixed where

| Where | What it says | Entered |
|---|---|---|
| `docs/bb2021-comparison-criteria.md` section 4 (1c5f2ba, line 145) | "barycentric osculating elements, as in `tools/analyze.py`" | #5 (and earlier version in #4) |
| the same file, addendum 13, "V3 done" (1c5f2ba, line 383) | "Conventions: varpi = Omega + omega; Jupiter's plane …; dog-leg longitudes" | #5 |
| `docs/production-criteria.md` (a649408, line 65) | the conventions fixed in prod-eval-v1: "varpi = Omega + omega" | #4 |
| `tools/prod_eval.py` at prod-eval-v1, lines 122–127 | ϖ = Ω + ω for every orbit; the comment says the projected eccentricity vector "differs by up to about 1 deg at 16 deg inclination" | #4, #5 |
| `tools/analyze.py`, lines 62–63 | ϖ = azimuth of the eccentricity vector in the reference plane (`atan2(e_y, e_x)`); the comment calls it "Omega + omega, for prograde orbits" | – |

**Reading:**
- The registered tool does what addendum 13 and the production criteria fix: ϖ = Ω + ω.
- Section 4's "as in `tools/analyze.py`" names the elements in general. For ϖ it conflicts with addendum 13, and the
  conflict matters only for strongly inclined orbits.
- Neither criteria file has a rule for retrograde orbits.
- The comment in `prod_eval.py` ("about 1 deg at 16 deg") holds for Planet Nine, not for the evaluated particles.

**How large the difference is:**
- For a prograde orbit, Ω + ω and the azimuth of the eccentricity vector differ by at most arcsin(tan²(i/2)): 1.1° at
  16°, 4.1° at 30°, 12.6° at 50°, 90° at 90°.
- For a retrograde orbit the azimuth lies near Ω − ω; Ω + ω can be off by up to 180°.
- Known before this addendum (`docs/sets-decomposition-2-20261117/*/summary.json`, `c_q>42/all`,
  `inc_q_cut_only`, particle-snapshots of 150 < a < 1000 au, q > 42 au, 1–4 Gyr):
  - set A 17.1 % retrograde and 36.8 % above 50°;
  - set B 0.8 % and 22.3 %.

**The paper:**
- Brown & Batygin 2021 (arXiv:2108.09868v2) name "longitude of perihelion, ϖ" (p. 3) without a formula.
- For the likelihood they use the canonical Poincaré variables, (x, y) "corresponding roughly to longitude of
  perihelion" (p. 7), and refer to Brown & Batygin 2019 for the details.
- Brown & Batygin 2019 (arXiv:1901.07115, p. 3, eqs. 1–2) take the reduced Poincaré coordinates with γ = −ϖ and
  x = √(2Γ) cos ϖ, after Morbidelli 2002. The standard construction there uses ϖ = ω + Ω. The formula itself is not
  printed.
- The word "retrograde" occurs in neither paper.
- Neither paper gives a rule for retrograde orbits, or says how ϖ of the simulated particles in the figures was
  formed.
- The likelihood of the comparison with the simulations combines a kernel in the pole position with one in Δϖ:
  "σ = 2° in great-circle distance from the pole position and σ = 10° in longitudinal distance from Δϖ"
  (Brown & Batygin 2021, p. 12).
- Brown & Batygin 2019 is at hand (arXiv:1901.07115v1, sha256 `2c8124ea…3d660`). It defines the variables, not ϖ:
  - Γ = 1 − √(1 − e²), γ = −ϖ, Z = √(1 − e²)(1 − cos i), z = −Ω (eq. 1);
  - x = √(2Γ) cos ϖ, y = √(2Γ) sin ϖ, p = √(2Z) cos Ω, q = √(2Z) sin Ω (eqs. 2–3; p. 3).
  - (x, y) points "in the direction of the longitude of perihelion" (p. 3).
  - There is no explicit definition of ϖ, so no further variant is added.

### What is computed

Sets A and B, window 1–4 Gyr (301 snapshots), selection S_BB (150 < a < 1000 au, q > 42 au), elements as
`frame_elements` of prod-eval-v1. The angle is formed for the particle and for Planet Nine in the same way, and
Δ = particle − Planet Nine:
- **(a)** ϖ = Ω + ω for every orbit, as registered. **Check:** it must give the registered M1 and M2
  (`docs/sets-result-A/B-20261117/result.json`) and R beyond the wall of S_BB (0.0974 / 0.1542,
  `docs/sets-decomposition-20261117/*/summary.json`), to 10⁻⁹. If not, nothing else is reported until the difference
  is explained.
- **(b)** the azimuth of the eccentricity vector in the reference plane, φ = Ω + atan2(cos i sin ω, cos ω), as
  `tools/analyze.py`.
- **(c)** Ω + ω for i < 90°, Ω − ω for i > 90°.

**For each:**
- M1 (pooled circular mean), M2 (mean of R per snapshot) and R_pooled;
- R beyond the wall of S_BB (bins as part 2, unweighted);
- M2 separately for the particles with i < 90° and i > 90°.

**For information, with the registered angle (a):** M2, R_pooled and R beyond the wall for S_BB with i < 40°. There
is no upper limit in q. This shows the effect of the inclination apart from the high perihelion.

### Prediction, fixed now

- **(a)** reproduces the registered values exactly.
- **M2 stays below 0.20 in both sets under all three definitions.** The reasons:
  - **Set B, (c):** only 0.8 % of the particle-snapshots change their angle. Changing the angles of a share f can move
    R by at most 2f, so M2 moves by about 0.02 at most.
  - **Set B, (b):** the prograde orbits move by a few degrees, those above 50° by more. Expected: M2 within ±0.03 of
    0.127.
  - **Set A, (b) and (c):** the 83 % prograde particles are unchanged under (c). To lift M2 from 0.050 to 0.20, the
    17 % retrograde ones would have to be clustered with R of about 0.9 in the same direction. That is not plausible
    for a population this scattered.
- **M1:**
  - set B within ±10° of 166.7°;
  - set A may move by more than 10°, because its cluster is weak.
- **M2 for i > 90° in set A:** no prediction.
- **S_BB with i < 40° (information):**
  - M2 higher than under (a) for all of S_BB, in both sets. The reason: addendum 2 found the observable orbits
    (i < 40°) clustered far more strongly beyond the wall than all of S_BB.
  - No prediction of the values. M2 also counts the bins inside the wall, where the clustering is weak in both sets.
- **Compared with the chat's proposal** (set A below 0.20, no firm prediction for B): this prediction is stronger for
  set B, because of the bound above.

## Part 2: R beyond the wall, weighting and particles

The three rows of Table 2 of section 6 of the website, with the registered angle (a):
- **SBB:** q > 42 au (as registered).
- **obs_q30-100:** 30 ≤ q ≤ 100 au and i < 40° (addendum 2, selection a).
- **q42-100_i<30:** q > 42 au, q < 100 au, i < 30° (addendum 1).

All three use 150 < a < 1000 au and the window 1–4 Gyr. Bins of 10 au from the wall (A 256 → 260–700 au, B 200 →
200–700 au); a bin counts with at least 10 particle-snapshots.

**Reported per selection:**
- per bin: the particle-snapshots n, the distinct particles k, and R;
- the unweighted mean over the bins, as before. **Check:** it must give 0.0974 / 0.1542, 0.5476 / 0.4820 and
  0.6284 / 0.4998.
- the mean weighted with n;
- the unweighted mean of the bins with at least **100 distinct particles**;
- a **bootstrap over particles:**
  - 1000 replicates, seed 20261121;
  - each particle drawn with replacement, with all its particle-snapshots of the selection;
  - the unweighted mean recomputed;
  - 2.5, 50 and 97.5 percentiles.

**Prediction, fixed now:**
- The unweighted values reproduce the registered ones.
- **Weighted, and from the bins with at least 100 particles,** the values of obs_q30-100 and q42-100_i<30 are lower
  than the unweighted ones (0.55 / 0.48 and 0.63 / 0.50).
  - The reason: bins with few distinct particles have an R biased upward; for k unclustered directions it is about
    0.89/√k.
  - Whether they stay near the figures' 0.60–0.61 / 0.51–0.52 is open.
- The 95 % span of the bootstrap is at least ±0.03 for these two selections.

## Tool and calls

- **Tool:** `tools/sets_addendum5.py`, which imports `frame_elements`, `snapshots`, `select` and `circ_mean` of
  prod-eval-v1 unchanged.
- **Tests:** `tests/test_sets_addendum5.py`, on synthetic orbits only:
  - (b) equals the eccentricity-vector azimuth of `tools/analyze.py`;
  - the bound for prograde orbits;
  - (c) equals (b) for nearly retrograde orbits;
  - counts, weights and bootstrap on a constructed case;
  - (a) gives M1 and M2 of prod-eval-v1 on a synthetic run;
  - the variant i < 40° is computed and, where all inclinations are below 40°, equals (a).
- **Calls,** from a clean checkout at the commit of this addendum, with the unpacked, checked archives of sets A and B
  (`docs/sets-evaluation-procedure.md`, 12ab70b) and their `bin/p9sim`:
  ```sh
  ../medas-p9-search/build/venv/bin/python -I tools/sets_addendum5.py RUN_A --p9sim PKG/bin/p9sim --wall 256 > OUT/A.json
  ../medas-p9-search/build/venv/bin/python -I tools/sets_addendum5.py RUN_B --p9sim PKG/bin/p9sim --wall 200 > OUT/B.json
  ```
- **Results** in `docs/sets-decomposition-5-<date>/` (A.json, B.json, a short report), committed and stamped.

## What follows

Nothing for outcome 4. The result is reported:
- in "What this does not mean" of section 6 of the website, in one sentence;
- in the notes of Table 2;
- in a sentence in section 4.

**Wording fixed now:**
- **If M2 stays below 0.20 in both sets under (a), (b) and (c):** section 6 says that the result does not depend on
  the definition of ϖ, with the values.
- **If M2 reaches 0.20 in one set under (b) or (c):** section 6 and `kurz.json` say two things:
  - outcome 4 holds for the registered definition;
  - with the other definition, this set reaches the limit.
- **Table 2, regardless of the outcome:**
  - the row of the observable orbits gives the value weighted with n and the 95 % span of the bootstrap;
  - the unweighted value stands in the note.
- The variant S_BB with i < 40° is information. It does not enter these rules.
