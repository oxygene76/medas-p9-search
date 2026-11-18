# The IRAS/AKARI Planet Nine candidates (track R, 2026-11-03)

The far-infrared candidates of two papers, checked against bound orbits, the optical surveys and our model:
- **Phan et al. 2025** (arXiv:2504.17288, PASA 42, e064): one IRAS/AKARI pair.
- **Chen et al. 2025** (arXiv:2506.12854, accepted by PASA): two AKARI candidates.

Criteria fixed before the analysis: `docs/iras-akari-criteria.md`.
- Sections 1–4 were written before the papers' values were read.
- Addendum A after reading them, addendum B after reading the survey papers, both before any computation; both
  committed and stamped with OpenTimestamps:
  - `runs/notary/iras-akari-criteria-0b0c773.md` (sha256 `f5cd796d…731e`);
  - `runs/notary/iras-akari-criteria-f0cc090.md` (sha256 `4c4e5b6d…ef28`).
- Addendum C was written after the result: two points of interpretation; no verdict changed.

Code: `tools/iras_akari.py` at b992cfe, tests `tests/test_iras_akari.py`; seed 2026, 10^5 trials per case.
Result: `runs/iras-akari/run3/` (not in git; `result.json` sha256 as of run2 `44260f1b…ba87`, the same numbers plus
the ellipses). Values of the papers as printed (arXiv v1 of both, read 2026-11-03).

## Results in brief

| case | Q-O (object) | Q-P (Planet Nine) | why |
|---|---|---|---|
| Phan et al.: IRAS F02211-4844 (1983) + AKARI-MUSL J0220440-491247 (2006-12-26) | **excluded** | – (not asked) | Bound orbits exist, but all of them lie in the DES footprint, where DES would have seen the body (V 18.0–22.3 against the limit V 24.0) for every temperature and albedo of the grid. DES reported no such body. |
| Chen et al.: FISSSDL J0250422-150114 (2007-07-28) | **not decidable** | excluded by the letter, not informative (C2) | One epoch only. If real at 500–1,000 au: V 17.0–22.1, in the DES footprint; DES would have seen it in at least 99.9 % of the cases. |
| Chen et al.: FISSSDL J0301112-164240 (2006-07-30) | **not decidable** | excluded by the letter, not informative (C2) | As above: V 17.2–22.3, DES at least 99.9 %. |
| Chen et al.: both as one body at two epochs | **excluded** | – | No bound orbit through both positions (0 of 10^5 trials): 2.95° in one year. Chen et al. reject such pairings too (all separations above 22.9′). |

**"Excluded" here means:** no body with these infrared fluxes on a bound orbit at 500–1,000 au can sit at these
places without having been seen by DES, under the brightness model of addendum A4. It does not say the infrared
sources are not real. They may be noise, cosmic rays (Chen et al. estimate about half of all single detections) or
other objects.

## 1. Inputs (as printed)

| | Phan et al. (Table 2) | Chen et al. (Table 2) |
|---|---|---|
| position 1 | IRAS F02211-4844: RA 35.74075°, Dec −48.5125° | J0250422-150114: RA 42.676°, Dec −15.021° |
| position 2 | AKARI-MUSL J0220440-491247: RA 35.18379°, Dec −49.2135° | J0301112-164240: RA 45.297°, Dec −16.711° |
| frame | not given (taken as ICRS, A1) | J2000 |
| position errors | not given (catalogues not readable on 2026-11-03: 1σ 30″, variant 90″; A1, B4) | 3.5″ × 2.3″, PA 340.3° / 340.7° |
| epochs | IRAS: scans of 1983-06-26 to 1983-09-01 (drawn uniformly); AKARI: 2006-12-26 (variant 2006-06-26, A2) | 2007-07-28; 2006-07-30 (two detections within 24 h each) |
| fluxes | S60 0.24, S65 0.09 (flagged "might be unreliable"), S90 0.27, S100 0.52 Jy; no errors | 90 µm per scan: 0.61 / 1.62 and 1.27 / 0.51 Jy; no errors |

## 2. Ranging (Phan et al.)

10^5 trials per case, r1 and r2 uniform in 500–1,000 au, Lambert in both directions, bound orbits kept (2.2):

| case | kept | r (5–95 %) | a (median, 5–95 %) | e (median) | q (median, 5–95 %) | i vs invariable plane |
|---|---|---|---|---|---|---|
| 30″ | 675 (0.68 %) | 507–657 au | 1,088 au (442–11,146) | 0.63 | 426 au (220–640) | 116.0–118.0° |
| 90″ | 707 (0.71 %) | 507–669 au | 1,119 au (427–15,271) | 0.63 | 413 au (225–644) | 114.7–119.1° |
| 30″, AKARI 26 June 2006 | 267 (0.27 %) | 504–578 au | 1,804 au (757–15,855) | 0.73 | 500 au (379–569) | 119.1–120.4° |

