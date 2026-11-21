"""Tests of tools/sets_addendum5.py on synthetic orbits only (no run data)."""
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
import prod_eval  # noqa: E402
import sets_addendum5 as s5  # noqa: E402
from prod_eval import elements  # noqa: E402
from test_prod_eval import make_run, states  # noqa: E402


def dist(x, y):
    return np.abs((x - y + 180) % 360 - 180)


class Angles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(5)
        n = 4000
        mu = 4 * math.pi ** 2
        a, e = rng.uniform(150, 900, n), rng.uniform(0.5, 0.95, n)
        inc, Om, om, M = np.radians(rng.uniform(0.5, 179.5, n)), *(np.radians(rng.uniform(0, 360, n)) for _ in range(3))
        r, v = states(mu, a, e, inc, Om, om, M)
        _, _, cls.inc, cls.Om, cls.vp = elements(mu, r, v)
        h = np.cross(r, v)
        ev = np.cross(v, h) / mu - r / np.linalg.norm(r, axis=-1)[:, None]
        cls.az = np.degrees(np.arctan2(ev[:, 1], ev[:, 0])) % 360   # tools/analyze.py
        cls.A = s5.angles(cls.Om, cls.vp, cls.inc)

    def test_a_is_Omega_plus_omega(self):
        self.assertLess(dist(self.A["a"], self.vp).max(), 1e-12)

    def test_b_is_the_azimuth_of_the_eccentricity_vector(self):
        self.assertLess(dist(self.A["b"], self.az).max(), 1e-6)

    def test_c_near_b_for_nearly_retrograde_a_near_b_for_nearly_flat(self):
        flat, retro = self.inc < 10, self.inc > 170
        self.assertLess(dist(self.A["a"][flat], self.A["b"][flat]).max(), 0.8)
        self.assertLess(dist(self.A["c"][retro], self.A["b"][retro]).max(), 0.8)
        self.assertGreater(dist(self.A["a"][retro], self.A["b"][retro]).max(), 90)

    def test_bound_for_prograde_orbits(self):
        pro = self.inc < 90
        bound = np.degrees(np.arcsin(np.tan(np.radians(self.inc[pro]) / 2) ** 2))
        self.assertTrue(np.all(dist(self.A["a"][pro], self.A["b"][pro]) <= bound + 1e-6))


class Beyond(unittest.TestCase):
    def test_counts_weights_and_bootstrap(self):
        rng = np.random.default_rng(1)
        # bin 300-310: 50 particles x 20 snapshots, all at 0 deg (R = 1); bin 400-410: 5 particles x 4 snapshots, uniform
        a = np.r_[np.full(1000, 305.0), np.full(20, 405.0)]
        dv = np.r_[np.zeros(1000), np.arange(20) * 18.0]
        idx = np.r_[np.repeat(np.arange(50), 20), np.repeat(np.arange(100, 105), 4)]
        out = s5.beyond(a, dv, idx, 256.0, 10, 200, rng)
        b = {x["a_mid_au"]: x for x in out["bins"]}
        self.assertEqual((b[305.0]["n"], b[305.0]["particles"]), (1000, 50))
        self.assertEqual((b[405.0]["n"], b[405.0]["particles"]), (20, 5))
        self.assertAlmostEqual(out["mean_R_unweighted"], (1.0 + 0.0) / 2, places=9)
        self.assertAlmostEqual(out["mean_R_weighted_n"], 1000 / 1020, places=9)
        self.assertAlmostEqual(out["mean_R_bins_with_at_least_10_particles"], 1.0, places=9)
        bs = out["bootstrap_particles"]
        self.assertEqual(bs["replicates"], 200)
        self.assertLessEqual(bs["p2.5"], bs["p50"]); self.assertLessEqual(bs["p50"], bs["p97.5"])


class OnASyntheticRun(unittest.TestCase):
    def test_a_reproduces_the_registered_tool(self):
        with tempfile.TemporaryDirectory() as d:
            run = Path(d) / "run"
            make_run(run, [k * 1e8 for k in range(1, 41)], n_tp=4000)
            out = s5.evaluate(run, None, wall=250.0, boot=20)
            ref, _ = prod_eval.evaluate(run, None, n_tp=4000)
            self.assertAlmostEqual(out["part1"]["a"]["M1_deg"], ref["measures"]["M1_deg"], places=9)
            self.assertAlmostEqual(out["part1"]["a"]["M2_mean_R"], ref["measures"]["M2_mean_R"], places=12)
            for k in s5.DEFS:
                self.assertIsNotNone(out["part1"][k]["R_beyond_wall_SBB"])
            self.assertAlmostEqual(out["part1"]["a"]["R_beyond_wall_SBB"], out["part2"]["SBB"]["mean_R_unweighted"], places=12)


if __name__ == "__main__":
    unittest.main()
