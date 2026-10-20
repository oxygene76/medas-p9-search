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
| Jacobi constant (restricted three-body problem: Sun, Neptune on a circular orbit, 256 Neptune crossers, 10 Myr; `tools/jacobi_test.py`) | must not grow systematically | median \|dC/C\| 1.1e-8 (1 Myr) to 4.5e-8 (10 Myr), growing as t^0.55 (a random walk), maximum 2.9e-6; hard switch: 3.4e-6, t^0.90, maximum 5.5e-4 (at 10 Myr the smooth transition is 75 times smaller in the median, 190 times in the maximum); fixed step: 1.2e-2, t^2.0, 37 particles lost (smooth: 4, all numerical, at the cap of 4,096 sub-steps, see below) |
| 3. MERCURIUS over 200 Myr | `docs/validation-smooth-200myr.md` | running |
| 5. speed | reported | Jacobi test (encounter-heavy): 1,130 s against 283 s with the fixed step; the real case: to be measured |

### The cap of 4,096 sub-steps and the 4 losses of the Jacobi test

Checked 2026-10-20 (question of the project lead: are the 4 losses real
ejections; where are the 4,082 steps at the cap).

**The 4 losses are numerical, not real ejections.** All 4 particles were
removed by the distance rule (10,000 au) within 500–5,000 yr of one flyby of
Neptune. Their |dC/C| stayed at 2e-8 to 2e-7 up to the snapshot just before
that flyby and jumped in that one flyby (`runs/jacobi-lost`: the 4 particles
alone, same bits as in the full run, a snapshot every 500 yr):

| particle | \|dC/C\| before the flyby | after | pericentre (IAS15) | heliocentric orbit after |
|---|---|---|---|---|
| 57 | 1.7e-8 | 0.97 | 2.25e-4 au = 1.36 R_N | hyperbolic, a = −8.4 au |
| 59 | 7.0e-8 | 9.1 | 9.4e-5 au = 0.57 R_N | hyperbolic, a = −1.1 au |
| 147 | 3.3e-8 | 0.32 | 2.61e-4 au = 1.58 R_N | hyperbolic, a = −33 au |
| 234 | 2.3e-7 | 58 | 2.0e-5 au = 0.12 R_N | hyperbolic, a = −0.2 au (about 70 km/s) |

(R_N = 24,764 km = 1.655e-4 au. In this test C is conserved exactly, so at
best Neptune can just unbind a particle; speeds like these are impossible.)
In all 4 flybys the steps through the pericentre were at the cap. Counter-test
(`tools/deep_flyby_test.py`, `runs/jacobi-lost/deep`): each particle restarted
1,500 steps before the flyby, run over 5,500 steps. With the cap of 4,096,
the same jumps (0.97, 0.32; 59 and 234 removed again). With a cap of 2^21
(experimental build, `-DP9_SUB_MAX=2097152`), |dC/C| stays at 7e-9, 9e-10,
9e-8 and 2e-9, and the position at the end agrees with IAS15 (to 0.3 au after
the deepest flyby, otherwise to 0.1 au). Particles 59 and 234 pass inside
Neptune: physically collisions. 57 and 147 graze it at 1.4 and 1.6 radii:
physically they survive.

**Where the 4,082 capped steps are** (`P9_CAPPED_OUT`, CPU, the same bits:
the run again gave result 0bb5ae67…; `tools/capped_report.py`,
`runs/jacobi-capped`):

