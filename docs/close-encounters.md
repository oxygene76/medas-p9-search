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
- Encounter radius (since 2026-10-19 evening, see "The radius rule" below):
  Planet Nine r_res = 0.5 au (dt / 0.5 yr)^(2/3); Jupiter to Neptune the
  larger of their Hill radius R_H = a (m / 3 M_Sun)^(1/3) (heliocentric
  osculating a of the start values) and r_res (m / m_P9)^(1/3). Rounded to
  1e-4 au. For the test case with dt = 0.5 yr: Jupiter 1.8575, Saturn 1.2427,
  Uranus 0.6643, Neptune 0.7759 (its Hill radius), Planet Nine 0.5000 au; for
  model j2 (dt = 5 yr): Neptune 3.2579, Planet Nine 2.3208 au.
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

## The radius rule (2026-10-19)

Until the fix of the radius order, every planet's radius was meant to be its
Hill radius. With the correct order that removes, at Planet Nine's 7 au,
about 25 % of the test particles within 10 Myr and most within 300 Myr
(5,000 test particles, 10 Myr: 1,240 removed at Planet Nine, 283 at Neptune,
none at Jupiter to Uranus). Batygin & Brown (2016, AJ 151, 22) removed
particles within one Hill radius of Planet Nine; Brown & Batygin (2021, AJ
162, 219), whose test case this is, integrated with mercury6's hybrid
integrator, which resolves close encounters, and kept such particles. To
follow the scattering by Planet Nine as they did, the radius is no longer the
Hill radius but the distance down to which the time step still resolves the
orbit around the planet:

- At 0.5 au from Planet Nine (6.2 Earth masses) the orbit around it takes
  2 pi sqrt(d^3 / G m) = 82 years, 164 steps of 0.5 years. The same number
  of steps per orbit for any planet and step gives
  r_res = 0.5 au (m / m_P9)^(1/3) (dt / 0.5 yr)^(2/3).
- Planet Nine: r_res (0.5 au at dt = 0.5 yr; 2.32 au at 5 yr, model j2).
- Jupiter to Neptune: the larger of r_res for their mass and their Hill
  radius (for the giant planets r_res is larger, except for Neptune at 0.5 yr).
- The values are in the job (`params.removal.encounter`: `radii_au`, and
  `hill_au`, `resolution_au`, `rule`; `--radius NAME=AU` overrides a value and
  is recorded) and in each program's report (`encounter_radius id=… au=…`).

**Extension (2026-10-19 evening): flybys of at least 1.5 steps.** An
independent check with REBOUND (`flyby_check.py` of the project lead, in the
development worktree: a test body passes a planet at closest distance d_min
with relative speed v_rel; error of the kick in orbital energy and angular
momentum against IAS15, relative to the size of the kick) showed that the
orbit criterion alone is not enough: the error stays at about 4 (dt/T_orb)^2
only while a flyby lasts at least about 1.5–2 steps (d_min / (v_rel dt));
below that it grows to per cent and beyond, whatever the orbital period.
Medians of the error relative to the kick:

| dt | planet, d_min | error |
|---|---|---|
| 0.5 yr | Planet Nine, 0.5 au | 1.5e-4 up to 0.5 au/yr |
| 0.5 yr | Neptune, 0.78 au | 1e-4 up to 0.8 au/yr; 4e-4 at 1.0 au/yr |
| 5 yr | Planet Nine, 2.32 au | 2 % at 0.5 au/yr |
| 5 yr | Neptune, 3.26 au | 10 % at 1.0 au/yr |

The rule is therefore

  r = max(Hill radius [Jupiter to Neptune], r_orbit, 1.5 v99 dt),
  r_orbit = 0.5 au (m / m_P9)^(1/3) (dt / 0.5 yr)^(2/3),

with v99 the 99th percentile of the encounter speeds at that planet
(`p9job make --v99 NAME=V`, recorded in the job with the resulting
`flyby_au`). Model j2 with dt = 5 yr is thereby unsuitable for encounters with
Neptune and Planet Nine (it would need about 8 and 4.5 au).

**The same check on p9gpu** (`tools/flyby_p9gpu.py`, 2026-10-19): the
project lead's script is in the repository unchanged (`tools/flyby_check.py`);
the port uses its test bodies, windows, reference (IAS15) and measures, and
integrates each window with p9gpu (its CPU twin; the GPU gives the same hashes,
checked for the cell Planet Nine 0.5 au / 0.35 au/yr / 0.5 yr). Result: in
every cell of both presets (Planet Nine: d_min 0.25–50 au, 0.1–0.5 au/yr;
Neptune: 0.5–5 au, 0.4–1.2 au/yr) and for dt = 0.5, 1 and 5 yr, p9gpu's
errors equal those of REBOUND's WHFast in democratic heliocentric coordinates
to two digits (median and maximum), e.g. Planet Nine 0.5 au, 0.35 au/yr,
dt 0.5: 1.5e-4; Neptune 0.78 au, 0.8 au/yr: 1.0e-4; Neptune 0.78 au, 1.2
au/yr (1.3 steps per flyby): 2.0e-3, maximum 2.8e-2. Tables:
`runs/flyby/p9gpu-p9.txt`, `runs/flyby/p9gpu-neptune.txt`. Test:
`tests/test_flyby.py` in `make test` (needs the Python package rebound 5.2.2,
installed from `third_party/rebound-5.2.2.tar.gz`).

