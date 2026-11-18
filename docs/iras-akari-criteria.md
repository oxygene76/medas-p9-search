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

## Addendum B (2026-11-03): written after reading the survey papers, before any computation

The survey papers named in 2.5 give several limits each. Fixed here, before any orbit, place or coverage is computed:

**B1. Limits** (the one tied to each survey's own detection rule; "would have detected" stays V ≤ limit − 0.5 mag
in the footprint, as in 2.5):
- ZTF: V = 20.5, the 95 % limit for at least 7 detections (Brown & Batygin 2022, Fig. 1).
- Pan-STARRS1: V = 21.0, the median 95 % limit for at least 9 detections outside the galactic plane (Brown, Holman &
  Batygin 2024, arXiv:2401.17977).
- DES: r = 23.8, the typical limit (Belyakov, Bernardinelli & Brown 2022). With V − r = 0.2 (2.5) this is V = 24.0.

**B2. Footprints:**
- ZTF and Pan-STARRS1: declination above −30° (both papers). For ZTF additionally the galactic latitude |b| > 5°
  (the paper names a strip of about 10° around the galactic plane).
- DES: the papers show the footprint only as a figure. Used instead: the DES round 19 footprint polygon (E. Neilsen,
  2019-03-19), file `des-round19-poly.txt` of the skymap package (github.com/kadrlica/skymap, branch master,
  read 2026-11-03, sha256 `e0f3a1e06ce31284…`).

**B3. Epochs:** the middles of the periods in the papers:
- ZTF 2019-05-20 (2018-06-01 to 2020-05-07);
- DES 2016-07-01 (2013–2019);
- Pan-STARRS1 2012-07-01 (2009–2015).

**B4. Error ellipses (A1):**
- The IRAS Faint Source Catalog could not be read on 2026-11-03: VizieR at CDS and its CfA mirror timed out, IRSA
  answered 504.
- The fallback of A1 applies: a circle of 1σ = 30″ for both detections of Phan et al., and the variant with 90″.

**B5. Planet Nine posterior (2.6),** checked against the abstract of Brown & Batygin 2021 (arXiv:2108.09868):
- m = 6.2 +2.2/−1.3 Earth masses;
- a = 380 +140/−80 au;
- i = 16 ± 5°;
- q = 300 +85/−60 au.
- These are the values of 2.6. The ZTF paper quotes q as 300 +85/−80 au; 2.6 stays with the source.

Nothing in sections 1–4 or in addendum A is changed by this addendum.

## Addendum C (2026-11-03): written after the result (run3 of tools/iras_akari.py at b992cfe); the verdicts stand

Two points of interpretation that the result showed. They change no verdict; they say what two verdicts mean.

**C1. The 5 % threshold of "supported" (section 3) measures the prior, not the data.**
- With r1 and r2 drawn independently in 500–1,000 au, a bound orbit needs |r2 − r1| of at most about 10 au over
  23 years.
- At most a few per cent of the trials can therefore be kept, whatever the positions are: Phan et al.: 0.27–0.71 %.
- So "supported" was not reachable for the two-epoch case by construction.
- No verdict here depends on it: the Phan pair is excluded by the survey criterion.
- For later criteria: a share of the trials that are consistent with the positions within their errors, among the
  bound ones, not among all.

**C2. Q-P for a single-epoch family (A3) has no information.**
- The family is the prior of A3: velocity uniform in direction and magnitude. Its a, q and i come from that prior,
  not from data.
- The verdict "excluded" for Q-P of the two Chen candidates follows the letter of section 3 (0 % of the family in the
  Planet Nine space). It says nothing about the candidates.
- It is reported as "excluded by the letter, not informative".

## Addendum D (2026-11-18): recomputation of the Phan et al. pair with the catalogue error ellipse; written before any computation

Asked for by the project lead on 2026-11-18 ("Vorschlag (b)"). No pilot run, no new criteria for a simulation. The
values below were read before this addendum: the PDF of Phan et al. (arXiv v1 and PASA 42, e064; read on 2026-11-18)
and the IRAS Faint Source Catalog entry; the result of 2026-11-03 is known (it is the reason for this addendum).

