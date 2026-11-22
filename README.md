# medas-p9-search

N-body simulations of the Planet Nine hypothesis, with a pre-registered and notarised protocol. The question: does
the Planet Nine of the posterior of Brown & Batygin (2021) keep the longitudes of perihelion of the distant
trans-Neptunian bodies clustered over 4 Gyr? And does our own GPU integrator give the same answer as an established
reference integrator?

**Status:** research code and results, not peer-reviewed. Planet Nine is a hypothesis. This project does not search
the sky for it; it computes what its gravity would do in a model. The research note is
[`docs/research-note.md`](docs/research-note.md) (version 1, tag `research-note-v1`). The results are in
`docs/production-result-20261110.md`, `docs/long-runs-result-20261110.md`, `docs/paired-result-A-20261112.md`,
`docs/paired-result-B-20261113.md` and `docs/sets-outcome-20261117.md` with the reports of sets A and B.

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

Criteria, evaluation programs and run packages were fixed before the runs (exceptions: the equivalence test was
entered before its evaluation; the evaluation tool of the long runs was written after the runs and timestamped before
their evaluation). They were entered as commitments in the notary contract
`medas1ghd753shjuwexxywmgs4xz7x2q732vcnkm6h2pyv9s6ah3hylvrqejyaze` on the chain medasdigital-2: entries #2 to #12
(#8 belongs to another project), with block heights, transactions and commitments in `docs/notary.md`.
- The documents name the entries a3, e2–e9, r1, rp and r2. On the chain: a3 #2, e2 #3, e3 #4, e4 #5, e5 #6, r1 #7,
  e6 #9, e9 #10, rp #11, r2 #12.
- #3, #5, #6, #7, #11 and #12 were revealed on 2026-11-22; their manifests and the files outside git are attachments
  of the release `notary-reveal-1`. #2 and #4 follow with the data package, #9 and #10 with their results.
- Each entry commits to a manifest listing every file by sha256 and git commit.
- The commits are tagged `notary-<entry>-<commit>`.
- The documents are also timestamped with OpenTimestamps (Bitcoin).
- Deviations from the protocol are listed in the result reports.

## Which run, which commit and package

`main` holds the documents, results and evaluation tools of the campaign. The programs of the runs were built from
other commits of this repository, listed below. `main` contains them as ancestors (a merge that keeps the tree of the
documents), so the source tree of `main` itself is not the code of the runs (`docs/code-review-20261121.md`, C1). To
rebuild or check a run, check out its commit or tag.

| run | package | commit | entry: criteria, result |
|---|---|---|---|
| equivalence test, 9 pairs | p9equiv-v5-47c7381, p9equiv-merc-47c7381 | 47c7381 | e2 (#3), result in e3 (#4) |
| production run | p9prod-9a084ed | 9a084ed | e3 (#4), r1 (#7) |
| long runs 110–112 | p9long-v5-ac47329, p9long-merc-ac47329 | ac47329 | e3 (#4), r1 (#7) |
| V2 short runs of sets A and B | p9bbv2-5b05cc3 | 5b05cc3 | e4 (#5), result in e5 (#6) |
| paired tests for sets A and B | p9pair-v5-fed221a, p9pair-merc-fed221a | fed221a (run set-up d4dadd9) | e5 (#6), rp (#11) |
| sets A and B | p9bbsets-5b05cc3 | 5b05cc3 | e4 (#5), r2 (#12) |
| reproduction check | p9repro-d3c2363 | d3c2363 | timestamped, not entered |
| check run BB-A-rin1 | p9rin-0b8971f | 0b8971f | e6 (#9), result to follow |
| set A, second seed (BB-A2) | p9bbA2-5b05cc3 | 5b05cc3, criteria 0003408 | e9 (#10), result to follow |

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
   a record against its `MANIFEST.sha256`, whose sha256 will be fixed by entry e7 (planned, with the data package).
3. **Bits:** any segment of a run, computed again from its stored input with the run package, gives the result hash in
   its `DONE` file. The hash is taken over the canonical states of all snapshots (`docs/reproducibility.md`).
   - Bit-identical on every platform: WHFast, and p9gpu with its CPU twin.
   - MERCURIUS (p9sim) so far only with glibc on x86-64, the platform of all runs so far. The cause is the libm
     function `cbrt`. The fix comes with a new p9sim binary, for future packages.

## Methods and tools

An AI assistant (Claude, by Anthropic) did much of the work under the direction of the author. It wrote and revised
the integrator, the evaluation programs, the tests and the computing packages, drafted the criteria, the reports and
the documents, ran evaluations by the procedures fixed beforehand, and checked texts and numbers. Further AI sessions
read the code and the texts of the website independently and, on 2026-11-22, after their entries, the result reports
of entries r1, rp and r2. The author made the decisions: the questions, the criteria and their limits, the order of the
runs, the acceptance of every result and every text, and every entry on the chain. The results rest on deterministic
programs, their tests and the checks described in the documents, not on the judgement of an AI (research note,
section 2.4).

## Licence and citation

- Code: GPL-3.0-or-later (REBOUND is GPL-3.0-or-later; see `LICENSE`).
- Data and documents in the data records: CC BY 4.0.
- Author: Eike Janßen, MEDAS Computers GmbH. Citation: `CITATION.cff`; the data records and their DOIs follow with
  the data package.
- Reference: Brown, M. E., & Batygin, K. 2021, The Orbit of Planet Nine, AJ 162, 219.
