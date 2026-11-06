# The A100 after V5 110–112, while the paired tests run: proposal (2026-11-06)

**Status:** proposal, not decided.

**Window:** from the end of V5 110–112 (about 2026-11-10/11) to the release or not of sets A and B after the paired
tests (about 2026-11-14), so 3–4 days. About 1.2 days of it are the V5 half of the paired tests
(`docs/bb2021-paired-test-proposal.md` section 7).

**Rule for everything here:** nothing that touches the preregistration.
- No run whose results enter or could inform an evaluation that is entered or planned.
- No extra seeds or variants of the registered configurations.
- No early start of sets A or B.
- No look at results of the production run before its evaluation.
- The chain of the A100 stays as it is: one run at a time, started by hand or by the chain only where its rules
  allow.

## Proposed, in this order

| # | what | A100 time | why it touches nothing |
|---|---|---|---|
| 1 | **CPU-2 measurement**, unless already done at the transition from the production run: `gpu-v5-4k-1m` and `gpu-v5-64k-1m` of the speed package, 3 times each, with 0, 8 and 12 cores of socket 1 busy with MERCURIUS slices | about 1 h | performance only; the result hashes are known, so it is also a bit check |
| 2 | **The V5 half of the paired tests**, 18 runs of 200 Myr, one after the other, after their chain entry | about 29 h | it is the registered paired test itself, under its own entry |
| 3 | **Reproduction of stored segments** for the data package: segments 0, 19 and 39 of the production run and one segment each of V5-s110–112, computed again from their stored inputs with the package binary; only the result hashes are compared | about 12 h | only hashes are compared; it shows "rerun a segment, get its hash" on real data, as the README of the data package promises |
| 4 | **C3, bundling** (engineering): several jobs in one p9gpu process. Developed and checked on the laptop first (CPU twin: every job of a bundle bit for bit equal to its run alone), then on the A100: the same bit check and the speed against single processes | about 0.5 day | a program test on test jobs; only for future runs, and only with its own check and entry, never for a run already registered |
| 5 | otherwise **idle** | – | an idle card costs nothing against the preregistration |

**Expected gain of C3:** latency-bound runs at 2,000–6,000 particles would become about 2.7 times faster (speed
comparison: one process of 6,000 particles about 25 s per Myr, against three processes of 2,000 at 23 s each). That
would help a new attempt of a paired test, or long pairs if decided (`bb2021-paired-test-proposal.md` section 8,
point 5).

## Not proposed

- Runs without Planet Nine (a null control), more seeds of the production configuration, other time steps or radii.
  They would be informative, but only with their own criteria and entry, after the registered evaluations.
- The 4-Gyr runs of sets A or B before their release.
- MERCURIUS on the A100 host cores beyond what the CPU-2 measurement allows.

## Preparations, on the laptop (nothing on the server)

- For 1: the measurement package, a variant of `speed/` with the three load levels and the 3 % rule.
- For 3: a small reproduction package (the input of each chosen segment from the run directory, the package binary,
  expected hash = the line in `segments.tsv`).
- For 4: C3 in p9gpu with tests.