v99 in the corrected 4-Gyr run (`tools/encounter_speeds.py`: orbits within 2
au of the planet's orbit; relative speed at the closest approach of the two
orbits, and Öpik's U from the Tisserand parameter):

| t | Planet Nine: v99 (MOID / Öpik), n | Neptune: v99 (MOID / Öpik), n |
|---|---|---|
| 10 Myr | 0.50 / 0.43 au/yr, 130 | 0.71 / 0.71 au/yr, 143 |
| 30 Myr | 0.47 / 0.43, 200 | 0.85 / 0.86, 73 |
| 50 Myr | 0.50 / 0.45, 183 | 0.87 / 0.87, 74 |

At dt = 0.5 yr the flyby term (Planet Nine 0.38 au, Neptune 0.65 au) stays
below the radii of the run (0.5 and 0.78 au): the run's radii follow the
extended rule. Limits to report: v99 above 0.65 au/yr at Planet Nine or 1.0
au/yr at Neptune (then the flyby term exceeds the radius). v99 at Neptune
rises with time and rests on few bodies; it is checked with every 500-Myr
report.

Evidence (to hold, the results must not change noticeably; otherwise the
distance is increased):

1. The same job over 10 Myr with half the step (0.25 yr) and the same radii:
   survivors, Δϖ and ΔΩ.
2. A control run with REBOUND's MERCURIUS (`p9sim`, `--integrator mercurius`:
   WHFast in democratic heliocentric coordinates, IAS15 within 3 Hill radii
   of a planet, like mercury6's hybrid integrator), 2,000 test particles over
   50 Myr on the CPU, without encounter removal, against p9gpu with the rule.
3. The J2 comparison repeated with the same radii for Neptune and Planet Nine
   in both models, so that only the J2 approximation differs.

Results: see the end of this file.

## Why the Hill radius, and why also for Planet Nine (until 2026-10-19)

The Hill radius is the usual measure of where a planet's gravity dominates over
the Sun's; GLISSE (Zhang & Gladman 2022) likewise removes particles close to a
planet. For Planet Nine the orbit around it at its Hill radius (about 7 au)
would still be resolved by the time step, but deeper encounters would not; the
same rule for every planet keeps the criterion simple and identical in both
programs. Particles removed this way are counted, so their number can be
reported with every result.

## Results of the evidence (2026-10-19)

1. **Half the step** (`runs/val/dt05`, `runs/val/dt025`; 5,000 test
   particles, seed 9, 10 Myr, the radii of dt = 0.5 yr in both):

   | at 10 Myr | dt = 0.5 yr | dt = 0.25 yr |
   |---|---|---|
   | surviving | 4,629 | 4,630 |
   | removed at Neptune / Planet Nine | 356 / 15 | 349 / 21 |
   | Δϖ: R, mean (distant, a > 230 au, q > 42 au) | 0.293, 307° | 0.291, 308° |
   | ΔΩ: R, mean | 0.526, 93° | 0.522, 93° |

   Two-sample KS tests of a, q, i, Δϖ and ΔΩ at 2, 5 and 10 Myr: p ≥ 0.97.
   The radii hold; the corrected 4-Gyr run was started with them
   (2026-10-19 18:50). For comparison, with Planet Nine's Hill radius (7 au)
   only 3,477 of the same 5,000 survived the 10 Myr.
2. **MERCURIUS control** (`runs/val/merc`, 16 slices of 125, 50 Myr, 64,141
   CPU-seconds, no removal at the planets) against p9gpu with the rule
   (`runs/val/gpu-2000`), the same 2,000 test particles:

   | at 50 Myr | MERCURIUS | p9gpu, rule |
   |---|---|---|
   | surviving | 1,933 | 1,521 |
   | removed | 67 (distance rules only) | 479 (Neptune 389, Planet Nine 82, Uranus 1, distance 7) |
   | distant (a > 230 au, q > 42 au) | 793 | 753 |
   | Δϖ: R, mean | 0.624, 282° | 0.629, 285° |
   | ΔΩ: R, mean | 0.709, 46° | 0.700, 48° |

   KS tests at 50 Myr: Δϖ p = 0.72, ΔΩ p = 0.92, a p = 0.12, i p = 0.13,
   **q p < 0.01** (also at 10, 20, 30 Myr). The clustering of the distant
   particles agrees within the noise at every time; the whole population does
   not: 21 % fewer survivors and another perihelion distribution, because the
   rule removes the particles that come close to Neptune (its Hill radius, 0.78
   au), which MERCURIUS follows and mostly keeps. A larger radius would remove
   more, not fewer: the difference is the removal itself, not the resolution.
   **Open decision** (2026-10-19): keep the rule (clustering of the distant
   population unchanged, total population biased), or follow encounters
   with Neptune instead of removing them (diagnostic without removal running:
   `runs/val/gpu-2000-noenc`), or a hybrid integrator on the GPU.
3. J2 comparison: the first one (dt = 5 yr) was stopped, the step is too long
   for the encounters (above). Repeated with dt = 1 yr and the radii of the
   extended rule with v99 = 0.6 (Planet Nine) and 1.13 au/yr (Neptune), more
   than measured so far: Planet Nine 0.9000 au, Neptune 1.6950 au; the full
   model with the same two radii.
