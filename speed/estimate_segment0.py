#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run time of the A100 sections, calibrated on segment 0 of the production run (0-100 Myr), with the sub-steps of
p9gpu v5 as the measure of the encounter load.

  python3 -I speed/estimate_segment0.py RESULTS.tsv G201_DIR EQUIV_V5_JOBS \\
      --obs 60 5603 --obs 100 10273.785 --n-end 58513 --substeps 237867825

Model: wall per Myr = w(N(t)) (1 + k (s(t) - s0)).
- w(N): the A100 scaling series (1-Myr jobs, interpolated log-log, as speed/estimate_a100.py).
- s(t): sub-steps per test particle and Myr.
  - 0-200 Myr: the mean of the 9 equivalence runs V5 per 20-Myr segment (flybys.tsv, sub_steps), scaled by segment 0
    of the production run against their mean over 0-100 Myr.
  - After 200 Myr: the flyby rate of G201 (within three encounter radii, per test particle and Myr) times the ratio
    of sub-steps to flybys over 0-200 Myr. That ratio is nearly constant there: 29-41, mean below.
  - After 820 Myr: the mean of the last 10 segments of G201.
- N(t) = 64,000 f(t).
  - 0-200 Myr: f is the mean survival of the equivalence runs V5, which remove at the encounter radii as the
    production run does (at 100 Myr: 0.917; the production run: 0.914).
  - After 200 Myr: G201 relative to its value at 200 Myr. G201 counted encounters without removing.
  - After 820 Myr: the cases (a) log fit and (b) constant, as speed/estimate_a100.py.
