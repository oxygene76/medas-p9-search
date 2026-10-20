#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""tools/flyby_check.py (the project lead's REBOUND check) for p9gpu.

  python tools/flyby_p9gpu.py run --planet p9 --dt 0.5 [--dmin 0.5 --vrel 0.35] --out f.json [--p9gpu build/gpu/p9gpu] [--mode cpu|gpu]
  python tools/flyby_p9gpu.py summary f.json
  python tools/flyby_p9gpu.py close --planet neptune --method substep [--dt 0.5] [--out c.json]

--method substep: p9gpu with sub-steps (docs/substeps-plan.md): the trigger
radius of the planet 4 times the radius rule at dt (Neptune: 4 x its Hill
radius 0.776 au at 0.5 yr; Planet Nine 4 x 0.5 au), the planets with 8 inner
steps (as p9job make --encounter-method substep).
"close": the very close flybys of flyby_check.py close (seed 7, 8 phases,
IAS15 with dt 0.001 as reference): signed kick ratio and spurious unbinding.

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


def method_env(method, planet_name, m, dt):
    """Environment for p9gpu: nothing (fixed step) or method substep with the rule's trigger radius."""
    if method != "substep":
        return {}
    import math as _m
    r_orbit = 0.5 * (m / (6.2 * fc.M_EARTH)) ** (1 / 3) * (dt / 0.5) ** (2 / 3)
    hill = 30.07 * (m / 3) ** (1 / 3) if planet_name == "Neptune" else 0.0
    # trigger radius: 4 times the rule's radius (p9job --trigger-factor); FLYBY_TRIGGER_FACTOR and
    # FLYBY_PLANET_SUBSTEPS override both for experiments
    r = float(os.environ.get("FLYBY_TRIGGER_FACTOR", "4")) * max(r_orbit, hill)
    return {"P9_ENCOUNTER_METHOD": "substep", "P9_ENCOUNTER_RADII": f"1={r:.4f}", "P9_PLANET_SUBSTEPS": os.environ.get("FLYBY_PLANET_SUBSTEPS", "8")}


def run_p9gpu(start, dt, nsteps, planet_name, p9gpu, p9sim, mode, extra):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        write_ic(d / "ic.txt", start, dt, planet_name)
        subprocess.run([str(p9sim), "init", str(d / "ic.txt"), str(d / "in.sa")], check=True, stdout=subprocess.DEVNULL)
        env = dict(os.environ, P9GPU_MODE=mode)
        for k in ("P9_ENCOUNTER_RADII", "P9_ENCOUNTER_METHOD", "P9_ENCOUNTER_REMOVE", "P9_J2", "P9_PLANET_SUBSTEPS", "P9_FLYBY_OUT"):
            env.pop(k, None)
        env.update(extra)
        out = subprocess.run([str(p9gpu), "run", str(d / "in.sa"), repr(nsteps * dt), "1", str(d / "out.sa")], env=env, capture_output=True, text=True)
        if out.returncode:
            sys.exit(out.stderr[-2000:])
        kv = dict(x.split("=", 1) for x in [l for l in out.stdout.splitlines() if l.startswith("result_sha256=")][-1].split())
        if int(kv["steps"]) != nsteps:
            sys.exit(f"p9gpu: {kv['steps']} steps instead of {nsteps}")
        return energy_and_h_dump(subprocess.run([str(p9sim), "dump", str(d / "out.sa"), "0"], capture_output=True, text=True, check=True).stdout), kv


