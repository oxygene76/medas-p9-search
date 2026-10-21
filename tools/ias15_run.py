#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The bodies of a start file (tools/make_ic.py format) with REBOUND's IAS15, as a reference.

  python tools/ias15_run.py ic.txt T_END N_SNAPSHOTS out.npz [--epsilon 1e-9]

Massive bodies interact, test particles (mass 0) feel them only (N_active,
testparticle_type 0, as p9sim and p9gpu). Snapshots at k T_END / N, k = 1..N
(exact times). out.npz: t (N), names, ids, xv (N, bodies, 6), barycentric,
none removed (no distance rules: a reference over a short time).
"""

import argparse
import time

import numpy as np
import rebound


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ic")
    ap.add_argument("t_end", type=float)
    ap.add_argument("n", type=int)
    ap.add_argument("out")
    ap.add_argument("--epsilon", type=float, default=1e-9)
    a = ap.parse_args()
    sim = rebound.Simulation()
    names, ids, n_active = [], [], None
    for line in open(a.ic):
        f = line.split()
        if not f or f[0].startswith("#"):
            continue
        if f[0] == "G":
            sim.G = float(f[1])
        elif f[0] == "N_active":
            n_active = int(f[1])
        elif f[0] == "p":
            m, x, y, z, vx, vy, vz = map(float, f[2:9])
            sim.add(m=m, x=x, y=y, z=z, vx=vx, vy=vy, vz=vz)
            names.append(f[1])
            ids.append(int(f[9]) if len(f) > 9 else len(ids))
    sim.N_active = n_active
    sim.testparticle_type = 0
    sim.integrator = "ias15"
    sim.integrator.epsilon = a.epsilon
    sim.dt = 0.01
    t0 = time.time()
    ts, xv = [], []
    for k in range(1, a.n + 1):
        sim.integrate(a.t_end * k / a.n, exact_finish_time=1)
        ts.append(sim.t)
        xv.append([[p.x, p.y, p.z, p.vx, p.vy, p.vz] for p in sim.particles])
    np.savez(a.out, t=np.array(ts), names=np.array(names), ids=np.array(ids), xv=np.array(xv), G=sim.G)
    print(f"ias15: {len(names)} bodies, {a.n} snapshots to {a.t_end:g} yr, {sim.steps_done} steps, {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
