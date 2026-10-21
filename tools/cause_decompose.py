#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Where does the difference in R(dvarpi) of the distant particles come from? (docs/cause-analysis.md)

  python tools/cause_decompose.py runs/cause/elements [--json out.json]

Input: the files of tools/cause_extract.py. Distant: a > 230 au and q > 42 au (as the evaluation).
Per time:
- the number of distant particles per run, and R(dvarpi) per run with the group means;
- for pairs of runs (X, Y), by particle index i: the bodies distant in both (C), only in X, only in Y;
  R of X and of Y on C (same bodies, own angles: "angles"), and the rest of R_X - R_Y ("composition");
  pairs across the groups (G-M) against pairs within a group (G-G, M1-M0) as the reference for chaos;
- "swap": R of the bodies distant in X with the angles they have in Y, and vice versa;
- R per bin of a and of q, group means;
- the mean direction of dvarpi per group; Planet Nine's varpi and Omega and Neptune's heliocentric
  longitude and varpi, G against M0.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

G_RUNS = ["G0", "G1", "G2", "G3"]
M_RUNS = ["M0", "M1"]
PAIRS_GM = [("G0", "M0"), ("G1", "M0"), ("G2", "M0"), ("G3", "M0"), ("G0", "M1"), ("G1", "M1"), ("G2", "M1"), ("G3", "M1")]
PAIRS_GG = [("G1", "G0"), ("G2", "G0"), ("G3", "G0"), ("G2", "G1"), ("G3", "G1"), ("G3", "G2")]
PAIRS_MM = [("M1", "M0")]
A_BINS = [(230, 300), (300, 400), (400, 1e9)]
Q_BINS = [(42, 50), (50, 1e9)]


def R(theta_deg):
    if len(theta_deg) == 0:
        return float("nan")
    x = np.radians(theta_deg)
    return math.hypot(np.cos(x).mean(), np.sin(x).mean())


def mean_dir(theta_deg):
    x = np.radians(theta_deg)
    return math.degrees(math.atan2(np.sin(x).mean(), np.cos(x).mean())) % 360


def runs_at(d):
    out = {}
    for k in d.files:
        if k.endswith("_i"):
            name = k[:-2]
            el = d[name + "_el"]
            a, e = el[:, 0], el[:, 1]
            out[name] = {"i": d[k], "a": a, "q": a * (1 - e), "dvarpi": el[:, 5], "dOmega": el[:, 6], "planets": d[name + "_planets"]}
    return out


def distant(r):
    return (r["a"] > 230) & (r["q"] > 42)


def by_index(r, mask):
    return {int(i): float(t) for i, t in zip(r["i"][mask], r["dvarpi"][mask])}


def pair_stats(X, Y):
    dx, dy = by_index(X, distant(X)), by_index(Y, distant(Y))
    ax, ay = by_index(X, np.ones(len(X["i"]), bool)), by_index(Y, np.ones(len(Y["i"]), bool))
    C = sorted(set(dx) & set(dy))
    rx, ry = R(list(dx.values())), R(list(dy.values()))
    rxc, ryc = R([dx[i] for i in C]), R([dy[i] for i in C])
    # swap: the bodies distant in X with the angles they have in Y (if they survive there), and vice versa
    sx = [ay[i] for i in dx if i in ay]
    sy = [ax[i] for i in dy if i in ax]
    return {"nX": len(dx), "nY": len(dy), "common": len(C), "onlyX": len(dx) - len(C), "onlyY": len(dy) - len(C),
            "dR": rx - ry, "angles": rxc - ryc, "composition": (rx - ry) - (rxc - ryc),
            "R_onlyX": R([dx[i] for i in dx if i not in dy]), "R_onlyY": R([dy[i] for i in dy if i not in dx]),
            "swap_X_sel_Y_angles": R(sx), "swap_Y_sel_X_angles": R(sy), "R_X": rx, "R_Y": ry}


