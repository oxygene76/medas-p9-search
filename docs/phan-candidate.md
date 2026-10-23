# The IRAS/AKARI pair of Phan et al. (2025): where it would be in 2026

A plausibility estimate (`tools/phan_candidate.py`, output `runs/phan/`), not an orbit; independent of the
equivalence test.

**Input** (Phan et al. 2025, PASA 42, e064, doi:10.1017/pasa.2025.10024, Table 2 and sec. 4): IRAS F02211-4844,
RA 35.74075°, Dec −48.5125° (co-added scans 26 June–1 September 1983); AKARI-MUSL J0220440-491247, RA 35.18379°,
Dec −49.2135° (three scans on 26 June 2006); 500–700 au; 7–17 Earth masses.

**Model:** for a distance d the same at both epochs, each direction gives a heliocentric position (Earth from
DE440s); straight motion between them; the direction at the date with the full parallax of that date. Monte Carlo
over d (500–700 au), the effective IRAS epoch (within the co-added interval) and the positions (IRAS 20", AKARI 8"
per axis, assumed).

**Result for 2026-12-31 0h UTC:** RA 34.44° (2h 17.8m), Dec −49.99° (ICRS); 68 % region 3.9′ × 1.7′, 95 %
region 7.1′ × 3.3′ (the distance moves the centre by only about ±2′). Earlier: 2014-11-15 RA 34.83°, Dec −49.63°;
2018-11-15 RA 34.73°, Dec −49.76°; 2025-11-15 RA 34.55°, Dec −49.99°.

The implied heliocentric speed is 0.38 au/yr, about the escape speed at 500–700 au (bound in 42 % of the draws),
and the implied orbit plane is inclined 119° to the ecliptic (retrograde, 61°): as Brown pointed out, not a Planet
Nine orbit that could shape the clustering.

**Brightness** (reflected sunlight, opposition; radius from 7–17 Earth masses and a density of 1.27–1.64 g/cm³,
2.9–4.2 Earth radii; geometric albedo 0.2–0.75): V ≈ 19.3–23.0; for the middle values (albedo 0.5) V ≈ 20.4–21.8
at 7 Earth masses and 19.7–21.4 at 17 Earth masses (500–700 au).

**Visibility:** at Dec −50° the region never rises in Germany (highest altitude 90° − latitude − 50°, i.e. −11°
at 51° N, −7° at 47.3° N). Pan-STARRS (Dec > −30°) and ZTF (Dec > −30°) do not cover it. Southern surveys do:
DES (DECam, 2013–2019, the region lies in its wide footprint at about RA 35°, Dec −50°; searched for Planet Nine by
Belyakov et al. 2022), the Legacy Surveys DR10 (DECam), SkyMapper (to about 20–21 mag), and Rubin/LSST.

**ASROC 2026 poster** (Phan, "Searching for triple-detection Planet Nine candidates using far-infrared all-sky
survey data", contribution 138): the public abstract gives no coordinates and no number of candidates; the poster
file is protected. No atlas layer until coordinates are published.

DES check (footprint, exposures, TNO catalogue, detectability): `docs/phan-des.md`.
