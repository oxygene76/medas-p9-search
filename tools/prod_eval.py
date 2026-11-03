#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Evaluation of the production run (docs/production-criteria.md section 4) and of the comparison runs with Brown &
Batygin 2021 (docs/bb2021-comparison-criteria.md sections 4 and 5; prerequisite V3).

  python tools/prod_eval.py RUN --out DIR [--p9sim PATH] [--criteria production|bb2021-A|bb2021-B]
                            [--window 1e9 4e9] [--n-tp 64000] [--subsets 4] [--observed FILE]
  python tools/prod_eval.py --outcome A/result.json B/result.json      (section 6: the outcome of sets A and B)

RUN: a package run (params.env and segments/segNNN/output.sa with DONE, read with `p9sim dump`) or a directory of
snapshot files snap-*.npz (arrays t, names, m, r, v; the synthetic tests). Writes DIR/result.json,
DIR/timeseries.csv (per snapshot, information) and DIR/report.txt.

Elements (varpi = Omega + omega): barycentric osculating elements of the test particles and Planet Nine (mu = G M_total of the massive
bodies), in the frame of Jupiter's orbital plane at each snapshot: z along Jupiter's heliocentric orbital angular
momentum, angles inc against that plane, and the longitudes Omega and varpi as dog-leg longitudes, from the
x axis of the run (the equinox of the ecliptic J2000) along the ecliptic to the ascending node N of Jupiter's plane,
then along that plane. So the longitude zero point of the start frame is kept (Brown & Batygin 2021, §4.1, p. 8),
and the longitudes differ from ecliptic ones only by terms of the order of Jupiter's inclination squared. Reported
as variants, not judged: the same in the ecliptic frame, and heliocentric elements (mu = G (M_Sun + m)) in
Jupiter's frame.

Measures (docs/bb2021-comparison-criteria.md section 4), selection S_BB: 150 < a < 1000 au, q > 42 au; window: the
snapshots with t in [window] (default 1-4 Gyr):
  M1  circular mean of dvarpi = varpi - varpi9 over S_BB, pooled over the window
  M2  mean over the snapshots of the window of R, the mean resultant length of dvarpi in S_BB
  M3  angle psi of the pooled mean of (sin i cos dOmega, sin i sin dOmega), dOmega = Omega - Omega9
  M4  wall: R of dvarpi pooled over the window in a bins of 10 au from 150 to 700 au; R_plat = median R of the bins
      400-700 au; the smallest bin centre up to 600 au from which R >= R_plat / 2 holds for it and the next 3 bins
  M5  width: the dvarpi interval at 850 < a < 950 au where the pooled density (1-deg bins, circular 10-deg moving
      average) is above half its maximum (reported only)
