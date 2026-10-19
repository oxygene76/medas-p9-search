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
- The radii are part of the job description, by planet name
  (`params.removal.encounter.radii_au`, and `body_ids`: the id of each named
  body in the start file), so the criterion is fixed by the job and covered by
  its id. `tools/p9job.py run` hands them to the program in
  `P9_ENCOUNTER_RADII` as `id=radius` pairs (exact decimals); the programs
  assign each radius to the body with that id, whatever the order, square the
  radii and compare squared distances (no cube root or other libm function on
  the running machine). Parsing: `src/p9encounter.c`, shared by both programs;
  it rejects a list without ids, an unknown id, a body named twice and a body
  left out. (Ids, not names, because REBOUND's names do not survive an archive
  read on 32-bit WebAssembly; the ids are stored with every body.)
- The programs print the radii they use (`encounter_radius id=… au=…`);
  `p9job run` checks them against the job by name and stores them in
  result.json (`encounter_radii_used_au`). A difference stops the run.
- Results: `removed_encounter` in the result line and in result.json.
- Tests: `make test` (`tests/test_encounter.c`, `tests/test_p9job.py`, the
  latter also end to end with both programs on a small job). Rebuilding the old
  error into `p9job.py` makes four of the tests fail.

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

## Error: radii in the wrong order (2026-10-19, fixed)

From d598a04 until the fix, `p9job run` passed the radii as a plain list in
the order in which they stood in job.json, which is written with sorted keys
(Jupiter, Neptune, P9, Saturn, Uranus), while the programs took the list in
the order of the bodies (Jupiter, Saturn, Uranus, Neptune, P9). Every run with
the criterion therefore used:

| Body | used (au) | intended (au) |
|---|---|---|
| Jupiter | 0.3552 | 0.3552 |
| Saturn | 0.7759 | 0.4374 |
| Uranus | 6.9836 | 0.4672 |
| Neptune | 0.4374 | 0.7759 |
| Planet Nine | 0.4672 | 6.9836 |

Both programs got the same wrong list, so their agreement (the check above,
the scaling runs) and the bitwise reproducibility are unaffected, and run
times are comparable; but the removals are not those of the intended
criterion: too many near Uranus, almost none near Planet Nine. Affected, all
in `runs/` (not published anywhere):

- `enc-test` (the check above), `ctest-gpu` (campaign test, 520,000 years);
- the scaling runs `scale/gpu-*`, `scale/sweep-*`, `scale/cpu-*` (run times
  valid; numbers of survivors and removals not);
- the 4-Gyr GPU run of 2026-10-19 (stopped at 260 Myr, kept as
  `gpu-4gyr-invalid-radii-order`, not used).

Not affected (no encounter criterion): the REBOUND pilot run of 18/19 October,
the GPU comparison runs `gpu-long*`, the reproducibility matrix and the check
package. Jobs made before the fix are refused by `p9job run` (radii without
body ids).

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
