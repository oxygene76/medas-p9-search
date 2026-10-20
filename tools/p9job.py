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
  p9job.py control DIR                                            (record the expected result)
  p9job.py check DIR [--expected HASH]                            (exit 0 if equal)

A control job carries its expected result in job.json under "control"
(outside the job id, which only covers schema, code, params and input): a
machine that computes it can be checked against a result known in advance.
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


def program_version(binary):
    """The version compiled into p9sim or p9gpu (git describe at build time)."""
    out = subprocess.run([str(binary), "version"], capture_output=True, text=True)
    m = __import__("re").search(r"version=(\S+)", out.stdout + out.stderr)
    return m.group(1) if m else None


def code_version(program, binary, allow_dirty=False):
    rev = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True).stdout.strip()
    if dirty and not allow_dirty:
        sys.exit("commit first: a job names the exact code it was made with")
    if dirty:
        rev += "-dirty"  # tests only (--allow-dirty): never a job of a run
    return {"commit": rev, "rebound": REBOUND, "program": program,
            "reference_binary": {"path": str(Path(binary).name), "sha256": sha256_file(binary)},
            "build": "make (see Makefile): -std=c99 -fno-fast-math -ffp-contract=off, any -O level and compiler; p9gpu: nvcc --fmad=false"}


def hill_radii(ic_path):
    """Encounter radii: one Hill radius a (m / 3 M_sun)^(1/3) per massive body but the Sun, from the
    heliocentric osculating semi-major axis of the start values, as decimals rounded to 1e-4 au.
    Returns {name: (radius, id)}; the id is the body's number in the start file (its 9th column, else
    its position), which p9sim stores with the body."""
    G = None
    bodies = []
    k = 0
    for line in open(ic_path).read().splitlines():
        f = line.split()
        if f and f[0] == "G":
            G = float(f[1])
        if f and f[0] == "p":
            if float(f[2]) > 0:
                bodies.append((f[1], float(f[2]), [float(x) for x in f[3:9]], int(f[9]) if len(f) > 9 else k))
            k += 1
    sun = bodies[0]
    out = {}
    for name, m, s, pid in bodies[1:]:
        if name in out:
            raise SystemExit(f"{ic_path}: body {name} twice")
        r = [s[k] - sun[2][k] for k in range(6)]
        rr = sum(x * x for x in r[:3]) ** 0.5
        v2 = sum(x * x for x in r[3:])
        a = 1 / (2 / rr - v2 / (G * (sun[1] + m)))
        out[name] = (f"{a * (m / (3 * sun[1])) ** (1 / 3):.4f}", pid)
    return out


# Encounter radii (docs/close-encounters.md): the time step must resolve the
# orbit around a planet at the removal distance. Reference: Planet Nine at 0.5
# au with dt = 0.5 yr (orbit around it about 82 yr, 164 steps); the same number
# of steps per orbit for any planet and step gives
#   r_res = 0.5 au (m / m_P9)^(1/3) (dt / 0.5 yr)^(2/3).
# Planet Nine: r_res. The others: the larger of their Hill radius and r_res.
RES_P9_AU, RES_DT_YR = 0.5, 0.5
RADII_RULE = ("max(Hill radius [not for Planet Nine], r_orbit = 0.5 au (m / m_P9)^(1/3) (dt / 0.5 yr)^(2/3), 1.5 v99 dt): "
              "about 164 steps per orbit around the planet at the removal distance, and a flyby of at least 1.5 steps at "
              "the 99th percentile v99 of the encounter speeds (docs/close-encounters.md)")


def masses(ic_path):
    out = {}
    for line in open(ic_path).read().splitlines():
        f = line.split()
        if f and f[0] == "p" and float(f[2]) > 0:
            out[f[1]] = float(f[2])
    return out


def encounter_radii(ic_path, dt, overrides, v99=()):
    """radii_au, body_ids and how they came about, for params.removal.encounter. v99: NAME=au/yr."""
    hill = hill_radii(ic_path)
    m = masses(ic_path)
    if "P9" not in m:
        raise SystemExit(f"{ic_path}: no body P9 (the reference of the radius rule)")
    res = {n: RES_P9_AU * (m[n] / m["P9"]) ** (1 / 3) * (dt / RES_DT_YR) ** (2 / 3) for n in hill}
    speeds = {}
    for o in v99:
        n, v = o.split("=", 1)
        if n not in hill:
            raise SystemExit(f"--v99: no body {n}")
        speeds[n] = float(v)
    flyby = {n: 1.5 * speeds.get(n, 0.0) * dt for n in hill}
    radii = {n: f"{max(res[n], flyby[n], 0.0 if n == 'P9' else float(hill[n][0])):.4f}" for n in hill}
    for o in overrides:
        n, v = o.split("=", 1)
        if n not in hill:
            raise SystemExit(f"--radius: no body {n}")
        float(v)
        radii[n] = v
    enc = {"radii_au": radii, "body_ids": {n: i for n, (_, i) in hill.items()}, "rule": RADII_RULE,
           "hill_au": {n: r for n, (r, _) in hill.items()}, "resolution_au": {n: f"{v:.4f}" for n, v in res.items()}}
    if v99:
        enc["v99_au_per_yr"] = {n: f"{v:g}" for n, v in speeds.items()}
        enc["flyby_au"] = {n: f"{flyby[n]:.4f}" for n in speeds}
    if overrides:
        enc["overrides"] = list(overrides)
    return enc


