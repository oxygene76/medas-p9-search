#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Start values of the test case (Brown & Batygin 2021) as exact decimal text.

  python tools/make_ic.py --out ic.txt [--n-tp 4000] [--seed 9] [--tp-from 0 --tp-to 4000]

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
           0-10 deg, the angles uniform; seeded, so the set is reproducible.

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


def build(n_tp, seed, tp_from, tp_to):
    bodies = planets()
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
    rows = [(n, m, p - com_p, v - com_v) for n, m, p, v in bodies]
    for i in range(tp_from, tp_to):
        rows.append((f"tp{i:05d}", 0.0, sun[2] + tp_p[i] - com_p, sun[3] + tp_v[i] - com_v))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-tp", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=9)
    ap.add_argument("--tp-from", type=int, default=0)
    ap.add_argument("--tp-to", type=int, default=None)
    ap.add_argument("--dt", type=float, default=0.5)
    args = ap.parse_args()
    tp_to = args.n_tp if args.tp_to is None else args.tp_to
    rows = build(args.n_tp, args.seed, args.tp_from, tp_to)
    with open(args.out, "w") as f:
        f.write("# p9sim start values, written by tools/make_ic.py (see its docstring); values are Python repr (exact)\n")
        f.write(f"# test particles {args.tp_from}..{tp_to - 1} of {args.n_tp}, seed {args.seed}\n")
        f.write(f"G {G!r}\ndt {args.dt!r}\nN_active 6\ncorrector 0\n")
        for name, m, p, v in rows:
            vals = [float(m), *map(float, p), *map(float, v)]
            f.write("p " + name + " " + " ".join(repr(x) for x in vals) + "\n")
    print(f"make_ic: {len(rows)} bodies ({len(rows) - 6} test particles) -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
