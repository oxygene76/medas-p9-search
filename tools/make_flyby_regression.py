#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression cases for sub-steps: the confirmed numerical losses of docs/validation-mercurius.md.

  python tools/make_flyby_regression.py --losses runs/val/flyby-losses/flyby-losses.json --gpu runs/val/gpu-2000-count \\
      --p9sim build/gcc-O3/p9sim --p9gpu build/gpu-cpu/p9gpu --out tests/data/flyby-regression

For every loss counted as numerical: the state of the whole system (Sun,
planets, that particle) M steps before its last too short flyby, rebuilt
bit-identically from the run (tools/flyby_losses.py), written as a start file
for p9sim init with exact decimals (case-<id>.txt), and the reference: the
particle's heliocentric orbital energy and angular momentum after 2M steps
with REBOUND's IAS15 (adaptive; checked against IAS15 with a fixed step of
0.001 yr), and p9gpu's fixed-step result that failed. index.json lists the
cases. The test (tests/test_flyby_regression.py) runs p9gpu over the same
2M steps and compares.
"""

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import flyby_losses as fl  # noqa: E402


def ref(rows, G, span, fixed):
    import rebound
    sim = rebound.Simulation()
    sim.G = G
    for r in rows:
        m, x, y, z, vx, vy, vz = map(float, r[2:9])
        sim.add(m=m, x=x, y=y, z=z, vx=vx, vy=vy, vz=vz)
    sim.N_active = len(rows) - 1
    sim.testparticle_type = 0
    sim.integrator = "ias15"
    if fixed:
        sim.integrator.epsilon = 0.0
        sim.dt = 0.001
    else:
        sim.dt = 0.01
    sim.integrate(span)
    s, q = sim.particles[0], sim.particles[sim.N - 1]
    rv = np.array([q.x - s.x, q.y - s.y, q.z - s.z])
    vv = np.array([q.vx - s.vx, q.vy - s.vy, q.vz - s.vz])
    return float(0.5 * vv @ vv - G * s.m / np.linalg.norm(rv)), [float(x) for x in np.cross(rv, vv)]


def heliocentric(rows, G):
    sun = np.array([float(x) for x in rows[0][3:9]])
    tp = np.array([float(x) for x in rows[-1][3:9]]) - sun
    return float(0.5 * tp[3:] @ tp[3:] - G * float(rows[0][2]) / np.linalg.norm(tp[:3])), [float(x) for x in np.cross(tp[:3], tp[3:])]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--losses", required=True)
    ap.add_argument("--gpu", required=True)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--p9gpu", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rep = json.loads(Path(a.losses).read_text())
    cases = [r for r in rep["b"]["rows"] if r.get("numerical")]
    g = Path(a.gpu)
    _, rows = fl.header_and_rows(a.p9sim, g / "input.sa")
    head = "".join(l + "\n" for l in (g / "ic.txt").read_text().splitlines() if l and l.split()[0] in ("G", "dt", "N_active", "corrector"))
    G = float([l for l in head.splitlines() if l.startswith("G ")][0].split()[1])
    dt = float([l for l in head.splitlines() if l.startswith("dt ")][0].split()[1])
    line = lambda r: "p " + r[0] + " " + " ".join(r[2:9]) + " " + r[1]
    ctx = {"header": head, "massive": [line(r) for r in rows if not r[0].startswith("tp")], "tp": {int(r[1]): line(r) for r in rows if r[0].startswith("tp")},
           "p9sim": a.p9sim, "p9gpu": a.p9gpu, "dt": dt}
    tasks = []
    for c in cases:
        M = 1200 if c["planet"] == "P9" else 240
        S = int(round(c["flyby_myr"] * 1e6 / dt))
        tasks.append((c["id"], max(S - M, 1), S + M, ctx))
    index = []
    with ProcessPoolExecutor(a.workers) as ex:
        for (pid, states, err), task, c in zip(ex.map(fl.rebuild, tasks), tasks, cases):
            if states is None:
                sys.exit(f"{pid}: {err}")
            before, after = states
            span = (task[2] - task[1]) * dt
            E0, h0 = heliocentric(before, G)
            Eg, hg = heliocentric(after, G)
            Ei, hi = ref(before, G, span, False)
            Ef, hf = ref(before, G, span, True)
            f = out / f"case-{pid}.txt"
            with open(f, "w") as fh:
                fh.write(f"# flyby regression case: test particle {pid}, last flyby shorter than 1.5 steps at {c['planet']}, "
                         f"closest {c['dmin_au']:.4f} au, at {c['flyby_myr']:.6f} Myr of runs/val/gpu-2000-count\n")
                fh.write(f"# state {task[2] - task[1]} // 2 steps before the flyby, rebuilt bit-identically (tools/flyby_losses.py); "
                         f"window {task[2] - task[1]} steps of {dt} yr\n")
                fh.write(head)
                for r in before:
                    fh.write(line(r) + "\n")
            index.append({"id": pid, "file": f.name, "planet": c["planet"], "dmin_au": c["dmin_au"], "steps": task[2] - task[1], "dt_yr": dt,
                          "E_before": E0, "h_before": h0, "E_ias15": Ei, "h_ias15": hi, "E_ias15_fixed": Ef,
                          "ias15_agreement_rel_kick": abs(Ei - Ef) / abs(Ei - E0), "E_fixed_step_p9gpu": Eg, "kick_ratio_fixed_step": (Eg - E0) / (Ei - E0),
                          "unbound_ias15": Ei > 0, "unbound_fixed_step": Eg > 0})
            print(f"{pid}: {c['planet']} {c['dmin_au']:.4f} au, fixed-step kick ratio {(Eg - E0) / (Ei - E0):.3g}, "
                  f"IAS15 adaptive/fixed agree to {abs(Ei - Ef) / abs(Ei - E0):.1e} of the kick", file=sys.stderr)
    index.sort(key=lambda x: x["id"])
    (out / "index.json").write_text(json.dumps({"source": "docs/validation-mercurius.md, runs/val/flyby-losses", "cases": index}, indent=1) + "\n")
    print(f"{len(index)} cases -> {out}")


if __name__ == "__main__":
    main()
