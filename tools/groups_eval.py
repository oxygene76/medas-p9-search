#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""R(dvarpi) of the distant survivors per run and the group comparisons of docs/ensemble-groups-plan.md.

  build/venv/bin/python -I tools/groups_eval.py > runs/cause/groups-eval.txt

Groups WH (plain Wisdom-Holman: p9gpu fixed step and REBOUND WHFast), M (MERCURIUS), V5 (p9gpu v5). Per run
R(dvarpi) of the survivors with a > 230 au, q > 42 au at 200 Myr, and the mean over 160-200 Myr (every 5 Myr,
for information). Per pair of groups: difference of the means, Welch t-test (two-sided), 95 % interval.
Runs whose directories are not complete at a time are left out at that time (and named).
"""

import math
import sys

import numpy as np

sys.path.insert(0, "tools")
import eval_ensemble as ee  # noqa: E402

P9SIM = "build/gcc-O3/p9sim"
RUNS = {
    "WH": [
        "F:G:0:runs/val/gpu-2000-count,runs/val/gpu-2000-count2",
        "W:G:0:runs/cause/wh05/part*",
        "F1:G:1:runs/cause/ensfix/m123/seg*",
        "F2:G:2:runs/cause/ensfix/m123/seg*",
        "F3:G:3:runs/cause/ensfix/m123/seg*",
    ],
    "M": [
        "M0:M:0:runs/val/merc/part*,runs/val/merc2/part*",
        "M1:M:4:runs/val/ens-merc/part*",
        "M2:M:5:runs/cause/ensmerc/m5/part*",
        "M3:M:6:runs/cause/ensmerc/m6/part*",
    ],
    "V5": [f"G{m}:G:{m}:runs/val/ens-gpu" for m in range(4)],
}
TIMES = [1.6e8 + 5e6 * k for k in range(9)]


def _betacf(a, b, x):
    """Continued fraction of the regularised incomplete beta function (Lentz)."""
    tiny, qab, qap, qam = 1e-300, a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        for aa in (m * (b - m) * x / ((qam + m2) * (a + m2)), -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))):
            d = 1 + aa * d
            d = 1 / (d if abs(d) > tiny else tiny)
            c = 1 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1) < 1e-15:
            break
    return h


def betainc(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lb = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    if x < (a + 1) / (a + b + 2):
        return math.exp(lb) * _betacf(a, b, x) / a
    return 1 - math.exp(lb) * _betacf(b, a, 1 - x) / b


def t_sf(t, df):
    """P(T > t) of Student's t with df degrees of freedom."""
    p = 0.5 * betainc(df / 2, 0.5, df / (df + t * t))
    return p if t >= 0 else 1 - p


def t_ppf(q, df):
    lo, hi = -1e3, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2
        if 1 - t_sf(mid, df) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def complete(run):
    """All result.json present (a run still computing is left out)."""
    return all((d / "result.json").exists() for d in run["dirs"]) and run["dirs"]


def r_at(run, T):
    x = ee.load(run, P9SIM, T)
    return ee.r_distant(x, "dvarpi")[0]


def welch(a, b):
    a, b = np.asarray(a), np.asarray(b)
    d = a.mean() - b.mean()
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = np.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    t = d / se
    p = 2 * t_sf(abs(t), df)
    h = t_ppf(0.975, df) * se
    return d, se, df, p, (d - h, d + h)


def main():
    per = {}
    for g, specs in RUNS.items():
        per[g] = []
        for s in specs:
            run = ee.parse_run(s)
            if not complete(run):
                print(f"{run['label']}: not complete, left out")
                continue
            r200 = r_at(run, 2e8)
            rmean = float(np.mean([r_at(run, T) for T in TIMES]))
            per[g].append((run["label"], r200, rmean))
    print("\nR(dvarpi), distant survivors (a > 230 au, q > 42 au): at 200 Myr | mean 160-200 Myr")
    for g, rows in per.items():
        for label, r200, rmean in rows:
            print(f"  {g:3s} {label:3s} {r200:.4f} | {rmean:.4f}")
        if rows:
            v = np.array([r[1] for r in rows])
            sd = v.std(ddof=1) if len(v) > 1 else float("nan")
            print(f"  {g:3s} mean {v.mean():.4f}, sd {sd:.4f}, n {len(v)}")
    for col, name in ((1, "at 200 Myr (the statistic)"), (2, "mean 160-200 Myr (for information)")):
        print(f"\nWelch t-test, {name}:")
        for a, b in (("WH", "M"), ("V5", "WH"), ("V5", "M")):
            xa, xb = [r[col] for r in per[a]], [r[col] for r in per[b]]
            if len(xa) < 2 or len(xb) < 2:
                print(f"  {a} - {b}: too few runs")
                continue
            d, se, df, p, ci = welch(xa, xb)
            print(f"  {a} - {b}: {d:+.4f} (se {se:.4f}, df {df:.1f}), p = {p:.3f}, 95 % [{ci[0]:+.4f}, {ci[1]:+.4f}]")


if __name__ == "__main__":
    main()
