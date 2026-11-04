# Speed comparison on appmdp-05, 3 and 4 November 2026

The repetition of the notebook comparison (`runs/speed/RESULT.md`) on a server: defined cores, pinned, full-load
throughput, a GPU scaling series.
- **Package:** `p9speed-12b5888` (`speed/`), the binaries of p9prod-9a084ed.
- **Run:** by the project lead, in two blocks: night (env, gpu L40S, cpuall) from 2026-11-03 16:40 UTC, then day (env,
  native, gpu A100, cpu1) until 2026-11-04 04:14 UTC.
- **Results:** `build/results-appmdp-05.tar.gz`, sha256
  `1b1cc436e80aa7aa75f0f2998420ede0056ba64d759366106a8fe6942f2ce316` (not in git).
- **Every one of the 142 runs gave the reference result hash.**

## Machine

| | |
|---|---|
| CPU | 2 × Intel Xeon Gold 6444Y, 16 cores each, no SMT; KVM virtual machine (the vCPUs as the hypervisor pins them), kernel 5.15.0-202 |
| GPUs | NVIDIA A100-PCIE-40GB (250 W, max SM clock 1410 MHz, ECC on) and NVIDIA L40S (350 W, 2520 MHz), driver 580.178.04 |
| background load before each stage | 0.73–0.81 busy logical CPUs over 60 s (limit 2) |
| compiler for the native build | gcc 11.4.0 (Ubuntu 22.04) |

## Results (`speed/report.py`)

**Decimal commas:** `RESULTS.tsv` was written under a German locale.
- bash printf could not read the decimal point there and wrote whole seconds with a decimal comma: `wall_shell_s`,
  `t_start` and `t_end`, 142 fields each, all ",000".