**D1. Inputs.**
- **IRAS F02211-4844:** the Faint Source Catalog entry (IRSA table `irasfsc`, queried 2026-11-18): RA 35.740746°,
  Dec −48.512474° (J2000, epoch B1983.5), 95 % error ellipse 18″ × 7″, position angle 79°. As a two-dimensional
  Gaussian: 1σ = 18″/2.4477 × 7″/2.4477 = 7.35″ × 2.86″ at 79°. The catalogue position replaces the rounded one of
  Phan's Table 2 (difference 0.15″).
- **AKARI-MUSL J0220440-491247:** no error is published (the list is not public). The fallback of A1 stays: 1σ = 30″,
  variant 90″.
- **AKARI epoch:** 2006-12-26 (PDF, section 4.2: the two detections of 26 December 2006; the three scans of 26 June
  2006 without detection). The June variant of A2 is not computed again.
- Everything else as in sections 2–3 and addenda A–C: r1, r2 uniform in 500–1,000 au, 10^5 trials, seed 2026, the
  temperature grid 30–50 K and the albedo grid 0.2–0.75 (A4), the survey limits and footprints (B).

**D2. Computation.**
- `tools/iras_akari.py` with two new cases, the code change committed before it runs: `phan-fsc` (IRAS ellipse,
  AKARI 30″) and `phan-fsc-akari90` (IRAS ellipse, AKARI 90″).
- **DES coverage per exposure** for the kept orbits of `phan-fsc`:
  - the method of `docs/phan-des.md` (`tools/phan_des.py`), evaluated at the centre time of every DES wide exposure;
  - the same archive list, footprint and CCD map (`runs/phan-des/`, sha256 there);
  - the places from the kept orbits (two-body, Earth from DE440s, light time) instead of the straight-line draws of
    `tools/phan_candidate.py`, which used the June epoch.
  - The detection model and the recovery criteria of Belyakov, Bernardinelli & Brown 2022 as in `docs/phan-des.md`:
    per-exposure efficiency, NUNIQUE ≥ 7, ARCCUT ≥ 180 days, a triplet within 90 days.

**D3. What the verdict "excluded" rests on, and when each part carries it.**
1. **The optical brightness from the infrared fluxes.** It carries the verdict if V ≤ 23.5 (the DES limit V 24.0
   minus the margin of 0.5 mag of 2.5) at the DES epoch for at least 95 % of the kept weight, for every combination
   of both models:
   - (a) the grid of A4: blackbody of 30–50 K fitted to the fluxes, geometric albedo 0.2–0.75;
   - (b) Phan's own assumptions: radius from 7–17 Earth masses at a density of 1.27–1.64 g/cm³ (their 1.46 and the
     Uranus and Neptune values), albedo 0.2–0.75.
   - Reported beside it, for information and not deciding: albedos below 0.2 (0.05 and 0.1) and the temperature range
     28–53 K that Phan et al. quote.
2. **The DES search.** It carries the verdict if all of these hold:
   - (a) the published search covers bodies at 500–700 au: distance or motion range, with page;
   - (b) it states no restriction that excludes a retrograde or highly inclined bound orbit: orbit linking, priors,
     injected population, with page;
   - (c) the recovery probability under its own criteria (D2), on the exposures that hold the kept orbits, is at least
     0.9 for V ≤ 23.5 in at least 95 % of the kept weight.
   - The source is the paper of Belyakov, Bernardinelli & Brown 2022 (AJ 163, 216) and the search it uses (Bernardinelli
     et al. 2022, ApJS 258, 41). Read after this addendum, with page numbers in the report. If the papers say
     nothing on (a) or (b), that part does not carry the verdict.

**D4. Verdicts.**
- Both parts of D3 carry it, and the survey criterion of section 3 holds: Q-O **"excluded"**, as on 2026-11-03.
- One of them does not: Q-O **"not excluded, but outside the Planet Nine parameter space"**, if Q-P gives less than
  5 % of the kept weight inside the space of 2.6; otherwise Q-P as in section 3.
- Q-P is computed in either case and reported.

Nothing in sections 1–4 or in addenda A–C is changed by this addendum.
