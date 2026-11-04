#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run time of the A100 sections with the cost of the close encounters, calibrated on the production run as it runs.

  python3 -I speed/estimate_encounters.py RESULTS.tsv G201_DIR EQUIV_V5_JOBS --observed T_MYR WALL_S N_LEFT

speed/estimate_a100.py takes the wall time per Myr from the 1-Myr scaling jobs (0-1 Myr after the start). p9gpu v5
also follows every close flyby with sub-steps, and their number per test particle changes with time: in the night
run G201 (the production configuration, 4,000 test particles, 0-820 Myr) the flybys within three encounter radii
per test particle and Myr (all planets, flybys.tsv) rise from 0.54 (0-20 Myr) to 1.9 (100-120 Myr) and fall to about
0.6-0.8 after 300 Myr. The model:

  wall per Myr at time t = w(N(t)) (1 + k (r(t) - r0))

- w(N): the scaling series, as speed/estimate_a100.py; N(t) = N0 f(t), f from G201 (cases a and b as there).
- r(t): the flyby rate of G201 per 20-Myr segment; after 820 Myr the mean of its last 10 segments.
- r0: the rate in the 1-Myr scaling job, not measured. Two cases bracket it: r0 = 0 and r0 = r(0-20 Myr).
- k: from the observation of the production run (--observed: t reached, wall time since the start of segment 0,
  test particles left).
- For seeds 110-112 (2,000 test particles each, latency-bound) k_lat comes instead from the 9 equivalence runs V5
  (4,000 test particles, latency-bound as well): their mean wall time per segment against r of the same segment of G201.
