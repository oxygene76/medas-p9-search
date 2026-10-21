#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Evaluation of the direct comparison p9gpu against WHFast (tools/direct_wh.c, tools/direct_wh_run.sh).

  python tools/direct_wh_eval.py runs/cause/direct [PAIR ...]

PAIR directories (default pw pp ww): pw = p9gpu against WHFast on member 0; pp = p9gpu member 0 against member 1
(start positions 1e-12 apart: the chaos baseline); ww = the same with WHFast. Per pair: the first time the
relative position difference of a test particle exceeds 1e-12, 1e-8, 1e-4, 1e-2 (quantiles over the particles
that cross it, and the fraction that crosses by 1 and 10 Myr), the time from 1e-12 to 1e-4, where the 1e-8 and
1e-4 separations happen (closest distance to Neptune and Planet Nine in the 1 to 2 kyr before; q and a), and the
planets' and Planet Nine's element differences (pw only; in pp and ww both sides have the same planets).
"""

import sys
from pathlib import Path

import numpy as np

THR = ["1e-12", "1e-08", "0.0001", "0.01"]
NAMES = {1: "Jupiter", 2: "Saturn", 3: "Uranus", 4: "Neptune", 5: "P9"}
DT = 0.5


def load_tp(d):
    rows = []
    for f in sorted(d.glob("s*.tp.tsv")):
        lines = f.read_text().splitlines()
        head = lines[0].split("\t")
        rows += [dict(zip(head, map(float, ln.split("\t")))) for ln in lines[1:]]
    return rows


def tp_report(name, rows):
    n = len(rows)
    print(f"\n== {name}: {n} test particles")
    print("threshold | crossed by 1 Myr | by 10 Myr | first time (Myr): 10 %, 25 %, median of those crossing")
    for t in THR:
        s = np.array([r[f"step_{t}"] for r in rows]) * DT / 1e6
        c = s[s > 0]
        q = np.percentile(c, [10, 25, 50]) if len(c) else [np.nan] * 3
        print(f"  {float(t):7.0e} | {np.sum((s > 0) & (s <= 1)):4d} ({np.mean((s > 0) & (s <= 1)):.1%}) | {len(c):4d} ({len(c) / n:.1%}) | "
              f"{q[0]:.3f} {q[1]:.3f} {q[2]:.3f}")
    a = np.array([r["step_1e-12"] for r in rows]) * DT / 1e6
    b = np.array([r["step_0.0001"] for r in rows]) * DT / 1e6
    m = (a > 0) & (b > 0)
    if m.any():
        g = b[m] - a[m]
        print(f"  time from 1e-12 to 1e-4 (Myr), {m.sum()} particles: 25 % {np.percentile(g, 25):.3f}, median {np.median(g):.3f}, 75 % {np.percentile(g, 75):.3f}")
    for t in ("1e-08", "0.0001"):
        s = np.array([r[f"step_{t}"] for r in rows])
        sel = [r for r, x in zip(rows, s) if x > 0]
        if not sel:
            continue
        dN = np.array([r[f"dminN_{t}"] for r in sel])
        dP = np.array([r[f"dminP9_{t}"] for r in sel])
        q = np.array([r[f"q_{t}"] for r in sel])
        aa = np.array([r[f"a_{t}"] for r in sel])
        print(f"  where the {float(t):.0e} separations happen ({len(sel)}): closest to Neptune within 1-2 kyr before: < 1 au {np.mean(dN < 1):.1%}, "
              f"< 2.3 au (3 Hill) {np.mean(dN < 2.33):.1%}, < 5 au {np.mean(dN < 5):.1%}; to Planet Nine < 21 au (3 Hill) {np.mean(dP < 20.95):.1%}; "
              f"neither (Neptune > 5 au and P9 > 21 au) {np.mean((dN >= 5) & (dP >= 20.95)):.1%}")
        print(f"     q: <35 au {np.mean(q < 35):.1%}, 35-42 {np.mean((q >= 35) & (q < 42)):.1%}, 42-50 {np.mean((q >= 42) & (q < 50)):.1%}, >50 {np.mean(q >= 50):.1%}; "
              f"a median {np.median(aa[aa > 0]):.0f} au")
    # the same split for all particles at the start: which q do the not separated ones have
    s = np.array([r["step_1e-08"] for r in rows])
    q0 = np.array([r["q_1e-12"] for r in rows])
    ok = q0 > 0
    for lo, hi in ((0, 42), (42, 50), (50, 1e9)):
        sel = ok & (q0 >= lo) & (q0 < hi)
        if sel.any():
            print(f"  q at 1e-12 in [{lo}, {hi if hi < 1e9 else 'inf'}) au: {sel.sum()} particles, crossed 1e-8 by 10 Myr {np.mean(s[sel] > 0):.1%}")


def planets_report(d):
    f = d / "s0.planets.tsv"
    lines = f.read_text().splitlines()
    head = lines[0].split("\t")
    x = np.array([list(map(float, ln.split("\t"))) for ln in lines[1:]])
    col = {h: i for i, h in enumerate(head)}
    print("\n== planets and Planet Nine, p9gpu against WHFast (B - A): relQ, da/a, de, di (deg), dvarpi (deg), dOmega (deg)")
    for body, nm in NAMES.items():
        y = x[x[:, col["body"]] == body]
        for T in (1e3, 1e4, 1e5, 1e6, 3e6, 1e7):
            k = np.argmin(abs(y[:, col["t"]] - T))
            r = y[k]
            print(f"  {nm:8s} t={r[col['t']] / 1e6:6.3f} Myr  relQ {r[col['relQ']]:.2e}  da/a {r[col['da_rel']]:+.2e}  de {r[col['de']]:+.2e}  "
                  f"di {r[col['di_deg']]:+.2e}  dvarpi {r[col['dvarpi_deg']]:+.2e}  dOmega {r[col['dOmega_deg']]:+.2e}")
        # drift: max |d| over the run
        print(f"  {nm:8s} max over 10 Myr: |da/a| {abs(y[:, col['da_rel']]).max():.2e}  |de| {abs(y[:, col['de']]).max():.2e}  "
              f"|dvarpi| {abs(y[:, col['dvarpi_deg']]).max():.2e} deg  |dOmega| {abs(y[:, col['dOmega_deg']]).max():.2e} deg")


def main():
    root = Path(sys.argv[1])
    pairs = sys.argv[2:] or ["pw", "pp", "ww"]
    for p in pairs:
        d = root / p
        if not d.exists():
            continue
        tp_report({"pw": "p9gpu against WHFast, member 0", "pp": "p9gpu member 0 against member 1 (1e-12)",
                   "ww": "WHFast member 0 against member 1 (1e-12)"}.get(p, p), load_tp(d))
        if p == "pw":
            planets_report(d)


if __name__ == "__main__":
    main()
