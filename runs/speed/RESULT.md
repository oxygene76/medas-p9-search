# Speed comparison, 23/24 October 2026

The same job four ways:

- Brown & Batygin (2021) configuration: Sun with the inner planets, Jupiter–Neptune (DE440s, JD 2458270.0) and Planet Nine.
- 4,000 test bodies (seed 101).
- Democratic heliocentric coordinates, dt = 0.5 yr, 10 Myr (2·10^7 steps), 10 snapshots.
- Three repetitions each; the time is the wall time of the program (`wall_s` in result.json, from `tools/p9job.py`).

| run | program | where | wall time (3 runs) | median |
|---|---|---|---|---|
| `wh-gpu` | p9gpu, fixed step (`step`, nothing removed at encounters) | GPU | 459.5 / 446.4 / 447.2 s | 447 s |
| `whfast-cpu` | p9sim, REBOUND WHFast | 1 CPU core | 10,024.8 / 10,026.3 / 10,027.5 s | 10,026 s |
| `v5-gpu` | p9gpu v5 (`smooth`: encounter sub-steps, collisions, planets with 8 inner steps) | GPU | 884.4 / 884.1 / 884.0 s | 884 s |
| `merc-cpu` | p9sim, REBOUND MERCURIUS (r_crit_hill 3) | 1 CPU core | 15,052.0 / 15,050.9 / 15,052.1 s | 15,052 s |

The result is bit-identical across the three repetitions of each run (result sha256 `2ce24189…`, `3e10bbab…`,
`9ed8e5f8…`, `32823da9…`).

Ratios of the medians:

- fixed step: p9gpu is about **22 times** as fast as WHFast on one core (10,026 / 447).
- with encounter handling: p9gpu v5 is about **17 times** as fast as MERCURIUS on one core (15,052 / 884).

v5 and MERCURIUS handle close encounters with different methods: the second ratio compares two tools on the same
task, not one method on two kinds of hardware.

## Hardware

- Notebook: Intel Core Ultra 9 275HX (8 P-cores, 16 E-cores, no SMT, 24 threads) and an NVIDIA GeForce RTX 5080
  Laptop GPU.
- Windows host with WSL2 (Ubuntu); the Linux VM sees 24 vCPUs (`lscpu`: hypervisor Microsoft).

## Precision

All four runs compute in FP64 (`real: double` in every result.json):

- p9sim (REBOUND) computes in double.
- p9gpu:
  - The test particles on the GPU use `P9GPU_REAL=double`, the default. It was not set, and the program records it.
  - The other number types (`double-t`, `float`, `df64`; `gpu/p9gpu_real.h`) were not used.
  - The planets are integrated on the CPU in double, in both variants.
- No fused multiply-add:
  - p9sim and the host part of p9gpu: `-ffp-contract=off`.
  - CUDA: `--fmad=false -prec-div=true -prec-sqrt=true`.
- FP64 on the GPU:
  - According to the NVIDIA whitepaper "NVIDIA RTX Blackwell GPU Architecture" (p. 9), GB202 has two FP64 units per SM, and its FP64 rate is 1/64 of the FP32 rate.
  - The paper gives no separate value for GB203 (the RTX 5080 Laptop GPU), but its SM architecture is the same.
  - So the GPU figures do not rest on a strong FP64 unit.
- Fairness:
  - Both sides are built to be reproducible: no FMA, no `-march`.
  - With `-march=native`, REBOUND would probably be somewhat faster, but no longer bit-identical on other machines.

## Programs and build

- Binaries: the ones in `build/equiv-bin/`, the same as in p9prod-9a084ed:
  - p9gpu: sha256 `7666c5ba4560a8c20437e01ee041194a17579e08efff90f43be9c6068c7d566f`;
  - p9sim: sha256 `b14f7956999a17b22e3de8b8b377f2218bf1bde046a29a32aaa981ed21e1ea65`;
  - both report version `9a084ed`.
- REBOUND 5.2.2 (`https://codeload.github.com/hannorein/rebound/tar.gz/refs/tags/5.2.2`, sha256 `86038080…`), compiled
  into both programs from source.
- p9sim (Makefile of 9a084ed): GCC 11.4.0 (Ubuntu 22.04), `-std=c99 -fno-fast-math -O3 -ffp-contract=off`; no
  `-march`, so generic x86-64 without AVX2/FMA code.
- p9gpu:
  - Kernel: nvcc from CUDA 13.3 (`Cuda compilation tools, release 13.3, V13.3.33` in the binary) with `-O3 --fmad=false -prec-div=true -prec-sqrt=true`. The binary contains code for sm_80, sm_89, sm_90 and sm_120; the RTX 5080 uses sm_120.
  - Host part: GCC 11.4.0 with `-std=c99 -fno-fast-math -O3 -ffp-contract=off`.

## CPU cores

- The six CPU runs ran at the same time: WHFast ×3 and MERCURIUS ×3, one process each and single-threaded.
  - They started at 21:05 and ended at 01:16. A first start at 20:31 was stopped after 3 minutes for cooling and restarted from scratch.
  - The GPU runs had finished before.
- **Not pinned.** No `taskset` or affinity was set. The Linux scheduler distributed the processes over the 24 vCPUs.
- **P- or E-cores: not determined.** Under WSL2 the Windows host schedules the vCPUs onto physical cores. Inside the VM
  all 24 vCPUs look alike: there is no hybrid information (`cpu_core`/`cpu_atom`) and no core-type field. So it is
  not known whether the runs were on P-cores or E-cores, or moved between them.
- Indications only:
  - The three repetitions of each program differ by less than 0.03 %. This suggests the same conditions throughout.
  - WHFast needed 125 ns per particle and step (10,026 s / (4,000 × 2·10^7)). That is close to the 110 ns measured on
    an idle P-core for the pilot run (`docs/pilot-run-2026-10-18.md`, 250 particles per process). It is far from the
    202 ns of the fully loaded machine there, with mixed P- and E-cores.
  - This points to P-cores, but does not prove it.
- For a statement per core type, the runs would have to be repeated with each process pinned and the core type known
  (for example on native Linux with `taskset` and `/sys/devices/cpu_core/cpus`).
- During the CPU half no other computation job was started. Desktop programs on the Windows side kept running.

## Files

- `run.sh`: the whole comparison, GPU half and the first CPU start.
- `run-cpu.sh`: the restarted CPU half, after a 30-minute pause.
- `run.log`: all times and result hashes.
- Job directories, outputs and result.json files are not in git.
