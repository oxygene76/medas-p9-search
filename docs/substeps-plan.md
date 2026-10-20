# Sub-steps for too short flybys (plan, not implemented)

Prepared 2026-10-19; **approved 2026-10-20** by the project lead, with the
additions below. Accepted only when the whole test plan is met. Goal: follow close
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
6. **Regression: the 32 confirmed numerical losses** of
   `docs/validation-mercurius.md` (their states before the flyby are in the
   repository, `tests/data/flyby-regression/`): with sub-steps each must match
   IAS15 (kick within ±5 %, no false loss: unbound only where IAS15 is).
7. After acceptance: df64 with sub-steps again against FP64.

## Implementation and acceptance (2026-10-20)

Implemented as method `smooth` (`gpu/whdh.h` p9_step_tp_smooth; template
p9t_step_tp_smooth for df64), decided by the project lead after the hard switch
(method `substep`, kept for comparison) missed the grid criterion: every
abrupt change of the step length leaves an error of the order of the planet's
perturbation there (the shadow orbit of a Wisdom-Holman step depends on the
step), up to 1e-2 of the small kick of a distant flyby.

- Split as in MERCURIUS: far part s(d) F in the kick at the middle of the step,
  near part (1 - s) F added to the Kepler motion around the Sun, which then runs
  in sub-steps (leapfrog Kepler / near kick). s: the "C5" polynomial of degree
  11 (five vanishing derivatives at both ends; Rein et al. 2019; the infinitely
  smooth function needs exp, not reproducible bit for bit). r_out = 4 times the
  radius rule's radius (Neptune 3.10 au, Planet Nine 2.00 au), r_in = r_out/10:
  the zone 2.8 and 1.8 au wide, more than 2 v99 dt (about 1.0 and 0.5 au).
- In the near part's sub-steps the jump term moves neither the particle nor
  the planets; the planet is taken at its Kepler drift from the kick plus
  a t^2/2 plus h w (derived: the integral of the jump velocity cancels).
- n for the near part: power of two up to 4,096, at least 32 sub-steps per
  flyby and 656 per orbit around the planet (with 8 per flyby and 164 per orbit
  the leapfrog, whose n changes from step to step, left up to 4e-3 of the kick);
  distance and speed at the pericentre of the two-body orbit around the planet
  where focusing brings it closer than the straight line.
- The planets take 8 inner steps per step (`planet_substeps`): their own
  0.5-yr integration was off enough to change the kick of flybys below about
  0.05 au by up to 13 %.

Results:

| test | criterion | result |
|---|---|---|
| 1. close, Neptune and Planet Nine, 0.02–0.78 / 0.02–7 au | medians 1 ± 0.01, all 1 ± 0.05, no spurious unbinding | worst ratio off by 4e-4 (both), medians 1 ± 1e-4, none unbound (fixed step: up to factor 170, 34 unbound) |
| 2. flyby grid, both presets, dt 0.5 yr | ≤ 1e-3 in every cell | worst cell 4.0e-4 (Neptune), 8.1e-4 (Planet Nine) |
| 6. the 32 numerical losses | kick ± 5 %, no false loss | all 32 (largest deviation 3.3 %, case 1673 at 0.0102 au) |
| 4. bits | GPU = CPU = WebAssembly | 32 of 32 cases GPU = CPU twin; WebAssembly = native (4 cases, up to n = 4,096); df64 GPU = CPU twin; double-t = double |
| Jacobi constant (restricted three-body problem: Sun, Neptune on a circular orbit, 256 Neptune crossers, 10 Myr; `tools/jacobi_test.py`) | must not grow systematically | median \|dC/C\| 1.1e-8 (1 Myr) to 4.5e-8 (10 Myr), growing as t^0.55 (a random walk), maximum 2.9e-6; hard switch: 3.4e-6, t^0.90; fixed step: 1.2e-2, t^2.0, 37 particles lost (smooth: 4) |
| 3. MERCURIUS over 200 Myr | `docs/validation-smooth-200myr.md` | running |
| 5. speed | reported | Jacobi test (encounter-heavy): 1,130 s against 283 s with the fixed step; the real case: to be measured |

The cap n = 4,096 was reached in 4,082 steps of the Jacobi test (the deepest
flybys); its errors stay at the level above.