Subsets (docs/production-criteria.md section 5, decision P1 of 2026-11-03): the test particles in --subsets equal
blocks of their index (0..n_tp/4-1, ...); M1 of each subset over the window; the scatter is the largest angular
distance of a subset's M1 from the pooled M1; more than 10 deg: "not decided"; a deviating subset is reported, never
excluded.
"""

import argparse
import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

G = (0.01720209895 * 365.25) ** 2
S_BB = (150.0, 1000.0, 42.0)
SCATTER_LIMIT_DEG = 10.0
SELECTIONS = {"S1": (250.0, math.inf, -math.inf), "S2": (250.0, math.inf, 30.0), "S3": (230.0, math.inf, 30.0)}
# docs/bb2021-comparison-criteria.md section 5
TOLERANCE = {"M1": (160.0, 200.0), "M2_min": 0.20, "M3_abs": 30.0, "M4_A": (226.0, 286.0)}


# --- reading ---------------------------------------------------------------------------------------------------------

def dump(p9sim, sa, idx):
    out = subprocess.run([p9sim, "dump", str(sa), str(idx)], capture_output=True, text=True, check=True).stdout
    t, names, m, r, v = None, [], [], [], []
    for line in out.splitlines():
        f = line.split()
        if not f or f[0].startswith("Warning"):
            continue
        if f[0] == "t":
            t = float(f[1])
            continue
        vals = list(map(float, f[1:]))
        names.append(f[0]); m.append(vals[-7]); r.append(vals[-6:-3]); v.append(vals[-3:])
    return t, np.array(names), np.array(m), np.array(r), np.array(v)


def snapshots(run, p9sim):
    """[(t, loader)] of a run, in time order."""
    run = Path(run)
    npz = sorted(run.glob("snap-*.npz"))
    if npz:
        def load(p):
            z = np.load(p, allow_pickle=False)
            return float(z["t"]), z["names"], z["m"], z["r"], z["v"]
        out = []
        for p in npz:
            out.append((float(np.load(p, allow_pickle=False)["t"]), (lambda p=p: load(p))))
        return sorted(out, key=lambda x: x[0])
    env = dict(l.split("=", 1) for l in (run / "params.env").read_text().splitlines() if "=" in l and not l.startswith("#"))
    seg_yr, per, nseg = float(env["SEGMENT_YR"]), int(env["SNAPSHOTS_PER_SEGMENT"]), int(env["SEGMENTS"])
    if not p9sim:
        sys.exit("--p9sim is needed to read output.sa")
    out = []
    for k in range(nseg):
        seg = run / "segments" / f"seg{k:03d}"
        if not (seg / "DONE").exists():
            break
        for i in range(per):
            out.append((k * seg_yr + (i + 1) * seg_yr / per, (lambda sa=seg / "output.sa", i=i: dump(p9sim, sa, i))))
    return out


# --- geometry --------------------------------------------------------------------------------------------------------

def rot_from_plane(I, N):
    """Rz(N) Rx(I): from the frame of a plane (x to its ascending node, z to its pole) to the run's frame."""
    cI, sI, cN, sN = math.cos(I), math.sin(I), math.cos(N), math.sin(N)
    return np.array([[cN, -sN * cI, sN * sI], [sN, cN * cI, -cN * sI], [0.0, sI, cI]])


def plane_of(h):
    n = h / np.linalg.norm(h)
    return math.acos(max(-1.0, min(1.0, n[2]))), math.atan2(n[0], -n[1])


def elements(mu, r, v):
    """a, e, inc (deg), Omega (deg), varpi (deg) of states in the frame of r and v; mu scalar or per body."""
    mu = np.broadcast_to(np.asarray(mu, float), r.shape[:1])
    rr = np.linalg.norm(r, axis=-1)
    h = np.cross(r, v)
    hn = np.linalg.norm(h, axis=-1)
    a = 1 / (2 / rr - (v * v).sum(-1) / mu)
    evec = np.cross(v, h) / mu[:, None] - r / rr[:, None]
    e = np.linalg.norm(evec, axis=-1)
    inc = np.degrees(np.arccos(np.clip(h[:, 2] / hn, -1, 1)))
    Omega = np.degrees(np.arctan2(h[:, 0], -h[:, 1])) % 360
    # varpi = Omega + omega (the standard definition; tools/analyze.py uses the direction of the projected
    # eccentricity vector instead, which differs by up to about 1 deg at 16 deg inclination)
    node = np.stack([-h[:, 1], h[:, 0], np.zeros(len(h))], -1)
    omega = np.degrees(np.arctan2((np.cross(node, evec) * h).sum(-1) / hn, (node * evec).sum(-1)))
    varpi = (Omega + omega) % 360
    return a, e, inc, Omega, varpi


