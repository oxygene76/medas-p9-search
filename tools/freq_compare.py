#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Secular frequencies of the planets and precession rates of distant test particles, integrators against IAS15.

  python tools/freq_compare.py planets LABEL=FILE ... --ref ias15      (planets alone, many snapshots)
  python tools/freq_compare.py tp LABEL=FILE ... --ref ias15           (test particles, a few Myr)

FILE: a simulation archive of p9sim/p9gpu (.sa, read with build/gcc-O3/p9sim dump) or an npz of
tools/ias15_run.py.
planets: for each giant planet the strongest line of z = e exp(i varpi) (g5..g8) and of zeta = sin(i/2)
exp(i Omega) (s6..s8; heliocentric, ecliptic J2000), by a Hann-windowed Fourier transform refined at
its maximum; their difference from the reference, relative and as the phase drift it gives over 200 Myr;
Planet Nine's mean drift of varpi and Omega (linear fit, barycentric).
tp: per test particle the mean rate of varpi and Omega (linear fit of the unwrapped angles, barycentric
elements as in the evaluations) and its difference from the reference: median, quartiles, and the
median relative to the rate itself.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import barycentric, elements  # noqa: E402
from make_ic import G  # noqa: E402

P9SIM = str(Path(__file__).resolve().parents[1] / "build/gcc-O3/p9sim")
PLANETS = ["Jupiter", "Saturn", "Uranus", "Neptune"]
ARCSEC = 180 / np.pi * 3600


def load(path):
    """t (n), names, xv (n, bodies, 6), masses."""
    if path.endswith(".npz"):
        d = np.load(path)
        names = [str(x) for x in d["names"]]
        return d["t"], names, d["xv"], None
    ts, xv, names, masses = [], [], None, None
    k = 0
    while True:
        out = subprocess.run([P9SIM, "dump", path, str(k)], capture_output=True, text=True)
        if out.returncode:
            break
        lines = [l.split() for l in out.stdout.splitlines() if l.strip()]
        ts.append(float(lines[0][1]))
        rows = lines[1:]
        if names is None:
            names = [r[0] for r in rows]
            masses = [float(r[2]) for r in rows]
        xv.append([[float(z) for z in r[3:9]] for r in rows])
        k += 1
    return np.array(ts), names, np.array(xv), masses


def masses_from_ic():
    out = {}
    for l in open(Path(__file__).resolve().parents[1] / "runs/freq/planets-wh05.txt"):
        f = l.split()
        if f and f[0] == "p":
            out[f[1]] = float(f[2])
    return out


# Laskar et al. 2011 (A&A 532, A89), fundamental frequencies (arcsec/yr): where to look for each line
LITERATURE = {"g Jupiter": 4.257452, "g Saturn": 28.2450, "g Uranus": 3.087951, "g Neptune": 0.673021,
              "s Saturn": -26.347855, "s Uranus": -2.9925259, "s Neptune": -0.691736}


def line_freq(t, z, near=None):
    """Frequency (rad/yr) and amplitude of the strongest line of z(t) (within 10 % of near, arcsec/yr, if given),
    Hann window, refined maximum."""
    t = t - t[0]
    T = t[-1]
    w = 0.5 * (1 - np.cos(2 * np.pi * t / T))
    zz = (z - z.mean()) * w
    n = len(t) * 8
    f = np.fft.fftfreq(n, d=t[1] - t[0]) * 2 * np.pi
    F = np.fft.fft(zz, n)
    if near is not None:
        band = np.abs(f * ARCSEC - near) <= 0.1 * abs(near)
        k = np.flatnonzero(band)[np.argmax(np.abs(F[band]))]
    else:
        k = np.argmax(np.abs(F))
    amp = lambda nu: abs(np.sum(zz * np.exp(-1j * nu * t)))
    lo, hi = f[k] - 2 * np.pi / T, f[k] + 2 * np.pi / T
    g = (np.sqrt(5) - 1) / 2
    a_, b_ = lo, hi
    c, d = b_ - g * (b_ - a_), a_ + g * (b_ - a_)
    for _ in range(80):
        if amp(c) > amp(d):
            b_ = d
        else:
            a_ = c
        c, d = b_ - g * (b_ - a_), a_ + g * (b_ - a_)
    nu = 0.5 * (a_ + b_)
    return nu, amp(nu) / w.sum()


