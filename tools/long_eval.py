#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The evaluation of the paired long runs, seeds 110-112, V5 against MERCURIUS, exactly as
docs/long-runs-110-112-criteria.md (entered with entry 3, commit 7302607) sections 2 and 3. Written after the runs
and before any look at R; committed and timestamped before the evaluation (docs/long-runs-evaluation-procedure.md).

  build/venv/bin/python -I tools/long_eval.py --v5 V5_DIR --m M_DIR --p9sim P9SIM --out OUT [--jobs 4]

  V5_DIR  the unpacked p9long-v5-ac47329 with its results: jobs/V5-s110 ... V5-s112/segments/seg000 ... seg039
  M_DIR   the unpacked p9long-merc-ac47329 with its results: jobs/M-s110-part00 ... M-s112-part07/segments/seg000 ...
          seg199
  P9SIM   the p9sim of p9prod-9a084ed (reads the snapshots of both groups)
  OUT     a new directory: result.json, timeseries.csv, report.txt (an existing directory is refused)

It refuses to evaluate unless every segment of all six runs is done (no interim look), and unless the start values
are paired: at t = 0 the 8 MERCURIUS slices of a seed together hold exactly the test particles of the V5 run, with
the same values.

The statistic (section 2): R(dvarpi), the mean resultant length, of the distant survivors (a > 230 au, q > 42 au;
barycentric elements; dvarpi = varpi minus that of the Planet Nine of the same simulation at the same snapshot), per
snapshot (every 10 Myr); for M the slices of a seed are pooled at each snapshot before R is computed. Per run
S(t) = the mean of R over the 11 snapshots from t - 100 Myr to t, for t = 0.5, 1, 2, 4 Gyr, and S(1-4) = the mean
over the 301 snapshots from 1 to 4 Gyr. Per seed d_s(t) = S(V5, s, t) - S(M, s, t); over the seeds the mean d(t)
and its standard error sd / sqrt(3).

Too few survivors (section 3): a window in which a run has fewer than 100 distant survivors in more than half of
its snapshots gets no S for that run. A time is used only if all six runs have S there (d(t) from the three
differences). Fewer than three of the four times left: "not decided".

