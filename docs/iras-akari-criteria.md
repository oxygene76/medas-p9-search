# IRAS/AKARI Planet Nine candidates: criteria, fixed before the analysis (2026-11-03)

Asked for by the project lead on 2026-11-03 (track R, laptop only). The candidates:
- the IRAS/AKARI pair of Phan et al. 2025 (arXiv:2504.17288);
- the two AKARI candidates of Chen et al. 2025 (arXiv:2506.12854).

This file is written, committed and stamped with OpenTimestamps before any orbit is computed and before any survey
coverage at the candidates' places is looked at. The input values (positions, epochs, fluxes, their errors) are
taken from the papers as printed, with the place they come from. After the first result nothing here is changed;
anything found missing goes into a dated addendum, marked as written after a result.

## 1. What is asked, per candidate

Two separate questions, each with its own verdict:
- **Q-O (object):** is a real distant body on a bound orbit through the published detections consistent with the
  published data and with the surveys that have looked at the predicted places since?
- **Q-P (Planet Nine):** are those orbits inside the Planet Nine parameter space that produces the clustering we
  model (Brown & Batygin 2021 posterior; sets A and B; the production run)?

Q-P is asked only if Q-O is not "excluded".

## 2. Methods (fixed now)

**2.1 Inputs.**
- Positions with their published errors; where only a beam or an error ellipse is given, that ellipse as a
  two-dimensional Gaussian with the stated size as 1σ (or as stated).
- Epochs as published.
- If a paper gives several positions for the same detection (e.g. abstract against table), the table counts and
  the difference is reported.

**2.2 Statistical ranging** (as Virtanen, Muinonen & Bowell 2001, for two epochs):
- For each candidate pair of detections, 10^5 trials:
  - draw both positions from their error distributions;
  - draw the heliocentric distances r1 and r2 at the two epochs uniformly in 500–1,000 au;
  - solve Lambert's problem (two-body, Sun with the masses of the planets inside, the prograde and the retrograde
    solution) for the orbit through both points;
  - keep the bound orbits (e < 1).
- Weights:
  - uniform priors in r1, r2; every kept trial has weight 1 (no Jacobian correction), so the result is the family
    of bound orbits compatible with the positions and the stated distance range;
  - a second weighting, reported beside it: the flux-based distance prior of 2.4 (if the paper gives a size or
    temperature model).
- For a single detection without a second epoch there is no ranging: only the distance range and the sky motion
  limits of bound orbits are given, and Q-O is "not decidable" by construction.

**2.3 The search region in 2026-11:**
- Each kept orbit is propagated (two-body) to 2026-11-15 0h UTC and to the epochs of the surveys in 2.5.
- The predicted places as a weighted sky density.
- The regions holding 68 % and 95 % of the weight, as polygons on a HEALPix map (nside 256), with their areas.

**2.4 Predicted brightness V:**
- From the published infrared fluxes and the paper's own thermal model, if it gives one: the radius R (or the
  range of R).
- Otherwise a blackbody at the equilibrium temperature at the orbit's distance plus an internal-heat term as
  stated by the authors.
- V = H + 5 log10(r Δ) (phase angle negligible beyond 400 au), with H from R and a geometric albedo p:
  - p from 0.2 to 0.75: Neptune-like 0.4–0.5 as the middle;
  - the range over p is reported.
- V is computed per kept orbit, for 2026-11 and for each survey epoch.

**2.5 Survey coverage:**
- The three surveys behind the atlas layer "Planet 9: still open", with their footprints and limiting magnitudes
  for a slow Planet Nine as stated in the papers that define the layer's flags (medas-notary-web,
  `docs/planet9-layers.md`):
  - ZTF: Brown & Batygin 2022 (AJ 163, 102);
  - DES: Belyakov, Bernardinelli & Brown 2022 (AJ 163, 216);
  - Pan-STARRS: Brown, Holman & Batygin 2024 (AJ 167, 146).
  - The limits are taken from these papers as printed, with the place they come from, like the candidate inputs.
    No value from memory.
- Epochs: the middle of each survey's period in those papers. Beyond 500 au a body moves less than about 0.05° per
  year, which is reported against the footprint edges.
- A survey **would have detected** a kept orbit if:
  - the orbit's predicted place lies in the survey's footprint at an epoch of the survey;
  - its V there, converted to the survey band (V − r = 0.2 for a Neptune-like reflectance), is at least 0.5 mag
    brighter than the survey's limit;
  - its motion during an exposure is below one seeing disk (true beyond 300 au).
- The share of the weight that would have been detected is reported per survey and in total.

**2.6 Planet Nine parameter space:**
- Brown & Batygin 2021 posterior: a = 380 +140/−80 au, q = 300 +85/−60 au, i = 16 ± 5°, m = 6.2 +2.2/−1.3 Earth masses.
- "Inside" means a and q within these ranges and i within 16 ± 10°, taken from the paper as printed.
- Sets A (7, 500 au, e 0.33, i 17°) and B (5, 300 au, e 0.15, i 17°) are reported as points beside it.
- The mass from 2.4, if the paper gives one, is compared with the range of m.
- Note: the orbit's i is compared with the invariable plane as in `docs/bb2021-comparison-criteria.md`; the
  ecliptic value is reported too.

