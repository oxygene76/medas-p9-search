# Paired tests V5 against MERCURIUS for sets A and B: proposal of criteria (2026-11-06)

**Status: proposal, not accepted.**
- The project lead checks it. Once accepted, it is fixed in a commit and entered on chain as its own entry before any
  run of it starts.
- Until then no run, no package start, and no look at anything that could inform it.

**Why:** the V2 short runs of both sets are outside the limits of addenda 13 and 16
(`docs/bb2021-v2-result-20261106.md`). In set A, Uranus fast flybys are × 2.02 and close flybys × 1.66; in set B,
Uranus fast flybys are × 0.62. As fixed there, each set needs a paired test V5 against MERCURIUS, with criteria fixed
beforehand, before its 4-Gyr run.

**Design:** the equivalence test of the production run (`docs/equivalence-criteria.md`, entry e2, result in entry e3),
with the same statistic, margin, test, size, duration and decision logic. What changes:
- the Planet Nine of the set;
- new seeds;
- one decision per set.

## 1. Question

For set A and for set B separately: does p9gpu v5, the method of the 4-Gyr package `p9bbsets-5b05cc3`, give the same
clustering of the distant bodies as MERCURIUS, within the margin of the equivalence test?

## 2. Runs

| | set A | set B |
|---|---|---|
| Planet Nine | 7 Earth masses, a 500 au, e 0.33, i 17° (invariable plane), ϖ 250°, Ω 100°, M 0 | 5 Earth masses, a 300 au, e 0.15, i 17°, ϖ 254°, Ω 108°, M 0 |
| seeds (new, not used before) | 331–339 | 341–349 |
| runs | 9 seeds × 4,000 test particles, in both groups | the same |

**Everything else** as the equivalence runs and as the sets:
- test particles a 150–500 au, q 30–50 au, i 0–25°;
- inner removal 4.5 au, dt 0.5 yr;
- 0 to 200 Myr, a snapshot every 1 Myr (10 segments of 20 Myr, 20 snapshots each);
- start values with `tools/make_ic.py` (make-ic-v1), Planet Nine relative to the invariable plane;
- radii of addendum 13: Jupiter–Neptune as in the production package, Planet Nine 2.0824 au (A) and 1.8616 au (B),
  collision radius 17,248.4 km (A) and 15,418.4 km (B).

**Groups**, paired by seed:

| group | method | program |
|---|---|---|
| V5 | p9gpu v5 as in `p9bbsets` (smooth transition, planets with 8 inner steps, collisions at the planets' radii, FP64) | the p9gpu binary of p9prod-9a084ed (sha256 `7666c5ba…`), on the A100 |
| M | MERCURIUS, settings unchanged from the M group of the equivalence test (package `p9equiv-merc-47c7381`), Planet Nine of the set | the p9sim binary of p9prod-9a084ed (sha256 `b14f7956…`), CPU, 16 slices of 250 particles per seed |

**Rules:**
- **Check before the runs:** each package first checks its programs bit for bit against the reference machine on a
  short piece of its own jobs, as the packages so far do.
- **No interim look:** no look at R before all runs of a set are complete, and no change of the number of runs after
  a look.
- **Technical failures:** a run that fails technically is repeated with the same job. No run is left out because of
  its result.
- **Packages:** `p9pair-v5` and `p9pair-merc`, built like `p9equiv-v5` / `p9equiv-merc` from the jobs of this
  proposal, at a commit named in the chain entry.

## 3. Statistic

As in the equivalence test, with its clarification of 2026-10-23:
- **Per run:** S = the mean of R(Δϖ) of the distant survivors (a > 230 au, q > 42 au) over 160, 165, …, 200 Myr
  (9 snapshots).
- **Elements:** barycentric. Δϖ is a body's ϖ minus that of the Planet Nine of its own simulation (for M: of its
  slice) at the same snapshot.
- **M:** the 16 slices of a seed are one run. Their distant survivors are pooled at each time before R is computed.
- **Evaluation tool:** `tools/equiv_eval.py`, or a copy that only takes the job directories of these packages, with
  the computation of S unchanged. It is committed and named in the chain entry before the evaluation.

For information only, deciding nothing:
- R at 200 Myr;
- S with the cut of the observed sample (150 < a < 1,000 au, q > 42 au);
- the number of survivors at 200 Myr per group.

## 4. Test and margin

