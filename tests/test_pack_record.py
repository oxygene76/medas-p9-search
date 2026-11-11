# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests of tools/pack_record.py.   build/venv/bin/python -I tests/test_pack_record.py -v"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = [sys.executable, "-I", str(ROOT / "tools/pack_record.py")]


def run(*a):
    return subprocess.run(TOOL + list(a), capture_output=True, text=True)


class PackRecord(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        (t / "run/segments/seg000").mkdir(parents=True)
        (t / "run/segments/seg000/result.txt").write_text("result_sha256=00\n")
        (t / "run/segments.tsv").write_text("0\t1\t2\t3\t00\t-\n")
        (t / "run/run.pid").write_text("123\n")
        (t / "eval.json").write_text("{}\n")
        (t / "README.md").write_text("# record\n")
        self.spec = t / "spec.json"
        self.spec.write_text(json.dumps({"record": "test", "top": [{"src": "README.md", "name": "README.md"}],
            "parts": [{"tar": "runs.tar", "add": [{"src": "run", "arcname": "runs/x", "exclude": ["*.pid"]}]},
                      {"tar": "evaluation.tar", "add": [{"src": "eval.json", "arcname": "evaluation/x/result.json"}]}]}))
        self.t = t

    def tearDown(self):
        self.tmp.cleanup()

    def test_pack_verify_reproducible(self):
        a, b = self.t / "a", self.t / "b"
        self.assertEqual(run("pack", str(self.spec), str(a)).returncode, 0)
        self.assertEqual(run("pack", str(self.spec), str(b)).returncode, 0)
        for f in ("runs.tar", "evaluation.tar", "MANIFEST.sha256", "README.md"):
            self.assertEqual((a / f).read_bytes(), (b / f).read_bytes(), f)
        m = (a / "MANIFEST.sha256").read_text()
        self.assertIn("runs.tar:runs/x/segments.tsv", m)
        self.assertNotIn("run.pid", m)
        r = run("verify", str(a))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_verify_finds_changes(self):
        a = self.t / "a"
        run("pack", str(self.spec), str(a))
        (a / "README.md").write_text("# changed\n")
        r = run("verify", str(a))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("FAIL README.md", r.stdout)
        a2 = self.t / "a2"
        run("pack", str(self.spec), str(a2))
        (a2 / "extra.txt").write_text("x\n")
        self.assertNotEqual(run("verify", str(a2)).returncode, 0)

    def test_refuses_existing_outdir(self):
        self.assertNotEqual(run("pack", str(self.spec), str(self.t)).returncode, 0)


if __name__ == "__main__":
    unittest.main()
