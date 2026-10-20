# GPU check package (p9gpucheck)

For a second machine with an NVIDIA GPU (first: the L40S server, run by the
project lead; no access from here). Built by `tools/make_gpu_check_package.sh`
from the jobs in `runs/gpkg/`; instructions in the package (`README.txt`,
from `check/README-gpu.txt`), script `check/run-gpucheck.sh`.

## Package of 2026-10-20: `p9gpucheck-53a12d6.tar.gz`

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