- **Per set, per seed:** d_s = S(V5, s) − S(M, s).
- **Interval:** the mean of the 9 differences and its two-sided 95 % interval (t distribution, 8 degrees of freedom).
- **Equivalent:** the interval lies inside (−0.035, +0.035).
- **Different:** the interval lies entirely outside it.
- **Not shown:** otherwise.

**Margin ±0.035**, unchanged. The reasoning is the same: a quarter of the standard deviation (about 0.14) of R for
the dozen observed objects. A larger margin for the sets would weaken exactly the comparison that V2 called into
question.

**No correction for two tests:** each set decides only its own 4-Gyr run. The two-sided 95 % interval is already the
pair of one-sided tests at α = 0.025.

**Power:**
- The equivalence test measured an sd of the pair differences of **0.0115**, as its noise model expected (0.012).
- With 9 × 4,000 the power is that of its table: equivalence found with probability 1.00 for a true difference of 0
  or 0.01, and 0.91 (0.75 at an sd of 0.015) for 0.02.
- **Proviso:** the sets may scatter differently, for example set B with Planet Nine at 300 au. Without an interim look
  there is no adjustment.

## 5. What follows from each outcome

Fixed before the runs. "Passed" means "equivalent"; "not shown" and "different" both count as not passed. The number
of runs is not raised after the result. A new attempt needs new criteria and new seeds.

**Per set:**

| outcome of the set | what follows for that set |
|---|---|
| **equivalent** | Its 4-Gyr run with `p9bbsets-5b05cc3` unchanged. Release: see "Release mechanism" below. The report names the V2 deviation and that the paired test covers 0–200 Myr only (section 6). |
| **not shown** | No 4-Gyr run of that set with v5. Its comparison with Brown & Batygin is reported as not carried out, with the V2 and paired results. Further steps only with new criteria, for example (b) or (c) below. |
| **different** | As "not shown". In addition, the deviation of v5 in that configuration is examined on its own branch: the variants with one difference switched off each, as planned for the production method. |

**Both sets together:**

| A | B | A100 after the paired tests |
|---|---|---|
| equivalent | equivalent | set A, then set B, as ordered on 2026-11-04 (each about 2.75–3.13 days) |
| equivalent | not passed | set A only |
| not passed | equivalent | set B only |
| not passed | not passed | neither; the comparison with Brown & Batygin is reported as not carried out with v5 |

**Not affected by any outcome:**
- the production run, whose method was decided by the equivalence test at its own configuration;
- the paired long runs 110–112;
- the evaluation criteria of the production run.

**Possible later steps for a set that did not pass** (each only with its own criteria and entry; listed here so that
nothing is decided after the result):
- **(b)** A 4-Gyr run of that set with MERCURIUS at a reduced number of test particles. 8,000 particles cost about
  2,000 core hours, about 3.5 days on 24 cores. The noise of M1–M4 is larger than with the 64,000 of `p9bbsets`, so the
  tolerances of section 5 of the comparison criteria would need a power analysis of their own.
- **(c)** The cause analysis of (different), first.

**Release mechanism** (to be decided with this proposal):
- `start.sh` of `p9bbsets` and the A100 chain start a set only if `v2/BB-<set>.ok` contains the line
  "within the limits". Today the files hold the V2 verdict "outside the limits".
- Proposal: the evaluation tool of the paired test writes, only for "equivalent", the file `v2/BB-<set>.paired`
  (outcome, interval, report commit).
- The operator then replaces `v2/BB-<set>.ok` by two lines: "within the limits" and "released by the paired test,
  `v2/BB-<set>.paired`".
- The V2 verdict stays in `docs/bb2021-v2-result-20261106.md` and its stamped copy, and the replaced file is kept
  as `v2/BB-<set>.v2`.
- `p9bbsets` itself stays unchanged; its check is `grep -qx "within the limits"`, which matches the first line.

## 6. Scope and residual risk

- **Scope:** as for the equivalence test, the clustering statistic S over 0–200 Myr, per set. Not covered: losses,
  the distributions of a, q and i, and the 1–4 Gyr of the comparison.
- **The V2 deviation stays a fact.** In set A more test particles meet Uranus fast and close than in the validated
  configuration; in set B fewer meet it fast. An equivalent S at 0–200 Myr does not show that a small bias per unit
  time stays small over 4 Gyr. For the production run that is the purpose of the long runs 110–112; for the sets no
  long pairs are proposed (cost).
- **The publication says so:** the 4-Gyr results of a set released by this test carry the note "method equivalence
  shown for 0–200 Myr in this configuration; encounter regime outside the V2 limits".

## 7. Computing need and schedule

