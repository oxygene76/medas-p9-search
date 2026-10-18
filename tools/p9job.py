#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Work packages ("jobs") of the Planet 9 orbit integrations.

A job is a directory with
  job.json    description: parameters, code version, input file with sha256
              and size, and the job id = sha256 over the canonical JSON of
              {schema, code, params, input}
  input.sa    the start state (REBOUND SimulationArchive, one snapshot)
Running it (on any machine, with a p9sim built from the same code) gives
  result.json result_sha256 (over the canonical states of all snapshots; the
              number to compare), final state hash, steps, particles left,
              wall and CPU time, platform, build flags, output size
  output.sa   the snapshots (its bytes differ between machines: REBOUND stores
              wall times in it; compare result_sha256, never the file)

  p9job.py make  --out DIR --t-end T --snapshots N [--n-tp 4000 --tp-from A --tp-to B --seed 9]
  p9job.py next  --prev DIR --out DIR --t-end T --snapshots N     (next segment of a chain)
  p9job.py run   DIR [--p9sim build/gcc-O3/p9sim] [--result-name result.json]
  p9job.py check DIR --expected HASH                              (exit 0 if equal)
"""

import argparse
import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "medas-p9-search/job/1"
REBOUND = {"version": "5.2.2", "source": "https://codeload.github.com/hannorein/rebound/tar.gz/refs/tags/5.2.2",
           "sha256": "86038080c4392c8c19c4df2004d1804b30ca2aebd3c0329bfd1b02afc41d6eda", "licence": "GPL-3.0-or-later"}
DEFAULT_P9SIM = ROOT / "build/gcc-O3/p9sim"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def code_version():
    rev = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True).stdout.strip()
    return {"p9sim_commit": rev or None, "dirty": bool(dirty), "rebound": REBOUND,
            "build": "make (see Makefile): -std=c99 -fno-fast-math -ffp-contract=off, any -O level and compiler"}


def write_job(out: Path, params, input_sa: Path):
    job = {"schema": SCHEMA, "code": code_version(), "params": params,
           "input": {"file": "input.sa", "sha256": sha256_file(input_sa), "bytes": input_sa.stat().st_size}}
    job["id"] = hashlib.sha256(canonical(job)).hexdigest()
    (out / "job.json").write_text(json.dumps(job, indent=1, sort_keys=True) + "\n")
    return job


def cmd_make(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ic = out / "ic.txt"
    cmd = [sys.executable, "-I", str(ROOT / "tools/make_ic.py"), "--out", str(ic), "--n-tp", str(a.n_tp), "--seed", str(a.seed),
           "--tp-from", str(a.tp_from), "--tp-to", str(a.tp_to if a.tp_to is not None else a.n_tp), "--dt", repr(a.dt)]
    subprocess.run(cmd, check=True)
    subprocess.run([str(a.p9sim), "init", str(ic), str(out / "input.sa")], check=True, stdout=subprocess.DEVNULL)
    params = {"case": "Brown & Batygin (2021): Sun (+ inner planets), Jupiter-Neptune (DE440s, JD 2458270.0), Planet Nine, test particles",
              "ic": {"generator": "tools/make_ic.py", "n_tp": a.n_tp, "seed": a.seed, "tp_from": a.tp_from,
                     "tp_to": a.tp_to if a.tp_to is not None else a.n_tp, "ic_sha256": sha256_file(ic)},
              "integrator": "whfast", "coordinates": "democraticheliocentric", "safe_mode": 1, "corrector": 0, "dt_yr": a.dt,
              "t_start_yr": 0.0, "t_end_yr": a.t_end, "snapshots": a.snapshots,
              "removal": {"r_out_au": 10000, "r_in_au": 5, "every_steps": 1000}}
    job = write_job(out, params, out / "input.sa")
    print(f"job {job['id'][:16]}… -> {out}")


def cmd_next(a):
    prev, out = Path(a.prev), Path(a.out)
    pj = json.loads((prev / "job.json").read_text())
    pr = json.loads((prev / "result.json").read_text())
    out.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(a.p9sim), "last", str(prev / "output.sa"), str(out / "input.sa")], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    params = dict(pj["params"])
    params.update({"t_start_yr": pj["params"]["t_end_yr"], "t_end_yr": a.t_end, "snapshots": a.snapshots,
                   "previous": {"job_id": pj["id"], "result_sha256": pr["result_sha256"]}})
    job = write_job(out, params, out / "input.sa")
    print(f"job {job['id'][:16]}… -> {out}")


def cmd_run(a):
    d = Path(a.dir)
    job = json.loads((d / "job.json").read_text())
    if sha256_file(d / "input.sa") != job["input"]["sha256"]:
        sys.exit("input.sa does not match job.json")
    p9sim = Path(a.p9sim)
    build_flags = (p9sim.parent / "BUILD-FLAGS").read_text().strip() if (p9sim.parent / "BUILD-FLAGS").exists() else str(p9sim)
    cmd = ([*a.prefix.split()] if a.prefix else []) + [str(p9sim), "run", str(d / "input.sa"), repr(float(job["params"]["t_end_yr"])),
                                                       str(job["params"]["snapshots"]), str(d / a.output), str(d / "final.state")]
    t0 = time.time()
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    p = subprocess.run(cmd, capture_output=True, text=True)
    r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    wall = time.time() - t0
    if p.returncode:
        sys.exit(f"p9sim failed ({p.returncode}): {p.stderr[-2000:]}")
    line = [l for l in p.stdout.splitlines() if l.startswith("result_sha256=")][-1]
    kv = dict(x.split("=", 1) for x in line.split())
    result = {"job_id": job["id"], "result_sha256": kv["result_sha256"], "final_state_sha256": kv["final_state_sha256"],
              "t_end": float(kv["t"]), "steps": int(kv["steps"]), "particles_start": int(kv["N_start"]), "particles_end": int(kv["N_end"]),
              "removed": int(kv["removed"]), "dE_rel_massive": float(kv["dE_rel"]),
              "wall_s": round(wall, 3), "cpu_s": round((r1.ru_utime - r0.ru_utime) + (r1.ru_stime - r0.ru_stime), 3),
              "input_bytes": job["input"]["bytes"], "output_bytes": (d / a.output).stat().st_size,
              "platform": {"machine": platform.machine(), "system": platform.system(), "node_hash": hashlib.sha256(platform.node().encode()).hexdigest()[:12],
                           "python": platform.python_version()},
              "build": build_flags, "runner": a.prefix or None}
    (d / a.result_name).write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("job_id", "result_sha256", "wall_s", "particles_end")}))


def cmd_check(a):
    r = json.loads((Path(a.dir) / a.result_name).read_text())
    ok = r["result_sha256"] == a.expected
    print(("OK " if ok else "MISMATCH ") + r["result_sha256"])
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--out", required=True)
    m.add_argument("--t-end", type=float, required=True)
    m.add_argument("--snapshots", type=int, required=True)
    m.add_argument("--n-tp", type=int, default=4000)
    m.add_argument("--tp-from", type=int, default=0)
    m.add_argument("--tp-to", type=int, default=None)
    m.add_argument("--seed", type=int, default=9)
    m.add_argument("--dt", type=float, default=0.5)
    m.add_argument("--p9sim", default=str(DEFAULT_P9SIM))
    n = sub.add_parser("next")
    n.add_argument("--prev", required=True)
    n.add_argument("--out", required=True)
    n.add_argument("--t-end", type=float, required=True)
    n.add_argument("--snapshots", type=int, required=True)
    n.add_argument("--p9sim", default=str(DEFAULT_P9SIM))
    r = sub.add_parser("run")
    r.add_argument("dir")
    r.add_argument("--p9sim", default=str(DEFAULT_P9SIM))
    r.add_argument("--prefix", default="", help="e.g. 'qemu-aarch64' or 'node tools/run_wasm.mjs'")
    r.add_argument("--output", default="output.sa")
    r.add_argument("--result-name", default="result.json")
    c = sub.add_parser("check")
    c.add_argument("dir")
    c.add_argument("--expected", required=True)
    c.add_argument("--result-name", default="result.json")
    a = ap.parse_args()
    {"make": cmd_make, "next": cmd_next, "run": cmd_run, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    main()
