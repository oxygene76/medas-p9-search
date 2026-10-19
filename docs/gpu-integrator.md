# p9gpu: test particles on the GPU

A Wisdom-Holman integrator for massless test particles on NVIDIA GPUs, written
for this project from published methods only. It takes the same jobs as p9sim
(same input SimulationArchive, same command line) and writes the same outputs
(SimulationArchive snapshots, canonical state hash), so `tools/p9job.py`,
`tools/analyze.py` and the check package work unchanged.

Licence: GPL-3.0-or-later, like the rest of the client.

## Sources

Only these publications were used; no code of GLISSE or of other GPU
integrators was looked at or taken over.

1. J. Wisdom & M. Holman (1991), "Symplectic maps for the n-body problem",
   AJ 102, 1528: the mixed-variable symplectic map (Kepler drift and
   interaction kicks).
2. M. J. Duncan, H. F. Levison & M. H. Lee (1998), "A multiple time step
   symplectic algorithm for integrating close encounters", AJ 116, 2067: the
   democratic heliocentric splitting (Kepler, interaction and "jump" parts), the
   coordinate system of p9sim's REBOUND runs.
3. H. Rein & D. Tamayo (2015), "WHFast: a fast and unbiased implementation of a
   symplectic Wisdom-Holman integrator for long-term gravitational simulations",
   MNRAS 452, 376: the Kepler solver in universal variables with Stumpff
   functions and Halley iterations.
4. K. Zhang & B. J. Gladman (2022), "GLISSE: A GPU-optimized planetary system
   integrator with application to orbital stability calculations", New Astronomy
   90, 101659, arXiv:2011.03484: the method description only, i.e. one thread
   per test particle, planet positions computed on the CPU in blocks
   ("planetary chunks") ahead of the GPU, a Kepler solver with a fixed number of
   iterations to avoid branch divergence, and removing particles that come too
   close.
5. Standard identities of the Stumpff functions (argument quartering and the
   doubling formulas c0(4z) = 2c0(z)² − 1, c1(4z) = c0 c1, c2(4z) = c1²/2,
   c3(4z) = (c2 + c0 c3)/4), as in J. M. A. Danby (1992), Fundamentals of
   Celestial Mechanics, 2nd ed., chapter 6.

## What was seen of the GLISSE repository

On 2026-10-18, while checking GLISSE's licence (docs/gpu.md), before p9gpu was
written:

- Downloaded: the archive of the branch `master` of
  https://github.com/skkestrel/glisse (sha256
  `d1bbf9615fe555a92d941d5a995d071834011b4844fcc7ed841216d7dda37cb1`), extracted
  under `build/glisse/` (not committed; deleted on 2026-10-19).
- Read: `README.md` in full (usage, configuration options, file formats) and the
  first 50 lines of the `Makefile` (compiler flags, e.g. `-arch=sm_35`,
  `-maxrregcount 64`).
- Searched, without reading code: the names of the files that contain the words
  licence/copyright/GPL/MIT (only file names were shown: files of the bundled
  docopt library, `src/util.h`, `src/data.cpp`, `sia4/main.cu`,
  `targets/filter_state.cpp`); the first 30 lines of `src/wh.cu` for a licence
  line (no match, nothing shown); the number of occurrences of "fma"/"fmad" in
  the `.cu` files (zero each); the file names in `src/` and `targets/`.
- Not done: no source file (`.cu`, `.cuh`, `.cpp`, `.h`) was opened or read, no
  code was copied, the code was not built or run.

p9gpu follows the paper's method description (source 4) and the other
publications listed above.

## Design

- Coordinates: positions relative to the Sun, barycentric velocities
  (democratic heliocentric). One step of length dt, drift-kick-drift: Kepler
  drift dt/2 around G m_Sun – jump dt/2 (velocity w = Σ m_j u_j / m_Sun of the
  planets) – kick dt (planets acting on the body) – jump dt/2 – Kepler drift
  dt/2 (`gpu/whdh.h`). The Kepler halves of consecutive steps are done as one
  drift of dt; the state is kept half a drift ahead and synchronised with a
  drift of −dt/2 for outputs and removal checks. A first version
  (kick-drift-kick, commit feb930b) had twice the phase error of WHFast against
  IAS15; drift-kick-drift has the same (below).
- Planets (all massive bodies but the Sun) are integrated on the CPU with the
  same map, in blocks of `P9GPU_BLOCK` steps (default 2,000). For each block the
  CPU writes a table: the planets' positions at all step boundaries and the
  two jump velocities per step. The GPU advances all test particles through the
  block while the CPU computes the next table (two pinned buffers, one CUDA
  stream; the host thread sleeps while it waits). The GPU never waits for the
  CPU within a block.
