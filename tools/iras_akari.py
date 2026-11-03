#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Track R: the IRAS/AKARI Planet Nine candidates of Phan et al. 2025 and Chen et al. 2025, as fixed in
docs/iras-akari-criteria.md (sections 1-4 and addenda A and B, stamped before this code was run).

  python tools/iras_akari.py --out runs/iras-akari --des DES_ROUND19_POLY [--open OPEN_2026_JS] [--n 100000]

Per case: statistical ranging (two epochs: Lambert through both detections with heliocentric distances uniform in
500-1,000 au, bound orbits kept; one epoch: bound orbits through the single position with velocity uniform in
direction and in magnitude below the escape speed), the places in 2026-11 and at the survey epochs (two-body,
geocentric, light time), the brightness V from the far-infrared fluxes (blackbody T 30-50 K, albedo 0.2-0.75), the
survey coverage (ZTF, Pan-STARRS1, DES; limits and footprints of addendum B), the Planet Nine parameter space,
the atlas layer "still open" and the own observatory. Writes result.json, regions (HEALPix nside 256, NESTED) and
maps (PNG) to --out. Seed 2026.
"""

import argparse
import json
import math
import struct
import zlib
from pathlib import Path

import numpy as np

AU_KM = 149597870.7
C_AU_YR = 299792.458 * 86400 * 365.25 / AU_KM
# the Sun with the planets inside (Mercury to Neptune), solar masses (DE440 GM ratios, as tools/make_ic.py)
M_INSIDE = 1 + 1 / 6023657.33 + 1 / 408523.7186 + 1 / 328900.5596 + 1 / 3098703.59 + 1 / 1047.348644 + 1 / 3497.9018 + 1 / 22902.951 + 1 / 19412.26
MU = 4 * math.pi ** 2 * M_INSIDE   # au^3 / yr^2
YEAR_D = 365.25
EPS = math.radians(84381.448 / 3600)
# invariable plane of Jupiter-Neptune on the ecliptic J2000 (tools/make_ic.py of medas-p9-search-bb2021, make-ic-v1)
INV_I, INV_N = math.radians(1.5793066836782754), math.radians(107.63369765691192)
T_GRID = [30.0, 35.0, 40.0, 45.0, 50.0]          # K (addendum A4)
P_GRID = [0.2, 0.4, 0.5, 0.75]                    # geometric albedo (2.4)
SURVEYS = {  # addendum B
    "ZTF": {"epoch": "2019-05-20", "V_limit": 20.5},
    "PS1": {"epoch": "2012-07-01", "V_limit": 21.0},
    "DES": {"epoch": "2016-07-01", "V_limit": 23.8 + 0.2},
}
POSTERIOR = {"a": (300.0, 520.0), "q": (240.0, 385.0), "i": (6.0, 26.0)}   # 2.6 and B5: a 380 +140/-80, q 300 +85/-60, i 16 +- 10
TARGET = "2026-11-15T00:00:00"
FOV_DEG2 = (2688 * 0.2184 / 3600) * (1520 * 0.2184 / 3600)   # Mewlon 300 + 0.8x reducer, IMX664 (the project lead, 2026-11-03)

# --- the cases (docs/iras-akari-criteria.md, extraction of 2026-11-03; ICRS by A1) ---------------------------------
PHAN = {"iras": {"ra": 35.74075, "dec": -48.5125, "t0": "1983-06-26T00:00:00", "t1": "1983-09-01T00:00:00"},
        "akari": {"ra": 35.18379, "dec": -49.2135, "t": "2006-12-26T12:00:00", "t_variant": "2006-06-26T12:00:00"},
        "flux_jy": {"IRAS 100": (100.0, 0.52), "AKARI 90": (90.0, 0.27)}}   # the bands not flagged as unreliable (A4)
CHEN = {"J0250422-150114": {"ra": 42.676, "dec": -15.021, "t": "2007-07-28", "flux90": (0.61, 1.62), "ell": (3.5, 2.3, 340.3)},
        "J0301112-164240": {"ra": 45.297, "dec": -16.711, "t": "2006-07-30", "flux90": (1.27, 0.51), "ell": (3.5, 2.3, 340.7)}}


# --- time and the Earth ------------------------------------------------------------------------------------------------

def jd(iso):
    from astropy.time import Time
    return Time(iso, scale="utc").tdb.jd


def earth(jds):
    """Heliocentric ICRS position of the Earth (au) at TDB Julian dates (DE440s)."""
    from astropy import units as u
    from astropy.coordinates import get_body_barycentric, solar_system_ephemeris
    from astropy.time import Time
    solar_system_ephemeris.set("de440s")
    t = Time(np.atleast_1d(jds), format="jd", scale="tdb")
    return (get_body_barycentric("earth", t).xyz - get_body_barycentric("sun", t).xyz).to_value(u.au).T


def unit(ra, dec):
    ra, dec = np.radians(ra), np.radians(dec)
    return np.stack([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)], -1)


def radec(v):
    v = v / np.linalg.norm(v, axis=-1, keepdims=True)
    return np.degrees(np.arctan2(v[..., 1], v[..., 0])) % 360, np.degrees(np.arcsin(np.clip(v[..., 2], -1, 1)))


def scatter(rng, ra, dec, n, sig_major, sig_minor=None, pa=0.0):
    """n unit vectors around (ra, dec) with a Gaussian error ellipse (arcsec, 1 sigma; pa east of north)."""
    sig_minor = sig_major if sig_minor is None else sig_minor
    a, b = rng.normal(0, sig_major, n), rng.normal(0, sig_minor, n)
    p = math.radians(pa)
    d_north, d_east = a * math.cos(p) - b * math.sin(p), a * math.sin(p) + b * math.cos(p)
    u0 = unit(ra, dec)
    e_ra = np.array([-math.sin(math.radians(ra)), math.cos(math.radians(ra)), 0.0])
    e_de = np.cross(u0, e_ra)
    v = u0 + np.outer(np.radians(d_east / 3600), e_ra) + np.outer(np.radians(d_north / 3600), e_de)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def place(E, u, r):
    """Heliocentric position at heliocentric distance r along the line of sight u from the Earth E; and rho."""
    b = (E * u).sum(-1)
    rho = -b + np.sqrt(b * b - (E * E).sum(-1) + r * r)
    return E + rho[:, None] * u, rho


# --- two-body ----------------------------------------------------------------------------------------------------------

def stumpff(z):
    C, S = np.empty_like(z), np.empty_like(z)
    p, m, s = z > 1e-8, z < -1e-8, np.abs(z) <= 1e-8
    sp, sm = np.sqrt(z[p]), np.sqrt(-z[m])
    C[p], S[p] = (1 - np.cos(sp)) / z[p], (sp - np.sin(sp)) / sp ** 3
    C[m], S[m] = (np.cosh(sm) - 1) / -z[m], (np.sinh(sm) - sm) / sm ** 3
    C[s], S[s] = 0.5 - z[s] / 24, 1 / 6 - z[s] / 120
    return C, S


def lambert_bound(r1v, r2v, dt, long_way=False):
    """Elliptic single-revolution Lambert solutions (universal variables, Curtis 2014 §5.3): velocity at r2 and a
    mask of trials with a bound solution. dt in years, positions in au."""
    r1, r2 = np.linalg.norm(r1v, axis=1), np.linalg.norm(r2v, axis=1)
    c = np.clip((r1v * r2v).sum(1) / (r1 * r2), -1, 1)
    dth = np.arccos(c)
    if long_way:
        dth = 2 * math.pi - dth
    A = np.sin(dth) * np.sqrt(r1 * r2 / (1 - np.cos(dth)))

    def F(z):
        C, S = stumpff(z)
        y = r1 + r2 + A * (z * S - 1) / np.sqrt(C)
        yp = np.maximum(y, 0)
        return (yp / C) ** 1.5 * S + A * np.sqrt(yp) - math.sqrt(MU) * dt, y

    lo, hi = np.full_like(r1, 1e-9), np.full_like(r1, 4 * math.pi ** 2 - 1e-6)
    f_lo, _ = F(lo)
    ok = f_lo < 0                       # the parabolic transfer is faster than dt: an elliptic solution exists
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        fm, _ = F(mid)
        lo, hi = np.where(fm < 0, mid, lo), np.where(fm < 0, hi, mid)
    z = 0.5 * (lo + hi)
    _, y = F(z)
    ok &= y > 0
    yv = np.maximum(y, 1e-300)
    g = A * np.sqrt(yv / MU)
    gdot = 1 - yv / r2
    v2 = (gdot[:, None] * r2v - r1v) / g[:, None]
    return v2, ok


def elements(r, v):
    rn = np.linalg.norm(r, axis=1)
    h = np.cross(r, v)
    a = 1 / (2 / rn - (v * v).sum(1) / MU)
    ev = np.cross(v, h) / MU - r / rn[:, None]
    return a, np.linalg.norm(ev, axis=1), h


def propagate(r0, v0, dt):
    """Elliptic two-body propagation by dt (years) with f and g in the eccentric anomaly."""
    r0n = np.linalg.norm(r0, axis=1)
    a, e, _ = elements(r0, v0)
    n = np.sqrt(MU / a ** 3)
    ecosE, esinE = 1 - r0n / a, (r0 * v0).sum(1) / np.sqrt(MU * a)
    E0 = np.arctan2(esinE, ecosE)
    M = E0 - esinE + n * dt
    E = M.copy()
    for _ in range(50):
        E = E - (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
    dE = E - E0
    f = 1 - a / r0n * (1 - np.cos(dE))
    g = dt - (dE - np.sin(dE)) / n
    return f[:, None] * r0 + g[:, None] * v0


def observe(r0, v0, t0_jd, t_jd):
    """Geocentric unit vector and distances (r, Delta) of the orbits (state at t0) seen from the Earth at t."""
    E = earth([t_jd])[0]
    tl = np.zeros(len(r0))
    for _ in range(3):   # light time
        p = propagate(r0, v0, (t_jd - t0_jd) / YEAR_D - tl)
        d = p - E
        tl = np.linalg.norm(d, axis=1) / C_AU_YR
    return d / np.linalg.norm(d, axis=1, keepdims=True), np.linalg.norm(p, axis=1), np.linalg.norm(d, axis=1)


# --- brightness --------------------------------------------------------------------------------------------------------

def planck_nu(lam_um, T):
    h, c, k = 6.62607015e-34, 2.99792458e8, 1.380649e-23
    nu = c / (lam_um * 1e-6)
    return 2 * h * nu ** 3 / c ** 2 / np.expm1(h * nu / (k * T))     # W m^-2 Hz^-1 sr^-1


def radius_km(flux_jy, lam_um, T, delta_au):
    """Radius of a blackbody disk of temperature T that gives flux_jy at distance delta (F = pi B (R / Delta)^2)."""
    return delta_au * AU_KM * np.sqrt(flux_jy * 1e-26 / (math.pi * planck_nu(lam_um, T)))


def v_mag(R_km, p, r, delta):
    return 5 * np.log10(1329.0 / (2 * R_km * math.sqrt(p))) + 5 * np.log10(r * delta)


# --- sky ---------------------------------------------------------------------------------------------------------------

def ang2pix_nest(nside, ra, dec):
    """HEALPix NESTED pixel of (ra, dec) in degrees (Gorski et al. 2005; the algorithm of healpix_base)."""
    z = np.sin(np.radians(dec))
    za = np.abs(z)
    tt = (np.radians(ra) % (2 * math.pi)) / (math.pi / 2)
    face, ix, iy = np.zeros(len(z), np.int64), np.zeros(len(z), np.int64), np.zeros(len(z), np.int64)
    eq = za <= 2 / 3
    t1, t2 = nside * (0.5 + tt[eq]), nside * z[eq] * 0.75
    jp, jm = (t1 - t2).astype(np.int64), (t1 + t2).astype(np.int64)
    ifp, ifm = jp // nside, jm // nside
    face[eq] = np.where(ifp == ifm, ifp | 4, np.where(ifp < ifm, ifp, ifm + 8))
    ix[eq], iy[eq] = jm & (nside - 1), nside - (jp & (nside - 1)) - 1
    po = ~eq
    ntt = np.minimum(tt[po].astype(np.int64), 3)
    tp = tt[po] - ntt
    tmp = nside * np.sqrt(3 * (1 - za[po]))
    jp, jm = np.minimum((tp * tmp).astype(np.int64), nside - 1), np.minimum(((1 - tp) * tmp).astype(np.int64), nside - 1)
    north = z[po] > 0
    face[po] = np.where(north, ntt, ntt + 8)
    ix[po], iy[po] = np.where(north, nside - jm - 1, jp), np.where(north, nside - jp - 1, jm)
    ipf = np.zeros_like(ix)
    for b in range(int(math.log2(nside))):
        ipf |= ((ix >> b) & 1) << (2 * b) | ((iy >> b) & 1) << (2 * b + 1)
    return face * nside * nside + ipf


def region(ra, dec, w, nside=256):
    """Pixels (NESTED) of the 68 % and 95 % highest-density regions of weighted points, and their areas."""
    pix = ang2pix_nest(nside, ra, dec)
    u, inv = np.unique(pix, return_inverse=True)
    wsum = np.bincount(inv, weights=w)
    order = np.argsort(-wsum)
    cum = np.cumsum(wsum[order]) / wsum.sum()
    area = 4 * math.pi * (180 / math.pi) ** 2 / (12 * nside * nside)
    out = {}
    for lv in (68, 95):
        k = np.searchsorted(cum, lv / 100) + 1
        sel = u[order[:k]]
        out[str(lv)] = {"pixels": sel, "area_deg2": round(len(sel) * area, 4)}
    return out


def in_polygon(ra, dec, poly):
    """Even-odd rule in (ra, dec) with ra unwrapped around the polygon's own range."""
    pr, pd = poly[:, 0], poly[:, 1]
    x = ((ra - pr.min() + 180) % 360) + pr.min() - 180
    inside = np.zeros(len(ra), bool)
    for i in range(len(pr)):
        x1, y1, x2, y2 = pr[i - 1], pd[i - 1], pr[i], pd[i]
        cond = (y1 > dec) != (y2 > dec)
        with np.errstate(divide="ignore", invalid="ignore"):
            xin = x1 + (dec - y1) * (x2 - x1) / (y2 - y1)
        inside ^= cond & (x < xin)
    return inside


