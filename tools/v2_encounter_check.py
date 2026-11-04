#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The V2 condition of docs/bb2021-comparison-criteria.md (addenda 13 and 16): the encounter regime of a short run of
set A or B against that of the equivalence runs.

  python3 -I tools/v2_encounter_check.py JOB_DIR [JOB_DIR ...] [--ok-dir DIR]

JOB_DIR: a job of the short-run package (jobs/V2-A, jobs/V2-B: job.json, segments/seg000..002/flybys.tsv). For each,
the share of the test particles with at least one flyby shorter than 1.5 steps ("fast") and with at least one within
0.1 au ("close"), per planet, over 0-60 Myr, against the reference of the equivalence V5 runs over the same 0-60 Myr
(9 x 4,000 test particles; addendum 13):
  Neptune 17.61 % fast, 4.47 % close; Uranus 2.75 %, 0.84 %; Planet Nine 1.09 %, 0.26 %.
Within the limits if Neptune and Uranus are within +-30 % of the reference (relative) and Planet Nine at most twice
it, for fast and close. With --ok-dir the verdict line is written to DIR/BB-<set>.ok (the 4-Gyr package reads it).
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path

REFERENCE = {"Neptune": (17.61, 4.47), "Uranus": (2.75, 0.84), "P9": (1.09, 0.26)}   # percent, addendum 13
BODY = {1: "Jupiter", 2: "Saturn", 3: "Uranus", 4: "Neptune", 5: "P9"}


def shares(job_dir, n_segments=3):
    job_dir = Path(job_dir)
    n_tp = json.loads((job_dir / "job.json").read_text())["params"]["ic"]["n_tp"]
    segs = sorted(glob.glob(str(job_dir / "segments" / "seg*")))
    fast, close, t = {k: set() for k in BODY}, {k: set() for k in BODY}, 0.0
    used = 0
    for s in segs[:n_segments]:          # segments of 20 Myr: the first three are 0-60 Myr
        p = os.path.join(s, "flybys.tsv")
        if not os.path.exists(os.path.join(s, "DONE")) or not os.path.exists(p):
            break
        lines = [l.split("\t") for l in open(p).read().splitlines() if l.strip()]
        h = lines[0]
        for r in lines[1:]:
            d = dict(zip(h, r))
            for k in BODY:
                if int(d.get(f"fast_{k}", 0)):
                    fast[k].add(d["id"])
                if int(d.get(f"close_{k}", 0)):
                    close[k].add(d["id"])
        used += 1
    return n_tp, used, {BODY[k]: (100 * len(fast[k]) / n_tp, 100 * len(close[k]) / n_tp) for k in BODY}


def verdict(sh):
    ok, notes = True, []
    for planet, (rf, rc) in REFERENCE.items():
        f, c = sh[planet]
        for what, v, ref in (("fast", f, rf), ("close", c, rc)):
            if planet == "P9":
                good = v <= 2 * ref
                notes.append(f"{planet} {what} {v:.2f} % (ref {ref:.2f} %, limit {2 * ref:.2f} %): {'ok' if good else 'OUT'}")
            else:
                good = abs(v / ref - 1) <= 0.30
                notes.append(f"{planet} {what} {v:.2f} % (ref {ref:.2f} %, ratio {v / ref:.2f}, limits 0.70-1.30): {'ok' if good else 'OUT'}")
            ok &= good
    return ("within the limits" if ok else "outside the limits"), notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jobs", nargs="+")
    ap.add_argument("--ok-dir")
    ap.add_argument("--segments", type=int, default=3, help="segments of 20 Myr that must be done (default 3: 0-60 Myr)")
    a = ap.parse_args()
    for j in a.jobs:
        n_tp, used, sh = shares(j, a.segments)
        name = Path(j).name
        if used < a.segments:
            print(f"{name}: only {used} of {a.segments} segments done: no verdict")
            continue
        v, notes = verdict(sh)
        print(f"{name}: {n_tp} test particles, {used} segments; {v}")
        for n in notes:
            print("   " + n)
        if a.ok_dir and name.startswith("V2-"):
            Path(a.ok_dir).mkdir(parents=True, exist_ok=True)
            (Path(a.ok_dir) / f"BB-{name[3:]}.ok").write_text(v + "\n")


if __name__ == "__main__":
    main()
