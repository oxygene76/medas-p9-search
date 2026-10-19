# Double-float (df64) for p9gpu: does it do the job?

Question (2026-10-19): can a double-float variant of the kernel (each number as
the sum of two float32) replace double: accuracy against FP64 over 300 Myr
(energy error, statistics of the clustering), bitwise reproducibility without
FMA, speed on the laptop GPU.

## Design

- `gpu/df64.h`: a number is hi + lo, two binary32 with |lo| <= ulp(hi)/2,
  about 48 significant bits (double: 53). Written from the published
  error-free transformations: Knuth's TwoSum, Dekker's FastTwoSum, Split and
  TwoProduct (1971) and the double-double arithmetic of Dekker and of Hida, Li
  & Bailey (2001): accurate addition, multiplication, long division with three
  quotient digits, square root with one correction.
- **No FMA**: the transformations need every product and sum rounded on its
  own (nvcc `--fmad=false`, host `-ffp-contract=off`), so TwoProduct uses
  Dekker's splitting (about 17 float operations instead of 2 with FMA).
- `gpu/whdh_t.h`: the integrator of `gpu/whdh.h` as a C++ template, every
  expression in the same order. Instantiated with double it gives the bits of
  the production code (checked: same result hash on CPU and GPU), so the df64
  kernel is the same algorithm, only in another number type.
- Selection: `P9GPU_REAL=df64`, in jobs `params.real` (`p9job make --real
  df64`); part of the job id, so a df64 result never passes for a double one.
  The planets, the conversions and the outputs stay double; the state is
  stored as double between GPU blocks, which is exact for df64 (hi + lo fits
  into a double), so results do not depend on the block size.

## Bitwise reproducibility

The same job (500 test particles, 20,000 years) on the GPU and with the CPU
twin (`gpu/cpu_t.cpp`, `P9GPU_MODE=cpu`): **identical result hashes** in df64
(`ba53b0ba…`), as in double and in float. Every operation is a correctly
rounded binary32 + − × ÷ or √ (nvcc's default `-prec-div`, `-prec-sqrt`, no
`-ftz`), which IEEE 754 fixes bit for bit.

## Speed (RTX 5080 Laptop GPU, particle-steps per second)

| test particles | double | df64 | df64 / double |
|---|---|---|---|
| 4,000 | 2.3e8 | 3.2e8 | 1.4 |
| 16,000 | 3.4e8 | 7.6e8 | 2.2 |
| 64,000 | 4.5e8 | 9.0e8 | 2.0 |
| 256,000 | 4.6e8 | 9.1e8 | 2.0 |

Details and the FP64 limit: `docs/gpu-performance.md`.

## Accuracy

(results of the 300-Myr runs: see below, added when they are done)
