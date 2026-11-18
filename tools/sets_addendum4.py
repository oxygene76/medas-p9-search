#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Addendum 4 of the decomposition (docs/sets-decomposition-addendum-4-20261118.md, 22f70fd): (b) inclination shares
and R beyond the wall with the a,q weighting of Brown & Batygin 2021 (pp. 9-10); (c) bounds for BB-A-rin1 from the
history of q. Exploratory, on the existing snapshots; changes nothing.

  python -I tools/sets_addendum4.py RUN --p9sim P9SIM --wall AU --observed docs/bb2021-observed-table1.tsv [--bounds]

Imports the snapshot readers and frame_elements of tools/prod_eval.py unchanged. Prints JSON.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prod_eval import dump, frame_elements, snapshots  # noqa: E402

WINDOW = (1e9, 4e9)
BANDS = ((0, 30), (30, 40), (40, 50), (50, 70))


def read_observed(path):
    used, all_ = [], []
    for line in open(path):
        s = line.strip()
        if not s or s.startswith("# name") or (s.startswith("#") and len(s.split()) != 5):
            continue
        commented = s.startswith("#")
        f = s.lstrip("# ").split()
        obj = (f[0], float(f[1]), float(f[2]))
        all_.append(obj)
        if not commented:
            used.append(obj)
    return used, all_


def s_a(a):
    frac = 0.05 if a < 230 else 0.30 if a >= 730 else 0.05 + 0.25 * (a - 230) / 500
    return frac * a


def shares(inc, w=None):
    w = np.ones(len(inc)) if w is None else w
    pro = inc < 70
    tot = w[pro].sum()
    out = [float(w[pro & (inc >= lo) & (inc < hi)].sum() / tot) if tot > 0 else math.nan for lo, hi in BANDS]
    return out + [float(w[inc > 90].sum() / w.sum()) if w.sum() > 0 else math.nan]


def weights_aq(a, q, objs):
    W = np.zeros(len(a))
    for _, aj, qj in objs:
        sa = s_a(aj)
        sel = (np.abs(a - aj) <= sa) & (np.abs(q - qj) <= 10) & (q >= 42)
        w = np.where(sel, np.exp(-0.5 * ((a - aj) / (sa / 2)) ** 2) * np.exp(-0.5 * ((q - qj) / 5.0) ** 2), 0.0)
        if w.sum() > 0:
            W += w / w.sum()
    return W


def weights_q(q, objs):
    W = np.zeros(len(q))
    for _, _, qj in objs:
        W += np.where((np.abs(q - qj) <= 10) & (q >= 42), np.exp(-0.5 * ((q - qj) / 5.0) ** 2), 0.0)
    return W


def rbins(a, dv, w, wall):
    Rs = []
    for lo in np.arange(150.0, 700.0, 10.0):
        if lo < wall:
            continue
        s = (a >= lo) & (a < lo + 10) & (w > 0)
        if s.sum() < 10:
            continue
        x = np.radians(dv[s]); ww = w[s]
        Rs.append(math.hypot((ww * np.cos(x)).sum() / ww.sum(), (ww * np.sin(x)).sum() / ww.sum()))
    return float(np.mean(Rs)) if Rs else math.nan, len(Rs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--wall", type=float, required=True)
    ap.add_argument("--observed", required=True)
    ap.add_argument("--bounds", action="store_true")
    a_ = ap.parse_args()
    used, all_ = read_observed(a_.observed)
    run = Path(a_.run)
    snaps = [(0.0, lambda: dump(a_.p9sim, run / "input.sa", 0))] + snapshots(run, a_.p9sim)
    qmin = None
    P = {k: [] for k in ("a", "q", "inc", "dv", "qmin", "snap")}
    Rsnap = {X: [] for X in (None, 4.5, 10.0, 20.0, 30.0)}
    k = 0
    for t, ld in snaps:
        el = frame_elements(*ld())
        if qmin is None:
            qmin = np.full(int(el["idx"].max()) + 1, math.inf)
        cur = np.minimum(qmin[el["idx"]], el["q"]); qmin[el["idx"]] = cur
        if not (WINDOW[0] - 1 <= t <= WINDOW[1] + 1):
            continue
        s = (el["a"] > 150) & (el["a"] < 1000) & (el["q"] > 42)
        P["a"].append(el["a"][s]); P["q"].append(el["q"][s]); P["inc"].append(el["inc"][s]); P["dv"].append(el["dvarpi"][s])
        P["qmin"].append(cur[s]); P["snap"].append(np.full(s.sum(), k)); k += 1
        for X in Rsnap:
            m = np.ones(s.sum(), bool) if X is None else cur[s] >= X
            x = np.radians(el["dvarpi"][s][m])
            Rsnap[X].append(math.hypot(np.cos(x).mean(), np.sin(x).mean()) if len(x) else math.nan)
    P = {key: np.concatenate(v) for key, v in P.items()}
    a, q, inc, dv = P["a"], P["q"], P["inc"], P["dv"]
    out = {"run": a_.run, "wall_au": a_.wall, "snapshots_window": k, "objects_used": [o[0] for o in used]}
    for label, objs in (("10_objects", used), ("11_objects", all_)):
        W = weights_aq(a, q, objs)
        Wq = weights_q(q, objs)
        R, nb = rbins(a, dv, Wq, a_.wall)
        out[f"b_{label}"] = {"inc_shares_weighted": shares(inc, W), "R_beyond_wall_qweighted": R, "bins": nb,
                             "effective_n": float(W.sum() ** 2 / (W ** 2).sum()) if W.sum() > 0 else 0}
    s30 = out["b_10_objects"]["inc_shares_weighted"][0]
    out["b_verdict"] = "the reading fits" if s30 >= 0.88 else "the reading does not fit" if s30 < 0.80 else "unclear"
    if a_.bounds:
        ones = np.ones(len(a))
        for X in (None, 4.5, 10.0, 20.0, 30.0):
            m = ones.astype(bool) if X is None else P["qmin"] >= X
            x = np.radians(dv[m])
            m1 = math.degrees(math.atan2(np.sin(x).mean(), np.cos(x).mean())) % 360 if m.any() else math.nan
            R, nb = rbins(a[m], dv[m], ones[m], a_.wall)
            q100 = m & (q <= 100)
            out[f"c_qmin>={X}" if X else "c_all"] = {
                "M2": float(np.nanmean(Rsnap[X])), "M1_pooled": m1, "R_beyond_wall": R, "particle_snapshots": int(m.sum()),
                "inc_q>42": shares(inc[m]), "inc_q42-100": shares(inc[q100])}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
