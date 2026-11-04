#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Export of a run for the time-lapse and the comparison of runs on the page "Simulations" (medas-notary-web):
a fixed subset of the test particles for drawing, and per snapshot the sums from which the page draws the curves of
the direction of dvarpi and of R, computed from all test particles with the definitions of tools/prod_eval.py.

  python3 -I tools/export_timelapse.py --p9sim PATH --id ID --title TITLE --group GROUP --out DIR
      [--show 2000] [--every 1e7] [--n-tp N] [--status TEXT] [--note TEXT] [--evaluation result.json]
      [--notary FILE] PART [PART ...]

PART: what together makes one run. A package job (params.env, input.sa, segments/segNNN/output.sa with DONE,
segments.tsv) or a directory of snapshot files snap-*.npz (the synthetic tests). A V5 run is one job; a MERCURIUS
run of the paired long runs is its slices (jobs M-s110-part00 ... ), whose test-particle ids are global.

Elements (as tools/prod_eval.py, frame_elements): barycentric osculating elements in the frame of Jupiter's orbital
plane at each snapshot, longitudes as dog-leg longitudes from the equinox of the ecliptic J2000. dvarpi and dOmega of
every test particle are taken against the Planet Nine of its own part. Snapshots: t = 0 (the input of the run) and
every time that is a multiple of --every and present in every part; a time missing in a part ends the export there.

Per snapshot and selection (S_BB of the evaluation and S1-S3 of tools/prod_eval.py) the number n, the sums C and S of
cos and sin of dvarpi and the number within 45 deg of 180 deg. The page gets from them, exactly as prod_eval does,
the direction atan2(S, C) and R = hypot(C, S) / n per snapshot, and over the window (default 1-4 Gyr) M1 =
atan2(sum S, sum C) and M2 = the mean of R over the snapshots of the window.

DIR/data.bin   P9WEB001 (format in tools/export_web.py of medas-p9-search-bb2021 and src/lib/simdata.ts of
               medas-notary-web): per snapshot Planet Nine (of the first part) and the test particles of the subset
               (id % stride == 0, stride = ceil(n_tp / show)) that are alive, bound and below 16,000 au, with a, e,
               i, Omega and omega quantised; Omega and varpi are written as Planet Nine's (first part) plus dOmega
               and dvarpi, so the page's colours are the evaluation's dvarpi.
DIR/curves.json  the sums per snapshot and selection.
DIR/SOURCES.sha256  sha256sum lines of every file read (paths relative to the common parent of the parts).
DIR/manifest.json   run, parts and segments with their result hashes, the sha256 of SOURCES.sha256 (the hash of the
               source data), the exporter's commit, p9sim's sha256, the files with sha256 and size.

