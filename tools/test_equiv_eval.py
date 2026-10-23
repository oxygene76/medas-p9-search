#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests of tools/equiv_eval.py on synthetic data and on the exploratory runs of 2026-10-21/22 only (never on the
runs of the equivalence test).

  build/venv/bin/python -I tools/test_equiv_eval.py

- the statistics: t quantiles, the three verdicts, the paired interval against a direct computation
- the packages' time -> (segment, snapshot) mapping, and the refusal when a segment is not done
- the loaders on old runs, linked into the two layouts in a temporary directory:
  the fixed-step run F (runs/val/gpu-2000-count2, member 0) as a p9job chain, and MERCURIUS M2
  (runs/cause/ensmerc/m5, member 5, 8 slices of 250) as package jobs; their S and R at 200 Myr must equal the
  values of tools/groups_eval.py (docs/cause-analysis.md section 10: F 0.6226 / 0.5778, M2 0.6181 / 0.5876),
  which pools the slices as the clarification of 2026-10-23 requires
"""

import math
import os
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import equiv_eval as ev  # noqa: E402

P9SIM = "build/gcc-O3/p9sim"
fails = 0


def check(name, ok, detail=""):
    global fails
    fails += not ok
    print(f"{'OK ' if ok else 'BAD'} {name}{': ' + detail if detail else ''}")


def must_exit(f, *a):
    try:
        f(*a)
    except SystemExit as e:
        return str(e)
    return None


# statistics
check("t quantile 0.975, 8 df = 2.306", abs(ev.t_ppf(0.975, 8) - 2.306004) < 1e-5, f"{ev.t_ppf(0.975, 8):.6f}")
check("t quantile 0.975, 1e6 df = 1.960", abs(ev.t_ppf(0.975, 1e6) - 1.959966) < 1e-4)
d = [0.01, -0.005, 0.0, 0.012, 0.003, -0.002, 0.007, 0.004, 0.001]
r = ev.paired(d)
h = 2.306004 * np.std(d, ddof=1) / 3
check("paired interval", abs(r["ci95"][0] - (np.mean(d) - h)) < 1e-6 and abs(r["ci95"][1] - (np.mean(d) + h)) < 1e-6, str(r["ci95"]))
check("verdict equivalent", r["verdict"] == "equivalent")
check("verdict different", ev.paired([x - 0.08 for x in d])["verdict"] == "different")
check("verdict not shown (interval across -0.035)", ev.paired([x - 0.035 for x in d])["verdict"] == "not shown", str(ev.paired([x - 0.035 for x in d])["ci95"]))
w = [0.09, -0.09, 0.07, -0.07, 0.0, 0.05, -0.05, 0.03, -0.03]
check("verdict not shown (wide, across both limits)", ev.paired(w)["verdict"] == "not shown", str(ev.paired(w)["ci95"]))
check("R of identical angles = 1, of opposite = 0", abs(ev.R([10, 10, 10]) - 1) < 1e-12 and abs(ev.R([0, 180])) < 1e-12)

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    # packages' time mapping (synthetic: 10 segments of 20 Myr, 20 snapshots, all DONE)
    job = tmp / "pkg" / "jobs" / "X"
    for k in range(10):
        (job / "segments" / f"seg{k:03d}").mkdir(parents=True)
        (job / "segments" / f"seg{k:03d}" / "DONE").write_text("")
    (job / "params.env").write_text("# x\nSEGMENT_YR=20000000\nSEGMENTS=10\nSNAPSHOTS_PER_SEGMENT=20\n")
    want = {1.6e8: (7, 19), 1.65e8: (8, 4), 1.8e8: (8, 19), 1.85e8: (9, 4), 2e8: (9, 19)}
    got = {T: ev.package_file(job, T) for T in want}
    check("time -> segment and snapshot", all(got[T] == (job / "segments" / f"seg{k:03d}" / "output.sa", i) for T, (k, i) in want.items()),
          ", ".join(f"{T / 1e6:.0f} Myr -> seg{k:03d}[{i}]" for T, (k, i) in want.items()))
    (job / "segments" / "seg008" / "DONE").unlink()
    check("refuses a segment that is not done", (must_exit(ev.package_file, job, 1.65e8) or "").endswith("not done"))
    check("refuses an incomplete set (complete())", must_exit(ev.complete, tmp / "none", tmp / "none", tmp / "none") is not None)

    # old runs in the two layouts
    root = Path.cwd()
    wh = tmp / "wh" / "s101"
    wh.mkdir(parents=True)
    os.symlink(root / "runs/val/gpu-2000-count2", wh / "seg00")
    m = tmp / "m" / "jobs"
    for k in range(8):
        j = m / f"M-s101-part{k:02d}"
        (j / "segments" / "seg000").mkdir(parents=True)
        (j / "params.env").write_text("SEGMENT_YR=200000000\nSEGMENTS=1\nSNAPSHOTS_PER_SEGMENT=200\n")
        os.symlink(root / f"runs/cause/ensmerc/m5/part{k:02d}/output.sa", j / "segments/seg000/output.sa")
        (j / "segments/seg000/DONE").write_text("")
    f = ev.run_stats(ev.files_wh(tmp / "wh", 101), P9SIM)
    check("F (old fixed step) S = 0.6226", round(f["S"], 4) == 0.6226, f"{f['S']:.6f}")
    check("F (old fixed step) R200 = 0.5778", round(f["R200"], 4) == 0.5778, f"{f['R200']:.6f}")
    mm = ev.run_stats(ev.files_m(tmp / "m", 101, parts=8), P9SIM)
    check("M2 (old MERCURIUS, 8 slices pooled) S = 0.6181", round(mm["S"], 4) == 0.6181, f"{mm['S']:.6f}")
    check("M2 (old MERCURIUS, 8 slices pooled) R200 = 0.5876", round(mm["R200"], 4) == 0.5876, f"{mm['R200']:.6f}, {mm['n_distant_200']} distant")
    # pooling against averaging the slices' R (the bias the clarification avoids), for information
    per = [ev.r_cut(*ev.elements_of([ev.package_file(m / f"M-s101-part{k:02d}", 2e8)], P9SIM)[:3], ev.CUT_MAIN)[0] for k in range(8)]
    print(f"    for information: R at 200 Myr pooled {mm['R200']:.4f}, mean of the 8 slices' R {np.mean(per):.4f}")
    check("pooling a particle twice is refused",
          (must_exit(ev.elements_of, [ev.package_file(m / "M-s101-part00", 2e8)] * 2, P9SIM) or "").startswith("a test particle appears twice"))

print("== ALL OK" if not fails else f"== {fails} FAILED")
sys.exit(1 if fails else 0)
