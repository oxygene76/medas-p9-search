#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The evaluation of the paired tests V5 against MERCURIUS for sets A and B (docs/bb2021-paired-test-proposal.md),
one set at a time. Committed and named in the chain entry of the criteria before any run; not changed afterwards.

  build/venv/bin/python -I tools/pair_eval.py --set A --v5 V5_DIR --m M_DIR [--p9sim P9SIM] [--json OUT]
                                              [--release-dir DIR]

  V5_DIR  the unpacked package p9pair-v5 with its results: jobs/PV5-s331 ... /segments/seg000 ... seg009
  M_DIR   the unpacked package p9pair-merc with its results: jobs/PM-s331-part00 ... PM-s349-part15/segments/...
  P9SIM   the p9sim of p9prod-9a084ed (sha256 b14f7956...), as for the equivalence test

It refuses to evaluate a set unless all 9 seeds of both groups of that set are complete (every segment done): no
interim look. The statistic, the paired interval and the verdict are those of tools/equiv_eval.py (imported, not
copied, unchanged):
- per run S = the mean over 160, 165, ..., 200 Myr of R(dvarpi) of the distant survivors (a > 230 au, q > 42 au),
  barycentric elements, dvarpi against the Planet Nine of the same simulation (for M: of the slice), the 16 slices of
  a seed pooled at each time;
- per seed d_s = S(V5) - S(M); the mean of the 9 differences and its two-sided 95 % interval (t, 8 degrees of freedom,
  from the measured spread of the 9 differences): "equivalent" inside (-0.035, +0.035), "different" entirely
  outside, else "not shown".

Reported, not deciding:
- R at 200 Myr and S with the cut of the observed sample;
- the test particles left at 200 Myr per group;
- the six encounter shares as in V2 (tools/v2_encounter_check.py): per planet the share of the test particles with
  at least one flyby shorter than 1.5 steps and with at least one within 0.1 au, Neptune, Uranus and Planet Nine,
  over 0-60 Myr (comparable with the V2 reference) and over 0-200 Myr, pooled over the 9 seeds;
- for the V5 half only: p9sim (MERCURIUS) keeps no flyby log per particle.

