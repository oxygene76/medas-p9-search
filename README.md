# medas-p9-search

N-body simulations of the Planet Nine hypothesis, with a pre-registered and notarised protocol. The question: does
the Planet Nine of the posterior of Brown & Batygin (2021) keep the longitudes of perihelion of the distant
trans-Neptunian bodies clustered over 4 Gyr? And does our own GPU integrator give the same answer as an established
reference integrator?

**Status:** research code and results, not peer-reviewed. Planet Nine is a hypothesis. This project does not search
the sky for it; it computes what its gravity would do in a model. The research note is in
`docs/research-note-draft.md`, and the results are in `docs/production-result-20261110.md` and
`docs/long-runs-result-20261110.md`.

## What is here

| | |
|---|---|
| `src/p9sim.c` | the CPU integration program on REBOUND 5.2.2 (WHFast or MERCURIUS): `init`, `run`, `last`, `state`, `dump`, `sha256` |
| `gpu/` | p9gpu, the GPU integrator (Wisdom–Holman in democratic heliocentric coordinates, smooth close-encounter sub-steps, FP64), with a bit-identical CPU twin |
| `tools/make_ic.py` | start values: Jupiter–Neptune from JPL DE440s, Planet Nine, test particles |
| `tools/p9job.py` | work packages: description, hashes, run, check |
| `tools/equiv_eval.py`, `tools/prod_eval.py`, `tools/long_eval.py`, `tools/pair_eval.py` | the evaluations, each committed before its run or before any look at its results |
| `tools/manifest.py`, `tools/notary/` | the manifests of the notary entries and their encrypted backups |
| `tools/check_segments.py`, `tools/pack_record.py`, `tools/publish_scan.py` | integrity checks of runs, packing of the data records, and the scan of anything published |
| `docs/` | criteria, procedures, results, notary entries (`docs/notary.md`), the data package (`docs/data-package-e6.md`) |
| `tests/` | tests of the tools (`make test`, `python3 -I tests/test_*.py`) |
| `third_party/README.md` | REBOUND version, checksum and licence |

## Pre-registration

Criteria, evaluation programs and run packages were fixed before the runs. They were entered as commitments in the
notary contract `medas1ghd753shjuwexxywmgs4xz7x2q732vcnkm6h2pyv9s6ah3hylvrqejyaze` on the chain medasdigital-2:
entries #2 to #7, with block heights, transactions and commitments in `docs/notary.md`.
- Each entry commits to a manifest listing every file by sha256 and git commit.
- The commits are tagged `notary-<entry>-<commit>`.
- The documents are also timestamped with OpenTimestamps (Bitcoin).
- Deviations from the protocol are listed in the result reports.

## Build and run

Needs a C99 compiler, Python 3 with numpy, and for p9gpu a CUDA toolkit (`nvcc --fmad=false`). The CPU twin needs no
GPU.
```sh
scripts/fetch-rebound.sh
make                                  # gcc -O3 -> build/gcc-O3/p9sim; no -ffast-math, -ffp-contract=off
make CC=clang OPT=-O2                 # other compilers and levels give the same bits (MERCURIUS: see below)
python3 -m venv build/venv && build/venv/bin/pip install -r tools/requirements.txt
build/venv/bin/python tools/p9job.py make --out runs/demo --t-end 10000 --snapshots 4 --tp-to 100
build/venv/bin/python tools/p9job.py run runs/demo
```

## Verify a result yourself

1. **Notary:** after the reveal, the sha256 of a manifest equals the content digest of its entry, and each listed
   file equals its sha256 in the manifest (`tools/manifest.py verify`).
2. **Data:** the data records [DOIs] hold the runs, evaluations and notary files. `tools/pack_record.py verify` checks
   a record against its `MANIFEST.sha256`, whose sha256 is fixed by entry e6.
3. **Bits:** any segment of a run, computed again from its stored input with the run package, gives the result hash in
   its `DONE` file. The hash is taken over the canonical states of all snapshots (`docs/reproducibility.md`).
   - Bit-identical on every platform: WHFast, and p9gpu with its CPU twin.
   - MERCURIUS (p9sim) so far only with glibc on x86-64, the platform of all runs so far. The cause is the libm
     function `cbrt`. The fix comes with a new p9sim binary, for future packages.

## Methods and tools

[Wording to be agreed with the author before publication.] An AI coding assistant (Claude, Anthropic) wrote and
revised code, tests, packages and documents under the direction of the author. The author made the scientific
decisions: questions, criteria, thresholds, the order of the runs, and the acceptance of each evaluation. Every result
rests on the deterministic programs and their tests. The criteria were notarised before the runs.

## Licence and citation

- Code: GPL-3.0-or-later (REBOUND is GPL-3.0-or-later; see `LICENSE`).
- Data and documents in the data records: CC BY 4.0.
- Author: Eike Janßen, MEDAS Computers GmbH. Please cite the data records and the software record [DOIs to follow].
- Reference: Brown, M. E., & Batygin, K. 2021, The Orbit of Planet Nine, AJ 162, 219.
