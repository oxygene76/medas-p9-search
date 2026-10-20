#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Start values of the test case (Brown & Batygin 2021) as exact decimal text.

  python tools/make_ic.py --out ic.txt [--n-tp 4000] [--seed 9] [--tp-from 0 --tp-to 4000] [--members 0,1,2,3 --perturb 1e-12]

Bodies, in this order (the first six are massive, N_active = 6):
  Sun      the Sun with the masses of Mercury, Venus, Earth+Moon and Mars, at
           their common barycentre
  Jupiter, Saturn, Uranus, Neptune
           barycentric states from JPL DE440s at JD 2458270.0 (TDB), the epoch
           of the Planet Nine reference population
  P9       Planet Nine, Brown & Batygin (2021, AJ 162, 219): m = 6.2 Earth
           masses, a = 380 au, perihelion 300 au (e = 0.2105), i = 16 deg; the
           longitudes, which the paper's abstract does not give, are the
           circular means of the reference population (CaltechDATA
           doi:10.22002/8fjad-x7y61): varpi = 248.5 deg, Omega = 98.5 deg, mean
           anomaly 180 deg (its median). Heliocentric elements, ecliptic J2000.
  tp00000… test particles (massless) in the distant Kuiper belt: a uniform in
           150-550 au, perihelion uniform in 30-50 au, inclination uniform in
           0-10 deg (other ranges with --a-range, --q-range, --inc-range;
           Brown & Batygin 2021: 150-500 au, 30-50 au, 0-25 deg), the angles
           uniform; seeded, so the set is reproducible.

Ensembles (--members): member 0 is the set itself; member m >= 1 is the same
set with each test particle's barycentric position multiplied, per component,
by 1 + perturb u, u uniform in [-1, 1] drawn from the seed (seed, m, i), so a
particle gets the same perturbation in any slice. Member m's particle i is
named tp{m * 100000 + i} (tp100005: member 1, particle 5; member 0 keeps
tp00005) with id 6 + m * 100000 + i; one file may hold several members (they
do not interact).

Frame: ecliptic and equinox J2000 (the elements of the reference population
refer to it), barycentric; units au, year (365.25 d), solar mass, G = (k *
365.25)^2 with the Gaussian constant k.

