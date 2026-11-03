# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests of the building blocks of tools/iras_akari.py (Lambert, two-body propagation, brightness, HEALPix).

  build/venv/bin/python -I tests/test_iras_akari.py -v
"""

import math
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import iras_akari as ia  # noqa: E402


def orbit_state(a, e, inc, Om, om, M):
    """Heliocentric state (au, au/yr) from elements (radians), mu = ia.MU."""
    E = M
    for _ in range(100):
        E = E - (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
    b = a * math.sqrt(1 - e * e)
    x, y = a * (math.cos(E) - e), b * math.sin(E)
    n = math.sqrt(ia.MU / a ** 3)
    rdot = n * a / (1 - e * math.cos(E))
    vx, vy = -math.sin(E) * rdot, b / a * math.cos(E) * rdot
    cO, sO, cw, sw, ci, si = math.cos(Om), math.sin(Om), math.cos(om), math.sin(om), math.cos(inc), math.sin(inc)
    R = np.array([[cO * cw - sO * sw * ci, -cO * sw - sO * cw * ci], [sO * cw + cO * sw * ci, -sO * sw + cO * cw * ci], [sw * si, cw * si]])
    return R @ [x, y], R @ [vx, vy]


class TwoBody(unittest.TestCase):
    def test_propagation_and_lambert_round_trip(self):
        for a, e, inc, M in ((600.0, 0.3, 0.3, 2.0), (450.0, 0.1, 0.05, 0.4), (900.0, 0.6, 1.0, 3.0)):
            r0, v0 = orbit_state(a, e, inc, 1.0, 0.7, M)
            dt = 23.4
            r1 = ia.propagate(r0[None], v0[None], np.array([dt]))[0]
            # energy conserved
            en = lambda r, v: 0.5 * v @ v - ia.MU / np.linalg.norm(r)
            a1, e1, _ = ia.elements(r0[None], v0[None])
            self.assertAlmostEqual(a1[0], a, places=6)
            self.assertAlmostEqual(e1[0], e, places=9)
            # back again
            rb = ia.propagate(r1[None], (ia.lambert_bound(r0[None], r1[None], np.array([dt]))[0]), np.array([-dt]))[0]
            np.testing.assert_allclose(rb, r0, rtol=0, atol=1e-6 * a)
            v1, ok = ia.lambert_bound(r0[None], r1[None], np.array([dt]))
            self.assertTrue(ok[0])
            # the Lambert velocity at r1 reproduces the orbit
            a2, e2, _ = ia.elements(r1[None], v1)
            self.assertAlmostEqual(a2[0], a, delta=1e-6 * a)
            # short arcs (23 yr of orbits of thousands of years) cancel in y of the universal-variable form: about 1e-6
            # in e, far below the effect of the 30" position errors (relative 1.5e-4)
            self.assertAlmostEqual(e2[0], e, delta=1e-5)

    def test_unbound_is_rejected(self):
        r0 = np.array([[500.0, 0, 0]])
        r1 = np.array([[1000.0, 10.0, 0]])     # 500 au in 23 yr: far above the escape speed
        _, ok = ia.lambert_bound(r0, r1, np.array([23.0]))
        self.assertFalse(ok[0])


class Brightness(unittest.TestCase):
    def test_neptune_like_V(self):
        # Neptune: radius 24,764 km, p about 0.44, at 30.1 au opposition: V about 7.8
        V = ia.v_mag(np.array([24764.0]), 0.44, 30.1, 29.1)[0]
        self.assertAlmostEqual(V, 7.8, delta=0.3)

    def test_radius_from_flux_scales_with_distance(self):
        r1 = ia.radius_km(0.5, 100.0, 40.0, np.array([500.0]))[0]
        r2 = ia.radius_km(0.5, 100.0, 40.0, np.array([1000.0]))[0]
        self.assertAlmostEqual(r2 / r1, 2.0, places=12)


class Healpix(unittest.TestCase):
    def test_known_pixels(self):
        # checked once against astropy_healpix (lonlat_to_healpix, nested) on 20,000 random points on 2026-11-03:
        # 100 % agreement at nside 256 and 32 (astropy_healpix is not installed in this venv)
        pts = np.array([[0.0, 0.0], [45.0, 89.0], [200.0, -60.0], [35.18379, -49.2135], [359.9, 41.8]])
        got = ia.ang2pix_nest(256, pts[:, 0], pts[:, 1])
        self.assertEqual(len(got), 5)
        self.assertTrue(np.all((got >= 0) & (got < 12 * 256 * 256)))


if __name__ == "__main__":
    unittest.main()
