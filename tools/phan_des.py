#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Would the Dark Energy Survey have seen the IRAS/AKARI pair of Phan et al. (2025), if it were one body at 500-700 au?

  build/venv/bin/python -I tools/phan_des.py --exposures raw.json --footprint des-round19-poly.txt \\
      --ccds ccd_corners_xy_fill.dat [--n 4000] [--V 19.3 21 22 23] [--json out.json]

Inputs (downloaded, see docs/phan-des.md):
  --exposures  NOIRLab Astro Data Archive, adv_search/find, DECam raw object exposures (JSON list, first entry
               metadata) with EXPNUM, proposal, caldat, dateobs_center, exposure, ifilter, ra_center, dec_center.
  --footprint  DES round19 footprint polygon (kadrlica/skymap, skymap/data/des-round19-poly.txt): "ra dec" lines.
  --ccds       DECam CCD corners in degrees about the pointing (skymap/data/ccd_corners_xy_fill.dat; CCDs 2 and 61
               not included, i.e. treated as dead throughout).

Position: the Monte Carlo draws of tools/phan_candidate.py (same seed), at the centre time of each exposure, with
full parallax. Per exposure: the fraction of the draws that fall on a CCD.
  --orbits NPZ  instead: the kept bound orbits of tools/iras_akari.py (r, v at t_jd; addendum D of
                docs/iras-akari-criteria.md), --n of them drawn with --seed, places by two-body propagation with the
                Earth from DE440s and light time (iras_akari.observe).

