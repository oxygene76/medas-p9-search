# SPDX-License-Identifier: GPL-3.0-or-later
"""The project lead's flyby check (tools/flyby_check.py, REBOUND) on p9gpu (tools/flyby_p9gpu.py).

  P9TEST_P9GPU=build/gpu-cpu/p9gpu P9TEST_P9SIM=build/test/p9sim python -I tests/test_flyby.py -v

Expected as with REBOUND (19.10.2026): Planet Nine, d_min 0.5 au, 0.35 au/yr,
dt 0.5 yr: error of the kick about 1.5e-4; Neptune at its Hill radius 0.78 au,
0.8 au/yr: about 1e-4. And the same as REBOUND's WHFast (democratic
heliocentric) on the same windows. Needs the Python package rebound (5.2.2).
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
try:
    import rebound  # noqa: F401
    HAVE_REBOUND = True
except ImportError:
    HAVE_REBOUND = False


def run(planet, dt, dmin, vrel):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "f.json"
        subprocess.run([sys.executable, "-I", str(ROOT / "tools/flyby_p9gpu.py"), "run", "--planet", planet, "--dt", str(dt), "--dmin", str(dmin),
                        "--vrel", str(vrel), "--out", str(out), "--p9gpu", os.environ["P9TEST_P9GPU"], "--p9sim", os.environ["P9TEST_P9SIM"]],
                       check=True, stderr=subprocess.DEVNULL)
        rows = json.loads(out.read_text())["rows"]
    med = lambda c, k: float(np.median([r[k] for r in rows if r["integrator"] == c]))
    return {c: (med(c, "err_E"), med(c, "err_h")) for c in ("p9gpu", "rebound_whfast_dh")}


@unittest.skipUnless(HAVE_REBOUND and os.environ.get("P9TEST_P9GPU") and os.environ.get("P9TEST_P9SIM"),
                     "needs the Python package rebound and P9TEST_P9GPU, P9TEST_P9SIM")
class Flyby(unittest.TestCase):
    def check(self, planet, dt, dmin, vrel, expected):
        r = run(planet, dt, dmin, vrel)
        for k in (0, 1):
            self.assertGreater(r["p9gpu"][k], expected / 2)
            self.assertLess(r["p9gpu"][k], expected * 2)
            self.assertAlmostEqual(r["p9gpu"][k] / r["rebound_whfast_dh"][k], 1.0, delta=0.05)

    def test_planet_nine_half_au(self):
        self.check("p9", 0.5, 0.5, 0.35, 1.5e-4)

    def test_neptune_hill_radius(self):
        self.check("neptune", 0.5, 0.78, 0.8, 1e-4)


if __name__ == "__main__":
    unittest.main()