def mean(pairs, key, st):
    v = [st[p][key] for p in pairs]
    return float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else float("nan")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir")
    ap.add_argument("--json")
    a = ap.parse_args()
    files = sorted(Path(a.dir).glob("t*Myr.npz"))
    res = []
    print("R(dvarpi) of the distant particles; dR of pairs split into 'angles' (same bodies) and 'composition' (which bodies);")
    print("G-M: mean over the 8 pairs across the groups; ref: mean over the 6 G-G pairs and M1-M0 (chaos only)\n")
    print("   t |  n_G  n_M | R_G    R_M   | G-M: dR    angles  compos. | ref: dR   angles  compos. | common/n G-M ref")
    for f in files:
        T = float(f.name[1:6])
        d = np.load(f)
        r = runs_at(d)
        if not all(k in r for k in G_RUNS + M_RUNS):
            continue
        st = {p: pair_stats(r[p[0]], r[p[1]]) for p in PAIRS_GM + PAIRS_GG + PAIRS_MM}
        nG = np.mean([distant(r[k]).sum() for k in G_RUNS]); nM = np.mean([distant(r[k]).sum() for k in M_RUNS])
        RG = np.mean([R(r[k]["dvarpi"][distant(r[k])]) for k in G_RUNS]); RM = np.mean([R(r[k]["dvarpi"][distant(r[k])]) for k in M_RUNS])
        ref = PAIRS_GG + PAIRS_MM
        row = {"t_Myr": T, "n_G": nG, "n_M": nM, "R_G": RG, "R_M": RM}
        for name, pairs in (("GM", PAIRS_GM), ("ref", ref)):
            for key in ("dR", "angles", "composition"):
                row[f"{name}_{key}"] = mean(pairs, key, st)[0]
            row[f"{name}_common_frac"] = float(np.mean([st[p]["common"] / st[p]["nX"] for p in pairs]))
        # the signed G-M difference uses (G, M) order; the reference pairs have no natural sign: use |dR|
        row["ref_absdR"] = float(np.mean([abs(st[p]["dR"]) for p in ref]))
        row["ref_absangles"] = float(np.mean([abs(st[p]["angles"]) for p in ref]))
        row["ref_abscomposition"] = float(np.mean([abs(st[p]["composition"]) for p in ref]))
        row["swap_G_sel_M_angles"] = mean(PAIRS_GM, "swap_X_sel_Y_angles", st)[0]
        row["swap_M_sel_G_angles"] = mean(PAIRS_GM, "swap_Y_sel_X_angles", st)[0]
        row["R_onlyG"] = mean(PAIRS_GM, "R_onlyX", st)[0]; row["R_onlyM"] = mean(PAIRS_GM, "R_onlyY", st)[0]
        for lo, hi in A_BINS:
            row[f"a{lo}"] = (float(np.mean([R(r[k]["dvarpi"][distant(r[k]) & (r[k]["a"] >= lo) & (r[k]["a"] < hi)]) for k in G_RUNS])),
                             float(np.mean([R(r[k]["dvarpi"][distant(r[k]) & (r[k]["a"] >= lo) & (r[k]["a"] < hi)]) for k in M_RUNS])),
                             float(np.mean([(distant(r[k]) & (r[k]["a"] >= lo) & (r[k]["a"] < hi)).sum() for k in G_RUNS])),
                             float(np.mean([(distant(r[k]) & (r[k]["a"] >= lo) & (r[k]["a"] < hi)).sum() for k in M_RUNS])))
        for lo, hi in Q_BINS:
            row[f"q{lo}"] = (float(np.mean([R(r[k]["dvarpi"][distant(r[k]) & (r[k]["q"] >= lo) & (r[k]["q"] < hi)]) for k in G_RUNS])),
                             float(np.mean([R(r[k]["dvarpi"][distant(r[k]) & (r[k]["q"] >= lo) & (r[k]["q"] < hi)]) for k in M_RUNS])),
                             float(np.mean([(distant(r[k]) & (r[k]["q"] >= lo) & (r[k]["q"] < hi)).sum() for k in G_RUNS])),
                             float(np.mean([(distant(r[k]) & (r[k]["q"] >= lo) & (r[k]["q"] < hi)).sum() for k in M_RUNS])))
        row["dir_G"] = mean_dir(np.concatenate([r[k]["dvarpi"][distant(r[k])] for k in G_RUNS]))
        row["dir_M"] = mean_dir(np.concatenate([r[k]["dvarpi"][distant(r[k])] for k in M_RUNS]))
        pg, pm = r["G0"]["planets"], r["M0"]["planets"]  # rows Jupiter, Saturn, Uranus, Neptune, P9; cols a e i Omega varpi lon
        w = lambda x: (x + 180) % 360 - 180
        row["P9_dvarpi_GM0"] = float(w(pg[4, 4] - pm[4, 4])); row["P9_dOmega_GM0"] = float(w(pg[4, 3] - pm[4, 3]))
        row["Nep_dlon_GM0"] = float(w(pg[3, 5] - pm[3, 5])); row["Nep_dvarpi_GM0"] = float(w(pg[3, 4] - pm[3, 4]))
        row["Nep_dlon_M1M0"] = float(w(r["M1"]["planets"][3, 5] - pm[3, 5]))
        res.append(row)
        print(f"{T:5.0f} | {nG:5.0f} {nM:5.0f} | {RG:.4f} {RM:.4f} | {row['GM_dR']:+.4f} {row['GM_angles']:+.4f} {row['GM_composition']:+.4f} | "
              f"{row['ref_absdR']:.4f} {row['ref_absangles']:.4f} {row['ref_abscomposition']:.4f} | {row['GM_common_frac']:.2f} {row['ref_common_frac']:.2f}")
    print("\nswap: R of the bodies distant in G with their M angles (and vice versa), only-G / only-M bodies; direction of the cluster")
    print("   t | R_G   R(G sel., M angles) | R_M   R(M sel., G angles) | R only-G  only-M | dir G   dir M")
    for x in res:
        print(f"{x['t_Myr']:5.0f} | {x['R_G']:.4f} {x['swap_G_sel_M_angles']:.4f}            | {x['R_M']:.4f} {x['swap_M_sel_G_angles']:.4f}            | "
              f"{x['R_onlyG']:.4f}   {x['R_onlyM']:.4f} | {x['dir_G']:6.1f} {x['dir_M']:6.1f}")
    print("\nR by a and by q (G mean / M mean, numbers of bodies)")
    print("   t | a 230-300          | a 300-400          | a > 400            | q 42-50            | q > 50")
    for x in res:
        cells = [x[k] for k in ("a230", "a300", "a400", "q42", "q50")]
        print(f"{x['t_Myr']:5.0f} | " + " | ".join(f"{c[0]:.3f}/{c[1]:.3f} {c[2]:4.0f}/{c[3]:4.0f}" for c in cells))
    print("\nPlanet Nine and Neptune, G0 minus M0 (deg): P9 varpi, P9 Omega, Neptune heliocentric longitude, Neptune varpi; Neptune longitude M1 - M0")
    for x in res:
        print(f"{x['t_Myr']:5.0f} | {x['P9_dvarpi_GM0']:+8.4f} {x['P9_dOmega_GM0']:+8.4f} | {x['Nep_dlon_GM0']:+8.2f} {x['Nep_dvarpi_GM0']:+8.2f} | {x['Nep_dlon_M1M0']:+8.3f}")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
