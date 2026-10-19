#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Statistical comparison of two runs of the same test particles.

  python tools/compare_stats.py --p9sim build/gcc-O3/p9sim --a CHAIN_DIRS... --b JOB_DIR --times 2e7 1e8 ...

A and B start from the same particles but use different integrators (here
REBOUND WHFast on the CPU and p9gpu on the GPU), so single orbits diverge
(chaos) and only distributions can agree. For every time: surviving test
particles, clustering of Delta varpi and Delta Omega relative to Planet Nine
(mean resultant length R, mean direction), and two-sample Kolmogorov-Smirnov
tests of a, q, i and Delta varpi of the distant particles (a > 230 au, q > 42 au).
Barycentric osculating elements throughout.
"""

import argparse
import math
import subprocess  # noqa: F401 (dump raises CalledProcessError)
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import G, at_time, barycentric, circ, dump, elements  # noqa: E402

MSUN = 1.0000059769986414


def load(dirs, p9sim, T):
    tps, p9 = [], None
    for d in map(Path, dirs):
        found = at_time(d, T)
        if found is None:
            return None
        sa, snap = found
        try:
            t, rows = dump(p9sim, sa, snap)
        except Exception:
            return None  # snapshot not written yet
        # barycentric elements (mu = G M_total): heliocentric osculating elements of
        # distant bodies follow the Sun's wobble (Jupiter's period), which differs
        # in phase between integrators
        rows, mu = barycentric(rows)
        for name, m, r, v in rows:
            if name == "P9":
                p9 = (r, v, m)
            elif name.startswith("tp"):
                tps.append((name, r, v))
    rP, vP, mP = p9
    _, _, _, OmP, vpP = elements(mu, rP[None, :], vP[None, :])
    names = [x[0] for x in tps]
    A, E, I, Om, vp = elements(mu, np.array([x[1] for x in tps]), np.array([x[2] for x in tps]))
    return {"names": names, "a": A, "e": E, "q": A * (1 - E), "i": I, "dvp": (vp - vpP[0]) % 360, "dOm": (Om - OmP[0]) % 360}


def ks(x, y):
    """Two-sample Kolmogorov-Smirnov statistic and asymptotic p-value."""
    x, y = np.sort(x), np.sort(y)
    if len(x) == 0 or len(y) == 0:
        return float("nan"), float("nan")
    allv = np.concatenate([x, y])
    d = np.max(np.abs(np.searchsorted(x, allv, side="right") / len(x) - np.searchsorted(y, allv, side="right") / len(y)))
    n = len(x) * len(y) / (len(x) + len(y))
    lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * d
    p = 2 * sum((-1) ** (k - 1) * math.exp(-2 * k * k * lam * lam) for k in range(1, 101))
    return float(d), float(min(max(p, 0.0), 1.0))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--a", nargs="+", required=True, help="run(s) A (pooled)")
    ap.add_argument("--b", nargs="+", required=True, help="run(s) B (pooled)")
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    ap.add_argument("--times", nargs="+", type=float, required=True)
    a = ap.parse_args()
    for T in a.times:
        A, B = load(a.a, a.p9sim, T), load(a.b, a.p9sim, T)
        if A is None or B is None:
            print(f"t = {T / 1e6:g} Myr: not available in both runs")
            continue
        print(f"t = {T / 1e6:g} Myr")
        for lab, X in ((a.label_a, A), (a.label_b, B)):
            sel = (X["a"] > 230) & (X["q"] > 42) & (X["e"] < 1)
            print(f"  {lab:8s} surviving {len(X['a']):5d}; distant (a>230, q>42) {int(sel.sum()):5d};"
                  f" Delta varpi {circ(X['dvp'][sel])}; Delta Omega {circ(X['dOm'][sel])}")
        sa = (A["a"] > 230) & (A["q"] > 42) & (A["e"] < 1)
        sb = (B["a"] > 230) & (B["q"] > 42) & (B["e"] < 1)
        tests = []
        for key, lo, hi in (("a", 0, 1e4), ("q", 0, 1e4), ("i", 0, 180)):
            fa = A[key][(A["e"] < 1) & (A[key] > lo) & (A[key] < hi)]
            fb = B[key][(B["e"] < 1) & (B[key] > lo) & (B[key] < hi)]
            d, p = ks(fa, fb)
            tests.append(f"{key}: D={d:.3f} p={p:.2f}")
        d, p = ks(A["dvp"][sa], B["dvp"][sb])
        tests.append(f"Delta varpi (distant): D={d:.3f} p={p:.2f}")
        d, p = ks(A["dOm"][sa], B["dOm"][sb])
        tests.append(f"Delta Omega (distant): D={d:.3f} p={p:.2f}")
        print("  KS " + "; ".join(tests))
        # how far single orbits have diverged: the same particles in both runs
        common = sorted(set(A["names"]) & set(B["names"]))
        ia = {n: k for k, n in enumerate(A["names"])}
        ib = {n: k for k, n in enumerate(B["names"])}
        da = np.array([abs(A["a"][ia[n]] - B["a"][ib[n]]) / A["a"][ia[n]] for n in common])
        print(f"  same particle in both runs: {len(common)}; relative difference in a: median {np.median(da):.1e}, 90 % {np.percentile(da, 90):.1e}")


if __name__ == "__main__":
    main()
