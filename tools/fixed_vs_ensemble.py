#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""R(dvarpi) and R(dOmega) of one run against the ensemble's MERCURIUS runs, in units of the ensemble scatter.

  build/venv/bin/python -I tools/fixed_vs_ensemble.py [RUN] > runs/cause/fixed-vs-ensemble.txt

RUN as in eval_ensemble.py (default: the fixed-step run gpu-2000-count/count2, member 0). The ensemble
course (m_M, m_G, s, d_G) comes from runs/val/eval-ensemble.json; d_F = (R_F - m_M) / (2 s).
"""

import json
import sys

sys.path.insert(0, "tools")
import eval_ensemble as ee  # noqa: E402

P9SIM = "build/gcc-O3/p9sim"
run = sys.argv[1] if len(sys.argv) > 1 else "F:G:0:runs/val/gpu-2000-count,runs/val/gpu-2000-count2"
ens = json.load(open("runs/val/eval-ensemble.json"))
course = {r["t"]: r for r in ens["course"]}
fixed = ee.parse_run(run)
print("Fixed step (gpu-2000-count/count2: p9gpu without sub-steps, planets 1 step, the start values of G0 and M0) against the ensemble:")
print("d_F = (R_F - m_M) / (2 s), s the run-to-run scatter of the ensemble (G0-G3, M0-M1); for comparison d_G of the ensemble")
for key in ("dvarpi", "dOmega"):
    print(f"\n{key}:   t |   R_F   m_M    M0    M1   m_G    2s |   d_F   d_G | F below both M")
    for T in sorted(course):
        if T < 5e7 and T not in (1e7, 2e7, 3e7, 4e7, 5e7):
            continue
        x = ee.load(fixed, P9SIM, T)
        rf, n = ee.r_distant(x, key)
        c = course[T][key]
        s = c["s"]
        dF = (rf - c["m_M"]) / (2 * s)
        below = rf < min(c["R"]["M0"], c["R"]["M1"])
        print(f"{key:7s} {T/1e6:5.0f} | {rf:.3f} {c['m_M']:.3f} {c['R']['M0']:.3f} {c['R']['M1']:.3f} {c['m_G']:.3f} {2*s:.3f} | {dF:+5.2f} {c['d']:+5.2f} | {'yes' if below else 'no'}")
