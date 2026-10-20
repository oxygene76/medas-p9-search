#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Jacobi constant in the circular restricted three-body problem: fixed step, hard switch, smooth transition.

  python tools/jacobi_test.py make --out DIR [--n-tp 256]
  python tools/jacobi_test.py run --dir DIR --method fixed|substep|smooth [--t-end 1e7 --snapshots 100] [--mode gpu]
  python tools/jacobi_test.py analyze --dir DIR

The Sun and Neptune on a circular orbit (in the xy plane), test particles on
Neptune-crossing orbits (heliocentric a 30-45 au, perihelion 22-30 au,
inclination 0-5 deg, seed 3): many close encounters. For a massless particle
the Jacobi constant C = 2 (mu_S / r_S + mu_N / r_N) - v^2 + 2 n (x v_y - y v_x)
(barycentric, inertial; n Neptune's mean motion) is conserved, encounters or
not, so its error shows the integrator's error over the encounters. p9gpu
with method fixed (dt = 0.5 yr, no radii; with counting, which leaves the
trajectories bit-identical), substep (hard switch) and smooth (the accepted
design), the radius 4 x Neptune's Hill radius as for the runs. Removal by the
distance rules and, with smooth, by a collision with Neptune (its physical
radius, tools/p9job.py). The steps at the cap of sub-steps (P9_CAPPED_OUT)
and the collisions are reported. analyze: per method and snapshot the median, 90 % and
maximum of |dC/C| over the particles still there, and the trend.
"""

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from make_ic import G, elements_to_state  # noqa: E402
import p9job  # noqa: E402

M_N = 5.151383713179197e-05  # Neptune / Sun (DE440 GM ratio, as make_ic.py)
A_N = 30.07
RADII = {"substep": "1=3.1036", "smooth": "1=3.1036", "fixed": "1=3.1036"}  # 4 x Neptune's Hill radius 0.7759 au


def cmd_make(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(3)
    mt = 1.0 + M_N
    n = math.sqrt(G * mt / A_N ** 3)
    xs, xn = -M_N / mt * A_N, 1.0 / mt * A_N
    vs, vn = -M_N / mt * n * A_N, 1.0 / mt * n * A_N
    sun = (1.0, np.array([xs, 0.0, 0.0]), np.array([0.0, vs, 0.0]))
    nep = (M_N, np.array([xn, 0.0, 0.0]), np.array([0.0, vn, 0.0]))
    k = a.n_tp
    aa = rng.uniform(30.0, 45.0, k)
    q = rng.uniform(22.0, 30.0, k)
    inc = np.radians(rng.uniform(0.0, 5.0, k))
    Om, om, M = (rng.uniform(0, 2 * np.pi, k) for _ in range(3))
    p, v = elements_to_state(G * 1.0, aa, 1 - q / aa, inc, Om, om, M)
    with open(out / "ic.txt", "w") as f:
        f.write(f"# circular restricted three-body test (tools/jacobi_test.py), n = {n!r} rad/yr\n")
        f.write(f"G {G!r}\ndt 0.5\nN_active 2\ncorrector 0\n")
        for name, (m, x, u), pid in (("Sun", sun, 0), ("Neptune", nep, 1)):
            f.write("p " + name + " " + " ".join(repr(float(z)) for z in [m, *x, *u]) + f" {pid}\n")
        for i in range(k):
            x, u = sun[1] + p[i], sun[2] + v[i]
            f.write(f"p tp{i:05d} 0.0 " + " ".join(repr(float(z)) for z in [*x, *u]) + f" {2 + i}\n")
    subprocess.run([str(ROOT / "build/test/p9sim"), "init", str(out / "ic.txt"), str(out / "input.sa")], check=True, stdout=subprocess.DEVNULL)
    (out / "params.json").write_text(json.dumps({"n": n, "n_tp": k, "mu_S": G * 1.0, "mu_N": G * M_N}) + "\n")
    print(f"jacobi_test: {k} test particles -> {out}")


def cmd_run(a):
    d = Path(a.dir)
    env = dict(os.environ, P9GPU_MODE=a.mode)
    for k in ("P9_ENCOUNTER_RADII", "P9_ENCOUNTER_METHOD", "P9_ENCOUNTER_REMOVE", "P9_FLYBY_OUT", "P9_J2", "P9GPU_REAL", "P9_PLANET_SUBSTEPS",
              "P9_COLLISION_RADII", "P9_CAPPED_OUT", "P9_REMOVED_OUT"):
        env.pop(k, None)
    env.update(P9_ENCOUNTER_RADII=RADII[a.method], P9_PLANET_SUBSTEPS="8", P9_FLYBY_OUT=str(d / f"flybys-{a.method}.tsv"))
    if a.method == "fixed":
        env.update(P9_ENCOUNTER_METHOD="step", P9_ENCOUNTER_REMOVE="0")  # counting only: the fixed step's trajectories
    else:
        env.update(P9_ENCOUNTER_METHOD=a.method)
    if a.method == "smooth":
        env.update(P9_COLLISION_RADII=f"1={p9job.PHYSICAL_RADII_KM['Neptune'] / p9job.AU_KM:.6e}", P9_REMOVED_OUT=str(d / f"removed-{a.method}.tsv"))
        if a.mode == "cpu":
            env.update(P9_CAPPED_OUT=str(d / f"capped-{a.method}.tsv"))
    p = subprocess.run([a.p9gpu, "run", str(d / "input.sa"), repr(a.t_end), str(a.snapshots), str(d / f"output-{a.method}.sa")], env=env,
                       capture_output=True, text=True)
    (d / f"run-{a.method}.log").write_text(p.stdout + p.stderr)
    if p.returncode:
        sys.exit(p.stderr[-2000:])
    print([l for l in p.stdout.splitlines() if l.startswith("result_sha256=")][-1])


def jacobi(rows, par):
    s = np.array([float(x) for x in rows[0][3:9]])
    nn = np.array([float(x) for x in rows[1][3:9]])
    out = {}
    for r in rows[2:]:
        x = np.array([float(z) for z in r[3:9]])
        rs, rn = np.linalg.norm(x[:3] - s[:3]), np.linalg.norm(x[:3] - nn[:3])
        C = 2 * (par["mu_S"] / rs + par["mu_N"] / rn) - x[3:] @ x[3:] + 2 * par["n"] * (x[0] * x[4] - x[1] * x[3])
        out[int(float(r[1]))] = C
    return out


def cmd_analyze(a):
    d = Path(a.dir)
    par = json.loads((d / "params.json").read_text())
    p9sim = str(ROOT / "build/test/p9sim")
    rows0 = [l.split() for l in subprocess.run([p9sim, "dump", str(d / "input.sa"), "0"], capture_output=True, text=True).stdout.splitlines()[1:]]
    C0 = jacobi(rows0, par)
    report = {}
    for method in ("fixed", "substep", "smooth"):
        sa = d / f"output-{method}.sa"
        if not sa.exists():
            continue
        series = []
        k = 0
        while True:
            out = subprocess.run([p9sim, "dump", str(sa), str(k)], capture_output=True, text=True)
            if out.returncode:
                break
            lines = out.stdout.splitlines()
            t = float(lines[0].split()[1])
            C = jacobi([l.split() for l in lines[1:]], par)
            err = np.array([abs((C[i] - C0[i]) / C0[i]) for i in C])
            series.append({"t": t, "n": int(len(err)), "median": float(np.median(err)), "p90": float(np.quantile(err, 0.9)), "max": float(err.max())})
            k += 1
        ts = np.array([x["t"] for x in series]) / 1e6
        med = np.array([x["median"] for x in series])
        # trend: slope of log(median) against log(t) (0: no growth; 0.5: random walk; 1: linear drift)
        slope = float(np.polyfit(np.log(ts), np.log(med), 1)[0]) if len(ts) > 2 and (med > 0).all() else float("nan")
        fb = d / f"flybys-{method}.tsv"
        enc = fast = close = 0
        if fb.exists():
            import csv
            for r in csv.DictReader(open(fb), delimiter="\t"):
                enc += int(r["near_1"]); fast += int(r["fast_1"]); close += int(r["close_1"])
        log = d / f"run-{method}.log"
        kv = dict(x.split("=", 1) for x in [l for l in log.read_text().splitlines() if l.startswith("result_sha256=")][-1].split()) if log.exists() else {}
        report[method] = {"series": series, "loglog_slope_median": slope, "flybys_within_3_rule_radii": enc, "under_1_5_steps": fast,
                          "under_0_1_au": close, "sub_capped": int(kv.get("sub_capped", 0)), "sub_max": int(kv.get("sub_max", 1)),
                          "collisions": kv.get("collisions", "-"), "removed": int(kv.get("removed", 0))}
        print(f"== {method}: flybys within 3 rule radii {enc}, shorter than 1.5 steps {fast}, closer than 0.1 au {close}; "
              f"removed {kv.get('removed', '-')}, collisions {kv.get('collisions', '-')}, steps at the cap {kv.get('sub_capped', '-')} "
              f"(largest n {kv.get('sub_max', '-')})")
        for x in series:
            if x["t"] in (1e6, 2e6, 5e6, 1e7) or x is series[-1]:
                print(f"   t = {x['t'] / 1e6:5.1f} Myr  n = {x['n']:4d}  |dC/C| median {x['median']:.2e}  90% {x['p90']:.2e}  max {x['max']:.2e}")
        print(f"   trend of the median: |dC/C| ~ t^{slope:.2f}")
    (d / "jacobi.json").write_text(json.dumps(report, indent=1) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make"); m.add_argument("--out", required=True); m.add_argument("--n-tp", type=int, default=256)
    r = sub.add_parser("run"); r.add_argument("--dir", required=True); r.add_argument("--method", choices=["fixed", "substep", "smooth"], required=True)
    r.add_argument("--t-end", type=float, default=1e7); r.add_argument("--snapshots", type=int, default=100)
    r.add_argument("--p9gpu", default=str(ROOT / "build/gpu-cpu/p9gpu")); r.add_argument("--mode", choices=["cpu", "gpu"], default="cpu")
    z = sub.add_parser("analyze"); z.add_argument("--dir", required=True)
    a = ap.parse_args()
    {"make": cmd_make, "run": cmd_run, "analyze": cmd_analyze}[a.cmd](a)


if __name__ == "__main__":
    main()
