#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Energy error of p9gpu's test-particle integrator in a number type (P9GPU_REAL).

  python tools/kepler_energy.py make --out DIR [--n-tp 1920]
  python tools/kepler_energy.py run  --dir DIR --real df64 --t-end 3e8 --snapshots 30 [--p9gpu build/gpu/p9gpu]
  python tools/kepler_energy.py analyze --dir DIR --real df64 [--p9sim build/test/p9sim]

In the full problem the energy of a test particle is not conserved (the planets
move). Here the same integrator runs with the planets made massless: the jump
and the kick vanish, every test particle moves on a Kepler orbit around the
Sun, and its energy E = v^2/2 - G m_Sun / r is conserved exactly. Any change is
numerical: rounding in the number type and the Kepler solver's convergence.
Start values: the test case's test particles (tools/make_ic.py, seed 9).

Output of analyze: for every snapshot the median and the largest |dE/E| over
the test particles, against their start values.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def cmd_make(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ic = out / "ic-full.txt"
    subprocess.run([sys.executable, "-I", str(ROOT / "tools/make_ic.py"), "--out", str(ic), "--n-tp", str(a.n_tp), "--seed", "9"], check=True)
    lines = []
    for line in ic.read_text().splitlines():
        f = line.split()
        if f and f[0] == "p" and f[1] != "Sun" and float(f[2]) > 0:
            f[2] = "0.0"  # the planets massless: pure Kepler orbits for the test particles
            line = " ".join(f)
        lines.append(line)
    (out / "ic.txt").write_text("\n".join(lines) + "\n")
    subprocess.run([str(a.p9sim), "init", str(out / "ic.txt"), str(out / "input.sa")], check=True, stdout=subprocess.DEVNULL)
    print(f"kepler_energy: {a.n_tp} test particles, planets massless -> {out}")


def cmd_run(a):
    d = Path(a.dir)
    env = dict(os.environ, P9GPU_REAL=a.real)
    env.pop("P9_ENCOUNTER_RADII", None)
    out = d / f"output-{a.real}.sa"
    p = subprocess.run([str(a.p9gpu), "run", str(d / "input.sa"), repr(a.t_end), str(a.snapshots), str(out)], env=env, capture_output=True, text=True)
    (d / f"run-{a.real}.log").write_text(p.stdout + p.stderr)
    if p.returncode:
        sys.exit(p.stderr[-2000:])
    print([l for l in p.stdout.splitlines() if l.startswith("result_sha256=")][-1])


def energies(p9sim, sa, k, mu):
    out = subprocess.run([str(p9sim), "dump", str(sa), str(k)], capture_output=True, text=True, check=True).stdout.splitlines()
    t = float(out[0].split()[1])
    rows = [l.split() for l in out[1:]]
    sun = np.array([float(x) for x in rows[0][3:9]])
    tp = np.array([[float(x) for x in r[3:9]] for r in rows if r[0].startswith("tp")])
    ids = np.array([int(float(r[1])) for r in rows if r[0].startswith("tp")])
    rel = tp - sun
    r = np.linalg.norm(rel[:, :3], axis=1)
    v2 = (rel[:, 3:] ** 2).sum(1)
    return t, ids, v2 / 2 - mu / r


def cmd_analyze(a):
    d = Path(a.dir)
    G = mu = None
    for line in (d / "ic.txt").read_text().splitlines():
        f = line.split()
        if f and f[0] == "G":
            G = float(f[1])
        if f and f[0] == "p" and f[1] == "Sun":
            mu = G * float(f[2])
    _, ids0, e0 = energies(a.p9sim, d / "input.sa", 0, mu)
    ref = dict(zip(ids0, e0))
    rows = []
    k = 0
    while True:
        try:
            t, ids, e = energies(a.p9sim, d / f"output-{a.real}.sa", k, mu)
        except subprocess.CalledProcessError:
            break
        rel = np.abs(np.array([(e[j] - ref[i]) / ref[i] for j, i in enumerate(ids)]))
        rows.append({"t_yr": t, "n": int(len(rel)), "median": float(np.median(rel)), "p90": float(np.quantile(rel, 0.9)), "max": float(rel.max())})
        print(f"t = {t / 1e6:7.1f} Myr  n = {len(rel)}  |dE/E| median {np.median(rel):.2e}  90% {np.quantile(rel, 0.9):.2e}  max {rel.max():.2e}")
        k += 1
    (d / f"energy-{a.real}.json").write_text(json.dumps(rows, indent=1) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--out", required=True)
    m.add_argument("--n-tp", type=int, default=1920)
    m.add_argument("--p9sim", default=str(ROOT / "build/test/p9sim"))
    r = sub.add_parser("run")
    r.add_argument("--dir", required=True)
    r.add_argument("--real", required=True)
    r.add_argument("--t-end", type=float, required=True)
    r.add_argument("--snapshots", type=int, required=True)
    r.add_argument("--p9gpu", default=str(ROOT / "build/gpu/p9gpu"))
    z = sub.add_parser("analyze")
    z.add_argument("--dir", required=True)
    z.add_argument("--real", required=True)
    z.add_argument("--p9sim", default=str(ROOT / "build/test/p9sim"))
    a = ap.parse_args()
    {"make": cmd_make, "run": cmd_run, "analyze": cmd_analyze}[a.cmd](a)


if __name__ == "__main__":
    main()
