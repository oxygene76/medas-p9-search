#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Report after a segment of a campaign (every 500 Myr in the 4-Gyr run).

  python tools/segment_report.py --p9sim build/gcc-O3/p9sim CAMPAIGN_ROOT [--segment N]

For the segment (default: the last finished one, chain00):
- removals by planet (close encounters) and by the distance rules; the share
  removed at Planet Nine, of the test particles at the start of the segment
  and of all removals, and since the start of the run (if it grows, check
  whether removing them strengthens the clustering artificially);
- v99 of the encounter speeds at Planet Nine and Neptune at the segment's end
  (tools/encounter_speeds.py), against the limits 0.65 and 1.0 au/yr;
- the clustering line of analysis.log at the segment's end.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIMITS = {"P9": 0.65, "Neptune": 1.0}


def finished(d):
    try:
        return json.loads((d / "result.json").read_text())["job_id"] == json.loads((d / "job.json").read_text())["id"]
    except (OSError, ValueError, KeyError):
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root")
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--segment", type=int, default=None)
    a = ap.parse_args()
    ch = Path(a.root) / "chain00"
    segs = [d for d in sorted(ch.glob("seg[0-9][0-9][0-9]")) if finished(d)]
    if not segs:
        sys.exit("no finished segment")
    seg = segs[-1] if a.segment is None else ch / f"seg{a.segment:03d}"
    r = json.loads((seg / "result.json").read_text())
    job = json.loads((seg / "job.json").read_text())
    p = job["params"]
    n_massive = len(p["removal"]["encounter"].get("body_ids", {})) + 1
    start = r["particles_start"] - n_massive
    by = r.get("removed_by_encounter") or {}
    print(f"== {seg.name}: {p['t_start_yr'] / 1e6:g} - {p['t_end_yr'] / 1e6:g} Myr (result {r['result_sha256'][:16]}, wall {r['wall_s'] / 3600:.1f} h)")
    print(f"test particles: {start} at the start, {r['particles_end'] - n_massive} at the end, removed {r['removed']}")
    if by:
        print("removed by close encounter: " + ", ".join(f"{k} {v}" for k, v in by.items() if v) +
              f"; distance rules {r['removed'] - r['removed_encounter']}")
    else:
        print(f"removed by close encounter: {r['removed_encounter']} (this program version reports no breakdown by planet)")
    n9 = by.get("P9")
    if n9 is not None:
        print(f"removed at Planet Nine: {n9} = {100 * n9 / max(start, 1):.2f} % of the test particles at the start of the segment, "
              f"{100 * n9 / max(r['removed'], 1):.1f} % of the removals")
    tot9 = tot = 0
    first = None
    for d in segs:
        rr = json.loads((d / "result.json").read_text())
        if first is None:
            first = rr["particles_start"] - n_massive
        tot9 += (rr.get("removed_by_encounter") or {}).get("P9", 0)
        tot += rr["removed"]
        if d == seg:
            break
    print(f"since the start: removed {tot} of {first}, at Planet Nine {tot9} ({100 * tot9 / max(first, 1):.2f} % of the start)")
    T = repr(float(p["t_end_yr"]))
    for planet in ("P9", "Neptune"):
        out = subprocess.run([sys.executable, "-I", str(ROOT / "tools/encounter_speeds.py"), "--p9sim", a.p9sim, "--planet", planet,
                              "--dmax", "2", str(seg), "--times", T], capture_output=True, text=True)
        line = [l for l in out.stdout.splitlines() if "Myr" in l and "|" in l]
        if not line:
            print(f"v99 at {planet}: not available ({out.stderr.strip()[-200:]})")
            continue
        f = line[-1].split("|")
        v99_moid, v99_opik = float(f[1].split()[2]), float(f[2].split()[2])
        n_close = int(f[0].split()[3])
        if n_close == 0:
            print(f"v99 at {planet}: no orbit within 2 au of its orbit")
            continue
        flag = "ABOVE THE LIMIT, report" if max(v99_moid, v99_opik) > LIMITS[planet] else "below the limit"
        print(f"v99 at {planet}: {v99_moid:.3f} (MOID) / {v99_opik:.3f} (Opik) au/yr from {n_close} orbits; limit {LIMITS[planet]}: {flag}")
    log = Path(a.root) / "analysis.log"
    if log.exists():
        lines, block = log.read_text().splitlines(), []
        for i, l in enumerate(lines):
            if l.startswith("==") and f"t = {p['t_end_yr'] / 1e6:g} Myr" in l:
                block = [l]
                for m in lines[i + 1:]:
                    if m.startswith("=="):
                        break
                    block.append(m)
        print("clustering (analysis.log):\n" + ("\n".join(block) if block else "  no entry for this time"))


if __name__ == "__main__":
    main()