def des_polygons(path):
    """The round 19 footprint file: blocks of 'ra dec' rows separated by comment or blank lines."""
    polys, cur = [], []
    for line in Path(path).read_text().splitlines():
        f = line.split()
        if not f or f[0].startswith("#"):
            if len(cur) > 2:
                polys.append(np.array(cur))
            cur = []
            continue
        cur.append([float(f[0]), float(f[1])])
    if len(cur) > 2:
        polys.append(np.array(cur))
    return polys


def galactic_b(ra, dec):
    from astropy import units as u
    from astropy.coordinates import SkyCoord
    return SkyCoord(ra * u.deg, dec * u.deg, frame="icrs").galactic.b.deg


def footprint(name, ra, dec, des):
    if name == "DES":
        return np.any([in_polygon(ra, dec, p) for p in des], axis=0)
    ok = dec > -30
    if name == "ZTF":
        ok &= np.abs(galactic_b(ra, dec)) > 5
    return ok


def inclination_invariable(h):
    """Inclination (deg) of orbit normals h (ICRS) against the invariable plane of Jupiter-Neptune."""
    pole_ecl = np.array([math.sin(INV_I) * math.sin(INV_N), -math.sin(INV_I) * math.cos(INV_N), math.cos(INV_I)])
    ce, se = math.cos(EPS), math.sin(EPS)
    pole = np.array([pole_ecl[0], ce * pole_ecl[1] - se * pole_ecl[2], se * pole_ecl[1] + ce * pole_ecl[2]])
    return np.degrees(np.arccos(np.clip(h @ pole / np.linalg.norm(h, axis=1), -1, 1)))


