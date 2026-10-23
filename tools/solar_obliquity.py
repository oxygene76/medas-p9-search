#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Solar obliquity from Planet Nine: the tilt of the planets' plane against a fixed solar spin axis.

Secular model of Lai (2016, arXiv:1608.01421, eqs. 1-5), as in Bailey, Batygin & Brown (2016,
arXiv:1607.03963) without the solar spin's own precession: the planets are strongly coupled and keep one
common plane (unit angular momentum l, total L); Planet Nine's orbit (l_p, L_p) is far outside
(quadrupole, orbit-averaged, semi-major axes fixed). Both precess about J = L + L_p, the mutual inclination
theta_p stays constant:
  dl/dt   =  Omega_L cos(theta_p) (l x l_p)
  dl_p/dt = (L / L_p) Omega_L cos(theta_p) (l_p x l)
  Omega_L = sum_j L_j Omega_jp / L,  Omega_jp = (3 m_p / 4 M) (a_j / a~_p)^3 n_j,  a~_p = a_p sqrt(1 - e_p^2)
The solar spin S is fixed (default) and parallel to l at t = 0; the obliquity is the angle between S and
l(t). Optional (--spin-days P/lambda, Lai eqs. 6-8): S precesses about l at Omega_ps cos(theta_sl),
Omega_ps = 2 pi / 55.8 Gyr (P/lambda / 10 d)^-1; for comparison with Lai's figures only.

  python tools/solar_obliquity.py secular --p9 10,500,0.6,30 [--p9 ...] [--t-gyr 4.5] [--planets all|giants]
          per candidate (mass in Earth masses, a in au, e, mutual inclination in degrees): the obliquity today
          (after t), Delta Omega (node of Planet Nine's orbit minus node of the solar equator, both on the
          planets' plane), the largest obliquity on the way, the precession period
  python tools/solar_obliquity.py check
          the model against the numbers of Lai (2016) and Bailey, Batygin & Brown (2016)
  python tools/solar_obliquity.py nbody-ic --p9 m,a,e,i --out ic.txt [--reverse]
          start file for p9gpu/p9sim: the Sun (with the inner planets), Jupiter-Neptune (tools/make_ic.py) and
          Planet Nine with these elements relative to the giant planets' plane; --reverse flips all velocities
          (a forward run of the reversed state is the backward run of the original)
  python tools/solar_obliquity.py snapshots --run DIR [--every 20]
          side metric of a run (reported, decides nothing): the tilt of the four giants' common plane against its
          direction at t = 0, from the planets in the snapshots (a p9job job or chain, or a package job), with the
          secular value for the same geometry
  python tools/solar_obliquity.py nbody-eval --ic ic.txt --out output.sa [--p9sim build/gcc-O3/p9sim]
          the angle between the giant planets' total angular momentum at each snapshot and at t = 0 (the
          obliquity against a solar axis that is parallel at t = 0), against the secular model for the
          same bodies and geometry
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "tools")

G = 4 * math.pi ** 2  # au^3 / (M_sun yr^2)
M_EARTH = 3.003489596e-6  # M_sun (tools/make_ic.py)
# masses (M_sun) and semi-major axes (au); the giants as in tools/make_ic.py, the inner planets for "all"
PLANETS = {
    "Mercury": (1.6601e-7, 0.38710), "Venus": (2.44781e-6, 0.72333), "Earth": (3.04043e-6, 1.00000), "Mars": (3.22715e-7, 1.52368),
    "Jupiter": (1 / 1047.348644, 5.20336), "Saturn": (1 / 3497.9018, 9.53707), "Uranus": (1 / 22902.951, 19.19126),
    "Neptune": (1 / 19412.26, 30.06896),
}
GIANTS = ["Jupiter", "Saturn", "Uranus", "Neptune"]
GYR = 1e9


def planet_set(which):
    names = GIANTS if which == "giants" else list(PLANETS)
    return [PLANETS[n] for n in names]


def rates(m9_earth, a9, e9, planets, msun=1.0):
    """L (planets), L_p (Planet Nine), Omega_L (rad/yr), per Lai (2016) eqs. 1-5 (circular planets)."""
    m9 = m9_earth * M_EARTH
    at = a9 * math.sqrt(1 - e9 * e9)
    L = sum(m * math.sqrt(G * msun * a) for m, a in planets)
    Lp = m9 * math.sqrt(G * msun * a9 * (1 - e9 * e9))
    om = sum(m * math.sqrt(G * msun * a) * 0.75 * (m9 / msun) * (a / at) ** 3 * math.sqrt(G * msun / a ** 3) for m, a in planets) / L
    return L, Lp, om


