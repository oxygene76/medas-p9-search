#!/usr/bin/env python3
"""Encounter (flyby) accuracy of a fixed-step Wisdom-Holman integrator.

Question: down to which minimum distance d_min does a fixed-step WH/DKD
integrator reproduce the kick a massless test body receives when it flies past
a planet? The kick is measured as the change of the test body's heliocentric
orbital energy E and angular momentum vector h across the encounter.

Setup (units AU, yr, Msun, G = 4 pi^2):
  * Sun + one planet on a circular orbit + massless test bodies.
  * Each test body starts at its closest approach to the planet at t = 0
    (distance d_min, relative speed v_rel perpendicular to the separation;
    random geometry, bound heliocentric orbit, optional minimum perihelion).
  * IAS15 integrates backward to t_start = -(T + phase*dt); from there the
    same state is integrated forward over the same window with
      - WHFast (Jacobi and democratic heliocentric), fixed step dt,
      - IAS15 adaptive and IAS15 with a fixed small step (reference check).
  * Error = |X_WH - X_ref| / |X_ref(end) - X(start)| for X = E and h,
    i.e. relative to the size of the kick. 10 geometries x 4 phases of the
    step grid relative to closest approach x 2 coordinate systems per cell.

Presets:  --planet p9       6.2 Earth masses at 400 AU, window +-300 yr
          --planet neptune  17.15 Earth masses at 30.07 AU, window +-60 yr,
                            test bodies with perihelion >= 20 AU
Usage:    python3 flyby_check.py run --planet p9 --dt 0.5 5 --out p9.json
          python3 flyby_check.py run --planet p9 --dt 5 --dmin 2.32 --vrel 0.2 0.35 0.5 --out x.json
          python3 flyby_check.py summary p9.json
          python3 flyby_check.py close --planet neptune --dt 0.5
            (very close flybys: signed kick ratio and spurious unbinding)

Result with REBOUND 5.2.2 (19.10.2026), short form:
  * If the flyby lasts at least two steps (d_min / (v_rel * dt) >= 2), the
    kick error is ~ 4 * (dt / T_orb)^2, with T_orb the orbital period around
    the planet at d_min. Keeping T_orb/dt fixed (164 steps) keeps the error at
    ~1.5e-4 of the kick (P9 at 0.5 AU, dt = 0.5 yr; Neptune at its Hill
    radius 0.78 AU: ~1.1e-4).
  * At ~1.5 steps per flyby the median error is still <= ~2e-3 (worst cases
    a few percent); below that it grows quickly to percent and >100 % of the
    kick, independent of the orbital-period criterion.
  * Hence: r_remove >= max(Hill radius, r_orbit(dt), 1.5 * v99 * dt), with v99
    the 99th percentile of encounter speeds at that planet.
  * Jacobi and democratic heliocentric coordinates give the same errors.
  * Very close Neptune flybys at dt = 0.5 yr ("close"): below ~0.1 AU the WH
    kick ranges from about -136 to +171 times the true kick and 3-15 % of the
    test bodies end spuriously unbound; at 0.35 AU the ratio is 0.4-1.6, at
    0.78 AU 1.00. Without removal such flybys need sub-steps.
Port this test to p9gpu (same initial states, same metrics) before relying on
these numbers for p9gpu itself.
"""
import argparse
import collections
import json
import math
import sys
import time

import numpy as np
import rebound

G = 4 * math.pi ** 2
M_EARTH = 3.0035e-6

PRESETS = {
    "p9": dict(mass_earth=6.2, orbit_au=400.0, halfwindow_yr=300.0,
               dmin=[0.25, 0.5, 1.0, 2.0, 3.5, 7.0, 15.0, 50.0],
               vrel=[0.1, 0.2, 0.35, 0.5], bound=0.9, qmin=0.0),
    "neptune": dict(mass_earth=17.15, orbit_au=30.07, halfwindow_yr=60.0,
                    dmin=[0.5, 0.78, 1.0, 1.5, 2.0, 3.26, 5.0],
                    vrel=[0.4, 0.6, 0.8, 1.0, 1.2], bound=0.98, qmin=20.0),
}
N_GEOMETRIES = 10
PHASES = [0.0, 0.25, 0.5, 0.75]
COORDS = ["jacobi", "democraticheliocentric"]


def set_whfast_coordinates(sim, coords):
    try:
        sim.integrator.coordinates = coords      # REBOUND >= 5
    except AttributeError:
        sim.ri_whfast.coordinates = coords       # REBOUND 4


def do_steps(sim, n):
    """Exactly n fixed steps (older REBOUND versions have no sim.steps)."""
    if hasattr(sim, "steps"):
        sim.steps(n)
    else:
        for _ in range(n):
            sim.step()


def set_ias15_epsilon(sim, eps):
    try:
        sim.integrator.epsilon = eps             # REBOUND >= 5
    except AttributeError:
        sim.ri_ias15.epsilon = eps               # REBOUND 4