- **All bound orbits are retrograde.**
  - This follows from the two heliocentric places alone, once the parallax is removed. With uniform distances,
    only the short way between them is fast enough to stay bound.
  - Checked independently: astropy's transformation of the orbit poles to the ecliptic gives 116° (median).
  - Planet Nine of Brown & Batygin 2021 and our sets A and B are prograde (i 16–17°).
- The kept share is a few tenths of a per cent by construction (C1).

## 3. Where in 2026-11 (2026-11-15 0h UTC, geocentric, light time included)

| case | centre (RA, Dec) | 95 % ellipse (semi-axes, PA) | 95 % region at HEALPix nside 256 |
|---|---|---|---|
| Phan, 30″ | 35.006°, −49.768° | 4.5′ × 3.4′, 2° | 0.105 deg² (2 pixels: the ellipse is smaller than a pixel of 13.7′) |
| Phan, 90″ | 35.011°, −49.767° | 8.4′ × 7.7′, 131° | 0.157 deg² |
| Phan, AKARI June | 34.514°, −50.032° | 5.4′ × 2.7′, 5° | 0.105 deg² |
| Chen J0250422 (one epoch) | 42.589°, −15.091° | 51′ × 41′, 32° | 0.89 deg² |
| Chen J0301112 (one epoch) | 45.211°, −16.784° | 71′ × 43′, 163° | 1.00 deg² |

Maps (north up, east left, the 95 % ellipse in red, a 10′ bar in blue) and the predicted places as npz:
`runs/iras-akari/run3/*-2026-11.png`, `*-points-2026-11.npz`.

## 4. Brightness

**Method:** the radius of a blackbody of 30–50 K that gives the fluxes at the trial's distance (A4), then V for
geometric albedos 0.2–0.75 (2.4).
- Phan et al.: the IRAS 100 µm and AKARI 90 µm fluxes, their log mean; S65 is flagged by the authors.
- Chen et al.: the log mean of the two 90 µm scan fluxes.

| case | radius (median) at 30 / 40 / 50 K | V in 2026-11 (median), over T and albedo |
|---|---|---|
| Phan, 30″ | 54,400 / 28,700 / 19,400 km (8.5 / 4.5 / 3.0 Earth radii) | 18.3 (30 K, p 0.75) to 22.0 (50 K, p 0.2) |
| Chen J0250422 | 122,700 / 62,600 / 41,500 km (19 / 9.8 / 6.5 Earth radii) | 17.7 to 21.5 |
| Chen J0301112 | 110,200 / 56,200 / 37,300 km (17 / 8.8 / 5.8 Earth radii) | 18.0 to 21.8 |

**Not modelled:** a non-blackbody spectrum. Fortney et al. 2016 show the far-infrared departing from it; their
T_eff is about 35–50 K and the radius 2.7–6 Earth radii for 5–20 Earth masses.

**What the radii mean, for information:**
- Phan's radius at 45–50 K (3.0–3.6 Earth radii) fits such a planet. At 30–40 K it does not.
- Chen's radii are at least 5.8 Earth radii (J0301112 at 50 K), at the upper end of that range or above it; at 30–45 K
  they are 7–19 Earth radii, larger than any planet of 5–20 Earth masses in Fortney's models.

## 5. Survey coverage (2.5, B)

**Limits and footprints** (addendum B):
- ZTF V 20.5, Pan-STARRS1 V 21.0, DES V 24.0 (r 23.8 + 0.2).
- "Would have detected" means in the footprint and V at least 0.5 mag brighter than the limit.
- Epochs: the middles of the survey periods.

| case | ZTF (dec > −30°, \|b\| > 5°) | Pan-STARRS1 (dec > −30°) | DES (round 19 polygon) | any |
|---|---|---|---|---|
| Phan (all three variants) | outside | outside | in the footprint: 100 % detected for every T and albedo | 100 % for every T and albedo |
| Chen J0250422 | 0–100 %, by T and albedo | 0–100 % | 99.9 % for every T and albedo | ≥ 99.9 % |
| Chen J0301112 | 0–100 % | 0–100 % | 99.9 % for every T and albedo | ≥ 99.9 % |

