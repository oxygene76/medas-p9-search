# SPDX-License-Identifier: GPL-3.0-or-later
"""The 32 confirmed numerical losses (tests/data/flyby-regression) with sub-steps.

  P9TEST_P9GPU=build/gpu-cpu/p9gpu P9TEST_P9SIM=build/test/p9sim python -I tests/test_flyby_regression.py -v

For every case: p9gpu (method substep, the trigger radii of the rule at
dt = 0.5 yr times 4, the planets with 8 inner steps per step) from the stored state
over the stored window; the kick (change of
the particle's heliocentric orbital energy) must be within 5 % of IAS15's,
and the particle unbound at the end only where it is with IAS15 (no false
loss). Prints one line per case (also with --verbose off: summary).
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests/data/flyby-regression"
# trigger radii: 4 times the rule at dt = 0.5 yr (Jupiter, Saturn, Uranus, Neptune, Planet Nine; ids 1..5),
# as p9job make --encounter-method substep (--trigger-factor 4)
RADII = "1=7.4300,2=4.9708,3=2.6572,4=3.1036,5=2.0000"
# the planets' inner steps per step (p9gpu P9_PLANET_SUBSTEPS; the job parameter planet_substeps of method substep)
PLANET_SUBSTEPS = "8"


def run_case(c, p9gpu, p9sim, mode="cpu"):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        subprocess.run([p9sim, "init", str(DATA / c["file"]), str(d / "in.sa")], check=True, stdout=subprocess.DEVNULL)
        env = dict(os.environ, P9GPU_MODE=mode, P9_ENCOUNTER_METHOD="substep", P9_ENCOUNTER_RADII=RADII, P9_PLANET_SUBSTEPS=PLANET_SUBSTEPS)
        for k in ("P9_ENCOUNTER_REMOVE", "P9_FLYBY_OUT", "P9_J2", "P9GPU_REAL"):
            env.pop(k, None)
        p = subprocess.run([p9gpu, "run", str(d / "in.sa"), repr(c["steps"] * c["dt_yr"]), "1", str(d / "o.sa")], env=env, capture_output=True,
                           text=True, check=True)
        kv = dict(x.split("=", 1) for x in [l for l in p.stdout.splitlines() if l.startswith("result_sha256=")][-1].split())
        rows = [l.split() for l in subprocess.run([p9sim, "dump", str(d / "o.sa"), "0"], capture_output=True, text=True, check=True).stdout.splitlines()[1:]]
    G = float([l for l in (DATA / c["file"]).read_text().splitlines() if l.startswith("G ")][0].split()[1])
    sun = [float(x) for x in rows[0][3:9]]
    tp = [float(x) - s for x, s in zip(rows[-1][3:9], sun)]
    r = sum(x * x for x in tp[:3]) ** 0.5
    E = 0.5 * sum(v * v for v in tp[3:]) - G * float(rows[0][2]) / r
    ratio = (E - c["E_before"]) / (c["E_ias15"] - c["E_before"])
    return {"ratio": ratio, "unbound": E > 0, "sub_steps": int(kv["sub_steps"]), "sub_max": int(kv["sub_max"]), "sub_capped": int(kv["sub_capped"]),
            "hash": kv["result_sha256"]}


@unittest.skipUnless(os.environ.get("P9TEST_P9GPU") and os.environ.get("P9TEST_P9SIM"), "needs P9TEST_P9GPU and P9TEST_P9SIM")
class FlybyRegression(unittest.TestCase):
    def test_the_32_cases(self):
        cases = json.loads((DATA / "index.json").read_text())["cases"]
        self.assertEqual(len(cases), 32)
        bad = []
        for c in cases:
            r = run_case(c, os.environ["P9TEST_P9GPU"], os.environ["P9TEST_P9SIM"])
            ok = abs(r["ratio"] - 1) <= 0.05 and r["unbound"] == c["unbound_ias15"]
            print(f"  {c['id']:5d} {c['planet']:8s} {c['dmin_au']:.4f} au: kick ratio {r['ratio']:.4f} (fixed step {c['kick_ratio_fixed_step']:.3g}), "
                  f"unbound {r['unbound']} (IAS15 {c['unbound_ias15']}), sub-steps {r['sub_steps']} up to n = {r['sub_max']}"
                  f"{', capped ' + str(r['sub_capped']) if r['sub_capped'] else ''}{'' if ok else '  FAIL'}", file=sys.stderr)
            if not ok:
                bad.append(c["id"])
        self.assertEqual(bad, [], f"{len(bad)} of 32 cases off")


if __name__ == "__main__":
    unittest.main()
