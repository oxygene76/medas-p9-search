#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Precession rates of distant test particles, integrators against IAS15, with bootstrap errors.

  python tools/rates_bootstrap.py --ref ias15=runs/freq/tp-ias15.npz LABEL=FILE ...

The runs of tools/freq_compare.py tp (the same 200 particles, same start values). Per particle the
mean rate of varpi and Omega (linear fit of the unwrapped barycentric angles). Per integrator:
- the median of rate - rate_ref with a bootstrap 95 % interval (resampling the particles);
- the spread of the rates (standard deviation over the particles) relative to the reference's, and
  the slope of the rate against log a, relative to the reference's, with bootstrap intervals: a
  common offset does not change R(dvarpi), a different spread or slope does (phase mixing).
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import barycentric, elements  # noqa: E402
from freq_compare import load, masses_from_ic  # noqa: E402

N_BOOT = 4000


def rates(path, m):
    t, names, xv, _ = load(path)
    vp_all, om_all, a_all = [], [], []
    for k in range(len(t)):
        rows = [(n, m.get(n, 0.0), xv[k, i, :3], xv[k, i, 3:]) for i, n in enumerate(names)]
        b, mu = barycentric(rows)
        tps = [x for x in b if x[0].startswith("tp")]
        A, _, _, Om, vp = elements(mu, np.array([x[2] for x in tps]), np.array([x[3] for x in tps]))
        vp_all.append(vp); om_all.append(Om); a_all.append(A)
    tm = t / 1e6
    tpn = [n for n in names if n.startswith("tp")]
    vp_all, om_all, a_all = np.array(vp_all), np.array(om_all), np.array(a_all)
    out = {}
    for j, n in enumerate(tpn):
        rv = np.polyfit(tm, np.degrees(np.unwrap(np.radians(vp_all[:, j]))), 1)[0]
        ro = np.polyfit(tm, np.degrees(np.unwrap(np.radians(om_all[:, j]))), 1)[0]
        out[n] = (rv, ro, a_all[:, j].mean())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", required=True)
    ap.add_argument("runs", nargs="+")
    a = ap.parse_args()
    m = masses_from_ic()
    ref_label, ref_path = a.ref.split("=", 1)
    ref = rates(ref_path, m)
    rng = np.random.default_rng(1)
    print(f"{len(ref)} particles; reference {ref_label}")
    for spec in a.runs:
        label, path = spec.split("=", 1)
        x = rates(path, m)
        names = [n for n in ref if n in x]
        rv0 = np.array([ref[n][0] for n in names]); ro0 = np.array([ref[n][1] for n in names]); la = np.log(np.array([ref[n][2] for n in names]))
        rv1 = np.array([x[n][0] for n in names]); ro1 = np.array([x[n][1] for n in names])
        idx = rng.integers(0, len(names), size=(N_BOOT, len(names)))

        def ci(f):
            v = np.array([f(i) for i in idx])
            return f(np.arange(len(names))), np.quantile(v, 0.025), np.quantile(v, 0.975)

        lines = []
        for nm, r0, r1 in (("varpi", rv0, rv1), ("Omega", ro0, ro1)):
            med = ci(lambda i: np.median(r1[i] - r0[i]))
            spread = ci(lambda i: np.std(r1[i]) / np.std(r0[i]) - 1)
            slope = ci(lambda i: np.polyfit(la[i], r1[i], 1)[0] / np.polyfit(la[i], r0[i], 1)[0] - 1)
            lines.append(f"{nm}: median difference {med[0]:+.4f} deg/Myr [{med[1]:+.4f}, {med[2]:+.4f}]; "
                         f"spread {spread[0]:+.3%} [{spread[1]:+.3%}, {spread[2]:+.3%}]; slope against ln a {slope[0]:+.3%} [{slope[1]:+.3%}, {slope[2]:+.3%}]")
        print(f"{label}:\n  " + "\n  ".join(lines))


if __name__ == "__main__":
    main()
