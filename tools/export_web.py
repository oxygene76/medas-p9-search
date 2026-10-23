#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Export of a run for the web page "Simulations" (medas-notary-web).

  python tools/export_web.py --p9sim build/gcc-O3/p9sim --run RUN_DIR [--every 1e7] [--a-min 150] \\
      [--until T] --out OUT_DIR

RUN_DIR: a campaign directory (chain*/seg*) or a single job directory. For every
snapshot time that is a multiple of --every (all chains pooled), the surviving
test particles with a barycentric semi-major axis above --a-min (bound orbits)
and Planet Nine are written with their barycentric osculating elements
(ecliptic J2000, mu = G M_total, as tools/analyze.py).

OUT_DIR/data.bin (little endian):
  "P9WEB001" (8 bytes), uint32 n_snapshots, then per snapshot:
    float64 t (years), float64[5] Planet Nine a (au), e, i, Omega, omega (degrees),
    uint32 n, then n records of 12 bytes:
      uint16 index of the test particle in its set (id - 6),
      uint16 a / 0.25 au, uint16 e * 65535, uint16 i * 100 (degrees),
      uint16 Omega * 100, uint16 omega * 100
OUT_DIR/manifest.json: the run (parameters, code, segment results with their
hashes), the format, the sha256 and size of data.bin. Values are quantised
for drawing; the run's archives remain the reference.
"""

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import barycentric, dump  # noqa: E402

MAGIC = b"P9WEB001"


def elements_full(mu, r, v):
    """a, e, i, Omega, omega (degrees) for arrays of positions and velocities."""
    rr = np.linalg.norm(r, axis=-1)
    vv2 = (v * v).sum(-1)
    h = np.cross(r, v)
    hn = np.linalg.norm(h, axis=-1)
    a = 1 / (2 / rr - vv2 / mu)
    evec = np.cross(v, h) / mu - r / rr[:, None]
    e = np.linalg.norm(evec, axis=-1)
    inc = np.degrees(np.arccos(np.clip(h[:, 2] / hn, -1, 1)))
    n = np.stack([-h[:, 1], h[:, 0], np.zeros(len(h))], axis=-1)
    nn = np.linalg.norm(n, axis=-1)
    Om = np.degrees(np.arctan2(n[:, 1], n[:, 0])) % 360
    cosw = np.clip((n * evec).sum(-1) / (nn * e), -1, 1)
    w = np.degrees(np.arccos(cosw))
    w = np.where(evec[:, 2] < 0, 360 - w, w) % 360
    return a, e, inc, Om, w


def snapshots(run: Path, every: float, until: float | None):
    """[(t, [(archive, index)])] for the snapshot times that are multiples of every, in all chains."""
    chains = sorted(run.glob("chain*")) or [run]
    per_chain = []
    for c in chains:
        segs = sorted(c.glob("seg*")) if (c / "job.json").exists() is False else [c]
        times = {}
        for s in segs:
            if not (s / "result.json").exists():
                continue  # only finished segments
            p = json.loads((s / "job.json").read_text())["params"]
            t0, t1, n = float(p["t_start_yr"]), float(p["t_end_yr"]), int(p["snapshots"])
            for k in range(n):
                t = t0 + (t1 - t0) * (k + 1) / n
                times[round(t)] = (s / "output.sa", k)
        per_chain.append(times)
    common = sorted(set.intersection(*(set(x) for x in per_chain)))
    out = [t for t in common if abs(t / every - round(t / every)) < 1e-9 and (until is None or t <= until)]
    return [(t, [pc[t] for pc in per_chain]) for t in out]


def segment_results(run: Path):
    res = []
    for s in sorted(run.glob("chain*/seg*")) or sorted(run.glob("seg*")) or [run]:
        if (s / "result.json").exists():
            j = json.loads((s / "job.json").read_text())
            r = json.loads((s / "result.json").read_text())
            res.append({"segment": str(s.relative_to(run)), "job_id": j["id"], "t_start_yr": j["params"]["t_start_yr"],
                        "t_end_yr": j["params"]["t_end_yr"], "result_sha256": r["result_sha256"], "particles_end": r["particles_end"],
                        "removed": r["removed"], "removed_encounter": r.get("removed_encounter", 0), "wall_s": r["wall_s"],
                        "program": r.get("program")})
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p9sim", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--every", type=float, default=1e7)
    ap.add_argument("--a-min", type=float, default=150.0)
    ap.add_argument("--until", type=float, default=None)
    ap.add_argument("--name", default=None, help="title of the run on the page")
    ap.add_argument("--member", type=int, default=None,
                    help="ensemble member to export (tools/make_ic.py --members): only its test particles, with their index in "
                         "the set (name tp<member * 100000 + index>); default: all, as named")
    a = ap.parse_args()
    run, out = Path(a.run), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    snaps = snapshots(run, a.every, a.until)
    if not snaps:
        sys.exit("no common snapshots")
    body = bytearray()
    body += MAGIC + struct.pack("<I", len(snaps))
    counts = []
    for t, refs in snaps:
        rows = []
        for sa, k in refs:
            _, rr = dump(a.p9sim, sa, k)
            rows += rr
        # Planet Nine and the massive bodies appear in every chain alike: keep one of each
        seen, uniq = set(), []
        for x in rows:
            if x[0] in seen and not x[0].startswith("tp"):
                continue
            seen.add(x[0])
            uniq.append(x)
        rows, mu = barycentric(uniq)
        p9 = [x for x in rows if x[0] == "P9"][0]
        tps = [x for x in rows if x[0].startswith("tp")]
        if a.member is not None:
            tps = [x for x in tps if int(x[0][2:]) // 100000 == a.member]
        pa = elements_full(mu, p9[2][None, :], p9[3][None, :])
        idx = np.array([int(x[0][2:]) % 100000 if a.member is not None else int(x[0][2:]) for x in tps], dtype=np.int64)
        if len(idx) and idx.max() > 65535:
            sys.exit("more than 65536 test particles: the format has 16-bit indices")
        A, E, I, Om, W = elements_full(mu, np.array([x[2] for x in tps]), np.array([x[3] for x in tps]))
        keep = (E < 1) & (A > a.a_min)
        body += struct.pack("<d5d", t, *(float(v[0]) for v in pa))
        body += struct.pack("<I", int(keep.sum()))
        rec = np.zeros(int(keep.sum()), dtype=[("k", "<u2"), ("a", "<u2"), ("e", "<u2"), ("i", "<u2"), ("Om", "<u2"), ("w", "<u2")])
        rec["k"] = idx[keep]
        rec["a"] = np.clip(np.round(A[keep] / 0.25), 0, 65535)
        rec["e"] = np.clip(np.round(E[keep] * 65535), 0, 65535)
        rec["i"] = np.clip(np.round(I[keep] * 100), 0, 18000)
        rec["Om"] = np.round(Om[keep] * 100) % 36000
        rec["w"] = np.round(W[keep] * 100) % 36000
        body += rec.tobytes()
        counts.append(int(keep.sum()))
        print(f"t = {t / 1e6:7.1f} Myr: {int(keep.sum())} distant test particles", file=sys.stderr)
    (out / "data.bin").write_bytes(bytes(body))
    first = sorted(run.glob("chain*/seg000/job.json")) or sorted(run.glob("seg*/job.json"))[:1] or [run / "job.json"]
    j0 = json.loads(first[0].read_text())
    manifest = {
        "schema": "medas-p9-search/web/1",
        "title": a.name or run.name,
        "status": "Pilot, not peer-reviewed",
        "run": {"directory": run.name, "chains": len(sorted(run.glob("chain*"))) or 1, "case": j0["params"]["case"],
                "params": {k: j0["params"][k] for k in ("integrator", "coordinates", "dt_yr", "removal") if k in j0["params"]},
                "test_particles": j0["params"]["ic"]["n_tp"],
                **({"member": a.member} if a.member is not None else {}),
                "ic": j0["params"]["ic"], "code": j0["code"], "segments": segment_results(run)},
        "export": {"tool": "tools/export_web.py", "every_yr": a.every, "a_min_au": a.a_min, "elements": "barycentric osculating, ecliptic J2000",
                   "snapshots": len(snaps), "t_first_yr": snaps[0][0], "t_last_yr": snaps[-1][0], "counts": counts},
        "format": {"file": "data.bin", "description": __doc__.split("OUT_DIR/data.bin (little endian):")[1].split("OUT_DIR/manifest.json")[0].strip(),
                   "sha256": hashlib.sha256(bytes(body)).hexdigest(), "bytes": len(body)},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    if len(body) > 10_000_000:
        print(f"warning: {len(body):,} bytes, above the 10 MB target; use a larger --every", file=sys.stderr)
    print(f"export: {len(snaps)} snapshots, {len(body):,} bytes, sha256 {manifest['format']['sha256'][:16]}… -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
