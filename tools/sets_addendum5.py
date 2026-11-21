#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Sets A and B, addendum 5 (docs/sets-decomposition-addendum-5-20261121.md): how far the numbers depend on the
definition of the longitude of perihelion (part 1) and on the weighting of R beyond the wall (part 2).
Exploratory, on the existing snapshots; changes neither criteria nor verdicts nor outcome 4.

  python -I tools/sets_addendum5.py RUN --p9sim P9SIM --wall AU [--boot 1000 --seed 20261121 --min-particles 100] > OUT.json

Imports the snapshot readers and frame_elements of tools/prod_eval.py (prod-eval-v1) unchanged: Jupiter's plane at
each snapshot, barycentric elements, dog-leg longitudes. Window 1-4 Gyr (301 snapshots).

Part 1, three definitions of the angle, for the particle and for Planet Nine alike (Delta = particle - Planet Nine):
  a  varpi = Omega + omega for every orbit (as prod-eval-v1; must give the registered M1 and M2)
  b  the azimuth of the eccentricity vector in the reference plane, phi = Omega + atan2(cos i sin omega, cos omega)
     (the definition of tools/analyze.py)
  c  Omega + omega for i < 90 deg, Omega - omega for i > 90 deg
  For each: M1 (circular mean of Delta over S_BB pooled over the window), M2 (mean over the snapshots of R in S_BB),
  R_pooled, R beyond the wall of S_BB (as in part 2, unweighted), and M2 separately for i < 90 deg and i > 90 deg.
  For information, with angle a: M2, R_pooled and R beyond the wall for S_BB with i < 40 deg (no upper limit in q).

Part 2, R beyond the wall, with the registered angle (a), for three selections (150 < a < 1000 au throughout):
  SBB          q > 42 au (as registered; tools/sets_decompose.py, 2d10dae)
  obs_q30-100  30 <= q <= 100 au and i < 40 deg (tools/sets_decompose2.py, 199211e, selection a)
  q42-100_i<30 q > 42 au, q < 100 au, i < 30 deg (tools/sets_decompose.py, selection q42-100_i<30)
  Bins of 10 au of a with lower edge >= the wall, up to 700 au; a bin counts with at least 10 particle-snapshots.
  Per bin: particle-snapshots n, distinct particles k, R. Reported: the unweighted mean over the bins (as before;
  must give the registered values), the mean weighted with n, the unweighted mean of the bins with k >= the minimum,
  and a bootstrap over particles (particles drawn with replacement, each with all its particle-snapshots of the
  selection; the unweighted mean recomputed; 2.5, 50 and 97.5 percentiles).
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prod_eval import S_BB, circ_mean, frame_elements, select, snapshots  # noqa: E402

WINDOW = (1e9, 4e9)
A_MAX = 700.0
DEFS = ("a", "b", "c")


def angles(Omega, varpi, inc):
    """The angles (deg) of definitions a, b, c from Omega, varpi = Omega + omega and inc, all in deg."""
    om = np.radians(varpi - Omega)
    a = varpi % 360
    b = (Omega + np.degrees(np.arctan2(np.cos(np.radians(inc)) * np.sin(om), np.cos(om)))) % 360
    c = np.where(inc > 90, (2 * Omega - varpi) % 360, a)
    return {"a": a, "b": b, "c": c}


def selections(el):
    a, q, inc = el["a"], el["q"], el["inc"]
    base = (a > 150.0) & (a < 1000.0)
    return {"SBB": select(el, S_BB),
            "obs_q30-100": base & (q >= 30.0) & (q <= 100.0) & (inc < 40.0),
            "q42-100_i<30": select(el, S_BB) & (q < 100.0) & (inc < 30.0)}


def beyond(a, dv, idx, wall, min_k, boot, rng):
    """R beyond the wall of pooled particle-snapshots (a, dv in deg, particle idx)."""
    lows = [lo for lo in np.arange(150.0, A_MAX, 10.0) if lo >= wall]
    m = (a >= lows[0]) & (a < A_MAX) if lows else np.zeros(len(a), bool)
    a, x, idx = a[m], np.radians(dv[m]), idx[m]
    b = np.floor((a - lows[0]) / 10.0).astype(int) if lows else np.zeros(0, int)
    nb = len(lows)
    n = np.bincount(b, minlength=nb)
    C = np.bincount(b, weights=np.cos(x), minlength=nb); S = np.bincount(b, weights=np.sin(x), minlength=nb)
    ok = n >= 10
    R = np.where(ok, np.hypot(C, S) / np.maximum(n, 1), np.nan)
    # distinct particles per bin, and the (particle, bin) pairs for the bootstrap
    pid, pinv = np.unique(idx, return_inverse=True)
    pair = pinv.astype(np.int64) * nb + b
    up, upinv = np.unique(pair, return_inverse=True)
    k = np.bincount(up % nb, minlength=nb)
    pc = np.bincount(upinv, weights=np.cos(x)); ps = np.bincount(upinv, weights=np.sin(x)); pn = np.bincount(upinv)
    p_of, b_of = up // nb, up % nb
    bins = [{"a_mid_au": float(lo + 5), "n": int(n[j]), "particles": int(k[j]),
             "R": None if not ok[j] else round(float(R[j]), 4)} for j, lo in enumerate(lows)]
    unw = float(np.nanmean(R)) if ok.any() else None
    wtd = float(np.nansum(R * n) / n[ok].sum()) if ok.any() else None
    big = ok & (k >= min_k)
    unw_big = float(np.nanmean(R[big])) if big.any() else None
    vals = []
    for _ in range(boot):
        w = rng.multinomial(len(pid), np.full(len(pid), 1.0 / len(pid))).astype(float) if len(pid) else np.zeros(0)
        wp = w[p_of]
        nn = np.bincount(b_of, weights=wp * pn, minlength=nb)
        cc = np.bincount(b_of, weights=wp * pc, minlength=nb); ss = np.bincount(b_of, weights=wp * ps, minlength=nb)
        okb = nn >= 10
        if okb.any():
            vals.append(float(np.mean(np.hypot(cc[okb], ss[okb]) / nn[okb])))
    q = [float(v) for v in np.percentile(vals, [2.5, 50, 97.5])] if vals else [None] * 3
    return {"bins": bins, "bins_counted": int(ok.sum()), "particle_snapshots": int(m.sum()), "particles": int(len(pid)),
            "mean_R_unweighted": unw, "mean_R_weighted_n": wtd,
            f"mean_R_bins_with_at_least_{min_k}_particles": unw_big, "bins_with_at_least_min_particles": int(big.sum()),
            "bootstrap_particles": {"replicates": len(vals), "p2.5": q[0], "p50": q[1], "p97.5": q[2]}}