- 2,364 steps (804 flybys) at the edge of r_out (about 3 au, outside
  Neptune's Hill radius of 0.78 au). There the two-body pericentre around
  Neptune is tiny, but the Sun's pull still changes the orbit around the
  planet, and the particle does not come within 0.1 au in a capped step. These
  steps only cost sub-steps; their errors are not measurable.
- 1,718 steps in 75 deep flybys (a capped step within 0.1 au), by pericentre:
  2 inside Neptune, 2 at 1–2 radii, 3 at 2–5, 4 at 5–10, 15 at 10–20, 29 at
  20–50, 20 beyond 50 radii. The 4 losses are exactly the 4 below 2 radii.
  Of the three at 2–5 radii, particles 39 and 205 (3.7 radii) changed |dC/C|
  by 3e-6 (the run's maximum of 2.9e-6), particle 101 (5.0 radii) by 5e-9;
  the four at 5–10 radii by at most 4e-8 (snapshots before and after).

Without the cap, n would have to reach 2^20 (Jupiter, Saturn, Uranus) or 2^21
(Neptune, Planet Nine with 6.2 Earth masses and 2.6 Earth radii) for a
flyby at the physical radius, by the same criteria (32 sub-steps per flyby,
656 per orbit around the planet).

Experiment with a cap of 2^21 (`runs/jacobi-cap21`, not a production build):
256 of 256 particles remain; |dC/C| median 3.8e-8 at 10 Myr, maximum
3.9e-7 (with the cap of 4,096: 4.5e-8, 2.9e-6, 4 lost), growth t^0.51.
The sub-steps in steps above 4,096 rise from 1.7e7 to 2.1e8 (mostly the edge
flybys). CPU time 660 s against 613 s (one core). This run had no flyby
inside Neptune; one would again be integrated as a point mass with too few
sub-steps.

**Proposal:** for the production runs, (1) a collision
with the physical radius of a planet ends the test particle, as in MERCURY
(at a sub-step's kick closer than the radius; fate `collision:<planet>`),
and (2) the cap raised to 2^21, so that every flyby outside the radius gets
the sub-steps that the criteria ask for. Both change the bits of capped steps
only. The running 200-Myr comparison (cap 4,096) stays as it is.

### Decision and the new version (2026-10-20)

Decision of the project lead: both, for the production runs; first the false
alarms at the edge of r_out are removed (else the higher cap costs time on the
GPU for nothing); then regression, close (down to 0.02 au, plus flybys at 0.5
to 5 planet radii), grid, bits GPU = CPU = WebAssembly and the Jacobi test
again; `P9_CAPPED_OUT` stays as a counter, plus the collisions per planet. The
running 200-Myr comparison stays the acceptance of the smooth transition and
is evaluated as committed; the two changes concern only rare steps at the cap
and are accepted with these tests. If the comparison fails, `P9_CAPPED_OUT`
shows whether steps at the cap cause it, and the comparison is repeated with
the new version.

Implementation (`gpu/whdh.h` p9_step_tp_smooth, the same in `gpu/whdh_t.h`,
GPU, CPU twin and WebAssembly; `tools/p9job.py`):

- **The cap 2^21 only near the pericentre** (v5, 79c16e2). n comes, as in
  the accepted version, from the two-body pericentre estimate in every step;
  only the cap depends on the step: up to 2^21 if the step is near the
  pericentre, else 4,096 as before (the false alarms at the edge of r_out stay
  at 4,096 and cost no more than before). Near: the straight line's time to
  its closest approach |r·v|/v² or the fall time sqrt(r³/μ) is at most 2 dt,
  before or after the pericentre, or the particle is bound to the planet with
  half a period π sqrt(a³/μ) of at most 2 dt. Only + − × ÷ and sqrt, compared
  without roots (|r·v| ≤ 2 dt v², r³ ≤ 4 dt² μ, π² a³ ≤ 4 dt² μ). The factor
  2: against the exact two-body time to the pericentre (Jupiter, Neptune,
  Planet Nine; distances 3e-5 to 5 au, speeds 0.003 to 10 au/yr; about 9e5
  approaching states with the pericentre within the step), factor 2 missed
  none, 1.5 missed 9, 1 missed 843.
- **How it got there** (all on this branch, tests in `runs/accept-v*`):
  - v2 (c7fccfb), as asked: without the pericentre in the step, n from the
    step's smallest distance (straight line, m² halved as the planet's pull
    brings the particle up to 1/0.68 closer, speed from the energy).
    Regression, close, grid passed; the Jacobi test failed: median |dC/C|
    3.3e-6 at 10 Myr, t^0.92 (accepted version 4.5e-8, t^0.55).
  - v3 (aa0eda7): n from the estimate, the cap 2^21 only with the pericentre
    ahead in the step. Jacobi 4.7e-8, t^0.56; but a step that starts at the
    pericentre (receding) got 4,096: close test at phase 0.5, 1.1 to 3 Neptune
    radii, kick off by up to a factor 9.
  - v4 (a9ea1f1): v3 plus, without the pericentre, at least what the step's
    smallest distance asks for. Close right again, Jacobi drifted again
    (3.3e-6, t^0.94).
  - So it is not the number of sub-steps but their change from step to step:
    the pericentre estimate stays nearly constant along a flyby, the step's
    distance does not, and an n that jumps within a flyby leaves the
    leapfrog's errors uncancelled (as with the hard switch). v5: the estimate
    alone, the window around the pericentre symmetric. Jacobi 5.1e-8, t^0.56,
    maximum 4.6e-7, 2 collisions with Neptune, none lost
    (`runs/jacobi-v5`); close at 1.1 to 3 Neptune radii 1 ± 2.2e-3.
- **Collision**: closer to a planet than its physical radius at a sub-step's
  kick: the particle is removed, fate `collision:<id>`, counted per planet
  (`collisions=` in the result line, `collisions` in result.json). The kicks
  are at most v dt/n apart, at 2^21 sub-steps under 3e-6 au, far below the
  radii.
- **Cap 2^21** for the smooth transition (`P9_SMOOTH_MAX`); the hard switch
  keeps 4,096. 2^21 is what the criteria ask for at the physical radius of
  Neptune and Planet Nine (2^20 for Jupiter, Saturn, Uranus).

Physical radii (`tools/p9job.py` PHYSICAL_RADII_KM, written into the job as
params.removal.encounter.collision with their source; `--no-collision` leaves
them out):

| planet | radius | source |
|---|---|---|
| Jupiter | 71,492 km = 4.7789e-4 au | equatorial radius at 1 bar, IAU WGCCRE 2015 (Archinal et al. 2018, Celest. Mech. Dyn. Astron. 130, 22) |
| Saturn | 60,268 km = 4.0287e-4 au | same |
| Uranus | 25,559 km = 1.7085e-4 au | same |
| Neptune | 24,764 km = 1.6554e-4 au | same |
| Planet Nine | 16,565 km = 1.1073e-4 au | **assumption**, not a measurement: 2.6 Earth radii (6,371.0 km) for 6.2 Earth masses |

Results of v5 (`runs/accept-v5`, 79c16e2; the decision of the project lead:
v5 runs the ensemble if all of these pass):

| test | criterion | result |
|---|---|---|
| regression, the 32 numerical losses | kick ± 5 %, no false loss | 32 of 32 (0.9815 to 1.0327) |
| close, Neptune and Planet Nine, 0.02–0.78 / 0.02–7 au | medians 1 ± 0.01, all 1 ± 0.05, none spuriously unbound | worst 4e-4 (both), medians 1 ± 1e-4, none unbound |
| close at 0.5–5 planet radii (10 geometries × 2 speeds × 8 phases per row) | inside the radius a collision, outside none; outside the kick criteria above | no wrong outcome (Neptune, Planet Nine); outside worst 8.9e-3 (Neptune), 3e-4 (Planet Nine), medians 1 ± 1e-4 |
| grid, both presets | ≤ 1e-3 in every cell | worst cell 4.0e-4 (Neptune), 8.1e-4 (Planet Nine) |
| bits | CPU = WebAssembly, GPU = CPU, df64 GPU = CPU twin, double-t = double | 36 of 36 cases each (the 32 regression cases, the 4 deep flybys up to n = 2^21 with collisions) |
| Jacobi constant | no systematic growth; GPU = CPU | median 5.1e-8 at 10 Myr, t^0.56, maximum 4.6e-7; 2 collisions, none lost; GPU hash: see `runs/val/ens-gpu/run.log` |

### The number of sub-steps must stay constant within a flyby

Found 2026-10-20 with the versions of the decision above. The Jacobi test
(Sun, Neptune on a circular orbit, 256 Neptune crossers, 10 Myr,
`tools/jacobi_test.py`; C is conserved exactly) for every version:

| version | n of the near part | median \|dC/C\| at 10 Myr | maximum | growth of the median | lost / collisions |
|---|---|---|---|---|---|
| fixed step | none (no sub-steps) | 1.2e-2 | – | t^2.0 | 37 lost |
| hard switch (`substep`) | sub-steps only inside the trigger radius | 3.4e-6 | 5.5e-4 | t^0.90 | – |
| v1, accepted (47127ba) | from the pericentre estimate, cap 4,096 | 4.5e-8 | 2.9e-6 | t^0.55 | 4 lost (numerical, at the cap) |
| v1 with cap 2^21 (experiment) | the same, cap 2^21 | 3.8e-8 | 3.9e-7 | t^0.51 | none |
| v2 (c7fccfb) | estimate only with the pericentre ahead in the step, else the step's smallest distance | 3.3e-6 | 3.0e-5 | t^0.92 | 1 lost (a real ejection) |
| v3 (aa0eda7) | estimate; cap 2^21 only with the pericentre ahead in the step | 4.7e-8 | 4.6e-7 | t^0.56 | 2 collisions |
| v4 (a9ea1f1) | v3, plus at least what the step's smallest distance asks for | 3.3e-6 | 1.8e-5 | t^0.94 | 1 collision |
| v5 (79c16e2) | estimate; cap 2^21 near the pericentre (before or after it) | 5.1e-8 | 4.6e-7 | t^0.56 | 2 collisions |

v4 has at least as many sub-steps as v3 in every step and yet drifts like the
hard switch: more sub-steps do not help, their change does. The two-body
pericentre estimate (distance and speed at the pericentre of the orbit around
the planet) is nearly constant along a flyby, so n is too; the step's
smallest distance changes from step to step, and n with it, by powers of two.
Each step's leapfrog in the near part leaves an error of the order of its
sub-step squared; with the same n in successive steps these errors largely
cancel (the composition of identical symmetric steps), with changing n they
do not and add up, as in the hard switch, whose abrupt change of the step at
the trigger radius left an error of the order of the planet's perturbation.

Rule for any change to the choice of n: **n may depend only on quantities that
are (nearly) conserved during a flyby** (the pericentre estimate, the
planetocentric energy and angular momentum), not on the particle's current
distance or the step's phase. A cap may depend on the phase (v5: near the
pericentre or not), because it only binds where the estimate asks for more
than 4,096, and then in all steps around the pericentre alike. Any change is
checked with the Jacobi test, besides the kick tests (regression, close,
grid), which do not see this drift: v2 and v4 passed all of those.
