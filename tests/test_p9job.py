# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests of the encounter radii in tools/p9job.py: assigned by planet name, never by order.

  P9TEST_P9SIM=build/test/p9sim P9TEST_P9GPU=build/gpu-cpu/p9gpu python -I tests/test_p9job.py -v

(`make test` sets both.) The end-to-end tests make a small job, run it with
each program and check, by name, the radii the program reports it used: the
check that would have caught the wrong order of 2026-10-19 (Uranus got Planet
Nine's 7 au, Planet Nine Uranus' 0.47 au).
"""

import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import p9job  # noqa: E402

# Hill radii of the test case (docs/close-encounters.md)
HILL = {"Jupiter": "0.3552", "Saturn": "0.4374", "Uranus": "0.4672", "Neptune": "0.7759", "P9": "6.9836"}
IDS = {"Jupiter": 1, "Saturn": 2, "Uranus": 3, "Neptune": 4, "P9": 5}


def job_with(radii, ids):
    return {"params": {"removal": {"encounter": {"radii_au": radii, "body_ids": ids}}}}


def items(env):
    return dict(x.split("=") for x in env.split(","))


class EncounterEnv(unittest.TestCase):
    def test_any_order_of_job_json_gives_the_same_assignment(self):
        want = {str(IDS[n]): HILL[n] for n in HILL}
        names = list(HILL)
        for seed in range(20):
            random.Random(seed).shuffle(names)
            radii = {n: HILL[n] for n in names}
            ids = {n: IDS[n] for n in reversed(names)}
            self.assertEqual(items(p9job.encounter_env(job_with(radii, ids))), want)

    def test_job_json_round_trip_sorted_by_name(self):
        # job.json is written with sort_keys: the order that broke the old positional list
        job = json.loads(json.dumps(job_with(HILL, IDS), sort_keys=True))
        self.assertEqual(list(job["params"]["removal"]["encounter"]["radii_au"]), ["Jupiter", "Neptune", "P9", "Saturn", "Uranus"])
        env = items(p9job.encounter_env(job))
        self.assertEqual(env["5"], "6.9836")  # Planet Nine
        self.assertEqual(env["3"], "0.4672")  # Uranus

    def test_old_jobs_without_ids_are_refused(self):
        with self.assertRaises(SystemExit):
            p9job.encounter_env({"params": {"removal": {"encounter": {"radii_au": HILL}}}})

    def test_names_must_agree(self):
        with self.assertRaises(SystemExit):
            p9job.encounter_env(job_with(HILL, {**IDS, "Pluto": 6}))

    def test_no_radii_no_variable(self):
        self.assertIsNone(p9job.encounter_env({"params": {"removal": {"encounter": {"radii_au": {}}}}}))
        self.assertIsNone(p9job.encounter_env({"params": {}}))

    def test_report_of_the_program_is_checked_by_name(self):
        job = job_with(HILL, IDS)
        good = "\n".join(f"encounter_radius id={IDS[n]} au={HILL[n]}" for n in HILL)
        self.assertEqual(p9job.check_encounter_report(job, good)["P9"], 6.9836)
        swapped = good.replace("id=3 au=0.4672", "id=3 au=6.9836").replace("id=5 au=6.9836", "id=5 au=0.4672")
        with self.assertRaises(SystemExit):
            p9job.check_encounter_report(job, swapped)
        with self.assertRaises(SystemExit):
            p9job.check_encounter_report(job, "")  # a program that reports nothing


class HillRadii(unittest.TestCase):
    def test_names_ids_and_radii_from_the_start_file(self):
        with tempfile.TemporaryDirectory() as d:
            ic = Path(d) / "ic.txt"
            subprocess.run([sys.executable, "-I", str(ROOT / "tools/make_ic.py"), "--out", str(ic), "--n-tp", "3"], check=True,
                           stderr=subprocess.DEVNULL)
            got = p9job.hill_radii(ic)
            self.assertEqual({n: r for n, (r, _) in got.items()}, HILL)
            self.assertEqual({n: i for n, (_, i) in got.items()}, IDS)


def program(var):
    p = os.environ.get(var)
    return Path(p).resolve() if p else None


class EndToEnd(unittest.TestCase):
    """A job made and run as in a campaign; the radii the program used, by name."""

    def run_job(self, prog, kind):
        with tempfile.TemporaryDirectory() as d:
            job = Path(d) / "job"
            mk = [sys.executable, "-I", str(ROOT / "tools/p9job.py"), "make", "--out", str(job), "--t-end", "1000", "--snapshots", "1",
                  "--n-tp", "5", "--program", kind, "--p9sim", str(prog), "--allow-dirty"]
            subprocess.run(mk, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            j = json.loads((job / "job.json").read_text())
            self.assertEqual(j["params"]["removal"]["encounter"]["body_ids"], IDS)
            env = dict(os.environ, P9GPU_MODE="cpu")
            subprocess.run([sys.executable, "-I", str(ROOT / "tools/p9job.py"), "run", str(job), "--p9sim", str(prog), "--any-version"],
                           check=True, stdout=subprocess.DEVNULL, env=env)
            used = json.loads((job / "result.json").read_text())["encounter_radii_used_au"]
            self.assertEqual(used, {n: float(r) for n, r in HILL.items()})

    @unittest.skipUnless(program("P9TEST_P9SIM"), "P9TEST_P9SIM not set")
    def test_p9sim(self):
        self.run_job(program("P9TEST_P9SIM"), "p9sim")

    @unittest.skipUnless(program("P9TEST_P9GPU"), "P9TEST_P9GPU not set")
    def test_p9gpu(self):
        self.run_job(program("P9TEST_P9GPU"), "p9gpu")


if __name__ == "__main__":
    unittest.main()