def make_test_bodies(p, seed=1):
    rng = np.random.default_rng(seed)
    m = p["mass_earth"] * M_EARTH
    a_pl = p["orbit_au"]
    vc = math.sqrt(G * (1 + m) / a_pl)
    rp = np.array([a_pl, 0.0, 0.0])
    vp = np.array([0.0, vc, 0.0])
    bodies = []
    for d in p["dmin"]:
        for v in p["vrel"]:
            if v < 1.2 * math.sqrt(2 * G * m / d):   # skip (nearly) bound captures
                continue
            k = 0
            while k < N_GEOMETRIES:
                n = rng.normal(size=3); n /= np.linalg.norm(n)
                u = rng.normal(size=3); u -= u.dot(n) * n; u /= np.linalg.norm(u)
                x = rp + d * n
                w = vp + v * u
                r = np.linalg.norm(x); w2 = w.dot(w)
                if w2 >= p["bound"] * 2 * G / r:
                    continue
                a = 1.0 / (2.0 / r - w2 / G)
                h = np.cross(x, w)
                e = math.sqrt(max(0.0, 1 - h.dot(h) / G / a))
                if a * (1 - e) < p["qmin"]:
                    continue
                bodies.append((d, v, x, w)); k += 1
    return m, rp, vp, bodies


def base_sim(m, rp, vp, bodies):
    sim = rebound.Simulation()
    sim.G = G
    sim.add(m=1.0)
    sim.add(m=m, x=rp[0], y=rp[1], z=rp[2], vx=vp[0], vy=vp[1], vz=vp[2])
    for (_, _, x, w) in bodies:
        sim.add(m=0.0, x=x[0], y=x[1], z=x[2], vx=w[0], vy=w[1], vz=w[2])
    sim.N_active = 2
    sim.testparticle_type = 0
    sim.move_to_com()
    return sim


def energy_and_h(sim):
    """Heliocentric specific orbital energy and angular momentum of test bodies."""
    ps = sim.particles
    s = ps[0]
    out = []
    for i in range(2, sim.N):
        q = ps[i]
        r = np.array([q.x - s.x, q.y - s.y, q.z - s.z])
        v = np.array([q.vx - s.vx, q.vy - s.vy, q.vz - s.vz])
        h = np.cross(r, v)
        out.append((0.5 * v.dot(v) - G / np.linalg.norm(r), h[0], h[1], h[2]))
    return np.array(out)


def one_window(p, dt, phase, m, rp, vp, bodies):
    t_start = -(p["halfwindow_yr"] + phase * dt)
    nsteps = int(math.ceil((2 * p["halfwindow_yr"] + phase * dt) / dt))
    sim = base_sim(m, rp, vp, bodies)
    sim.integrator = "ias15"
    sim.dt = -0.01
    sim.integrate(t_start)
    start = sim.copy()
    res = {"start": energy_and_h(start)}
    for c in COORDS:
        wh = start.copy()
        wh.integrator = "whfast"
        set_whfast_coordinates(wh, c)
        wh.dt = dt
        do_steps(wh, nsteps)
        wh.synchronize()
        res[c] = energy_and_h(wh)
        t_end = wh.t
    ref = start.copy(); ref.integrator = "ias15"; ref.dt = 0.01
    ref.integrate(t_end)
    res["ref_adaptive"] = energy_and_h(ref)
    ref2 = start.copy(); ref2.integrator = "ias15"; set_ias15_epsilon(ref2, 0.0); ref2.dt = 0.02
    ref2.integrate(t_end)
    res["ref_fixed"] = energy_and_h(ref2)
    return res


def cmd_run(args):
    p = dict(PRESETS[args.planet])
    if args.dmin: p["dmin"] = args.dmin
    if args.vrel: p["vrel"] = args.vrel
    m, rp, vp, bodies = make_test_bodies(p)
    rows = []
    for dt in args.dt:
        for ph in PHASES:
            t0 = time.time()
            r = one_window(p, dt, ph, m, rp, vp, bodies)
            s, ref = r["start"], r["ref_fixed"]
            kick_e = np.abs(ref[:, 0] - s[:, 0])
            kick_h = np.linalg.norm(ref[:, 1:4] - s[:, 1:4], axis=1)
            ref_check = np.maximum(np.abs(r["ref_adaptive"][:, 0] - ref[:, 0]) / kick_e,
                                   np.linalg.norm(r["ref_adaptive"][:, 1:4] - ref[:, 1:4], axis=1) / kick_h)
            for c in COORDS:
                w = r[c]
                for i, (d, v, _, _) in enumerate(bodies):
                    rows.append(dict(planet=args.planet, dt=dt, phase=ph, coords=c, dmin=d, vrel=v,
                                     err_E=float(abs(w[i, 0] - ref[i, 0]) / kick_e[i]),
                                     err_h=float(np.linalg.norm(w[i, 1:4] - ref[i, 1:4]) / kick_h[i]),
                                     kick_E_rel=float(kick_e[i] / (G / p["orbit_au"])),
                                     ref_check=float(ref_check[i])))
            print(f"{args.planet} dt={dt} phase={ph}: {time.time() - t0:.1f} s, "
                  f"reference agreement (max, rel. to kick) {ref_check.max():.1e}", file=sys.stderr)
    with open(args.out, "w") as f:
        json.dump(rows, f)


