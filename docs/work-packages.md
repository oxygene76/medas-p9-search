# Work packages (jobs)

A job is a self-contained piece of computation that another machine can run;
the result is compared by hash. Tool: `tools/p9job.py`.

## Contents of a job directory

| File | Content |
|---|---|
| `job.json` | description (below) |
| `input.sa` | start state: REBOUND SimulationArchive with one snapshot; holds every integration setting (integrator, coordinates, dt, N_active, G) |
| `ic.txt` | the exact decimal start values `input.sa` was built from (first segment only; informational) |
| after a run: `result.json`, `output.sa`, `final.state` | result, snapshots, canonical final state |

`job.json`:

- `schema`: `medas-p9-search/job/1`
- `code`: commit of this repository (and whether the tree was clean), REBOUND
  version with source URL, sha256 and licence, build rules
- `params`: test case, start-value generator and its arguments with the sha256 of
  `ic.txt`, integrator settings, `t_start_yr`, `t_end_yr`, `snapshots`, removal
  rule; for a later segment of a chain also `previous` (job id and result hash of
  the segment before)
- `input`: file name, sha256, size in bytes
- `id`: SHA-256 over the canonical JSON (sorted keys, no spaces) of `schema`,
  `code`, `params` and `input`, i.e. over the description and, through its hash,
  the input
- optional `control`: the expected `result_sha256` (and final state hash) of a
  reference run, outside the id. A machine that computes a control job can be
  checked against a result known in advance.

`result.json`: `job_id`, `result_sha256` (the number to compare),
`final_state_sha256`, steps, particles at start and end, removed particles,
relative energy error of the massive bodies, wall and CPU time, input and output
size in bytes, platform (machine, system, a short hash of the host name), build
flags, runner (e.g. qemu or Node).

## Commands

```sh
tools/p9job.py make --out runs/x --t-end 1e6 --snapshots 10 --tp-from 0 --tp-to 250
tools/p9job.py run runs/x [--p9sim build/clang-O2/p9sim] [--prefix "node --no-warnings tools/run_wasm.mjs"]
tools/p9job.py control runs/x        # record the reference result as the expected one
tools/p9job.py check runs/x          # compare with it (exit code 0 if equal)
tools/p9job.py next --prev runs/x --out runs/x2 --t-end 2e6 --snapshots 10   # next segment
```

`tools/campaign.py` runs chains of such jobs in parallel (one chain per slice of
test particles; the massive bodies are in every job and evolve identically,
since test particles are massless) with a deadline.

## Measured sizes and times (gcc -O3, 2026-10-18)

| Job | Test particles | Span | Steps | Input | Output (snapshots) | Wall time |
|---|---|---|---|---|---|---|
| control | 20 | 0.1 Myr | 200,000 | 6,080 B | 33,267 B (5) | 0.86 s |
| repro | 100 | 1 Myr | 2,000,000 | 16,320 B | 244,042 B (10) | 34.9 s |
| bench | 250 | 5 Myr | 10,000,000 | 35,520 B | 294,547 B (5) | 459.6 s (machine busy with the long run) |
| long run segment | 250 | 20 Myr | 40,000,000 | ≈ 36 kB | ≈ 1.2 MB (20) | ≈ 1,800 s (16 in parallel) |

Cost per particle and step: about 0.11 µs on one core (27 µs per step with 256
bodies), linear in the number of particles; the planets alone cost 0.7 µs per step.
