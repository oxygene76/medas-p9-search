# Close encounters of test particles with planets

Both integrators of this repository split each step into Kepler motion around
the Sun and kicks by the planets (Wisdom-Holman, democratic heliocentric
coordinates, dt = 0.5 yr). Neither resolves a close encounter with a planet:
there the planet's pull dominates and the step is far too long for the orbit
around the planet. Instead of following such particles with wrong orbits, both
remove them by the same criterion.

## The criterion (since commit d598a04, 2026-10-19)

A test particle is removed when, **at the kick of a step**, it is **closer to a
planet than that planet's encounter radius**.

- "At the kick": the positions in the middle of the step, after the first
  Kepler half step and the first jump (drift–kick–drift order). In p9gpu this
  is the distance computed for the kick itself (`p9_kick_tp` in `gpu/whdh.h`);
  in p9sim REBOUND calls `additional_forces` at exactly this point of its WHFast
  step (`encounter_check` in `src/p9sim.c`, which only marks particles; the
  heartbeat removes them after the step). Checked at every step.
- Encounter radius: one Hill radius, R_H = a (m / 3 M_Sun)^(1/3), from the
  heliocentric osculating semi-major axis of the start values, rounded to
  1e-4 au. For the test case: Jupiter 0.3552, Saturn 0.4374, Uranus 0.4672,
  Neptune 0.7759, Planet Nine 6.9836 au.
- The radii are part of the job description
  (`params.removal.encounter.radii_au`), so the criterion is fixed by the job
  and covered by its id. `tools/p9job.py run` hands them to the program in
  `P9_ENCOUNTER_RADII` as exact decimals; the programs square them and compare
  squared distances (no cube root or other libm function on the running
  machine). Parsing: `src/p9encounter.c`, shared by both programs.
- Results: `removed_encounter` in the result line and in result.json.

The other removal rule is unchanged: every 1000 steps (counted over the whole
run), a test particle farther than 10,000 au or closer than 5 au to the Sun is
removed (synchronous positions).

## Check

The same job (4,000 test particles, 100,000 years, `runs/enc-test`) with p9sim
and p9gpu: both removed the same three particles by the encounter criterion and
kept the same 4,003 bodies (the orbits have not yet diverged chaotically at that
time). The removals are deterministic in each program; between the two programs
the distances are computed in different coordinates (REBOUND: inertial, p9gpu:
heliocentric), so a particle exactly at a radius could be decided differently by
one rounding; statistically the criterion is the same.

## Earlier runs

The pilot runs of 18/19 October 2026 (`runs/long-20261018`, the GPU comparison
runs `runs/gpu-long*` in the development worktree) used no encounter criterion:
particles were followed through encounters, inaccurately, and only removed by
the distance rules. Both integrators did the same there too, so the statistical
comparison remains valid; new runs use the criterion.

## Why the Hill radius, and why also for Planet Nine

The Hill radius is the usual measure of where a planet's gravity dominates over
the Sun's; GLISSE (Zhang & Gladman 2022) likewise removes particles close to a
planet. For Planet Nine the orbit around it at its Hill radius (about 7 au)
would still be resolved by the time step, but deeper encounters would not; the
same rule for every planet keeps the criterion simple and identical in both
programs. Particles removed this way are counted, so their number can be
reported with every result.
