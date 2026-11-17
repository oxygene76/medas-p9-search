#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Decomposition of sets A and B, addendum 2 (docs/sets-decomposition-addendum-2-20261117.md, 843438e): the selection of
Batygin et al. 2019. Exploratory, after outcome 4; changes neither criteria nor verdicts nor outcome.

  python -I tools/sets_decompose2.py RUN --p9sim P9SIM --wall AU --out DIR --name A|B

Imports the snapshot readers and frame_elements of tools/prod_eval.py (prod-eval-v1) unchanged.
Writes summary.json (means, anti-aligned shares, inclination shares, verdicts), bins.csv, inc_hist.csv and
image_a_survivors.npz (a x dvarpi, 2 au x 1 deg, normalised per a column).
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prod_eval import frame_elements, snapshots  # noqa: E402

WINDOW = (1e9, 4e9)
A_MAX = 700.0
SELECTIONS = {"a_q30-100_i<40": (30.0, 100.0, 40.0), "b_q42-100_i<40": (42.0, 100.0, 40.0), "c_q>42": (42.0, math.inf, None)}


def rlen(deg):
    if len(deg) == 0:
        return math.nan
    x = np.radians(deg)
    return math.hypot(np.cos(x).mean(), np.sin(x).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--wall", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    snaps = snapshots(args.run, args.p9sim)
    win = [(t, ld) for t, ld in snaps if WINDOW[0] - 1 <= t <= WINDOW[1] + 1]
    last_t, last_ld = snaps[-1]
    survivors = set(frame_elements(*last_ld())["idx"].tolist())
    P = {k: [] for k in ("idx", "a", "q", "inc", "dvarpi")}
    for t, ld in win:
        el = frame_elements(*ld())
        s = (el["a"] > 150.0) & (el["a"] < 1000.0) & (el["q"] >= 30.0)
        for k in P:
            P[k].append(el[k][s])
    P = {k: np.concatenate(v) for k, v in P.items()}
    surv = np.isin(P["idx"], list(survivors))
    a, q, inc, dv = P["a"], P["q"], P["inc"], P["dvarpi"]
    edges = np.arange(150.0, A_MAX + 1e-9, 10.0)
    res = {"name": args.name, "wall_au": args.wall, "snapshots_window": len(win), "last_snapshot_yr": last_t,
           "n_survivors": len(survivors), "selections": {}}
    rows_out, hist_out = [], []
    for name, (qlo, qhi, imax) in SELECTIONS.items():
        qcut = (q >= qlo) & (q <= qhi) if name != "c_q>42" else (q > qlo)
        full = qcut & (inc < imax) if imax is not None else qcut
        for who, w in (("all", np.ones(len(a), bool)), ("survivors", surv)):
            m = full & w
            Rs = []
            for lo in edges[:-1]:
                s = m & (a >= lo) & (a < lo + 10)
                n = int(s.sum())
                R = rlen(dv[s]) if n >= 10 else math.nan
                rows_out.append([name, who, f"{lo + 5:.0f}", n, f"{R:.4f}"])
                if lo >= args.wall and not math.isnan(R):
                    Rs.append(R)
            bw = m & (a >= args.wall) & (a < A_MAX)
            anti = float(((dv[bw] > 90) & (dv[bw] < 270)).mean()) if bw.any() else math.nan
            qw = qcut & w  # inclinations: q cut, no i cut, 150 < a < 1000
            ih = np.histogram(inc[qw], bins=np.arange(0, 185, 5))[0]
            for lo, n in zip(range(0, 180, 5), ih):
                hist_out.append([name, who, lo, lo + 5, int(n)])
            mean = float(np.mean(Rs)) if Rs else math.nan
            res["selections"][f"{name}/{who}"] = {
                "mean_R_beyond_wall": mean, "bins": len(Rs), "particle_snapshots_beyond_wall": int(bw.sum()),
                "anti_share_beyond_wall": anti,
                "inc_q_cut_only": {"n": int(qw.sum()), "lt30": float((inc[qw] < 30).mean()), "lt40": float((inc[qw] < 40).mean()),
                                   "gt50": float((inc[qw] > 50).mean()), "gt90": float((inc[qw] > 90).mean())},
                "share_i_lt30_within_selection": float((inc[m] < 30).mean()) if m.any() else math.nan,
                "verdict": ("no bins" if math.isnan(mean) else "cluster as in the figures" if mean >= 0.4 else "no cluster" if mean <= 0.2 else "unclear"),
            }
    with open(out / "bins.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["selection", "who", "a_mid_au", "n", "R"]); w.writerows(rows_out)
    with open(out / "inc_hist.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["selection", "who", "i_lo", "i_hi", "n"]); w.writerows(hist_out)
    qlo, qhi, imax = SELECTIONS["a_q30-100_i<40"]
    m = (q >= qlo) & (q <= qhi) & (inc < imax) & surv
    H = np.histogram2d(dv[m], a[m], bins=[360, 450], range=[[0, 360], [100, 1000]])[0]
    col = H.sum(0)
    np.savez_compressed(out / "image_a_survivors.npz", img=np.where(col > 0, H / np.where(col > 0, col, 1), np.nan).astype(np.float32),
                        n=col.astype(np.int64))
    (out / "summary.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    for k, v in res["selections"].items():
        print(f"{args.name} {k:28s} R {v['mean_R_beyond_wall']:.3f}  anti {v['anti_share_beyond_wall']:.3f}  {v['verdict']}")


if __name__ == "__main__":
    main()
