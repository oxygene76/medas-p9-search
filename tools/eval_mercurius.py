#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Evaluates the acceptance criteria of docs/validation-mercurius.md.

  python tools/eval_mercurius.py --p9sim build/gcc-O3/p9sim --merc runs/val/merc/part* --gpu runs/val/gpu-2000 [--times 1e7 2e7 3e7 5e7]

The criteria are applied at the last time; the earlier times are printed for
information. Exit code 0 if every criterion holds at the last time.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import at_time, barycentric, dump, elements  # noqa: E402
from compare_stats import ks  # noqa: E402

N_BOOT = 2000


def load(dirs, p9sim, T):
    tps, p9 = [], None
    for d in map(Path, dirs):
        found = at_time(d, T)
        if found is None:
            sys.exit(f"{d}: no snapshot at {T:g}")
        t, rows = dump(p9sim, *found)
        rows, mu = barycentric(rows)
        for name, m, r, v in rows:
            if name == "P9":
                p9 = (r, v)
            elif name.startswith("tp"):
                tps.append((r, v))
    _, _, _, OmP, vpP = elements(mu, p9[0][None, :], p9[1][None, :])
    A, E, I, Om, vp = elements(mu, np.array([x[0] for x in tps]), np.array([x[1] for x in tps]))
    return {"a": A, "q": A * (1 - E), "i": I, "varpi": vp % 360, "Omega": Om % 360,
            "dvarpi": (vp - vpP[0]) % 360, "dOmega": (Om - OmP[0]) % 360}


def R(angles):
    a = np.radians(angles)
    return math.hypot(np.cos(a).mean(), np.sin(a).mean()) if len(a) else float("nan")


def boot_se(angles, rng):
    n = len(angles)
    if n < 2:
        return float("nan")
    idx = rng.integers(0, n, size=(N_BOOT, n))
    a = np.radians(angles)[idx]
    return float(np.hypot(np.cos(a).mean(1), np.sin(a).mean(1)).std(ddof=1))


def evaluate(m, g, n_rule, n0):
    out = {}
    nm, ng = len(m["a"]), len(g["a"])
    fm, fg = nm / n0, ng / n0
    sigma = math.sqrt(n0 * fm * (1 - fm) + n0 * fg * (1 - fg))
    out["survivors"] = {"mercurius": nm, "p9gpu": ng, "difference": abs(nm - ng), "n_rule": n_rule, "sigma": round(sigma, 2),
                        "limit": round(n_rule + 2 * sigma, 2), "pass": abs(nm - ng) <= n_rule + 2 * sigma}
    out["ks"] = {}
    for k in ("a", "q", "i", "varpi", "Omega"):
        d, p = ks(m[k], g[k])
        out["ks"][k] = {"D": round(d, 4), "p": p, "pass": p >= 0.01}
    out["R"] = {}
    for pop in ("distant", "all"):
        sel = (lambda x: (x["a"] > 230) & (x["q"] > 42)) if pop == "distant" else (lambda x: np.ones(len(x["a"]), bool))
        for k in ("dvarpi", "dOmega"):
            am, ag = m[k][sel(m)], g[k][sel(g)]
            rm, rg = R(am), R(ag)
            sm, sg = boot_se(am, np.random.default_rng(1)), boot_se(ag, np.random.default_rng(1))
            lim = 2 * math.sqrt(sm * sm + sg * sg)
            out["R"][f"{pop} {k}"] = {"n": [int(len(am)), int(len(ag))], "R": [round(rm, 4), round(rg, 4)], "se": [round(sm, 4), round(sg, 4)],
                                      "difference": round(abs(rm - rg), 4), "limit": round(lim, 4), "pass": abs(rm - rg) <= lim}
    out["pass"] = out["survivors"]["pass"] and all(v["pass"] for v in out["ks"].values()) and all(v["pass"] for v in out["R"].values())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--merc", nargs="+", required=True)
    ap.add_argument("--gpu", required=True)
    ap.add_argument("--times", nargs="+", type=float, default=[1e7, 2e7, 3e7, 5e7])
    ap.add_argument("--n0", type=int, default=2000)
    a = ap.parse_args()
    res = json.loads((Path(a.gpu) / "result.json").read_text())
    n_rule = int(res["removed_encounter"])
    results = {}
    for T in a.times:
        r = evaluate(load(a.merc, a.p9sim, T), load([a.gpu], a.p9sim, T), n_rule, a.n0)
        results[f"{T:g}"] = r
        s = r["survivors"]
        print(f"t = {T / 1e6:g} Myr  {'PASS' if r['pass'] else 'FAIL'}" + ("  (criteria apply at the last time)" if T != a.times[-1] else "  <- criteria"))
        print(f"  survivors: MERCURIUS {s['mercurius']}, p9gpu {s['p9gpu']}, |diff| {s['difference']} <= n_rule {s['n_rule']} + 2 sigma "
              f"({2 * s['sigma']:.1f}) = {s['limit']}: {'pass' if s['pass'] else 'FAIL'}")
        print("  KS (all survivors): " + ", ".join(f"{k} p={v['p']:.3g}{'' if v['pass'] else ' FAIL'}" for k, v in r["ks"].items()))
        for k, v in r["R"].items():
            print(f"  R {k}: {v['R'][0]:.4f} vs {v['R'][1]:.4f} (n {v['n'][0]}/{v['n'][1]}), |diff| {v['difference']:.4f} <= 2 SE {v['limit']:.4f}: "
                  f"{'pass' if v['pass'] else 'FAIL'}")
    print(json.dumps({"n_rule": n_rule, "results": results}, default=bool), file=sys.stderr)
    return 0 if results[f"{a.times[-1]:g}"]["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