def substep_radii(enc, factor):
    """Method substep: the trigger radii are factor times the rule's radii (docs/substeps-plan.md: with the rule's
    radius itself, flybys just outside it, still under two steps long, were off by up to 40 %; with 4 times it by
    under 1 %)."""
    out = dict(enc)
    out["rule_radii_au"] = enc["radii_au"]
    out["radii_au"] = {n: f"{float(r) * factor:.4f}" for n, r in enc["radii_au"].items()}
    out["trigger_factor"] = factor
    return out


def encounter_env(job):
    """P9_ENCOUNTER_RADII for a job: "id=radius,..." with each radius assigned by the body's name
    (params.removal.encounter.radii_au and .body_ids). The programs assign by id, so the order of
    the items does not matter; it is sorted by name here on purpose. Returns None without radii.
    Jobs from before the fix (radii without ids, joined in the order of job.json, which is
    sorted by name and so not the order of the bodies) are refused."""
    enc = job["params"].get("removal", {}).get("encounter", {})
    radii = enc.get("radii_au", {})
    if not radii:
        return None
    ids = enc.get("body_ids")
    if not ids:
        raise SystemExit("job has encounter radii without body ids (made before 2026-10-19 fix): its radii were applied "
                         "in the wrong order; make the job again")
    if set(ids) != set(radii):
        raise SystemExit(f"encounter radii and body ids name different bodies: {sorted(radii)} / {sorted(ids)}")
    return ",".join(f"{ids[n]}={radii[n]}" for n in sorted(radii))


def removed_by(job, text):
    """Removals by close encounter per planet name, from the programs' "removed_by=id:n,..."."""
    ids = job["params"].get("removal", {}).get("encounter", {}).get("body_ids", {})
    names = {str(i): n for n, i in ids.items()}
    return {names.get(i, f"id {i}"): int(n) for i, n in (x.split(":") for x in text.split(",") if x and x != "-")}


def check_encounter_report(job, stdout):
    """The radii the program reports (lines "encounter_radius id=… au=…") must be the job's, by name."""
    enc = job["params"].get("removal", {}).get("encounter", {})
    radii, ids = enc.get("radii_au", {}), enc.get("body_ids", {})
    got = {}
    for line in stdout.splitlines():
        if line.startswith("encounter_radius "):
            kv = dict(x.split("=", 1) for x in line.split()[1:])
            got[int(kv["id"])] = float(kv["au"])
    want = {ids[n]: float(radii[n]) for n in radii}
    if got != want:
        raise SystemExit(f"the program used other encounter radii than the job: {got} instead of {want}")
    return {n: got[ids[n]] for n in sorted(radii)}


def job_id(job):
    """sha256 over the canonical JSON of schema, code, params and input (not id or control)."""
    return hashlib.sha256(canonical({k: job[k] for k in ("schema", "code", "params", "input")})).hexdigest()


def write_job(out: Path, params, input_sa: Path, program="p9sim", binary=DEFAULT_P9SIM, allow_dirty=False):
    job = {"schema": SCHEMA, "code": code_version(program, binary, allow_dirty), "params": params,
           "input": {"file": "input.sa", "sha256": sha256_file(input_sa), "bytes": input_sa.stat().st_size}}
    job["id"] = job_id(job)
    (out / "job.json").write_text(json.dumps(job, indent=1, sort_keys=True) + "\n")
    return job


