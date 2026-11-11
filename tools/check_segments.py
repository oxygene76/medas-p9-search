#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Integrity check of the segment chains of run packages (p9gpu and p9sim jobs), without looking at any result
measure. Used before an evaluation (docs/paired-tests-evaluation-procedure.md); the same checks as for the long runs
110-112 (docs/long-runs-evaluation-procedure.md section 1).

  build/venv/bin/python -I tools/check_segments.py --p9sim P9SIM --jobs DIR/jobs/PV5-s331 ... [--pair V5JOB=MPREFIX ...]

Per job (params.env, input.sa, INPUT-SHA256, segments.tsv, segments/segNNN):
- every segment has DONE; the input and output hashes in DONE equal the files; its result line equals result.txt and
  the row of segments.tsv; final.state equals final_state_sha256; t equals (k + 1) * SEGMENT_YR;
- N_start of segment 0 is the number of bodies of input.sa, N_start of segment k equals N_end of segment k - 1, and
  N_start - N_end equals removed;
- the state of the last snapshot of each segment equals its final_state_sha256 and the state of the next segment's
  input (states, not bytes: REBOUND writes wall times and a random seed into the archive);
- segment 0's input equals the job's input.sa, whose sha256 equals INPUT-SHA256.
Reported as information: the model counters removed_encounter, collisions and sub_capped where not zero.
--pair V5JOB=MPREFIX: at t = 0 the slices MPREFIX-part00 ... hold exactly the test particles of V5JOB, with the same
values, and the same massive bodies.
Exit 1 if any check fails.
"""

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import dump  # noqa: E402


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fields(line):
    return dict(x.split("=", 1) for x in line.split() if "=" in x)


def state(p9sim, sa, idx):
    out = subprocess.run([p9sim, "state", str(sa), str(idx)], capture_output=True, text=True, check=True).stdout
    return fields(out.strip().splitlines()[-1])


def env_of(job):
    return dict(l.split("=", 1) for l in (job / "params.env").read_text().splitlines() if "=" in l and not l.startswith("#"))


def check_job(job, p9sim, report):
    fail = []
    env = env_of(job)
    n, seg_yr = int(env["SEGMENTS"]), int(float(env["SEGMENT_YR"]))
    if sha(job / "input.sa") != (job / "INPUT-SHA256").read_text().split()[0]:
        fail.append("input.sa does not match INPUT-SHA256")
    rows = [l.split("\t") for l in (job / "segments.tsv").read_text().splitlines() if l.strip()]
    if len(rows) != n:
        fail.append(f"segments.tsv has {len(rows)} rows, not {n}")
    n0 = int(state(p9sim, job / "input.sa", 0)["N"])
    prev_n, prev_fs = None, None
    for k in range(n):
        s = job / "segments" / f"seg{k:03d}"
        tag = f"segment {k}"
        if not (s / "DONE").exists():
            fail.append(f"{tag}: no DONE")
            continue
        done = (s / "DONE").read_text().splitlines()
        line = next((l for l in (s / "result.txt").read_text().splitlines() if l.startswith("result_sha256=")), "")
        f = fields(line)
        if len(done) < 3 or done[2] != line:
            fail.append(f"{tag}: DONE line differs from result.txt")
        if done[0] != f"input_sha256={sha(s / 'input.sa')}":
            fail.append(f"{tag}: input hash")
        if done[1] != f"output_sha256={sha(s / 'output.sa')}":
            fail.append(f"{tag}: output hash")
        if f.get("final_state_sha256") != sha(s / "final.state"):
            fail.append(f"{tag}: final.state")
        if float(f.get("t", "nan")) != (k + 1) * seg_yr:
            fail.append(f"{tag}: t {f.get('t')}")
        ns, ne, rm = int(f["N_start"]), int(f["N_end"]), int(f["removed"])
        if ns - ne != rm:
            fail.append(f"{tag}: N_start - N_end != removed")
        if k == 0:
            if (s / "input.sa").read_bytes() != (job / "input.sa").read_bytes():
                fail.append(f"{tag}: input differs from the job's input.sa")
            if ns != n0:
                fail.append(f"{tag}: N_start {ns}, input has {n0}")
        else:
            if ns != prev_n:
                fail.append(f"{tag}: N_start {ns} after N_end {prev_n}")
            if state(p9sim, s / "input.sa", 0)["state_sha256"] != prev_fs:
                fail.append(f"{tag}: input state differs from the final state of segment {k - 1}")
        last = state(p9sim, s / "output.sa", -1)
        if last["state_sha256"] != f["final_state_sha256"] or int(last["N"]) != ne:
            fail.append(f"{tag}: last snapshot differs from final_state_sha256 or N_end")
        if k < len(rows):
            r = rows[k]
            if (int(r[0]), float(r[1]), int(r[2]), r[4]) != (k, (k + 1) * seg_yr, ne, f["result_sha256"]):
                fail.append(f"{tag}: segments.tsv row")
        for key in ("removed_encounter", "sub_capped"):
            if f.get(key, "0") not in ("0", "-"):
                report.append(f"info {job.name} {tag}: {key}={f[key]}" + (f" collisions={f.get('collisions')}" if key == "removed_encounter" else ""))
        prev_n, prev_fs = ne, f["final_state_sha256"]
    return fail, (rows[-1][2], rows[-1][4]) if rows else None


def tp_rows(p9sim, sa):
    _, rows = dump(p9sim, sa, 0)
    tps = {name: (m, tuple(r), tuple(v)) for name, m, r, v in rows if name.startswith("tp")}
    massive = sorted((name, m, tuple(r), tuple(v)) for name, m, r, v in rows if not name.startswith("tp"))
    return tps, massive


def check_pair(v5job, slices, p9sim):
    tv, pv = tp_rows(p9sim, v5job / "input.sa")
    tm = {}
    for j in slices:
        t, p = tp_rows(p9sim, j / "input.sa")
        if p != pv:
            return f"{j.name}: other massive bodies than {v5job.name}"
        if set(t) & set(tm):
            return f"{j.name}: a test particle in two slices"
        tm.update(t)
    if tm != tv:
        return f"{v5job.name}: the slices hold {len(tm)} test particles, V5 {len(tv)}, {len(set(tm) ^ set(tv))} not in both"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--jobs", nargs="+", required=True)
    ap.add_argument("--pair", nargs="*", default=[], help="V5JOB=MPREFIX (directory prefix of the slices)")
    a = ap.parse_args()
    bad, report = 0, []
    for j in a.jobs:
        job = Path(j)
        fail, last = check_job(job, a.p9sim, report)
        for x in fail:
            print(f"FAIL {job.name}: {x}")
        bad += len(fail)
        print(f"{job.name}: {'ok' if not fail else str(len(fail)) + ' failures'}; last row N {last[0] if last else '-'}, result {last[1] if last else '-'}", flush=True)
    for p in a.pair:
        v5, prefix = p.split("=", 1)
        slices = sorted(Path(prefix).parent.glob(Path(prefix).name + "-part*"))
        err = check_pair(Path(v5), slices, a.p9sim) if slices else f"{prefix}: no slices"
        print(f"pair {Path(v5).name} with {len(slices)} slices: {'ok' if err is None else 'FAIL ' + err}")
        bad += err is not None
    for x in report:
        print(x)
    print(f"failures: {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
