# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests of tools/publish_scan.py.   build/venv/bin/python -I tests/test_publish_scan.py -v"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import publish_scan as ps  # noqa: E402


# a host name of the known kind, put together here so that this file does not hold one
HOST = b"app" + b"mdp-" + b"05"


def scan(name, data):
    out = []
    ps.scan_bytes(name, data, out)
    return [(c, w) for c, w, *_ in out]


class Archives(unittest.TestCase):
    def test_tars_inside_a_directory_and_nested(self):
        """A record directory with tar files, and a .tar.gz inside a tar: their text files are scanned."""
        import io as _io, tarfile as _tar, tempfile as _tmp
        def tar_bytes(files, gz=False):
            buf = _io.BytesIO()
            with _tar.open(fileobj=buf, mode="w:gz" if gz else "w") as t:
                for n, d in files.items():
                    ti = _tar.TarInfo(n); ti.size = len(d); t.addfile(ti, _io.BytesIO(d))
            return buf.getvalue()
        inner = tar_bytes({"src/a.log": b"start on " + HOST + b"\n"}, gz=True)
        with _tmp.TemporaryDirectory() as d:
            Path(d, "rec").mkdir()
            Path(d, "rec/runs.tar").write_bytes(tar_bytes({"runs/x/start.log": b"GPU-1cf3e09f-4b70-9369-f482-af987eff83cd\n"}))
            Path(d, "rec/code.tar").write_bytes(tar_bytes({"code/src.tar.gz": inner}))
            out = []
            ps.scan_path(Path(d, "rec"), out)
        whats = sorted((w, loc.split(":")[0]) for _, w, loc, _ in out)
        self.assertIn(("GPU UUID", "rec/runs.tar"), whats)
        self.assertIn(("host name", "rec/code.tar"), whats)
        self.assertTrue(any(loc.startswith("rec/code.tar:code/src.tar.gz:src/a.log") for _, _, loc, _ in out))


class Hosts(unittest.TestCase):
    def test_host_names_block_unless_the_file_is_listed(self):
        data = b"on " + HOST + b" at night\n"
        self.assertIn(("host", "host name"), scan("r.md", data))
        self.assertIn(("host", "host name"), scan("output.sa", b"\0\0" + data))      # binary too
        self.assertEqual(scan("output.sa", b"\0\x80F" + b"LUX@\xda\0"), [])              # by chance in binary data
        self.assertIn(("host", "host name"), scan("r.md", b"backup on F" + b"LUX\n"))
        self.assertEqual(scan("r.md", b"the flux of a field; Neptune\n"), [])
        import hashlib
        ps.HOST_EXCEPTIONS[hashlib.sha256(data).hexdigest()] = "e3 x/r.md"
        try:
            self.assertIn(("host-listed", "host name"), scan("r.md", data))
            self.assertIn(("host", "host name"), scan("r.md", data + b"changed\n"))   # another version blocks
        finally:
            ps.HOST_EXCEPTIONS.clear()

    def test_account_name_only_in_account_context(self):
        acc = b"p9" + b"sim"
        self.assertIn(("account", "account name"), scan("r.md", b"Run as " + acc + b", in this directory.\n"))
        self.assertIn(("account", "account name"), scan("r.sh", b"# Runs as the user of the runs (" + acc + b"), never as root.\n"))
        self.assertIn(("account", "account name"), scan("r.md", b"cd /home/" + acc + b"/runs\n"))
        self.assertEqual(scan("r.md", b"MERCURIUS (" + acc + b") removes with the same rule\n"), [])
        self.assertEqual(scan("r.md", b"bin/" + acc + b" dump out.sa 0\n"), [])
        self.assertEqual(scan("Makefile", b"# the host part is built with the same flags\n# as " + acc + b". PTX\n"), [])

    def test_history_lines_are_reported(self):
        out = []
        ps.scan_bytes("c:r.md", b"on " + HOST, out, line_only=True)
        self.assertEqual([(c, w) for c, w, *_ in out], [("host-line", "host name")])


class Fixtures(unittest.TestCase):
    def test_own_fixtures_do_not_block_elsewhere_they_do(self):
        key = b"-----BEGIN OPENSSH " + b"PRIVATE KEY-----\n"
        self.assertIn(("fixture", "private key block"), scan("x:tests/test_publish_scan.py", key))
        self.assertIn(("secret", "private key block"), scan("x:tests/other.py", key))
        other = b"API_KEY=" + b"zyx9876543210fedcba\n"
        self.assertIn(("secret", "secret assignment"), scan("x:tests/test_publish_scan.py", other))


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
        self.assertIn(("private", "private IPv4"), scan("r.md", b"host 192.168.1.20 up\n"))
        self.assertEqual(scan("output.sa", b"\0\0C@S.ot 10.1.2.3"), [])          # binary: no private patterns
        self.assertEqual(scan("requirements.txt", b"astropy-iers-data==0.2026.10.19.0.52.1\n"), [])
        self.assertEqual(scan("CITATION.cff", ps.AUTHOR_EMAIL.encode()), [])


if __name__ == "__main__":
    unittest.main()
