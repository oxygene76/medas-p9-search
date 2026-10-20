# What limits p9gpu: FP64 throughput (measured 2026-10-19)

Question: does p9gpu's run time depend on the GPU's double-precision (FP64)
rate, and what would a GPU with full FP64 (A100, H100) bring?

Answer: **yes**. With enough test particles the kernel runs at 92 % of the
rate that the FP64 operations alone allow on this GPU; without FP64 (the same
code in float, as a probe) it is 14 times faster. A data-centre GPU with full
FP64 would be about 17 (A100) to 59 (H100 SXM) times faster per GPU, if it is
given enough test particles (several hundred thousand); an L40S, which has as
little FP64 as this laptop GPU relative to its size, about 2.5 times.

## How it was measured

Nsight Compute (2026.3.1, from NVIDIA's CUDA redistributables) could not be
used: under WSL2 the GPU's performance counters are reserved for
administrators (`ERR_NVGPUCTRPERM`). Enabling them needs the NVIDIA Control
Panel on Windows with administrator rights (Desktop > Enable Developer
Settings, then Developer > Manage GPU Performance Counters > "Allow access to
the GPU performance counters to all users"); on a Linux server the driver
option `NVreg_RestrictProfilingToAdminUsers=0` or running ncu as root. Instead,
three measurements without counters:

1. **Operations per step**, counted exactly: the kernel's code
   (`gpu/whdh_t.h`, the template copy that gives the same bits as `whdh.h`)
   run with a number type that counts (`gpu/probe/count_ops.cpp`, `make
   gpu-probe`). One test-particle step with 5 planets (Jupiter–Neptune,
   Planet Nine): **157 add/sub, 275 mul, 10 div, 6 sqrt, 13 compare**; every
   1000 steps a synchronisation (a Kepler half step) adds about 0.3 %.
2. **Throughput per operation** on this GPU (`gpu/probe/peak.cu`, built like
   p9gpu with `--fmad=false`; 15,360 threads × 8 independent chains):

   | | double | float |
   |---|---|---|
   | add | 2.86e11 /s | 1.97e13 /s |
   | mul | 2.85e11 /s | 1.94e13 /s |
   | div | 3.69e10 /s | 8.5e11 /s |
   | sqrt | about 3.7e10 /s | about 1.2e12 /s |

   NVIDIA GeForce RTX 5080 Laptop GPU (sm_120, 60 SMs): double runs at 1/69
   of float. Division and square root are subroutines (about 8 adds each).
3. **The same kernel in three number types** (`P9GPU_REAL`, 20,000 steps,
   test-case inputs of the scaling runs, particle-steps per second):

   | test particles | double | df64 | float (probe) |
   |---|---|---|---|
   | 4,000 | 2.3e8 | 3.2e8 | 1.3e9 |
   | 16,000 | 3.4e8 | 7.6e8 | 4.4e9 |
   | 64,000 | 4.5e8 | 9.0e8 | 7.7e9 |
   | 256,000 | 4.6e8 | 9.1e8 | 6.4e9 |

From 1 and 2: the FP64 operations of one step take 157/2.86e11 + 275/2.85e11 +
10/3.69e10 + 6/3.7e10 + 13/2.86e11 = 2.0 ns on this GPU, so at most **5.0e8
particle-steps per second**. Measured at 256,000 test particles: 4.6e8, i.e.
**92 %**; at 64,000: 90 %. Everything else (loads of the planet table, integer
work, the CPU's planet steps) fits into the remaining few per cent. The float
probe, whose FP64 work is gone, is 14 times faster and itself far below its own
limit (float would allow 2.6e10): the kernel is FP64-bound.

Below about 30,000 test particles the GPU is not filled: with 4,000 there are
67 threads per SM, and fixed costs per run (loading, output) weigh more. Then
the speed is about half the saturated value.

## Estimate for other GPUs

If the kernel stays FP64-bound, its speed scales with the FP64 instruction
rate. With `--fmad=false` every add and every mul is one FP64 instruction, so
the relevant rate is half the FP64 FLOPS that NVIDIA states (which count an FMA
as two):

| GPU | FP64 (datasheet) | FP64 instructions/s | factor vs this GPU | particle-steps/s (saturated, estimate) |
|---|---|---|---|---|
| RTX 5080 Laptop (this) | – | 2.86e11 (measured) | 1 | 4.6e8 (measured) |
| L40S | not stated; 1/64 of 91.6 TFLOPS FP32 = about 1.4 TFLOPS | about 7.2e11; **measured 6.0e11** | about 2.5; **measured 2.0** | about 1.2e9; **measured 9.0e8 (df64: 2.7e9)** |
| A100 (SXM or PCIe) | 9.7 TFLOPS | 4.9e12 | 17 | about 7.8e9 |
| H100 PCIe | 26 TFLOPS | 1.3e13 | 45 | about 2.1e10 |
| H100 SXM | 34 TFLOPS | 1.7e13 | 59 | about 2.7e10 |

Conditions and limits of the estimate:

- **Enough test particles.** These GPUs have 108 (A100), 114 (H100 PCIe), 132
  (H100 SXM) and 142 (L40S) SMs against 60 here, and on A100/H100 each SM
  executes 32 times as many FP64 operations per cycle, so many more threads are
  needed to keep the FP64 units busy: about 250,000–500,000 test particles per
  GPU (here 64,000 suffice). With 5,000 test particles (the 4-Gyr run) an
  H100 is limited by the latency of one particle's step, not by throughput; a
  rough estimate is a factor of up to about 10 over this GPU, not 59.
- **The CPU part** (the planets' table) takes 0.75 µs per step here, up to
  1.3 million steps per second: at 256,000 test particles an H100 needs about
  100,000 steps per second, so the CPU stays far from limiting.
- **Same bits.** All these GPUs compute IEEE binary64 with correctly rounded
  operations; with `--fmad=false` the results are the same as here (to be
  confirmed with the GPU check package, `docs/gpu-check.md`).

For the L40S check (64,000 test particles, 10 million years; here 2,850 s):
expected about 2,850 × 4.5e8 / 1.15e9 ≈ **1,100 s**, if the L40S runs at the
same fraction of its FP64 rate.

## df64 (double-float)

The double-float variant (`P9GPU_REAL=df64`, `gpu/df64.h`) replaces each
double by two floats; it costs about 20 float operations per add and 23 per
multiplication (without FMA, see `docs/gpu-precision.md`). On this GPU it is
**2.0 times faster** than double when saturated (9.1e8 against 4.6e8), 1.4
times at 4,000 test particles. On an L40S the ratio of float to double is the
same (1/64), so the gain would be similar there; on an A100 or H100 df64 would
be slower than double.
