# Production run p9prod-9a084ed: result of the evaluation (2026-11-10)

**Status:** result report, for independent review before anything of it goes into the research note. The criteria are
`docs/production-criteria.md` as entered in entry 3 (chain entry #4, block 10723643). The steps are
`docs/production-evaluation-procedure.md` (0ca9595). The files as the tool wrote them are in
`docs/production-result-20261110/` (commit 14d2c43).

**Version 2 (2026-11-10, after the independent review):**
- The review confirmed the verdict and the numbers; it recomputed M2 from `timeseries.csv`.
- Added under "Scope": the significance of the long-run differences (t at 2 degrees of freedom) and the noise floors.
- Added as a new section: the check of the model assumption against the text of Brown & Batygin 2021 (galactic tide,
  passing stars).
- Version 1 is commit cce5b92, stamped as `runs/notary/production-result-cce5b92.md`, and stays unchanged.

## Verdict

**Decided** (criteria section 5, decision P1):
- The largest angular distance of the M1 of the four subsets from the pooled M1 is **1.41°** (limit 10°).
- No subset deviates.
- The measures are reported and not judged against values of Brown & Batygin (2021), because the paper has no
  distribution for this set (decision D1).

## The run and the steps before the evaluation

- **Run:** p9gpu v5 on the A100, 64,000 test bodies, 0–4 Gyr, 40 segments.
  - Complete: 40 of 40 segments, 17,798 test bodies left.
  - Result hash of `seg039`: `d41152221b3dfc9ff490a21eb0120896b9bfce95a6a2bb0378c8005b0527f1c3`.
- **Checksum list:** 517 files, sha256 `48d6fa3b…57e6`, timestamped with OpenTimestamps on 2026-11-09 before any
  evaluation. `sha256sum -c` of the unpacked archive gave 517 of 517, again right before the evaluation.
- **Archive:** sha256 `940d95b8…c44f`, backed up encrypted at three places and restore-checked by the project lead
  (2026-11-10 09:12).
- **Tool:** `tools/prod_eval.py`, byte-identical to `prod-eval-v1` and to the file of entry 3 (sha256 `1ebb2d45…`),
  run from a clean detached checkout of 0ca9595.
- **Observed objects:** `docs/bb2021-observed-table1.tsv`, checked against Table 1 (p. 4) of the paper before the
  evaluation. All 11 rows are equal, and 2013 FT28 is left out as fixed.
- **Two runs of the tool:** the first gave the absolute path of the run in `result.json` and `report.txt`, so the
  tool was run again with a relative path. The outputs differ only in that path, and `timeseries.csv` is
  byte-identical. The files of the second run are committed (`environment.txt`).

## Measures over 1–4 Gyr

Selection S_BB (150 < a < 1,000 au, q > 42 au); 301 snapshots; barycentric elements, angles in Jupiter's orbital plane
at each snapshot.

| measure | pooled |
|---|---|
| M1, direction of the Δϖ cluster | **154.1°** (5,756,220 particle-snapshots) |
| M2, strength (mean R per snapshot) | **0.076** (R of the pooled sample 0.078) |
| M3, mean pole relative to Planet Nine's, ψ | **1.5°** |
| M4, wall | **155 au** (R_plat 0.078) |
| M5, width at 850–950 au | **135°**, from 106.5° to 240.5° (116,794 particle-snapshots) |

| subset (test bodies) | M1 | distance to the pooled M1 | R pooled |
|---|---|---|---|
| 0 (0–15,999) | 154.35° | 0.23° | 0.079 |
| 1 (16,000–31,999) | 155.53° | 1.41° | 0.076 |
| 2 (32,000–47,999) | 152.80° | 1.32° | 0.077 |
| 3 (48,000–63,999) | 153.81° | 0.31° | 0.080 |

**Variants, reported, not judged:**
- ecliptic frame: M1 154.2°, ψ 3.9°;
- heliocentric elements: M1 154.1°, ψ 1.6°.

## Information (reported, not judged)

**Time series** (`timeseries.csv`, every 10 Myr; S1–S3 are the selections of `docs/night-20261024.md`):

| t | test bodies | in S_BB | M1 | R | ψ | ϖ of Planet Nine | R in S1 / S2 / S3 |
|---|---|---|---|---|---|---|---|
| 0.1 Gyr | 58,513 | 33,403 | 270.7° | 0.568 | 28.0° | 251.6° | 0.298 / 0.555 / 0.536 |
| 0.5 Gyr | 41,501 | 31,711 | 135.0° | 0.221 | 3.6° | 262.1° | 0.262 / 0.261 / 0.254 |
| 1.0 Gyr | 33,560 | 26,158 | 172.7° | 0.098 | 6.2° | 275.3° | 0.133 / 0.141 / 0.143 |
| 1.5 Gyr | 29,108 | 23,185 | 153.4° | 0.101 | 2.3° | 288.6° | 0.137 / 0.144 / 0.148 |
| 2.0 Gyr | 25,915 | 20,710 | 147.4° | 0.080 | −1.0° | 301.8° | 0.123 / 0.126 / 0.130 |
| 2.5 Gyr | 23,293 | 18,629 | 146.0° | 0.078 | −1.3° | 315.0° | 0.122 / 0.123 / 0.129 |
| 3.0 Gyr | 21,129 | 16,782 | 141.2° | 0.061 | 0.1° | 328.2° | 0.105 / 0.108 / 0.112 |
| 3.5 Gyr | 19,324 | 15,346 | 150.1° | 0.063 | 3.1° | 341.4° | 0.105 / 0.108 / 0.113 |
| 4.0 Gyr | 17,798 | 14,196 | 151.1° | 0.052 | 7.2° | 354.6° | 0.094 / 0.097 / 0.102 |

What the series shows, as a description:
- **The strength falls.** R in S_BB goes from 0.57 at 0.1 Gyr to 0.10 at 1 Gyr and 0.05 at 4 Gyr. An isotropic sample
  of that size would give R of about 0.89/√n, that is 0.006–0.008 (the noise estimate of the long-run criteria, Q2).
- **The direction settles.** After an early phase near 270° (0.1 Gyr) and 135° (0.5 Gyr), M1 stays between 141° and
  173° from 1 to 4 Gyr.
- **The pole stays close.** ψ stays within 7° of Planet Nine's pole from 0.5 Gyr on.
- **Planet Nine's ϖ precesses** from 248.5° at the start to 354.6° at 4 Gyr. Δϖ is always taken against its value at
  the same snapshot.

**Survivors:** 63,911 test bodies at 10 Myr, 25,864 at 2.01 Gyr, 17,798 at 4 Gyr.

**The observed objects** (Table 1 of Brown & Batygin 2021; Δϖ = ϖ − 254°, as fixed in
`docs/bb2021-comparison-criteria.md` section 8):
- For each object, the share of the pooled S_BB particle-snapshots of the window with a within ±20 % of its a whose Δϖ
  lies within ±15° of its Δϖ. An even distribution would give 0.083.
- The Planet Nine of the run starts at ϖ = 248.5° and precesses, while the observed Δϖ refer to the fixed 254°. That
  difference is noted, and nothing is judged on it.

| object | a (au) | Δϖ | share within ±15° |
|---|---|---|---|
| 2000 CR105 | 218 | 191.0° | 0.110 |
| 2003 VB12 | 479 | 201.8° | 0.091 |
| 2004 VN112 | 319 | 138.8° | 0.107 |
| 2010 GB174 | 351 | 224.2° | 0.084 |
| 2012 VP113 | 258 | 130.2° | 0.115 |
| 2013 RA109 | 458 | 113.5° | 0.072 |
| 2013 SY99 | 694 | 167.6° | 0.119 |
| 2013 UT15 | 197 | 190.1° | 0.099 |
| 2014 SR349 | 302 | 121.7° | 0.091 |
| 2015 RX245 | 412 | 179.7° | 0.091 |

## Scope (criteria section 5)

- **Method:** the equivalence of v5 and MERCURIUS was shown for 0–200 Myr (entry e3).
- **Long-time residual risk:** the paired long runs of seeds 110–112 found no growing bias
  (`docs/long-runs-result-20261110.md`). Three pairs can find only large biases, about 0.05 in R.
- **Assessment, not part of the criteria:**
  - **Differences:** in the long runs the difference at 4 Gyr is −0.045 ± 0.031, of the same order as R of this run
    at late times (0.05–0.06 at 3–4 Gyr).
  - **Not significant:** none of the differences of the long runs is, with t at 2 degrees of freedom (three pairs):
    - S(1–4), reported there: −0.0132 ± 0.0049, p ≈ 0.12;
    - d(0.5 Gyr): +0.0073 ± 0.0025, p ≈ 0.10;
    - d(4 Gyr): p ≈ 0.29.
  - **Noise floor:** an isotropic sample of n bodies gives R ≈ 0.89/√n.
    - The long runs have about 417 distant survivors per run at 4 Gyr. Their floor, about 0.044, is as large as R of
      this run at 4 Gyr (0.052).
    - So they cannot test the late-time strength M2 at all. They are informative up to about 1–2 Gyr, with floors of
      0.034 and 0.037 against S of 0.08–0.15.
  - **This run's own floor:** 14,196 bodies in S_BB at 4 Gyr give a floor of 0.0075. R(4 Gyr) = 0.052 lies about
    7 times above it, so the late-time strength of this run is well above its own noise. Whether it is the same
    with MERCURIUS is not tested beyond about 2 Gyr.
  - The long runs test R, not the direction M1.
- **Reading with sets A and B:** still open. Both V2 short runs were outside the limits (entry e4, report of
  2026-11-06). The paired tests of both sets are running (entry e5). As fixed in section 5:
  - only if A and B agree with Brown & Batygin (outcome 1 there) does this run stand as the long-term behaviour of
    their posterior Planet Nine with our method;
  - otherwise it is reported as not confirmed at long times, together with the outcome of A and B.
- **Model** (criteria section 7): gravity of the Sun and the planets only, massless test bodies, no galactic tide and
  no passing stars. No observational bias: the measures describe the simulated distribution, not what surveys would
  see.

## Model check against Brown & Batygin (2021): galactic tide and passing stars

Section 7 of the criteria left open whether their simulations contained a galactic tide. It was checked on
2026-11-10 against the text of arXiv:2108.09868v2 (26 Aug 2021): section 4.1 read in full, and the whole text
searched for "galactic", "tide", "tidal", "passing" and "stellar".

- **What they integrate** (section 4.1 "Simulations", p. 8):
  - "The orbits of the 5 giant planets and test particles are integrated using the mercury6 gravitational dynamics
    software package (Chambers 1999)", hybrid symplectic/Bulirsch–Stoer, time step 300 days;
  - "Objects that collide with planets or reach r < 4.5 or r > 10000 AU are removed from the simulation".
  - No galactic tide, no passing stars and no other external force is named there.
- **Galactic tide:** not mentioned anywhere in the paper. "Tide" and "tidal" do not occur. "Galactic" occurs only in
  the caption of the sky map (the galactic plane), p. 18.
- **Passing stars:** only in the introduction (section 1, p. 2), as the explanation once favoured for the orbit of
  Sedna: "perturbation by passing stars within the solar birth cluster". It is not part of their simulations.
- **The inner Oort cloud:** bodies scattered inward from it are discussed as a possible contaminant of the observed
  sample (section 2, p. 4; section 6 "Caveats", p. 19). They are handled by excluding the one object with
  a > 1,000 au, not by modelling.

**Result:** as far as the text says, the simulations of Brown & Batygin contain the four giant planets, Planet Nine and
massless test particles, with no galactic tide and no passing stars. Our model makes the same assumption, so the
assumption of criteria section 7 is confirmed for this comparison.
- Two differences remain:
  - their integrator (mercury6, hybrid, 300 days) against ours (v5, dt 0.5 yr);
  - our Sun carries the masses of the inner planets.
- This is a reading of what the text states. The paper does not say explicitly that a tide is absent; it names what
  is integrated, and the tide is not in it.
- Checked against the arXiv version. The journal version (AJ 162, 219) was not compared.

## Not stated here

- No comparison with numbers of Brown & Batygin for this set: the paper has none (D1).
- No statement on Planet Nine itself.
- The result goes into the research note only after the independent review.