def unit(v):
    return v / np.linalg.norm(v)


def node_angle(l, n_a, n_b):
    """Delta Omega: azimuth of the node of plane b minus that of plane a, both on the plane with normal l."""
    na, nb = np.cross(l, n_a), np.cross(l, n_b)
    if np.linalg.norm(na) < 1e-15 or np.linalg.norm(nb) < 1e-15:
        return float("nan")
    na, nb = unit(na), unit(nb)
    return math.degrees(math.atan2(np.dot(l, np.cross(na, nb)), np.dot(na, nb)))


def evolve(L, Lp, om, inc_deg, t_end, spin_days=math.inf, n=20000, l0=None, lp0=None):
    """Integrate l, l_p and S (RK4, renormalised); returns times (yr), obliquity (deg), Delta Omega (deg)."""
    i = math.radians(inc_deg)
    l = np.array([0.0, 0.0, 1.0]) if l0 is None else unit(np.asarray(l0, float))
    lp = np.array([math.sin(i), 0.0, math.cos(i)]) if lp0 is None else unit(np.asarray(lp0, float))
    S = l.copy()
    ops = 0.0 if math.isinf(spin_days) else 2 * math.pi / (55.8 * GYR) * (10.0 / spin_days)

    def f(y):
        l, lp, S = y[0:3], y[3:6], y[6:9]
        c = np.dot(l, lp)
        return np.concatenate([om * c * np.cross(l, lp), (L / Lp) * om * c * np.cross(lp, l), ops * np.dot(S, l) * np.cross(S, l)])

    y = np.concatenate([l, lp, S])
    h = t_end / n
    ts, obl, dom = [0.0], [0.0], [float("nan")]
    for k in range(n):
        k1 = f(y); k2 = f(y + 0.5 * h * k1); k3 = f(y + 0.5 * h * k2); k4 = f(y + h * k3)
        y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        y = np.concatenate([unit(y[0:3]), unit(y[3:6]), unit(y[6:9])])
        ts.append((k + 1) * h)
        obl.append(math.degrees(math.acos(min(1.0, max(-1.0, np.dot(y[0:3], y[6:9]))))))
        dom.append(node_angle(y[0:3], y[6:9], y[3:6]))
    return np.array(ts), np.array(obl), np.array(dom)


def analytic_fixed(L, Lp, om, inc_deg, t):
    """Fixed spin, exact for the rigid precession: l rotates about J by w t at the cone angle beta."""
    th = math.radians(inc_deg)
    J = math.sqrt(L * L + Lp * Lp + 2 * L * Lp * math.cos(th))
    beta = math.asin(Lp * math.sin(th) / J)
    w = om * math.cos(th) * J / Lp
    return np.degrees(2 * np.arcsin(np.sin(beta) * np.abs(np.sin(w * np.asarray(t) / 2)))), 2 * math.pi / abs(w)


def lai_analytic(L, Lp, om, inc_deg, t, spin_days=math.inf):
    """Lai (2016) eqs. 12-16 (small obliquity): theta_sl = |2 Omega_y / Omega_z sin(Omega_z t / 2)|."""
    th = math.radians(inc_deg)
    ops = 0.0 if math.isinf(spin_days) else 2 * math.pi / (55.8 * GYR) * (10.0 / spin_days)
    oy = om * math.sin(th) * math.cos(th)
    oz = ops - om * math.cos(th) * (L / Lp + math.cos(th))
    return math.degrees(abs(2 * oy / oz * math.sin(oz * t / 2)))


def parse_p9(s):
    m, a, e, i = (float(x) for x in s.split(","))
    return m, a, e, i


def cmd_secular(a):
    planets = planet_set(a.planets)
    t = a.t_gyr * GYR
    print(f"secular model (Lai 2016), planets: {a.planets}, solar axis: {'fixed' if math.isinf(a.spin_days) else f'precessing, P/lambda {a.spin_days} d'}, "
          f"parallel to the planets' plane at t = 0; after {a.t_gyr} Gyr")
    print(" m_p [M_E]   a_p [au]   e_p   i_p [deg] | obliquity [deg]  Delta Omega [deg]  max on the way [deg] | precession period [Gyr]")
    for s in a.p9:
        m, a9, e9, inc = parse_p9(s)
        L, Lp, om = rates(m, a9, e9, planets)
        ts, obl, dom = evolve(L, Lp, om, inc, t, a.spin_days)
        _, per = analytic_fixed(L, Lp, om, inc, t)
        print(f"{m:9.1f} {a9:10.0f} {e9:5.2f} {inc:9.1f}  | {obl[-1]:15.2f} {dom[-1]:18.1f} {obl.max():21.2f} | {per / GYR:10.2f}")


