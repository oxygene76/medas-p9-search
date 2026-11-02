#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Are the planets of several slices of one run bit-identical over time?

  build/venv/bin/python -I tools/planet_hash.py --p9sim build/gcc-O3/p9sim \\
      --slice runs/cause/ensmerc/m5/part00,runs/night-20261024/merc-m5/part00 --slice ... [--every 1e7] [--json out.json]

A slice is one integration of the same planets with a different set of test particles (comma-separated job or
chain directories, in time order, or a job of an equivalence package with params.env and segments/segNNN). At every snapshot time held by all
slices (or every --every years): the sha256 of the massive bodies' masses, positions and velocities as float64
(from p9sim dump, which prints 17 significant digits, so the values are exact), per slice; the number of distinct
hashes; and the largest difference between slices in the position of each planet (au).

With WHFast the test particles do not act on the planets, so all slices should agree bit for bit. With MERCURIUS
a close encounter of a test particle with a planet is integrated with IAS15 for the bodies involved, which can
include the planet; afterwards the planets of that slice differ in the last bits and drift apart chaotically.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import dump  # noqa: E402


def package_snapshots(job):
    """{time: (output.sa, index)} of a job of an equivalence package (params.env, segments/segNNN with DONE), with
    the same times as tools/equiv_eval.py package_file: snapshot j of segment k at (k + (j + 1) / per) * SEGMENT_YR."""
    env = dict(l.split("=", 1) for l in (job / "params.env").read_text().splitlines() if "=" in l and not l.startswith("#"))
    seg_yr, per, nseg = float(env["SEGMENT_YR"]), int(env["SNAPSHOTS_PER_SEGMENT"]), int(env["SEGMENTS"])
    out = {}
    for k in range(nseg):
        seg = job / "segments" / f"seg{k:03d}"
        if not (seg / "DONE").exists():
            continue
        for j in range(per):
            out[round(k * seg_yr + (j + 1) * seg_yr / per)] = (seg / "output.sa", j)
    return out


def snapshots(dirs):
    """{time: (output.sa, index)} over the segments of the directories (p9job chains or jobs of a package)."""
    out = {}
    for d in dirs:
        if (d / "params.env").exists() and (d / "segments").is_dir():
            out.update(package_snapshots(d))
            continue
        for seg in ([d] if (d / "job.json").exists() else sorted(d.glob("seg*"))):
            if not (seg / "result.json").exists():
                continue
            p = json.loads((seg / "job.json").read_text())["params"]
            t0, t1, n = float(p["t_start_yr"]), float(p["t_end_yr"]), int(p["snapshots"])
            for j in range(n):
                out[round(t0 + (j + 1) * (t1 - t0) / n)] = (seg / "output.sa", j)
    return out


def planets(p9sim, sa, idx):
    _, rows = dump(p9sim, sa, idx)
    rows = [r for r in rows if r[1] > 0]
    arr = np.array([[m, *r, *v] for _, m, r, v in rows], dtype=np.float64)
    return [r[0] for r in rows], arr


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--slice", action="append", required=True)
    ap.add_argument("--every", type=float, default=None, help="only these multiples of years (default: every snapshot)")
    ap.add_argument("--json")
    a = ap.parse_args()
    slices = [[Path(x) for x in s.split(",")] for s in a.slice]
    snaps = [snapshots(s) for s in slices]
    times = sorted(set.intersection(*(set(s) for s in snaps)))
    if a.every:
        times = [t for t in times if abs(t / a.every - round(t / a.every)) < 1e-9]
    res, first = [], None
    names = None
    print(f"{len(slices)} slices, {len(times)} common times; per time: distinct planet hashes, largest position difference (au)")
    for t in times:
        hs, arrs = [], []
        for s in snaps:
            nm, arr = planets(a.p9sim, *s[t])
            names = names or nm
            hs.append(hashlib.sha256(arr.tobytes()).hexdigest())
            arrs.append(arr)
        stack = np.stack(arrs)
        dpos = np.linalg.norm(stack[:, :, 1:4] - stack[0][None, :, 1:4], axis=2).max(axis=0)
        distinct = len(set(hs))
        if distinct > 1 and first is None:
            first = t
        row = {"t_yr": t, "distinct": distinct, "hashes": [h[:16] for h in hs],
               "max_dpos_au": {n: float(d) for n, d in zip(names, dpos)}}
        res.append(row)
        print(f"  t {t / 1e6:7.1f} Myr: {distinct} distinct  " + "  ".join(f"{n} {d:.2e}" for n, d in zip(names, dpos) if n != "Sun"))
    print(f"first time with differing planets: {'none' if first is None else f'{first / 1e6:.1f} Myr'}")
    if a.json:
        Path(a.json).write_text(json.dumps({"slices": a.slice, "first_differing_yr": first, "times": res}, indent=1) + "\n")


if __name__ == "__main__":
    main()
