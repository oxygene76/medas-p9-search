#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Evaluates the ensemble of docs/validation-ensemble-200myr.md (criteria as committed in 0e14d7e).

  python tools/eval_ensemble.py --p9sim build/gcc-O3/p9sim \\
      --run G0:G:0:runs/val/ens-gpu --run G1:G:1:runs/val/ens-gpu --run G2:G:2:runs/val/ens-gpu --run G3:G:3:runs/val/ens-gpu \\
      --run "M0:M:0:runs/val/merc/part*,runs/val/merc2/part*" --run "M1:M:4:runs/val/ens-merc/part*" \\
      [--times 5e6 ... 2e8] [--out ens.json]

A run is LABEL:GROUP:MEMBER:DIRS: group G (p9gpu) or M (MERCURIUS), the
ensemble member (tools/make_ic.py --members; its particles are named
tp{member * 100000 + i}), and the job directories (comma-separated, globs
allowed; at each time the one that holds it is used).

Measures at each time: R(dvarpi) and R(dOmega) of the distant survivors (a >
230 au, q > 42 au) per run; per group the mean; s the pooled standard
deviation of the runs about their group's mean (s^2 = sum of squares / (n_G
- 1 + n_M - 1)).
Criterion 1: |m_G - m_M| <= 2 s for both measures at 100, 150 and 200 Myr.
Criterion 2 (systematic): at 200 Myr all G values below all M values, for
either measure. Passed: criterion 1 holds and criterion 2 does not apply.
Also, per run and not part of the decision: the criteria of
tools/eval_mercurius.py (survivors, KS, R within 2 bootstrap SE) and the
paired losses with McNemar, for each G run against each M run and M1 against
M0, at 100, 150 and 200 Myr.
"""

import argparse
import glob
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import at_time, barycentric, dump, elements  # noqa: E402
import eval_mercurius as em  # noqa: E402
from pair_losses import mcnemar  # noqa: E402

N0 = 2000


def parse_run(text):
    label, group, member, dirs = text.split(":", 3)
    paths = []
    for d in dirs.split(","):
        paths += sorted(glob.glob(d)) if any(c in d for c in "*?[") else [d]
    return {"label": label, "group": group, "member": int(member), "dirs": [Path(p) for p in paths]}


def load(run, p9sim, T):
    """Elements of the run's member's survivors at T: dict of arrays and the particle indices i."""
    tps, p9, found_any = [], None, False
    for d in run["dirs"]:
        found = at_time(d, T)
        if found is None:
            continue
        found_any = True
        _, rows = dump(p9sim, *found)
        rows, mu = barycentric(rows)
        for name, m, r, v in rows:
            if name == "P9":
                p9 = (r, v)
            elif name.startswith("tp"):
                k = int(name[2:])
                if k // 100000 == run["member"]:
                    tps.append((k % 100000, r, v))
    if not found_any:
        sys.exit(f"{run['label']}: no snapshot at {T:g}")
    _, _, _, OmP, vpP = elements(mu, p9[0][None, :], p9[1][None, :])
    A, E, I, Om, vp = elements(mu, np.array([x[1] for x in tps]), np.array([x[2] for x in tps]))
    return {"i": np.array([x[0] for x in tps]), "a": A, "q": A * (1 - E), "i_deg": I, "inc": I, "varpi": vp % 360, "Omega": Om % 360,
            "dvarpi": (vp - vpP[0]) % 360, "dOmega": (Om - OmP[0]) % 360}


def r_distant(x, key):
    sel = (x["a"] > 230) & (x["q"] > 42)
    return em.R(x[key][sel]), int(sel.sum())


def pair(m, g):
    """Losses paired by particle: (only g lost, only m lost, both lost, McNemar p)."""
    sm, sg = set(m["i"].tolist()), set(g["i"].tolist())
    allp = set(range(N0))
    lm, lg = allp - sm, allp - sg
    b, c = len(lg - lm), len(lm - lg)
    return b, c, len(lg & lm), mcnemar(b, c)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--run", action="append", required=True)
    ap.add_argument("--times", nargs="+", type=float, default=[5e6 * k for k in range(1, 41)])
    ap.add_argument("--out")
    a = ap.parse_args()
    runs = [parse_run(t) for t in a.run]
    G = [r for r in runs if r["group"] == "G"]
    M = [r for r in runs if r["group"] == "M"]
    out = {"runs": [r["label"] for r in runs], "course": [], "criteria": {}, "per_run": {}}
    print("R of the distant survivors (a > 230 au, q > 42 au) per run; m_G, m_M the group means, s the pooled run-to-run SD; "
          "d = (m_G - m_M) / (2 s)")
    for key in ("dvarpi", "dOmega"):
        print(f"\n{key}:   t | " + " ".join(f"{r['label']:>6}" for r in runs) + " |    m_G    m_M      s      d")
    data = {}
    for T in a.times:
        x = {r["label"]: load(r, a.p9sim, T) for r in runs}
        data[T] = x
        row = {"t": T}
        for key in ("dvarpi", "dOmega"):
            vals = {lab: r_distant(x[lab], key) for lab in x}
            g = np.array([vals[r["label"]][0] for r in G])
            mm = np.array([vals[r["label"]][0] for r in M])
            ss = ((g - g.mean()) ** 2).sum() + ((mm - mm.mean()) ** 2).sum()
            dof = len(g) - 1 + len(mm) - 1
            s = math.sqrt(ss / dof) if dof > 0 else float("nan")
            d = (g.mean() - mm.mean()) / (2 * s) if s > 0 else float("nan")
            row[key] = {"R": {lab: round(v[0], 4) for lab, v in vals.items()}, "n": {lab: v[1] for lab, v in vals.items()},
                        "m_G": round(float(g.mean()), 4), "m_M": round(float(mm.mean()), 4), "s": round(s, 4), "d": round(d, 3),
                        "pass": bool(abs(g.mean() - mm.mean()) <= 2 * s), "all_G_below_all_M": bool(g.max() < mm.min())}
            print(f"{key:7s} {T / 1e6:5.0f} | " + " ".join(f"{vals[r['label']][0]:6.4f}" for r in runs)
                  + f" | {g.mean():6.4f} {mm.mean():6.4f} {s:6.4f} {d:+6.2f}{'' if row[key]['pass'] else '  FAIL'}"
                  + ("  (all G below all M)" if row[key]["all_G_below_all_M"] else ""))
        out["course"].append(row)
    check = [T for T in (1e8, 1.5e8, 2e8) if T in data]
    c1 = all(r[key]["pass"] for r in out["course"] if r["t"] in check for key in ("dvarpi", "dOmega"))
    last = [r for r in out["course"] if r["t"] == 2e8]
    c2 = bool(last) and any(last[0][key]["all_G_below_all_M"] for key in ("dvarpi", "dOmega"))
    out["criteria"] = {"times": check, "criterion_1_mean_within_2s": c1, "criterion_2_systematic": c2, "pass": c1 and not c2}
    print(f"\ncriterion 1 (|m_G - m_M| <= 2 s at {', '.join(f'{t / 1e6:.0f}' for t in check)} Myr, both measures): {'holds' if c1 else 'FAILS'}")
    print(f"criterion 2 (at 200 Myr all G below all M): {'APPLIES (systematic)' if c2 else 'does not apply'}")
    print(f"ensemble: {'PASSED' if c1 and not c2 else 'NOT PASSED'}")
    print("\nper run, for information (criteria of tools/eval_mercurius.py and McNemar):")
    pairs = [(g, m) for g in G for m in M] + ([(M[1], M[0])] if len(M) > 1 else [])
    for T in check:
        for g, m in pairs:
            xm, xg = dict(data[T][m["label"]]), dict(data[T][g["label"]])
            xm["i"], xg["i"] = xm.pop("i_deg"), xg.pop("i_deg")  # eval_mercurius uses "i" for the inclination
            res = em.evaluate(xm, xg, 0, N0)
            b, c, both, p = pair(data[T][m["label"]], data[T][g["label"]])
            failed = [k for k in ("survivors",) if not res["survivors"]["pass"]] + [f"KS {k}" for k, v in res["ks"].items() if not v["pass"]] \
                + [f"R {k}" for k, v in res["R"].items() if not v["pass"]] + (["McNemar"] if p < 0.05 else [])
            out["per_run"][f"{g['label']} vs {m['label']} {T / 1e6:.0f}"] = {**res, "mcnemar": {"only_first": b, "only_second": c, "both": both, "p": p},
                                                                             "failed": failed}
            print(f"  {T / 1e6:3.0f} Myr {g['label']} vs {m['label']}: survivors {res['survivors']['p9gpu']}/{res['survivors']['mercurius']}, "
                  f"McNemar {b}/{c}/{both} p={p:.2f}; failed: {', '.join(failed) if failed else 'none'}")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    sys.exit(0 if c1 and not c2 else 1)


if __name__ == "__main__":
    main()
