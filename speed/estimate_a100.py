#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run-time estimate of the four A100 sections and of the MERCURIUS part of seeds 110-112 on CPU 1, from the speed
comparison on appmdp-05 (2026-11-03/04) and the survival of the test particles in the night run G201.

  python3 -I speed/estimate_a100.py RESULTS.tsv G201_DIR

- Wall time per Myr of p9gpu v5 on the A100 as a function of the number of test particles N: the scaling series
  (1 Myr at 4,000 / 16,000 / 64,000 / 256,000), interpolated log-log; below 4,000 the value at 4,000 (latency-bound).
- N(t) = N0 f(t): f from G201 (4,000 test particles, the production configuration, 0-820 Myr, segments of 20 Myr);
  after 820 Myr two cases: (a) f = 1.6043 - 0.1553 ln(t / Myr), the log fit over 200-820 Myr (f = 0.32 at 4 Gyr);
  (b) no further loss after 820 Myr (f = 0.56): an upper bound.
- Three processes on one GPU take as long as one after the other (no MPS; speed comparison and the laptop test).
- MERCURIUS: ns per test-particle step from the comparison (cpu1, 6 processes at once: 253 ns; cpuall, 32 at once:
  306 ns), 8 slices of 250 per seed, 24 slices on the 16 cores of CPU 1.
"""
import csv
import glob
import json
import math
import os
import statistics
import sys


def num(x):
    return float(x.replace(",", ".")) if "," in x and "." not in x else float(x)


rows = list(csv.DictReader(open(sys.argv[1]), delimiter="\t"))
wall = {}
for n, lab in ((4000, "4k"), (16000, "16k"), (64000, "64k"), (256000, "256k")):
    w = [num(r["wall_s"]) for r in rows if r["stage"] == "gpu" and r["device"].startswith("NVIDIA_A100") and r["job"] == f"gpu-v5-{lab}-1m" and r["verdict"] == "SAME"]
    wall[n] = statistics.median(w)
pts = []
for s in sorted(glob.glob(os.path.join(sys.argv[2], "seg*/result.json"))):
    r = json.load(open(s))
    j = json.load(open(os.path.join(os.path.dirname(s), "job.json")))
    pts.append((j["params"]["t_end_yr"] / 1e6, (r["particles_end"] - 6) / 4000))
pts = [(0.0, 1.0)] + pts


def f(t, case):
    if t <= pts[-1][0]:
        for (t0, f0), (t1, f1) in zip(pts, pts[1:]):
            if t0 <= t <= t1:
                return f0 + (f1 - f0) * (t - t0) / (t1 - t0)
    return 1.6043 - 0.1553 * math.log(t) if case == "a" else pts[-1][1]


def w_per_myr(n):
    xs = sorted(wall)
    if n <= xs[0]:
        return wall[xs[0]]
    for a, b in zip(xs, xs[1:]):
        if n <= b:
            return math.exp(math.log(wall[a]) + (math.log(wall[b]) - math.log(wall[a])) * (math.log(n) - math.log(a)) / (math.log(b) - math.log(a)))
    return wall[xs[-1]] * n / xs[-1]


def gpu_days(n0, procs, case):
    return procs * sum(w_per_myr(n0 * f(t + 0.5, case)) for t in range(4000)) / 86400


print("A100, p9gpu v5, wall per Myr:", {k: round(v, 1) for k, v in wall.items()})
print(f"G201: f(200) {f(200, 'a'):.3f}, f(820) {f(820, 'a'):.3f}; f(4000): (a) {f(4000, 'a'):.3f}, (b) {f(4000, 'b'):.3f}")
total = {"a": 0.0, "b": 0.0}
for name, n0, procs in (("1. production run (64,000)", 64000, 1), ("2. seeds 110-112, V5 (3 x 2,000)", 2000, 3),
                        ("3. set A (64,000)", 64000, 1), ("4. set B (64,000)", 64000, 1)):
    da, db = gpu_days(n0, procs, "a"), gpu_days(n0, procs, "b")
    total["a"] += da
    total["b"] += db
    print(f"{name}: {da:.1f} days (case a) to {db:.1f} days (case b); constant N: {procs * 4000 * w_per_myr(n0) / 86400:.1f} days")
print(f"A100 in all: {total['a']:.1f} to {total['b']:.1f} days")
fbar = {c: sum(f(t + 0.5, c) for t in range(4000)) / 4000 for c in "ab"}
for ns in (253.0, 306.0):
    for c in "ab":
        slice_h = 250 * 8e9 * fbar[c] * ns * 1e-9 / 3600
        print(f"MERCURIUS, {ns:.0f} ns, case {c} (mean f {fbar[c]:.3f}): {slice_h:.0f} h per slice, {24 * slice_h:.0f} core hours; "
              f"24 slices on 16 cores (two rounds: 16, then 8): {2 * slice_h / 24:.1f} days")