- **Footprint checked:** the DES round 19 polygon reaches Dec +5° at RA ≤ 45° and about −9° at RA 45–47°. Both Chen
  positions are inside, and so is Phan's (Dec −49°).
- **Reported results** (Belyakov, Bernardinelli & Brown 2022; Brown, Holman & Batygin 2024): neither DES nor
  Pan-STARRS nor ZTF reported a Planet Nine.
- **Limit of this check:** footprint and limiting magnitude stand for detection.
  - DES's recovery tests (Belyakov et al. 2022) used Brown's reference population of prograde Planet Nine orbits.
  - Whether DES's pipeline finds a retrograde body at 510–660 au as reliably is assumed, not shown.
  - The epochs are the survey middles. Beyond 500 au a body moves less than 0.05° per year, far inside the footprint
    here.

## 6. Our model and the atlas layer

**Planet Nine parameter space** (2.6; Brown & Batygin 2021: a 380 +140/−80 au, q 300 +85/−60 au, i 16 ± 5°, checked
against their abstract):
- **Phan:** 0 % of the bound orbits inside, because they are retrograde. They match neither the production run
  (6.2 Earth masses, a 380 au, q 300 au, i 16°) nor set A (7, 500 au, e 0.33, i 17°) nor set B (5, 300 au, e 0.15,
  i 17°). The distances (510–660 au) alone would fit set A's orbit (q 335 to Q 665 au).
- **Chen:** a single epoch gives no orbit (C2).

**Atlas layer "Planet 9: still open"** (`open-2026-07-01.js`, the 90 % band):
- Phan: 0 % of the 95 % region and 0 % of the predicted places.
- Chen: 0 % of the 95 % region and at most 0.008 % of the places.
- Both sky regions lie where the reference population's orbits are already ruled out by DES or by ZTF and
  Pan-STARRS. That agrees with section 5.

## 7. Own observatory (Mewlon 300, 0.8× reducer, IMX664: 9.8′ × 5.5′, limit about V 21)

**Phan, 2026-11, RA 35.0°, Dec −49.8°:** at a declination of −50° this never rises north of latitude 40° N (highest
altitude 40° − latitude), so it is out of reach from Central Europe. Should it be observed from elsewhere:
- the 95 % ellipse (4.5′ × 3.4′ semi-axes) needs about 2 fields;
- V ≤ 21 holds for the whole family at 30–35 K;
- at 40 K for albedo ≥ 0.4;
- at 45–50 K only for high albedos (p 0.75: 100 %; p 0.2: 0 %).

**Chen, Dec −15° to −17°:** observable in November from Central Europe, low in the south (at 50° N at most 23–25°
altitude).
- 95 % ellipses 51′ × 41′ and 71′ × 43′ (semi-axes): about 120 and 180 fields.
- V ≤ 21 for 6–100 % of the family, by temperature and albedo.
- The single-epoch family is the prior of A3, not a prediction. A search there would test the prior, not the
  candidate.

**Verdict for the observatory:** no worthwhile chance.
- The Phan region is out of reach.
- The Chen regions are large.
- If the candidates were bodies at 500–1,000 au, the optical surveys would already have seen them (section 5).

## 8. Limits of this report

- Phan et al. give no position errors. The catalogues could not be read on 2026-11-03, so 30″ (and 90″) were
  assumed. With 90″ the result is the same.
- No flux errors in either paper. The brightness rests on a blackbody of 30–50 K (A4). A body colder than 30 K or
  hotter than 50 K, or darker than albedo 0.2, is outside the grid.
- The survey check uses footprints and limits, not the surveys' own detection lists at these places (section 5).
- Two-body orbits around the Sun with the planets' masses inside, no perturbations: over 23 years at 500 au this
  is far below the position errors.
- Values of the papers from the arXiv HTML of v1. The PDF was not converted.

## 9. Addendum D (2026-11-18): the Phan et al. pair recomputed with the catalogue error ellipse

As fixed in addendum D of `docs/iras-akari-criteria.md` (52ff92a, timestamped before the computation). Code
`tools/iras_akari.py --addendum-d` (7cfb8a6) and `tools/phan_des.py --orbits … --per-orbit 400` (48f2ee3), both
committed before they ran and run from clean checkouts. Results in `runs/iras-akari/runD-7cfb8a6/` (not in git;
`result.json` sha256 `85c07f7f…`, `phan-des-fsc-perorbit.json` `b4f447a6…`).

**Inputs, new:**
- IRAS position and error from the Faint Source Catalog: 95 % ellipse 18″ × 7″ at 79° (1σ 7.35″ × 2.86″).
- AKARI epoch 2006-12-26, now from the PDF. Phan et al. publish no AKARI error, so 30″ is used, with a variant of 90″.

