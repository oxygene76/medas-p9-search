#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Direction and strength of the apsidal clustering over time, for several selections of the distant particles.

  build/venv/bin/python -I tools/cluster_direction.py --p9sim build/gcc-O3/p9sim \\
      --run "M5:5:runs/cause/ensmerc/m5/part*" --times 0 1e7 2e7 ... [--json out.json]

A run is LABEL:MEMBERS:DIRS: the ensemble members (tools/make_ic.py --members, '+'-separated; particles
tp{member * 100000 + i}; 0 for runs without members) and the job or chain directories (comma-separated, globs
allowed; at each time all directories that hold it are used, and their number is reported, so a run whose chains
end at different times is visible).

Per member, time and selection: n, R and circular mean of dvarpi = varpi - varpi_P9 (barycentric elements, as in
tools/analyze.py) and the Rayleigh p-value (tools/analyze.py circ). Anti-alignment with Planet Nine is a mean near
180 deg. Selections: a >= 250 au; a >= 250 au and q > 30 au; a > 230 au and q > 30 au (Brown & Batygin 2019);
for reference a > 230 au and q > 42 au (tools/analyze.py, tools/eval_ensemble.py).
At t = 0 the input.sa of the segment starting at 0 is used.
"""

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import at_time, barycentric, circ, dump, elements  # noqa: E402

SELECTIONS = {
    "a>=250": lambda x: x["a"] >= 250,
    "a>=250,q>30": lambda x: (x["a"] >= 250) & (x["q"] > 30),
    "a>230,q>30": lambda x: (x["a"] > 230) & (x["q"] > 30),
    "a>230,q>42": lambda x: (x["a"] > 230) & (x["q"] > 42),
}


def parse_run(text):
    label, members, dirs = text.split(":", 2)
    paths = []
    for d in dirs.split(","):
        paths += sorted(glob.glob(d)) if any(c in d for c in "*?[") else [d]
    return {"label": label, "members": [int(m) for m in members.split("+")], "dirs": [Path(p) for p in paths]}


def at_start(d):
    """(input.sa, 0) of the job or chain directory's segment that starts at t = 0, or None."""
    for seg in ([d] if (d / "job.json").exists() else sorted(d.glob("seg*"))):
        p = json.loads((seg / "job.json").read_text())["params"]
        if float(p["t_start_yr"]) == 0 and (seg / "input.sa").exists():
            return seg / "input.sa", 0
    return None


def load(run, p9sim, T):
    """Per member: elements of the survivors at T; and the number of directories that hold T."""
    tps, p9s, n_dirs = [], [], 0
    for d in run["dirs"]:
        found = at_start(d) if T == 0 else at_time(d, T)
        if found is None:
            continue
        n_dirs += 1
        _, rows = dump(p9sim, *found)
        rows, mu = barycentric(rows)
        for name, m, r, v in rows:
            if name == "P9":
                p9s.append((r, v))
            elif name.startswith("tp"):
                tps.append((int(name[2:]), r, v))
    if not n_dirs:
        return None, 0
    r9, v9 = p9s[0]
    _, _, _, _, vpP = elements(mu, r9[None, :], v9[None, :])
    k = np.array([x[0] for x in tps])
    A, E, _, _, vp = elements(mu, np.array([x[1] for x in tps]), np.array([x[2] for x in tps]))
    out = {}
    for mem in run["members"]:
        s = k // 100000 == mem
        out[mem] = {"a": A[s], "q": A[s] * (1 - E[s]), "dvarpi": (vp[s] - vpP[0]) % 360}
    return out, n_dirs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--run", action="append", required=True)
    ap.add_argument("--times", nargs="+", type=float, default=[1e7 * k for k in range(21)])
    ap.add_argument("--json")
    a = ap.parse_args()
    runs = [parse_run(t) for t in a.run]
    res = []
    print("dvarpi of the selected survivors: n, R, circular mean (deg); * Rayleigh p < 0.01")
    print(f"{'run':>8} {'t/Myr':>6} {'dirs':>4} | " + " | ".join(f"{s:^21}" for s in SELECTIONS))
    for run in runs:
        for T in a.times:
            x, n_dirs = load(run, a.p9sim, T)
            if x is None:
                continue
            for mem, xm in x.items():
                row = {"run": run["label"], "member": mem, "t_yr": T, "dirs": n_dirs, "of_dirs": len(run["dirs"]),
                       "survivors": int(len(xm["a"]))}
                cells = []
                for name, f in SELECTIONS.items():
                    c = circ(xm["dvarpi"][f(xm)])
                    row[name] = c
                    cells.append(f"{c['n']:4d} {c.get('R', float('nan')):5.3f} {c.get('mean_deg', float('nan')):5.1f}"
                                 f"{'*' if c.get('rayleigh_p', 1) < 0.01 else ' '}")
                res.append(row)
                print(f"{run['label'] + '/' + str(mem):>8} {T / 1e6:6.0f} {n_dirs:2d}/{len(run['dirs']):<2d}| " + " | ".join(cells),
                      flush=True)
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