Runs of the evaluated campaigns (groups production, long-110-112, set-A, set-B) are exported only with --evaluation,
the result.json of tools/prod_eval.py over the complete run; its sha256 and verdict go into the manifest. So no
result of these runs reaches the page before its evaluation (decision of 2026-11-04).
"""

import argparse
import hashlib
import json
import math
import os
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prod_eval as pe  # noqa: E402

MAGIC = b"P9WEB001"
SCHEMA = "medas-p9-search/timelapse/1"
SELECTIONS = {"SBB": pe.S_BB, **pe.SELECTIONS}
LABELS = {"SBB": "150 < a < 1000 au, q > 42 au (S_BB, the evaluation)", "S1": "a > 250 au", "S2": "a > 250 au, q > 30 au",
          "S3": "a > 230 au, q > 30 au (Brown & Batygin 2019)"}
ANTI_HALF_WIDTH = 45.0
A_MAX_DRAW = 16000.0          # a / 0.25 au must fit into uint16
EVALUATED_GROUPS = ("production", "long-110-112", "set-A", "set-B")
GROUPS = EVALUATED_GROUPS + ("equivalence", "validation", "test")


# --- reading ---------------------------------------------------------------------------------------------------------

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_env(p):
    return dict(l.split("=", 1) for l in Path(p).read_text().splitlines() if "=" in l and not l.startswith("#"))


class Part:
    """One part of a run: its snapshots (time -> loader) and the files read."""

    def __init__(self, path, p9sim):
        self.path = Path(path)
        self.files = []                   # files whose content enters the export
        self.segments = []
        self.job = None
        npz = sorted(self.path.glob("snap-*.npz"))
        if npz:
            self.kind = "npz"
            self.snaps = {}
            for p in npz:
                t = float(np.load(p, allow_pickle=False)["t"])
                self.snaps[t] = (lambda p=p: self._npz(p))
                self.files.append(p)
            self.planned = max(self.snaps)
            return
        self.kind = "job"
        if not p9sim:
            sys.exit("--p9sim is needed to read output.sa")
        env = read_env(self.path / "params.env")
        seg_yr, per, nseg = float(env["SEGMENT_YR"]), int(env["SNAPSHOTS_PER_SEGMENT"]), int(env["SEGMENTS"])
        self.planned = seg_yr * nseg
        self.job = json.loads((self.path / "job.json").read_text())
        self.files += [self.path / "job.json", self.path / "params.env", self.path / "input.sa"]
        self.snaps = {0.0: (lambda: pe.dump(p9sim, self.path / "input.sa", 0))}
        rows = {}
        if (self.path / "segments.tsv").exists():
            self.files.append(self.path / "segments.tsv")
            for line in (self.path / "segments.tsv").read_text().splitlines():
                f = line.split("\t")
                if len(f) >= 5 and f[0].isdigit():
                    rows[int(f[0])] = f
        for k in range(nseg):
            seg = self.path / "segments" / f"seg{k:03d}"
            if not (seg / "DONE").exists():
                break
            out = seg / "output.sa"
            self.files.append(out)
            row = rows.get(k)
            self.segments.append({"segment": f"seg{k:03d}", "t_end_yr": (k + 1) * seg_yr,
                                  "particles_end": int(row[2]) if row else None, "result_sha256": row[4] if row else None,
                                  "output_sha256": None})
            for i in range(per):
                t = k * seg_yr + (i + 1) * seg_yr / per
                self.snaps[t] = (lambda sa=out, i=i: pe.dump(p9sim, sa, i))

    @staticmethod
    def _npz(p):
        z = np.load(p, allow_pickle=False)
        return float(z["t"]), z["names"], z["m"], z["r"], z["v"]


def common_times(parts, every):
    """t = 0 and the multiples of every present in all parts, up to the first one missing in a part."""
    def on_grid(t):
        return t == 0.0 or abs(t / every - round(t / every)) < 1e-9 * max(1.0, t / every)
    grid = sorted({t for p in parts for t in p.snaps if on_grid(t)})
    out = []
    for t in grid:
        if not all(any(abs(t - u) <= 1e-6 * max(1.0, t) for u in p.snaps) for p in parts):
            if t == 0.0:
                continue          # npz runs need not start at 0
            break
        out.append(t)
    return out


def loader(part, t):
    for u, f in part.snaps.items():
        if abs(t - u) <= 1e-6 * max(1.0, t):
            return f
    raise KeyError(t)


# --- one snapshot ----------------------------------------------------------------------------------------------------

def snapshot(parts, t, stride):
    """Curves (per selection n, C, S, anti) over all parts; drawn particles of the subset; Planet Nine of part 0."""
    sums = {k: [0, 0.0, 0.0, 0] for k in SELECTIONS}
    draw, p9_0, n_alive = [], None, 0
    for j, part in enumerate(parts):
        el = pe.frame_elements(*loader(part, t)())
        n_alive += len(el["idx"])
        if j == 0:
            p9_0 = el["p9"]
        dv = el["dvarpi"]
        for k, cut in SELECTIONS.items():
            s = pe.select(el, cut)
            x = np.radians(dv[s])
            sums[k][0] += int(s.sum())
            sums[k][1] += float(np.cos(x).sum())
            sums[k][2] += float(np.sin(x).sum())
            sums[k][3] += int((np.abs(dv[s] % 360.0 - 180.0) <= ANTI_HALF_WIDTH).sum())   # dvarpi within 45 deg of 180
        a, q = el["a"], el["q"]
        e = 1 - q / a
        keep = (el["idx"] % stride == 0) & (a > 0) & (a < A_MAX_DRAW) & (e >= 0) & (e < 1)
        Om = (el["dOmega"][keep] + p9_0["Omega"]) % 360
        vp = (el["dvarpi"][keep] + p9_0["varpi"]) % 360
        draw.append((el["idx"][keep], a[keep], e[keep], el["inc"][keep], Om, (vp - Om) % 360))
    cat = [np.concatenate([d[c] for d in draw]) for c in range(6)]
    order = np.argsort(cat[0], kind="stable")
    return n_alive, sums, p9_0, [c[order] for c in cat]


def pack(t, p9, d):
    idx, a, e, inc, Om, om = d
    if len(idx) and idx.max() > 65535:
        sys.exit("test-particle index above 65535: does not fit P9WEB001")
    om9 = (p9["varpi"] - p9["Omega"]) % 360
    body = struct.pack("<d5d", t, p9["a"], p9["e"], p9["inc"], p9["Omega"], om9) + struct.pack("<I", len(idx))
    rec = np.zeros(len(idx), dtype=[("i", "<u2"), ("a", "<u2"), ("e", "<u2"), ("inc", "<u2"), ("Om", "<u2"), ("om", "<u2")])
    rec["i"] = idx
    rec["a"] = np.clip(np.round(a / 0.25), 0, 65535)
    rec["e"] = np.clip(np.round(e * 65535), 0, 65535)
    rec["inc"] = np.clip(np.round(inc * 100), 0, 18000)
    rec["Om"] = np.round(Om * 100) % 36000
    rec["om"] = np.round(om * 100) % 36000
    return body + rec.tobytes()


# --- the export ------------------------------------------------------------------------------------------------------

def git_commit():
    root = Path(__file__).resolve().parents[1]
    p = subprocess.run(["git", "-C", str(root), "describe", "--tags", "--match", "export-timelapse-*", "--dirty", "--always"],
                       capture_output=True, text=True)
    return p.stdout.strip() or "unknown"


def p9sim_info(p9sim):
    if not p9sim:
        return None
    v = subprocess.run([p9sim, "version"], capture_output=True, text=True).stdout.strip()
    return {"version": v, "sha256": sha256_file(p9sim)}


def describe(parts):
    j = parts[0].job
    if not j:
        return {"case": "synthetic snapshots (snap-*.npz)"}
    p = j["params"]
    enc = p.get("removal", {}).get("encounter", {})
    return {"case": p.get("case"), "integrator": p.get("integrator"), "coordinates": p.get("coordinates"), "dt_yr": p.get("dt_yr"),
            "encounter_method": enc.get("method"), "seed": p.get("ic", {}).get("seed"), "p9": p.get("ic", {}).get("p9"),
            "p9_plane": p.get("ic", {}).get("p9_plane"), "program": j.get("code", {}).get("program"), "commit": j.get("code", {}).get("commit")}


def export(parts_paths, out, *, p9sim=None, run_id, title, group, show=2000, every=1e7, n_tp=None, status="Pilot, not peer-reviewed",
           note="", window=(1e9, 4e9), evaluation=None, notary=None):
    if group not in GROUPS:
        sys.exit(f"--group must be one of {', '.join(GROUPS)}")
    if group in EVALUATED_GROUPS:
        if not evaluation:
            sys.exit(f"group {group}: results only after the evaluation; give --evaluation (result.json of tools/prod_eval.py)")
        ev = json.loads(Path(evaluation).read_text())
        if not ev.get("complete"):
            sys.exit(f"{evaluation}: the evaluation is not over the complete run")
    parts = [Part(p, p9sim) for p in parts_paths]
    if n_tp is None:
        if not parts[0].job:
            sys.exit("--n-tp is needed for npz runs")
        n_tp = int(parts[0].job["params"]["ic"]["n_tp"])
    stride = max(1, math.ceil(n_tp / show))
    times = common_times(parts, every)
    if not times:
        sys.exit("no snapshot common to all parts")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    body = bytearray(MAGIC + struct.pack("<I", len(times)))
    curves = {"t_yr": [], "n_tp": [], "selections": {k: {"n": [], "C": [], "S": [], "anti": []} for k in SELECTIONS}}
    drawn = []
    for t in times:
        n_alive, sums, p9, d = snapshot(parts, t, stride)
        body += pack(t, p9, d)
        drawn.append(int(len(d[0])))
        curves["t_yr"].append(t)
        curves["n_tp"].append(n_alive)
        for k, (n, C, S, anti) in sums.items():
            c = curves["selections"][k]
            c["n"].append(n); c["C"].append(C); c["S"].append(S); c["anti"].append(anti)
    (out / "data.bin").write_bytes(bytes(body))
    (out / "curves.json").write_text(json.dumps(curves, separators=(",", ":")) + "\n")

    # the source data: every file read, relative to the common parent of the parts
    base = Path(os.path.commonpath([str(Path(p).resolve()) for p in parts_paths]))
    if len(parts) == 1:
        base = base.parent
    lines, by_path = [], {}
    for part in parts:
        for f in part.files:
            h = sha256_file(f)
            by_path[Path(f).resolve()] = h
            lines.append(f"{h}  {Path(f).resolve().relative_to(base)}")
        for s in part.segments:
            s["output_sha256"] = by_path.get((part.path / "segments" / s["segment"] / "output.sa").resolve())
    src = "\n".join(lines) + "\n"
    (out / "SOURCES.sha256").write_text(src)

    in_window = [t for t in times if window[0] - 1 <= t <= window[1] + 1]
    manifest = {
        "schema": SCHEMA, "id": run_id, "title": title, "group": group, "status": status, "note": note,
        "model": describe(parts),
        "planned_t_end_yr": max(p.planned for p in parts),
        "window_yr": list(window),
        "frame": "barycentric osculating elements in the frame of Jupiter's orbital plane at each snapshot, longitudes as dog-leg "
                 "longitudes from the equinox of the ecliptic J2000 (tools/prod_eval.py); dvarpi, dOmega against the Planet Nine "
                 "of the particle's own part",
        "selections": {k: {"label": LABELS[k], "a_min_au": c[0], "a_max_au": None if math.isinf(c[1]) else c[1],
                           "q_min_au": None if math.isinf(c[2]) else c[2]} for k, c in SELECTIONS.items()},
        "anti_half_width_deg": ANTI_HALF_WIDTH,
        "test_particles": n_tp,
        "parts": [{"name": p.path.name, "kind": p.kind,
                   "job_id": p.job["id"] if p.job else None,
                   "input_sha256": p.job["input"]["sha256"] if p.job else None,
                   "tp_from": p.job["params"]["ic"].get("tp_from") if p.job else None,
                   "tp_to": p.job["params"]["ic"].get("tp_to") if p.job else None,
                   "planned_t_end_yr": p.planned, "segments": p.segments} for p in parts],
        "sources": {"file": "SOURCES.sha256", "sha256": hashlib.sha256(src.encode()).hexdigest(), "files": len(lines),
                    "note": "sha256sum lines of every file read; the sha256 of this file is the hash of the source data"},
        "export": {"tool": "tools/export_timelapse.py", "version": git_commit(), "p9sim": p9sim_info(p9sim), "every_yr": every,
                   "snapshots": len(times), "t_first_yr": times[0], "t_last_yr": times[-1], "snapshots_in_window": len(in_window),
                   "subset": {"show": show, "stride": stride, "rule": f"test particles with id % {stride} == 0, alive, bound, a < {A_MAX_DRAW:g} au"},
                   "drawn": drawn,
                   "quantisation": "a to 0.25 au, e to 1/65535, angles to 0.01 deg (drawing only; the curves are from the full values)"},
        "files": {"data.bin": {"sha256": sha256_file(out / "data.bin"), "bytes": (out / "data.bin").stat().st_size, "format": "P9WEB001"},
                  "curves.json": {"sha256": sha256_file(out / "curves.json"), "bytes": (out / "curves.json").stat().st_size}},
    }
    if evaluation:
        ev = json.loads(Path(evaluation).read_text())
        manifest["evaluation"] = {"file": Path(evaluation).name, "sha256": sha256_file(evaluation), "verdict": ev.get("verdict"),
                                  "criteria": ev.get("criteria")}
    if notary:
        manifest["notary"] = json.loads(Path(notary).read_text())
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest, curves


def pooled(curves, key="SBB", window=(1e9, 4e9)):
    """M1 and M2 over the window from the curves (what the page computes), for the tests."""
    c = curves["selections"][key]
    w = [k for k, t in enumerate(curves["t_yr"]) if window[0] - 1 <= t <= window[1] + 1]
    C, S = sum(c["C"][k] for k in w), sum(c["S"][k] for k in w)
    Rs = [math.hypot(c["C"][k], c["S"][k]) / c["n"][k] for k in w if c["n"][k] > 0]
    return math.degrees(math.atan2(S, C)) % 360, (sum(Rs) / len(Rs) if Rs else None)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("parts", nargs="+")
    ap.add_argument("--p9sim")
    ap.add_argument("--id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--group", required=True, choices=GROUPS)
    ap.add_argument("--out", required=True)
    ap.add_argument("--show", type=int, default=2000)
    ap.add_argument("--every", type=float, default=1e7)
    ap.add_argument("--n-tp", type=int)
    ap.add_argument("--status", default="Pilot, not peer-reviewed")
    ap.add_argument("--note", default="")
    ap.add_argument("--window", type=float, nargs=2, default=(1e9, 4e9))
    ap.add_argument("--evaluation")
    ap.add_argument("--notary", help="JSON file with the notary entries the run refers to (copied into the manifest)")
    a = ap.parse_args()
    m, _ = export(a.parts, a.out, p9sim=a.p9sim, run_id=a.id, title=a.title, group=a.group, show=a.show, every=a.every, n_tp=a.n_tp,
                  status=a.status, note=a.note, window=tuple(a.window), evaluation=a.evaluation, notary=a.notary)
    e = m["export"]
    print(f"{a.out}: {e['snapshots']} snapshots {e['t_first_yr']:.6g}-{e['t_last_yr']:.6g} yr, drawn {min(e['drawn'])}-{max(e['drawn'])}, "
          f"data.bin {m['files']['data.bin']['bytes']} bytes, sources {m['sources']['files']} files sha256 {m['sources']['sha256']}")


if __name__ == "__main__":
    main()