With --release-dir and only for "equivalent": writes DIR/BB-<set>.paired (the release record of the criteria,
section 5).
"""

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import equiv_eval as ee  # noqa: E402
import v2_encounter_check as v2  # noqa: E402

SETS = {"A": list(range(331, 340)), "B": list(range(341, 350))}
PARTS = 16
V5_PREFIX, M_PREFIX = "PV5", "PM"


def job_complete(job):
    env = dict(l.split("=", 1) for l in (Path(job) / "params.env").read_text().splitlines() if "=" in l and not l.startswith("#"))
    for k in range(int(env["SEGMENTS"])):
        if not (Path(job) / "segments" / f"seg{k:03d}" / "DONE").exists():
            raise SystemExit(f"{job}: segment {k} not done (no interim look)")


def jobs(v5, m, seeds, v5_prefix=V5_PREFIX, m_prefix=M_PREFIX):
    return {s: (Path(v5) / "jobs" / f"{v5_prefix}-s{s}", [Path(m) / "jobs" / f"{m_prefix}-s{s}-part{k:02d}" for k in range(PARTS)]) for s in seeds}


def complete(js):
    for s, (vj, mjs) in js.items():
        for j in [vj] + mjs:
            if not (j / "params.env").exists():
                raise SystemExit(f"{j}: missing")
            job_complete(j)


def left_at_end(job):
    rows = [l.split("\t") for l in (Path(job) / "segments.tsv").read_text().splitlines() if l.strip()]
    return int(rows[-1][2]) - 6


def encounter_shares(v5_jobs, n_segments):
    """Shares (percent) pooled over the seeds: mean of the per-seed shares (the same number of test particles each)."""
    per = [v2.shares(j, n_segments) for j in v5_jobs]
    if any(used < n_segments for _, used, _ in per):
        return None
    out = {}
    for planet in ("Neptune", "Uranus", "P9"):
        out[planet] = {"fast": sum(sh[planet][0] for _, _, sh in per) / len(per), "close": sum(sh[planet][1] for _, _, sh in per) / len(per)}
    return out


def release_text(set_name, seeds, res, version):
    lo, hi = res["S"]["ci95"]
    return ("paired test V5 against MERCURIUS: equivalent\n"
            f"set {set_name}, seeds {seeds[0]}-{seeds[-1]}, 9 pairs\n"
            f"S(V5) - S(M): mean {res['S']['mean']:+.4f}, 95 % interval [{lo:+.4f}, {hi:+.4f}], margin +-{ee.MARGIN}\n"
            f"tools/pair_eval.py {version}; criteria docs/bb2021-paired-test-proposal.md (as entered on chain)\n")


def code_version():
    root = Path(__file__).resolve().parents[1]
    p = subprocess.run(["git", "-C", str(root), "describe", "--tags", "--match", "pair-eval-*", "--dirty", "--always"], capture_output=True, text=True)
    return p.stdout.strip() or "unknown"


def evaluate(set_name, v5, m, p9sim, seeds=None, v5_prefix=V5_PREFIX, m_prefix=M_PREFIX, stats=None):
    seeds = seeds or SETS[set_name]
    js = jobs(v5, m, seeds, v5_prefix, m_prefix)
    complete(js)
    stats = stats or (lambda files: ee.run_stats(files, p9sim))
    runs = {}
    for s, (vj, mjs) in js.items():
        fv = {T: [ee.package_file(vj, T)] for T in ee.TIMES}
        fm = {T: [ee.package_file(j, T) for j in mjs] for T in ee.TIMES}
        runs[s] = {"V5": stats(fv), "M": stats(fm), "left_200": {"V5": left_at_end(vj), "M": sum(left_at_end(j) for j in mjs)}}
        print(f"seed {s}: S  V5 {runs[s]['V5']['S']:.4f}  M {runs[s]['M']['S']:.4f}", flush=True)
    res = {key: ee.paired([runs[s]["V5"][key] - runs[s]["M"][key] for s in seeds]) for key in ("S", "R200", "S_obs_cut")}
    v5_jobs = [js[s][0] for s in seeds]
    enc = {"reported, not deciding": True, "M": "not available: p9sim (MERCURIUS) keeps no flyby log per particle",
           "V5 0-60 Myr": encounter_shares(v5_jobs, 3), "V5 0-200 Myr": encounter_shares(v5_jobs, 10), "V2 reference 0-60 Myr": v2.REFERENCE}
    left = {g: sum(runs[s]["left_200"][g] for s in seeds) for g in ("V5", "M")}
    return {"set": set_name, "seeds": seeds, "criteria": "docs/bb2021-paired-test-proposal.md (as entered on chain)", "margin": ee.MARGIN,
            "runs": runs, "S": res["S"], "information": {"R200": res["R200"], "S_obs_cut": res["S_obs_cut"], "left_200": left,
            "encounter_shares": enc}, "verdict": res["S"]["verdict"]}


def report(out):
    r = out["S"]
    print(f"\nset {out['set']}, S (decision): mean {r['mean']:+.4f}, sd {r['sd']:.4f}, 95 % [{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}] -> {out['verdict']}")
    for key in ("R200", "S_obs_cut"):
        x = out["information"][key]
        print(f"  {key} (information): mean {x['mean']:+.4f}, 95 % [{x['ci95'][0]:+.4f}, {x['ci95'][1]:+.4f}] -> {x['verdict']}")
    left = out["information"]["left_200"]
    print(f"  test particles left at 200 Myr (information): V5 {left['V5']}, M {left['M']}")
    enc = out["information"]["encounter_shares"]
    print("  encounter shares, reported, not deciding (percent of the test particles; M: " + enc["M"] + "):")
    for span in ("V5 0-60 Myr", "V5 0-200 Myr"):
        sh = enc[span]
        if sh is None:
            print(f"    {span}: flyby logs incomplete")
            continue
        print(f"    {span}: " + "; ".join(f"{p} fast {sh[p]['fast']:.2f}, close {sh[p]['close']:.2f}" for p in ("Neptune", "Uranus", "P9")))
    ref = enc["V2 reference 0-60 Myr"]
    print("    V2 reference 0-60 Myr: " + "; ".join(f"{p} fast {ref[p][0]:.2f}, close {ref[p][1]:.2f}" for p in ("Neptune", "Uranus", "P9")))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", required=True, choices=sorted(SETS))
    ap.add_argument("--v5", required=True)
    ap.add_argument("--m", required=True)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--json")
    ap.add_argument("--release-dir")
    # for the test of this tool on the equivalence runs only (tests/test_pair_eval.py): other seeds and job names
    ap.add_argument("--seeds", help=argparse.SUPPRESS)
    ap.add_argument("--v5-prefix", default=V5_PREFIX, help=argparse.SUPPRESS)
    ap.add_argument("--m-prefix", default=M_PREFIX, help=argparse.SUPPRESS)
    a = ap.parse_args()
    seeds = None
    if a.seeds:
        lo, hi = (int(x) for x in a.seeds.split("-"))
        seeds = list(range(lo, hi + 1))
    out = evaluate(a.set, a.v5, a.m, a.p9sim, seeds, a.v5_prefix, a.m_prefix)
    out["tool"] = f"tools/pair_eval.py {code_version()}"
    report(out)
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + "\n")
    if a.release_dir:
        if out["verdict"] == "equivalent":
            Path(a.release_dir).mkdir(parents=True, exist_ok=True)
            f = Path(a.release_dir) / f"BB-{a.set}.paired"
            f.write_text(release_text(a.set, out["seeds"], out, code_version()))
            print(f"release record: {f}")
        else:
            print(f"no release record: the verdict is '{out['verdict']}'")


if __name__ == "__main__":
    main()
