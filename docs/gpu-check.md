# GPU check package (p9gpucheck)

For a second machine with an NVIDIA GPU (first: the L40S server, run by the
project lead; no access from here). Built by `tools/make_gpu_check_package.sh`
from the jobs in `runs/gpkg/`; instructions in the package (`README.txt`,
from `check/README-gpu.txt`), script `check/run-gpucheck.sh`.

## Package of 2026-10-20, second: `p9gpucheck-07e5d2c.tar.gz` (current)

sha256 `b9d06e7ee0e3ee994a21d0a2a37f30e03f2b4506d537206adde32c434e767e88`, 15 MB. The same jobs and expected hashes as
53a12d6 below. Changed because the first one failed on the L40S server
(Ubuntu 22.04, glibc 2.35, driver 580.178.04, no CUDA toolkit): its prebuilt
binary, linked on this machine (glibc 2.43), needed `GLIBC_2.38`.

- The prebuilt binaries are now built in NVIDIA's image
  `nvidia/cuda:13.3.0-devel-ubuntu22.04` (CUDA 13.3, gcc 11, glibc 2.35),
  libstdc++ and libgcc linked statically; `objdump -T`: at most `GLIBC_2.34`,
  no `GLIBCXX`. The requirement is recorded in `bin/REQUIRES-glibc`.
- `run-gpucheck.sh` compares it with the system's glibc (`getconf
  GNU_LIBC_VERSION`) before running anything and stops with a clear message
  (exit code 3) if the system is older.
- Tested before delivery, unpacked into a plain container, without the
  benchmark: `ubuntu:22.04` with the GPU (`docker run --gpus all`), only make,
  gcc and g++ installed, `USE_PREBUILT=1`: **ALL SAME** (control and repro on
  GPU and CPU, repro-df64 on the GPU); `ubuntu:20.04` (glibc 2.31): stops
  with "the prebuilt binaries need glibc 2.34 or newer, this system has 2.31".

## Package of 2026-10-20, first: `p9gpucheck-53a12d6.tar.gz` (superseded)

sha256 `3a7b9d72a58ee69bde7cf86e9fc892ae7ca129f7b272ba6dc774bad733a314d7`,
14 MB. No removal at the planets in any job (only the distance rules).

| job | particles, time | runs on | expected (reference) |
|---|---|---|---|
| control | 20, 100 kyr | GPU and CPU | `d4905e7a…` (CPU twin) |
| repro | 1,000, 1 Myr | GPU and CPU | `6fc1b351…` (CPU twin) |
| repro-df64 | 1,000, 100 kyr, df64 | GPU | `b47cb900…` (CPU twin) |
| bench | 64,000, 10 Myr, double | GPU | `6a115e59…` (laptop GPU) |
| bench-df64 | 64,000, 10 Myr, df64 | GPU | `3b57df63…` (laptop GPU) |

Plus the throughput probe (`gpu/probe/peak.cu`) and 20,000 steps of the bench
input in double, df64 and float. The report states the speed ratio of df64 to
double on that GPU (the question for the second card).

Tested here before delivery, unpacked into an empty directory, without the
benchmark: with the prebuilt binary (`USE_PREBUILT=1`) and built from source
(nvcc 13.4, `-gencode arch=compute_120,code=sm_120`): **ALL SAME** both times
(control and repro on GPU and CPU, repro-df64 on the GPU).

Expected on an L40S (`docs/gpu-performance.md`): the double benchmark about
1,100 s if the kernel runs at the same share of the FP64 rate; df64 about
twice as fast, since the L40S, like this GPU, computes float 64 times faster
than double.

## Result on the L40S (2026-10-20, package 07e5d2c, prebuilt binary)

Server appmdp-05 (QEMU virtual machine, 32 threads, Ubuntu 22.04, glibc 2.35,
gcc 11.4); NVIDIA L40S (sm_89, 142 SMs, 46 GB), driver 580.178.04, power
limit 350 W, ECC on. Run by the project lead; report-gpu.txt:

- **ALL SAME**: control and repro on GPU and CPU, repro-df64, and both
  benchmarks give the hashes of the reference machine (laptop GPU and CPU
  twin), bit for bit, on another GPU architecture (sm_89 against sm_120) and
  another CPU.
- Benchmark, 64,000 test particles over 10 Myr:

  | | L40S | RTX 5080 Laptop (alone) | L40S / laptop |
  |---|---|---|---|
  | double (FP64) | 1,417 s, 9.0e8 particle-steps/s | 2,850 s, 4.5e8 | 2.0 |
  | df64 | 478 s, 2.7e9 | about 1,430 s, 9.1e8 | 2.9 |
  | df64 / double on the same GPU | 2.96 | 2.0 | |

  GPU utilisation 100 % in both; power 138 W (double: limited by the FP64
  units) against 353 W (df64: the float units at full load, at the power
  limit, SM clock 2,308 instead of 2,520 MHz).
- Throughput per operation (probe): double add/mul 6.0e11/s (laptop 2.86e11),
  float 4.3e13/s (1.97e13): the L40S computes double at 1/71 of float, as the
  laptop GPU (1/69). The double benchmark runs at 86 % of the limit its FP64
  rate allows (`docs/gpu-performance.md`: 572 FP64 operations per step), as on
  the laptop (90 %).
- Estimate in `docs/gpu-performance.md` was about 1,100 s and a factor 2.5;
  measured 1,417 s and 2.0: the L40S's FP64 rate is 2.1 times the laptop's,
  not 2.5 times.
