#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The evaluation of the equivalence test, exactly as docs/equivalence-criteria.md (accepted 2026-10-22, margin
0.035, with the clarification of 2026-10-23). Committed before the evaluation; not changed afterwards.

  build/venv/bin/python -I tools/equiv_eval.py --wh WH_DIR --v5 V5_DIR --m M_DIR [--p9sim build/gcc-O3/p9sim] [--json OUT]

  WH_DIR  medas-p9-search-bb2021/runs/equiv/wh: chains s101 ... s109 of p9job segments (seg00 ... seg09, job.json,
          output.sa, result.json)
  V5_DIR  the unpacked package p9equiv-v5-47c7381 with its results: jobs/V5-s101 ... /segments/seg000 ... seg009
  M_DIR   the unpacked package p9equiv-merc-47c7381 with its results: jobs/M-s101-part00 ... M-s109-part15/segments/...

It refuses to evaluate unless all 9 seeds of all three groups are complete (every segment done): no interim look.

Per run (group, seed) S = the mean over 160, 165, ..., 200 Myr of R(dvarpi) of the distant survivors (a > 230 au,
q > 42 au); barycentric elements; dvarpi = varpi minus that of the Planet Nine of the same simulation at the same
snapshot. For M the 16 slices of a seed are pooled at each time before R is computed. Per seed d_s = S(V5) - S(M),
e_s = S(WH) - S(M); for each comparison the mean of the 9 differences and its two-sided 95 % interval (t, 8 degrees
of freedom): "equivalent" if the interval lies inside (-0.035, +0.035), "different" if entirely outside, else "not
shown". For information only (no decision): the same for R at 200 Myr and for S with the cut of the observed sample
(150 < a < 1,000 au, q > 42 au).
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import barycentric, dump, elements  # noqa: E402

SEEDS = list(range(101, 110))
PARTS = 16
TIMES = [1.6e8 + 5e6 * k for k in range(9)]
MARGIN = 0.035
CUT_MAIN = (230.0, math.inf, 42.0)    # a_min, a_max, q_min
CUT_OBS = (150.0, 1000.0, 42.0)


# --- the statistics, self-contained ---------------------------------------------------------------------------------

def R(dvarpi_deg):
    """Mean resultant length of the angles (degrees)."""
    a = np.radians(np.asarray(dvarpi_deg, float))
    return math.hypot(np.cos(a).mean(), np.sin(a).mean()) if len(a) else float("nan")


def _betacf(a, b, x):
    tiny, qab, qap, qam = 1e-300, a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        for aa in (m * (b - m) * x / ((qam + m2) * (a + m2)), -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))):
            d = 1 + aa * d
            d = 1 / (d if abs(d) > tiny else tiny)
            c = 1 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1) < 1e-15:
            break
    return h


def t_sf(t, df):
    """P(T > t), Student's t."""
    x = df / (df + t * t)
    a, b = df / 2, 0.5
    lb = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x) if 0 < x < 1 else None
    if lb is None:
        ib = 0.0 if x <= 0 else 1.0
    elif x < (a + 1) / (a + b + 2):
        ib = math.exp(lb) * _betacf(a, b, x) / a
    else:
        ib = 1 - math.exp(lb) * _betacf(b, a, 1 - x) / b
    p = 0.5 * ib
    return p if t >= 0 else 1 - p


def t_ppf(q, df):
    lo, hi = -1e3, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if 1 - t_sf(mid, df) < q else (lo, mid)
    return (lo + hi) / 2


def paired(diffs, margin=MARGIN):
    """Mean of the paired differences, its two-sided 95 % interval (t, n - 1), and the verdict."""
    d = np.asarray(diffs, float)
    n = len(d)
    m, sd = float(d.mean()), float(d.std(ddof=1))
    h = t_ppf(0.975, n - 1) * sd / math.sqrt(n)
    lo, hi = m - h, m + h
    verdict = "equivalent" if (lo > -margin and hi < margin) else "different" if (hi < -margin or lo > margin) else "not shown"
    return {"n": n, "mean": m, "sd": sd, "ci95": [lo, hi], "verdict": verdict}


# --- the data -------------------------------------------------------------------------------------------------------

def chain_file(d, T):
    """(output.sa, snapshot index) at time T in a p9job chain (seg* with job.json, output.sa, result.json)."""
    for seg in sorted(Path(d).glob("seg*")):
        p = json.loads((seg / "job.json").read_text())["params"]
        t0, t1, n = float(p["t_start_yr"]), float(p["t_end_yr"]), int(p["snapshots"])
        if t0 < T <= t1:
            x = (T - t0) / ((t1 - t0) / n)
            if abs(x - round(x)) > 1e-9:
                raise SystemExit(f"{seg}: no snapshot at {T:g}")
            if not (seg / "result.json").exists():
                raise SystemExit(f"{seg}: not done")
            return seg / "output.sa", round(x) - 1
    raise SystemExit(f"{d}: no segment contains {T:g}")


def package_file(job, T):
    """(output.sa, snapshot index) at time T in a package job (params.env, segments/segNNN with DONE)."""
    env = dict(l.split("=", 1) for l in (Path(job) / "params.env").read_text().splitlines() if "=" in l and not l.startswith("#"))
    seg_yr, per, nseg = float(env["SEGMENT_YR"]), int(env["SNAPSHOTS_PER_SEGMENT"]), int(env["SEGMENTS"])
    k = math.ceil(T / seg_yr - 1e-12) - 1
    x = (T - k * seg_yr) / (seg_yr / per)
    if not 0 <= k < nseg or abs(x - round(x)) > 1e-9:
        raise SystemExit(f"{job}: no snapshot at {T:g}")
    seg = Path(job) / "segments" / f"seg{k:03d}"
    if not (seg / "DONE").exists():
        raise SystemExit(f"{seg}: not done")
    return seg / "output.sa", round(x) - 1


