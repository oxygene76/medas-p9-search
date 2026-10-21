#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Barycentric elements of the ensemble runs at many times, as compact files for the cause analysis.

  python tools/cause_extract.py --out runs/cause/elements [--times 1e7 2e7 ...]

Runs (docs/validation-ensemble-200myr.md): G0-G3 = runs/val/ens-gpu members 0-3, M0 =
runs/val/merc (to 50 Myr) and runs/val/merc2 (after), M1 = runs/val/ens-merc member 4; also the
first comparison's p9gpu run (S = runs/val/gpu-2000-smooth) and the fixed-step run (F =
runs/val/gpu-2000-count, gpu-2000-count2). Per time one npz: for each run the particle index i,
a, e, i (deg), Omega, varpi, dvarpi, dOmega (relative to Planet Nine), and the planets' elements
and heliocentric longitudes. Resumable: times already written are skipped.
"""

import argparse
import glob
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import at_time, barycentric, dump, elements  # noqa: E402

P9SIM = str(Path(__file__).resolve().parents[1] / "build/gcc-O3/p9sim")
RUNS = {
    "G": (["runs/val/ens-gpu"], [0, 1, 2, 3]),
    "M0": (sorted(glob.glob("runs/val/merc/part*")) + sorted(glob.glob("runs/val/merc2/part*")), [0]),
    "M1": (sorted(glob.glob("runs/val/ens-merc/part*")), [4]),
    "S": (["runs/val/gpu-2000-smooth"], [0]),
    "F": (["runs/val/gpu-2000-count", "runs/val/gpu-2000-count2"], [0]),
}
PLANETS = ["Jupiter", "Saturn", "Uranus", "Neptune", "P9"]


def extract(T):
    out = {}
    for key, (dirs, members) in RUNS.items():
        tps, planets = {m: [] for m in members}, None
        for d in dirs:
            f = at_time(Path(d), T)
            if f is None:
                continue
            _, rows = dump(P9SIM, *f)
            rows, mu = barycentric(rows)
            if planets is None:
                sun = [r for r in rows if r[0] == "Sun"][0]
                planets = {}
                for n, m, r, v in rows:
                    if n in PLANETS:
                        A, E, I, Om, vp = elements(mu, r[None, :], v[None, :])
                        hr = r - sun[2]
                        planets[n] = (A[0], E[0], I[0], Om[0], vp[0], np.degrees(np.arctan2(hr[1], hr[0])) % 360)
            for n, m, r, v in rows:
                if n.startswith("tp"):
                    k = int(n[2:])
                    if k // 100000 in tps:
                        tps[k // 100000].append((k % 100000, r, v))
        if planets is None:
            continue
        p9 = planets["P9"]
        for mem, lst in tps.items():
            if not lst:
                continue
            A, E, I, Om, vp = elements(mu, np.array([x[1] for x in lst]), np.array([x[2] for x in lst]))
            label = f"G{mem}" if key == "G" else key
            out[f"{label}_i"] = np.array([x[0] for x in lst])
            out[f"{label}_el"] = np.stack([A, E, I, Om % 360, vp % 360, (vp - p9[4]) % 360, (Om - p9[3]) % 360], axis=1)
            out[f"{label}_planets"] = np.array([planets[n] for n in PLANETS])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--times", nargs="+", type=float,
                    default=[1e7 * k for k in range(1, 10)] + [5e6 * k for k in range(20, 41)])
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for T in a.times:
        f = out / f"t{T / 1e6:05.0f}Myr.npz"
        if f.exists():
            continue
        np.savez(str(f) + ".tmp.npz", **extract(T))
        Path(str(f) + ".tmp.npz").rename(f)
        print(f"{f.name}", flush=True)


if __name__ == "__main__":
    main()