**Ranging** (10^5 trials, seed 2026):

| case | kept | r (5–95 %) | a (median) | q (median) | i vs invariable plane (5–95 %) | 95 % region 2026-11 |
|---|---|---|---|---|---|---|
| IRAS ellipse, AKARI 30″ | 679 (0.68 %) | 507–657 au | 1,089 au | 430 au | 116.1–118.0° | 4.4′ × 3.3′ |
| IRAS ellipse, AKARI 90″ | 694 (0.69 %) | 507–665 au | 1,106 au | 407 au | 115.2–118.6° | 7.7′ × 7.3′ |

- All bound orbits are still retrograde.
- Planet Nine parameter space: 0 % of the kept weight (Q-P "excluded").
- The narrower IRAS error changes the family only a little; the AKARI error, still assumed, dominates.

**D3.1, the brightness from the infrared fluxes: carries the verdict.**
- In every deciding combination V ≤ 23.5 holds at the DES epoch for 100 % of the kept weight:
  - (a) blackbody 30–50 K fitted to the fluxes, albedo 0.2–0.75;
  - (b) Phan's radii from 7–17 Earth masses at 1.27–1.64 g/cm³, 18,300–26,700 km, albedo 0.2–0.75.
- The span of V over all of these is 18.1–22.8.
- For information, outside the deciding grid:
  - albedo 0.1 keeps V ≤ 23.5 for 94–100 % of the weight;
  - albedo 0.05 does not in every case: 38–53 % for 7 Earth masses, 47 % at 50 K, 15 % at 53 K.
  - A very dark body (albedo ≲ 0.05) could therefore escape this limit.

**D3.2, the DES search: does not carry the verdict.**
- **(a) Distance range, carries.** Belyakov, Bernardinelli & Brown 2022 (arXiv:2203.07642, PDF sha256
  `d5b0bb52…d4c7`) give two statements:
  - p. 3: "Bernardinelli et al. (2022) reported the search for KBOs to be >99% complete for objects at distances
    29 < d < 2500 AU … that appear in at least 7 nights of data in at least 2 opposition seasons with at least a
    triplet of detections per season";
  - p. 5: "complete to a magnitude of r≈23.8 for distances 29 < d < 2500 AU and 100% efficiency for objects in the
    catalog above 200AU".
- **(b) No restriction against retrograde orbits: not established.**
  - Belyakov et al. test only the reference population of Brown & Batygin 2021b (p. 2–3), whose orbits come from the
    prograde Planet Nine posterior.
  - p. 5: "we do not search for these objects using a full pipeline that would recover orbits".
  - Neither page says anything about retrograde or highly inclined bodies. The linking of Bernardinelli et al. 2022
    was not read; since (c) does not hold either, it would not change the verdict.
- **(c) Recovery on the actual exposures: does not hold.**
  - Coverage of the kept orbits with the December epoch: 35 DES wide exposures on 26 nights in four seasons put the
    track on a CCD (the old analysis with the June epoch: 34 exposures, 25 nights).
  - Recovery probability per orbit, with the criteria of Belyakov et al.: share of the orbits with P ≥ 0.9.

  | V | Neptune-like colours | BB21 colours |
  |---|---|---|
  | 21.0 | 0.97 | 1.00 |
  | 22.0 | 0.90 | 1.00 |
  | 22.8 (bright end of D3.1's faint limit) | 0.75 | 1.00 |
  | 23.5 | 0.71 | 0.88 |

  - Required were at least 0.95 up to V 23.5. That fails for both colour sets.
  - The mean recovery probability stays high: 0.88 (Neptune-like) and 0.95 (BB21) at V 23.5; 0.90 and 1.00 at V 23.0.
    A body of this kind would probably have been found, but not with the certainty fixed in D3.2.

**Verdict (D4):** Q-O **"not excluded, but outside the Planet Nine parameter space"**; Q-P "excluded" (0 %).
- **Against 2026-11-03:** The earlier "excluded" rested on footprint and limiting magnitude alone. The per-exposure
  recovery and the missing statement on retrograde orbits do not carry it with the certainty required here.
- **What stands:**
  - Every bound orbit through both detections is retrograde (i ≈ 116–118° to the invariable plane).
  - None lies in the Planet Nine parameter space that produces the clustering we model.
  - If the pair is one body, it is not this Planet Nine.
- **What this does not say:** that the infrared sources are a real body. The verdict only removes "excluded" as a
  statement about the optical surveys.
