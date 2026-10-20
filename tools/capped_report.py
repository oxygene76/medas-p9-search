#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Steps at the cap of 4,096 sub-steps (P9_CAPPED_OUT of p9gpu), grouped into flybys.

  python tools/capped_report.py CAPPED_TSV [--radius-au 1.6554e-4] [--gap 40] [--list]

A flyby: the capped steps of one test particle and planet with gaps of at
most --gap steps. Per flyby the step where the particle comes closest to the
planet (smallest distance at the sub-steps' kicks, d_min). If that is within
--deep au (default 0.1, an eighth of Neptune's Hill radius) the flyby is deep
and its pericentre is q_est of that step: the two-body pericentre around the
planet from the state at the start of that step (q_loc, the same at the
closest kick, comes after the step's own error). Otherwise the cap came from
the pericentre estimate alone, at the edge of r_out, where the Sun's pull
still changes the orbit around the planet, and the particle never came close
in a capped step. Summary: the deep flybys by pericentre in planet radii
(--radius-au; Neptune's equatorial radius 24,764 km by default), and the n
the criteria asked for.
"""

import argparse
import csv

import numpy as np


def flybys(path, gap):
    rows = sorted(csv.DictReader(open(path), delimiter="\t"), key=lambda r: (int(r["id"]), int(r["planet"]), int(r["step"])))
    out = []
    for r in rows:
        k = (int(r["id"]), int(r["planet"]))
        s = int(r["step"])
        if out and out[-1]["key"] == k and s - out[-1]["last"] <= gap:
            f = out[-1]
        else:
            f = {"key": k, "first": s, "steps": 0, "d_min": np.inf, "q_est": np.inf, "q_loc": np.nan, "n_want": 0, "v": 0.0}
            out.append(f)
        f["last"] = s
        f["steps"] += 1
        f["n_want"] = max(f["n_want"], int(r["n_want"]))
        if float(r["d_min_au"]) < f["d_min"]:
            f["d_min"], f["q_est"], f["v"] = float(r["d_min_au"]), float(r["q_est_au"]), float(r["v_est_au_yr"])
            f["q_loc"] = float(r.get("q_loc_au", "nan"))
    return rows, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capped")
    ap.add_argument("--radius-au", type=float, default=24764.0 / 149597870.7)
    ap.add_argument("--gap", type=int, default=40)
    ap.add_argument("--deep", type=float, default=0.1)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    rows, fb = flybys(a.capped, a.gap)
    R = a.radius_au
    d = np.array([float(r["d_min_au"]) for r in rows])
    q = np.array([float(r["q_est_au"]) for r in rows])
    print(f"capped steps {len(rows)}, flybys {len(fb)}; radius {R:.4e} au")
    print(f"steps: distance within the step d_min / R: median {np.median(d) / R:.0f}, 10 % {np.quantile(d, 0.1) / R:.1f}, "
          f"min {d.min() / R:.2f}; estimated pericentre q_est / R: median {np.median(q) / R:.1f}, min {q.min() / R:.2f}")
    deep = [f for f in fb if f["d_min"] < a.deep]
    edge = [f for f in fb if f["d_min"] >= a.deep]
    print(f"edge flybys (capped only at > {a.deep} au, by the estimate): {len(edge)} with {sum(f['steps'] for f in edge)} capped steps")
    print(f"deep flybys (a capped step within {a.deep} au): {len(deep)} with {sum(f['steps'] for f in deep)} capped steps; by pericentre in planet radii:")
    c = np.array([f["q_est"] for f in deep])
    edges = [0, 1, 2, 5, 10, 20, 50, np.inf]
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (c >= lo * R) & (c < hi * R)
        nw = [f["n_want"] for f, k in zip(deep, m) if k]
        print(f"   {lo:>4} - {hi:<4}: {int(m.sum()):4d} flybys" + (f", n asked for up to {max(nw)}" if nw else ""))
    if a.list:
        print("id\tplanet\tfirst_step\tsteps\td_min_au\tq_est_au\tq_loc_au\tv_au_yr\tn_want")
        for f in fb:
            print(f"{f['key'][0]}\t{f['key'][1]}\t{f['first']}\t{f['steps']}\t{f['d_min']:.3e}\t{f['q_est']:.3e}\t{f['q_loc']:.3e}\t{f['v']:.3f}\t{f['n_want']}")


if __name__ == "__main__":
    main()