def frame_elements(t, names, m, r, v, frame="jupiter", centre="barycentric"):
    """Per snapshot: test-particle index, a, q, dvarpi, inc, dOmega in the given frame, and Planet Nine's elements."""
    massive = m > 0
    M = m[massive].sum()
    sun = np.flatnonzero(names == "Sun")
    jup = np.flatnonzero(names == "Jupiter")
    p9 = np.flatnonzero(names == "P9")
    if len(sun) != 1 or len(jup) != 1 or len(p9) != 1:
        raise SystemExit(f"t={t}: need exactly one Sun, Jupiter and P9")
    sun, jup, p9 = sun[0], jup[0], p9[0]
    if centre == "barycentric":
        R0 = (m[massive, None] * r[massive]).sum(0) / M
        V0 = (m[massive, None] * v[massive]).sum(0) / M
        mu_tp = mu_p9 = G * M
    else:
        R0, V0 = r[sun], v[sun]
        mu_tp, mu_p9 = G * m[sun], G * (m[sun] + m[p9])
    rr, vv = r - R0, v - V0
    if frame == "jupiter":
        I, N = plane_of(np.cross(r[jup] - r[sun], v[jup] - v[sun]))
        Rm = rot_from_plane(I, N)
        rr, vv = rr @ Rm, vv @ Rm          # coordinates in the plane's frame (row vectors: x' = R^T x)
        shift = math.degrees(N)            # dog-leg longitudes
    else:
        I = N = shift = 0.0
    tp = np.char.startswith(names.astype(str), "tp")
    idx = np.array([int(n[2:]) for n in names[tp]])
    a, e, inc, Om, vp = elements(mu_tp, rr[tp], vv[tp])
    a9, e9, i9, Om9, vp9 = (x[0] for x in elements(mu_p9, rr[p9:p9 + 1], vv[p9:p9 + 1]))
    Om, vp, Om9, vp9 = (Om + shift) % 360, (vp + shift) % 360, (Om9 + shift) % 360, (vp9 + shift) % 360
    return {"idx": idx, "a": a, "q": a * (1 - e), "dvarpi": (vp - vp9) % 360, "inc": inc, "dOmega": (Om - Om9) % 360,
            "p9": {"a": a9, "e": e9, "inc": i9, "Omega": Om9, "varpi": vp9}, "plane_deg": (math.degrees(I), math.degrees(N) % 360)}


# --- statistics -------------------------------------------------------------------------------------------------------

def circ_mean(deg):
    x = np.radians(np.asarray(deg))
    if len(x) == 0:
        return None, 0.0
    C, S = np.cos(x).mean(), np.sin(x).mean()
    return math.degrees(math.atan2(S, C)) % 360, math.hypot(C, S)


def angdist(x, y):
    return abs((x - y + 180) % 360 - 180)


def select(el, cut):
    amin, amax, qmin = cut
    return (el["a"] > amin) & (el["a"] < amax) & (el["q"] > qmin)


def wall(a, dv):
    edges = np.arange(150.0, 700.0 + 1e-9, 10.0)
    centres = edges[:-1] + 5
    R = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        s = (a >= lo) & (a < hi)
        R.append(circ_mean(dv[s])[1] if s.sum() >= 10 else math.nan)
    R = np.array(R)
    plat = R[(centres > 400) & (centres < 700)]
    plat = plat[~np.isnan(plat)]
    if len(plat) == 0:
        return None, None, centres, R
    R_plat = float(np.median(plat))
    for k, c in enumerate(centres):
        if c > 600:
            break
        nxt = R[k:k + 4]
        if len(nxt) == 4 and np.all(nxt >= R_plat / 2):
            return float(c), R_plat, centres, R
    return None, R_plat, centres, R