- The measured value `wall_s` (the program's own wall time) was written as text and is complete.
- `speed/convert_results.py` made a copy with points. The original (sha256 `0d99a776…7186`) is unchanged.
- The report uses `wall_s`. The whole seconds of `t_start` and `t_end` serve only for the clock windows and the batch
  time of cpuall.
- Since ae26a3e `speed.sh` runs with `LC_ALL=C`.

**1. The notebook jobs: 4,000 test bodies, 10 Myr** (median of 3; ratio = 1 CPU core / GPU):

| | wh (fixed step) | v5 (smooth) |
|---|---|---|
| p9gpu, A100 | 124.3 s | 240.6 s |
| p9gpu, L40S | 474.1 s | 820.4 s |
| REBOUND, 1 core (6 at once on CPU 1) | WHFast 13,466 s (168 ns per body step) | MERCURIUS 20,239 s (253 ns) |
| ratio A100 | 108 | 84 |
| ratio L40S | 28 | 25 |
| notebook (2026-10-23, RTX 5080 Laptop, WSL2, not pinned) | 447 s; WHFast 10,026 s | 884 s; MERCURIUS 15,052 s |

**2. Scaling series, 1 Myr, test-body steps per second** (median of 3):

| test bodies | A100 wh | A100 v5 | L40S wh | L40S v5 | A100 / L40S (v5) |
|---|---|---|---|---|---|
| 4,000 | 6.42e8 | 3.46e8 | 1.69e8 | 1.00e8 | 3.5 |
| 16,000 | 2.39e9 | 1.08e9 | 6.75e8 | 3.51e8 | 3.1 |
| 64,000 | 4.28e9 | 1.99e9 (64.3 s per Myr) | 6.80e8 | 4.13e8 | 4.8 |
| 256,000 | 4.57e9 | 2.48e9 | 7.26e8 | 4.63e8 | 5.4 |

- The A100 kept 1335–1410 MHz. SW power cap (0x4) appeared at 64,000 and more; no other clock event reason.
- The L40S ran at 2520 MHz throughout.
- The ratio A100 / L40S grows with the number of test bodies:
  - v5: 3.1–5.4;
  - wh: 3.5–6.3.

**3. Whole CPU** (the same 1-Myr slice on all 32 cores at once):
- WHFast: 1.53e8 body steps/s, 194 ns per step and core;
- MERCURIUS: 9.66e7 body steps/s, 306 ns per step and core;
- with every core busy, a core is 15–21 % slower than in cpu1 (6 at once).

**4. Whole GPU against whole CPU** (best point of the scaling series):
- A100: wh / WHFast 29.9, v5 / MERCURIUS 25.7;
- L40S: 4.7 and 4.8.

**5. `-march=native`:** the same result hashes. It was not faster: WHFast 1.021, MERCURIUS 1.074 times the standard
build's time. The builds stay without `-march`.

## Run time of the A100 sections and of MERCURIUS 110–112 (`speed/estimate_a100.py`)

**Method:**
- Wall time per Myr of v5 on the A100 from the scaling series: 23.1 s at 4,000, 29.7 s at 16,000, 64.3 s at 64,000
  and 206.4 s at 256,000 test bodies, interpolated log-log. Below 4,000 the value at 4,000, as the GPU is
  latency-bound there.
- The number of test bodies falls as in the night run G201: the production configuration, 4,000 test bodies,
  0–820 Myr, 78 % left at 200 Myr and 56 % at 820 Myr. Beyond that, two cases:
  - (a) the log fit over 200–820 Myr, 32 % left at 4 Gyr;
  - (b) no further loss after 820 Myr, an upper bound.
- Three processes on one GPU take as long as one after the other.

| A100 section (decision of 2026-11-04) | test bodies | days, (a) to (b) | at constant N |
|---|---|---|---|
| 1. production run | 64,000 | 1.9–2.2 | 3.0 |
| 2. seeds 110–112, V5 | 3 × 2,000 | 3.2 | 3.2 |
| 3. set A | 64,000 | 1.9–2.2 | 3.0 |
| 4. set B | 64,000 | 1.9–2.2 (B may lose bodies faster: less) | 3.0 |
| **in all** | | **9.0–9.8 days** | 12.2 |

**Seeds 110–112:**
- They are latency-bound: 2,000 bodies cost as much per Myr as 4,000.
- Three processes take three times as long; the time hardly falls with the loss of bodies.
- Bundled into one process (6,000 bodies, about 25 s per Myr), they would take about 1.2 days instead of 3.2.
  This is follow-up C3.

**MERCURIUS 110–112 on CPU 1** (16 cores; 24 slices of 250, two rounds):
- 253–306 ns per body step (6 at once to all 32 cores busy);
- mean share of bodies alive 0.47 (a) to 0.59 (b);
- 1,600–2,400 core hours, **5.5–8.3 days**, in parallel to the A100.

## Correction after the start of the production run (2026-11-04, provisional)

**Observed:** segment 0 of the production run reached 60 Myr after 5,603 s with 61,790 test bodies left. That is
93 s per Myr, 45 % more than the 64.3 s of the 1-Myr scaling job at 64,000.

**Explanation (to be confirmed with `flybys.tsv` of segment 0):** the scaling job covers only 0–1 Myr after the start.
p9gpu v5 follows every close flyby with sub-steps, and flybys become more frequent after the start.
- The flybys within three encounter radii per test body and Myr in G201 (the same configuration, `flybys.tsv`) rise
  from 0.54 (0–20 Myr) to 1.24 (40–60 Myr) and 1.9 (100–120 Myr), then fall to about 0.7 after 300 Myr.
- In the 9 equivalence runs V5 the sub-steps per 20-Myr segment rise likewise, from 1.3 million (0–20 Myr) to 4.3
  million (100–120 Myr).
- The early phase therefore does not have more flybys than later; it has more than the first Myr. The busiest part
  is 100–160 Myr.

**Model** (`speed/estimate_encounters.py`): wall per Myr = w(N) (1 + k (r(t) − r0)).
- r(t) is the flyby rate of G201.
- r0, the rate of the scaling job, is not measured; the two cases r0 = 0 and r0 = 0.54 bracket it.
- k is fitted to the observation at 60 Myr.

| A100 section | before | with the flybys |
|---|---|---|
| production run | 1.9–2.2 days | **2.4–3.1 days** |
| set A, set B (each, same flyby profile assumed) | 1.9–2.2 days | **2.4–3.1 days** |
| seeds 110–112, V5 (latency-bound; k from the equivalence runs, +11 % per unit of r, correlation 0.58 only) | 3.2 days | **3.3–3.5 days** |
| **A100 in all** | 9.0–9.8 days | **10.6–12.6 days** |

What follows for the production run:
- Segment 0 (0–100 Myr) takes about 2.7–2.9 h.
- Segments 1 to about 3 (100–300 Myr) are slower per Myr, not faster.
- From about 300 Myr the flybys and the number of bodies both fall.

Set B (Planet Nine at 300 au) may have a different flyby profile than G201; its estimate is the least certain.