def cmd_check(a):
    ok = True

    def report(name, got, want, tol):
        nonlocal ok
        good = abs(got - want) <= tol
        ok &= good
        print(f"{'OK ' if good else 'BAD'} {name}: {got:.4g} (expected {want:.4g} +- {tol:.2g})")

    allp = planet_set("all")
    LJ = PLANETS["Jupiter"][0] * math.sqrt(G * PLANETS["Jupiter"][1])
    # Lai eq. 1 and 5: normalisations
    L, Lp, om = rates(10, 400 / math.sqrt(1 - 0.0), 0.0, allp)
    report("Lai: L / L_J (Mercury-Neptune)", L / LJ, 1.624, 0.005)
    report("Lai eq. 1: L_p / L_J (10 M_E, a~ 400 au, e 0)", Lp / LJ, 0.276, 0.003)
    report("Lai eq. 5: 2 pi / Omega_L [Gyr] (10 M_E, a~ 400 au)", 2 * math.pi / om / GYR, 87.5, 0.6)
    Ljp = 0.75 * 10 * M_EARTH * (PLANETS["Jupiter"][1] / 400) ** 3 * math.sqrt(G / PLANETS["Jupiter"][1] ** 3)
    report("Lai eq. 5: Omega_L / Omega_Jp", om / Ljp, 2.74, 0.02)
    # e enters only through a~ (Omega_L) and L_p (eq. 1): same a~, e 0.6
    L6, Lp6, om6 = rates(10, 400 / math.sqrt(1 - 0.36), 0.6, allp)
    report("Lai eq. 1: L_p / L_J (10 M_E, a~ 400 au, e 0.6) = 0.276 (1 - e^2)^(1/4)", Lp6 / LJ, 0.276 * 0.64 ** 0.25, 0.003)
    report("Omega_L depends on a~ only", om6 / om, 1.0, 1e-9)
    # numerical integration against the exact rigid precession and Lai's small-angle formula (fixed spin)
    for m, a9, e9, inc in ((10, 500, 0.6, 30), (15, 500, 0.5, 20), (20, 700, 0.6, 15)):
        L, Lp, om = rates(m, a9, e9, allp)
        ts, obl, _ = evolve(L, Lp, om, inc, 4.5 * GYR)
        ex, _ = analytic_fixed(L, Lp, om, inc, ts)
        report(f"RK4 against the exact precession ({m}, {a9}, {e9}, {inc}): largest difference [deg]", float(np.max(np.abs(obl - ex))), 0.0, 1e-6)
        report(f"Lai eqs. 12-16 (small angle) ({m}, {a9}, {e9}, {inc}) [deg]", lai_analytic(L, Lp, om, inc, 4.5 * GYR), obl[-1], 0.1 * obl[-1] + 0.05)
    # Lai eqs. 17-18, fixed spin (P/lambda -> infinity): for m_p, theta_p and Delta Omega = 45 deg they give a~ and L / L_p,
    # i.e. a and e; the model must then give about 6 deg and Delta Omega about 45 deg after 4.5 Gyr
    for m, thp in ((20, 20.0), (20, 25.0), (30, 15.0)):
        dO = math.radians(45)
        f = abs((math.pi / 2 - dO) / math.cos(dO))
        g = (math.pi / 2 - dO) / (math.pi / 4)
        at = 462 * (m / 10 * math.sin(2 * math.radians(thp)) / f) ** (1 / 3)
        LoLp = 15 * g * math.sin(math.radians(thp)) / f - math.cos(math.radians(thp))
        Lp_need = 1.624 * LJ / LoLp
        q4 = Lp_need / (0.276 * LJ * (m / 10) * math.sqrt(at / 400))  # (1 - e^2)^(1/4)
        if not 0 < q4 <= 1:
            print(f"    Lai eqs. 17-18 ({m} M_E, theta_p {thp}): no orbit (1 - e^2)^(1/4) = {q4:.3f}")
            continue
        e9 = math.sqrt(1 - q4 ** 4)
        a9 = at / math.sqrt(1 - e9 * e9)
        L, Lp, om = rates(m, a9, e9, allp)
        ts, obl, dom = evolve(L, Lp, om, thp, 4.5 * GYR)
        print(f"    Lai eqs. 17-18: {m} M_E, theta_p {thp} deg, Delta Omega 45 deg -> a~ {at:.0f} au, a {a9:.0f} au, e {e9:.3f}")
        report(f"  obliquity after 4.5 Gyr for it [deg]", obl[-1], 6.0, 0.6)
        report(f"  Delta Omega after 4.5 Gyr for it [deg]", abs(dom[-1]), 45.0, 6.0)
    # Bailey, Batygin & Brown (2016): their model also lets the solar spin precess (solar J2 with a spin-down);
    # with a fixed axis the numbers are not expected to agree exactly. For information:
    print("    Bailey, Batygin & Brown (2016), for information (their solar axis precesses, here fixed):")
    for (m, a9, e9, inc), theirs in (((10, 700, 0.6, 30), "3-5 deg (Batygin & Brown 2016 case, their sec. 3)"),
                                     ((15, 500, 0.5, 20), "about 6 deg today from 1-6 deg at the start (their Fig. 4, backward)")):
        for spin in (math.inf, 24.0):
            L, Lp, om = rates(m, a9, e9, allp)
            ts, obl, dom = evolve(L, Lp, om, inc, 4.5 * GYR, spin)
            print(f"      {m} M_E, {a9} au, e {e9}, i {inc}: {obl[-1]:.2f} deg, Delta Omega {dom[-1]:.0f} deg "
                  f"({'fixed axis' if math.isinf(spin) else 'axis precessing, P/lambda 24 d'}); theirs: {theirs}")
    print("== ALL OK" if ok else "== DIFFERENCES")
    sys.exit(0 if ok else 1)