**V5 half** (18 runs) on the A100:
- 4,000 particles are latency-bound there: 23.1 s per Myr at the start, more with the encounter load.
- The equivalence runs took 5.3–7.9 h on the L40S, which is 3.45 times slower than the A100 at 4,000 (speed
  comparison).
- That gives about **1.6 h per run on the A100, about 29 h for all 18**, one after the other (no MPS: several at once
  are not faster in all).

**M half** (18 runs × 16 slices of 250 = 288 slices of 10 segments):
- The equivalence M runs took **92–97 core hours per run** on CPU 1, 93 in the mean. The long runs 110–112 show the
  same rate: about 9 s per particle and 20-Myr segment.
- Set A has more Uranus encounters (more IAS15 phases in MERCURIUS), so up to +25 % is planned for.
- That gives **1,670–2,160 core hours for both sets**:

| cores for M | days |
|---|---|
| 16 (CPU 1) | 4.4–5.6 |
| 24 (CPU 1 + 8 of CPU 2) | 3.2–4.2 (the cores 10 % slower when more are busy) |
| 28 (CPU 1 + 12 of CPU 2) | 2.8–3.6 |

**Earlier start on CPU 1:**
- From about 2026-11-07 the MERCURIUS part of seeds 110–112 runs its second round with 8 slices only, so 8 cores of
  CPU 1 are free until about 2026-11-10.
- If the chain entry of these criteria is made by then, the M half can start there with `THREADS=8`.
- From Tuesday it continues with 16 threads or more (`stop.sh`, then `start.sh` with the new number; done segments
  are kept, the bits do not depend on it).
- 576 core hours of the M half are then done before Tuesday.

**Cores of CPU 2 (socket 1, where the A100 runs are pinned):**
- **Fact:** an A100 run uses one host thread per p9gpu process (the production run and a set: 1; V5 110–112: 3;
  the V5 half of the paired tests: 1).
- **Risk:**
  - With all 32 cores busy, a core of the server ran 15–21 % slower than with 6 busy (speed comparison, cpuall
    against cpu1): shared clock and power budget of the VM.
  - At 4,000 particles p9gpu is latency-bound, so a slower host thread slows the A100 directly.
  - At 64,000 the GPU dominates, so the effect is small.
- **No measurement yet** of A100 throughput under CPU load. Proposed: a measurement of about 1 h on the A100:
  - jobs: the scaling jobs `gpu-v5-4k-1m` and `gpu-v5-64k-1m` of the speed package, 3 times each;
  - under three loads: CPU 2 otherwise idle, 8 cores busy, 12 cores busy with MERCURIUS slices (`cpu-merc-4k-1m`,
    pinned to socket-1 cores, `nice 19`);
  - result hashes as known, so it is also a bit check.
- **Rule:**
  - k cores of CPU 2 are used for the M half only if the median wall time at 4,000 rises by at most 3 % with k cores
    busy;
  - the M processes then run pinned to the upper k cores of socket 1 with `nice 19`;
  - the p9gpu processes keep the lower ones free; the running processes are not touched.
- **When:**
  - preferably at the transition from the production run to V5 110–112 (`chain-a100.sh pause` shortly before the end
    of the production run, measure, `resume`), so that the answer is there by Tuesday;
  - otherwise at the start of the A100 window after V5 110–112.

**Schedule** (estimates):

| | from | to |
|---|---|---|
| production run (A100) | running | about 2026-11-07 |
| V5 110–112 (A100) | about 2026-11-07 | about 2026-11-10/11 |
| M 110–112 round 2 (8 cores of CPU 1) | about 2026-11-07 | about 2026-11-10 |
| chain entry of these criteria | after the project lead's check | – |
| paired M half (CPU 1, 8 → 16 + k cores) | entry, at the earliest 2026-11-07 | about 2026-11-13/14 |
| paired V5 half (A100) | after V5 110–112, about 2026-11-11 | about 2026-11-12 |
| evaluation, release | about 2026-11-14 | – |
| sets A / B (A100, if released) | about 2026-11-14 | about 2026-11-17 / 2026-11-20 |

## 8. Open points for the project lead

1. The seeds 331–339 (A) and 341–349 (B).
2. One evaluation per set without a multiplicity correction (section 4).
3. The release mechanism (section 5).
4. The CPU-2 measurement and its 3 % rule; the measurement at the transition from the production run.
5. Whether the long-run residual risk of section 6 should be narrowed for a released set with one or two long pairs
   (V5 and M, 2,000 particles, 0–4 Gyr, as 110–112). That costs about 300–600 core hours per pair.
