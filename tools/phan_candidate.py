#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Where the IRAS/AKARI pair of Phan et al. (2025, PASA 42, e064, doi:10.1017/pasa.2025.10024) would be at a later date,
if both detections were one body at 500-700 au, and how bright it would be. A plausibility estimate, not an orbit.

  build/venv/bin/python -I tools/phan_candidate.py [--date 2026-12-31T00:00:00] [--n 20000]

Input (Phan et al. 2025, Table 2 and sec. 4): IRAS F02211-4844 at RA 35.74075, Dec -48.5125 (co-added scans from
26 June to 1 September 1983); AKARI-MUSL J0220440-491247 at RA 35.18379, Dec -49.2135 (three scans on 26 June 2006);
heliocentric distance 500-700 au; 7-17 Earth masses.

Model: for an assumed heliocentric distance d (the same at both epochs), each observed direction gives a heliocentric
position (Earth's position from DE440s); the body moves on a straight line between them (over 43 years an orbit of
more than 10,000 years bends by less than 1.5 degrees); its geocentric direction at the date follows from the Earth's
position then (full parallax). Monte Carlo over d (uniform 500-700 au), the effective IRAS epoch (uniform in the
co-added scans' interval), and the positions (Gaussian, IRAS 20", AKARI 8" per axis, assumed). Reported: the centre,
the 68 % and 95 % regions (along and across the major axis), the implied transverse speed against the local circular
and escape speeds, and the inclination of the implied motion against the ecliptic.

Brightness (reflected sunlight, opposition): V = -26.74 - 2.5 log10(p R^2 / (r^2 Delta^2)) with R in au;
R from the mass and a density of 1.27-1.64 g/cm^3 (Uranus, Neptune; Phan et al. use 1.46), geometric albedo
p = 0.2-0.75 (an ice giant: Uranus and Neptune about 0.5; cold, cloud-free atmospheres can be darker or, with
methane clouds, brighter), r = Delta = d.
"""

import argparse
import math

import numpy as np

IRAS = (35.74075, -48.5125)
AKARI = (35.18379, -49.2135)
IRAS_T = ("1983-06-26T00:00:00", "1983-09-01T00:00:00")
AKARI_T = "2006-06-26T12:00:00"
M_EARTH_KG, R_EARTH_KM, AU_KM = 5.9722e24, 6371.0, 1.495978707e8
V_SUN = -26.74


def unit(ra, dec):
    a, d = np.radians(ra), np.radians(dec)
    return np.stack([np.cos(d) * np.cos(a), np.cos(d) * np.sin(a), np.sin(d)], axis=-1)


def radec(v):
    v = v / np.linalg.norm(v, axis=-1, keepdims=True)
    return np.degrees(np.arctan2(v[..., 1], v[..., 0])) % 360, np.degrees(np.arcsin(v[..., 2]))


def earth_helio(times):
    """Heliocentric position of the Earth (au, ICRS) at astropy Times."""
    from astropy import units as u
    from astropy.coordinates import get_body_barycentric, solar_system_ephemeris
    solar_system_ephemeris.set("de440s")
    e = get_body_barycentric("earth", times).xyz.to_value(u.au)
    s = get_body_barycentric("sun", times).xyz.to_value(u.au)
    return (e - s).T


def helio(E, u, d):
    """Heliocentric position at distance d along the geocentric direction u from the Earth E."""
    eu = (E * u).sum(-1)
    delta = -eu + np.sqrt(eu ** 2 - (E * E).sum(-1) + d ** 2)
    return E + delta[..., None] * u


def jitter(ra, dec, sig_arcsec, rng, n):
    s = sig_arcsec / 3600
    return ra + rng.normal(0, s, n) / math.cos(math.radians(dec)), dec + rng.normal(0, s, n)


def main():
    from astropy.time import Time
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default="2026-12-31T00:00:00")
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=2025)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    n = a.n
    d = rng.uniform(500, 700, n)
    t1 = Time(IRAS_T[0]) + (Time(IRAS_T[1]) - Time(IRAS_T[0])) * rng.uniform(0, 1, n)
    t2 = Time([AKARI_T] * n)
    t3 = Time(a.date)
    E1, E2 = earth_helio(t1), earth_helio(t2)
    E3 = earth_helio(Time([a.date]))[0]
    r1, d1 = jitter(*IRAS, 20.0, rng, n)
    r2, d2 = jitter(*AKARI, 8.0, rng, n)
    P1, P2 = helio(E1, unit(r1, d1), d), helio(E2, unit(r2, d2), d)
    dt12 = (t2 - t1).to_value("jd") / 365.25
    V = (P2 - P1) / dt12[:, None]                      # au / yr
    P3 = P2 + V * ((t3 - t2).to_value("jd") / 365.25)[:, None]
    ra3, de3 = radec(P3 - E3)
    # region on the sky: tangent plane at the mean direction
    c = np.array(radec(np.mean(unit(ra3, de3), axis=0)))
    x = (ra3 - c[0] + 180) % 360 - 180
    x *= math.cos(math.radians(c[1])) * 60
    y = (de3 - c[1]) * 60
    cov = np.cov(np.stack([x, y]))
    w, vecs = np.linalg.eigh(cov)
    along = np.stack([x, y], 1) @ vecs[:, 1]
    across = np.stack([x, y], 1) @ vecs[:, 0]
    pa = math.degrees(math.atan2(vecs[0, 1], vecs[1, 1])) % 180  # east of north
    q = lambda v, p: np.percentile(v, p)
    print(f"Phan et al. 2025 pair, extrapolated to {a.date} UTC ({n} Monte Carlo draws)")
    print(f"  centre RA {c[0]:.3f} deg ({c[0] / 15:.4f} h), Dec {c[1]:+.3f} deg (J2000/ICRS)")
    print(f"  68 % region: {q(along, 84) - q(along, 16):.1f}' x {q(across, 84) - q(across, 16):.1f}'; "
          f"95 %: {q(along, 97.5) - q(along, 2.5):.1f}' x {q(across, 97.5) - q(across, 2.5):.1f}' (major axis PA {pa:.0f} deg)")
    for lo, hi in ((500, 520), (590, 610), (680, 700)):
        sel = (d >= lo) & (d <= hi)
        rr, dd = radec(np.mean(unit(ra3[sel], de3[sel]), axis=0))
        print(f"  d {lo}-{hi} au: RA {rr:.3f}, Dec {dd:+.3f}")
    vt = np.linalg.norm(V, axis=1)
    vc = 2 * math.pi / np.sqrt(d)
    print(f"  implied heliocentric speed {np.median(vt):.3f} au/yr (68 %: {q(vt, 16):.3f}-{q(vt, 84):.3f}); circular speed at d "
          f"{np.median(vc):.3f}, escape {np.median(vc) * math.sqrt(2):.3f}; ratio to escape: median {np.median(vt / (vc * math.sqrt(2))):.2f}, "
          f"bound (below escape) in {100 * np.mean(vt < vc * math.sqrt(2)):.0f} % of the draws")
    # inclination of the implied orbit plane (P2 x V) against the ecliptic (normal: ICRS rotated by the obliquity)
    eps = math.radians(23.4392911)
    n_ecl = np.array([0.0, -math.sin(eps), math.cos(eps)])
    h = np.cross(P2, V)
    inc = np.degrees(np.arccos((h @ n_ecl) / np.linalg.norm(h, axis=1)))
    print(f"  inclination of the implied orbit plane to the ecliptic: median {np.median(inc):.0f} deg (68 %: {q(inc, 16):.0f}-{q(inc, 84):.0f}); "
          f"above 90 deg = retrograde")
    sep = np.degrees(np.arccos(np.clip((unit(*IRAS) * unit(*AKARI)).sum(), -1, 1))) * 60
    print(f"  separation of the two detections {sep:.2f}' (Phan et al.: 47.4586')")
    print("brightness V at opposition (r = Delta = d):")
    print("   mass [M_E]  density [g/cm3]  R [R_E]   p     d 500 au   d 600 au   d 700 au")
    for m in (7, 17):
        for rho in (1.27, 1.64):
            R_km = (3 * m * M_EARTH_KG / (4 * math.pi * rho * 1000)) ** (1 / 3) / 1000
            for p in (0.2, 0.5, 0.75):
                vs = [V_SUN - 2.5 * math.log10(p * (R_km / AU_KM) ** 2 / dd ** 4) for dd in (500, 600, 700)]
                print(f"   {m:9d}  {rho:15.2f}  {R_km / R_EARTH_KM:7.2f}  {p:4.2f}   " + "   ".join(f"{v:8.1f}" for v in vs))


if __name__ == "__main__":
    main()
