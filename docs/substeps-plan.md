# Sub-steps for too short flybys (plan, not implemented)

Prepared 2026-10-19 for the decision of 2026-10-20; implementation only after
the project lead's OK. Goal: follow close
encounters correctly instead of removing them or integrating them with the
fixed step. Only the particle concerned computes the step in sub-steps, so
that its flyby lasts at least about four sub-steps; the planets' positions in
the sub-steps are interpolated. Method as RMVS in SWIFT (Levison & Duncan 1994,
Icarus 108, 18), written from the paper (as p9gpu itself), not from SWIFT's
code.

## What changes

1. **Trigger: the predicted closest distance within the step**, not the
   distances at the step points, so that no flyby slips through between two
   of them. Linear approximation from relative position d and relative
   velocity w (planet minus particle): d(τ) = d + w τ, closest at
   τ* = −(d·w)/(w·w), clipped to the step's interval. The decision is a
   comparison of squared distances: sub-steps if |d + w τ*|² < r_sub², and,
   for the number of sub-steps, |d + w τ*|² < (4 |w| dt / n)² (the flyby lasts
   fewer than 4 sub-steps of dt/n). No square root, no division other than
   the one for τ*, so CPU and GPU decide identically. The decision comes
   before the step: at the kick of step k the prediction covers step k+1
   (τ in [dt/2, 3dt/2] after this kick); a particle whose closest approach
   falls into the current step's second half is caught by the same test one
   step earlier. r_sub per planet: the outer zone (a few Hill radii; for
   Planet Nine at least 1.5 v99 dt). Deterministic, from + − × ÷ only.
2. **The marked step** (only that particle): n sub-steps of dt/n, n from
   d_min / (|w| dt) so that the flyby lasts ≥ 4 sub-steps (n a power of two up
   to a limit, e.g. 256; chosen with comparisons only, no log or pow).
   - Planets in the sub-steps: their heliocentric positions and velocities at
     the kick (the table already holds both) drifted with the Sun's Kepler
     solution over the sub-step offsets (RMVS: planets on two-body orbits
     during the step), the same p9_kepler code.
   - Outer zone (a few Hill radii): the usual democratic heliocentric
     drift–kick–drift with the shorter step.
   - Inner zone (inside a fraction of the Hill radius, below about 0.1 au for
     Neptune where the fixed step fails by factors of 100): RMVS's split
     around the planet, a Kepler drift around the planet with the Sun as the
     perturbation, so that even 0.02 au is resolved.
   - The jump terms (Sun's barycentric motion) are applied per sub-step from
     the interpolated planet velocities.
3. **Removal** stays only by the distance rules; a particle that collides
   with a planet (inside its physical radius) is removed (new, for completeness).

## Effort

About 2–3 working days: whdh.h (prediction, sub-step loop, planetocentric
inner zone, planet interpolation), the same code in the kernel and the CPU
twin, unit tests; then the checks below. Code size: about 200–300 lines in
whdh.h, little in kernel.cu and p9gpu.c. Speed: only marked particles
sub-step. With the flyby counts of the runs without removal (to be read from
`flybys.tsv` tonight) the share of marked steps can be estimated; on a GPU a
sub-stepping thread holds back its warp (32 particles) for that step, so the
cost is about (marked steps per particle-step) × 32 × n. If marked steps are
of order 1e-6 of all particle-steps, the slowdown is a few per cent.

## Bitwise equality CPU / GPU

Not affected in principle: the decision, n, the interpolation and the inner
Kepler solution are all computed with the same code from correctly rounded
+ − × ÷ and √ (no log, pow, exp; n from comparisons), so CPU, GPU and
WebAssembly give the same bits, as now. Data-dependent loop lengths change
only the run time. To be shown again with the reproducibility jobs and a job
with many encounters (control in the GPU check package).

## Test plan

1. **flyby_check close down to 0.02 au** (port of the "close" mode to p9gpu,
   like `tools/flyby_p9gpu.py`): Neptune, v_rel 0.6 and 1.0 au/yr, dt 0.5 yr,
   d_min 0.02–0.78 au, 8 phases × 10 geometries: median kick ratio within
   1 ± 0.01 and all ratios within 1 ± 0.05 for every d_min, no spurious
   unbinding. **The same for Planet Nine** (preset p9: d_min 0.02–7 au,
   v_rel 0.2–0.5 au/yr, dt 0.5 yr, and the speeds up to v99), with the same
   limits.
   Plus a trigger test: flybys whose closest approach lies exactly between
   two step points (phase 0.5 of the grid) at the highest speeds must be
   sub-stepped, for Neptune and Planet Nine.
2. **flyby_check run**: error relative to the kick ≤ 1e-3 in every cell of
   both presets at dt = 0.5 yr, including the cells below 1.5 steps per flyby
   (now 2e-3 … 1e+0).
3. **MERCURIUS**: the 2,000 test particles over 50 and 200 Myr with the
   criteria of `docs/validation-mercurius-200myr.md`, and additionally the
   same losses particle by particle where the trajectories have not yet
   diverged (first Myr), McNemar p ≥ 0.05 throughout.
4. **Bits**: GPU = CPU twin = WebAssembly on a control job with close
   encounters; the jobs of the GPU check package.
5. **Speed**: the 64,000-particle benchmark; slowdown reported.