def build_ic(m9_earth, a9, e9, inc_deg, reverse=False):
    import make_ic as mi
    bodies = mi.planets()  # the Sun (with the inner planets), Jupiter-Neptune, ecliptic frame, heliocentric-barycentric
    sun = bodies[0]
    Lg = sum(m * np.cross(p - sun[2], v - sun[3]) for _, m, p, v in bodies[1:])
    z = unit(Lg)
    x = unit(np.cross([0.0, 0.0, 1.0], z)) if abs(z[2]) < 1 else np.array([1.0, 0.0, 0.0])
    y = np.cross(z, x)
    R = np.array([x, y, z]).T  # columns: the giants' plane frame in ecliptic coordinates
    m9 = m9_earth * M_EARTH
    p, v = mi.elements_to_state(mi.G * (sun[1] + m9), np.array([a9]), np.array([e9]), np.array([math.radians(inc_deg)]),
                                np.array([0.0]), np.array([math.radians(150.0)]), np.array([math.radians(180.0)]))
    bodies.append(("P9", m9, sun[2] + R @ p[0], sun[3] + R @ v[0]))
    mtot = sum(b[1] for b in bodies)
    cp = sum(b[1] * b[2] for b in bodies) / mtot
    cv = sum(b[1] * b[3] for b in bodies) / mtot
    s = -1.0 if reverse else 1.0
    return [(n, m, pp - cp, s * (vv - cv), k) for k, (n, m, pp, vv) in enumerate(bodies)]


def cmd_nbody_ic(a):
    import make_ic as mi
    m, a9, e9, inc = parse_p9(a.p9)
    rows = build_ic(m, a9, e9, inc, a.reverse)
    with open(a.out, "w") as f:
        f.write(f"# planets and Planet Nine only (tools/solar_obliquity.py nbody-ic --p9 {a.p9}{' --reverse' if a.reverse else ''}); "
                "values are Python repr (exact)\n")
        f.write(f"# Planet Nine: {m} Earth masses, a {a9} au, e {e9}, inclination {inc} deg to the giant planets' plane"
                + ("; all velocities reversed (a forward run is the backward run)" if a.reverse else "") + "\n")
        f.write(f"G {mi.G!r}\ndt {a.dt!r}\nN_active {len(rows)}\ncorrector 0\n")
        for name, mm, p, v, pid in rows:
            f.write("p " + name + " " + " ".join(repr(float(x)) for x in [mm, *p, *v]) + f" {pid}\n")
    print(f"{a.out}: {len(rows)} bodies")


