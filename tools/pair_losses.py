#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Losses paired by test particle: MERCURIUS against p9gpu, and the flybys before them.

  python tools/pair_losses.py --p9sim build/gcc-O3/p9sim --merc runs/val/merc/part* --gpu runs/val/gpu-2000-count --time 5e7 [--n0 2000]

Both runs start from the same test particles (ids 6 ... 6 + n0 - 1). Lost by T:
not among the survivors of the snapshot at T. b = lost only in p9gpu, c = lost
only in MERCURIUS; exact two-sided McNemar test (b against b + c, p = 1/2).
For the particles lost only in p9gpu, from the p9gpu run's flybys.tsv (method
step, counting): their removal step and their last flyby shorter than 1.5
steps (closest distance, planet), and how often that came shortly before the
removal; the same share among the particles that survive in both runs, for
comparison. --gpu may list several segments of one chain (their flybys.tsv
are combined: counts added, the last fast flyby and the removal taken from the
latest segment that has them).
"""

import argparse
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import at_time, dump  # noqa: E402


def survivors(dirs, p9sim, T):
    ids = set()
    for d in map(Path, dirs):
        found = at_time(d, T)
        if found is None:
            continue
        _, rows = dump(p9sim, *found)
        n_active = sum(1 for r in rows if not r[0].startswith("tp"))
        ids |= {n_active + int(r[0][2:]) for r in rows if r[0].startswith("tp")}
    return ids


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def flybys(dirs, dt):
    """id -> record from the flybys.tsv of the segments, in time order."""
    rec = {}
    for d in map(Path, dirs):
        f = d / "flybys.tsv"
        if not f.exists():
            continue
        for row in csv.DictReader(open(f), delimiter="\t"):
            i = int(row["id"])
            r = rec.setdefault(i, {"fast": 0, "close": 0, "removed_step": 0, "last_fast_step": 0, "last_fast_planet": 0, "last_fast_dmin": 0.0})
            r["fast"] += sum(int(v) for k, v in row.items() if k.startswith("fast_"))
            r["close"] += sum(int(v) for k, v in row.items() if k.startswith("close_"))
            if int(row["removed_step"]):
                r["removed_step"] = int(row["removed_step"])
            if int(row["last_fast_step"]):
                r["last_fast_step"] = int(row["last_fast_step"])
                r["last_fast_planet"] = int(float(row["last_fast_planet"]))
                r["last_fast_dmin"] = float(row["last_fast_dmin_au"])
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--merc", nargs="+", required=True)
    ap.add_argument("--gpu", nargs="+", required=True)
    ap.add_argument("--time", type=float, required=True)
    ap.add_argument("--n0", type=int, default=2000)
    ap.add_argument("--dt", type=float, default=0.5)
    a = ap.parse_args()
    all_ids = set(range(6, 6 + a.n0))
    sm, sg = survivors(a.merc, a.p9sim, a.time), survivors(a.gpu, a.p9sim, a.time)
    lm, lg = all_ids - sm, all_ids - sg
    b, c = sorted(lg - lm), sorted(lm - lg)
    print(f"t = {a.time / 1e6:g} Myr: lost in MERCURIUS {len(lm)}, in p9gpu {len(lg)}, in both {len(lm & lg)}")
    print(f"  lost only in p9gpu b = {len(b)}, only in MERCURIUS c = {len(c)}; McNemar exact p = {mcnemar(len(b), len(c)):.3g}")
    rec = flybys(a.gpu, a.dt)
    if not rec:
        print("  (no flybys.tsv: the p9gpu run did not count flybys)")
        return
    names = {1: "Jupiter", 2: "Saturn", 3: "Uranus", 4: "Neptune", 5: "P9", 0: "-"}
    windows = [(1e4, "10 kyr"), (1e5, "100 kyr"), (1e6, "1 Myr")]

    def share(ids):
        out = []
        for w, label in windows:
            k = 0
            for i in ids:
                r = rec.get(i)
                if not r or not r["last_fast_step"]:
                    continue
                end = r["removed_step"] or int(a.time / a.dt)
                if 0 <= (end - r["last_fast_step"]) * a.dt <= w:
                    k += 1
            out.append(f"{k} of {len(ids)} within {label}")
        return ", ".join(out)

    print("  lost only in p9gpu, last flyby shorter than 1.5 steps before the removal: " + share(b))
    both_alive = sorted(sm & sg)
    print("  for comparison, survivors in both runs, such a flyby within the same time before t: " + share(both_alive))
    print("  lost in both: " + share(sorted(lm & lg)))
    print("  lost only in p9gpu (id, removal t [Myr], fast flybys, of them < 0.1 au, last fast: t [Myr], planet, d_min [au]):")
    for i in b:
        r = rec.get(i, {})
        print(f"    {i:5d}  {r.get('removed_step', 0) * a.dt / 1e6:7.3f}  {r.get('fast', 0):3d}  {r.get('close', 0):3d}  "
              f"{r.get('last_fast_step', 0) * a.dt / 1e6:8.3f}  {names.get(r.get('last_fast_planet', 0), '?'):8s}  {r.get('last_fast_dmin', 0):.4f}")


if __name__ == "__main__":
    main()
