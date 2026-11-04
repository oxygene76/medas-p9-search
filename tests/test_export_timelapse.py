# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests of tools/export_timelapse.py on the synthetic runs of tests/test_prod_eval.py.

  build/venv/bin/python -I tests/test_export_timelapse.py -v

- The curves give the evaluation's M1 and M2 (tools/prod_eval.py) over the window, exactly as the page computes them.
- A run split into two parts (disjoint test particles, the same planets) gives the same curves and the same data.bin.
- data.bin: the subset by id, and the dvarpi of the drawn elements against Planet Nine is the evaluation's.
- The source hash is the sha256 of SOURCES.sha256, which lists every file read.
- Runs of the evaluated campaigns only with a complete evaluation.
"""

import hashlib
import json
import math
import struct
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
import export_timelapse as ex  # noqa: E402
import prod_eval as pe  # noqa: E402
from test_prod_eval import TIMES, make_run  # noqa: E402

N_TP = 8000


def decode(buf):
    """P9WEB001 as src/lib/simdata.ts of medas-notary-web decodes it."""
    assert buf[:8] == ex.MAGIC
    (n,) = struct.unpack_from("<I", buf, 8)
    off, out = 12, []
    for _ in range(n):
        t, a9, e9, i9, O9, w9 = struct.unpack_from("<d5d", buf, off)
        (m,) = struct.unpack_from("<I", buf, off + 48)
        off += 52
        rec = np.frombuffer(buf, dtype="<u2", count=6 * m, offset=off).reshape(m, 6).astype(float)
        off += 12 * m
        out.append({"t": t, "p9": (a9, e9, i9, O9, w9), "idx": rec[:, 0].astype(int), "a": rec[:, 1] * 0.25, "e": rec[:, 2] / 65535,
                    "i": rec[:, 3] / 100, "node": rec[:, 4] / 100, "peri": rec[:, 5] / 100})
    assert off == len(buf)
    return out


def split(src, dst_a, dst_b, cut):
    """The npz run of src as two parts: test particles with index < cut and the rest, each with all massive bodies."""
    for d in (dst_a, dst_b):
        d.mkdir(parents=True, exist_ok=True)
    for p in sorted(src.glob("snap-*.npz")):
        z = np.load(p, allow_pickle=False)
        names = z["names"].astype(str)
        tp = np.char.startswith(names, "tp")
        idx = np.array([int(n[2:]) if t else -1 for n, t in zip(names, tp)])
        for d, keep in ((dst_a, ~tp | (idx < cut)), (dst_b, ~tp | (idx >= cut))):
            np.savez(d / p.name, t=z["t"], names=z["names"][keep], m=z["m"][keep], r=z["r"][keep], v=z["v"][keep])


class Export(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.tmp.name)
        make_run(cls.base / "run", TIMES, n_tp=N_TP)
        cls.res, cls.series = pe.evaluate(cls.base / "run", n_tp=N_TP)
        cls.m, cls.c = ex.export([cls.base / "run"], cls.base / "out", run_id="syn", title="synthetic", group="test", show=1000, n_tp=N_TP)
        split(cls.base / "run", cls.base / "parts" / "a", cls.base / "parts" / "b", 3000)
        cls.m2, cls.c2 = ex.export([cls.base / "parts" / "a", cls.base / "parts" / "b"], cls.base / "out2", run_id="syn2", title="split",
                                   group="test", show=1000, n_tp=N_TP)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_pooled_measures_are_the_evaluations(self):
        m1, m2 = ex.pooled(self.c)
        self.assertLess(pe.angdist(m1, self.res["measures"]["M1_deg"]), 1e-9)
        self.assertAlmostEqual(m2, self.res["measures"]["M2_mean_R"], places=12)
        self.assertEqual(self.m["export"]["snapshots_in_window"], self.res["snapshots_in_window"])

    def test_per_snapshot_curves_are_the_evaluations(self):
        sel = self.c["selections"]
        for k, row in enumerate(self.series):
            self.assertEqual(self.c["t_yr"][k], row["t_yr"])
            self.assertEqual(self.c["n_tp"][k], row["n_tp"])
            self.assertEqual(sel["SBB"]["n"][k], row["n_SBB"])
            C, S, n = sel["SBB"]["C"][k], sel["SBB"]["S"][k], sel["SBB"]["n"][k]
            self.assertLess(pe.angdist(math.degrees(math.atan2(S, C)) % 360, row["M1_deg"]), 1e-9)
            self.assertAlmostEqual(math.hypot(C, S) / n, row["R"], places=12)
            for name in ("S1", "S2", "S3"):
                self.assertEqual(sel[name]["n"][k], row[f"{name}_n"])
                self.assertAlmostEqual(math.hypot(sel[name]["C"][k], sel[name]["S"][k]) / sel[name]["n"][k], row[f"{name}_R"], places=12)
            self.assertGreater(sel["SBB"]["anti"][k], 0.3 * n)      # von Mises about 180 deg for most of S_BB

    def test_split_run_gives_the_same(self):
        for k in self.c["selections"]:
            for f in ("n", "anti"):
                self.assertEqual(self.c["selections"][k][f], self.c2["selections"][k][f])
            for f in ("C", "S"):
                np.testing.assert_allclose(self.c["selections"][k][f], self.c2["selections"][k][f], rtol=0, atol=1e-9)
        self.assertEqual((self.base / "out" / "data.bin").read_bytes(), (self.base / "out2" / "data.bin").read_bytes())
        self.assertEqual(len(self.m2["parts"]), 2)

    def test_data_subset_and_dvarpi(self):
        snaps = decode((self.base / "out" / "data.bin").read_bytes())
        self.assertEqual(len(snaps), len(TIMES))
        self.assertEqual(self.m["export"]["subset"]["stride"], 8)
        for s, t in zip(snaps, TIMES):
            self.assertEqual(s["t"], t)
            self.assertTrue(np.all(s["idx"] % 8 == 0))
            self.assertEqual(len(s["idx"]), N_TP // 8)
            el = pe.frame_elements(*ex.Part._npz(sorted((self.base / "run").glob("snap-*.npz"))[TIMES.index(t)]))
            ref = dict(zip(el["idx"], el["dvarpi"]))
            varpi9 = (s["p9"][3] + s["p9"][4]) % 360
            dv = (s["node"] + s["peri"] - varpi9) % 360
            err = [pe.angdist(d, ref[i]) for i, d in zip(s["idx"], dv)]
            self.assertLess(max(err), 0.02)
            self.assertLess(pe.angdist(varpi9, el["p9"]["varpi"]), 1e-9)

    def test_source_hash(self):
        out = self.base / "out"
        src = (out / "SOURCES.sha256").read_text()
        self.assertEqual(self.m["sources"]["sha256"], hashlib.sha256(src.encode()).hexdigest())
        self.assertEqual(self.m["sources"]["files"], len(TIMES))
        for line in src.splitlines():
            h, rel = line.split("  ", 1)
            self.assertEqual(h, ex.sha256_file(self.base / rel))
        for f in ("data.bin", "curves.json"):
            self.assertEqual(self.m["files"][f]["sha256"], ex.sha256_file(out / f))
        self.assertEqual(json.loads((out / "manifest.json").read_text())["sources"]["sha256"], self.m["sources"]["sha256"])

    def test_evaluated_groups_need_a_complete_evaluation(self):
        with self.assertRaises(SystemExit):
            ex.export([self.base / "run"], self.base / "x", run_id="p", title="p", group="production", n_tp=N_TP)
        bad = self.base / "incomplete.json"
        bad.write_text(json.dumps({"complete": False}))
        with self.assertRaises(SystemExit):
            ex.export([self.base / "run"], self.base / "x", run_id="p", title="p", group="production", n_tp=N_TP, evaluation=bad)
        good = self.base / "result.json"
        good.write_text(json.dumps({"complete": True, "verdict": "decided", "criteria": "production"}))
        m, _ = ex.export([self.base / "run"], self.base / "y", run_id="p", title="p", group="production", n_tp=N_TP, evaluation=good)
        self.assertEqual(m["evaluation"]["sha256"], ex.sha256_file(good))

    def test_every(self):
        m, c = ex.export([self.base / "run"], self.base / "z", run_id="e", title="e", group="test", n_tp=N_TP, every=1e9)
        self.assertEqual(c["t_yr"], [1e9, 2e9, 3e9, 4e9])


if __name__ == "__main__":
    unittest.main()