def read_ic(path):
    rows = []
    for line in open(path):
        f = line.split()
        if f and f[0] == "p":
            rows.append((f[1], float(f[2]), np.array(list(map(float, f[3:6]))), np.array(list(map(float, f[6:9])))))
    return rows


def ang_mom(rows):
    """Total orbital angular momentum of the giants (heliocentric) and of Planet Nine."""
    sun = next(r for r in rows if r[0] == "Sun")
    Lg = sum(m * np.cross(p - sun[2], v - sun[3]) for n, m, p, v in rows if n in GIANTS)
    p9 = next(r for r in rows if r[0] == "P9")
    return Lg, p9[1] * np.cross(p9[2] - sun[2], p9[3] - sun[3])


def cmd_nbody_eval(a):
    from analyze import dump
    ic = read_ic(a.ic)
    Lg0, L90 = ang_mom(ic)
    msun = next(r[1] for r in ic if r[0] == "Sun")
    inc0 = math.degrees(math.acos(np.dot(unit(Lg0), unit(L90))))
    # the secular model for the same bodies: giants with their present semi-major axes, Planet Nine's osculating elements
    sun = next(r for r in ic if r[0] == "Sun")
    p9 = next(r for r in ic if r[0] == "P9")
    rr, vv = p9[2] - sun[2], p9[3] - sun[3]
    mu = G * (msun + p9[1])
    a9 = 1 / (2 / np.linalg.norm(rr) - vv @ vv / mu)
    e9 = math.sqrt(max(0.0, 1 - np.linalg.norm(np.cross(rr, vv)) ** 2 / (mu * a9)))
    L, Lp, om = rates(p9[1] / M_EARTH, a9, e9, planet_set("giants"), msun)
    print(f"Planet Nine: {p9[1] / M_EARTH:.2f} M_E, a {a9:.1f} au, e {e9:.4f}, inclination to the giants' plane {inc0:.3f} deg; "
          f"secular period {analytic_fixed(L, Lp, om, inc0, 0.0)[1] / GYR:.3f} Gyr")
    print("  t [Myr] | obliquity N-body [deg]  secular [deg] | inclination of Planet Nine [deg] | a_P9 [au]")
    k = 0
    worst = 0.0
    while True:
        try:
            t, rows = dump(a.p9sim, a.out, k)
        except Exception:
            break
        rows = [(nm, m, np.asarray(p), np.asarray(v)) for nm, m, p, v in rows]
        Lg, L9 = ang_mom(rows)
        obl = math.degrees(math.acos(min(1.0, max(-1.0, np.dot(unit(Lg), unit(Lg0))))))
        sec, _ = analytic_fixed(L, Lp, om, inc0, abs(t))
        inc = math.degrees(math.acos(np.dot(unit(Lg), unit(L9))))
        s9 = next(r for r in rows if r[0] == "Sun"); q9 = next(r for r in rows if r[0] == "P9")
        r9, v9 = q9[2] - s9[2], q9[3] - s9[3]
        a9t = 1 / (2 / np.linalg.norm(r9) - v9 @ v9 / mu)
        worst = max(worst, abs(obl - float(sec)))
        if k % a.every == 0:
            print(f"{abs(t) / 1e6:9.0f} | {obl:22.3f} {float(sec):14.3f} | {inc:32.3f} | {a9t:8.2f}")
        k += 1
    print(f"snapshots: {k}; largest difference N-body - secular: {worst:.3f} deg")


def run_snapshots(run):
    """The snapshot files of a run in time order: [(output.sa, index, t)] and the start file. Layouts: a p9job job
    (job.json in the directory), a p9job chain (seg* with job.json), a package job (params.env, segments/segNNN)."""
    import json
    run = Path(run)
    if (run / "params.env").exists():
        env = dict(l.split("=", 1) for l in (run / "params.env").read_text().splitlines() if "=" in l and not l.startswith("#"))
        seg_yr, per, nseg = float(env["SEGMENT_YR"]), int(env["SNAPSHOTS_PER_SEGMENT"]), int(env["SEGMENTS"])
        segs = [(run / "segments" / f"seg{k:03d}", k * seg_yr, (k + 1) * seg_yr, per) for k in range(nseg)]
        segs = [x for x in segs if (x[0] / "DONE").exists()]
        start = run / "input.sa"
    else:
        dirs = [run] if (run / "job.json").exists() else sorted(run.glob("seg*"))
        segs = []
        for d in dirs:
            if not (d / "result.json").exists():
                continue
            q = json.loads((d / "job.json").read_text())["params"]
            segs.append((d, float(q["t_start_yr"]), float(q["t_end_yr"]), int(q["snapshots"])))
        start = dirs[0] / "input.sa"
    out = []
    for d, t0, t1, n in segs:
        out += [(d / "output.sa", k, t0 + (t1 - t0) * (k + 1) / n) for k in range(n)]
    return out, start


