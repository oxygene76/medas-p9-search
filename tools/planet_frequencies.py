#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fundamental secular frequencies of the giant planets against Laskar et al. (2011, A&A 532, A89, Table 6: La2004 and
La2010a); planets only, no test particles (docs/literature-checks.md).

  python tools/planet_frequencies.py ic --model A|B|C --dt DT --out ic.txt
        A  the four giants, the inner planets' masses and momenta in the Sun (as tools/make_ic.py)
        B  A plus Planet Nine (Brown & Batygin 2021, as tools/make_ic.py)
        C  all eight planets, the Sun alone (DE440s, JD 2458270.0, as tools/make_ic.py), no Planet Nine
  python tools/planet_frequencies.py analyse LABEL=output.sa ... [--t-max YR] [--json OUT]
        g5..g8 (strongest line of e exp(i varpi) near the literature value) and s6..s8 (of sin(i/2) exp(i Omega)),
        heliocentric elements, ecliptic J2000; Hann window, FFT zero-padded 8 times, maximum refined (golden section);
        against La2004 and La2010a, and between the runs
"""

import argparse
import json
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_ic as mi  # noqa: E402
from analyze import elements  # noqa: E402

P9SIM = str(Path(__file__).resolve().parents[1] / "build/gcc-O3/p9sim")
ARCSEC = 180 / np.pi * 3600
GIANTS = ["Jupiter", "Saturn", "Uranus", "Neptune"]
# Laskar et al. 2011, Table 6 (arXiv:1103.1084v1), arcsec/yr: La2004, La2010a, and Delta_100 (variation over 100 Myr)
LIT = {"g5": (4.257452, 4.257482, 0.000030), "g6": (28.2450, 28.2449, 0.001), "g7": (3.087951, 3.087946, 0.000034),
       "g8": (0.673021, 0.673019, 0.000015), "s6": (-26.347855, -26.347841, 0.000076),
       "s7": (-2.9925259, -2.9925258, 0.000025), "s8": (-0.691736, -0.691740, 0.000010)}
WHICH = {"g5": ("Jupiter", "g"), "g6": ("Saturn", "g"), "g7": ("Uranus", "g"), "g8": ("Neptune", "g"),
         "s6": ("Saturn", "s"), "s7": ("Uranus", "s"), "s8": ("Neptune", "s")}


def bodies_all8():
    """Barycentric ecliptic states of the Sun and all eight planets (DE440s, the epoch and masses of make_ic)."""
    from astropy import units as u
    from astropy.coordinates import get_body_barycentric_posvel, solar_system_ephemeris
    from astropy.time import Time
    solar_system_ephemeris.set("de440s")
    t = Time(mi.EPOCH_JD, format="jd", scale="tdb")
    out = []
    for body, name in (("sun", "Sun"), ("mercury", "Mercury"), ("venus", "Venus"), ("earth-moon-barycenter", "Earth"),
                       ("mars", "Mars"), ("jupiter", "Jupiter"), ("saturn", "Saturn"), ("uranus", "Uranus"), ("neptune", "Neptune")):
        p, v = get_body_barycentric_posvel(body, t)
        key = body.replace("-barycenter", "")
        m = 1.0 if key == "sun" else mi.MASS[key]
        out.append((name, m, mi.equatorial_to_ecliptic(p.xyz.to_value(u.au)), mi.equatorial_to_ecliptic(v.xyz.to_value(u.au / u.yr))))
    return out


def build(model):
    if model == "C":
        bodies = bodies_all8()
    else:
        rows, _ = mi.build(1, 9, 0, 1)  # the massive bodies of the start files (with Planet Nine); the one test particle is dropped
        bodies = [(n, m, p, v) for n, m, p, v, _ in rows if not n.startswith("tp")]
        if model == "A":
            bodies = [b for b in bodies if b[0] != "P9"]
    mt = sum(b[1] for b in bodies)
    cp = sum(b[1] * b[2] for b in bodies) / mt
    cv = sum(b[1] * b[3] for b in bodies) / mt
    return [(n, m, p - cp, v - cv, k) for k, (n, m, p, v) in enumerate(bodies)]


def cmd_ic(a):
    rows = build(a.model)
    with open(a.out, "w") as f:
        f.write(f"# planets only, model {a.model} (tools/planet_frequencies.py, docs/literature-checks.md); values are Python repr (exact)\n")
        f.write(f"G {mi.G!r}\ndt {a.dt!r}\nN_active {len(rows)}\ncorrector 0\n")
        for name, m, p, v, pid in rows:
            f.write("p " + name + " " + " ".join(repr(float(x)) for x in [m, *p, *v]) + f" {pid}\n")
    print(f"{a.out}: model {a.model}, {len(rows)} bodies: {', '.join(r[0] for r in rows)}")


def load(path, p9sim, t_max=None):
    """t (n), names, masses, xv (n, bodies, 6) of all snapshots (p9sim dump, in parallel)."""
    def one(k):
        r = subprocess.run([p9sim, "dump", path, str(k)], capture_output=True, text=True)
        if r.returncode:
            return None
        lines = [l.split() for l in r.stdout.splitlines() if l.strip() and not l.startswith("Warning")]
        return float(lines[0][1]), [x[0] for x in lines[1:]], [float(x[-7]) for x in lines[1:]], [[float(z) for z in x[-6:]] for x in lines[1:]]
    out, k, step = [], 0, 4000
    with ThreadPoolExecutor(8) as ex:
        while True:
            part = list(ex.map(one, range(k, k + step)))
            got = [p for p in part if p is not None]
            out += got
            if len(got) < step or (t_max and got[-1][0] >= t_max):
                break
            k += step
    if t_max:
        out = [o for o in out if o[0] <= t_max * (1 + 1e-12)]
    t = np.array([o[0] for o in out])
    return t, out[0][1], out[0][2], np.array([o[3] for o in out])


def line_freq(t, z, near):
    """Frequency (arcsec/yr) of the strongest line of z(t) within 10 % of near: Hann window, FFT zero-padded 8 times,
    maximum refined by a golden-section search of |sum z w exp(-i nu t)|."""
    t = t - t[0]
    T = t[-1]
    w = 0.5 * (1 - np.cos(2 * np.pi * t / T))
    zz = (z - z.mean()) * w
    n = len(t) * 8
    f = np.fft.fftfreq(n, d=t[1] - t[0]) * 2 * np.pi
    F = np.fft.fft(zz, n)
    band = np.abs(f * ARCSEC - near) <= 0.1 * abs(near)
    k = np.flatnonzero(band)[np.argmax(np.abs(F[band]))]
    amp = lambda nu: abs(np.sum(zz * np.exp(-1j * nu * t)))
    a_, b_ = f[k] - 2 * np.pi / T, f[k] + 2 * np.pi / T
    g = (math.sqrt(5) - 1) / 2
    c, d = b_ - g * (b_ - a_), a_ + g * (b_ - a_)
    for _ in range(80):
        if amp(c) > amp(d):
            b_ = d
        else:
            a_ = c
        c, d = b_ - g * (b_ - a_), a_ + g * (b_ - a_)
    return 0.5 * (a_ + b_) * ARCSEC


def frequencies(t, names, masses, xv):
    sun = xv[:, names.index("Sun"), :]
    msun = masses[names.index("Sun")]
    out = {}
    for key, (planet, kind) in WHICH.items():
        j = names.index(planet)
        x = xv[:, j, :] - sun
        _, E, I, Om, vp = elements(mi.G * (msun + masses[j]), x[:, :3], x[:, 3:])
        z = E * np.exp(1j * np.radians(vp)) if kind == "g" else np.sin(np.radians(I) / 2) * np.exp(1j * np.radians(Om))
        out[key] = line_freq(t, z, LIT[key][0])
    return out


def cmd_analyse(a):
    res, span = {}, {}
    for spec in a.runs:
        label, path = spec.split("=", 1)
        t, names, masses, xv = load(path, a.p9sim, a.t_max)
        res[label] = frequencies(t, names, masses, xv)
        span[label] = (t[0], t[-1], len(t))
    print("snapshots: " + "; ".join(f"{l} {s[2]} from {s[0]:g} to {s[1] / 1e6:g} Myr" for l, s in span.items()))
    print("frequencies (arcsec/yr) and relative difference to La2004 | La2010a; Delta_100 = variation over 100 Myr (Laskar et al. 2004)")
    for key in LIT:
        l04, l10, d100 = LIT[key]
        cells = [f"{key}: La2004 {l04:+.7f}, La2010a {l10:+.7f}, Delta_100 {d100:.6f} ({d100 / abs(l04):.1e})"]
        for label in res:
            v = res[label][key]
            cells.append(f"   {label:12s} {v:+.7f}  {v / l04 - 1:+.2e} | {v / l10 - 1:+.2e}")
        print("\n".join(cells))
    labels = list(res)
    if len(labels) > 1:
        print("between the runs (relative):")
        for i, x in enumerate(labels):
            for y in labels[i + 1:]:
                print(f"   {y} - {x}: " + ", ".join(f"{k} {res[y][k] / res[x][k] - 1:+.2e}" for k in LIT))
    if a.json:
        Path(a.json).write_text(json.dumps({"literature": LIT, "runs": res, "span": span}, indent=1) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("ic")
    i.add_argument("--model", choices=["A", "B", "C"], required=True)
    i.add_argument("--dt", type=float, required=True)
    i.add_argument("--out", required=True)
    s = sub.add_parser("analyse")
    s.add_argument("runs", nargs="+")
    s.add_argument("--p9sim", default=P9SIM)
    s.add_argument("--t-max", type=float, default=None)
    s.add_argument("--json", default=None)
    a = ap.parse_args()
    {"ic": cmd_ic, "analyse": cmd_analyse}[a.cmd](a)


if __name__ == "__main__":
    main()