# --- PNG map -----------------------------------------------------------------------------------------------------------

def png_map(path, ra, dec, w, reg, centre, half=None):
    """A small density map (gnomonic, 400 x 400 px) around centre with the 68/95 % regions' points marked."""
    from math import cos, sin, radians
    ra0, de0 = radians(centre[0]), radians(centre[1])
    r_, d_ = np.radians(ra), np.radians(dec)
    cosc = sin(de0) * np.sin(d_) + cos(de0) * np.cos(d_) * np.cos(r_ - ra0)
    x = np.cos(d_) * np.sin(r_ - ra0) / cosc
    y = (cos(de0) * np.sin(d_) - sin(de0) * np.cos(d_) * np.cos(r_ - ra0)) / cosc
    half = half or max(np.percentile(np.abs(x), 99.5), np.percentile(np.abs(y), 99.5)) * 1.1
    N = 400
    ix = np.clip(((-x / half + 1) / 2 * (N - 1)).astype(int), 0, N - 1)       # east to the left
    iy = np.clip(((-y / half + 1) / 2 * (N - 1)).astype(int), 0, N - 1)       # north up
    img = np.zeros((N, N))
    np.add.at(img, (iy, ix), w)
    g = (255 * (1 - np.sqrt(img / max(img.max(), 1e-30)))).astype(np.uint8)
    rgb = np.stack([g, g, g], -1)
    raw = b"".join(b"\x00" + rgb[r].tobytes() for r in range(N))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", N, N, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    return math.degrees(half)