def cmd_snapshots(a):
    """Side metric (reported, decides nothing): tilt of the four giants' common plane (total orbital angular
    momentum, heliocentric, without Planet Nine) against its direction at t = 0, from the planets in the snapshots."""
    from analyze import dump
    snaps, start = run_snapshots(a.run)
    _, rows0 = dump(a.p9sim, start, 0)
    rows0 = [(n, m, np.asarray(p), np.asarray(v)) for n, m, p, v in rows0 if not n.startswith("tp")]
    Lg0, L90 = ang_mom(rows0)
    sun = next(r for r in rows0 if r[0] == "Sun"); p9 = next(r for r in rows0 if r[0] == "P9")
    rr, vv = p9[2] - sun[2], p9[3] - sun[3]
    mu = G * (sun[1] + p9[1])
    a9 = 1 / (2 / np.linalg.norm(rr) - vv @ vv / mu)
    e9 = math.sqrt(max(0.0, 1 - np.linalg.norm(np.cross(rr, vv)) ** 2 / (mu * a9)))
    inc0 = math.degrees(math.acos(np.dot(unit(Lg0), unit(L90))))
    L, Lp, om = rates(p9[1] / M_EARTH, a9, e9, planet_set("giants"), sun[1])
    print(f"{a.run}: {len(snaps)} snapshots; Planet Nine {p9[1] / M_EARTH:.2f} M_E, a {a9:.1f} au, e {e9:.3f}, "
          f"inclination to the giants' plane {inc0:.2f} deg")
    print("  t [Myr] | tilt of the giants' plane [deg] | secular (fixed axis) [deg]")
    last = None
    for k, (sa, idx, t) in enumerate(snaps):
        if not (k % a.every == a.every - 1 or k == len(snaps) - 1):
            continue
        _, rows = dump(a.p9sim, sa, idx)
        rows = [(n, m, np.asarray(p), np.asarray(v)) for n, m, p, v in rows if not n.startswith("tp")]
        Lg, _ = ang_mom(rows)
        tilt = math.degrees(math.acos(min(1.0, max(-1.0, np.dot(unit(Lg), unit(Lg0))))))
        sec, _ = analytic_fixed(L, Lp, om, inc0, t)
        print(f"{t / 1e6:9.0f} | {tilt:31.4f} | {float(sec):26.4f}")
        last = (t, tilt, float(sec))
    if last:
        print(f"at {last[0] / 1e6:.0f} Myr: tilt {last[1]:.4f} deg (secular {last[2]:.4f} deg)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("secular")
    s.add_argument("--p9", action="append", required=True, help="mass [M_E],a [au],e,i [deg]")
    s.add_argument("--t-gyr", type=float, default=4.5)
    s.add_argument("--planets", choices=["all", "giants"], default="all")
    s.add_argument("--spin-days", type=float, default=math.inf, help="P/lambda of the Sun (Lai 2016); default: fixed axis")
    sub.add_parser("check")
    n = sub.add_parser("nbody-ic")
    n.add_argument("--p9", required=True)
    n.add_argument("--out", required=True)
    n.add_argument("--dt", type=float, default=0.5)
    n.add_argument("--reverse", action="store_true")
    e = sub.add_parser("nbody-eval")
    e.add_argument("--ic", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--p9sim", default="build/gcc-O3/p9sim")
    e.add_argument("--every", type=int, default=10)
    w = sub.add_parser("snapshots")
    w.add_argument("--run", required=True, help="a p9job job or chain directory, or a package job directory")
    w.add_argument("--p9sim", default="build/gcc-O3/p9sim")
    w.add_argument("--every", type=int, default=20)
    a = ap.parse_args()
    {"secular": cmd_secular, "check": cmd_check, "nbody-ic": cmd_nbody_ic, "nbody-eval": cmd_nbody_eval,
     "snapshots": cmd_snapshots}[a.cmd](a)


if __name__ == "__main__":
    main()
