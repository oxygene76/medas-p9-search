# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests of tools/publish_scan.py.   build/venv/bin/python -I tests/test_publish_scan.py -v"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import publish_scan as ps  # noqa: E402


def scan(name, data):
    out = []
    ps.scan_bytes(name, data, out)
    return [(c, w) for c, w, *_ in out]


class Rules(unittest.TestCase):
    def test_secrets_block(self):
        self.assertIn(("secret", "private key block"), scan("a.txt", b"-----BEGIN OPENSSH PRIVATE KEY-----\n"))
        self.assertIn(("secret", "secret assignment"), scan("x.env", b"API_KEY=abcdef0123456789xyz\n"))
        self.assertIn(("secret", "service token"), scan("x", b"ghp_" + b"a" * 36))
        self.assertEqual(scan("x", b"the secret of the method: a short one\n"), [])

    def test_gaia_data_blocks_queries_reported(self):
        row = b"source_id,ra,dec,parallax,phot_g_mean_mag,bp_rp\n1234,10.1,20.2,0.5,17.1,0.8\n"
        self.assertIn(("gaia", "Gaia columns"), scan("cat.csv", row))
        self.assertIn(("gaia-code", "Gaia columns"), scan("fetch.py", row))
        self.assertIn(("gaia", "Gaia table"), scan("q.json", b'{"table": "gaiadr3.gaia_source"}'))
        self.assertIn(("gaia", "file of the plate or own-images tools"), scan("runs/plates/f1/stars.tsv", b"1 2 3"))

    def test_private_text_only(self):
        self.assertIn(("private", "home or root path"), scan("env.txt", b"p9sim /home/someone/dev/x\n"))
        self.assertIn(("private", "internal host"), scan("r.md", b"on appmdp-05 at night\n"))
        self.assertIn(("private", "private IPv4"), scan("r.md", b"host 192.168.1.20 up\n"))
        self.assertEqual(scan("output.sa", b"\0\0C@S.ot 10.1.2.3"), [])          # binary: no private patterns
        self.assertEqual(scan("requirements.txt", b"astropy-iers-data==0.2026.10.19.0.52.1\n"), [])
        self.assertEqual(scan("CITATION.cff", ps.AUTHOR_EMAIL.encode()), [])


if __name__ == "__main__":
    unittest.main()
