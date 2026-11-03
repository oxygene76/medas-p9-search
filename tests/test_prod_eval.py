# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests of tools/prod_eval.py on synthetic runs of known orientation (prerequisite V3 of
docs/bb2021-comparison-criteria.md; docs/production-criteria.md section 4).

  build/venv/bin/python -I tests/test_prod_eval.py -v

The synthetic run: the Sun, Jupiter on an orbit whose plane is tilted against the run's frame (inclination 1.3 deg,
node 100.5 deg) and turns slowly with time, Planet Nine and test particles whose elements are drawn in Jupiter's
frame with known distributions:
  - dvarpi from a von Mises distribution about 180 deg (kappa 1: R = I1(1)/I0(1) = 0.4464) for a >= 300 au, uniform
    below: the wall is the bin 300-310 au (centre 305);
  - the poles about Planet Nine's (dOmega von Mises about PSI deg), so M3 = PSI;
  - 850-950 au with the same von Mises: half-maximum width 2 arccos(1 - ln 2) = 144.2 deg (before smoothing);
  - q 43-60 au (selected) and a part with q 30-41 au (not selected), which carries the opposite direction.
"""

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import prod_eval as pe  # noqa: E402

G = pe.G
R_KAPPA1 = 0.44639     # I1(1) / I0(1)
WIDTH_KAPPA1 = 2 * math.degrees(math.acos(1 - math.log(2)))


def states(mu, a, e, inc, Om, om, M):
    """Heliocentric states from elements (radians), vectorised (as tools/make_ic.py)."""
    E = M.copy()
    for _ in range(60):
        E = E - (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
    cE, sE = np.cos(E), np.sin(E)
    b = a * np.sqrt(1 - e * e)
    xo, yo = a * (cE - e), b * sE
    n = np.sqrt(mu / a**3)
    rdot = n * a / (1 - e * cE)
    vxo, vyo = -sE * rdot, b * cE * rdot / a
    cO, sO, cw, sw, ci, si = np.cos(Om), np.sin(Om), np.cos(om), np.sin(om), np.cos(inc), np.sin(inc)
    R = np.array([[cO * cw - sO * sw * ci, -cO * sw - sO * cw * ci], [sO * cw + cO * sw * ci, -sO * sw + cO * cw * ci], [sw * si, cw * si]])
    return np.stack([R[k][0] * xo + R[k][1] * yo for k in range(3)], -1), np.stack([R[k][0] * vxo + R[k][1] * vyo for k in range(3)], -1)


def make_run(d, times, n_tp=8000, psi=0.0, rotate_subset=None, rotate_deg=0.0, seed=1, kappa=1.0):
    rng = np.random.default_rng(seed)
    m_sun, m_jup, m9 = 1.0, 1 / 1047.348644, 6.2 * 3.003489596e-6
    d.mkdir(parents=True, exist_ok=True)
    vp9_dl, Om9_dl, i9 = 250.0, 100.0, 16.0           # Planet Nine in Jupiter's frame, dog-leg longitudes
    for k, t in enumerate(times):
        I, N = math.radians(1.3), math.radians(100.5 + 0.01 * k)    # Jupiter's plane, turning slowly
        Rm = pe.rot_from_plane(I, N)
        mu = G * (m_sun + m_jup)
        rj, vj = states(mu, np.array([5.2]), np.array([0.05]), np.array([0.0]), np.array([0.0]), np.array([0.3]), np.array([0.1 * k]))
        # Planet Nine and the test particles barycentric (mu = G M_total, as the tool reads them); Jupiter heliocentric
        Mt = m_sun + m_jup + m9
        # Planet Nine: angles from the plane's node = dog-leg longitude - N
        r9, v9 = states(G * Mt, np.array([380.0]), np.array([0.2]), np.radians([i9]), np.radians([Om9_dl]) - N,
                        np.radians([vp9_dl - Om9_dl]), np.array([0.5 + 0.01 * k]))
        idx = np.arange(n_tp)
        a = np.where(idx % 10 < 8, rng.uniform(150, 1000, n_tp), rng.uniform(850, 950, n_tp))
        sel = idx % 7 != 0                                  # 6/7 selected (q > 42), 1/7 not
        q = np.where(sel, rng.uniform(43, 60, n_tp), rng.uniform(30, 41, n_tp))
        dv = np.where(a >= 300, 180 + np.degrees(rng.vonmises(0, kappa, n_tp)), rng.uniform(0, 360, n_tp))
        dv = np.where(sel, dv, 0.0 + np.degrees(rng.vonmises(0, 4, n_tp)))   # the unselected ones point the other way
        if rotate_subset is not None:
            blk = n_tp // 4
            dv = np.where((idx >= rotate_subset * blk) & (idx < (rotate_subset + 1) * blk), dv + rotate_deg, dv)
        inc = rng.uniform(5, 25, n_tp)
        dOm = psi + np.degrees(rng.vonmises(0, 2, n_tp))
        Om_dl = Om9_dl + dOm
        vp_dl = vp9_dl + dv
        e = 1 - q / a
        r, v = states(G * Mt, a, e, np.radians(inc), np.radians(Om_dl) - N, np.radians(vp_dl - Om_dl), rng.uniform(0, 2 * np.pi, n_tp))
        # Jupiter's frame -> run frame; the Sun placed so that the barycentre of the massive bodies is at rest at the origin
        rj, vj, r9, v9, r, v = (x @ Rm.T for x in (rj, vj, r9, v9, r, v))
        rs = -(m_jup * rj[0] + m9 * r9[0]) / (m_sun + m_jup)
        vs = -(m_jup * vj[0] + m9 * v9[0]) / (m_sun + m_jup)
        names = np.array(["Sun", "Jupiter", "P9"] + [f"tp{i:05d}" for i in idx])
        m = np.concatenate([[m_sun, m_jup, m9], np.zeros(n_tp)])
        rr = np.vstack([rs, rs + rj[0], r9, r])
        vv = np.vstack([vs, vs + vj[0], v9, v])
        np.savez(d / f"snap-{k:04d}.npz", t=np.float64(t), names=names, m=m, r=rr, v=vv)


TIMES = [0.5e9, 0.99e9, 1.0e9, 1.5e9, 2.0e9, 3.0e9, 4.0e9]   # 5 in the window


class Synthetic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.tmp.name)
        make_run(cls.base / "known", TIMES)
        cls.res, cls.series = pe.evaluate(cls.base / "known", n_tp=8000)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_window(self):
        self.assertEqual(self.res["snapshots"], 7)
        self.assertEqual(self.res["snapshots_in_window"], 5)
        self.assertTrue(self.res["complete"])

    def test_planet_nine_recovered_in_jupiters_frame(self):
        for row in self.series:
            self.assertLess(pe.angdist(row["p9_varpi_deg"], 250.0), 1e-6)
            self.assertAlmostEqual(row["jupiter_inc_deg"], 1.3, places=6)

    def test_M1_M2(self):
        m = self.res["measures"]
        self.assertLess(pe.angdist(m["M1_deg"], 180.0), 2.0)
        # M2: mean R per snapshot; R of the selected 150-1000 au mixes the uniform part below 300 au
        frac_clustered = np.mean([(1000 - 300) / 850 * 0.8 + 0.2, ])  # a >= 300: 70/85 of the uniform part plus the 850-950 block
        self.assertGreater(m["M2_mean_R"], 0.30)
        self.assertLess(m["M2_mean_R"], R_KAPPA1 + 0.02)
        self.assertGreater(frac_clustered, 0.8)

    def test_M3(self):
        self.assertLess(abs(self.res["measures"]["M3_psi_deg"]), 2.0)

    def test_M4_wall(self):
        self.assertEqual(self.res["measures"]["M4_wall_au"], 305.0)
        self.assertAlmostEqual(self.res["measures"]["M4_R_plat"], R_KAPPA1, delta=0.03)

    def test_M5_width(self):
        w = self.res["measures"]["M5"]
        self.assertLess(abs(w["width_deg"] - WIDTH_KAPPA1), 12)
        centre = (w["from_deg"] + ((w["to_deg"] - w["from_deg"]) % 360) / 2) % 360
        self.assertLess(pe.angdist(centre, 180.0), 8)

    def test_subsets_agree(self):
        self.assertLess(self.res["subset_scatter_deg"], 5.0)
        self.assertEqual(self.res["deviating_subsets_reported"], [])
        self.assertTrue(self.res["verdict"].startswith("decided"))

    def test_ecliptic_variant_differs_only_little(self):
        v = self.res["variants_not_judged"]["ecliptic"]
        d = pe.angdist(v["M1_deg"], self.res["measures"]["M1_deg"])
        self.assertLess(d, 3.0)

    def test_selections_and_survivors(self):
        row = self.series[0]
        for s in ("S1", "S2", "S3"):
            self.assertIn(f"{s}_R", row)
        self.assertEqual(set(self.res["survivors"].values()), {8000})

    def test_rotated_poles_give_psi(self):
        make_run(self.base / "psi40", TIMES, psi=40.0, seed=2)
        r, _ = pe.evaluate(self.base / "psi40", n_tp=8000)
        self.assertLess(abs(r["measures"]["M3_psi_deg"] - 40.0), 2.5)

    def test_deviating_subset_makes_it_not_decided(self):
        make_run(self.base / "dev", TIMES, rotate_subset=2, rotate_deg=60.0, seed=3)
        r, _ = pe.evaluate(self.base / "dev", n_tp=8000)
        self.assertGreater(r["subset_scatter_deg"], 10.0)
        self.assertIn(2, r["deviating_subsets_reported"])
        self.assertTrue(r["verdict"].startswith("not decided"))
        # the deviating subset is not excluded: the pooled M1 moves towards it
        self.assertGreater(pe.angdist(r["measures"]["M1_deg"], 180.0), 3.0)

    def test_incomplete_run(self):
        r, _ = pe.evaluate(self.base / "known", n_tp=8000, t_end=5e9)
        self.assertTrue(r["verdict"].startswith("not decided (run not complete"))

    def test_bb_judgement_and_outcome(self):
        r, _ = pe.evaluate(self.base / "known", n_tp=8000, criteria="bb2021-B")
        self.assertEqual(r["verdict"], "agrees with Brown & Batygin")
        rA, _ = pe.evaluate(self.base / "known", n_tp=8000, criteria="bb2021-A")
        self.assertIn("M4 305.0 outside 226-286 au", rA["verdict"])
        a, b = self.base / "a.json", self.base / "b.json"
        a.write_text(json.dumps(rA)); b.write_text(json.dumps(r))
        self.assertEqual(pe.outcome(a, b), "2. One set agrees")
        b.write_text(json.dumps(r)); a.write_text(json.dumps(r))
        self.assertEqual(pe.outcome(a, b), "1. Agreement")

    def test_weak_cluster_is_outcome_4(self):
        make_run(self.base / "weak", TIMES, kappa=0.2, seed=4)
        r, _ = pe.evaluate(self.base / "weak", n_tp=8000, criteria="bb2021-B")
        self.assertLess(r["measures"]["M2_mean_R"], 0.20)
        a = self.base / "w.json"
        a.write_text(json.dumps(r))
        self.assertEqual(pe.outcome(a, a), "4. No cluster (M2 below 0.20 in at least one set)")


if __name__ == "__main__":
    unittest.main()