def width(dv, smooth_deg=10):
    if len(dv) < 50:
        return None
    h = np.bincount(np.floor(np.asarray(dv) % 360).astype(int), minlength=360).astype(float)
    k = np.ones(smooth_deg) / smooth_deg
    hs = np.real(np.fft.ifft(np.fft.fft(h) * np.fft.fft(np.roll(np.pad(k, (0, 360 - smooth_deg)), -(smooth_deg // 2)))))
    top = int(np.argmax(hs))
    half = hs[top] / 2
    lo = hi = 0
    while lo < 359 and hs[(top - lo - 1) % 360] > half:
        lo += 1
    while hi < 359 and hs[(top + hi + 1) % 360] > half:
        hi += 1
    if lo + hi + 1 >= 360:
        return {"width_deg": 360, "from_deg": None, "to_deg": None, "n": len(dv)}
    return {"width_deg": lo + hi + 1, "from_deg": (top - lo) % 360 + 0.5, "to_deg": (top + hi) % 360 + 0.5, "n": len(dv)}


# --- evaluation ------------------------------------------------------------------------------------------------------

def evaluate(run, p9sim=None, window=(1e9, 4e9), n_tp=64000, subsets=4, criteria="production", observed=None, t_end=4e9):
    snaps = snapshots(run, p9sim)
    if not snaps:
        raise SystemExit(f"{run}: no snapshots")
    pooled = {v: {k: [] for k in ("idx", "a", "dvarpi", "inc", "dOmega")} for v in ("main", "ecliptic", "heliocentric")}
    R_snap, series = [], []
    block = n_tp // subsets
    for t, load in snaps:
        snap = load()
        el = frame_elements(*snap)
        s_bb = select(el, S_BB)
        m1_t, r_t = circ_mean(el["dvarpi"][s_bb])
        si = np.radians(el["inc"][s_bb]); do = np.radians(el["dOmega"][s_bb])
        psi_t = math.degrees(math.atan2(np.sum(np.sin(si) * np.sin(do)), np.sum(np.sin(si) * np.cos(do)))) if s_bb.any() else None
        row = {"t_yr": t, "n_tp": int(len(el["idx"])), "n_SBB": int(s_bb.sum()), "M1_deg": m1_t, "R": r_t, "psi_deg": psi_t,
               "jupiter_inc_deg": el["plane_deg"][0], "jupiter_node_deg": el["plane_deg"][1], "p9_varpi_deg": el["p9"]["varpi"]}
        for name, cut in SELECTIONS.items():
            mm, rr = circ_mean(el["dvarpi"][select(el, cut)])
            row[f"{name}_n"], row[f"{name}_R"], row[f"{name}_M1_deg"] = int(select(el, cut).sum()), rr, mm
        series.append(row)
        if not (window[0] - 1 <= t <= window[1] + 1):
            continue
        R_snap.append(r_t)
        for variant, kw in (("main", {}), ("ecliptic", {"frame": "ecliptic"}), ("heliocentric", {"centre": "heliocentric"})):
            ev = el if variant == "main" else frame_elements(*snap, **kw)
            s = select(ev, S_BB)
            for k in pooled[variant]:
                pooled[variant][k].append(ev[k][s] if k != "a" else ev["a"][s])
    times = [r["t_yr"] for r in series]
    in_window = [t for t in times if window[0] - 1 <= t <= window[1] + 1]
    P = {v: {k: (np.concatenate(x) if x else np.array([])) for k, x in d.items()} for v, d in pooled.items()}

    def measures(p, with_wall=True):
        m1, r_pool = circ_mean(p["dvarpi"])
        si, do = np.radians(p["inc"]), np.radians(p["dOmega"])
        psi = math.degrees(math.atan2(np.sum(np.sin(si) * np.sin(do)), np.sum(np.sin(si) * np.cos(do)))) if len(si) else None
        out = {"M1_deg": m1, "R_pooled": r_pool, "M3_psi_deg": psi, "n_pooled": int(len(p["dvarpi"]))}
        if with_wall:
            w, rp, centres, Rb = wall(p["a"], p["dvarpi"])
            far = (p["a"] > 850) & (p["a"] < 950)
            out.update({"M4_wall_au": w, "M4_R_plat": rp, "M4_bins": {f"{c:.0f}": (None if math.isnan(x) else round(float(x), 4)) for c, x in zip(centres, Rb)},
                        "M5": width(p["dvarpi"][far])})
        return out

    main = measures(P["main"])
    main["M2_mean_R"] = float(np.mean(R_snap)) if R_snap else None
    subs = []
    for k in range(subsets):
        s = (P["main"]["idx"] >= k * block) & (P["main"]["idx"] < (k + 1) * block)
        m1s, rs = circ_mean(P["main"]["dvarpi"][s])
        subs.append({"subset": k, "idx": [k * block, (k + 1) * block - 1], "n_pooled": int(s.sum()), "M1_deg": m1s, "R_pooled": rs,
                     "distance_to_pooled_M1_deg": angdist(m1s, main["M1_deg"]) if m1s is not None and main["M1_deg"] is not None else None})
    d = [x["distance_to_pooled_M1_deg"] for x in subs if x["distance_to_pooled_M1_deg"] is not None]
    scatter = max(d) if len(d) == subsets else None
    complete = bool(times) and times[-1] >= t_end - 1 and len(in_window) > 0
    result = {"run": str(run), "criteria": criteria, "window_yr": list(window), "snapshots": len(times), "snapshots_in_window": len(in_window),
              "last_snapshot_yr": times[-1] if times else None, "complete_to_yr": t_end, "complete": complete,
              "selection": "S_BB: 150 < a < 1000 au, q > 42 au", "frame": "Jupiter's orbital plane at each snapshot, dog-leg longitudes",
              "measures": main, "subsets": subs, "subset_scatter_deg": scatter, "scatter_limit_deg": SCATTER_LIMIT_DEG,
              "variants_not_judged": {"ecliptic": measures(P["ecliptic"], False), "heliocentric": measures(P["heliocentric"], False)},
              "survivors": {f"{r['t_yr']:.6g}": r["n_tp"] for r in series}}
    deviating = [x["subset"] for x in subs if x["distance_to_pooled_M1_deg"] is not None and x["distance_to_pooled_M1_deg"] > SCATTER_LIMIT_DEG]
    result["deviating_subsets_reported"] = deviating
    if not complete or scatter is None:
        verdict = "not decided (run not complete over the window)" if not complete else "not decided (a subset without particles)"
    elif scatter > SCATTER_LIMIT_DEG:
        verdict = f"not decided (subset scatter {scatter:.1f} deg > {SCATTER_LIMIT_DEG:g} deg)"
    elif criteria == "production":
        verdict = "decided (subset scatter within 10 deg); the measures are reported, not judged against Brown & Batygin values"
    else:
        verdict = judge_bb(main, subs, criteria)
    result["verdict"] = verdict
    if observed:
        result["observed"] = observed_positions(observed, P["main"])
    return result, series


def judge_bb(main, subs, criteria):
    """Section 5 of docs/bb2021-comparison-criteria.md: agrees if M1 (pooled and every subset), M2, M3 and for set A
    also M4 are within tolerance."""
    lo, hi = TOLERANCE["M1"]
    fails = []
    for name, m1 in [("pooled", main["M1_deg"])] + [(f"subset {s['subset']}", s["M1_deg"]) for s in subs]:
        if m1 is None or not lo <= m1 <= hi:
            fails.append(f"M1 {name} {m1 if m1 is None else round(m1, 1)} outside {lo:g}-{hi:g}")
    if main["M2_mean_R"] is None or main["M2_mean_R"] < TOLERANCE["M2_min"]:
        fails.append(f"M2 {main['M2_mean_R']} < {TOLERANCE['M2_min']}")
    psi = main["M3_psi_deg"]
    if psi is None or abs((psi + 180) % 360 - 180) > TOLERANCE["M3_abs"]:
        fails.append(f"M3 {psi} outside +-{TOLERANCE['M3_abs']:g}")
    if criteria == "bb2021-A":
        lo4, hi4 = TOLERANCE["M4_A"]
        if main["M4_wall_au"] is None or not lo4 <= main["M4_wall_au"] <= hi4:
            fails.append(f"M4 {main['M4_wall_au']} outside {lo4:g}-{hi4:g} au")
    return "agrees with Brown & Batygin" if not fails else "does not agree: " + "; ".join(fails)


def outcome(a, b):
    """Section 6: the outcome of sets A and B from their result.json."""
    ra, rb = (json.loads(Path(x).read_text()) for x in (a, b))
    if any(r["verdict"].startswith("not decided") for r in (ra, rb)):
        return "5. Not decided"
    agree = [r["verdict"] == "agrees with Brown & Batygin" for r in (ra, rb)]
    if all(agree):
        return "1. Agreement"
    wrong_dir = any(r["measures"]["M2_mean_R"] >= TOLERANCE["M2_min"] and not TOLERANCE["M1"][0] <= r["measures"]["M1_deg"] <= TOLERANCE["M1"][1]
                    for r in (ra, rb))
    no_cluster = any(r["measures"]["M2_mean_R"] < TOLERANCE["M2_min"] for r in (ra, rb))
    if no_cluster:
        return "4. No cluster (M2 below 0.20 in at least one set)"
    if wrong_dir:
        return "3. Cluster in the wrong direction"
    return "2. One set agrees" if any(agree) else "2/other: neither set agrees, see the verdicts"


def observed_positions(path, p):
    """Observed objects (TSV: name, a_au, q_au, dvarpi_deg): the share of the pooled S_BB particles with a within 20 % of
    the object's a whose dvarpi lies within 15 deg of the object's (density at its place, reported only)."""
    out = []
    for line in Path(path).read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, a, q, dv = line.split("\t")[:4]
        a, dv = float(a), float(dv)
        near_a = (p["a"] > 0.8 * a) & (p["a"] < 1.2 * a)
        share = float(np.mean(np.abs((p["dvarpi"][near_a] - dv + 180) % 360 - 180) <= 15)) if near_a.any() else None
        out.append({"name": name, "a_au": a, "q_au": float(q), "dvarpi_deg": dv, "n_near_a": int(near_a.sum()),
                    "share_within_15deg": share, "uniform_would_give": 30 / 360})
    return out


def report_text(r):
    m = r["measures"]
    lines = [f"run {r['run']}  criteria {r['criteria']}",
             f"window {r['window_yr'][0]:.3g}-{r['window_yr'][1]:.3g} yr: {r['snapshots_in_window']} snapshots; last snapshot {r['last_snapshot_yr']:.6g} yr; complete: {r['complete']}",
             f"M1 {m['M1_deg']:.1f} deg (pooled n {m['n_pooled']})" if m["M1_deg"] is not None else "M1 -",
             f"M2 {m['M2_mean_R']:.3f}" if m["M2_mean_R"] is not None else "M2 -",
             f"M3 psi {m['M3_psi_deg']:.1f} deg" if m["M3_psi_deg"] is not None else "M3 -",
             f"M4 wall {m['M4_wall_au']} au (R_plat {m['M4_R_plat']})",
             f"M5 {m['M5']}",
             "subsets: " + "; ".join(f"{s['subset']}: M1 {s['M1_deg']:.1f} ({s['distance_to_pooled_M1_deg']:.1f} deg)" if s["M1_deg"] is not None else f"{s['subset']}: -"
                                     for s in r["subsets"]),
             f"subset scatter {r['subset_scatter_deg']} deg (limit {r['scatter_limit_deg']:g}); deviating, reported: {r['deviating_subsets_reported']}",
             "variants (not judged): " + "; ".join(f"{k}: M1 {v['M1_deg']:.1f}, psi {v['M3_psi_deg']:.1f}" for k, v in r["variants_not_judged"].items()
                                                  if v["M1_deg"] is not None and v["M3_psi_deg"] is not None),
             f"== {r['verdict']}"]
    return "\n".join(lines) + "\n"


def code_version():
    root = Path(__file__).resolve().parents[1]
    p = subprocess.run(["git", "-C", str(root), "describe", "--tags", "--match", "prod-eval-*", "--dirty", "--always"], capture_output=True, text=True)
    return p.stdout.strip() or "unknown"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--p9sim")
    ap.add_argument("--criteria", choices=["production", "bb2021-A", "bb2021-B"], default="production")
    ap.add_argument("--window", type=float, nargs=2, default=[1e9, 4e9])
    ap.add_argument("--t-end", type=float, default=4e9, help="the run counts as complete if it has a snapshot at this time")
    ap.add_argument("--n-tp", type=int, default=64000)
    ap.add_argument("--subsets", type=int, default=4)
    ap.add_argument("--observed")
    ap.add_argument("--outcome", nargs=2, metavar=("A_RESULT", "B_RESULT"))
    a = ap.parse_args()
    if a.outcome:
        print(outcome(*a.outcome))
        return
    if not a.run or not a.out:
        ap.error("RUN and --out are needed")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    result, series = evaluate(a.run, a.p9sim, tuple(a.window), a.n_tp, a.subsets, a.criteria, a.observed, a.t_end)
    result["code_version"] = code_version()
    (out / "result.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    with open(out / "timeseries.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(series[0].keys()))
        w.writeheader()
        w.writerows(series)
    text = report_text(result)
    (out / "report.txt").write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
