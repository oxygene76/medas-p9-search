# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests of tools/pair_eval.py.   build/venv/bin/python -I tests/test_pair_eval.py -v

- On the equivalence runs (if present: runs/equiv-import-20261102 and the p9sim of p9prod-9a084ed) the tool gives
  exactly the published equivalence result (S per seed, mean +0.0033, 95 % [-0.0055, +0.0121], equivalent) and the V5
  encounter shares over 0-60 Myr are the V2 reference of addendum 13.
- It refuses a set with a segment not done (no interim look).
- The verdicts and the release record, on fake job trees with set values of S.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import pair_eval as pe  # noqa: E402

EQUIV = ROOT / "runs/equiv-import-20261102"
P9SIM = ROOT.parent / "medas-p9-search-bb2021/build/p9prod-9a084ed/bin/p9sim"


def fake_job(d, segments=10, done=None, n_tp=4000, left=3500):
    d.mkdir(parents=True)
    (d / "params.env").write_text(f"SEGMENT_YR=20000000\nSEGMENTS={segments}\nSNAPSHOTS_PER_SEGMENT=20\n")
    (d / "job.json").write_text(json.dumps({"params": {"ic": {"n_tp": n_tp}}}))
    rows = []
    for k in range(segments):
        s = d / "segments" / f"seg{k:03d}"
        s.mkdir(parents=True)
        if done is None or k < done:
            (s / "DONE").write_text("x\n")
        (s / "flybys.tsv").write_text("id\tfast_3\tclose_3\tfast_4\tclose_4\tfast_5\tclose_5\n" + "".join(f"{6 + i}\t{int(i < 40)}\t0\t0\t0\t0\t0\n" for i in range(n_tp)))
        rows.append(f"{k}\t{(k + 1) * 20000000}\t{left + 6}\t1.0\t{'0' * 64}\t-")
    (d / "segments.tsv").write_text("\n".join(rows) + "\n")


def fake_tree(root, seeds, done_v5=None):
    for s in seeds:
        fake_job(root / "v5/jobs" / f"PV5-s{s}", done=done_v5)
        for k in range(pe.PARTS):
            fake_job(root / "m/jobs" / f"PM-s{s}-part{k:02d}", n_tp=4000, left=200)


class Logic(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def stats_for(self, diffs):
        """A stand-in for equiv_eval.run_stats: S(V5) = 0.6 + d_s, S(M) = 0.6, in the order of the calls."""
        calls = []
        def stats(files):
            seed_index = len(calls) // 2
            group = "V5" if len(calls) % 2 == 0 else "M"
            calls.append(group)
            s = 0.6 + (diffs[seed_index] if group == "V5" else 0.0)
            return {"S": s, "S_obs_cut": s, "R200": s, "n_distant_200": 100}
        return stats

    def test_refuses_an_incomplete_set(self):
        fake_tree(self.root, pe.SETS["A"], done_v5=9)
        with self.assertRaises(SystemExit) as c:
            pe.evaluate("A", self.root / "v5", self.root / "m", "unused", stats=self.stats_for([0.0] * 9))
        self.assertIn("not done", str(c.exception))

    def test_verdicts(self):
        fake_tree(self.root, pe.SETS["B"])
        cases = {"equivalent": [0.005, -0.004, 0.002, 0.0, 0.003, -0.002, 0.001, 0.004, -0.001],
                 "not shown": [0.03, 0.01, 0.05, 0.02, 0.04, 0.0, 0.03, 0.06, 0.02],
                 "different": [0.10, 0.11, 0.09, 0.10, 0.12, 0.10, 0.11, 0.09, 0.10]}
        for verdict, diffs in cases.items():
            out = pe.evaluate("B", self.root / "v5", self.root / "m", "unused", stats=self.stats_for(diffs))
            self.assertEqual(out["verdict"], verdict, diffs)
            self.assertEqual(out["seeds"], list(range(341, 350)))
        self.assertEqual(out["information"]["left_200"], {"V5": 9 * 3500, "M": 9 * 16 * 200})
        enc = out["information"]["encounter_shares"]
        self.assertTrue(enc["reported, not deciding"])
        self.assertAlmostEqual(enc["V5 0-60 Myr"]["Uranus"]["fast"], 1.0)     # 40 of 4,000
        self.assertIn("not available", enc["M"])

    def test_release_text(self):
        res = {"S": {"mean": 0.001, "ci95": [-0.004, 0.006]}}
        t = pe.release_text("A", list(range(331, 340)), res, "abc1234")
        self.assertTrue(t.startswith("paired test V5 against MERCURIUS: equivalent\nset A, seeds 331-339"))
        self.assertIn("[-0.0040, +0.0060]", t)


@unittest.skipUnless((EQUIV / "p9equiv-v5-47c7381").exists() and P9SIM.exists(), "equivalence runs or p9sim not here")
class OnTheEquivalenceRuns(unittest.TestCase):
    def test_reproduces_the_equivalence_result(self):
        out = pe.evaluate("A", EQUIV / "p9equiv-v5-47c7381", EQUIV / "p9equiv-merc-47c7381", str(P9SIM),
                          seeds=list(range(101, 110)), v5_prefix="V5", m_prefix="M")
        published = {101: (0.6308, 0.6034), 102: (0.6092, 0.6094), 103: (0.6262, 0.6164), 104: (0.6133, 0.6032), 105: (0.6219, 0.6282),
                     106: (0.6194, 0.6160), 107: (0.6092, 0.6085), 108: (0.6082, 0.6201), 109: (0.6264, 0.6295)}
        for s, (v, m) in published.items():
            self.assertEqual(round(out["runs"][s]["V5"]["S"], 4), v)
            self.assertEqual(round(out["runs"][s]["M"]["S"], 4), m)
        self.assertEqual(round(out["S"]["mean"], 4), 0.0033)
        self.assertEqual([round(x, 4) for x in out["S"]["ci95"]], [-0.0055, 0.0121])
        self.assertEqual(out["verdict"], "equivalent")
        sh = out["information"]["encounter_shares"]["V5 0-60 Myr"]
        for planet, (f, c) in pe.v2.REFERENCE.items():
            self.assertAlmostEqual(sh[planet]["fast"], f, places=2)
            self.assertAlmostEqual(sh[planet]["close"], c, places=2)


if __name__ == "__main__":
    unittest.main()