def planets(args, runs):
    m = masses_from_ic()
    res = {}
    for label, path in runs:
        t, names, xv, _ = load(path)
        sun = xv[:, names.index("Sun"), :]
        out = {}
        for p in PLANETS:
            x = xv[:, names.index(p), :] - sun
            A, E, I, Om, vp = elements(G * (m["Sun"] + m[p]), x[:, :3], x[:, 3:])
            z = E * np.exp(1j * np.radians(vp))
            zeta = np.sin(np.radians(I) / 2) * np.exp(1j * np.radians(Om))
            out["g " + p] = line_freq(t, z, LITERATURE["g " + p])[0] * ARCSEC
            if p != "Jupiter":
                out["s " + p] = line_freq(t, zeta, LITERATURE["s " + p])[0] * ARCSEC
        # Planet Nine: barycentric varpi and Omega, mean drift
        rows = [[(n, mm, xv[k, i, :3], xv[k, i, 3:]) for i, (n, mm) in enumerate(zip(names, [m.get(n, 0.0) for n in names])) if mm > 0] for k in range(len(t))]
        vps, oms = [], []
        for r in rows:
            b, mu = barycentric(r)
            nine = [x for x in b if x[0] == "P9"][0]
            _, _, _, Om, vp = elements(mu, nine[2][None, :], nine[3][None, :])
            vps.append(vp[0]); oms.append(Om[0])
        tm = t / 1e6
        out["P9 varpi deg/Myr"] = np.polyfit(tm, np.degrees(np.unwrap(np.radians(vps))), 1)[0]
        out["P9 Omega deg/Myr"] = np.polyfit(tm, np.degrees(np.unwrap(np.radians(oms))), 1)[0]
        res[label] = out
    ref = res[args.ref]
    keys = list(ref)
    print("literature (Laskar et al. 2011), and the reference against it:")
    for k in keys:
        if k in LITERATURE:
            print(f"   {k:12s} literature {LITERATURE[k]:+11.6f}, {args.ref} {ref[k]:+11.6f}, relative {ref[k] / LITERATURE[k] - 1:+.2e}")
    print(f"frequencies (arcsec/yr; P9: deg/Myr) over {t[-1] / 1e6:.0f} Myr; difference from {args.ref}: relative, and the phase drift over 200 Myr (deg)")
    print(f"{'':22s}" + "".join(f"{l:>26s}" for l, _ in runs))
    for k in keys:
        cells = []
        for l, _ in runs:
            v = res[l][k]
            if l == args.ref:
                cells.append(f"{v:26.6f}")
            else:
                dv = v - ref[k]
                drift = dv / 3600 * 200e6 if not k.startswith("P9") else dv * 200
                cells.append(f"{dv / ref[k]:+12.2e} {drift:+10.2f} deg ")
        print(f"{k:22s}" + "".join(cells))


def tp(args, runs):
    m = masses_from_ic()
    res = {}
    for label, path in runs:
        t, names, xv, _ = load(path)
        if label != args.ref and not path.endswith(".npz"):
            pass
        idx = [i for i, n in enumerate(names) if n.startswith("tp")]
        rates_v, rates_o = {}, {}
        vp_all, om_all = [], []
        for k in range(len(t)):
            rows = [(n, m.get(n, 0.0), xv[k, i, :3], xv[k, i, 3:]) for i, n in enumerate(names)]
            b, mu = barycentric(rows)
            tps = [x for x in b if x[0].startswith("tp")]
            _, _, _, Om, vp = elements(mu, np.array([x[2] for x in tps]), np.array([x[3] for x in tps]))
            vp_all.append(vp); om_all.append(Om)
        vp_all, om_all = np.array(vp_all), np.array(om_all)
        tm = t / 1e6
        tpn = [names[i] for i in idx]
        for j, n in enumerate(tpn):
            rates_v[n] = np.polyfit(tm, np.degrees(np.unwrap(np.radians(vp_all[:, j]))), 1)[0]
            rates_o[n] = np.polyfit(tm, np.degrees(np.unwrap(np.radians(om_all[:, j]))), 1)[0]
        res[label] = (rates_v, rates_o)
    rv, ro = res[args.ref]
    print(f"precession rates of the test particles over {t[-1] / 1e6:.0f} Myr (deg/Myr); reference {args.ref}: median varpi rate "
          f"{np.median(list(rv.values())):+.4f}, Omega rate {np.median(list(ro.values())):+.4f}")
    for label, _ in runs:
        if label == args.ref:
            continue
        v, o = res[label]
        common = [n for n in rv if n in v]
        dv = np.array([v[n] - rv[n] for n in common]); do = np.array([o[n] - ro[n] for n in common])
        relv = np.array([(v[n] - rv[n]) / abs(rv[n]) for n in common if abs(rv[n]) > 1e-3])
        relo = np.array([(o[n] - ro[n]) / abs(ro[n]) for n in common if abs(ro[n]) > 1e-3])
        q = lambda x: f"median {np.median(x):+.2e}, quartiles {np.quantile(x, 0.25):+.2e} .. {np.quantile(x, 0.75):+.2e}"
        print(f"  {label:16s} varpi: {q(dv)} deg/Myr (relative median {np.median(relv):+.2e}); Omega: {q(do)} deg/Myr (relative {np.median(relo):+.2e}); n {len(common)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["planets", "tp"])
    ap.add_argument("runs", nargs="+", help="LABEL=FILE")
    ap.add_argument("--ref", required=True)
    a = ap.parse_args()
    runs = [tuple(r.split("=", 1)) for r in a.runs]
    {"planets": planets, "tp": tp}[a.what](a, runs)


if __name__ == "__main__":
    main()
