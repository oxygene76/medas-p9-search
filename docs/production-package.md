# Production package for the GPU server (p9prod)

Built by `tools/make_prod_package.sh` from the job in `runs/prod` (64,000 test
particles, seed 21, Brown & Batygin 2021 start conditions, 4.5 au, smooth v5,
FP64, 4 Gyr in 40 segments of 100 Myr); scripts in `prod/`, instructions in the
package (`README.txt`). Tested by `tools/test_prod_package.sh` (plain
ubuntu:22.04 container, CPU twin): check ALL SAME, two shortened segments give
the check's chain hash, resume after a simulated interruption gives the same,
stop during the check works.

## Package of 2026-10-21: `p9prod-9a084ed.tar.gz` (current)

sha256 `caff48128882982a4a11affe7111f33f950d2e2027e633e6002aed0c04d9b12e`,
11.8 MB; prebuilt p9gpu sha256 `7666c5ba4560a8c2…` (CUDA 13.3, Ubuntu 22.04,
glibc ≥ 2.34).

## Check on the L40S (2026-10-21, appmdp-05, run by the project lead)

`sh check.sh`: **ALL SAME**, all 38 jobs bit for bit as on the reference
machine (NVIDIA L40S, driver 580.178.04, compute capability 8.9): the 32
regression cases (0.07–5.0 s each), the 4 deep Neptune flybys with up to 2^21
sub-steps and 2 collisions (23–33 s each), the production start values over
10 kyr (3.2 s) and the same as two joined segments (1.6 s). About 2.2 min of
computing.

The production run itself is not started: it waits for the acceptance of the
smooth transition (the ensemble of `docs/validation-ensemble-200myr.md` did not
pass; the cause is being searched).
