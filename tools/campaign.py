#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""A long run as chains of work packages, in parallel, with a deadline.

The test particles are split into --chains slices; each slice is an
independent chain of jobs (the massive bodies are in every job and evolve
identically, test particles are massless). Every chain runs segments of
--segment years one after the other (each segment a job whose input is the
last snapshot of the previous one; p9job.py next), with a snapshot every
--snap-every years in its SimulationArchive. A segment is only started if it
should end before --deadline (estimated from the chain's last segment);
whatever runs at the deadline + --grace is stopped (its snapshots so far stay).

  python tools/campaign.py --root runs/long --chains 16 --n-tp 4000 \
      --segment 2e7 --snap-every 1e6 --deadline 2026-10-19T06:55
"""

import argparse
import json
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
JOB = [PY, "-I", str(ROOT / "tools/p9job.py")]
lock = threading.Lock()


def log(root, msg):
    line = f"{datetime.now().isoformat(timespec='seconds')} {msg}"
    with lock:
        print(line, flush=True)
        with open(root / "campaign.log", "a") as f:
            f.write(line + "\n")


def chain(root, c, a, deadline, procs):
    per = a.n_tp // a.chains
    lo, hi = c * per, (c + 1) * per
    seg_wall = None
    k = 0
    t = 0.0
    while True:
        d = root / f"chain{c:02d}" / f"seg{k:03d}"
        t_end = t + a.segment
        snaps = int(round(a.segment / a.snap_every))
        if seg_wall is not None and time.time() + seg_wall * 1.1 > deadline:
            log(root, f"chain{c:02d} stops before seg{k:03d}: would end after the deadline")
            return
        if not (d / "job.json").exists():
            if k == 0:
                cmd = JOB + ["make", "--out", str(d), "--t-end", repr(t_end), "--snapshots", str(snaps), "--n-tp", str(a.n_tp),
                             "--tp-from", str(lo), "--tp-to", str(hi), "--seed", str(a.seed)]
            else:
                cmd = JOB + ["next", "--prev", str(root / f"chain{c:02d}" / f"seg{k - 1:03d}"), "--out", str(d), "--t-end", repr(t_end),
                             "--snapshots", str(snaps)]
            subprocess.run(cmd, check=True, capture_output=True)
        w0 = time.time()
        p = subprocess.Popen(["nice", "-n", "10"] + JOB + ["run", str(d)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        with lock:
            procs[c] = p
        out, err = p.communicate()
        with lock:
            procs[c] = None
        if p.returncode != 0:
            log(root, f"chain{c:02d} seg{k:03d} stopped (code {p.returncode}) {err.strip()[-300:]}")
            return
        seg_wall = time.time() - w0
        r = json.loads((d / "result.json").read_text())
        log(root, f"chain{c:02d} seg{k:03d} t={t_end:.4g} wall={seg_wall:.0f}s Myr/h={a.segment / 1e6 / (seg_wall / 3600):.1f} "
                  f"N={r['particles_end']} removed={r['removed']} result={r['result_sha256'][:16]}")
        t = t_end
        k += 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--chains", type=int, default=16)
    ap.add_argument("--n-tp", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=9)
    ap.add_argument("--segment", type=float, default=2e7)
    ap.add_argument("--snap-every", type=float, default=1e6)
    ap.add_argument("--deadline", required=True, help="local time, e.g. 2026-10-19T06:55")
    ap.add_argument("--grace", type=float, default=180, help="seconds after the deadline before running segments are stopped")
    a = ap.parse_args()
    root = Path(a.root)
    root.mkdir(parents=True, exist_ok=True)
    deadline = datetime.fromisoformat(a.deadline).timestamp()
    log(root, f"campaign start: {a.chains} chains x {a.n_tp // a.chains} test particles, segments {a.segment:g} yr, deadline {a.deadline}")
    procs = {}
    threads = [threading.Thread(target=chain, args=(root, c, a, deadline, procs), daemon=True) for c in range(a.chains)]
    for th in threads:
        th.start()
    while any(th.is_alive() for th in threads):
        time.sleep(10)
        if time.time() > deadline + a.grace:
            with lock:
                running = [(c, p) for c, p in procs.items() if p]
            for c, p in running:
                p.terminate()
            if running:
                log(root, f"deadline: stopped {len(running)} running segments (their snapshots so far are kept)")
            break
    for th in threads:
        th.join(timeout=60)
    log(root, "campaign end")


if __name__ == "__main__":
    main()
