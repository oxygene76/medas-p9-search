#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""tools/flyby_check.py (the project lead's REBOUND check) for p9gpu.

  python tools/flyby_p9gpu.py run --planet p9 --dt 0.5 [--dmin 0.5 --vrel 0.35] --out f.json [--p9gpu build/gpu/p9gpu] [--mode cpu|gpu]
  python tools/flyby_p9gpu.py summary f.json

The same test bodies (flyby_check.make_test_bodies, seed 1), the same windows
(start at -(T + phase dt), IAS15 backwards from closest approach), the same
reference (IAS15 with a fixed small step) and the same measures (error of the
change of heliocentric orbital energy E and angular momentum h, relative to
the change itself). Instead of REBOUND's WHFast, p9gpu integrates the window:
Wisdom-Holman in democratic heliocentric coordinates, gpu/whdh.h, the same
code as on the GPU (P9GPU_MODE=cpu runs it on the CPU and gives the same bits).
For comparison the rows also hold REBOUND's WHFast (democratic heliocentric)
on the same window. p9gpu runs without encounter removal (no radii).
"""

import argparse
import collections
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import flyby_check as fc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def write_ic(path, sim, dt, planet_name):
    """The REBOUND state as a start file for p9sim init (exact decimals; ids 0, 1, 2, ...)."""
    with open(path, "w") as f:
        f.write(f"# flyby window for p9gpu (tools/flyby_p9gpu.py)\nG {fc.G!r}\ndt {float(dt)!r}\nN_active 2\ncorrector 0\n")
        for k, p in enumerate(sim.particles):
            name = "Sun" if k == 0 else planet_name if k == 1 else f"tp{k - 2:05d}"
            vals = [p.m, p.x, p.y, p.z, p.vx, p.vy, p.vz]
            f.write("p " + name + " " + " ".join(repr(float(v)) for v in vals) + f" {k}\n")


def energy_and_h_dump(text):
    """E and h of the test bodies from `p9sim dump` (heliocentric, as flyby_check.energy_and_h)."""
    rows = [l.split() for l in text.splitlines()[1:]]
    s = np.array([float(x) for x in rows[0][3:9]])
    out = []
    for r in rows[2:]:
        q = np.array([float(x) for x in r[3:9]]) - s
        h = np.cross(q[:3], q[3:])
        out.append((0.5 * q[3:] @ q[3:] - fc.G / np.linalg.norm(q[:3]), *h))
    return np.array(out)


def one_window(p, dt, phase, m, rp, vp, bodies, p9gpu, p9sim, mode, planet_name):
    t_start = -(p["halfwindow_yr"] + phase * dt)
    nsteps = int(math.ceil((2 * p["halfwindow_yr"] + phase * dt) / dt))
    sim = fc.base_sim(m, rp, vp, bodies)
    sim.integrator = "ias15"
    sim.dt = -0.01
    sim.integrate(t_start)
    start = sim.copy()
    res = {"start": fc.energy_and_h(start)}
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        write_ic(d / "ic.txt", start, dt, planet_name)
        subprocess.run([str(p9sim), "init", str(d / "ic.txt"), str(d / "in.sa")], check=True, stdout=subprocess.DEVNULL)
        env = dict(os.environ, P9GPU_MODE=mode)
        env.pop("P9_ENCOUNTER_RADII", None)
        env.pop("P9_J2", None)
        out = subprocess.run([str(p9gpu), "run", str(d / "in.sa"), repr(nsteps * dt), "1", str(d / "out.sa")], env=env, capture_output=True, text=True)
        if out.returncode:
            sys.exit(out.stderr[-2000:])
        line = [l for l in out.stdout.splitlines() if l.startswith("result_sha256=")][-1]
        kv = dict(x.split("=", 1) for x in line.split())
        if int(kv["steps"]) != nsteps or int(kv["N_end"]) != sim.N:
            sys.exit(f"p9gpu: {kv['steps']} steps, {kv['N_end']} bodies; expected {nsteps}, {sim.N}")
        res["p9gpu"] = energy_and_h_dump(subprocess.run([str(p9sim), "dump", str(d / "out.sa"), "0"], capture_output=True, text=True, check=True).stdout)
        res["hash"] = kv["result_sha256"]
    wh = start.copy()
    wh.integrator = "whfast"
    fc.set_whfast_coordinates(wh, "democraticheliocentric")
    wh.dt = dt
    wh.steps(nsteps)
    wh.synchronize()
    res["rebound_whfast_dh"] = fc.energy_and_h(wh)
    t_end = wh.t
    ref = start.copy()
    ref.integrator = "ias15"
    fc.set_ias15_epsilon(ref, 0.0)
    ref.dt = 0.02
    ref.integrate(t_end)
    res["ref_fixed"] = fc.energy_and_h(ref)
    return res


def cmd_run(a):
    p = dict(fc.PRESETS[a.planet])
    if a.dmin:
        p["dmin"] = a.dmin
    if a.vrel:
        p["vrel"] = a.vrel
    m, rp, vp, bodies = fc.make_test_bodies(p)
    name = "P9" if a.planet == "p9" else "Neptune"
    rows, hashes = [], []
    for dt in a.dt:
        for ph in fc.PHASES:
            r = one_window(p, dt, ph, m, rp, vp, bodies, a.p9gpu, a.p9sim, a.mode, name)
            hashes.append(r["hash"])
            s, ref = r["start"], r["ref_fixed"]
            kick_e = np.abs(ref[:, 0] - s[:, 0])
            kick_h = np.linalg.norm(ref[:, 1:4] - s[:, 1:4], axis=1)
            for c in ("p9gpu", "rebound_whfast_dh"):
                w = r[c]
                for i, (d, v, _, _) in enumerate(bodies):
                    rows.append(dict(planet=a.planet, dt=dt, phase=ph, integrator=c, dmin=d, vrel=v,
                                     err_E=float(abs(w[i, 0] - ref[i, 0]) / kick_e[i]),
                                     err_h=float(np.linalg.norm(w[i, 1:4] - ref[i, 1:4]) / kick_h[i])))
            print(f"{a.planet} dt={dt} phase={ph}: p9gpu ({a.mode}) result {r['hash'][:16]}", file=sys.stderr)
    Path(a.out).write_text(json.dumps({"rows": rows, "p9gpu_hashes": hashes, "mode": a.mode}))


def cmd_summary(a):
    data = json.loads(Path(a.file).read_text())
    cells = collections.defaultdict(list)
    for r in data["rows"]:
        cells[(r["dt"], r["dmin"], r["vrel"], r["integrator"])].append(r)
    keys = sorted({k[:3] for k in cells})
    print(f"error relative to the kick, median / max (p9gpu mode {data['mode']}; REBOUND WHFast democratic heliocentric beside it)")
    print("    dt  d_min  v_rel  flyby/dt |  p9gpu E med    max  h med    max | WHFast E med    max  h med    max")
    for dt, d, v in keys:
        def col(c):
            e = np.array([x["err_E"] for x in cells[(dt, d, v, c)]])
            h = np.array([x["err_h"] for x in cells[(dt, d, v, c)]])
            return f"{np.median(e):8.1e} {e.max():6.1e} {np.median(h):6.1e} {h.max():6.1e}"
        print(f"  {dt:4.1f}  {d:5.2f}  {v:5.2f}  {d / (v * dt):7.2f}  | {col('p9gpu')} | {col('rebound_whfast_dh')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--planet", choices=fc.PRESETS, default="p9")
    r.add_argument("--dt", type=float, nargs="+", default=[0.5])
    r.add_argument("--dmin", type=float, nargs="+")
    r.add_argument("--vrel", type=float, nargs="+")
    r.add_argument("--out", required=True)
    r.add_argument("--p9gpu", default=str(ROOT / "build/gpu-cpu/p9gpu"))
    r.add_argument("--p9sim", default=str(ROOT / "build/gcc-O3/p9sim"))
    r.add_argument("--mode", choices=["cpu", "gpu"], default="cpu")
    s = sub.add_parser("summary")
    s.add_argument("file")
    a = ap.parse_args()
    {"run": cmd_run, "summary": cmd_summary}[a.cmd](a)


if __name__ == "__main__":
    main()
