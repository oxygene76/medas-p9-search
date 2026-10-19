#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Encounter speeds of the test particles at a planet, from the snapshots of a run.

  python tools/encounter_speeds.py --p9sim build/gcc-O3/p9sim --planet P9 --dmax 2 --times 1e7 5e7 RUN_DIRS...

For the radius rule of docs/close-encounters.md, which needs v99, the 99th
percentile of the relative speed of encounters at each planet. Two estimates
per snapshot, over the test particles whose orbit comes within --dmax au of
the planet's orbit (osculating heliocentric Kepler orbits of both):

- MOID: the closest approach of the two orbits (found on a grid of 720 x 720
  eccentric anomalies, then refined), and the relative speed of the two
  bodies at those points of their orbits (as if both were there at the same
  time; gravitational focusing by the planet neglected, which for these
  planets and speeds changes it by well under a per cent at a few au).
- Opik: U = v_p sqrt(3 - T) with the Tisserand parameter T = a_p/a +
  2 cos(i') sqrt(a (1 - e^2) / a_p), i' the inclination to the planet's
  orbital plane, v_p the circular speed at a_p; exact only for a circular
  planet orbit (Planet Nine: e = 0.21, an approximation).
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import G, at_time, dump  # noqa: E402


def orbit_elements(mu, r, v):
    """a, e, unit vectors P, Q (perifocal) and h for state arrays."""
    rr = np.linalg.norm(r, axis=-1)
    h = np.cross(r, v)
    evec = np.cross(v, h) / mu - r / rr[:, None]
    e = np.linalg.norm(evec, axis=-1)
    a = 1 / (2 / rr - (v * v).sum(-1) / mu)
    P = evec / e[:, None]
    hn = h / np.linalg.norm(h, axis=-1)[:, None]
    Q = np.cross(hn, P)
    return a, e, P, Q, hn


def states(a, e, P, Q, mu, E):
    """Positions and velocities at eccentric anomalies E (shape n x k)."""
    b = a * np.sqrt(1 - e * e)
    cE, sE = np.cos(E), np.sin(E)
    x, y = a[:, None] * (cE - e[:, None]), b[:, None] * sE
    n = np.sqrt(mu / a ** 3)
    edot = n[:, None] / (1 - e[:, None] * cE)
    vx, vy = -a[:, None] * sE * edot, b[:, None] * cE * edot
    pos = x[..., None] * P[:, None, :] + y[..., None] * Q[:, None, :]
    vel = vx[..., None] * P[:, None, :] + vy[..., None] * Q[:, None, :]
    return pos, vel


def moid_speed(mu, tp, pl, k=720):
    """Closest approach of each test particle's orbit to the planet's orbit and the relative speed there."""
    a, e, P, Q, _ = tp
    ap, ep, Pp, Qp, _ = pl
    Eg = np.linspace(0, 2 * np.pi, k, endpoint=False)
    pp, vp = states(ap, ep, Pp, Qp, mu, Eg[None, :])
    pp, vp = pp[0], vp[0]
    dmin = np.empty(len(a))
    vrel = np.empty(len(a))
    for i in range(len(a)):
        # grid, then a finer grid around the best cell
        E1, E2 = Eg, Eg
        p1, v1 = states(a[i:i + 1], e[i:i + 1], P[i:i + 1], Q[i:i + 1], mu, E1[None, :])
        d = np.linalg.norm(p1[0][:, None, :] - pp[None, :, :], axis=-1)
        j1, j2 = np.unravel_index(np.argmin(d), d.shape)
        step = 2 * np.pi / k
        for _ in range(3):
            f1 = E1[j1] + np.linspace(-step, step, 41)
            f2 = E2[j2] + np.linspace(-step, step, 41)
            q1, w1 = states(a[i:i + 1], e[i:i + 1], P[i:i + 1], Q[i:i + 1], mu, f1[None, :])
            q2, w2 = states(ap, ep, Pp, Qp, mu, f2[None, :])
            d = np.linalg.norm(q1[0][:, None, :] - q2[0][None, :, :], axis=-1)
            j1, j2 = np.unravel_index(np.argmin(d), d.shape)
            E1, E2, step = f1, f2, step / 20
        dmin[i] = d[j1, j2]
        vrel[i] = np.linalg.norm(w1[0][j1] - w2[0][j2])
    return dmin, vrel


def opik(mu, tp, pl):
    a, e, _, _, h = tp
    ap, _, _, _, hp = pl
    cosi = np.clip((h * hp).sum(-1), -1, 1)
    T = ap[0] / a + 2 * cosi * np.sqrt(np.clip(a * (1 - e * e) / ap[0], 0, None))
    return np.sqrt(mu / ap[0]) * np.sqrt(np.clip(3 - T, 0, None))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--planet", required=True)
    ap.add_argument("--dmax", type=float, default=2.0, help="au: orbits that come this close to the planet's orbit count")
    ap.add_argument("--times", nargs="+", type=float, required=True)
    ap.add_argument("dirs", nargs="+")
    a = ap.parse_args()
    print(f"planet {a.planet}, orbits within {a.dmax} au of its orbit; speeds in au/yr")
    print("      t   n_bodies  n_close |  MOID v_rel: median   90%    99%    max |  Opik U: median   90%    99%")
    for T in a.times:
        tps, pl, sun, msun = [], None, None, None
        for d in map(Path, a.dirs):
            found = at_time(d, T)
            if found is None:
                continue
            _, rows = dump(a.p9sim, *found)
            for name, m, r, v in rows:
                if name == "Sun":
                    sun, msun = (r, v), m
                elif name == a.planet:
                    pl = (r, v, m)
                elif name.startswith("tp"):
                    tps.append((r, v))
        if pl is None or not tps:
            print(f"{T / 1e6:7.0f} Myr: no snapshot")
            continue
        mu = G * msun
        rt = np.array([x[0] for x in tps]) - sun[0]
        vt = np.array([x[1] for x in tps]) - sun[1]
        tp = orbit_elements(mu, rt, vt)
        bound = (tp[1] < 1) & (tp[0] > 0)
        tp = tuple(x[bound] for x in tp)
        pel = orbit_elements(G * (msun + pl[2]), (pl[0] - sun[0])[None, :], (pl[1] - sun[1])[None, :])
        q, Qa = tp[0] * (1 - tp[1]), tp[0] * (1 + tp[1])
        qp, Qp = pel[0][0] * (1 - pel[1][0]), pel[0][0] * (1 + pel[1][0])
        cand = (q < Qp + a.dmax) & (Qa > qp - a.dmax)  # radial ranges overlap: only these can come close
        sub = tuple(x[cand] for x in tp)
        dmin, vrel = moid_speed(G * msun, sub, pel)
        close = dmin < a.dmax
        U = opik(G * msun, tuple(x[close] for x in sub), pel)
        pct = lambda x, p: float(np.percentile(x, p)) if len(x) else float("nan")
        v = vrel[close]
        print(f"{T / 1e6:7.0f} Myr {len(tp[0]):8d} {int(close.sum()):8d} |  {pct(v, 50):6.3f} {pct(v, 90):6.3f} {pct(v, 99):6.3f} "
              f"{(v.max() if len(v) else float('nan')):6.3f} |  {pct(U, 50):6.3f} {pct(U, 90):6.3f} {pct(U, 99):6.3f}")


if __name__ == "__main__":
    main()
