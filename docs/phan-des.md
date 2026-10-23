# The Phan et al. (2025) pair in the Dark Energy Survey

Question: if the IRAS/AKARI pair of Phan et al. (2025) were one body at 500–700 au with V ≈ 19.3–23.0
(`docs/phan-candidate.md`), would DES (August 2013 to January 2019) have found it?

Tool: `tools/phan_des.py`. It uses the Monte Carlo draws of `tools/phan_candidate.py` (same seed), evaluated at
the centre time of every exposure with full parallax. Output and inputs are in `runs/phan-des/` (not in git).

## Inputs (downloaded 23 October 2026)

| file | source | sha256 |
|---|---|---|
| `archive-raw.json` | NOIRLab Astro Data Archive, `POST https://astroarchive.noirlab.edu/api/adv_search/find/?limit=2000`: DECam, `proc_type` raw, `obs_type` object, centre RA 32.5–37.0°, Dec −51.2 to −48.0°, caldat 2013-08-01 to 2019-02-28 (174 exposures) | `3626ca59…40cc0` |
| `des-round19-poly.txt` | DES round19 footprint (E. Neilsen, March 2019), github.com/kadrlica/skymap `skymap/data/` | `e0f3a1e0…79ddf` |
| `ccd_corners_xy_fill.dat` | DECam CCD corners about the pointing, same repository; without CCDs 2 and 61 | `633fba2f…be2d` |
| `tno.tsv` | VizieR J/ApJS/258/41/catalog (Bernardinelli et al. 2022), 814 objects | `a189923f…dc73c` |

The query box covers every pointing whose 1.1° field could contain the track (RA 34.7–34.85°, Dec −49.6 to −49.8°).

## Result

**1. Footprint and exposures**

- All draws lie inside the DES wide footprint in every season from 2013 to 2018.
- 34 DES wide exposures (proposal 2012B-0001) in g, r, i or z put the track on a CCD in at least half of the draws:
  - by band: g 10, r 9, i 5, z 10;
  - 25 nights in four seasons: 12 in 2013, 5 in 2016/17, 5 in 2017/18, 3 in 2018;
  - the 2014/15 and 2015/16 seasons give no usable griz exposure.
- Robustness:
  - The orientation of the CCD map is not certain. Mirroring it in x, in y, or turning it by 180° changes this to 34 exposures on 24–25 nights.
  - CCD 2 is treated as dead throughout. In fact it was dead only from November 2013 to December 2016, so this is conservative.
- The archive lists all raw exposures. DES Y6 used the 76,217 of 83,706 wide exposures that passed quality cuts, so a few of these may be missing from the search. The margin is large: 25 nights against the 7 required.
- Other programmes add exposures that the DES search did not use, for example 7 i-band exposures from 2017B-0110 on 14–25 August 2017.

**2. DES TNO catalogue (Bernardinelli et al. 2022)**

- The largest discovery distance in the catalogue is 96.3 au, so nothing is near 500–700 au.
- No object lies within 5° of the track (direction of the catalogue position vector). The nearest is 2013 TB187 at 10°, a scattering object at 35 au.

**3. Detectability** (criteria of Belyakov, Bernardinelli & Brown 2022, AJ 163, 216)

The criteria per exposure:

- p(m) = c / (1 + exp(k (m − m50))), times the transient efficiency 0.955;
- c = 0.943 and k = 6.37;
- median m50: g 24.2, r 24.0, i 23.5, z 22.7.

The criteria for recovery:

- NUNIQUE ≥ 7;
- ARCCUT ≥ 180 days;
- a triplet of nights within 90 days.

Colours from Belyakov et al. Table 1:

| colours | V | g | r | i | z | P(recovered) | median NUNIQUE |
|---|---|---|---|---|---|---|---|
| Neptune-like (g−r −0.3, g−i −1.35, g−z −2.15) | 19.3 | 19.1 | 19.4 | 20.5 | 21.3 | 1.00 | 20 |
| | 21.0 | 20.8 | 21.1 | 22.2 | 23.0 | 1.00 | 14 |
| | 23.0 | 22.8 | 23.1 | 24.2 | 25.0 | 0.98 | 10 |
| | 23.5 | 23.3 | 23.6 | 24.7 | 25.5 | 0.95 | 9 |
| | 24.0 | 23.8 | 24.1 | 25.2 | 26.0 | 0.67 | 8 |
| | 24.5 | 24.3 | 24.6 | 25.7 | 26.5 | 0.00 | 2 |
| BB21 fiducial (g−r 0.53, g−i 0.55, g−z 0.6 assumed) | 19.3–22.0 | | | | | 1.00 | 20 |
| | 23.0 | 23.3 | 22.8 | 22.8 | 22.7 | 1.00 | 16 |
| | 24.0 | 24.3 | 23.8 | 23.8 | 23.7 | 0.49 | 7 |

With the mirrored CCD maps, the lowest value for V ≤ 23 is 0.90 (Neptune-like, V = 23).

Belyakov et al. assume that every object meeting the three criteria is found, and report "100% efficiency for
objects in the catalog above 200AU". The search covers 29–2500 au. It has no inclination cut: the catalogue
contains orbits up to 96°, and the candidate's orbit plane is at 119°.

## Conclusion

- The track lies inside the DES footprint and is on silicon on 25 nights in four seasons.
- Over the whole range V 19.3–23.0, DES would have recovered such a body with a probability of at least 0.9; the main
  estimate is at least 0.97.
- The catalogue contains nothing beyond 96 au.
- **So the pair is probably not one real body at 500–700 au on this track, or it is fainter than V ≈ 24.**
  - V ≈ 24 is about 1 mag below the faint end of `docs/phan-candidate.md`. Even the faintest case there (7 Earth masses, 1.64 g/cm³, 700 au) would need an albedo below about 0.1, or a smaller body.
  - Other distances give other tracks; they are not covered here.

There is one remaining gap, in the linking. The pair finding of Bernardinelli et al. keeps pairs that "could contain
a common bound TNO within the distance bin". The implied transverse speed of the pair is a median 1.04 times the
escape speed, and bound in only 42 % of the draws (`docs/phan-candidate.md`). Whether the distance bins leave
enough room for that is not stated. Even if every unbound draw were lost, P(recovered) would stay at about 0.4 or
more. A body faster than the escape speed would also not be a bound planet. Coverage is not missing, so the
fallback to single Legacy Surveys DR10 exposures is not needed. DR10 contains these same DES exposures. The most
direct ones to inspect are those with the track on one CCD in more than 90 % of the draws:

| expnum | night | band | CCD | RA, Dec (mean of the draws) |
|---|---|---|---|---|
| 233617, 233618 | 2013-09-12 | g, r | 16 | 34.993, −49.556 |
| 248090 | 2013-10-28 | g | 5 | 34.890, −49.596 |
| 253510 | 2013-11-12 | z | 5 | 34.853, −49.598 |
| 605285, 605286 | 2016-12-29 | r, g | 29 | 34.688, −49.666 |
| 605571 | 2016-12-30 | r | 29 | 34.687, −49.665 |
| 615087 | 2017-01-31 | z | 29 | 34.670, −49.623 |

The CCD numbers depend on the assumed orientation of the CCD map.
