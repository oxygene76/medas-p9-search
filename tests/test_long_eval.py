# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests of tools/long_eval.py.   build/venv/bin/python -I tests/test_long_eval.py -v

Without the runs of seeds 110-112 (no look at R before the evaluation): the windows and the rule of too few
survivors, d and its standard error, every branch of the decision, the refusal of incomplete runs, the snapshot
addressing of both packages, and the whole evaluation on fake job trees with set values of R.
"""

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import equiv_eval as ee  # noqa: E402
import long_eval as le  # noqa: E402

EQUIV = ROOT / "runs/equiv-import-20261102"
P9SIM = ROOT.parent / "medas-p9-search-bb2021/build/p9prod-9a084ed/bin/p9sim"


def d_of(**means):
    """{time: mean_se} from given means (se 0.01 unless a tuple (mean, se) is given); None for a missing time."""
    out = {}
    for t in list(le.TIMES) + ["1-4"]:
        key = {"0.5": "t05", "1": "t1", "2": "t2", "4": "t4", "1-4": "t14"}[t]
        v = means.get(key, 0.0)
        if v is None:
            out[t] = None
            continue
        m, se = v if isinstance(v, tuple) else (v, 0.01)
        out[t] = {"n": 3, "mean": m, "sd": se * math.sqrt(3), "se": se, "d_s": [m, m, m]}
    return out


def fake_job(d, seg_yr, segments, per, done=None, left=500):
    d.mkdir(parents=True)
    (d / "params.env").write_text(f"# test\nSEGMENT_YR={seg_yr}\nSEGMENTS={segments}\nSNAPSHOTS_PER_SEGMENT={per}\n")
    rows = []
    for k in range(segments):
        s = d / "segments" / f"seg{k:03d}"
        s.mkdir(parents=True)
        if done is None or k < done:
            (s / "DONE").write_text("x\n")
        rows.append(f"{k}\t{(k + 1) * seg_yr}\t{left + 6}\t1.0\t{'0' * 64}\t-")
    (d / "segments.tsv").write_text("\n".join(rows) + "\n")


def fake_tree(root, done_v5=None, v5_segments=40):
    v5, m = root / "v5", root / "m"
    for s in le.SEEDS:
        fake_job(v5 / "jobs" / f"V5-s{s}", 4_000_000_000 // v5_segments, v5_segments, 10 * 40 // v5_segments, done=done_v5, left=540)
        for k in range(le.PARTS):
            fake_job(m / "jobs" / f"M-s{s}-part{k:02d}", 20_000_000, 200, 2, left=70)
    return v5, m


class Windows(unittest.TestCase):
    def test_sizes(self):
        self.assertEqual(len(le.SNAPS), 400)
        self.assertEqual(le.window(400_000_000, 500_000_000)[0], 400_000_000)
        self.assertEqual(len(le.window(400_000_000, 500_000_000)), 11)
        self.assertEqual(len(le.window(*le.SPAN_1_4)), 301)

    def test_mean_and_few(self):
        series = {T: (0.5, 200) for T in le.SNAPS}
        series[500_000_000] = (0.6, 200)
        self.assertAlmostEqual(le.window_S(series, 400_000_000, 500_000_000), (10 * 0.5 + 0.6) / 11)
        w = le.window(3_900_000_000, 4_000_000_000)
        for T in w[:5]:
            series[T] = (0.9, 99)                    # 5 of 11 below 100: still computed, with their R
        self.assertAlmostEqual(le.window_S(series, 3_900_000_000, 4_000_000_000), (5 * 0.9 + 6 * 0.5) / 11)
        series[w[5]] = (0.9, 50)                     # 6 of 11: more than half
        self.assertIsNone(le.window_S(series, 3_900_000_000, 4_000_000_000))
        S = le.run_S(series)
        self.assertIsNone(S["4"])
        self.assertIsNotNone(S["1-4"])               # 6 of 301

    def test_dbar(self):
        S = {s: {"V5": {t: 0.6 + 0.01 * i for t in list(le.TIMES) + ["1-4"]}, "M": {t: 0.6 for t in list(le.TIMES) + ["1-4"]}}
             for i, s in enumerate(le.SEEDS)}
        d = le.dbar(S)
        self.assertAlmostEqual(d["4"]["mean"], 0.01)
        self.assertAlmostEqual(d["4"]["se"], 0.01 / math.sqrt(3))
        S[111]["M"]["2"] = None                      # one run without S at 2 Gyr: no d there
        self.assertIsNone(le.dbar(S)["2"])
        self.assertIsNotNone(le.dbar(S)["4"])


class Decision(unittest.TestCase):
    def test_found(self):
        self.assertEqual(le.decide(d_of(t05=0.01, t1=0.03, t2=0.04, t4=0.06))[0], "growing bias found")
        self.assertEqual(le.decide(d_of(t05=-0.01, t1=-0.03, t2=-0.04, t4=-0.06))[0], "growing bias found")

    def test_not_found(self):
        cases = {"below 0.05": d_of(t05=0.01, t1=0.03, t2=0.04, t4=0.049),
                 "within 2 SE": d_of(t05=0.01, t1=0.03, t2=0.04, t4=(0.06, 0.031)),
                 "sign at 1 Gyr": d_of(t05=0.01, t1=-0.01, t2=0.04, t4=0.06),
                 "sign at 2 Gyr": d_of(t05=0.01, t1=0.03, t2=-0.04, t4=0.06),
                 "not growing": d_of(t05=0.07, t1=0.03, t2=0.04, t4=0.06),
                 "zero at 1 Gyr": d_of(t05=0.01, t1=0.0, t2=0.04, t4=0.06)}
        for name, d in cases.items():
            with self.subTest(name):
                self.assertEqual(le.decide(d)[0], "no growing bias found")

    def test_exactly_two_se_is_not_more(self):
        self.assertEqual(le.decide(d_of(t05=0.01, t1=0.03, t2=0.04, t4=(0.06, 0.03)))[0], "no growing bias found")

    def test_missing_times(self):
        self.assertEqual(le.decide(d_of(t05=0.01, t1=None, t2=0.04, t4=0.06))[0], "growing bias found")
        self.assertEqual(le.decide(d_of(t05=0.01, t1=-0.03, t2=None, t4=0.06))[0], "no growing bias found")
        self.assertEqual(le.decide(d_of(t05=0.01, t1=None, t2=None, t4=0.06))[0], "not decided")
        self.assertEqual(le.decide(d_of(t05=0.01, t1=0.03, t2=0.04, t4=None))[0], "not decided")
        self.assertEqual(le.decide(d_of(t05=None, t1=0.03, t2=0.04, t4=0.06))[0], "not decided")


class Data(unittest.TestCase):
    def test_package_file_addresses(self):
        with tempfile.TemporaryDirectory() as tmp:
            v5, m = fake_tree(Path(tmp))
            j = v5 / "jobs" / "V5-s110"
            self.assertEqual(ee.package_file(j, 10_000_000), (j / "segments/seg000/output.sa", 0))
            self.assertEqual(ee.package_file(j, 100_000_000), (j / "segments/seg000/output.sa", 9))
            self.assertEqual(ee.package_file(j, 4_000_000_000), (j / "segments/seg039/output.sa", 9))
            j = m / "jobs" / "M-s110-part00"
            self.assertEqual(ee.package_file(j, 20_000_000), (j / "segments/seg000/output.sa", 1))
            self.assertEqual(ee.package_file(j, 30_000_000), (j / "segments/seg001/output.sa", 0))
            self.assertEqual(ee.package_file(j, 4_000_000_000), (j / "segments/seg199/output.sa", 1))

    def test_refuses_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            v5, m = fake_tree(Path(tmp), done_v5=39)
            with self.assertRaises(SystemExit) as e:
                le.evaluate(v5, m, "p9sim-not-used", series=lambda jl, pool: {})
            self.assertIn("not done", str(e.exception))

    def test_refuses_other_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            v5, m = fake_tree(Path(tmp), v5_segments=20)    # 200 Myr segments, 20 snapshots each: still 10 Myr
            le.complete(le.jobs(v5, m))
        with tempfile.TemporaryDirectory() as tmp:
            v5, m = fake_tree(Path(tmp))
            (v5 / "jobs/V5-s111/params.env").write_text("SEGMENT_YR=100000000\nSEGMENTS=39\nSNAPSHOTS_PER_SEGMENT=10\n")
            with self.assertRaises(SystemExit):
                le.complete(le.jobs(v5, m))

    def test_evaluate_on_fake_trees(self):
        """d grows from 0.01 to 0.06 in V5 against a constant M: found; the outputs as written by main()."""
        def series(job_list, pool):
            v5 = job_list[0].name.startswith("V5")
            seed = int(job_list[0].name.split("-")[1][1:])
            out = {}
            for T in le.SNAPS:
                r = 0.6 + (0.01 + 0.05 * T / 4e9 + 0.001 * (seed - 111) if v5 else 0.0)
                out[T] = (r, 300 if v5 else 320, 540 if v5 else 560)
            return out
        with tempfile.TemporaryDirectory() as tmp:
            v5, m = fake_tree(Path(tmp))
            out, data = le.evaluate(v5, m, "p9sim-not-used", series=series)
            self.assertEqual(out["verdict"], "growing bias found", out["reasons"])
            self.assertAlmostEqual(out["d"]["4"]["mean"], 0.01 + 0.05 * 3.95e9 / 4e9, places=12)
            self.assertAlmostEqual(out["d"]["4"]["sd"], 0.001, places=12)
            self.assertEqual(out["information"]["test particles left at 4 Gyr"]["110"], {"V5": 540, "M": 8 * 70})
            json.dumps(out)
            csv_text = le.timeseries_csv(data)
            self.assertEqual(len(csv_text.splitlines()), 1 + 3 * 2 * 400)
            text = le.report(out)
            self.assertIn("decision: growing bias found", text)
            self.assertIn("(reported, not deciding)", text)
            self.assertIn("is not evidence", text)

    @unittest.skipUnless(EQUIV.exists() and P9SIM.exists(), "equivalence runs or p9sim not present")
    def test_reader_on_equivalence_runs(self):
        """series_of reads the real snapshots of both packages (V5 one job, M its slices pooled): on the equivalence
        runs of seed 101 at 160-200 Myr the mean of R is the published S of V5 and of M exactly."""
        from concurrent.futures import ThreadPoolExecutor
        pub = json.loads((ROOT / "docs/equivalence-result-20261102/equiv-eval.json").read_text())["runs"]["101"]
        snaps = le.SNAPS
        try:
            le.SNAPS = [int(T) for T in ee.TIMES]
            with ThreadPoolExecutor(max_workers=4) as pool:
                v5 = le.series_of([EQUIV / "p9equiv-v5-47c7381/jobs/V5-s101"], str(P9SIM), pool)
                m = le.series_of([EQUIV / f"p9equiv-merc-47c7381/jobs/M-s101-part{k:02d}" for k in range(16)], str(P9SIM), pool)
        finally:
            le.SNAPS = snaps
        for got, grp in ((v5, "V5"), (m, "M")):
            self.assertEqual(sum(got[T][0] for T in sorted(got)) / len(got), pub[grp]["S"])
            self.assertEqual(got[max(got)][1], pub[grp]["n_distant_200"])

    def test_main_refuses_existing_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            sys.argv = ["long_eval.py", "--v5", tmp, "--m", tmp, "--p9sim", "x", "--out", tmp]
            with self.assertRaises(SystemExit) as e:
                le.main()
            self.assertIn("exists", str(e.exception))


if __name__ == "__main__":
    unittest.main()
