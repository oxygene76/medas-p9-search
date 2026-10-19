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
# radii of the rule at dt = 0.5 yr (p9job.RADII_RULE): Planet Nine 0.5 au, the others max(Hill, resolution)
RULE_05 = {"Jupiter": "1.8575", "Saturn": "1.2427", "Uranus": "0.6643", "Neptune": "0.7759", "P9": "0.5000"}


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

    def test_rule_scales_with_the_step(self):
        with tempfile.TemporaryDirectory() as d:
            ic = Path(d) / "ic.txt"
            subprocess.run([sys.executable, "-I", str(ROOT / "tools/make_ic.py"), "--out", str(ic), "--n-tp", "3"], check=True,
                           stderr=subprocess.DEVNULL)
            self.assertEqual(p9job.encounter_radii(ic, 0.5, [])["radii_au"], RULE_05)
            r5 = p9job.encounter_radii(ic, 5.0, [])["radii_au"]
            self.assertEqual(r5["P9"], "2.3208")  # 0.5 au * 10^(2/3)
            self.assertEqual(r5["Neptune"], "3.2579")  # the rule exceeds Neptune's Hill radius at this step
            e = p9job.encounter_radii(ic, 0.25, ["P9=0.5000", "Neptune=0.7759"])
            self.assertEqual((e["radii_au"]["P9"], e["radii_au"]["Neptune"], e["radii_au"]["Jupiter"]), ("0.5000", "0.7759", "1.1702"))
            self.assertEqual(e["overrides"], ["P9=0.5000", "Neptune=0.7759"])
            with self.assertRaises(SystemExit):
                p9job.encounter_radii(ic, 0.5, ["Pluto=1"])
            # flyby term (1.5 v99 dt): J2 comparison of 2026-10-19 with dt = 1 yr
            e = p9job.encounter_radii(ic, 1.0, [], ["P9=0.6", "Neptune=1.13"])
            self.assertEqual((e["radii_au"]["P9"], e["radii_au"]["Neptune"]), ("0.9000", "1.6950"))
            self.assertEqual(e["flyby_au"], {"P9": "0.9000", "Neptune": "1.6950"})
            # with the speeds measured in the 4-Gyr run the radii at dt = 0.5 yr stay those of the rule
            self.assertEqual(p9job.encounter_radii(ic, 0.5, [], ["P9=0.50", "Neptune=0.87"])["radii_au"], RULE_05)


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
            res = json.loads((job / "result.json").read_text())
            self.assertEqual(res["encounter_radii_used_au"], {n: float(r) for n, r in RULE_05.items()})
            # new jobs: closest approach within the step, with flyby counts per planet
            self.assertEqual(j["params"]["removal"]["encounter"]["method"], "step")
            self.assertEqual(res["encounter_method"], "step")
            self.assertEqual(set(res["flybys_within_3_radii"]), set(IDS))
            self.assertEqual(set(res["flybys_under_1_5_steps"]), set(IDS))

    @unittest.skipUnless(program("P9TEST_P9SIM"), "P9TEST_P9SIM not set")
    def test_p9sim(self):
        self.run_job(program("P9TEST_P9SIM"), "p9sim")

    @unittest.skipUnless(program("P9TEST_P9GPU"), "P9TEST_P9GPU not set")
    def test_p9gpu(self):
        self.run_job(program("P9TEST_P9GPU"), "p9gpu")


class Mercurius(unittest.TestCase):
    """p9sim with REBOUND's MERCURIUS: the ids leave r while it integrates and come back for the outputs."""

    @unittest.skipUnless(program("P9TEST_P9SIM"), "P9TEST_P9SIM not set")
    def test_ids_survive(self):
        prog = program("P9TEST_P9SIM")
        with tempfile.TemporaryDirectory() as d:
            job = Path(d) / "job"
            subprocess.run([sys.executable, "-I", str(ROOT / "tools/p9job.py"), "make", "--out", str(job), "--t-end", "2000", "--snapshots", "2",
                            "--n-tp", "8", "--p9sim", str(prog), "--integrator", "mercurius", "--no-encounters", "--allow-dirty"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run([sys.executable, "-I", str(ROOT / "tools/p9job.py"), "run", str(job), "--p9sim", str(prog), "--any-version"],
                           check=True, stdout=subprocess.DEVNULL)
            for k in (0, 1):
                out = subprocess.run([str(prog), "dump", str(job / "output.sa"), str(k)], capture_output=True, text=True, check=True).stdout
                ids = [int(float(l.split()[1])) for l in out.splitlines()[1:]]
                self.assertEqual(ids, list(range(6 + 8)))
            self.assertIn("mercurius", (job / "ic.txt").read_text())


if __name__ == "__main__":
    unittest.main()