def cmd_make(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ic = out / "ic.txt"
    cmd = [sys.executable, "-I", str(ROOT / "tools/make_ic.py"), "--out", str(ic), "--n-tp", str(a.n_tp), "--seed", str(a.seed),
           "--tp-from", str(a.tp_from), "--tp-to", str(a.tp_to if a.tp_to is not None else a.n_tp), "--dt", repr(a.dt)]
    if a.no_removal and (a.encounter_method != "step" or not a.encounters or a.program != "p9gpu"):
        sys.exit("--no-removal needs --program p9gpu, the encounter method step and the radii (they define the counting zone)")
    if a.encounter_method == "substep" and (not a.encounters or a.program != "p9gpu"):
        sys.exit("--encounter-method substep needs --program p9gpu and the radii (they are the trigger radii)")
    if a.integrator != "whfast":
        if a.program != "p9sim":
            sys.exit("--integrator mercurius needs --program p9sim")
        cmd += ["--integrator", a.integrator]
    if a.j2:
        if a.program != "p9gpu":
            sys.exit("--j2 needs --program p9gpu")
        cmd += ["--j2", a.j2, "--j2-out", str(out / "j2.json")]
    subprocess.run(cmd, check=True)
    subprocess.run([str(DEFAULT_P9SIM if a.program == "p9gpu" else a.p9sim), "init", str(ic), str(out / "input.sa")], check=True, stdout=subprocess.DEVNULL)
    params = {"case": "Brown & Batygin (2021): Sun (+ inner planets), Jupiter-Neptune (DE440s, JD 2458270.0), Planet Nine, test particles",
              "ic": {"generator": "tools/make_ic.py", "n_tp": a.n_tp, "seed": a.seed, "tp_from": a.tp_from,
                     "tp_to": a.tp_to if a.tp_to is not None else a.n_tp, "ic_sha256": sha256_file(ic)},
              **({"real": a.real} if a.real != "double" else {}),
              **({"model": {"name": "j2", **json.loads((out / "j2.json").read_text())}} if a.j2 else {}),
              "integrator": a.integrator, "coordinates": "democraticheliocentric", "safe_mode": 1, "corrector": 0, "dt_yr": a.dt,
              **({"r_crit_hill": 3} if a.integrator == "mercurius" else {}),
              "t_start_yr": 0.0, "t_end_yr": a.t_end, "snapshots": a.snapshots,
              "removal": {"r_out_au": 10000, "r_in_au": 5, "every_steps": 1000,
                          "encounter": {"criterion": ("removed when the closest approach to a planet within a step (from relative position "
                                                      "and velocity at the kick) is below its encounter radius; gpu/whdh.h p9_kick_tp_step"
                                                      if a.encounter_method == "step" else
                                                      "removed when closer to a planet than its encounter radius at the kick of a step "
                                                      "(positions of the middle of the step); src/p9encounter.h"),
                                        **({"method": a.encounter_method} if a.encounters else {}),
                                        **({"remove": False, "note": "close encounters are counted (flybys.tsv), not removed; only the "
                                                                     "distance rules remove"} if a.no_removal and a.encounter_method != "substep" else {}),
                                        **({"remove": False, "planet_substeps": a.planet_substeps,
                                            "note": "close encounters are followed with sub-steps where a step is too "
                                                                     "long (gpu/whdh.h p9_step_tp_sub, docs/substeps-plan.md); the radii are "
                                                                     "the trigger radii; only the distance rules remove"}
                                           if a.encounter_method == "substep" else {}),
                                        **(substep_radii(encounter_radii(ic, a.dt, a.radius, a.v99), a.trigger_factor)
                                           if a.encounters and a.encounter_method == "substep" else
                                           encounter_radii(ic, a.dt, a.radius, a.v99) if a.encounters else {"radii_au": {}, "body_ids": {}})}}}
    job = write_job(out, params, out / "input.sa", a.program, a.p9sim, a.allow_dirty)
    print(f"job {job['id'][:16]}… -> {out}")


def cmd_next(a):
    prev, out = Path(a.prev), Path(a.out)
    pj = json.loads((prev / "job.json").read_text())
    pr = json.loads((prev / "result.json").read_text())
    out.mkdir(parents=True, exist_ok=True)
    # the archive is read and written by p9sim (REBOUND), whichever program runs the job
    r = subprocess.run([str(DEFAULT_P9SIM), "last", str(prev / "output.sa"), str(out / "input.sa")], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    params = dict(pj["params"])
    params.update({"t_start_yr": pj["params"]["t_end_yr"], "t_end_yr": a.t_end, "snapshots": a.snapshots,
                   "previous": {"job_id": pj["id"], "result_sha256": pr["result_sha256"]}})
    job = write_job(out, params, out / "input.sa", pj["code"].get("program", "p9sim"), a.p9sim)
    print(f"job {job['id'][:16]}… -> {out}")


def cmd_run(a):
    d = Path(a.dir)
    job = json.loads((d / "job.json").read_text())
    if sha256_file(d / "input.sa") != job["input"]["sha256"]:
        sys.exit("input.sa does not match job.json")
    p9sim = Path(a.p9sim)
    want = job["code"].get("commit")
    have = program_version(p9sim)
    if want and have and have.split("-dirty")[0] != want and not a.any_version:
        sys.exit(f"{p9sim} is version {have}, the job needs {want} (--any-version to run it anyway)")
    env = dict(os.environ)
    env.pop("P9_ENCOUNTER_RADII", None)
    # number type of p9gpu's integrator (params.real, default double); part of the job, never taken from outside
    real = job["params"].get("real", "double")
    if real != "double" and job["code"].get("program") != "p9gpu":
        sys.exit(f"params.real={real} needs p9gpu")
    env["P9GPU_REAL"] = real
    model = job["params"].get("model", {"name": "full"})
    env.pop("P9_J2", None)
    if model["name"] == "j2":
        if job["code"].get("program") != "p9gpu":
            sys.exit("model j2 needs p9gpu")
        env["P9_J2"] = ",".join([model["mu_j2r2"], *model["axis"], model["r_remove_au"]])
    enc = encounter_env(job)
    method = job["params"].get("removal", {}).get("encounter", {}).get("method", "kick")  # jobs before the method: at the kick
    env["P9_ENCOUNTER_METHOD"] = method
    env.pop("P9_PLANET_SUBSTEPS", None)
    if method == "substep":
        env["P9_PLANET_SUBSTEPS"] = str(job["params"]["removal"]["encounter"]["planet_substeps"])
    remove = job["params"].get("removal", {}).get("encounter", {}).get("remove", True)
    env["P9_ENCOUNTER_REMOVE"] = "1" if remove else "0"
    env.pop("P9_FLYBY_OUT", None)
    if method in ("step", "substep") and enc:
        env["P9_FLYBY_OUT"] = str(d / "flybys.tsv")
    if enc:
        env["P9_ENCOUNTER_RADII"] = enc
    build_flags = (p9sim.parent / "BUILD-FLAGS").read_text().strip() if (p9sim.parent / "BUILD-FLAGS").exists() else str(p9sim)
    cmd = ([*a.prefix.split()] if a.prefix else []) + [str(p9sim), "run", str(d / "input.sa"), repr(float(job["params"]["t_end_yr"])),
                                                       str(job["params"]["snapshots"]), str(d / a.output), str(d / "final.state")]
    t0 = time.time()
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    wall = time.time() - t0
    if p.returncode:
        sys.exit(f"p9sim failed ({p.returncode}): {p.stderr[-2000:]}")
    line = [l for l in p.stdout.splitlines() if l.startswith("result_sha256=")][-1]
    used = check_encounter_report(job, p.stdout) if enc else {}
    kv = dict(x.split("=", 1) for x in line.split())
    if enc and int(kv.get("encounter_remove", 1)) != (1 if remove else 0):
        sys.exit(f"the program used encounter_remove={kv.get('encounter_remove', 1)}, the job needs {remove}")
    if enc and kv.get("encounter_method", "kick") != method:
        sys.exit(f"the program used encounter method {kv.get('encounter_method', 'kick')}, the job needs {method}")
    if method == "substep" and int(kv.get("planet_substeps", 1)) != job["params"]["removal"]["encounter"]["planet_substeps"]:
        sys.exit("the program used other planet sub-steps than the job")
    if kv.get("model", "full") != model["name"]:
        sys.exit(f"the program integrated model {kv.get('model', 'full')}, the job needs {model['name']}")
    if kv.get("real", "double") != real:
        sys.exit(f"the program integrated in {kv.get('real')}, the job needs {real}")
    result = {"job_id": job["id"], "result_sha256": kv["result_sha256"], "final_state_sha256": kv["final_state_sha256"],
              "t_end": float(kv["t"]), "steps": int(kv["steps"]), "particles_start": int(kv["N_start"]), "particles_end": int(kv["N_end"]),
              "removed": int(kv["removed"]), "removed_encounter": int(kv.get("removed_encounter", 0)), "dE_rel_massive": float(kv["dE_rel"]),
              "program": {"name": kv.get("program"), "version": kv.get("version"), "sha256": sha256_file(p9sim)},
              "wall_s": round(wall, 3), "cpu_s": round((r1.ru_utime - r0.ru_utime) + (r1.ru_stime - r0.ru_stime), 3),
              "input_bytes": job["input"]["bytes"], "output_bytes": (d / a.output).stat().st_size,
              "platform": {"machine": platform.machine(), "system": platform.system(), "node_hash": hashlib.sha256(platform.node().encode()).hexdigest()[:12],
                           "python": platform.python_version()},
              "build": build_flags, "runner": a.prefix or None, "encounter_radii_used_au": used, "real": real, "model": model["name"],
              "removed_inner": int(kv.get("removed_inner", 0)), "removed_by_encounter": removed_by(job, kv.get("removed_by", "")),
              **({"encounter_method": method, "flybys_within_3_radii": removed_by(job, kv.get("flybys", "")),
                  "flybys_under_1_5_steps": removed_by(job, kv.get("fast_flybys", "")),
                  "flybys_under_0_1_au": removed_by(job, kv.get("close_flybys", "")), "encounter_remove": remove,
                  **({"flybys_file": {"file": "flybys.tsv", "sha256": sha256_file(d / "flybys.tsv")}} if (d / "flybys.tsv").exists() else {})}
                 if enc and method in ("step", "substep") else {}),
              **({"sub_steps": int(kv.get("sub_steps", 0)), "sub_max": int(kv.get("sub_max", 1)), "sub_capped": int(kv.get("sub_capped", 0))}
                 if method == "substep" else {})}
    (d / a.result_name).write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("job_id", "result_sha256", "wall_s", "particles_end")}))


