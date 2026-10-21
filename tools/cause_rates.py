#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Precession rates of the same distant bodies in two runs, from the 1-Myr files of tools/cause_extract.py.

  python tools/cause_rates.py runs/cause/elements-1myr [--window 100 200]

For each pair of runs (X, Y) the bodies (particle index i) that are distant (a > 230 au, q > 42 au)
at every snapshot of the window in both runs; per body the rate of dvarpi (linear fit of the
unwrapped angle over the window, deg/Myr). Reported per pair group (G-M across the integrators,
G-G and M1-M0 within, as the reference for chaos): the median of rate_X - rate_Y with its spread,
the standard deviation of the rates in X relative to Y, the slope of the rate against ln a in X
relative to Y, and the same split by a.
"""

import argparse
from pathlib import Path

import numpy as np

G_RUNS = ["G0", "G1", "G2", "G3"]
PAIRS = {"G-M": [(g, m) for m in ("M0", "M1") for g in G_RUNS],
         "G-G": [("G1", "G0"), ("G2", "G0"), ("G3", "G0"), ("G2", "G1"), ("G3", "G1"), ("G3", "G2")],
         "M1-M0": [("M1", "M0")]}


def series(files, run):
    """i -> (t, a, q, dvarpi) over the files where the body is alive."""
    out = {}
    for f in files:
        d = np.load(f)
        if run + "_i" not in d.files:
            continue
        T = float(f.name[1:6])
        el = d[run + "_el"]
        for i, a, e, dv in zip(d[run + "_i"], el[:, 0], el[:, 1], el[:, 5]):
            out.setdefault(int(i), []).append((T, a, a * (1 - e), dv))
    return {i: np.array(v) for i, v in out.items()}


def window_rates(s, lo, hi, n_need):
    out = {}
    for i, v in s.items():
        w = v[(v[:, 0] >= lo) & (v[:, 0] <= hi)]
        if len(w) < n_need or not ((w[:, 1] > 230) & (w[:, 2] > 42)).all():
            continue
        out[i] = (np.polyfit(w[:, 0], np.degrees(np.unwrap(np.radians(w[:, 3]))), 1)[0], w[:, 1].mean())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir")
    ap.add_argument("--window", type=float, nargs=2, default=[100, 200])
    a = ap.parse_args()
    files = sorted(Path(a.dir).glob("t*Myr.npz"))
    lo, hi = a.window
    n_need = sum(1 for f in files if lo <= float(f.name[1:6]) <= hi)
    rates = {r: window_rates(series(files, r), lo, hi, n_need) for r in G_RUNS + ["M0", "M1"]}
    print(f"window {lo:.0f}-{hi:.0f} Myr ({n_need} snapshots); bodies distant throughout: " + ", ".join(f"{r} {len(v)}" for r, v in rates.items()))
    print("pairs   | n common | median rate X-Y   | |X-Y| median | std X / std Y - 1 | slope(ln a) X / Y - 1 | median X-Y by a: 230-300, 300-400, >400")
    for name, pairs in PAIRS.items():
        cols = []
        for X, Y in pairs:
            c = sorted(set(rates[X]) & set(rates[Y]))
            rx = np.array([rates[X][i][0] for i in c]); ry = np.array([rates[Y][i][0] for i in c]); la = np.log(np.array([rates[Y][i][1] for i in c]))
            aa = np.exp(la)
            bins = [np.median((rx - ry)[(aa >= b0) & (aa < b1)]) if ((aa >= b0) & (aa < b1)).any() else np.nan for b0, b1 in ((230, 300), (300, 400), (400, 1e9))]
            cols.append((len(c), np.median(rx - ry), np.median(np.abs(rx - ry)), rx.std() / ry.std() - 1,
                         np.polyfit(la, rx, 1)[0] / np.polyfit(la, ry, 1)[0] - 1, *bins))
        c = np.array(cols)
        m, s = np.nanmean(c, axis=0), np.nanstd(c, axis=0, ddof=1) if len(c) > 1 else np.zeros(c.shape[1])
        print(f"{name:7s} | {m[0]:6.0f}   | {m[1]:+.4f} ± {s[1]:.4f} | {m[2]:.4f}       | {m[3]:+.3f} ± {s[3]:.3f}    | {m[4]:+.3f} ± {s[4]:.3f}        | "
              f"{m[5]:+.4f} {m[6]:+.4f} {m[7]:+.4f}")
    # the rates themselves, per group, by a
    print("\nmedian rate of dvarpi (deg/Myr) by a, group means")
    for grp, runs in (("G", G_RUNS), ("M", ["M0", "M1"])):
        cells = []
        for b0, b1 in ((230, 300), (300, 400), (400, 1e9)):
            cells.append(np.mean([np.median([v[0] for v in rates[r].values() if b0 <= v[1] < b1]) for r in runs]))
        print(f"  {grp}: " + ", ".join(f"{x:+.4f}" for x in cells))


if __name__ == "__main__":
    main()