- One GPU thread per test particle; a thread reads its particle once per block
  and writes it once. The table is read by all threads alike (cached).
- Removal as in p9sim: every 1,000 steps (counted over the whole run) a particle
  beyond 10,000 au or within 5 au of the Sun is dropped (flag; the thread then
  idles).
- Kepler solver: universal variables, second-order start value, three Halley
  iterations (fixed), Stumpff series (seven terms after quartering the argument
  to |z| ≤ 0.1). Divisions by constants are multiplications by the reciprocals;
  one division per Halley step.

## Reproducibility

- Only + − × ÷ and sqrt, correctly rounded in IEEE-754 binary64: on the CPU
  with `-ffp-contract=off` and without `-ffast-math`, on the GPU with nvcc
  `--fmad=false -prec-div=true -prec-sqrt=true`. No atomics, no reductions in
  the computation; threads are independent.
- Result: **the GPU and the CPU build give the same bits** (`P9GPU_MODE=cpu`
  and the CUDA-free build `make gpu-cpu`), for every block size tried (500,
  2,000, 8,000 steps), and the same job twice on the GPU gives the same hash.
- p9gpu and p9sim (REBOUND WHFast) do not give the same bits: their operator
  order differs. They agree to second order in dt (after 100 years: test
  particles to 3 × 10⁻⁶ relative, Jupiter to 1.4 × 10⁻⁴, a phase drift that
  grows linearly with time), with energy errors of the same size (about 10⁻⁶,
  bounded). Their results are compared statistically (`tools/compare_stats.py`).

## Measurements (2026-10-19, RTX 5080 Laptop GPU, CUDA 13.4, test case of Brown & Batygin 2021)

Accuracy against IAS15 (REBOUND's adaptive 15th-order integrator), planets after
1,000 years, distance in au:

| | Jupiter | Saturn | Uranus | Neptune | Planet Nine |
|---|---|---|---|---|---|
| REBOUND WHFast (DH, dt = 0.5 yr) | 2.58e-3 | 7.44e-3 | 2.10e-3 | 4.65e-4 | 2.49e-5 |
| p9gpu kick-drift-kick (feb930b) | 4.97e-3 | 1.49e-2 | 4.18e-3 | 9.18e-4 | 4.95e-5 |
| p9gpu drift-kick-drift (ce19c2d) | 2.58e-3 | 7.44e-3 | 2.10e-3 | 4.65e-4 | 2.49e-5 |

Relative energy error of the massive bodies, control job (100,000 years):
REBOUND −4.802e-7, p9gpu −4.802e-7.

Speed (job of 10,000 years = 20,000 steps; wall time; the machine's CPU cores
were busy with the REBOUND long run, which also limits the laptop GPU's power):

| Test particles | REBOUND, 1 core | p9gpu CPU build, 1 core | p9gpu GPU | particle-steps/s on the GPU |
|---|---|---|---|---|
| 4,000 | 13.6 s | 11.3 s | 0.317 s | 2.5e8 |
| 20,000 | – | – | 0.95 s | 4.2e8 |

Long runs, all 4,000 test particles, 300 Myr, 600 million steps, one snapshot
per Myr (110 MB): kick-drift-kick 3.46 h (with a busy-waiting CPU core, fixed
since), drift-kick-drift 2.73 h (110 Myr per hour; the host used 5.8 % of one
core). The REBOUND long run of the same particles needed 16 CPU cores for about
45 Myr per hour.

Statistics against REBOUND (`tools/compare_stats.py`, barycentric elements,
`runs/compare-*.txt`): at 2, 20, 50, 100, 150, 200, 250 and 300 Myr the number
of survivors, the distributions of a, q and i (Kolmogorov-Smirnov p ≥ 0.18), and
the clustering of Δϖ and ΔΩ of the distant particles (R and mean direction;
KS p ≥ 0.08) agree. Example at 300 Myr: survivors 2,695 (REBOUND) and 2,672
(p9gpu); Δϖ R = 0.38 / 0.40, mean 200.0° / 199.0°; ΔΩ R = 0.73 / 0.72, mean
357.5° / 359.5°. Single orbits diverge (median relative difference in a about
10 % after 100 Myr; chaotic encounters with Neptune), as expected.

## Build

```sh
python3 -m venv build/cuda-venv
build/cuda-venv/bin/pip install nvidia-cuda-nvcc==13.4.92 nvidia-cuda-runtime==13.4.92
make gpu          # build/gpu/p9gpu (CUDA, sm_120 and PTX for compute_75)
make gpu-cpu      # build/gpu-cpu/p9gpu (no CUDA; the reference)
LD_LIBRARY_PATH=/usr/lib/wsl/lib build/gpu/p9gpu run in.sa 1e6 10 out.sa   # WSL: libcuda from the Windows driver
```