def cmd_control(a):
    d = Path(a.dir)
    job = json.loads((d / "job.json").read_text())
    r = json.loads((d / a.result_name).read_text())
    if r["job_id"] != job["id"]:
        sys.exit("result.json belongs to another job")
    job["control"] = {"expected_result_sha256": r["result_sha256"], "expected_final_state_sha256": r["final_state_sha256"],
                      "reference_build": r["build"], "reference_platform": r["platform"]["machine"]}
    (d / "job.json").write_text(json.dumps(job, indent=1, sort_keys=True) + "\n")
    print(f"control: {r['result_sha256']}")


def cmd_check(a):
    r = json.loads((Path(a.dir) / a.result_name).read_text())
    expected = a.expected or json.loads((Path(a.dir) / "job.json").read_text())["control"]["expected_result_sha256"]
    ok = r["result_sha256"] == expected
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
    m.add_argument("--p9sim", default=str(DEFAULT_P9SIM), help="the program that will run the job (its binary is hashed into the job)")
    m.add_argument("--program", choices=["p9sim", "p9gpu"], default="p9sim")
    m.add_argument("--no-encounters", dest="encounters", action="store_false", help="no close-encounter removal (as before 2026-10-19)")
    m.add_argument("--real", choices=["double", "df64", "float", "double-t"], default="double",
                   help="number type of p9gpu's integrator (default double; df64: double-float, see docs/gpu-precision.md)")
    m.add_argument("--radius", action="append", default=[], metavar="NAME=AU",
                   help="encounter radius of a planet instead of the rule (e.g. the radii of another job); repeatable")
    m.add_argument("--v99", action="append", default=[], metavar="NAME=AU_PER_YR",
                   help="99th percentile of the encounter speed at a planet: the radius is at least 1.5 v99 dt; repeatable")
    m.add_argument("--encounter-method", choices=["step", "kick", "substep"], default="step",
                   help="close encounters by the closest approach within a step (step, default) or at the kick (kick, before 2026-10-19 evening)")
    m.add_argument("--trigger-factor", type=float, default=4.0,
                   help="method substep: trigger radius = this times the rule's radius (docs/substeps-plan.md)")
    m.add_argument("--planet-substeps", type=int, default=8,
                   help="method substep: inner steps of the planets per step (even; docs/substeps-plan.md)")
    m.add_argument("--no-removal", action="store_true",
                   help="with method step: count close encounters (flybys.tsv) instead of removing them; only the distance rules remove")
    m.add_argument("--integrator", choices=["whfast", "mercurius"], default="whfast",
                   help="p9sim's integrator (mercurius resolves close encounters; use with --no-encounters)")
    m.add_argument("--j2", default=None, metavar="NAMES",
                   help='model "j2": these planets merged into the Sun as its J2 (e.g. Jupiter,Saturn,Uranus; p9gpu only)')
    m.add_argument("--allow-dirty", action="store_true", help="tests only: allow uncommitted changes (the job's commit gets \"-dirty\")")
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
    r.add_argument("--any-version", action="store_true", help="run with a program of another version (e.g. a reproducibility check)")
    k = sub.add_parser("control")
    k.add_argument("dir")
    k.add_argument("--result-name", default="result.json")
    c = sub.add_parser("check")
    c.add_argument("dir")
    c.add_argument("--expected", default=None)
    c.add_argument("--result-name", default="result.json")
    a = ap.parse_args()
    {"make": cmd_make, "next": cmd_next, "run": cmd_run, "control": cmd_control, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    main()
