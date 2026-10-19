# Related work: GPU integrators for test particles

Searched and checked on 2026-10-18/19. Licences as found in the repositories
and on the authors' pages; "not documented" means that neither the paper nor
the repository says so, as far as checked here.

| Code | What | Test particles | Code available | Licence | Bitwise reproducible CPU / GPU / WebAssembly |
|---|---|---|---|---|---|
| **GLISSE** (Zhang & Gladman 2022, New Astron. 90, 101659; arXiv:2011.03484) | Wisdom-Holman (MVS) for test particles on CUDA, planets computed ahead in blocks on the CPU, particles near planets removed; about 100× one CPU core (paper) | yes, the purpose | https://github.com/skkestrel/glisse (last change 2020-12) | **none** (no licence file, no headers): no right to use or modify | not documented |
| **GENGA** (Grimm & Stadel 2014, ApJ 796, 23; Grimm et al. 2022, ApJ 932, 124) | hybrid symplectic integrator with close encounters, CUDA (also HIP and a CPU version); modes for up to 2048 massive bodies, up to a million test particles, or many small systems | yes | https://bitbucket.org/sigrimm/genga (active, 2026) | no licence file; documentation: "free to use, but when results from GENGA are published, then the following paper has to be referenced" (no terms for modifying or redistributing) | not documented |
| **QYMSYM** (Moore & Quillen 2011, New Astron. 16, 445; arXiv:1007.3458; ascl:1210.028) | hybrid symplectic (switches to Hermite in close encounters), CUDA; meant as a parallel mercury6 | massless particles possible ("will never collide") | https://astro.pas.rochester.edu/~aquillen/qymsym/ (version 0.1) | "nonexclusive, royalty-free license to use this code" (no terms for modifying or redistributing); contains modified routines of NVIDIA's CUDA SDK 1.1 (parallel reduction and n-body) | not documented; uses parallel reductions |
| **Swarm-NG** (Dindar et al. 2013, New Astron. 23, 6; arXiv:1208.1157) | CUDA library for integrating many small n-body systems in parallel (ensembles) | not its focus | https://github.com/AstroGPU/swarm (last change 2014) | no licence file in the repository root; GitHub detects none | not documented |
| GPU VOVS Adams integrator (Sharp & Newman 2016, J. Comput. Sci. 16, 89) | variable-order, variable-step Adams method on GPUs for the Solar System near limiting precision | yes | no public code found | – | not documented |
| **Swiftest** (Wishard et al. 2023, JOSS 8, 5409) | WHM, RMVS (test particles with close encounters), HELIO, SyMBA; modern Fortran with OpenMP | yes (RMVS) | https://github.com/MintonGroup/swiftest | GPL-3.0 | CPU only (no GPU version found) |
| **REBOUND** (Rein & Liu 2012; WHFast: Rein & Tamayo 2015) | many integrators (WHFast, IAS15, MERCURIUS, TRACE, …), CPU; WHFast512 with AVX-512 | yes | https://github.com/hannorein/rebound | GPL-3.0-or-later | bit-by-bit reproducibility of runs with the SimulationArchive (Rein & Tamayo 2017, MNRAS 467, 2377); the paper names compilers, libraries and hardware as the source of differences and does not claim it across them. No GPU version |

## Where p9gpu stands

- Written from published methods (docs/gpu-integrator.md), GPL-3.0-or-later.
- Bitwise identical results on the CPU and the GPU (same code, `--fmad=false`,
  no atomics or reductions), and the CPU build of p9sim gives the same bits with
  gcc and clang at -O2 and -O3, on x86-64 and ARM64 and in WebAssembly
  (docs/reproducibility.md). We found no other GPU code for test particles that
  documents bitwise reproducibility between CPU, GPU and WebAssembly. p9gpu's
  integrator built as WebAssembly (`make gpu-wasm`, run in Node) gives the same
  hash as on the GPU and on the CPU (control job, `9231ae16…`, 2026-10-19).

## Sources

- GLISSE: https://ar5iv.labs.arxiv.org/html/2011.03484
- GENGA: https://arxiv.org/abs/1404.2324, https://iopscience.iop.org/article/10.3847/1538-4357/ac6dd2,
  documentation at https://bitbucket.org/sigrimm/genga (Documentation.md, section "License")
- QYMSYM: https://arxiv.org/abs/1007.3458, https://astro.pas.rochester.edu/~aquillen/qymsym/00README (section "Copyright notices")
- Swarm-NG: https://arxiv.org/abs/1208.1157
- VOVS Adams: https://www.sciencedirect.com/science/article/abs/pii/S1877750316300412
- Swiftest: https://www.theoj.org/joss-papers/joss.05409/10.21105.joss.05409.pdf
- REBOUND SimulationArchive: https://arxiv.org/abs/1701.07423