Detection model of Belyakov, Bernardinelli & Brown (2022, AJ 163, 216, sec. 3): per exposure the probability
p(m) = c / (1 + exp(k (m - m50))) times the transient efficiency 0.955, with c = 0.943, k = 6.37 (Bernardinelli et al.
2022, ApJS 258, 41, survey-wide in r) and the median per-exposure m50 of Bernardinelli et al. 2022 (g 24.2, r 24.0,
i 23.5, z 22.7; Y is not searched). Recovered if NUNIQUE >= 7 (unique nights), ARCCUT >= 180 days (the arc after
removing any single night) and a triplet of nights whose pairs are within 90 days. Only DES wide exposures (proposal
2012B-0001) count. Magnitudes from V with the colours of Belyakov et al. Table 1 (Neptune-like: g-r -0.3, g-i -1.35,
g-z -2.15; BB21 fiducial: g-r 0.53, g-i 0.55, g-z assumed 0.6) and V = g - 0.5784 (g-r) - 0.0038 (Lupton 2005).
"""

import argparse
import ast
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phan_candidate import directions, draws, unit  # noqa: E402

M50 = {"g": 24.2, "r": 24.0, "i": 23.5, "z": 22.7}
C, K, TRANSIENT = 0.943, 6.37, 0.955
COLOURS = {"Neptune-like": {"g-r": -0.3, "g-i": -1.35, "g-z": -2.15}, "BB21 fiducial": {"g-r": 0.53, "g-i": 0.55, "g-z": 0.6}}
DES = "2012B-0001"


def band_mag(V, col, band):
    g = V + 0.5784 * col["g-r"] + 0.0038
    return g if band == "g" else g - col[f"g-{band}"]


def in_poly(x, y, poly):
    """Ray casting; x, y arrays, poly (k, 2)."""
    inside = np.zeros(x.shape, bool)
    px, py = poly[:, 0], poly[:, 1]
    for j in range(len(poly)):
        x1, y1, x2, y2 = px[j - 1], py[j - 1], px[j], py[j]
        cross = (y1 > y) != (y2 > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
        inside ^= cross & (x < xi)
    return inside


def read_footprint(path):
    polys, cur = [], []
    for line in Path(path).read_text().splitlines():
        f = line.split()
        if line.startswith("#"):
            continue
        if len(f) == 2:
            cur.append((float(f[0]), float(f[1])))
        elif cur:
            polys.append(np.array(cur))
            cur = []
    if cur:
        polys.append(np.array(cur))
    return polys


def in_footprint(ra, dec, polys):
    r = (np.atleast_1d(ra) + 180) % 360 - 180
    return np.any([in_poly(r, np.atleast_1d(dec), p) for p in polys], axis=0)


def frame_offsets(ra, dec, ra0, dec0):
    """Longitude/latitude offsets (deg) of directions in the frame whose origin is the pointing (ra0, dec0)."""
    u = unit(ra, dec)
    a, b = math.radians(ra0), math.radians(dec0)
    x1 = u[:, 0] * math.cos(a) + u[:, 1] * math.sin(a)
    y1 = -u[:, 0] * math.sin(a) + u[:, 1] * math.cos(a)
    x2 = x1 * math.cos(b) + u[:, 2] * math.sin(b)
    z2 = -x1 * math.sin(b) + u[:, 2] * math.cos(b)
    return np.degrees(np.arctan2(y1, x2)), np.degrees(np.arcsin(np.clip(z2, -1, 1)))


def recovered(nights):
    """Criteria of Belyakov et al. 2022 on a sorted array of unique detection nights (days)."""
    if len(nights) < 7:
        return False
    arccut = min(np.ptp(np.delete(nights, j)) for j in range(len(nights)))
    if arccut < 180:
        return False
    return any(nights[j + 2] - nights[j] <= 90 for j in range(len(nights) - 2))


def main():
    from astropy.time import Time
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exposures", required=True)
    ap.add_argument("--footprint", required=True)
    ap.add_argument("--ccds", required=True)
    ap.add_argument("--n", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=2025)
    ap.add_argument("--trials", type=int, default=2000)
    ap.add_argument("--V", type=float, nargs="+", default=[19.3, 21.0, 22.0, 23.0])
    ap.add_argument("--json")
    ap.add_argument("--orbits", default=None)
    a = ap.parse_args()
    exps = [e for e in json.loads(Path(a.exposures).read_text()) if "EXPNUM" in e]
    exps = sorted({e["EXPNUM"]: e for e in exps}.values(), key=lambda e: e["dateobs_center"])
    ccds = {k: np.array(v) for k, v in ast.literal_eval(Path(a.ccds).read_text().split("\n", 2)[2]).items()}
    polys = read_footprint(a.footprint)
    if a.orbits:
        import iras_akari as ia
        orb = np.load(a.orbits)
        pick = np.random.default_rng(a.seed).choice(len(orb["r"]), size=min(a.n, len(orb["r"])), replace=False)
        R0, V0, T0 = orb["r"][pick], orb["v"][pick], orb["t_jd"][pick]
        a.n = len(pick)

        def directions_at(t):
            u, _, _ = ia.observe(R0, V0, T0, t.tdb.jd)
            return ia.radec(u)
    else:
        _, P2, V, t2 = draws(a.n, a.seed)

        def directions_at(t):
            return directions(P2, V, t2, t)

    print(f"{len(exps)} DECam exposures with centres in the query box; draws {a.n}")
    for season in range(2013, 2019):
        t = Time(f"{season}-11-15T00:00:00")
        ra, dec = directions_at(t)
        print(f"  {season}-11-15: draws inside the DES footprint {100 * in_footprint(ra, dec, polys).mean():.0f} %")

    rows, masks = [], {}
    for e in exps:
        t = Time(e["dateobs_center"].rstrip("Z"), scale="utc")
        ra, dec = directions_at(t)
        x, y = frame_offsets(ra, dec, e["ra_center"], e["dec_center"])
        on = np.zeros(len(x), bool)
        ccd_hit = defaultdict(int)
        for k, poly in ccds.items():
            h = in_poly(x, y, poly)
            ccd_hit[k] += int(h.sum())
            on |= h
        if not on.any() and np.hypot(x, y).min() > 1.3:
            continue
        masks[e["EXPNUM"]] = on
        rows.append({"expnum": e["EXPNUM"], "proposal": e["proposal"], "night": e["caldat"][:10], "time": e["dateobs_center"],
                     "band": e["ifilter"][0], "exptime": e["exposure"], "frac_on_ccd": round(float(on.mean()), 3),
                     "ccd": max(ccd_hit, key=ccd_hit.get) if on.any() else None,
                     "ra": round(float(np.mean(ra)), 4), "dec": round(float(np.mean(dec)), 4),
                     "offset_deg": round(float(np.hypot(x, y).mean()), 3)})
    print("\nexposures within 1.3 deg of the track (frac = fraction of the draws on a CCD):")
    print("   expnum  proposal    night       band exptime  frac  ccd  offset")
    for r in rows:
        print(f"  {r['expnum']:7d}  {r['proposal']}  {r['night']}  {r['band']:>3}  {r['exptime']:6.0f}  {r['frac_on_ccd']:5.2f}  "
              f"{str(r['ccd']):>3}  {r['offset_deg']:5.2f}")
    des = [r for r in rows if r["proposal"] == DES and r["band"] in M50]
    on_des = [r for r in des if r["frac_on_ccd"] >= 0.5]
    nights = sorted({r["night"] for r in on_des})
    print(f"\nDES wide (griz) exposures with the track on a CCD in >= 50 % of the draws: {len(on_des)} "
          f"on {len(nights)} nights: " + ", ".join(nights))
    by_band = defaultdict(int)
    for r in on_des:
        by_band[r["band"]] += 1
    print("  per band: " + ", ".join(f"{b} {by_band[b]}" for b in "griz"))

    rng = np.random.default_rng(a.seed)
    day = {r["expnum"]: int(round((Time(r["night"]) - Time("2013-01-01")).to_value("jd"))) for r in des}
    out = {"exposures": rows, "recovery": []}
    print(f"\nrecovery probability (criteria of Belyakov et al. 2022; {a.trials} trials over the draws and the detections):")
    print("  colours        V     g     r     i     z    P(recovered)  median NUNIQUE")
    for name, col in COLOURS.items():
        for Vmag in a.V:
            mags = {b: band_mag(Vmag, col, b) for b in M50}
            p = {b: TRANSIENT * C / (1 + math.exp(K * (mags[b] - M50[b]))) for b in M50}
            n_rec, nun = 0, []
            for _ in range(a.trials):
                j = rng.integers(a.n)
                det = set()
                for r in des:
                    if masks[r["expnum"]][j] and rng.random() < p[r["band"]]:
                        det.add(day[r["expnum"]])
                nn = np.array(sorted(det))
                nun.append(len(nn))
                n_rec += recovered(nn)
            out["recovery"].append({"colours": name, "V": Vmag, "mags": mags, "p_exposure": p, "p_recovered": n_rec / a.trials,
                                    "median_nunique": float(np.median(nun))})
            print(f"  {name:13s} {Vmag:5.1f} " + " ".join(f"{mags[b]:5.1f}" for b in "griz")
                  + f"   {n_rec / a.trials:8.3f}       {np.median(nun):4.0f}")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