def cmd_close(a):
    p = dict(fc.PRESETS[a.planet])
    p["dmin"] = a.dmin or ([0.02, 0.05, 0.1, 0.2, 0.35, 0.78] if a.planet == "neptune" else [0.02, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 7.0])
    p["vrel"] = a.vrel or ([0.6, 1.0] if a.planet == "neptune" else [0.2, 0.35, 0.5])
    m, rp, vp, bodies = fc.make_test_bodies(p, seed=7)
    name = "P9" if a.planet == "p9" else "Neptune"
    extra = method_env(a.method, name, m, a.dt)
    rows = []
    for ph in [k / 8 for k in range(8)]:
        t_start = -(p["halfwindow_yr"] + ph * a.dt)
        nsteps = int(math.ceil((2 * p["halfwindow_yr"] + ph * a.dt) / a.dt))
        sim = fc.base_sim(m, rp, vp, bodies)
        sim.integrator = "ias15"
        sim.dt = -0.001
        sim.integrate(t_start)
        start = sim.copy()
        e0 = fc.energy_and_h(start)[:, 0]
        res, kv = run_p9gpu(start, a.dt, nsteps, name, a.p9gpu, a.p9sim, a.mode, extra)
        ew = res[:, 0]
        ref = start.copy()
        ref.integrator = "ias15"
        ref.dt = 0.001
        ref.integrate(start.t + nsteps * a.dt)
        er = fc.energy_and_h(ref)[:, 0]
        for i, (d, v, _, _) in enumerate(bodies):
            rows.append(dict(d=d, v=v, ratio=float((ew[i] - e0[i]) / (er[i] - e0[i])), unbound_wh=bool(ew[i] > 0), unbound_ref=bool(er[i] > 0)))
        print(f"{a.planet} close dt={a.dt} phase={ph}: sub-steps {kv.get('sub_steps', '-')} up to n = {kv.get('sub_max', '-')}", file=sys.stderr)
    cells = collections.defaultdict(list)
    for r in rows:
        cells[(r["d"], r["v"])].append(r)
    print(f"{a.planet}  dt = {a.dt} yr  p9gpu ({a.method})   (8 step phases x 10 geometries per row)")
    print("  d_min  v_rel  flyby/dt | kick ratio: median    min     max | spuriously unbound")
    worst_med = worst_all = 0.0
    spur_total = 0
    for (d, v), c in sorted(cells.items()):
        ra = np.array([x["ratio"] for x in c])
        spur = sum(1 for x in c if x["unbound_wh"] and not x["unbound_ref"])
        spur_total += spur
        worst_med = max(worst_med, abs(np.median(ra) - 1))
        worst_all = max(worst_all, float(np.max(np.abs(ra - 1))))
        print(f"  {d:5.2f}  {v:5.2f}  {d / (v * a.dt):7.2f}  | {np.median(ra):12.4f} {ra.min():7.4f} {ra.max():7.4f} | {spur:3d} of {len(c)}")
    print(f"worst |median - 1| {worst_med:.4f}, worst |ratio - 1| {worst_all:.4f}, spuriously unbound {spur_total}")
    if a.out:
        Path(a.out).write_text(json.dumps({"rows": rows, "worst_median": worst_med, "worst_all": worst_all, "spurious": spur_total}))


def one_window(p, dt, phase, m, rp, vp, bodies, p9gpu, p9sim, mode, planet_name, extra=None):
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
        for k in ("P9_ENCOUNTER_RADII", "P9_ENCOUNTER_METHOD", "P9_ENCOUNTER_REMOVE", "P9_J2", "P9_PLANET_SUBSTEPS", "P9_FLYBY_OUT"):
            env.pop(k, None)
        env.update(extra or {})
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
            r = one_window(p, dt, ph, m, rp, vp, bodies, a.p9gpu, a.p9sim, a.mode, name, method_env(a.method, name, m, dt))
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
    r.add_argument("--method", choices=["fixed", "substep"], default="fixed")
    c = sub.add_parser("close")
    c.add_argument("--planet", choices=fc.PRESETS, default="neptune")
    c.add_argument("--dt", type=float, default=0.5)
    c.add_argument("--dmin", type=float, nargs="+")
    c.add_argument("--vrel", type=float, nargs="+")
    c.add_argument("--method", choices=["fixed", "substep"], default="substep")
    c.add_argument("--out", default=None)
    c.add_argument("--p9gpu", default=str(ROOT / "build/gpu-cpu/p9gpu"))
    c.add_argument("--p9sim", default=str(ROOT / "build/gcc-O3/p9sim"))
    c.add_argument("--mode", choices=["cpu", "gpu"], default="cpu")
    s = sub.add_parser("summary")
    s.add_argument("file")
    a = ap.parse_args()
    {"run": cmd_run, "summary": cmd_summary, "close": cmd_close}[a.cmd](a)


if __name__ == "__main__":
    main()
