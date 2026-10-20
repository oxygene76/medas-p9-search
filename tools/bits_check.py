#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Method smooth gives the same bits on CPU, GPU and WebAssembly (and df64 on GPU and its CPU twin).

  python tools/bits_check.py [--gpu build/gpu/p9gpu] [--cpu build/gpu-cpu/p9gpu] [--wasm build/gpu-wasm/p9gpu] [--wasm-cases 4]
      [--deep runs/jacobi-lost/deep] [--out bits.json]

Cases: the 32 numerical losses (tests/data/flyby-regression, settings of
tests/test_flyby_regression.py: method smooth, r_out 4 x the rule, planets
with 8 inner steps, collisions at the physical radii) and, with --deep, the 4
deep Neptune flybys of the Jacobi test restarted before the flyby
(tools/deep_flyby_test.py: two pass inside Neptune, a collision; two at 1.4
and 1.6 radii with up to 2^21 sub-steps). Per case the result hash of
  - the native CPU build (double): the reference,
  - the GPU build (double, P9GPU_MODE=gpu), if --gpu,
  - the CPU build with P9GPU_REAL=double-t (the template code),
  - the WebAssembly build (node tools/run_wasm.mjs), for the first --wasm-cases
    regression cases and all deep cases, if --wasm,
and df64 on the GPU against df64 on the CPU twin. All must agree.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))
import test_flyby_regression as tr  # noqa: E402
import p9job  # noqa: E402

P9SIM = ROOT / "build/test/p9sim"
NEPTUNE = f"1={p9job.PHYSICAL_RADII_KM['Neptune'] / p9job.AU_KM:.6e}"


def run(binary, sa, t_end, env_extra, mode="cpu", real="double", wasm=False):
    env = dict(os.environ, P9GPU_MODE=mode, P9GPU_REAL=real, **env_extra)
    for k in ("P9_ENCOUNTER_REMOVE", "P9_FLYBY_OUT", "P9_J2", "P9_CAPPED_OUT", "P9_REMOVED_OUT"):
        env.pop(k, None)
    with tempfile.TemporaryDirectory() as d:
        cmd = (["node", str(ROOT / "tools/run_wasm.mjs")] if wasm else []) + [str(binary), "run", str(sa), repr(t_end), "1", str(Path(d) / "o.sa")]
        p = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"{' '.join(cmd)}: {p.stderr[-1500:]}")
    kv = dict(x.split("=", 1) for x in [l for l in p.stdout.splitlines() if l.startswith("result_sha256=")][-1].split())
    return kv["result_sha256"], kv


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cpu", default=str(ROOT / "build/gpu-cpu/p9gpu"))
    ap.add_argument("--gpu")
    ap.add_argument("--wasm")
    ap.add_argument("--wasm-cases", type=int, default=4)
    ap.add_argument("--deep")
    ap.add_argument("--out")
    a = ap.parse_args()
    reg_env = {"P9_ENCOUNTER_METHOD": "smooth", "P9_ENCOUNTER_RADII": tr.RADII, "P9_PLANET_SUBSTEPS": tr.PLANET_SUBSTEPS,
               "P9_COLLISION_RADII": tr.COLLISION}
    deep_env = {"P9_ENCOUNTER_METHOD": "smooth", "P9_ENCOUNTER_RADII": "1=3.1036", "P9_PLANET_SUBSTEPS": "8", "P9_COLLISION_RADII": NEPTUNE}
    with tempfile.TemporaryDirectory() as tmp:
        cases = []
        for k, c in enumerate(json.loads((tr.DATA / "index.json").read_text())["cases"]):
            sa = Path(tmp) / f"case-{c['id']}.sa"
            subprocess.run([str(P9SIM), "init", str(tr.DATA / c["file"]), str(sa)], check=True, stdout=subprocess.DEVNULL)
            cases.append((f"regression {c['id']}", sa, c["steps"] * c["dt_yr"], reg_env, k < a.wasm_cases))
        if a.deep:
            rep = {r["id"]: r for r in json.loads((Path(a.deep) / "report.json").read_text())}
            for i, r in sorted(rep.items()):
                cases.append((f"deep {i}", Path(a.deep) / f"p{i}" / "input.sa", r["t_end"], deep_env, True))
        rows, bad = [], 0
        for name, sa, t_end, env, wasm in cases:
            ref, kv = run(a.cpu, sa, t_end, env)
            row = {"case": name, "cpu": ref, "sub_max": int(kv["sub_max"]), "collisions": kv.get("collisions", "-")}
            row["double_t"] = run(a.cpu, sa, t_end, env, real="double-t")[0]
            if a.gpu:
                row["gpu"] = run(a.gpu, sa, t_end, env, mode="gpu")[0]
                row["df64_cpu"] = run(a.cpu, sa, t_end, env, real="df64")[0]
                row["df64_gpu"] = run(a.gpu, sa, t_end, env, mode="gpu", real="df64")[0]
            if a.wasm and wasm:
                row["wasm"] = run(a.wasm, sa, t_end, env, wasm=True)[0]
            same = all(row[k] == ref for k in ("double_t", "gpu", "wasm") if k in row) and row.get("df64_gpu") == row.get("df64_cpu")
            row["same"] = same
            bad += not same
            rows.append(row)
            print(f"{name:16s} n up to {row['sub_max']:8d} collisions {row['collisions']:6s} cpu {ref[:12]} "
                  + " ".join(f"{k} {'=' if row[k] == ref else row[k][:12]}" for k in ("double_t", "gpu", "wasm") if k in row)
                  + (f" df64 gpu {'=' if row['df64_gpu'] == row['df64_cpu'] else '!='} cpu twin" if "df64_gpu" in row else "")
                  + ("" if same else "  DIFFERENT"), flush=True)
    print(f"{len(rows) - bad} of {len(rows)} cases the same bits")
    if a.out:
        Path(a.out).write_text(json.dumps({"rows": rows, "different": bad}, indent=1) + "\n")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