**2.7 "Still open":**
- The share of the 95 % region of 2.3 that lies inside the 90 % band of the atlas layer "Planet 9: still open" for
  the date nearest to 2026-11 (`public/atlas/data/planet9/open-<date>.js` of feat/atlas-p9-open, any magnitude).
- The layer is the density of the open orbits of Brown's reference population (the three flags 0). It is not a
  coverage map. "Inside" therefore means: where the hypothesis' still-open orbits are, not that no survey looked
  there.

**2.8 Own observatory** (Mewlon 300, limit about V 21 in the project lead's estimate):
- the share of the weight with V ≤ 21.0 in 2026-11;
- the area of the 95 % region against the field of view, which the project lead states. Until then: in square
  degrees only.

## 3. Verdicts (fixed now)

**Q-O, per candidate:**
- **Excluded** if one of these holds:
  - no bound orbit with r in 500–1,000 au passes through both detections within their 3σ errors (fewer than 0.1 %
    of the trials kept);
  - or at least 95 % of the kept weight would have been detected by the surveys of 2.5 and was not reported
    (that no detection has been reported is taken from the literature at the date of the report; the report names
    what was checked).
- **Supported** if all of these hold:
  - at least 5 % of the trials are kept;
  - at most 50 % of the kept weight would have been detected;
  - the predicted V of the kept weight is consistent with the published infrared fluxes within their 2σ errors for
    some albedo in 0.2–0.75.
  - "Supported" means "consistent with all checks here", not "confirmed": only a new detection at a predicted place
    confirms.
- **Not decidable** otherwise, among them: a single detection without a second epoch, more than 50 % but less than
  95 % of the weight that would have been detected, or a brightness range across the survey limits.

**Q-P, per candidate (only if Q-O is not "excluded"):**
- **Supported:** at least 50 % of the kept weight inside the parameter space of 2.6, and the mass from the fluxes
  (if given) within the posterior range of m.
- **Excluded:** less than 5 % of the kept weight inside.
- **Not decidable** otherwise.

## 4. Report

`docs/iras-akari-candidates.md`. Per candidate:
- the inputs with their sources;
- the ranging (kept share, distributions of a, e, i, q, r);
- the search region in 2026-11 (map and polygons, areas);
- V;
- the survey coverage per survey;
- the share in "still open";
- the observatory's chance;
- the two verdicts with the numbers that led to them.

The code of the analysis is committed and named with its commit; random numbers with a fixed seed (2026).

## Addendum A (2026-11-03): written after reading the inputs, before any computation

Sections 1–4 above were written before the values of the two papers were read. Reading them (arXiv v1 of both,
read 2026-11-03) showed four gaps. How they are handled is fixed here, before any orbit, place or coverage is
computed:

**A1. Phan et al.: no position errors and no frame in the paper (their Table 2).**
- The positions are taken as ICRS (J2000).
- The error ellipses are taken from the catalogue entries themselves:
  - IRAS F02211-4844: the IRAS Faint Source Catalog in VizieR (II/156A), its error ellipse;
  - AKARI-MUSL J0220440-491247: the ellipse given with the source (to be named with its source in the report).
- If a catalogue gives none: a circle of 1σ = 30″, the ranging also repeated with 3 × that, and both reported.

**A2. Epochs.**
- IRAS: the paper's detection is a sum of scans from 1983-06-26 to 1983-09-01. Its epoch is drawn uniformly in that
  interval per trial.
- AKARI (Phan): the paper states 2006-12-26 in its figure caption, in section 6 and in most of section 4.2, and once
  "26 June 2006" in section 4.2. The 26 December 2006 is used, and the other reading is reported as a variant.

**A3. Chen et al.: each candidate has one epoch only** (two detections within 24 h, none half a year later).
- As fixed in 2.2, Q-O is "not decidable" for each of them alone.
- Computed for them: the region in 2026-11 reachable by bound orbits through the single position with r in
  500–1,000 au. Per trial: the position and epoch as given, r uniform, and the velocity uniform in direction and
  uniform in magnitude below the escape speed at r (no other constraint). The 68 % and 95 % regions of that
  family, as in 2.3.
- Additionally, the two Chen candidates as one body at two epochs (2006-07-30 and 2007-07-28) are ranged as in 2.2
  ("pair hypothesis"), with Q-O for that pair.

**A4. Brightness.**
- Neither paper gives a radius from its fluxes for its candidate. Phan's 7–17 Earth masses and 500–700 au are
  assumptions of their search; Chen state that the physical quantities cannot be determined.
- Therefore 2.4 uses a blackbody of temperature T in 30–50 K (the range for a planet of 5–20 Earth masses with
  internal heat beyond 500 au, Fortney et al. 2016, ApJL 824, L25, to be quoted with its numbers in the report).
- Fitted to the 90 and 100 µm fluxes (those not flagged as unreliable): the radius R for each kept orbit's distance
  and each T on a grid, then V as in 2.4.
- A V range that spans the survey limits leads to "not decidable" under 3, as fixed.

Nothing in sections 1–4 is changed by this addendum.
