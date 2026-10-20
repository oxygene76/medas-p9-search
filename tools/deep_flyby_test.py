#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Deep Neptune flybys of the Jacobi test, restarted shortly before the flyby: p9gpu (smooth) with the cap of 4,096 sub-steps, with a higher cap, and IAS15.

  python tools/deep_flyby_test.py --fine DIR/fine.sa --flybys DIR/flybys.tsv --ids 57 59 147 234 \\
      --p9gpu build/gpu-cpu/p9gpu --p9gpu-cap build/exp-cap21/p9gpu [--before 1500 --after 4000] --out DIR/deep

For each test particle the snapshot of --fine (one every 1,000 steps, the run
of the 4 lost particles of runs/jacobi with the same bits) at least --before
steps before its last fast flyby (flybys.tsv): the Sun, Neptune and the
particle as a new input, integrated over --before + --after steps with p9gpu
(method smooth, radius 4 Hill radii, planets with 8 inner steps) with each of
the two programs, and with IAS15 (REBOUND, adaptive, epsilon 1e-9) as the
reference. Reported: |dC/C| (Jacobi constant, tools/jacobi_test.py) at the
end, the end distance from the Sun, and IAS15's closest approach to Neptune
(the two-body pericentre around Neptune at IAS15's step closest to it) in
Neptune radii (24,764 km).
"""

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import rebound

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import jacobi_test as jt  # noqa: E402

R_N = 24764.0 / 149597870.7


def dump(sa, k):
    out = subprocess.run([str(ROOT / "build/test/p9sim"), "dump", str(sa), str(k)], capture_output=True, text=True, check=True).stdout.splitlines()
    return float(out[0].split()[1]), [l.split() for l in out[1:]]


def p9run(binary, d, tag, t_end):
    env = dict(os.environ, P9GPU_MODE="cpu", P9_ENCOUNTER_RADII="1=3.1036", P9_PLANET_SUBSTEPS="8", P9_ENCOUNTER_METHOD="smooth",
               P9_FLYBY_OUT=str(d / f"flybys-{tag}.tsv"), P9_REMOVED_OUT=str(d / f"removed-{tag}.tsv"))
    for k in ("P9GPU_REAL", "P9_J2", "P9_ENCOUNTER_REMOVE", "P9_CAPPED_OUT"):
        env.pop(k, None)
    p = subprocess.run([binary, "run", str(d / "input.sa"), repr(t_end), "1", str(d / f"out-{tag}.sa")], env=env, capture_output=True, text=True)
    (d / f"run-{tag}.log").write_text(p.stdout + p.stderr)
    fate = [l.split("\t")[1] for l in (d / f"removed-{tag}.tsv").read_text().splitlines()[1:]][0]
    if fate != "alive":
        return None, fate
    return dump(d / f"out-{tag}.sa", 0)[1], fate


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fine", required=True)
    ap.add_argument("--flybys", required=True)
    ap.add_argument("--ids", type=int, nargs="+", required=True)
    ap.add_argument("--p9gpu", default=str(ROOT / "build/gpu-cpu/p9gpu"))
    ap.add_argument("--p9gpu-cap", required=True)
    ap.add_argument("--before", type=int, default=1500)
    ap.add_argument("--after", type=int, default=4000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    par = json.loads((ROOT / "runs/jacobi/params.json").read_text())
    fb = {int(r["id"]): r for r in csv.DictReader(open(a.flybys), delimiter="\t")}
    out = Path(a.out)
    report = []
    for i in a.ids:
        step_f = int(fb[i]["last_fast_step"])
        k = (step_f - a.before) // 1000 - 1  # snapshot k of --fine is at step (k + 1) * 1000
        t0, rows = dump(a.fine, k)
        rows = [r for r in rows if int(float(r[1])) in (0, 1, i)]
        d = out / f"p{i}"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "ic.txt", "w") as f:
            f.write(f"# particle {i} of runs/jacobi from t = {t0!r} (tools/deep_flyby_test.py)\nG {par['mu_S']!r}\ndt 0.5\nN_active 2\ncorrector 0\n")
            for r in rows:
                f.write(f"p {r[0]} {r[2]} " + " ".join(r[3:9]) + f" {r[1]}\n")
        subprocess.run([str(ROOT / "build/test/p9sim"), "init", str(d / "ic.txt"), str(d / "input.sa")], check=True, stdout=subprocess.DEVNULL)
        t_end = 0.5 * (step_f - (k + 1) * 1000 + a.after)
        C0 = jt.jacobi(rows, par)[i]
        res = {"id": i, "t_start": t0, "flyby_step_offset": step_f - (k + 1) * 1000, "t_end": t_end}
        for tag, binary in (("cap4096", a.p9gpu), ("caphigh", a.p9gpu_cap)):
            r, fate = p9run(binary, d, tag, t_end)
            if r is None:
                res[tag] = {"fate": fate}
                continue
            s = np.array([float(x) for x in r[0][3:9]])
            x = np.array([float(z) for z in r[2][3:9]])
            res[tag] = {"fate": fate, "dC_C": abs((jt.jacobi(r, par)[i] - C0) / C0), "r_sun_au": float(np.linalg.norm(x[:3] - s[:3]))}
        sim = rebound.Simulation()
        sim.G = par["mu_S"]
        for r in rows:
            sim.add(m=float(r[2]), x=float(r[3]), y=float(r[4]), z=float(r[5]), vx=float(r[6]), vy=float(r[7]), vz=float(r[8]))
        sim.N_active = 2
        sim.integrator = "ias15"
        sim.integrator.epsilon = 1e-9  # REBOUND 5
        sim.dt = 0.01
        dmin, qmin = np.inf, np.inf
        while sim.t < t_end:
            sim.steps(1)
            pn, pp = sim.particles[1], sim.particles[2]
            dx = np.array([pp.x - pn.x, pp.y - pn.y, pp.z - pn.z])
            dv = np.array([pp.vx - pn.vx, pp.vy - pn.vy, pp.vz - pn.vz])
            dd = float(np.linalg.norm(dx))
            if dd < dmin:
                mu = sim.G * pn.m
                L = np.cross(dx, dv)
                e = np.linalg.norm(np.cross(dv, L) / mu - dx / dd)
                dmin, qmin = dd, float(L @ L / mu / (1 + e))
        sim.integrate(t_end, exact_finish_time=1)
        ps = sim.particles
        r = [[None, "0", None] + [repr(v) for v in (p.x, p.y, p.z, p.vx, p.vy, p.vz)] for p in ps]
        r[2][1] = str(i)
        s = np.array([ps[0].x, ps[0].y, ps[0].z])
        res["ias15"] = {"dC_C": abs((jt.jacobi(r, par)[i] - C0) / C0), "r_sun_au": float(np.linalg.norm(np.array([ps[2].x, ps[2].y, ps[2].z]) - s)),
                        "q_neptune_au": qmin, "q_neptune_radii": qmin / R_N, "steps": int(sim.steps_done) if hasattr(sim, "steps_done") else None}
        report.append(res)
        line = f"particle {i}: IAS15 pericentre {qmin:.3e} au = {qmin / R_N:.2f} R_N, |dC/C| {res['ias15']['dC_C']:.1e}, r {res['ias15']['r_sun_au']:.1f} au"
        for tag in ("cap4096", "caphigh"):
            x = res[tag]
            line += f"; {tag}: " + (f"|dC/C| {x['dC_C']:.1e}, r {x['r_sun_au']:.1f} au" if "dC_C" in x else x["fate"])
        print(line, flush=True)
    (out / "report.json").write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
