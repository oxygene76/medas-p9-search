# SPDX-License-Identifier: GPL-3.0-or-later
"""Report of the speed comparison (speed.sh report): RESULTS.tsv -> throughput tables and ratios.

Only runs with the reference result hash (verdict SAME) count. Throughput is in test-body steps per second:
test bodies at the start x steps / wall time of the program (wall_s of its result line). Removed test bodies are
few in these jobs (at most 15 of 4,000 over 10 Myr in the notebook runs) and are not subtracted.
"""
import csv
import datetime
import os
import statistics
import sys
from collections import defaultdict

tsv, res = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(tsv), delimiter="\t"))
for r in rows:
    for k in ("n_tp", "steps", "rep"):
        r[k] = int(r[k])
    for k in ("wall_s", "wall_shell_s", "t_start", "t_end"):
        r[k] = float(r[k])

# a stage run again appends its runs: only the latest run of each (stage, device, job, build, repetition) counts
latest = {}
for r in sorted(rows, key=lambda r: r["t_start"]):
    latest[(r["stage"], r["device"], r["job"], r["build"], r["rep"])] = r
rows = list(latest.values())
group = defaultdict(list)
for r in rows:
    group[(r["stage"], r["device"], r["job"], r["build"])].append(r)


def med(stage, device, job, build="bin"):
    """median wall time of the valid runs, number valid, number in all"""
    g = group.get((stage, device, job, build), [])
    ok = [r["wall_s"] for r in g if r["verdict"] == "SAME"]
    return (statistics.median(ok) if ok else None), len(ok), len(g)


def rate(stage, device, job, build="bin"):
    g = group.get((stage, device, job, build), [])
    m, n, _ = med(stage, device, job, build)
    return g[0]["n_tp"] * g[0]["steps"] / m if m else None


def fmt(x, f="{:.3g}"):
    return "-" if x is None else f.format(x)


def gpu_clock(device, t0, t1):
    """median SM clock, max temperature and the clock event reasons seen in [t0, t1] of the GPU monitor log"""
    p = os.path.join(res, f"gpu-{device}-monitor.csv")
    if not os.path.exists(p):
        return None
    if not hasattr(gpu_clock, "cache"):
        gpu_clock.cache = {}
    if p not in gpu_clock.cache:
        rr = list(csv.reader(open(p), skipinitialspace=True))
        head = [h.split(" [")[0] for h in rr[0]]
        data = []
        for r in rr[1:]:
            if len(r) != len(head):
                continue
            try:
                ts = datetime.datetime.strptime(r[0], "%Y/%m/%d %H:%M:%S.%f").replace(tzinfo=datetime.timezone.utc).timestamp()
            except ValueError:
                continue
            data.append((ts, dict(zip(head, r))))
        gpu_clock.cache[p] = data
    inside = [d for ts, d in gpu_clock.cache[p] if t0 <= ts <= t1]
    clk = [float(d.get("clocks.current.sm", d.get("clocks.sm", "nan"))) for d in inside if d.get("clocks.current.sm", d.get("clocks.sm", "")).isdigit()]
    tmp = [float(d["temperature.gpu"]) for d in inside if d.get("temperature.gpu", "").isdigit()]
    reasons = sorted({d.get("clocks_event_reasons.active", "?") for d in inside})
    return (statistics.median(clk) if clk else None, max(tmp) if tmp else None, reasons, len(inside))


out = []
p = out.append
p(f"== speed comparison, {len(rows)} runs, {sum(r['verdict'] == 'SAME' for r in rows)} with the reference hash")
bad = [r for r in rows if r["verdict"] != "SAME"]
if bad:
    p("== runs that do not count (not the reference hash):")
    for r in bad:
        p(f"   {r['stage']} {r['device']} {r['job']} {r['build']} r{r['rep']}: {r['verdict']} {r['result_sha256'][:16]}")

devices = sorted({r["device"] for r in rows if r["stage"] == "gpu"})
node = sorted({r["device"] for r in rows if r["stage"] == "cpu1"})
cpu1 = node[0] if node else None

p("\n== 1. The notebook comparison repeated: 4,000 test bodies, 10 Myr (median wall time, valid/all runs)")
p(f"{'':28s} {'wh (fixed step)':>22s} {'v5 (smooth)':>22s}")
for dev in devices:
    a, b = med("gpu", dev, "gpu-wh-4k-10m"), med("gpu", dev, "gpu-v5-4k-10m")
    p(f"{'p9gpu on ' + dev:28s} {fmt(a[0], '{:.1f} s'):>14s} ({a[1]}/{a[2]}) {fmt(b[0], '{:.1f} s'):>14s} ({b[1]}/{b[2]})")
