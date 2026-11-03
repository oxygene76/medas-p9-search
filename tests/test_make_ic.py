# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests of tools/make_ic.py: the start values of existing cases stay bit for bit the same (hashes recorded with the
code before --p9 and --p9-plane, 2026-11-03), and Planet Nine relative to the invariable plane of Jupiter to Neptune
(prerequisite V1 of docs/bb2021-comparison-criteria.md, medas-p9-search).

  build/venv/bin/python -I tests/test_make_ic.py -v
"""

import hashlib
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MAKE_IC = ROOT / "tools/make_ic.py"
BB = ["--a-range", "150", "500", "--q-range", "30", "50", "--inc-range", "0", "25"]

# sha256 of the output of make_ic.py at 0a5b7f5 (the code of the production package's start values)
REGRESSION = {
    "default": ([], "9e7f895c6a611f75ea2894ed868bca8786d946411657d3f02c486fe35bcf381e"),
    "speed-4k-seed101": (["--n-tp", "4000", "--seed", "101", *BB], "2ff26f5ea06b50f4a1b5ba8d7f369444bc009c2ce0f1aa927253c73becb0048d"),
    "slice-of-64k-seed21": (["--n-tp", "64000", "--seed", "21", "--tp-from", "1000", "--tp-to", "1500", *BB],
                            "e21e33ed2e5ba3360a2217b553c1b85b81d73147171d0f308f943c002ff832b7"),
    "members-mercurius": (["--n-tp", "2000", "--seed", "9", "--members", "0,1,2", "--integrator", "mercurius"],
                          "e4a43543c34acadb00efd674283c83b8656a3747c10c018e73794446ff70f197"),
    "j2": (["--n-tp", "1000", "--seed", "5", "--j2", "Jupiter,Saturn,Uranus"], "7014d1995a42d53521f5e3440ff94310ca98b688f77bb8988381019004a2dd96"),
    # the production run's start values (runs/prod/ic.txt, params.ic.ic_sha256 of p9prod-9a084ed)
    "production-64k-seed21": (["--n-tp", "64000", "--seed", "21", *BB], "f8c073075789ebfcf40bd0cc2b9c88355a6aef80b35c896d9344c08546fbde1b"),
}
G = (0.01720209895 * 365.25) ** 2


def run(args, out):
    p = subprocess.run([sys.executable, "-I", str(MAKE_IC), "--out", str(out), *args], capture_output=True, text=True)
    return p


def bodies(path):
    out = {}
    for line in Path(path).read_text().splitlines():
        f = line.split()
        if f and f[0] == "p":
            v = [float(x) for x in f[2:9]]
            out[f[1]] = (v[0], np.array(v[1:4]), np.array(v[4:7]))
    return out


def elements(mu, r, v):
    """a, e, inc, Omega, omega (radians) of a heliocentric state, in the frame of r and v."""
    h = np.cross(r, v)
    nvec = np.cross([0.0, 0.0, 1.0], h)
    evec = np.cross(v, h) / mu - r / np.linalg.norm(r)
    a = 1 / (2 / np.linalg.norm(r) - v @ v / mu)
    inc = math.acos(h[2] / np.linalg.norm(h))
    Om = math.atan2(nvec[1], nvec[0])
    om = math.atan2(np.cross(nvec, evec) @ h / np.linalg.norm(h), nvec @ evec)
    return a, np.linalg.norm(evec), inc, Om % (2 * math.pi), om % (2 * math.pi)


def angdiff(x, y):
    return abs((x - y + 180) % 360 - 180)


class Regression(unittest.TestCase):
    def test_existing_cases_unchanged(self):
        with tempfile.TemporaryDirectory() as t:
            for name, (args, want) in REGRESSION.items():
                with self.subTest(name):
                    out = Path(t) / f"{name}.txt"
                    p = run(args, out)
                    self.assertEqual(p.returncode, 0, p.stderr)
                    self.assertEqual(hashlib.sha256(out.read_bytes()).hexdigest(), want)

    def test_p9_defaults_given_explicitly_change_nothing(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "x.txt"
            p = run(["--p9", "m_earth=6.2,a=380,q=300,inc=16,varpi=248.5,Omega=98.5,M=180", "--p9-plane", "ecliptic"], out)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(hashlib.sha256(out.read_bytes()).hexdigest(), REGRESSION["default"][1])


class PlanetNine(unittest.TestCase):
    SET_A = "m_earth=7,a=500,e=0.33,inc=17,varpi=250,Omega=100,M=0"
    SET_B = "m_earth=5,a=300,e=0.15,inc=17,varpi=254,Omega=108,M=0"

    def p9_elements(self, path):
        b = bodies(path)
        m_sun, r_sun, v_sun = b["Sun"]
        m9, r9, v9 = b["P9"]
        return m9, r9 - r_sun, v9 - v_sun, G * (m_sun + m9), b

    def test_ecliptic_round_trip(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "b.txt"
            self.assertEqual(run(["--n-tp", "10", "--p9", self.SET_B], out).returncode, 0)
            m9, r, v, mu, _ = self.p9_elements(out)
            a, e, inc, Om, om = elements(mu, r, v)
            self.assertAlmostEqual(m9 / 3.003489596e-6, 5.0, places=12)
            self.assertAlmostEqual(a, 300.0, places=8)
            self.assertAlmostEqual(e, 0.15, places=10)
            self.assertAlmostEqual(math.degrees(inc), 17.0, places=8)
            self.assertLess(angdiff(math.degrees(Om), 108.0), 1e-8)
            self.assertLess(angdiff(math.degrees(Om + om), 254.0), 1e-8)
            self.assertIn("# Planet Nine m_earth 5.0", out.read_text())

    def test_invariable_plane(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "a.txt"
            p = run(["--n-tp", "10", "--p9", self.SET_A, "--p9-plane", "invariable"], out)
            self.assertEqual(p.returncode, 0, p.stderr)
            m9, r, v, mu, b = self.p9_elements(out)
            # the plane from the file's own states (heliocentric angular momentum of Jupiter to Neptune)
            _, r_sun, v_sun = b["Sun"]
            L = sum(m * np.cross(rr - r_sun, vv - v_sun) for n, (m, rr, vv) in b.items() if n in ("Jupiter", "Saturn", "Uranus", "Neptune"))
            pole = L / np.linalg.norm(L)
            I, N = math.acos(pole[2]), math.atan2(pole[0], -pole[1])
            # close to the invariable plane of the solar system (Souami & Souchay 2012: 1.578 deg, 107.58 deg)
            self.assertLess(abs(math.degrees(I) - 1.58), 0.05)
            self.assertLess(angdiff(math.degrees(N), 107.6), 0.5)
            # Planet Nine's elements in the frame of that plane (x to its node, z to its pole)
            cI, sI, cN, sN = math.cos(I), math.sin(I), math.cos(N), math.sin(N)
            R = np.array([[cN, -sN * cI, sN * sI], [sN, cN * cI, -cN * sI], [0.0, sI, cI]])
            a, e, inc, Om, om = elements(mu, R.T @ r, R.T @ v)
            self.assertAlmostEqual(a, 500.0, places=7)
            self.assertAlmostEqual(e, 0.33, places=10)
            self.assertAlmostEqual(math.degrees(inc), 17.0, places=8)
            self.assertLess(angdiff(math.degrees(Om + N), 100.0), 1e-7)            # dog-leg Omega
            self.assertLess(angdiff(math.degrees(Om + N + om), 250.0), 1e-7)       # dog-leg varpi
            # against the ecliptic the inclination differs, by at most I
            _, _, inc_ecl, _, _ = elements(mu, r, v)
            self.assertGreater(abs(math.degrees(inc_ecl) - 17.0), 1e-3)
            self.assertLessEqual(abs(math.degrees(inc_ecl) - 17.0), math.degrees(I) + 1e-9)
            text = out.read_text()
            self.assertIn("relative to the invariable plane of Jupiter-Neptune", text)

    def test_test_particles_unaffected_by_planet_nine_options(self):
        with tempfile.TemporaryDirectory() as t:
            a, b = Path(t) / "a.txt", Path(t) / "b.txt"
            run(["--n-tp", "50", "--seed", "311", *BB], a)
            run(["--n-tp", "50", "--seed", "311", *BB, "--p9", self.SET_A, "--p9-plane", "invariable"], b)
            ba, bb = bodies(a), bodies(b)
            # barycentric: the shift of the barycentre by the other Planet Nine moves every body equally
            shift = ba["Sun"][1] - bb["Sun"][1]
            for n in ba:
                if n.startswith("tp"):
                    np.testing.assert_allclose(ba[n][1] - bb[n][1], shift, rtol=0, atol=1e-12)

    def test_bad_options(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "x.txt"
            self.assertNotEqual(run(["--p9", "e=0.2,q=300"], out).returncode, 0)
            self.assertNotEqual(run(["--p9", "mass=7"], out).returncode, 0)
            self.assertNotEqual(run(["--p9-plane", "invariable", "--j2", "Jupiter"], out).returncode, 0)


if __name__ == "__main__":
    unittest.main()