# --- the cases ---------------------------------------------------------------------------------------------------------

def ranging_two(rng, n, ra1, de1, t1_jd, sig1, ra2, de2, t2_jd, sig2, ell1=None, ell2=None):
    """Two-epoch ranging (2.2): kept bound orbits as (state at the second epoch, its time, r1, r2)."""
    if ell1:
        u1 = scatter(rng, ra1, de1, n, *ell1)
    else:
        u1 = scatter(rng, ra1, de1, n, sig1)
    u2 = scatter(rng, ra2, de2, n, *ell2) if ell2 else scatter(rng, ra2, de2, n, sig2)
    E1, E2 = earth(t1_jd), earth(np.full(n, t2_jd))
    r1, r2 = rng.uniform(500, 1000, n), rng.uniform(500, 1000, n)
    p1, rho1 = place(E1, u1, r1)
    p2, rho2 = place(E2, u2, r2)
    dt = ((t2_jd - rho2 / C_AU_YR * YEAR_D) - (t1_jd - rho1 / C_AU_YR * YEAR_D)) / YEAR_D
    kept = []
    for lw in (False, True):
        v2, ok = lambert_bound(p1, p2, dt, lw)
        ok &= np.isfinite(v2).all(1)
        aa, ee, _ = elements(p2, np.where(np.isfinite(v2), v2, 0.0))
        ok &= (aa > 0) & (ee < 1)          # bound (2.2): checked on the state, the Lambert edge z -> 0 is not exact
        kept.append((p2[ok], v2[ok], (t2_jd - rho2[ok] / C_AU_YR * YEAR_D), r1[ok], r2[ok], rho1[ok], rho2[ok]))
    cat = [np.concatenate([k[i] for k in kept]) for i in range(7)]
    return {"n_trials": n, "n_kept": int(len(cat[0])), "share": len(cat[0]) / n, "r": cat[0], "v": cat[1], "t_jd": cat[2],
            "r1": cat[3], "r2": cat[4], "rho1": cat[5], "rho2": cat[6]}


