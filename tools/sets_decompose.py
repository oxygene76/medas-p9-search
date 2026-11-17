#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exploratory decomposition of sets A and B beyond the wall (docs/sets-decomposition-addendum-20261117.md, 6130d44).

After outcome 4; it changes neither the criteria nor the verdicts nor the outcome. Elements and angles exactly as
tools/prod_eval.py (prod-eval-v1) forms them: its functions dump, snapshots and frame_elements are imported unchanged.

  python -I tools/sets_decompose.py RUN --p9sim P9SIM --wall AU --out DIR --name A|B

RUN is the job directory (jobs/BB-A), with input.sa (t = 0) and segments/segNNN/output.sa.
Writes into DIR:
  export-<name>.npz     h) 32 snapshots (t = 0 and 1.0, 1.1, ..., 4.0 Gyr), all test particles present (float32)
  preview-f.csv         f) R per 10 au beyond the wall for particles whose q was never below X up to that snapshot
  bins.csv              a) and c): per 10-au bin and selection: n, R, direction, second harmonic, 10-deg histogram
  qi.csv                b) q and i distributions in S_BB beyond the wall, pooled over 1-4 Gyr
  libration.csv         d) classes per particle and R per bin per class
  survival.csv          e) per snapshot of the window: particles in S_BB beyond the wall, share of all
  images.npz            g) density a x dvarpi (2 au x 1 deg, 100-1000 au, normalised per a column) for six selections
  summary.json          the means beyond the wall and the verdicts of the scales fixed in the addendum
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prod_eval import dump, elements, frame_elements, snapshots  # noqa: E402

S_BB = (150.0, 1000.0, 42.0)
WINDOW = (1e9, 4e9)
A_MAX = 700.0
X_LIST = (4.5, 10.0, 20.0, 30.0)
SCALE_HI, SCALE_LO = 0.4, 0.2


def rlen(deg, k=1):
    x = np.radians(deg) * k
    if len(x) == 0:
        return math.nan, math.nan
    C, S = np.cos(x).mean(), np.sin(x).mean()
    return math.hypot(C, S), math.degrees(math.atan2(S, C)) % 360