def evaluate(run, p9sim, wall, boot=1000, seed=20261121, min_k=100):
    P1 = {d: {"a": [], "dv": [], "idx": []} for d in DEFS}
    R_t = {d: {"all": [], "pro": [], "retro": []} for d in DEFS}
    I40 = {"R_t": [], "a": [], "dv": [], "idx": []}
    P2 = {s: {"a": [], "dv": [], "idx": []} for s in ("SBB", "obs_q30-100", "q42-100_i<30")}
    n_snap = n_sbb = n_retro = 0
    for t, load in snapshots(run, p9sim):
        if not (WINDOW[0] - 1 <= t <= WINDOW[1] + 1):
            continue
        el = frame_elements(*load())
        p9 = el["p9"]
        A = angles((el["dOmega"] + p9["Omega"]) % 360, (el["dvarpi"] + p9["varpi"]) % 360, el["inc"])
        A9 = angles(np.array([p9["Omega"]]), np.array([p9["varpi"]]), np.array([p9["inc"]]))
        sel = selections(el)
        s = sel["SBB"]
        pro, retro = s & (el["inc"] < 90), s & (el["inc"] > 90)
        n_snap += 1; n_sbb += int(s.sum()); n_retro += int(retro.sum())
        for d in DEFS:
            dv = (A[d] - A9[d][0]) % 360
            R_t[d]["all"].append(circ_mean(dv[s])[1])
            R_t[d]["pro"].append(circ_mean(dv[pro])[1])
            R_t[d]["retro"].append(circ_mean(dv[retro])[1])
            for key, val in (("a", el["a"][s]), ("dv", dv[s]), ("idx", el["idx"][s])):
                P1[d][key].append(val)
        i40 = s & (el["inc"] < 40.0)
        I40["R_t"].append(circ_mean(el["dvarpi"][i40])[1])
        for key, val in (("a", el["a"][i40]), ("dv", el["dvarpi"][i40]), ("idx", el["idx"][i40])):
            I40[key].append(val)
        for name, m in sel.items():
            for key, val in (("a", el["a"][m]), ("dv", el["dvarpi"][m]), ("idx", el["idx"][m])):
                P2[name][key].append(val)
    if n_snap == 0:
        raise SystemExit(f"{run}: no snapshot in the window")
    cat = lambda d: {k: np.concatenate(v) for k, v in d.items()}  # noqa: E731
    out = {"run": str(run), "wall_au": wall, "snapshots_in_window": n_snap, "particle_snapshots_SBB": n_sbb,
           "share_retrograde_SBB": n_retro / n_sbb if n_sbb else None, "part1": {}, "part2": {},
           "bootstrap": {"replicates": boot, "seed": seed, "min_particles": min_k}}
    rng = np.random.default_rng(seed)
    for d in DEFS:
        p = cat(P1[d])
        m1, r_pool = circ_mean(p["dv"])
        out["part1"][d] = {"M1_deg": m1, "M2_mean_R": float(np.mean(R_t[d]["all"])), "R_pooled": r_pool,
                           "M2_i_lt_90": float(np.mean(R_t[d]["pro"])), "M2_i_gt_90": float(np.mean(R_t[d]["retro"])),
                           "R_beyond_wall_SBB": beyond(p["a"], p["dv"], p["idx"], wall, min_k, 0, rng)["mean_R_unweighted"]}
    p = {k: np.concatenate(I40[k]) for k in ("a", "dv", "idx")}
    out["part1"]["a_SBB_i_lt_40"] = {"M2_mean_R": float(np.mean(I40["R_t"])), "R_pooled": circ_mean(p["dv"])[1],
                                     "R_beyond_wall": beyond(p["a"], p["dv"], p["idx"], wall, min_k, 0, rng)["mean_R_unweighted"],
                                     "particle_snapshots": int(len(p["dv"]))}
    for name in P2:
        p = cat(P2[name])
        out["part2"][name] = beyond(p["a"], p["dv"], p["idx"], wall, min_k, boot, rng)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--p9sim", default=None)
    ap.add_argument("--wall", type=float, required=True)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20261121)
    ap.add_argument("--min-particles", type=int, default=100)
    args = ap.parse_args()
    print(json.dumps(evaluate(Path(args.run), args.p9sim, args.wall, args.boot, args.seed, args.min_particles), indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