All conversions (DE440s, rotation, elements to states) happen here once; the
file holds every value as the shortest decimal that reads back to the same
double (Python repr), so `p9sim init` builds bit-identical start states on any
machine. Integration settings: WHFast, democratic heliocentric coordinates,
dt = 0.5 yr (1/24 of Jupiter's period), no corrector.
"""

import argparse
import math
import sys

import numpy as np

K_GAUSS = 0.01720209895
YEAR_D = 365.25
G = (K_GAUSS * YEAR_D) ** 2
EPOCH_JD = 2458270.0
EPS_J2000 = math.radians(84381.448 / 3600)

# masses as fractions of the Sun (DE440 GM ratios)
MASS = {
    "mercury": 1 / 6023657.33,
    "venus": 1 / 408523.7186,
    "earth-moon": 1 / 328900.5596,
    "mars": 1 / 3098703.59,
    "jupiter": 1 / 1047.348644,
    "saturn": 1 / 3497.9018,
    "uranus": 1 / 22902.951,
    "neptune": 1 / 19412.26,
}
EARTH_IN_SUN = 3.003489596e-6

P9 = {"m_earth": 6.2, "a": 380.0, "q": 300.0, "inc": 16.0, "varpi": 248.5, "Omega": 98.5, "M": 180.0}
TP = {"a": (150.0, 550.0), "q": (30.0, 50.0), "inc": (0.0, 10.0)}


def kepler_E(M, e):
    E = M + e * np.sin(M)
    for _ in range(100):
        dE = (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
        E = E - dE
        if np.max(np.abs(dE)) < 1e-15:
            break
    return E


def elements_to_state(mu, a, e, inc, Omega, omega, M):
    """Heliocentric state (au, au/yr) from elements (angles in radians); arrays."""
    E = kepler_E(np.mod(M, 2 * np.pi), e)
    cE, sE = np.cos(E), np.sin(E)
    b = a * np.sqrt(1 - e * e)
    xo, yo = a * (cE - e), b * sE
    n = np.sqrt(mu / a**3)
    rdot = n * a / (1 - e * cE)
    vxo, vyo = -a * sE * rdot / a, b * cE * rdot / a
    cO, sO, cw, sw, ci, si = np.cos(Omega), np.sin(Omega), np.cos(omega), np.sin(omega), np.cos(inc), np.sin(inc)
    R = np.array([
        [cO * cw - sO * sw * ci, -cO * sw - sO * cw * ci],
        [sO * cw + cO * sw * ci, -sO * sw + cO * cw * ci],
        [sw * si, cw * si],
    ])
    pos = np.stack([R[k][0] * xo + R[k][1] * yo for k in range(3)], axis=-1)
    vel = np.stack([R[k][0] * vxo + R[k][1] * vyo for k in range(3)], axis=-1)
    return pos, vel


def equatorial_to_ecliptic(v):
    ce, se = math.cos(EPS_J2000), math.sin(EPS_J2000)
    x, y, z = v[..., 0], v[..., 1], v[..., 2]
    return np.stack([x, ce * y + se * z, -se * y + ce * z], axis=-1)


def planets():
    """Barycentric ecliptic states of the Sun (+ inner planets) and the giants from DE440s."""
    from astropy import units as u
    from astropy.coordinates import get_body_barycentric_posvel, solar_system_ephemeris
    from astropy.time import Time

    solar_system_ephemeris.set("de440s")
    t = Time(EPOCH_JD, format="jd", scale="tdb")
    state = {}
    for body in ["sun", "mercury", "venus", "earth-moon-barycenter", "mars", "jupiter", "saturn", "uranus", "neptune"]:
        p, v = get_body_barycentric_posvel(body, t)
        state[body.replace("-barycenter", "")] = (p.xyz.to_value(u.au), v.xyz.to_value(u.au / u.yr))
    inner = ["sun", "mercury", "venus", "earth-moon", "mars"]
    m_in = {"sun": 1.0, **{k: MASS[k] for k in inner[1:]}}
    msum = sum(m_in.values())
    sun_p = sum(m_in[k] * state[k][0] for k in inner) / msum
    sun_v = sum(m_in[k] * state[k][1] for k in inner) / msum
    out = [("Sun", msum, sun_p, sun_v)]
    for k in ["jupiter", "saturn", "uranus", "neptune"]:
        out.append((k.capitalize(), MASS[k], state[k][0], state[k][1]))
    return [(n, m, equatorial_to_ecliptic(p), equatorial_to_ecliptic(v)) for n, m, p, v in out]


def absorb(bodies, names):
    """Model "j2" (Batygin & Brown 2016, AJ 151, 22, sec. 5.2): the planets in names merged into the
    central body (mass, centre of mass), which gets the quadrupole of their orbit-averaged rings,
    J2 R^2 = 1/2 sum m_i a_i^2 / M (a_i: heliocentric osculating semi-major axes), about the axis
    of their total angular momentum. Returns the new list of bodies and the J2 parameters."""
    sun = bodies[0]
    gone = [b for b in bodies if b[0] in names]
    if len(gone) != len(names):
        raise SystemExit(f"--j2: unknown body in {names}")
    M = sun[1] + sum(b[1] for b in gone)
    P = (sun[1] * sun[2] + sum(b[1] * b[2] for b in gone)) / M
    V = (sun[1] * sun[3] + sum(b[1] * b[3] for b in gone)) / M
    s = 0.0
    L = np.zeros(3)
    a_out = {}
    for name, m, p, v in gone:
        r, u = p - sun[2], v - sun[3]
        a = 1 / (2 / np.linalg.norm(r) - u @ u / (G * (sun[1] + m)))
        a_out[name] = a
        s += m * a * a
        L += m * np.cross(p - P, v - V)
    n = L / np.linalg.norm(L)
    j2 = {"absorbed": list(names), "j2r2_au2": repr(float(s / (2 * M))), "mu_j2r2": repr(float(G * M * s / (2 * M))),
          "axis": [repr(float(x)) for x in n], "r_remove_au": f"{max(a_out.values()):.2f}",
          "note": "J2 R^2 = 1/2 sum m a^2 / M of the absorbed planets; test particles within r_remove (the outermost absorbed "
                  "planet's semi-major axis) are removed"}
    rest = [("Sun", M, P, V)] + [b for b in bodies[1:] if b[0] not in names]
    return rest, j2


def build(n_tp, seed, tp_from, tp_to, j2_names=None):
    bodies = planets()
    j2 = None
    if j2_names:
        bodies, j2 = absorb(bodies, j2_names)
    sun = bodies[0]
    m9 = P9["m_earth"] * EARTH_IN_SUN
    e9 = 1 - P9["q"] / P9["a"]
    d = math.radians
    p9_p, p9_v = elements_to_state(G * (sun[1] + m9), np.array([P9["a"]]), np.array([e9]), np.array([d(P9["inc"])]),
                                   np.array([d(P9["Omega"])]), np.array([d(P9["varpi"] - P9["Omega"])]), np.array([d(P9["M"])]))
    bodies.append(("P9", m9, sun[2] + p9_p[0], sun[3] + p9_v[0]))
    # test particles: all n_tp drawn, then the slice [tp_from, tp_to) kept (work packages)
    rng = np.random.default_rng(seed)
    a = rng.uniform(*TP["a"], n_tp)
    q = rng.uniform(*TP["q"], n_tp)
    inc = np.radians(rng.uniform(*TP["inc"], n_tp))
    Om, om, M = (rng.uniform(0, 2 * np.pi, n_tp) for _ in range(3))
    tp_p, tp_v = elements_to_state(G * sun[1], a, 1 - q / a, inc, Om, om, M)
    # barycentric frame of the massive bodies
    mtot = sum(b[1] for b in bodies)
    com_p = sum(b[1] * b[2] for b in bodies) / mtot
    com_v = sum(b[1] * b[3] for b in bodies) / mtot
    rows = [(n, m, p - com_p, v - com_v, k) for k, (n, m, p, v) in enumerate(bodies)]
    # ids: 0..5 the massive bodies, 6 + i test particle i of the whole set (also in a slice)
    for i in range(tp_from, tp_to):
        rows.append((f"tp{i:05d}", 0.0, sun[2] + tp_p[i] - com_p, sun[3] + tp_v[i] - com_v, len(bodies) + i))
    return rows, j2


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-tp", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=9)
    ap.add_argument("--tp-from", type=int, default=0)
    ap.add_argument("--tp-to", type=int, default=None)
    ap.add_argument("--dt", type=float, default=0.5)
    ap.add_argument("--a-range", type=float, nargs=2, default=list(TP["a"]), help="semi-major axes of the test particles (au), uniform")
    ap.add_argument("--q-range", type=float, nargs=2, default=list(TP["q"]), help="perihelia (au), uniform")
    ap.add_argument("--inc-range", type=float, nargs=2, default=list(TP["inc"]), help="inclinations (deg), uniform")
    ap.add_argument("--members", default="0", help="ensemble members (comma-separated, 0 = the set itself; see above)")
    ap.add_argument("--perturb", type=float, default=1e-12, help="relative perturbation of the positions of members >= 1")
    ap.add_argument("--integrator", choices=["whfast", "mercurius"], default="whfast",
                    help="p9sim's integrator (mercurius: hybrid, resolves close encounters with IAS15)")
    ap.add_argument("--j2", default=None, help='model "j2": planets merged into the central body, e.g. Jupiter,Saturn,Uranus')
    ap.add_argument("--j2-out", default=None, help="file for the J2 parameters (JSON)")
    args = ap.parse_args()
    tp_to = args.n_tp if args.tp_to is None else args.tp_to
    default_ranges = dict(TP)
    TP.update(a=tuple(args.a_range), q=tuple(args.q_range), inc=tuple(args.inc_range))
    rows, j2 = build(args.n_tp, args.seed, args.tp_from, tp_to, args.j2.split(",") if args.j2 else None)
    members = [int(m) for m in args.members.split(",")]
    if members != [0]:
        if args.n_tp > 100000 or min(members) < 0 or max(members) > 9 or len(set(members)) != len(members):
            sys.exit("--members: distinct members 0..9, at most 100000 test particles")
        massive = [r for r in rows if not r[0].startswith("tp")]
        tps = [r for r in rows if r[0].startswith("tp")]
        rows = list(massive)
        for mem in members:
            for name, m, pos, v, pid in tps:
                i = int(name[2:])
                if mem == 0:
                    rows.append((name, m, pos, v, pid))
                    continue
                u = np.random.default_rng([args.seed, mem, i]).uniform(-1.0, 1.0, 3)
                rows.append((f"tp{mem * 100000 + i:06d}", m, pos * (1.0 + args.perturb * u), v, pid + mem * 100000))
    if j2 and args.j2_out:
        import json
        open(args.j2_out, "w").write(json.dumps(j2, indent=1) + "\n")
    with open(args.out, "w") as f:
        f.write("# p9sim start values, written by tools/make_ic.py (see its docstring); values are Python repr (exact)\n")
        f.write(f"# test particles {args.tp_from}..{tp_to - 1} of {args.n_tp}, seed {args.seed}"
                + (f", members {args.members} (positions perturbed by {args.perturb:g} relative)" if members != [0] else "")
                + (f", a {TP['a']} au, q {TP['q']} au, i {TP['inc']} deg" if TP != default_ranges else "") + "\n")
        f.write(f"G {G!r}\ndt {args.dt!r}\nN_active {sum(1 for r in rows if r[1] > 0)}\ncorrector 0\n")
        if args.integrator != "whfast":
            f.write(f"integrator {args.integrator}\n")
        for name, m, p, v, pid in rows:
            vals = [float(m), *map(float, p), *map(float, v)]
            f.write("p " + name + " " + " ".join(repr(x) for x in vals) + f" {pid}\n")
    n_massive = sum(1 for r in rows if r[1] > 0)
    print(f"make_ic: {len(rows)} bodies ({len(rows) - n_massive} test particles) -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
