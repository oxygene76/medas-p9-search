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

## Design

- Coordinates: positions relative to the Sun, barycentric velocities
  (democratic heliocentric). One step of length dt: kick dt/2 (planets acting
  on the body) – jump dt/2 (velocity w = Σ m_j u_j / m_Sun of the planets) –
  Kepler drift dt around G m_Sun – jump dt/2 (w after the planets' drift) –
  kick dt/2 with the planets' positions at the end of the step
  (`gpu/whdh.h`).
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

## Build

```sh
python3 -m venv build/cuda-venv
build/cuda-venv/bin/pip install nvidia-cuda-nvcc==13.4.92 nvidia-cuda-runtime==13.4.92
make gpu          # build/gpu/p9gpu (CUDA, sm_120 and PTX for compute_75)
make gpu-cpu      # build/gpu-cpu/p9gpu (no CUDA; the reference)
LD_LIBRARY_PATH=/usr/lib/wsl/lib build/gpu/p9gpu run in.sa 1e6 10 out.sa   # WSL: libcuda from the Windows driver
```
