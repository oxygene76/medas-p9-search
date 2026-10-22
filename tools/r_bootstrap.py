#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Is the run-to-run scatter of R(dvarpi) sampling noise? Bootstrap error within each run against the scatter
between the runs of a group.

  build/venv/bin/python -I tools/r_bootstrap.py > runs/cause/r-bootstrap.txt

Per run (the runs of tools/groups_eval.py): R(dvarpi) of the distant survivors (a > 230 au, q > 42 au) at 200 Myr
and the mean over 160-200 Myr, each with its bootstrap standard error. The bootstrap draws the run's 2,000
particles with replacement (the same draw at every time), so it covers both the selection at each time and the
correlation between the times. Per group: the sd between the runs against the root mean square of the
bootstrap errors, and the ratio (about 1: the scatter between runs is sampling noise of the finite number of
particles; clearly above 1: additional scatter between runs).
"""

import sys

import numpy as np

sys.path.insert(0, "tools")
import eval_ensemble as ee  # noqa: E402
from groups_eval import RUNS, TIMES, complete  # noqa: E402

P9SIM = "build/gcc-O3/p9sim"
B = 2000


def wR(theta, w):
    return abs(np.sum(w * np.exp(1j * theta))) / np.sum(w)


def main():
    rng = np.random.default_rng(20261022)
    times = TIMES  # 160 ... 200 Myr; the last one is 200 Myr
    out = {}
    for g, specs in RUNS.items():
        out[g] = []
        for s in specs:
            run = ee.parse_run(s)
            if not complete(run):
                print(f"{run['label']}: not complete, left out")
                continue
            sel = []
            for T in times:
                x = ee.load(run, P9SIM, T)
                m = (x["a"] > 230) & (x["q"] > 42)
                sel.append((x["i"][m], np.radians(x["dvarpi"][m])))
            one = np.ones(ee.N0)
            r200 = wR(sel[-1][1], one[sel[-1][0]])
            rmean = np.mean([wR(th, one[i]) for i, th in sel])
            b200, bmean = np.empty(B), np.empty(B)
            for k in range(B):
                w = np.bincount(rng.integers(0, ee.N0, ee.N0), minlength=ee.N0).astype(float)
                rs = [wR(th, w[i]) if w[i].sum() > 0 else np.nan for i, th in sel]
                b200[k], bmean[k] = rs[-1], np.mean(rs)
            out[g].append((run["label"], r200, b200.std(ddof=1), rmean, bmean.std(ddof=1), len(sel[-1][0])))
            print(f"{g:3s} {run['label']:3s} n_distant(200) {len(sel[-1][0])}: R200 {r200:.4f} +- {b200.std(ddof=1):.4f} | "
                  f"mean160-200 {rmean:.4f} +- {bmean.std(ddof=1):.4f}", flush=True)
    print("\nper group: sd between runs | rms bootstrap error within a run | ratio")
    for g, rows in out.items():
        if len(rows) < 2:
            continue
        for col, name in ((1, "R200"), (3, "mean160-200")):
            v = np.array([r[col] for r in rows])
            e = np.sqrt(np.mean([r[col + 1] ** 2 for r in rows]))
            print(f"  {g:3s} {name:11s} n {len(rows)}: sd {v.std(ddof=1):.4f} | boot {e:.4f} | {v.std(ddof=1) / e:.2f}")
    allr = [r for rows in out.values() for r in rows]
    for col, name in ((1, "R200"), (3, "mean160-200")):
        # pooled within-group sd (each group around its own mean) against the pooled bootstrap error
        ss = sum(((np.array([r[col] for r in rows]) - np.mean([r[col] for r in rows])) ** 2).sum() for rows in out.values() if len(rows) > 1)
        df = sum(len(rows) - 1 for rows in out.values() if len(rows) > 1)
        e = np.sqrt(np.mean([r[col + 1] ** 2 for r in allr]))
        print(f"  pooled {name:11s} df {df}: sd {np.sqrt(ss / df):.4f} | boot {e:.4f} | {np.sqrt(ss / df) / e:.2f}")


if __name__ == "__main__":
    main()