def reach_one(rng, n, c):
    """One epoch (A3): bound orbits through the position, r uniform, velocity uniform in direction and magnitude."""
    u = scatter(rng, c["ra"], c["dec"], n, *c["ell"])
    t = jd(c["t"] + "T00:00:00") + rng.uniform(0, 1, n)
    E = earth(t)
    r = rng.uniform(500, 1000, n)
    p, rho = place(E, u, r)
    d = rng.normal(size=(n, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    v = d * (rng.uniform(0, 1, n) * np.sqrt(2 * MU / r))[:, None]
    return {"n_trials": n, "n_kept": n, "share": 1.0, "r": p, "v": v, "t_jd": t - rho / C_AU_YR * YEAR_D, "r1": r, "r2": r, "rho1": rho, "rho2": rho}


def evaluate(name, fam, flux_fit, des, open_pix32, outdir, single):
    res = {"name": name, "n_trials": fam["n_trials"], "n_kept": fam["n_kept"], "kept_share": fam["share"]}
    if fam["n_kept"] == 0:
        res["note"] = "no bound orbit kept"
        res["Q_O"] = "excluded (fewer than 0.1 % of the trials kept)"
        return res
    r, v = fam["r"], fam["v"]
    a, e, h = elements(r, v)
    q = a * (1 - e)
    inc = inclination_invariable(h)
    res["orbits"] = {k: {"p5": float(np.percentile(x, 5)), "median": float(np.median(x)), "p95": float(np.percentile(x, 95))}
                     for k, x in (("a_au", a), ("e", e), ("q_au", q), ("i_invariable_deg", inc), ("r_au", np.linalg.norm(r, axis=1)))}
    inside = (a >= POSTERIOR["a"][0]) & (a <= POSTERIOR["a"][1]) & (q >= POSTERIOR["q"][0]) & (q <= POSTERIOR["q"][1]) & \
             (inc >= POSTERIOR["i"][0]) & (inc <= POSTERIOR["i"][1])
    res["planet_nine_space_share"] = float(inside.mean())
    # 2026-11
    u26, r26, d26 = [], [], []
    for k0 in range(0, len(r), 20000):
        uu, rr, dd = observe(r[k0:k0 + 20000], v[k0:k0 + 20000], fam["t_jd"][k0:k0 + 20000], jd(TARGET))
        u26.append(uu); r26.append(rr); d26.append(dd)
    u26, r26, d26 = np.concatenate(u26), np.concatenate(r26), np.concatenate(d26)
    ra26, de26 = radec(u26)
    w = np.ones(len(ra26))
    reg = region(ra26, de26, w)
    cen = radec(u26.mean(0))
    res["search_2026_11"] = {"centre_ra_deg": float(cen[0]), "centre_dec_deg": float(cen[1]),
                             "area_68_deg2": reg["68"]["area_deg2"], "area_95_deg2": reg["95"]["area_deg2"],
                             "ra_range_95": [float(np.percentile(ra26, 2.5)), float(np.percentile(ra26, 97.5))],
                             "dec_range_95": [float(np.percentile(de26, 2.5)), float(np.percentile(de26, 97.5))]}
    np.savez_compressed(outdir / f"{name}-region.npz", pix68=reg["68"]["pixels"], pix95=reg["95"]["pixels"], nside=256)
    res["map_half_width_deg"] = png_map(outdir / f"{name}-2026-11.png", ra26, de26, w, reg, cen)
    # still open (2.7): share of the 95 % pixels whose nside-32 parent is in the open 90 % band
    parents = reg["95"]["pixels"] // 64
    res["still_open_share_of_95"] = float(np.isin(parents, list(open_pix32)).mean()) if open_pix32 is not None else None
    res["still_open_share_of_points"] = float(np.isin(ang2pix_nest(32, ra26, de26), list(open_pix32)).mean()) if open_pix32 is not None else None
    # brightness (2.4, A4)
    R = flux_fit(fam)                     # {T: radius_km array}
    res["radius_km"] = {str(T): {"median": float(np.median(x)), "p5": float(np.percentile(x, 5)), "p95": float(np.percentile(x, 95))} for T, x in R.items()}
    res["V_2026_11"] = {}
    res["mewlon_V21_share"] = {}
    for T, Rk in R.items():
        for p in P_GRID:
            V = v_mag(Rk, p, r26, d26)
            key = f"T{T:g}_p{p:g}"
            res["V_2026_11"][key] = {"median": float(np.median(V)), "p5": float(np.percentile(V, 5)), "p95": float(np.percentile(V, 95))}
            res["mewlon_V21_share"][key] = float((V <= 21.0).mean())
    res["mewlon_fields_for_95"] = round(reg["95"]["area_deg2"] / FOV_DEG2, 1)
    # surveys (2.5, B)
    res["surveys"] = {}
    detected_any = {}
    for s, cfg in SURVEYS.items():
        us, rs, ds = observe(r, v, fam["t_jd"], jd(cfg["epoch"] + "T00:00:00"))
        ras, des_ = radec(us)
        inf = footprint(s, ras, des_, des)
        res["surveys"][s] = {"in_footprint_share": float(inf.mean()), "V_limit": cfg["V_limit"], "detected_share": {}}
        for T, Rk in R.items():
            for p in P_GRID:
                key = f"T{T:g}_p{p:g}"
                det = inf & (v_mag(Rk, p, rs, ds) <= cfg["V_limit"] - 0.5)
                res["surveys"][s]["detected_share"][key] = float(det.mean())
                detected_any[key] = detected_any.get(key, np.zeros(len(r), bool)) | det
    res["detected_by_any_share"] = {k: float(x.mean()) for k, x in detected_any.items()}
    # verdicts (section 3)
    shares = list(res["detected_by_any_share"].values())
    if single:
        res["Q_O"] = "not decidable (one epoch, 2.2 and A3)"
    elif fam["share"] < 0.001:
        res["Q_O"] = "excluded (fewer than 0.1 % of the trials kept)"
    elif min(shares) >= 0.95:
        res["Q_O"] = "excluded (at least 95 % of the kept weight would have been detected for every T and albedo)"
    elif fam["share"] >= 0.05 and max(shares) <= 0.50:
        res["Q_O"] = "supported only if the flux condition of section 3 holds; see the report"
    else:
        res["Q_O"] = "not decidable"
    if not res["Q_O"].startswith("excluded"):
        s = res["planet_nine_space_share"]
        res["Q_P"] = "supported" if s >= 0.5 else ("excluded" if s < 0.05 else "not decidable")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--des", required=True)
    ap.add_argument("--open", default=None)
    ap.add_argument("--n", type=int, default=100000)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2026)
    des = des_polygons(a.des)
    open32 = None
    if a.open:
        txt = Path(a.open).read_text()
        d = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        cols = d["columns"]
        rows = sorted(d["pixels"], key=lambda x: -x[cols.index("n")])
        cum, sel = 0.0, []
        for row in rows:                      # band rule of scripts/planet9/build.py: the pixel's band from the share before it
            if cum < 90 - 1e-9:
                sel.append(int(row[0]))
            cum += row[cols.index("share_percent")]
        open32 = set(sel)
    results = {"criteria": "docs/iras-akari-criteria.md (sections 1-4, addenda A and B)", "target": TARGET, "seed": 2026, "n": a.n, "cases": []}
    P = PHAN

    def phan_flux(fam):
        # IRAS 100 um at the IRAS epoch (rho1), AKARI 90 um at the AKARI epoch (rho2): log-mean of the two radii
        out = {}
        for T in T_GRID:
            R1 = radius_km(P["flux_jy"]["IRAS 100"][1], 100.0, T, fam["rho1"])
            R2 = radius_km(P["flux_jy"]["AKARI 90"][1], 90.0, T, fam["rho2"])
            out[T] = np.sqrt(R1 * R2)
        return out

    def chen_flux(c):
        def f(fam):
            out = {}
            for T in T_GRID:
                lo, hi = (radius_km(fx, 90.0, T, fam["rho2"]) for fx in sorted(c["flux90"]))
                out[T] = np.sqrt(lo * hi)     # the two per-scan fluxes: their log-mean (the range is reported apart)
            return out
        return f

    t_iras = jd(P["iras"]["t0"]) + rng.uniform(0, jd(P["iras"]["t1"]) - jd(P["iras"]["t0"]), a.n)
    for label, sig, t_ak in (("phan-30arcsec", 30.0, P["akari"]["t"]), ("phan-90arcsec", 90.0, P["akari"]["t"]),
                             ("phan-30arcsec-akari-june", 30.0, P["akari"]["t_variant"])):
        fam = ranging_two(rng, a.n, P["iras"]["ra"], P["iras"]["dec"], t_iras, sig, P["akari"]["ra"], P["akari"]["dec"], jd(t_ak), sig)
        results["cases"].append(evaluate(label, fam, phan_flux, des, open32, out, single=False))
    for cname, c in CHEN.items():
        fam = reach_one(rng, a.n, c)
        results["cases"].append(evaluate(f"chen-{cname}", fam, chen_flux(c), des, open32, out, single=True))
    c1, c2 = CHEN["J0301112-164240"], CHEN["J0250422-150114"]      # the pair hypothesis (A3), in time order
    fam = ranging_two(rng, a.n, c1["ra"], c1["dec"], jd(c1["t"] + "T12:00:00") + rng.uniform(-0.5, 0.5, a.n), None,
                      c2["ra"], c2["dec"], jd(c2["t"] + "T12:00:00"), None, ell1=c1["ell"], ell2=c2["ell"])
    results["cases"].append(evaluate("chen-pair", fam, chen_flux(c2), des, open32, out, single=False))
    (out / "result.json").write_text(json.dumps(results, indent=1, default=float) + "\n")
    for cse in results["cases"]:
        print(cse["name"], cse["n_kept"], round(cse["kept_share"], 5), cse.get("Q_O"), cse.get("Q_P"))


if __name__ == "__main__":
    main()