def elements_of(files, p9sim):
    """Pooled a, q, dvarpi (deg) of the test particles of the given snapshots; each file's dvarpi against its own
    Planet Nine. Checks that no particle appears twice."""
    A, Q, DV, ids = [], [], [], []
    for sa, idx in files:
        _, rows = dump(p9sim, sa, idx)
        rows, mu = barycentric(rows)
        p9 = [(r, v) for name, m, r, v in rows if name == "P9"]
        tps = [(int(name[2:]), r, v) for name, m, r, v in rows if name.startswith("tp")]
        if len(p9) != 1:
            raise SystemExit(f"{sa}: {len(p9)} Planet Nines")
        _, _, _, _, vpP = elements(mu, p9[0][0][None, :], p9[0][1][None, :])
        if tps:
            a, e, _, _, vp = elements(mu, np.array([x[1] for x in tps]), np.array([x[2] for x in tps]))
            A.append(a); Q.append(a * (1 - e)); DV.append((vp - vpP[0]) % 360); ids += [x[0] for x in tps]
    if len(set(ids)) != len(ids):
        raise SystemExit("a test particle appears twice when pooling")
    cat = (lambda xs: np.concatenate(xs) if xs else np.array([]))
    return cat(A), cat(Q), cat(DV), len(ids)


def r_cut(a, q, dv, cut):
    amin, amax, qmin = cut
    sel = (a > amin) & (a < amax) & (q > qmin)
    return R(dv[sel]), int(sel.sum())


def run_stats(file_sets, p9sim):
    """file_sets: {T: [(output.sa, index), ...]} of one run -> S, S with the observed cut, R at 200 Myr, counts."""
    rs, ro, n = {}, {}, {}
    for T in TIMES:
        a, q, dv, ntot = elements_of(file_sets[T], p9sim)
        rs[T], n[T] = r_cut(a, q, dv, CUT_MAIN)
        ro[T], _ = r_cut(a, q, dv, CUT_OBS)
    return {"S": float(np.mean([rs[T] for T in TIMES])), "S_obs_cut": float(np.mean([ro[T] for T in TIMES])),
            "R200": float(rs[TIMES[-1]]), "n_distant_200": n[TIMES[-1]]}


def files_wh(root, seed):
    return {T: [chain_file(Path(root) / f"s{seed}", T)] for T in TIMES}


def files_v5(root, seed):
    return {T: [package_file(Path(root) / "jobs" / f"V5-s{seed}", T)] for T in TIMES}


def files_m(root, seed, parts=PARTS):
    return {T: [package_file(Path(root) / "jobs" / f"M-s{seed}-part{k:02d}", T) for k in range(parts)] for T in TIMES}


def complete(wh, v5, m):
    """All segments of all runs done (raises SystemExit otherwise)."""
    for s in SEEDS:
        for T in (TIMES[0], TIMES[-1]):
            files_wh(wh, s); files_v5(v5, s); files_m(m, s)
        for seg in sorted((Path(wh) / f"s{s}").glob("seg*")):
            if not (seg / "result.json").exists():
                raise SystemExit(f"{seg}: not done")
        for job in [Path(v5) / "jobs" / f"V5-s{s}"] + [Path(m) / "jobs" / f"M-s{s}-part{k:02d}" for k in range(PARTS)]:
            env = dict(l.split("=", 1) for l in (job / "params.env").read_text().splitlines() if "=" in l and not l.startswith("#"))
            for k in range(int(env["SEGMENTS"])):
                if not (job / "segments" / f"seg{k:03d}" / "DONE").exists():
                    raise SystemExit(f"{job}: segment {k} not done")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wh", required=True)
    ap.add_argument("--v5", required=True)
    ap.add_argument("--m", required=True)
    ap.add_argument("--p9sim", default="build/gcc-O3/p9sim")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    complete(a.wh, a.v5, a.m)
    runs = {}
    for s in SEEDS:
        runs[s] = {"WH": run_stats(files_wh(a.wh, s), a.p9sim), "V5": run_stats(files_v5(a.v5, s), a.p9sim),
                   "M": run_stats(files_m(a.m, s), a.p9sim)}
        print(f"seed {s}: S  V5 {runs[s]['V5']['S']:.4f}  WH {runs[s]['WH']['S']:.4f}  M {runs[s]['M']['S']:.4f}", flush=True)
    out = {"criteria": "docs/equivalence-criteria.md (accepted 2026-10-22, clarification 2026-10-23)", "margin": MARGIN, "runs": runs}
    for key, label in (("S", "decision"), ("R200", "information"), ("S_obs_cut", "information")):
        out[key] = {"(1) V5 - M": paired([runs[s]["V5"][key] - runs[s]["M"][key] for s in SEEDS]),
                    "(2) WH - M": paired([runs[s]["WH"][key] - runs[s]["M"][key] for s in SEEDS])}
        print(f"\n{key} ({label}):")
        for comp, r in out[key].items():
            print(f"  {comp}: mean {r['mean']:+.4f}, 95 % [{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}] -> {r['verdict']}")
    print(f"\nproduction run, method side (criteria: decided by (1) on S): {out['S']['(1) V5 - M']['verdict']}")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
