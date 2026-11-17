#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Spread of M2 and of the inclination shares over the 4 subsets of a set (index blocks as in prod_eval.py), for the
scale of the criteria of the run BB-A-rin1 (draft of 2026-11-17). Exploratory, on the existing snapshots; changes
nothing.

  python -I tools/sets_subset_spread.py RUN --p9sim P9SIM [--subsets 4] [--n-tp 64000]

Prints JSON: per subset and for the whole set M2 (mean over the window snapshots of R of dvarpi in S_BB) and the
inclination shares for 150 < a < 1000 au, 1-4 Gyr, for q > 42 au and for 42 <= q <= 100 au: below 30, 30-40, 40-50,
50-70 deg normalised to 0-70 deg, and the retrograde share (i > 90 deg) of all.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prod_eval import frame_elements, snapshots  # noqa: E402

WINDOW = (1e9, 4e9)
BANDS = ((0, 30), (30, 40), (40, 50), (50, 70))


def shares(inc):
    pro = inc[inc < 70]
    n = len(pro)
    out = [float(((pro >= lo) & (pro < hi)).sum() / n) if n else math.nan for lo, hi in BANDS]
    return out + [float((inc > 90).mean()) if len(inc) else math.nan]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--subsets", type=int, default=4)
    ap.add_argument("--n-tp", type=int, default=64000)
    a = ap.parse_args()
    block = a.n_tp // a.subsets
    groups = list(range(a.subsets)) + ["all"]
    R = {g: [] for g in groups}
    INC42 = {g: [] for g in groups}
    INC100 = {g: [] for g in groups}
    for t, ld in snapshots(a.run, a.p9sim):
        if not (WINDOW[0] - 1 <= t <= WINDOW[1] + 1):
            continue
        el = frame_elements(*ld())
        sub = el["idx"] // block
        sbb = (el["a"] > 150) & (el["a"] < 1000) & (el["q"] > 42)
        q100 = sbb & (el["q"] <= 100)
        for g in groups:
            m = np.ones(len(sub), bool) if g == "all" else (sub == g)
            x = np.radians(el["dvarpi"][m & sbb])
            R[g].append(math.hypot(np.cos(x).mean(), np.sin(x).mean()) if len(x) else math.nan)
            INC42[g].append(el["inc"][m & sbb]); INC100[g].append(el["inc"][m & q100])
    out = {}
    for g in groups:
        out[str(g)] = {"M2": float(np.nanmean(R[g])), "inc_q>42": shares(np.concatenate(INC42[g])),
                       "inc_q42-100": shares(np.concatenate(INC100[g])), "snapshots": len(R[g])}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