"""
import argparse
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
ap.add_argument("--observed", nargs=3, type=float, metavar=("T_MYR", "WALL_S", "N_LEFT"), required=True)
a = ap.parse_args()

import csv  # noqa: E402

rows = list(csv.DictReader(open(a.results), delimiter="\t"))
wall = {}
for n, lab in ((4000, "4k"), (16000, "16k"), (64000, "64k"), (256000, "256k")):
    wall[n] = statistics.median(num(r["wall_s"]) for r in rows if r["stage"] == "gpu" and r["device"].startswith("NVIDIA_A100")
                                and r["job"] == f"gpu-v5-{lab}-1m" and r["verdict"] == "SAME")

segs = sorted(glob.glob(os.path.join(a.g201, "seg*")))
pts, rate = [(0.0, 1.0)], []
for s in segs:
    r = json.load(open(os.path.join(s, "result.json")))
    j = json.load(open(os.path.join(s, "job.json")))
    t_end = j["params"]["t_end_yr"] / 1e6
    pts.append((t_end, (r["particles_end"] - 6) / 4000))
    x = np.genfromtxt(os.path.join(s, "flybys.tsv"), delimiter="\t", names=True)
    near = sum(x[f"near_{k}"].sum() for k in range(1, 6))
    rate.append((t_end - 20, t_end, near / len(x) / 20))
late = statistics.mean(r for *_, r in rate[-10:])


def f(t, case):
    if t <= pts[-1][0]:
        for (t0, f0), (t1, f1) in zip(pts, pts[1:]):
            if t0 <= t <= t1:
                return f0 + (f1 - f0) * (t - t0) / (t1 - t0)
    return 1.6043 - 0.1553 * math.log(t) if case == "a" else pts[-1][1]


def r_at(t):
    for t0, t1, r in rate:
        if t0 <= t < t1:
            return r
    return late


def w(n):
    xs = sorted(wall)
    if n <= xs[0]:
        return wall[xs[0]]
    for lo, hi in zip(xs, xs[1:]):
        if n <= hi:
            return math.exp(math.log(wall[lo]) + (math.log(wall[hi]) - math.log(wall[lo])) * (math.log(n) - math.log(lo)) / (math.log(hi) - math.log(lo)))
    return wall[xs[-1]] * n / xs[-1]


def run_s(n0, t_end, k, r0, case, steps=10):
    """Wall time (s) from 0 to t_end Myr, in steps of 1/steps Myr."""
    s = 0.0
    for i in range(int(t_end * steps)):
        t = (i + 0.5) / steps
        s += w(n0 * f(t, case)) * (1 + k * (r_at(t) - r0)) / steps
    return s


T, WALL, NLEFT = a.observed
print(f"observed: {T:g} Myr after {WALL:.0f} s, {NLEFT:.0f} left ({NLEFT / 64000:.3f}; G201 f({T:g}) = {f(T, 'a'):.3f})")
print(f"  {WALL / T:.1f} s per Myr; the scaling series gives {w(64000):.1f} at 64,000 and {w((64000 + NLEFT) / 2):.1f} at the mean N")
print("G201 flyby rate per test particle and Myr (within 3 encounter radii): "
      + ", ".join(f"{t0:.0f}-{t1:.0f} {r:.2f}" for t0, t1, r in rate[:8]) + f", ... after 820 Myr {late:.2f}")

# k_lat from the equivalence runs V5 (notebook, 4,000 test particles, 20-Myr segments)
by_seg = {}
for j in sorted(glob.glob(os.path.join(a.equiv_jobs, "V5-s*"))):
    for line in open(os.path.join(j, "segments.tsv")):
        f_ = line.split("\t")
        by_seg.setdefault(int(f_[0]), []).append(float(f_[3]))
xs = np.array([rate[k][2] for k in sorted(by_seg)])
ys = np.array([statistics.mean(by_seg[k]) for k in sorted(by_seg)])
slope, icpt = np.polyfit(xs, ys, 1)
k_lat_rel = slope / (icpt + slope * rate[0][2])     # per unit r, relative to the cost at r(0-20 Myr)
print(f"equivalence V5 (latency-bound): mean wall per 20-Myr segment {', '.join(f'{v:.0f}' for v in ys)} s; "
      f"against r: {slope:.0f} s per unit r (corr {np.corrcoef(xs, ys)[0, 1]:.2f}), {100 * k_lat_rel:.0f} % per unit r")

print()
for r0_name, r0 in (("r0 = 0", 0.0), (f"r0 = r(0-20 Myr) = {rate[0][2]:.2f}", rate[0][2])):
    lo, hi = 0.0, 50.0                          # k from the observation (bisection; the wall time grows with k)
    for _ in range(80):
        k = (lo + hi) / 2
        lo, hi = (k, hi) if run_s(64000, T, k, r0, "a") < WALL else (lo, k)
    print(f"case {r0_name}: k = {k:.3f} (wall per Myr = w(N) (1 + k (r - r0)))")
    tot = {"a": 0.0, "b": 0.0}
    for name, n0 in (("production run", 64000), ("set A", 64000), ("set B", 64000)):
        da, db = run_s(n0, 4000, k, r0, "a", 2) / 86400, run_s(n0, 4000, k, r0, "b", 2) / 86400
        tot["a"] += da; tot["b"] += db
        print(f"  {name} (64,000): {da:.1f} to {db:.1f} days (was {run_s(n0, 4000, 0.0, 0.0, 'a', 2) / 86400:.1f} to {run_s(n0, 4000, 0.0, 0.0, 'b', 2) / 86400:.1f})")
    v5 = 3 * sum(w(2000) * (1 + k_lat_rel * (r_at(t + 0.5) - r0)) for t in range(4000)) / 86400
    print(f"  seeds 110-112, V5 (3 x 2,000, latency-bound, k_lat): {v5:.1f} days (was {3 * 4000 * w(2000) / 86400:.1f})")
    print(f"  A100 in all: {tot['a'] + v5:.1f} to {tot['b'] + v5:.1f} days")
    seg0 = run_s(64000, 100, k, r0, "a")
    print(f"  segment 0 (0-100 Myr) of the production run: {seg0 / 3600:.2f} h")
