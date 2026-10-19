#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The test particles lost only in p9gpu (not in MERCURIUS): were their losses numerical?

  python tools/flyby_losses.py --p9sim build/gcc-O3/p9sim --p9gpu build/gpu-cpu/p9gpu \\
      --merc runs/val/merc/part* --gpu runs/val/gpu-2000-count --time 5e7 --out runs/val/flyby-losses [--workers 6]

(a) Flybys closer than 0.1 au (counted by the run, flybys.tsv) among the
    particles lost only in p9gpu, against a control group of particles at risk
    that were not lost: alive at the time in both runs, with at least one
    flyby within three radii of a planet. Share with at least one such flyby,
    and their rate per Myr of the particle's life in the run (lost particles
    live shorter); Fisher's exact test of the shares.
(b) For each particle lost only in p9gpu, its last flyby shorter than 1.5
    steps before the loss (flybys.tsv: step, planet), rebuilt bit-identically:
    a start file with the Sun, the planets and only that particle (test
    particles are massless and independent; the start values are the exact
    decimals of the run's input) run with p9gpu's CPU twin to M steps before
    and M steps after the flyby (both from the start, so both states are those
    of the original run). From the state before, REBOUND's IAS15 integrates
    the whole system over the same 2M steps. Kick = change of the particle's
    heliocentric orbital energy over the window; ratio = p9gpu / IAS15. The
    loss counts as numerical if |ratio - 1| > 0.5 and the particle was removed
    within one orbital period after the flyby (period of p9gpu's orbit after
    the flyby; an unbound orbit counts as within one period).
    Window: M = 240 steps (120 yr) for Jupiter to Neptune, 1,200 steps (600
    yr) for Planet Nine.
"""

import argparse
import csv
import json
import math
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pair_losses import survivors  # noqa: E402

PLANET_NAMES = {1: "Jupiter", 2: "Saturn", 3: "Uranus", 4: "Neptune", 5: "P9"}


def read_flybys(d):
    rows = {}
    for r in csv.DictReader(open(Path(d) / "flybys.tsv"), delimiter="\t"):
        i = int(r["id"])
        rows[i] = {"removed_step": int(r["removed_step"]), "last_fast_step": int(r["last_fast_step"]),
                   "last_fast_planet": int(float(r["last_fast_planet"])), "last_fast_dmin": float(r["last_fast_dmin_au"]),
                   "near": sum(int(v) for k, v in r.items() if k.startswith("near_")),
                   "fast": sum(int(v) for k, v in r.items() if k.startswith("fast_")),
                   "close": sum(int(v) for k, v in r.items() if k.startswith("close_"))}
    return rows


def fisher_two_sided(a, b, c, d):
    """Fisher's exact test for [[a, b], [c, d]] (two-sided, sum of tables no more probable)."""
    n1, n2, k = a + b, c + d, a + c
    def p(x):
        return math.comb(n1, x) * math.comb(n2, k - x) / math.comb(n1 + n2, k)
    p0 = p(a)
    return min(1.0, sum(p(x) for x in range(max(0, k - n2), min(k, n1) + 1) if p(x) <= p0 * (1 + 1e-9)))


def header_and_rows(p9sim, sa):
    out = subprocess.run([p9sim, "dump", str(sa), "0"], capture_output=True, text=True, check=True).stdout.splitlines()
    return out[0], [l.split() for l in out[1:]]


def rebuild(args):
    """State of particle pid at the steps s0 and s1 of the original run (CPU twin, bit-identical)."""
    pid, s0, s1, ctx = args
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        ic = d / "ic.txt"
        with open(ic, "w") as f:
            f.write(ctx["header"])
            for r in ctx["massive"] + [ctx["tp"][pid]]:
                f.write(r + "\n")
        subprocess.run([ctx["p9sim"], "init", str(ic), str(d / "in.sa")], check=True, stdout=subprocess.DEVNULL)
        env = dict(os.environ, P9GPU_MODE="cpu")
        for k in ("P9_ENCOUNTER_RADII", "P9_ENCOUNTER_METHOD", "P9_ENCOUNTER_REMOVE", "P9_FLYBY_OUT", "P9_J2", "P9GPU_REAL"):
            env.pop(k, None)
        states = []
        for s in (s0, s1):
            out = d / f"o{s}.sa"
            p = subprocess.run([ctx["p9gpu"], "run", str(d / "in.sa"), repr(s * ctx["dt"]), "1", str(out)], env=env, capture_output=True, text=True)
            if p.returncode:
                return pid, None, p.stderr[-300:]
            kv = dict(x.split("=", 1) for x in [l for l in p.stdout.splitlines() if l.startswith("result_sha256=")][-1].split())
            if int(kv["steps"]) != s:
                return pid, None, f"{kv['steps']} steps instead of {s}"
            rows = [l.split() for l in subprocess.run([ctx["p9sim"], "dump", str(out), "0"], capture_output=True, text=True,
                                                      check=True).stdout.splitlines()[1:]]
            states.append(rows)
        return pid, states, None


def energy(rows, G, pid_index):
    sun = np.array([float(x) for x in rows[0][3:9]])
    tp = np.array([float(x) for x in rows[pid_index][3:9]]) - sun
    msun = float(rows[0][2])
    r, v = tp[:3], tp[3:]
    E = 0.5 * v @ v - G * msun / np.linalg.norm(r)
    return E, G * msun


def ias15_energy(rows, G, t_span):
    import rebound
    sim = rebound.Simulation()
    sim.G = G
    for r in rows:
        m, x, y, z, vx, vy, vz = map(float, r[2:9])
        sim.add(m=m, x=x, y=y, z=z, vx=vx, vy=vy, vz=vz)
    sim.N_active = len(rows) - 1
    sim.testparticle_type = 0
    sim.integrator = "ias15"
    sim.dt = 0.01
    sim.integrate(t_span)
    s, q = sim.particles[0], sim.particles[sim.N - 1]
    rv = np.array([q.x - s.x, q.y - s.y, q.z - s.z])
    vv = np.array([q.vx - s.vx, q.vy - s.vy, q.vz - s.vz])
    return 0.5 * vv @ vv - G * s.m / np.linalg.norm(rv)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--p9gpu", required=True)
    ap.add_argument("--merc", nargs="+", required=True)
    ap.add_argument("--gpu", required=True, help="the p9gpu run with counting (flybys.tsv), one job from t = 0")
    ap.add_argument("--time", type=float, required=True)
    ap.add_argument("--n0", type=int, default=2000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    job = json.loads((Path(a.gpu) / "job.json").read_text())
    dt = float(job["params"]["dt_yr"])
    ids = set(range(6, 6 + a.n0))
    sm, sg = survivors(a.merc, a.p9sim, a.time), survivors([a.gpu], a.p9sim, a.time)
    lm, lg = ids - sm, ids - sg
    only_g = sorted(lg - lm)
    fb = read_flybys(a.gpu)
    T_steps = int(round(a.time / dt))
    report = {"time_yr": a.time, "lost_only_p9gpu": len(only_g), "lost_only_mercurius": len(lm - lg), "lost_both": len(lm & lg)}

    # (a) close flybys: lost only in p9gpu against particles at risk alive in both
    control = [i for i in sorted(sm & sg) if fb[i]["near"] > 0]
    def stats(group):
        life = [((fb[i]["removed_step"] or T_steps) * dt / 1e6) for i in group]
        with_close = sum(1 for i in group if fb[i]["close"] > 0)
        n_close = sum(fb[i]["close"] for i in group)
        return with_close, len(group), n_close, sum(life)
    wl, nl, cl, yl = stats(only_g)
    wc, nc, cc, yc = stats(control)
    p_f = fisher_two_sided(wl, nl - wl, wc, nc - wc)
    report["a"] = {"lost_only_p9gpu": {"with_close_flyby": wl, "n": nl, "close_flybys": cl, "life_myr": round(yl, 1)},
                   "control_at_risk_alive_in_both": {"with_close_flyby": wc, "n": nc, "close_flybys": cc, "life_myr": round(yc, 1)},
                   "fisher_p": p_f}
    print(f"(a) flybys closer than 0.1 au (t = {a.time / 1e6:g} Myr)")
    print(f"    lost only in p9gpu: {wl} of {nl} with at least one ({100 * wl / max(nl, 1):.1f} %), {cl} in {yl:.0f} particle-Myr "
          f"= {cl / max(yl, 1e-9):.4f} per Myr")
    print(f"    control (alive in both, at least one flyby within three radii): {wc} of {nc} ({100 * wc / max(nc, 1):.1f} %), "
          f"{cc} in {yc:.0f} particle-Myr = {cc / max(yc, 1e-9):.4f} per Myr")
    print(f"    Fisher exact (shares): p = {p_f:.3g}")

    # (b) rebuild the last too short flyby of each and compare with IAS15
    header, rows = header_and_rows(a.p9sim, Path(a.gpu) / "input.sa")
    ic_head = "".join(l + "\n" for l in (Path(a.gpu) / "ic.txt").read_text().splitlines() if l and l.split()[0] in ("G", "dt", "N_active", "corrector"))
    G = float([l for l in ic_head.splitlines() if l.startswith("G ")][0].split()[1])
    def line(r):
        return "p " + r[0] + " " + " ".join(r[2:9]) + " " + r[1]
    massive = [line(r) for r in rows if not r[0].startswith("tp")]
    tp = {int(r[1]): line(r) for r in rows if r[0].startswith("tp")}
    ctx = {"header": ic_head, "massive": massive, "tp": tp, "p9sim": a.p9sim, "p9gpu": a.p9gpu, "dt": dt}
    tasks = []
    for i in only_g:
        S = fb[i]["last_fast_step"]
        if not S:
            continue
        M = 1200 if fb[i]["last_fast_planet"] == 5 else 240
        tasks.append((i, max(S - M, 1), S + M, ctx))
    print(f"(b) rebuilding {len(tasks)} flybys ({len(only_g) - len(tasks)} of the {len(only_g)} had no flyby shorter than 1.5 steps)",
          file=sys.stderr)
    results = []
    with ProcessPoolExecutor(a.workers) as ex:
        for pid, states, err in ex.map(rebuild, tasks):
            S = fb[pid]["last_fast_step"]
            R = fb[pid]["removed_step"]
            if states is None:
                results.append({"id": pid, "error": err})
                continue
            before, after = states
            k = len(before) - 1  # the particle is the last body
            E0, mu = energy(before, G, k)
            E1, _ = energy(after, G, k)
            t0 = (max(S - (1200 if fb[pid]["last_fast_planet"] == 5 else 240), 1)) * dt
            t1 = (S + (1200 if fb[pid]["last_fast_planet"] == 5 else 240)) * dt
            Ei = ias15_energy(before, G, t1 - t0)
            ratio = (E1 - E0) / (Ei - E0) if Ei != E0 else float("inf")
            a_after = -mu / (2 * E1) if E1 < 0 else float("inf")
            period = a_after ** 1.5 if math.isfinite(a_after) else 0.0
            since = (R - S) * dt
            numerical = abs(ratio - 1) > 0.5 and (not math.isfinite(a_after) or since <= period)
            results.append({"id": pid, "planet": PLANET_NAMES.get(fb[pid]["last_fast_planet"], "?"), "dmin_au": fb[pid]["last_fast_dmin"],
                            "flyby_myr": S * dt / 1e6, "removed_myr": R * dt / 1e6, "since_flyby_yr": since, "kick_ratio": ratio,
                            "E_before": E0, "E_after_p9gpu": E1, "E_after_ias15": Ei, "a_after_p9gpu": a_after, "period_after_yr": period,
                            "numerical": bool(numerical)})
    n_num = sum(1 for r in results if r.get("numerical"))
    report["b"] = {"rebuilt": len([r for r in results if "error" not in r]), "numerical": n_num, "of": len(only_g), "rows": results}
    print(f"(b) losses counted as numerical: {n_num} of {len(only_g)} (kick off by more than half and lost within one orbit after it)")
    print("    id   planet   d_min[au]  flyby[Myr] lost[Myr]  since[yr]  kick ratio  a_after[au]  numerical")
    for r in sorted(results, key=lambda x: x["id"]):
        if "error" in r:
            print(f"    {r['id']:5d}  error: {r['error']}")
            continue
        print(f"    {r['id']:5d}  {r['planet']:7s}  {r['dmin_au']:8.4f}  {r['flyby_myr']:9.3f}  {r['removed_myr']:8.3f}  {r['since_flyby_yr']:9.0f}  "
              f"{r['kick_ratio']:10.3g}  {r['a_after_p9gpu']:11.4g}  {'yes' if r['numerical'] else 'no'}")
    (out / "flyby-losses.json").write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
