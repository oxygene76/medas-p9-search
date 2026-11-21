# Run BB-A2: set A with a second seed (criteria, DRAFT of 2026-11-21)

**Status:**
- Draft for review. To be entered on medasdigital-2, as its hash only, **before** the run starts.
- Nothing is started before:
  1. the review;
  2. the entry;
  3. the project lead's go.
- **It changes nothing:** not the criteria of sets A and B, not their verdicts, not outcome 4, not its consequences.
  There is no pass or fail. The run gives a measure of spread, fixed here before it exists.

## 1. The question

**How far do the measures of set A differ between two independent draws of its test particles?**
- The outcome report names "one realisation of each set" as a limit.
- Addendum 3 measured the spread over the four subsets of the one run BB-A and set from it the tolerance band of
  BB-A-rin1: twice the largest deviation of a subset from the whole.
- BB-A2 measures the difference between two whole runs of 64,000 test particles.

**What the run varies, and what not:**
- **Varied:** only the test particles. A new, independent seed (313 instead of 311) draws new start values from the
  same distributions (a 150–500 au, q 30–50 au, i 0–25°, angles uniform; `tools/make_ic.py`, make-ic-v1).
- **The same:** the Sun, the giant planets and Planet Nine, start values and evolution, bit for bit. The test
  particles are massless and do not act on them. The program and all settings are those of BB-A.
- **So the run measures the spread from the choice of test particles,** not that of another realisation of the
  planets. That is the same kind of spread as addendum 3, from samples four times larger.

## 2. The run

**Identical to BB-A:**
- package `p9bbsets-5b05cc3`, binaries p9gpu `7666c5ba…` and p9sim `b14f7956…`;
- `params.env` of BB-A (smooth encounters, 8 planet sub-steps, collisions at the radii of addendum 13, r_in 4.5 au
  checked every 1000 steps, r_out 10,000 au);
- 64,000 test particles, 0–4 Gyr in 40 segments of 100 Myr, a snapshot every 10 Myr;
- the A100, CPUs 16–31.

**The only difference:**
- the seed 313. `job.json` of BB-A2 differs from that of BB-A only in the seed, `ic_sha256`, the input sha256 and
  the job id.

**Checked before the start:**
- **The recipe:** rebuilding BB-A with seed 311 by the same command gives the state of BB-A's `input.sa`, by
  `p9sim dump`. The bytes of `input.sa` written by `p9sim init` are not reproducible (unset padding); its state is.
- **The start file:** Sun, planets and Planet Nine in BB-A2's `input.sa` equal those of BB-A.
- **The package check** (`check.sh`, 40 cases, unchanged): ALL SAME on the A100 before the job, as for BB-A.

**Package:** `p9bbA2-5b05cc3` (description in its `RUN.txt`).

## 3. What is measured

Window 1–4 Gyr, 301 snapshots, elements as `tools/prod_eval.py`. The tools and calls of
`docs/bb-a-rin1-evaluation-procedure.md`, section 3, with RUN = `jobs/BB-A2`:
1. **M1–M5** with `tools/prod_eval.py --criteria bb2021-A` (prod-eval-v1).
2. **R per 10 au beyond the wall,** 260–700 au, all of S_BB (`tools/sets_decompose.py`, 2d10dae, `--wall 256`).
3. **The inclination shares** < 30°, 30–40°, 40–50°, 50–70° (normalised to 0–70°) and retrograde (of all), for
   q > 42 au and for 42 ≤ q ≤ 100 au; M2 per subset (`tools/sets_subset_spread.py`, 4eec855).
4. **Survivors** at 1, 2, 3 and 4 Gyr, all and in S_BB beyond the wall.

## 4. What is compared, and the statement fixed now

**Comparison values,** BB-A:

| measure | BB-A |
|---|---|
| M1 | 127.3° |
| M2 | 0.0496 |
| M3 | 3.2° |
| M4 | 165 au |
| R beyond the wall | 0.097 |
| shares q > 42 au | 0.622 / 0.134 / 0.095 / 0.149, retrograde 0.171 |
| shares 42 ≤ q ≤ 100 au | 0.794 / 0.109 / 0.045 / 0.053, retrograde 0.069 |

Sources: `docs/sets-result-A-20261117/result.json`, `docs/sets-decomposition-20261117/A/summary.json`,
`docs/sets-decomposition-3-20261117/spread-A.json`.

**The tolerance of addendum 3:** M2 ± 0.012; each share ± 0.008; retrograde ± 0.022 (q > 42 au) and ± 0.011
(42 ≤ q ≤ 100 au).

**The statement, without pass or fail:**
- **The differences BB-A2 − BB-A** of all measures of section 3 are reported as the measure of the spread between two
  realisations of the test particles. Each with its value and its sign.
- **For M2 and the ten shares:** each difference is set against the tolerance of addendum 3, as **"within"** or
  **"outside"** it. The number outside is reported.
- **What follows from it:**
  - **All within:** the spread between two realisations is no larger than the tolerance set from the subsets. The
    scale of addendum 3, and with it the band of BB-A-rin1, is supported by a second, independent draw.
  - **Some outside:** the spread between two realisations is larger than that scale for these measures. This is
    reported next to the result of BB-A-rin1 as a caution about its tolerance band.
    - The verdict of BB-A-rin1 stays as its criteria fix it.
    - BB-A-rin1 shares its test particles with BB-A, so for it the scale of the particle choice within one run applies
      (its criteria, section 4).
- **For information,** not judged: the verdict BB-A2 would get by the comparison criteria (sections 5 and 6 of
  `docs/bb2021-comparison-criteria.md`, set A). It changes nothing of outcome 4, which was fixed for BB-A and BB-B.

**Prediction, fixed now:**
- **M2 and the ten shares:** all within the tolerance. Expected are differences of the order of the subset spread
  divided by two, since the samples are four times larger: about 0.003 for M2 and 0.002–0.004 for the shares.
- **M1:** BB-A2 − BB-A within ± 15°. The cluster of set A is weak (R ≈ 0.05), so its direction scatters more than its
  strength. The four subsets of BB-A lie at 123–134°.
- **M4:** may differ by a few 10-au bins, because it is the first bin above a threshold of R.
- **Survivors** at 4 Gyr: within ± 2 % of BB-A.
- **BB-A2 alone** will not agree with Brown & Batygin 2021 (M2 far below 0.20).

## 5. The entry

- **Type:** `job`, referring to entry #5 (e4, which holds the package of sets A and B).
- **Content:** a manifest of
  - this file (as committed);
  - `docs/sets-decomposition-addendum-3-20261117.md` (the tolerance);
  - the package `p9bbA2-5b05cc3` with its sha256;
  - the job files of BB-A2.
- **After the run:** its result as `result` referring to this entry.
- **Proposed names:** e9 for this entry and r4 for its result. e7 and e8 are kept for the data package.

## 6. What the run does not decide

- **Not tested:**
  - another realisation of the planets or of Planet Nine, which are the same bit for bit;
  - integrator, time step, reference plane, the removal rule (BB-A-rin1 tests the latter).
- **Not touched:** the verdicts on sets A and B, outcome 4 and its consequences, the mercury6 counter-run of set A.