def verdict(m, hi_word, lo_word):
    if m is None or math.isnan(m):
        return "no bins"
    return hi_word if m >= SCALE_HI else lo_word if m <= SCALE_LO else "unclear"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--wall", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True)
    args = ap.parse_args()
    run, out = Path(args.run), Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    wall = args.wall

    # all snapshots from t = 0: input.sa, then every output snapshot
    snaps = [(0.0, lambda: dump(args.p9sim, run / "input.sa", 0))] + snapshots(run, args.p9sim)
    export_t = [0.0] + [1e9 + k * 1e8 for k in range(31)]  # t = 0 and 1.0, 1.1, ..., 4.0 Gyr
    T, EL = [], []
    exp_rows = {k: [] for k in ("t", "idx", "a", "e", "inc", "Omega", "omega")}
    exp_meta = {k: [] for k in ("t", "p9_a", "p9_e", "p9_inc", "p9_Omega", "p9_varpi", "jup_a", "jup_e", "plane_inc", "plane_node")}
    n_tp0 = None
    for t, load in snaps:
        snap = load()
        el = frame_elements(*snap)
        if n_tp0 is None:
            n_tp0 = len(el["idx"])
        T.append(t)
        EL.append({k: el[k] for k in ("idx", "a", "q", "dvarpi", "inc")})
        if any(abs(t - te) < 1.0 for te in export_t):
            # e, Omega, omega from the same values as prod_eval.py (no new conversion of the states)
            e = 1.0 - el["q"] / el["a"]
            Om = (el["dOmega"] + el["p9"]["Omega"]) % 360
            vp = (el["dvarpi"] + el["p9"]["varpi"]) % 360
            n = len(el["idx"])
            exp_rows["t"].append(np.full(n, t / 1e9)); exp_rows["idx"].append(el["idx"]); exp_rows["a"].append(el["a"])
            exp_rows["e"].append(e); exp_rows["inc"].append(el["inc"]); exp_rows["Omega"].append(Om); exp_rows["omega"].append((vp - Om) % 360)
            # Jupiter in the same frame as prod_eval (barycentric, its own plane: inc 0); a and e only
            tt, names, m, r, v = snap
            massive = m > 0
            M = m[massive].sum()
            R0 = (m[massive, None] * r[massive]).sum(0) / M; V0 = (m[massive, None] * v[massive]).sum(0) / M
            j = int(np.flatnonzero(names == "Jupiter")[0])
            G = (0.01720209895 * 365.25) ** 2
            ja, je, *_ = (x[0] for x in elements(G * M, (r[j:j + 1] - R0), (v[j:j + 1] - V0)))
            for k, val in (("t", t / 1e9), ("p9_a", el["p9"]["a"]), ("p9_e", el["p9"]["e"]), ("p9_inc", el["p9"]["inc"]),
                           ("p9_Omega", el["p9"]["Omega"]), ("p9_varpi", el["p9"]["varpi"]), ("jup_a", ja), ("jup_e", je),
                           ("plane_inc", el["plane_deg"][0]), ("plane_node", el["plane_deg"][1])):
                exp_meta[k].append(val)
    T = np.array(T)
    np.savez_compressed(out / f"export-{args.name}.npz",
                        **{k: (np.concatenate(v).astype(np.int32) if k == "idx" else np.concatenate(v).astype(np.float32)) for k, v in exp_rows.items()},
                        **{f"snap_{k}": np.array(v, dtype=np.float32) for k, v in exp_meta.items()})

    # running minimum of q per particle since t = 0, at every snapshot
    qmin = np.full(max(int(el["idx"].max()) for el in EL) + 1, math.inf)
    QMIN = []
    for el in EL:
        cur = np.minimum(qmin[el["idx"]], el["q"])
        qmin[el["idx"]] = cur
        QMIN.append(cur)

    win = [k for k, t in enumerate(T) if WINDOW[0] - 1 <= t <= WINDOW[1] + 1]
    last_ids = set(EL[-1]["idx"].tolist())
    # pooled particle-snapshots of the window, S_BB
    P = {k: [] for k in ("idx", "a", "q", "inc", "dvarpi", "qmin", "t")}
    for k in win:
        el = EL[k]
        s = (el["a"] > S_BB[0]) & (el["a"] < S_BB[1]) & (el["q"] > S_BB[2])
        for key in ("idx", "a", "q", "inc", "dvarpi"):
            P[key].append(el[key][s])
        P["qmin"].append(QMIN[k][s]); P["t"].append(np.full(s.sum(), T[k]))
    P = {k: np.concatenate(v) for k, v in P.items()}
    surv = np.isin(P["idx"], list(last_ids))
    edges = np.arange(150.0, A_MAX + 1e-9, 10.0)
    beyond_lo = [lo for lo in edges[:-1] if lo >= wall]

    def bins(mask):
        rows = []
        for lo in edges[:-1]:
            s = mask & (P["a"] >= lo) & (P["a"] < lo + 10)
            n = int(s.sum())
            R, d = rlen(P["dvarpi"][s]) if n >= 10 else (math.nan, math.nan)
            R2, _ = rlen(P["dvarpi"][s], 2) if n >= 10 else (math.nan, math.nan)
            hist = np.histogram(P["dvarpi"][s], bins=36, range=(0, 360))[0] if n else np.zeros(36, int)
            rows.append((lo + 5, n, R, d, R2, hist))
        return rows

    def mean_beyond(rows, lo_min=None):
        v = [r[2] for r in rows if r[0] - 5 >= (wall if lo_min is None else lo_min) and not math.isnan(r[2])]
        return (float(np.mean(v)) if v else math.nan), len(v)

    q, inc = P["q"], P["inc"]
    sel = {
        "S_BB": np.ones(len(q), bool),
        "q42-60": q < 60,
        "q42-100": q < 100,
        "i<30": inc < 30,
        "q42-100_i<30": (q < 100) & (inc < 30),
        "survivors_4Gyr": surv,
    }
    for X in X_LIST:
        sel[f"qmin>={X:g}"] = P["qmin"] >= X
    B = {name: bins(m) for name, m in sel.items()}
    with open(out / "bins.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["selection", "a_mid_au", "n", "R", "dir_deg", "R2"] + [f"h{10 * k}" for k in range(36)])
        for name, rows in B.items():
            for a_mid, n, R, d, R2, h in rows:
                w.writerow([name, f"{a_mid:.0f}", n, f"{R:.4f}", f"{d:.1f}", f"{R2:.4f}"] + list(map(int, h)))
    with open(out / "preview-f.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["X_au", "a_mid_au", "n", "R"])
        for X in X_LIST:
            for a_mid, n, R, *_ in B[f"qmin>={X:g}"]:
                if a_mid - 5 >= wall:
                    w.writerow([X, f"{a_mid:.0f}", n, f"{R:.4f}"])

    # b) q and i beyond the wall
    bw = (P["a"] >= wall) & (P["a"] < A_MAX)
    qh = np.histogram(q[bw], bins=[42, 50, 60, 70, 80, 100, 150, 200, 300, 500, 1000])[0]
    ih = np.histogram(inc[bw], bins=np.arange(0, 185, 5))[0]
    with open(out / "qi.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "lo", "hi", "n"])
        for lo, hi, n in zip([42, 50, 60, 70, 80, 100, 150, 200, 300, 500], [50, 60, 70, 80, 100, 150, 200, 300, 500, 1000], qh):
            w.writerow(["q", lo, hi, int(n)])
        for lo, n in zip(range(0, 180, 5), ih):
            w.writerow(["i", lo, lo + 5, int(n)])
    nbw = int(bw.sum())
    qi = {"n_beyond_wall": nbw, "share_i_lt_30": float((inc[bw] < 30).mean()) if nbw else None,
          "share_i_gt_50": float((inc[bw] > 50).mean()) if nbw else None, "share_q_lt_60": float((q[bw] < 60).mean()) if nbw else None,
          "share_q_lt_100": float((q[bw] < 100).mean()) if nbw else None, "median_q": float(np.median(q[bw])) if nbw else None,
          "median_i": float(np.median(inc[bw])) if nbw else None}

    # d) libration / circulation, per particle over its snapshots in S_BB beyond the wall
    ids = P["idx"][bw]; dv = P["dvarpi"][bw]
    order = np.argsort(ids, kind="stable"); ids, dv = ids[order], dv[order]
    cls = {}
    if len(ids):
        cuts = np.flatnonzero(np.diff(ids)) + 1
        for g_ids, g_dv in zip(np.split(ids, cuts), np.split(dv, cuts)):
            if len(g_dv) < 20:
                continue
            quad = set((g_dv // 90).astype(int).tolist())
            cls[int(g_ids[0])] = "librating" if np.all((g_dv > 90) & (g_dv < 270)) else "circulating" if len(quad) == 4 else "mixed"
    counts = {c: sum(1 for v in cls.values() if v == c) for c in ("librating", "circulating", "mixed")}
    with open(out / "libration.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["class", "particles", "a_mid_au", "n", "R"])
        for c in ("librating", "circulating", "mixed"):
            members = [i for i, v in cls.items() if v == c]
            rows = bins(np.isin(P["idx"], members))
            for a_mid, n, R, *_ in rows:
                if a_mid - 5 >= wall:
                    w.writerow([c, counts[c], f"{a_mid:.0f}", n, f"{R:.4f}"])

    # e) survival
    with open(out / "survival.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_gyr", "n_alive", "share_alive", "n_SBB_beyond_wall", "rel_to_1Gyr"])
        base = None
        for k in win:
            el = EL[k]
            s = (el["a"] >= wall) & (el["a"] < A_MAX) & (el["q"] > S_BB[2])
            n = int(s.sum()); base = base or n
            w.writerow([f"{T[k] / 1e9:.2f}", len(el["idx"]), f"{len(el['idx']) / n_tp0:.4f}", n, f"{n / base:.4f}"])

    # g) images, 2 au x 1 deg, normalised per a column
    img_sel = {"1_S_BB": sel["S_BB"], "2_q42-60": q < 60, "3_q60-100": (q >= 60) & (q < 100), "4_q>100": q >= 100,
               "5_i<30": inc < 30, "6_i>30": inc >= 30}
    images = {}
    for name, m in img_sel.items():
        H = np.histogram2d(P["dvarpi"][m], P["a"][m], bins=[360, 450], range=[[0, 360], [100, 1000]])[0]
        col = H.sum(0)
        images[name] = np.where(col > 0, H / np.where(col > 0, col, 1), np.nan).astype(np.float32)
        images[name + "_n"] = col.astype(np.int64)
    np.savez_compressed(out / "images.npz", **images)

    summary = {"name": args.name, "wall_au": wall, "beyond_wall_bins": f"{beyond_lo[0]:.0f}-{A_MAX:.0f} au" if beyond_lo else None,
               "window_yr": WINDOW, "snapshots_total": len(T), "snapshots_window": len(win), "n_tp_start": n_tp0,
               "particle_snapshots_SBB_window": int(len(q)), "qi_beyond_wall": qi, "libration_counts": counts, "means_beyond_wall": {}}
    for name, rows in B.items():
        mval, nb = mean_beyond(rows)
        m270, _ = mean_beyond(rows, 270.0)
        inside = [r[2] for r in rows if 150 <= r[0] - 5 < 230 and not math.isnan(r[2])]
        summary["means_beyond_wall"][name] = {"mean_R": mval, "bins": nb, "mean_R_270_700": m270,
                                              "mean_R_150_230": float(np.mean(inside)) if inside else None,
                                              "particle_snapshots_beyond": int(sum(r[1] for r in rows if r[0] - 5 >= wall))}
    summary["scale_c_core"] = verdict(summary["means_beyond_wall"]["q42-100_i<30"]["mean_R"], "core present", "no core")
    summary["scale_f"] = {f"{X:g}": verdict(summary["means_beyond_wall"][f"qmin>={X:g}"]["mean_R"], "explains", "does not explain") for X in X_LIST}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: summary[k] for k in ("name", "scale_c_core", "scale_f", "libration_counts")}))


if __name__ == "__main__":
    main()