def cmd_summary(args):
    rows = json.load(open(args.file))
    cells = collections.defaultdict(list)
    for r in rows:
        cells[(r["dt"], r["dmin"], r["vrel"])].append(r)
    print("max reference disagreement (rel. to kick):", f"{max(r['ref_check'] for r in rows):.1e}")
    for dt in sorted({r["dt"] for r in rows}):
        print(f"\n{rows[0]['planet']}  dt = {dt} yr   (error relative to the kick, median / max)")
        print("  d_min  v_rel  flyby/dt |   E med    E max |   h med    h max")
        for d in sorted({r["dmin"] for r in rows}):
            for v in sorted({r["vrel"] for r in rows}):
                c = cells.get((dt, d, v))
                if not c:
                    continue
                e = np.array([x["err_E"] for x in c]); h = np.array([x["err_h"] for x in c])
                print(f"  {d:5.2f}  {v:5.2f}  {d / (v * dt):7.2f}  | {np.median(e):8.1e} {e.max():8.1e} |"
                      f" {np.median(h):8.1e} {h.max():8.1e}")


def cmd_close(args):
    """Very close flybys: signed ratio of the WH kick to the true kick and
    spurious unbinding (WH ends unbound, reference stays bound)."""
    p = dict(PRESETS[args.planet])
    p["dmin"] = args.dmin or [0.02, 0.05, 0.1, 0.2, 0.35, 0.78]
    p["vrel"] = args.vrel or [0.6, 1.0]
    m, rp, vp, bodies = make_test_bodies(p, seed=7)
    dt = args.dt
    rows = []
    for ph in [k / 8 for k in range(8)]:
        t_start = -(p["halfwindow_yr"] + ph * dt)
        nsteps = int(math.ceil((2 * p["halfwindow_yr"] + ph * dt) / dt))
        sim = base_sim(m, rp, vp, bodies)
        sim.integrator = "ias15"; sim.dt = -0.001
        sim.integrate(t_start)
        start = sim.copy()
        e0 = energy_and_h(start)[:, 0]
        wh = start.copy(); wh.integrator = "whfast"; set_whfast_coordinates(wh, "democraticheliocentric")
        wh.dt = dt; do_steps(wh, nsteps); wh.synchronize()
        ew = energy_and_h(wh)[:, 0]
        ref = start.copy(); ref.integrator = "ias15"; ref.dt = 0.001; ref.integrate(wh.t)
        er = energy_and_h(ref)[:, 0]
        ref2 = start.copy(); ref2.integrator = "ias15"; set_ias15_epsilon(ref2, 0.0); ref2.dt = 0.0005
        ref2.integrate(wh.t)
        er2 = energy_and_h(ref2)[:, 0]
        for i, (d, v, _, _) in enumerate(bodies):
            rows.append(dict(d=d, v=v, ratio=(ew[i] - e0[i]) / (er[i] - e0[i]),
                             unbound_wh=bool(ew[i] > 0), unbound_ref=bool(er[i] > 0),
                             ref_check=abs(er[i] - er2[i]) / abs(er[i] - e0[i])))
        print(f"{args.planet} close flybys dt={dt} phase={ph} done", file=sys.stderr)
    cells = collections.defaultdict(list)
    for r in rows:
        cells[(r["d"], r["v"])].append(r)
    print("max reference disagreement (rel. to kick):", f"{max(r['ref_check'] for r in rows):.1e}")
    print(f"\n{args.planet}  dt = {dt} yr   (8 step phases x 10 geometries per row)")
    print("  d_min  v_rel  flyby/dt | WH kick / true kick: median    min     max | spuriously unbound")
    for (d, v), c in sorted(cells.items()):
        ra = np.array([x["ratio"] for x in c])
        spur = sum(1 for x in c if x["unbound_wh"] and not x["unbound_ref"])
        print(f"  {d:5.2f}  {v:5.2f}  {d / (v * dt):7.2f}  | {np.median(ra):17.2f} {ra.min():7.2f} {ra.max():7.2f} |"
              f" {spur:3d} of {len(c)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("run"); a.add_argument("--planet", choices=PRESETS, default="p9")
    a.add_argument("--dt", type=float, nargs="+", default=[0.5, 5.0]); a.add_argument("--out", required=True)
    a.add_argument("--dmin", type=float, nargs="+", help="override the preset's closest-approach distances (AU)")
    a.add_argument("--vrel", type=float, nargs="+", help="override the preset's relative speeds (AU/yr)")
    b = sub.add_parser("summary"); b.add_argument("file")
    c = sub.add_parser("close", help="very close flybys: kick ratio and spurious unbinding")
    c.add_argument("--planet", choices=PRESETS, default="neptune")
    c.add_argument("--dt", type=float, default=0.5)
    c.add_argument("--dmin", type=float, nargs="+"); c.add_argument("--vrel", type=float, nargs="+")
    args = ap.parse_args()
    {"run": cmd_run, "summary": cmd_summary, "close": cmd_close}[args.cmd](args)


if __name__ == "__main__":
    main()