- k and s0 from the two observed intervals of segment 0 (0-60 and 60-100 Myr): two equations, two unknowns.
Sets A and B are assumed to have the encounter profile of the production run: the least certain part.
"""
import argparse
import csv
import glob
import json
import math
import os
import statistics

import numpy as np


def num(x):
    return float(x.replace(",", ".")) if "," in x and "." not in x else float(x)


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("results")
ap.add_argument("g201")
ap.add_argument("equiv_jobs")
ap.add_argument("--obs", nargs=2, type=float, action="append", metavar=("T_MYR", "WALL_S"), required=True)
ap.add_argument("--n-end", type=float, required=True, help="test particles left at the end of segment 0")
ap.add_argument("--substeps", type=float, required=True, help="sub-steps of segment 0 (sum of flybys.tsv sub_steps)")
a = ap.parse_args()

rows = list(csv.DictReader(open(a.results), delimiter="\t"))
wall = {n: statistics.median(num(r["wall_s"]) for r in rows if r["stage"] == "gpu" and r["device"].startswith("NVIDIA_A100")
                             and r["job"] == f"gpu-v5-{lab}-1m" and r["verdict"] == "SAME")
        for n, lab in ((4000, "4k"), (16000, "16k"), (64000, "64k"), (256000, "256k"))}


def w(n):
    xs = sorted(wall)
    if n <= xs[0]:
        return wall[xs[0]]
    for lo, hi in zip(xs, xs[1:]):
        if n <= hi:
            return math.exp(math.log(wall[lo]) + (math.log(wall[hi]) - math.log(wall[lo])) * (math.log(n) - math.log(lo)) / (math.log(hi) - math.log(lo)))
    return wall[xs[-1]] * n / xs[-1]


# equivalence runs V5: survival at segment ends and sub-steps per test particle and Myr, per 20-Myr segment
jobs = sorted(glob.glob(os.path.join(a.equiv_jobs, "V5-s*")))
eq_s, eq_f = np.zeros(10), np.zeros(10)
for j in jobs:
    nend = {int(l.split("\t")[0]): int(l.split("\t")[2]) - 6 for l in open(os.path.join(j, "segments.tsv"))}
    for k in range(10):
        d = np.genfromtxt(os.path.join(j, "segments", f"seg{k:03d}", "flybys.tsv"), delimiter="\t", names=True)
        eq_s[k] += d["sub_steps"].sum() / len(d) / 20 / len(jobs)
        eq_f[k] += nend[k] / 4000 / len(jobs)
# G201: survival and flyby rate per 20-Myr segment
g_pts, g_rate = [(0.0, 1.0)], []
for s in sorted(glob.glob(os.path.join(a.g201, "seg*"))):
    r = json.load(open(os.path.join(s, "result.json")))
    t_end = json.load(open(os.path.join(s, "job.json")))["params"]["t_end_yr"] / 1e6
    g_pts.append((t_end, (r["particles_end"] - 6) / 4000))
    x = np.genfromtxt(os.path.join(s, "flybys.tsv"), delimiter="\t", names=True)
    g_rate.append(sum(x[f"near_{k}"].sum() for k in range(1, 6)) / len(x) / 20)
late_rate = statistics.mean(g_rate[-10:])
ratio = statistics.mean(eq_s[k] / g_rate[k] for k in range(10))
seg0_rate = a.substeps / 64000 / 100
scale = seg0_rate / eq_s[:5].mean()


def interp(pts, t):
    for (t0, f0), (t1, f1) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            return f0 + (f1 - f0) * (t - t0) / (t1 - t0)
    return pts[-1][1]


eq_pts = [(0.0, 1.0)] + [(20.0 * (k + 1), eq_f[k]) for k in range(10)]


def f(t, case):
    if t <= 200:
        return interp(eq_pts, t)
    g200 = interp(g_pts, 200)
    if t <= g_pts[-1][0]:
        return eq_f[9] * interp(g_pts, t) / g200
    g = (1.6043 - 0.1553 * math.log(t)) if case == "a" else g_pts[-1][1]
    return eq_f[9] * g / g200


def s_at(t):
    if t < 200:
        return scale * eq_s[int(t // 20)]
    k = int(t // 20)
    return scale * ratio * (g_rate[k] if k < len(g_rate) else late_rate)


def run_s(t0, t1, k, s0, case="a", n0=64000, steps=10):
    tot = 0.0
    for i in range(int(round((t1 - t0) * steps))):
        t = t0 + (i + 0.5) / steps
        tot += w(n0 * f(t, case)) * (1 + k * (s_at(t) - s0)) / steps
    return tot


(t1, W1), (t2, W2) = sorted(a.obs)
# linear in k and k*s0: run_s = A + k B - k s0 C, with A = sum w, B = sum w s, C = sum w
def parts(ta, tb):
    A = run_s(ta, tb, 0.0, 0.0)
    B = run_s(ta, tb, 1.0, 0.0) - A
    return A, B
A1, B1 = parts(0, t1)
A2, B2 = parts(t1, t2)
# W = A + k B - k s0 A  ->  (W/A - 1) = k (B/A - s0)
y1, y2 = W1 / A1 - 1, (W2 - W1) / A2 - 1
x1, x2 = B1 / A1, B2 / A2
k = (y2 - y1) / (x2 - x1)
s0 = x1 - y1 / k

print(f"segment 0: {a.n_end:.0f} test particles left ({a.n_end / 64000:.4f}; equivalence runs V5 at 100 Myr {eq_f[4]:.4f}); "
      f"{seg0_rate:.1f} sub-steps per test particle and Myr (equivalence runs over 0-100 Myr {eq_s[:5].mean():.1f}, scale {scale:.3f})")
print(f"observed: 0-{t1:g} Myr {W1 / t1:.1f} s per Myr, {t1:g}-{t2:g} Myr {(W2 - W1) / (t2 - t1):.1f} s per Myr; scaling series at 64,000: {w(64000):.1f}")
print("sub-steps per test particle and Myr, 20-Myr segments 0-200 Myr (scaled): " + ", ".join(f"{scale * v:.0f}" for v in eq_s)
      + f"; after 200 Myr {ratio:.1f} x the flyby rate of G201 (after 820 Myr: {scale * ratio * late_rate:.0f})")
print(f"fit: k = {k:.4f} per sub-step and Myr, s0 = {s0:.1f} (the 1-Myr scaling job); check: 0-{t1:g} {run_s(0, t1, k, s0):.0f} s, 0-{t2:g} {run_s(0, t2, k, s0):.0f} s")
print()
seg0 = W2
for case in "ab":
    prod = seg0 + run_s(t2, 4000, k, s0, case, steps=2)
    full = run_s(0, 4000, k, s0, case, steps=2)
    segs = [run_s(100 * i, 100 * (i + 1), k, s0, case, steps=2) / 3600 for i in range(1, 6)]
    print(f"case {case}: production run {prod / 86400:.2f} days in all ({(prod - seg0) / 86400:.2f} days after segment 0); "
          f"segments 1-5: {', '.join(f'{h:.1f}' for h in segs)} h; sets A and B each {full / 86400:.2f} days")
