#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Clustering of the distant test particles relative to Planet Nine.

  python tools/analyze.py --p9sim build/gcc-O3/p9sim [--snapshot -1] RUN_DIR...

RUN_DIR: job directories (with output.sa) or chain directories (the last
segment with an output is used). For each snapshot asked for, the particles
of all directories are pooled. Heliocentric osculating elements (ecliptic
J2000, the frame of the start values) relative to the Sun; mu = G M_sun for
test particles.

Statistic as in Brown & Batygin (2016, 2021): the longitude of perihelion
varpi and of the ascending node Omega of the distant, detached objects
relative to those of Planet Nine (Delta varpi, Delta Omega); their clustering
as the mean resultant length R of the angles (0: uniform, 1: all equal), the
mean direction, and the Rayleigh test p-value (p ~ exp(-n R^2)). Brown &
Batygin find the observed objects anti-aligned in varpi (Delta varpi near
180 deg). Selections: "distant" a > 230 au and q > 42 au (the observational
selection of Brown & Batygin 2021 uses 150-1000 au and q > 42 au; here both
are given), "all" every surviving test particle.
"""

import argparse
import math
import subprocess
from pathlib import Path

import numpy as np

G = (0.01720209895 * 365.25) ** 2


def dump(p9sim, sa, snapshot):
    out = subprocess.run([p9sim, "dump", str(sa), str(snapshot)], capture_output=True, text=True, check=True).stdout
    t = None
    rows = []
    for line in out.splitlines():
        f = line.split()
        if not f or f[0].startswith("Warning"):
            continue
        if f[0] == "t":
            t = float(f[1])
            continue
        # "name m x y z vx vy vz" (before particle ids) or "name id m x y z vx vy vz"
        vals = list(map(float, f[1:]))
        rows.append((f[0], vals[-7], np.array(vals[-6:-3]), np.array(vals[-3:])))
    return t, rows


def elements(mu, r, v):
    rr = np.linalg.norm(r, axis=-1)
    vv2 = (v * v).sum(-1)
    h = np.cross(r, v)
    hn = np.linalg.norm(h, axis=-1)
    a = 1 / (2 / rr - vv2 / mu)
    evec = np.cross(v, h) / mu - r / rr[:, None]
    e = np.linalg.norm(evec, axis=-1)
    inc = np.degrees(np.arccos(np.clip(h[:, 2] / hn, -1, 1)))
    node = np.cross(np.array([0.0, 0.0, 1.0]), h)
    Omega = np.degrees(np.arctan2(node[:, 1], node[:, 0])) % 360
    # longitude of perihelion: Omega + omega, for prograde orbits the angle of the eccentricity vector projected
    varpi = np.degrees(np.arctan2(evec[:, 1], evec[:, 0])) % 360
    return a, e, inc, Omega, varpi


def circ(angles_deg):
    x = np.radians(angles_deg)
    n = len(x)
    if n == 0:
        return {"n": 0}
    C, S = np.cos(x).mean(), np.sin(x).mean()
    R = math.hypot(C, S)
    z = n * R * R
    p = math.exp(-z) * (1 + (2 * z - z * z) / (4 * n) - (24 * z - 132 * z**2 + 76 * z**3 - 9 * z**4) / (288 * n * n))
    return {"n": n, "R": round(R, 4), "mean_deg": round(math.degrees(math.atan2(S, C)) % 360, 1), "rayleigh_p": float(f"{max(min(p, 1.0), 0.0):.3g}")}


def at_time(d: Path, T: float):
    """(output.sa, snapshot index) of a job or chain directory at time T, or None."""
    import json
    for seg in ([d] if (d / "job.json").exists() else sorted(d.glob("seg*"))):
        if not (seg / "output.sa").exists():
            continue
        p = json.loads((seg / "job.json").read_text())["params"]
        t0, t1, n = float(p["t_start_yr"]), float(p["t_end_yr"]), int(p["snapshots"])
        if t0 < T <= t1:
            k = round((T - t0) / ((t1 - t0) / n)) - 1
            return seg / "output.sa", k
    return None


def last_output(d: Path):
    if (d / "output.sa").exists():
        return d / "output.sa"
    segs = sorted(x for x in d.glob("seg*") if (x / "output.sa").exists())
    return segs[-1] / "output.sa" if segs else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--snapshot", type=int, default=-1)
    ap.add_argument("--time", type=float, default=None, help="years: the same time in every run (snapshots must exist)")
    ap.add_argument("--input", action="store_true", help="analyse the start state (input.sa of the first segment) instead")
    a = ap.parse_args()
    pooled = []
    planets = {}
    t_seen = set()
    for d in map(Path, a.dirs):
        snap = a.snapshot
        if a.input:
            sa, snap = (d / "seg000" / "input.sa" if (d / "seg000").exists() else d / "input.sa"), 0
        elif a.time is not None:
            found = at_time(d, a.time)
            if found is None:
                print(f"{d}: no snapshot at t={a.time:g}")
                continue
            sa, snap = found
        else:
            sa = last_output(d)
        if sa is None:
            continue
        try:
            t, rows = dump(a.p9sim, sa, snap)
        except subprocess.CalledProcessError:
            print(f"{d}: snapshot {snap} not readable")
            continue
        t_seen.add(t)
        sun = [r for r in rows if r[0] == "Sun"][0]
        for name, m, r, v in rows:
            if name in ("Jupiter", "Saturn", "Uranus", "Neptune", "P9"):
                planets.setdefault(name, []).append((r - sun[2], v - sun[3], m))
            elif name != "Sun":
                pooled.append((r - sun[2], v - sun[3]))
    if len(t_seen) != 1:
        print(f"note: snapshots at different times {sorted(t_seen)}")
    t = min(t_seen)
    # Planet Nine: the same in every job (massless test particles); check and use
    p9 = planets["P9"]
    spread = max(float(np.abs(x[0] - p9[0][0]).max()) for x in p9)
    rP, vP, mP = p9[0]
    msun = 1.0000059769986414
    _, _, _, OmP, vpP = elements(G * (msun + mP), rP[None, :], vP[None, :])
    r = np.array([x[0] for x in pooled])
    v = np.array([x[1] for x in pooled])
    A, E, I, Om, vp = elements(G * msun, r, v)
    q = A * (1 - E)
    print(f"t = {t / 1e6:.1f} Myr; {len(a.dirs)} runs; Planet Nine identical in all runs: {spread == 0.0} (max difference {spread:.1e} au)")
    print(f"Planet Nine: varpi {vpP[0]:.1f} deg, Omega {OmP[0]:.1f} deg")
    print(f"test particles: {len(pooled)} surviving")
    for label, sel in [("distant a>230 q>42", (A > 230) & (q > 42) & (E < 1)),
                       ("a 150-1000, q>42", (A > 150) & (A < 1000) & (q > 42) & (E < 1)),
                       ("all bound", (E < 1))]:
        dv = (vp[sel] - vpP[0]) % 360
        dO = (Om[sel] - OmP[0]) % 360
        print(f"  {label:20s} n={int(sel.sum()):5d}  Delta varpi {circ(dv)}  Delta Omega {circ(dO)}")


if __name__ == "__main__":
    main()
