# Proposal: the production run (draft of 2026-10-21, not started)

Asked for by the project lead on 2026-10-20 (point 4): start conditions and
removal limits as Brown & Batygin (2021), number of test particles, several
runs bundled in one GPU job, run time on the laptop and on an L40S. Nothing
is started; the decisions are listed at the end.

## Start conditions and removal (as Brown & Batygin 2021)

- **Massive bodies** as in all runs so far (`tools/make_ic.py`): the Sun with
  the inner planets' masses, Jupiter–Neptune from DE440s at JD 2458270.0,
  Planet Nine with the reference values of Brown & Batygin (2021): 6.2 Earth
  masses, a = 380 au, perihelion 300 au, i = 16°.
- **Test particles**: a uniform in 150–500 au, perihelion uniform in
  30–50 au, inclination uniform in 0–25°, the angles uniform
  (`make_ic.py --a-range 150 500 --q-range 30 50 --inc-range 0 25`; so far
  150–550 au and 0–10°).
- **Removal**: closer than 4.5 au to the Sun or beyond 10,000 au (checked
  every 1,000 steps = 500 yr, `--r-in 4.5`; so far 5 au), and a collision
  with a planet's physical radius (method smooth, `tools/p9job.py`
  PHYSICAL_RADII_KM; Planet Nine's 2.6 Earth radii are an assumption).
- The options for the ranges and for 4.5 au are on branch
  `feat/bb2021-setup` (0a5b7f5): with their defaults the start values and all
  test hashes are unchanged (p9sim, p9gpu 36 of 36 cases, `make test`).

## Integrator

p9gpu, Wisdom–Holman in democratic heliocentric coordinates, dt = 0.5 yr,
close encounters with the smooth transition v5 (`docs/substeps-plan.md`;
r_out 4 times the rule's radii, planets with 8 inner steps, at most 2^21
sub-steps near a pericentre), FP64. Its acceptance by the ensemble
(`docs/validation-ensemble-200myr.md`) is due on 2026-10-21. The faster
variant v6 (branch `feat/smooth-prefilter`) gives the same bits; it can
replace v5 in a running job at a segment boundary once its GPU check passed.

## Number of test particles

The measure of interest, the clustering R of the distant particles
(a > 230 au, q > 42 au), has a statistical error of about
SE ≈ 0.55 / √n for n distant survivors (measured: 0.018 at n ≈ 950). For
SE ≈ 0.005, n ≈ 12,000 distant survivors are needed at the end.

How many survive 4 Gyr is not known yet: the 4-Gyr run with the fixed step
(5,000 particles, paused) had 88 % at 100 Myr, 74 % at 200 Myr and 71 % at
240 Myr; about 64 % of the survivors are distant (2,000-particle runs at
200 Myr). With an assumed 20–40 % surviving 4 Gyr, 12,000 distant survivors
need about 50,000–95,000 test particles.

**Proposal: 64,000 test particles**, the size at which the laptop GPU is
saturated (`docs/gpu-performance.md`), in one GPU job (one start file, one
seed). Evaluated in 4 subsets of 16,000 (particles 0–15,999, …): the test
particles do not interact, so the subsets are independent runs, and their
scatter gives the run-to-run error directly, as the ensemble does now.

## Bundling and segments

- One job, 64,000 test particles; members are not needed (independent
  particles are independent runs). Ensemble members (`--members`) only where
  the same particles are wanted with perturbed start values.
- Segments of 500 Myr with `tools/campaign.py` (resume after an interruption,
  as for the 4-Gyr run), a snapshot every 10 Myr.

## Run time

Particle-steps: 64,000 × 8·10^9 steps × the mean fraction still alive
(assumed 0.5) ≈ 2.6·10^14.

| GPU | fixed step (measured) | smooth v5 | smooth v6 | 4 Gyr with v5 | 4 Gyr with v6 |
|---|---|---|---|---|---|
| RTX 5080 Laptop | 4.5e8 /s | (measurement under full load, 2026-10-21) | | | |
| L40S | 9.0e8 /s | estimate 9.0e8 / 1.70 = 5.3e8 /s | 9.0e8 / 1.30 = 6.9e8 /s | ≈ 5.7 days | ≈ 4.4 days |

(The factors 1.70 and 1.30 are the counted FP64 cost per step, `count_ops`;
the measurement on the laptop under full load replaces them there.) df64 on
the L40S was 3 times as fast as FP64 with the fixed step; with the smooth
transition it is implemented, but its check against FP64 is still open.

## Decisions for the project lead

1. Duration (proposed: 4 Gyr) and number of test particles (proposed:
   64,000).
2. Merge `feat/bb2021-setup` (ranges, 4.5 au) for the run.
3. v5 or v6 (same bits; v6 after its GPU check).
4. Where: laptop (with the 4-Gyr comparison run paused or finished) or L40S;
   FP64, or df64 after its check.
