# Open points from the code reading of 2026-11-21 (to be worked on after 2026-11-24)

From `docs/code-review-20261121.md`. Each point is checked against the code before it is acted on. Nothing here
changes a registered result; where a computation is needed, it is fixed and timestamped before it is run.

| Point | What | Next step |
|---|---|---|
| A2 | removal at r < 4.5 au checked only every 1000 steps; the criteria name no cadence | result of the run BB-A-rin1 (entry #9); then a sentence in the criteria's addenda |
| B1 | Kepler solver with a fixed number of iterations, no convergence check close to the Sun | test over the range of the orbits that occur (q 0.05–4.5 au), energy error per perihelion passage |
| B2 | particles with a non-finite state are never removed and are skipped in the evaluation | count non-finite values in all snapshots of the runs (expected: none) |
| B3 | an empty S_BB snapshot enters M2 with R = 0 (`prod_eval.py`), NaN in `sets_subset_spread.py` | note; not the case in the runs |
| B4 | order of outcomes 3 and 4 in `prod_eval.py --outcome`, outcome 3 from the pooled M1 only | note against section 6 of the criteria |
| B5 | exactly flat orbits (i = 0) give an undefined node | note; test case |
| B6 | snapshot time computed from the segment, not read from the file | an assert comparing both |
| B7 | synchronous state of particles in sub-steps (smooth) for output and removal | estimate the size |
| B8 | R beyond the wall: unweighted mean over bins of dependent particle-snapshots | addendum 5, part 2 |
| B9 | division by zero in `sets_decompose.py` if the first window snapshot beyond the wall is empty | guard |
| C3 | M4 follows from M2 when the plateau is weak | text of section 6 and of the outcome report (addendum 5, part 3) |
| C4 | "401 snapshots from 0 to 4.0 Gyr" in the criteria: there are 400 (no snapshot at t = 0) | correction as a dated note |
| C5 | "beyond the wall" bounded twice (bins with lower edge ≥ wall, and a ≥ wall) | note in the decomposition reports |
| C6 | tests of the evaluation do not cover the read path of the runs or inclined orbits | tests |
| C7 | removal counters (`removed_inner` only for the model j2) | documented; separate counters since 0b8971f |
