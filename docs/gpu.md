# GPU integrators for test particles: checked 2026-10-18

## GLISSE

- Paper: Zhang & Gladman, "GLISSE: A GPU-optimized planetary system integrator
  with application to orbital stability calculations", New Astronomy 90 (2022)
  101659, doi:10.1016/j.newast.2021.101659, arXiv:2011.03484. Wisdom-Holman for
  test particles on CUDA, about 100 times faster than the same code on one CPU core
  (paper); no close-encounter handling (particles near a planet are removed, as in
  p9sim).
- Source: the only public code is https://github.com/skkestrel/glisse (C++/CUDA,
  last change 2020-12-02; archive of `master` sha256
  `d1bbf9615fe555a92d941d5a995d071834011b4844fcc7ed841216d7dda37cb1`). The paper
  itself names no repository.
- **Licence: none.** No LICENSE file, no licence header in the sources, GitHub
  detects none. Without a licence there is no right to use, modify or distribute
  the code. **It was therefore not built and not run.** Needed: a licence from the
  authors (K. Zhang, B. Gladman), ideally a GPL-compatible one, since p9sim is
  GPL-3.0-or-later through REBOUND.
- Technically: CUDA, Makefile for sm_35 (Kepler); would need CUDA ≥ 12.8 and sm_120
  for the GPU here (RTX 5080 Laptop GPU, 16 GB, Blackwell). No CUDA toolkit is
  installed (no root); it can be installed without root from NVIDIA's pip packages.

## GENGA (alternative)

- Grimm & Stadel 2014, https://bitbucket.org/sigrimm/genga (CUDA, also HIP and a
  CPU version; active, last change 2026-04-22). Hybrid symplectic integrator with
  close encounters, test particles supported.
- Licence: no licence file; the documentation says "GENGA is free to use, but when
  results from GENGA are published, then the following paper has to be
  referenced". That allows use, but says nothing about modifying or redistributing;
  it is not an open-source licence. Before integrating: clarify with the author.

## Reproducibility on GPUs

- NVIDIA GPUs compute IEEE-754 binary64 with correctly rounded + − × ÷ and sqrt
  (CUDA's default `-prec-div=true -prec-sqrt=true`), but nvcc contracts a·b+c into
  FMA by default (`--fmad=true`). With `--fmad=false` and the same operation order
  as the CPU code, bit-identical results are possible in principle; GPU and CPU
  results then still differ if the code orders sums differently (parallel
  reductions). For test particles each particle is independent, so no reduction
  is needed for them.
- Consequence: a GPU integrator would have to be checked like p9sim (same jobs,
  same canonical state hash), and its results compared statistically with REBOUND
  if it uses a different scheme.

## Estimate for this machine

The laptop GPU computes double precision at 1/64 of its single precision rate:
about 0.4–0.5 TFLOPS FP64 (7,680 CUDA cores, up to 3.09 GHz, 105 W), similar to
the GTX 1080 Ti used for GLISSE. The paper's factor of about 100 per CPU core is
therefore a reasonable upper end here; with p9sim's CPU core at about 0.11 µs per
particle and step, a range of 30–100 CPU cores per GPU is a cautious estimate (not
measured). A data-centre GPU with full FP64 (e.g. NVIDIA H100, about 30 times the
FP64 rate) would be far faster.
