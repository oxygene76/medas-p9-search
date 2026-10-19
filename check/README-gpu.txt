MEDAS p9-search: GPU check (p9gpu, CUDA) for a second machine
=============================================================

What it does: builds p9gpu (test particles on an NVIDIA GPU, planets on the
CPU; sources included) and its CPU twin, computes the jobs in jobs/ and
compares each result with the hash computed on the reference machine
(EXPECTED); then a benchmark with 64,000 test particles over 10 million
years and a short speed probe (double, double-float, float). Nothing is sent
anywhere; nothing outside this directory is changed.

Run, either
  a) directly (Linux; needs make, gcc, g++, tar, sha256sum, the NVIDIA driver,
     and the CUDA toolkit for building, e.g. /usr/local/cuda/bin/nvcc):
       sh run-gpucheck.sh
     with nvcc elsewhere:   NVCC=/path/to/nvcc CUDA_LIB=/path/to/lib64 sh run-gpucheck.sh
     without a toolkit:     USE_PREBUILT=1 sh run-gpucheck.sh   (needs driver 580 or newer)
     without the benchmark: SKIP_BENCH=1 sh run-gpucheck.sh
  b) in a container (needs Docker with the NVIDIA Container Toolkit):
       docker build -f Dockerfile.gpu -t p9gpucheck . && docker run --rm --gpus all p9gpucheck

Time: the jobs take a few minutes (the CPU runs about 5 minutes); the
benchmark in double took about 2,850 s on the reference GPU (RTX 5080 Laptop
GPU) and should take about 1,100 s on an L40S, in df64 about half of that; the
probe under a minute.

Send back: the file report-gpu.txt (or the printed report). It contains the
system, CPU and GPU model, driver, compiler and CUDA versions, the hashes, run
times and GPU utilisation; no user names, no paths, no network data.

Jobs (the test case of Brown & Batygin 2021; no removal at the planets, only
beyond 10,000 au or within 5 au of the Sun):
  control     20 test particles, 100,000 years, on the GPU and on the CPU
  repro       1,000 test particles, 1 million years, on the GPU and on the CPU:
              the same bits are expected on both and on the reference machine
  repro-df64  1,000 test particles, 100,000 years, double-float arithmetic
              (two floats per number) on the GPU
  bench       64,000 test particles, 10 million years, on the GPU, double (FP64)
  bench-df64  the same in double-float (df64): the speed ratio of the two is
              what decides whether df64 pays on this GPU

Licence: GPL-3.0-or-later (REBOUND and p9gpu); sources included. The prebuilt
binary in bin/ contains NVIDIA's CUDA runtime (statically linked), which NVIDIA
permits to redistribute with applications.