if cpu1:
    a, b = med("cpu1", cpu1, "cpu-whfast-4k-10m"), med("cpu1", cpu1, "cpu-merc-4k-10m")
    p(f"{'REBOUND, 1 core (' + cpu1 + ')':28s} {fmt(a[0], '{:.1f} s'):>14s} ({a[1]}/{a[2]}) {fmt(b[0], '{:.1f} s'):>14s} ({b[1]}/{b[2]})"
      "   (WHFast | MERCURIUS)")
    for dev in devices:
        wh, v5 = med("gpu", dev, "gpu-wh-4k-10m")[0], med("gpu", dev, "gpu-v5-4k-10m")[0]
        p(f"   ratio 1 core / {dev}: WHFast / wh {fmt(a[0] / wh if a[0] and wh else None, '{:.1f}')}, "
          f"MERCURIUS / v5 {fmt(b[0] / v5 if b[0] and v5 else None, '{:.1f}')}")
    for j in ("cpu-whfast-4k-10m", "cpu-merc-4k-10m"):
        r = rate("cpu1", cpu1, j)
        if r:
            p(f"   {j}: {1e9 / r:.1f} ns per test-body step")
    p("   notebook (runs/speed, 2026-10-23, RTX 5080 Laptop, WSL2, not pinned): wh 447 s, v5 884 s, WHFast 10,026 s, MERCURIUS 15,052 s")

p("\n== 2. GPU scaling series, 1 Myr (2e6 steps): test-body steps per second at full load (median of the valid runs)")
for dev in devices:
    p(f"-- {dev}")
    p(f"{'test bodies':>12s} {'wh steps/s':>12s} {'wall':>9s} {'v5 steps/s':>12s} {'wall':>9s}  SM clock (median, wh / v5), max temp, reasons")
    for n, lab in ((4000, "4k"), (16000, "16k"), (64000, "64k"), (256000, "256k")):
        cells = []
        info = []
        for meth in ("wh", "v5"):
            j = f"gpu-{meth}-{lab}-1m"
            m, k, t = med("gpu", dev, j)
            cells += [fmt(rate("gpu", dev, j)), fmt(m, "{:.1f} s") + (f"*{k}/{t}" if k != t else "")]
            g = [r for r in group.get(("gpu", dev, j, "bin"), []) if r["verdict"] == "SAME"]
            c = [gpu_clock(dev, r["t_start"], r["t_end"]) for r in g]
            c = [x for x in c if x and x[0]]
            info.append(f"{statistics.median(x[0] for x in c):.0f} MHz, {max(x[1] or 0 for x in c):.0f} C, {'/'.join(sorted({y for x in c for y in x[2]}))}"
                        if c else "no clock log")
        p(f"{n:>12,d} {cells[0]:>12s} {cells[1]:>9s} {cells[2]:>12s} {cells[3]:>9s}  {' | '.join(info)}")

p("\n== 3. Whole CPU: the 1-Myr slice of 4,000 test bodies on every core at once")
whole = {}
for (stage, dev, job, build), g in sorted(group.items()):
    if stage != "cpuall":
        continue
    ok = all(r["verdict"] == "SAME" for r in g)
    t = max(r["t_end"] for r in g) - min(r["t_start"] for r in g)
    thr = len(g) * g[0]["n_tp"] * g[0]["steps"] / t
    per = statistics.median(r["wall_s"] for r in g)
    whole[(dev, job)] = thr if ok else None
    p(f"   {job} ({dev}): {len(g)} processes, {sum(r['verdict'] == 'SAME' for r in g)} with the reference hash; whole batch {t:.0f} s; "
      f"median per process {per:.0f} s = {1e9 * per / (g[0]['n_tp'] * g[0]['steps']):.1f} ns per test-body step; "
      f"throughput {fmt(thr if ok else None)} test-body steps/s" + ("" if ok else " (does not count: a run without the reference hash)"))

p("\n== 4. Whole GPU against whole CPU (test-body steps per second; GPU: the best point of the scaling series)")
for dev in devices:
    for meth, cj in (("wh", "cpu-whfast-4k-1m"), ("v5", "cpu-merc-4k-1m")):
        best = max(((rate("gpu", dev, f"gpu-{meth}-{lab}-1m") or 0), lab) for lab in ("4k", "16k", "64k", "256k"))
        cw = [v for (d, j), v in whole.items() if j == cj and d == "all"]
        cw = cw[0] if cw else None
        p(f"   {dev} {meth} {fmt(best[0] or None)} (at {best[1]}) against the CPU {'WHFast' if meth == 'wh' else 'MERCURIUS'} {fmt(cw)}: "
          f"ratio {fmt(best[0] / cw if best[0] and cw else None, '{:.1f}')}")

p("\n== 5. -march=native (p9sim built on this machine; 1-Myr jobs, single core, all at once)")
for j in ("cpu-whfast-4k-1m", "cpu-merc-4k-1m"):
    devs = sorted({d for (s, d, jj, b) in group if s == "native" and jj == j})
    for dev in devs:
        s, n = med("native", dev, j, "std"), med("native", dev, j, "native")
        p(f"   {j}: standard {fmt(s[0], '{:.1f} s')} ({s[1]}/{s[2]} with the reference hash), "
          f"-march=native {fmt(n[0], '{:.1f} s')} ({n[1]}/{n[2]}); native/standard {fmt(n[0] / s[0] if n[0] and s[0] else None, '{:.3f}')}")
print("\n".join(out))