The decision (section 3, Q1 of section 7): "growing bias found" if |d(4)| >= 0.05 and |d(4)| > 2 standard errors,
d has the same sign at 1, 2 and 4 Gyr (those of them that are left), and |d(4)| > |d(0.5)|; otherwise "no growing bias
found". Where the criteria leave a case open, the tool takes the reading of docs/long-runs-evaluation-procedure.md
section 3: without d(4 Gyr) or d(0.5 Gyr) the result is "not decided". S(1-4) is reported, it does not decide.
"""

import argparse
import csv
import io
import json
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import equiv_eval as ee  # noqa: E402
from analyze import dump  # noqa: E402

SEEDS = [110, 111, 112]
PARTS = 8
STEP = 10_000_000                        # yr between snapshots
SNAPS = [STEP * k for k in range(1, 401)]  # 10 Myr ... 4 Gyr
TIMES = {"0.5": 500_000_000, "1": 1_000_000_000, "2": 2_000_000_000, "4": 4_000_000_000}
WIN = 100_000_000                        # t - 100 Myr ... t: 11 snapshots
SPAN_1_4 = (1_000_000_000, 4_000_000_000)
MIN_DISTANT = 100
THRESHOLD = 0.05
N_SE = 2.0


# --- the statistics, without data ------------------------------------------------------------------------------------

def window(T0, T1):
    return [T for T in SNAPS if T0 <= T <= T1]


def window_S(series, T0, T1):
    """series: {T: (R, n_distant)} of one run. S over the snapshots T0..T1, or None if more than half of them have
    fewer than MIN_DISTANT distant survivors."""
    w = window(T0, T1)
    few = sum(1 for T in w if series[T][1] < MIN_DISTANT)
    if few > len(w) / 2:
        return None
    return float(np.mean([series[T][0] for T in w]))


def run_S(series):
    out = {t: window_S(series, T - WIN, T) for t, T in TIMES.items()}
    out["1-4"] = window_S(series, *SPAN_1_4)
    return out


def mean_se(diffs):
    d = np.asarray(diffs, float)
    sd = float(d.std(ddof=1))
    return {"n": len(d), "mean": float(d.mean()), "sd": sd, "se": sd / math.sqrt(len(d)), "d_s": [float(x) for x in d]}


def dbar(S, seeds=SEEDS):
    """S: {seed: {"V5": run_S, "M": run_S}} -> {time: mean_se or None}; a time only if every run has S there."""
    out = {}
    for t in list(TIMES) + ["1-4"]:
        vals = [(S[s]["V5"][t], S[s]["M"][t]) for s in seeds]
        out[t] = None if any(v is None or m is None for v, m in vals) else mean_se([v - m for v, m in vals])
    return out


def decide(d):
    """d: {time: mean_se or None} -> (verdict, reasons)."""
    left = [t for t in TIMES if d[t] is not None]
    if len(left) < 3:
        return "not decided", [f"only {len(left)} of the four times left ({', '.join(left) or 'none'})"]
    for t in ("4", "0.5"):
        if d[t] is None:
            return "not decided", [f"no d at {t} Gyr (reading of the procedure, section 3)"]
    m4, se4 = d["4"]["mean"], d["4"]["se"]
    size = abs(m4) >= THRESHOLD and abs(m4) > N_SE * se4
    signs = [t for t in ("1", "2", "4") if d[t] is not None]
    same = m4 != 0 and all(np.sign(d[t]["mean"]) == np.sign(m4) for t in signs)
    grows = abs(m4) > abs(d["0.5"]["mean"])
    reasons = [f"|d(4)| = {abs(m4):.4f} {'>=' if abs(m4) >= THRESHOLD else '<'} {THRESHOLD} and "
               f"{'>' if abs(m4) > N_SE * se4 else '<='} 2 SE = {N_SE * se4:.4f}: {'yes' if size else 'no'}",
               f"same sign at {', '.join(signs)} Gyr: {'yes' if same else 'no'}",
               f"|d(4)| > |d(0.5)| = {abs(d['0.5']['mean']):.4f}: {'yes' if grows else 'no'}"]
    return ("growing bias found" if size and same and grows else "no growing bias found"), reasons


# --- the data -------------------------------------------------------------------------------------------------------

def env_of(job):
    return dict(l.split("=", 1) for l in (Path(job) / "params.env").read_text().splitlines() if "=" in l and not l.startswith("#"))


def jobs(v5, m, seeds=SEEDS, parts=PARTS):
    return {s: (Path(v5) / "jobs" / f"V5-s{s}", [Path(m) / "jobs" / f"M-s{s}-part{k:02d}" for k in range(parts)]) for s in seeds}


def complete(js):
    """Every segment of every job done, and each job reaches 4 Gyr (raises SystemExit otherwise)."""
    for s, (vj, mjs) in js.items():
        for job in [vj] + mjs:
            env = env_of(job)
            n, seg_yr = int(env["SEGMENTS"]), int(env["SEGMENT_YR"])
            if n * seg_yr != SNAPS[-1] or (seg_yr // int(env["SNAPSHOTS_PER_SEGMENT"])) != STEP:
                raise SystemExit(f"{job}: segments do not give a snapshot every 10 Myr to 4 Gyr")
            for k in range(n):
                if not (job / "segments" / f"seg{k:03d}" / "DONE").exists():
                    raise SystemExit(f"{job}: segment {k} not done (no interim look)")


def tp_rows(p9sim, sa, idx):
    _, rows = dump(p9sim, sa, idx)
    return {name: (m, tuple(r), tuple(v)) for name, m, r, v in rows if name.startswith("tp")}, \
        sorted((name, m, tuple(r), tuple(v)) for name, m, r, v in rows if not name.startswith("tp"))


def start_paired(js, p9sim):
    """At t = 0 the slices of a seed hold exactly the test particles of the V5 run, with the same values, and the
    same Sun and planets. Returns {seed: number of test particles}; raises SystemExit otherwise."""
    out = {}
    for s, (vj, mjs) in js.items():
        tv, pv = tp_rows(p9sim, vj / "input.sa", 0)
        tm = {}
        for j in mjs:
            t, p = tp_rows(p9sim, j / "input.sa", 0)
            if p != pv:
                raise SystemExit(f"seed {s}: {j.name} starts with other massive bodies than V5")
            if set(t) & set(tm):
                raise SystemExit(f"seed {s}: a test particle in two slices")
            tm.update(t)
        if tm != tv:
            raise SystemExit(f"seed {s}: the slices do not hold exactly the test particles of V5 "
                             f"({len(tm)} against {len(tv)}, {len(set(tm) ^ set(tv))} not in both)")
        out[s] = len(tv)
    return out


def series_of(job_list, p9sim, pool):
    """{T: (R, n_distant, n_tp)} of one run (its jobs pooled at each snapshot)."""
    def one(T):
        a, q, dv, n = ee.elements_of([ee.package_file(j, T) for j in job_list], p9sim)
        r, nd = ee.r_cut(a, q, dv, ee.CUT_MAIN)
        return T, (float(r), nd, n)
    return dict(pool.map(one, SNAPS))


def left_at_end(job):
    rows = [l.split("\t") for l in (Path(job) / "segments.tsv").read_text().splitlines() if l.strip()]
    return int(rows[-1][2]) - 6        # N_end minus the Sun and five planets


def evaluate(v5, m, p9sim, n_jobs=4, seeds=SEEDS, parts=PARTS, series=None):
    js = jobs(v5, m, seeds, parts)
    complete(js)
    paired = start_paired(js, p9sim) if series is None else None
    series = series or (lambda jl, pool: series_of(jl, p9sim, pool))
    data, S = {}, {}
    with ThreadPoolExecutor(max_workers=n_jobs) as pool:
        for s, (vj, mjs) in js.items():
            data[s] = {"V5": series([vj], pool), "M": series(mjs, pool)}
            S[s] = {g: run_S(data[s][g]) for g in ("V5", "M")}
            print(f"seed {s}: done", flush=True)
    d = dbar(S, seeds)
    verdict, reasons = decide(d)
    few = {f"{s} {g}": [T for T in SNAPS if data[s][g][T][1] < MIN_DISTANT] for s in seeds for g in ("V5", "M")}
    out = {"criteria": "docs/long-runs-110-112-criteria.md (entry 3, commit 7302607), sections 2 and 3",
           "seeds": seeds, "threshold": THRESHOLD, "n_se": N_SE, "min_distant": MIN_DISTANT,
           "start_paired_tp": paired, "S": {str(s): S[s] for s in seeds}, "d": d, "verdict": verdict, "reasons": reasons,
           "information": {"S(1-4) reported, not deciding": d["1-4"],
                           "snapshots with fewer than 100 distant survivors": {k: len(v) for k, v in few.items()},
                           "test particles left at 4 Gyr": {str(s): {"V5": left_at_end(js[s][0]),
                                                                     "M": sum(left_at_end(j) for j in js[s][1])} for s in seeds},
                           "power": "three pairs can find only large biases; 'no growing bias found' is not evidence "
                                    "that there is none (about 0.05, docs/equivalence-criteria.md)"}}
    return out, data


def timeseries_csv(data, seeds=SEEDS):
    f = io.StringIO()
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["seed", "group", "t_yr", "R", "n_distant", "n_tp"])
    for s in seeds:
        for g in ("V5", "M"):
            for T in SNAPS:
                r, nd, n = data[s][g][T]
                w.writerow([s, g, T, f"{r:.10f}", nd, n])
    return f.getvalue()


def report(out):
    L = ["Paired long runs, seeds 110-112, V5 against MERCURIUS (" + out["criteria"] + ")", ""]
    if out["start_paired_tp"]:
        L.append("start values paired: " + ", ".join(f"seed {s} {n} test particles" for s, n in out["start_paired_tp"].items()))
    L.append("S(t) per run (- = too few distant survivors in the window):")
    fmt = (lambda x: "-" if x is None else f"{x:.4f}")
    for s, g in out["S"].items():
        for grp in ("V5", "M"):
            L.append(f"  seed {s} {grp:2s}: " + "  ".join(f"S({t}) {fmt(g[grp][t])}" for t in list(TIMES) + ["1-4"]))
    L.append("d(t) = mean over the seeds of S(V5) - S(M), with its standard error:")
    for t in list(TIMES) + ["1-4"]:
        x = out["d"][t]
        tag = " (reported, not deciding)" if t == "1-4" else ""
        L.append(f"  {t:>3s} Gyr: " + ("not computed" if x is None else
                 f"{x['mean']:+.4f} +- {x['se']:.4f} (d_s " + ", ".join(f"{v:+.4f}" for v in x["d_s"]) + ")") + tag)
    L += ["", "decision: " + out["verdict"]] + ["  " + r for r in out["reasons"]]
    L += ["", "information:"]
    L.append("  test particles left at 4 Gyr: " + "; ".join(f"seed {s} V5 {v['V5']}, M {v['M']}"
             for s, v in out["information"]["test particles left at 4 Gyr"].items()))
    L.append("  snapshots with fewer than 100 distant survivors: " + ", ".join(
             f"{k} {v}" for k, v in out["information"]["snapshots with fewer than 100 distant survivors"].items()))
    L.append("  power: " + out["information"]["power"])
    return "\n".join(L) + "\n"


def code_version():
    try:
        here = Path(__file__).resolve().parent
        c = subprocess.run(["git", "-C", str(here), "describe", "--always", "--dirty"], capture_output=True, text=True).stdout.strip()
        return c or "unknown"
    except OSError:
        return "unknown"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--v5", required=True)
    ap.add_argument("--m", required=True)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    out_dir = Path(a.out)
    if out_dir.exists():
        raise SystemExit(f"{out_dir} exists; the output goes into a new directory")
    out, data = evaluate(a.v5, a.m, a.p9sim, a.jobs)
    out["tool"] = f"tools/long_eval.py {code_version()}"
    out_dir.mkdir(parents=True)
    (out_dir / "result.json").write_text(json.dumps(out, indent=1) + "\n")
    (out_dir / "timeseries.csv").write_text(timeseries_csv(data))
    text = report(out)
    (out_dir / "report.txt").write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
