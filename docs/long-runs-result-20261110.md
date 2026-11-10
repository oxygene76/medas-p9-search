# Paired long runs 110–112, V5 against MERCURIUS: result of the evaluation (2026-11-10)

**Status:** result report, for independent review before anything of it goes into the research note. The criteria are
`docs/long-runs-110-112-criteria.md` as entered in entry 3 (chain entry #4, block 10723643, commit 7302607). The
steps, and the decisions L1 and L2 of 2026-11-10, are in `docs/long-runs-evaluation-procedure.md` (af2e058,
timestamped). The files as the tool wrote them are in `docs/long-runs-result-20261110/` (commit afad411).

**Version 2 (2026-11-10, after the independent review):**
- The review confirmed the verdicts and numbers; it recomputed S(t), d̄, the standard errors and M2 from
  `timeseries.csv`.
- Added: the significance of S(1–4) and d(0.5 Gyr) with t at 2 degrees of freedom, and the noise floor at late times.
  Both are under "Power".
- Version 1 is commit ea38f05, stamped as `runs/notary/long-runs-result-ea38f05.md`, and stays unchanged.

## Verdict

**No growing bias found** (criteria section 3, with the low power stated below).

| condition of "growing bias found" | value | holds |
|---|---|---|
| \|d(4 Gyr)\| ≥ 0.05 | 0.0450 | no |
| \|d(4 Gyr)\| > 2 standard errors | 2 SE = 0.0626 | no |
| d has the same sign at 1, 2 and 4 Gyr | −, −, − | yes |
| \|d(4 Gyr)\| > \|d(0.5 Gyr)\| | 0.0450 > 0.0073 | yes |

All four conditions must hold for "growing bias found". The size conditions fail, and the sign and growth conditions
hold. The cases L1 and L2 did not arise: every run has at least 382 distant survivors in every snapshot (limit 100),
so all four times are used.

## Values

S(t) is the mean of R(Δϖ) of the distant survivors (a > 230 au, q > 42 au) over the 11 snapshots up to t. S(1–4) is
the mean over the 301 snapshots from 1 to 4 Gyr.

| seed | group | S(0.5) | S(1) | S(2) | S(4) | S(1–4) |
|---|---|---|---|---|---|---|
| 110 | V5 | 0.2624 | 0.1091 | 0.0447 | 0.0339 | 0.0809 |
| 110 | M | 0.2513 | 0.0833 | 0.0784 | 0.1218 | 0.1014 |
| 111 | V5 | 0.3040 | 0.1162 | 0.1338 | 0.0469 | 0.1050 |
| 111 | M | 0.3014 | 0.1497 | 0.1456 | 0.1097 | 0.1089 |
| 112 | V5 | 0.3313 | 0.1072 | 0.1523 | 0.1434 | 0.1179 |
| 112 | M | 0.3232 | 0.1248 | 0.1086 | 0.1275 | 0.1332 |

| t | d̄ = mean of S(V5) − S(M) | standard error | d_s (seeds 110, 111, 112) |
|---|---|---|---|
| 0.5 Gyr | +0.0073 | 0.0025 | +0.0111, +0.0027, +0.0082 |
| 1 Gyr | −0.0084 | 0.0177 | +0.0258, −0.0336, −0.0176 |
| 2 Gyr | −0.0006 | 0.0230 | −0.0338, −0.0118, +0.0437 |
| 4 Gyr | −0.0450 | 0.0313 | −0.0880, −0.0629, +0.0159 |
| 1–4 Gyr (reported, not deciding) | −0.0132 | 0.0049 | −0.0205, −0.0038, −0.0153 |

**Test bodies left at 4 Gyr:**

| seed | V5 | M |
|---|---|---|
| 110 | 541 | 553 |
| 111 | 570 | 544 |
| 112 | 561 | 572 |

## What follows (criteria section 4)

**"No growing bias found":** the production run's 1–4-Gyr result stands with the scope of
`docs/production-criteria.md` section 5, now with this check of the long-time residual risk.

## Power, and what the result does not say

As the criteria require, stated explicitly: three pairs can find only large biases, about 0.05 in R (stated in
`docs/equivalence-criteria.md`). "No growing bias found" is not evidence that there is none.

Assessment, not part of the criteria:
- **d(4 Gyr) is close to the threshold:** −0.045 against 0.05, at 1.4 standard errors. Two of the four conditions
  hold, and the sign is negative at 1, 2 and 4 Gyr: V5 lower than MERCURIUS.
- **The single values scatter widely.** Seed 112 has the opposite sign at 2 and 4 Gyr. With about 380–440 distant
  survivors per run at 4 Gyr, R of one snapshot has a noise of about 0.89/√n ≈ 0.045 (Q2 of the criteria). That is
  the size of the differences themselves. The 11 snapshots of a window share most particles, so the window mean
  reduces that noise only partly.
- **S(1–4) and d(0.5 Gyr) are not significant.** With three pairs the mean divided by its standard error follows a t
  distribution with 2 degrees of freedom (as in the equivalence test).
  - S(1–4), reported and not deciding: −0.0132 ± 0.0049, t = −2.68, two-sided p ≈ 0.12. It is negative in all three
    seeds and smaller than the margin of the equivalence test (±0.035). The criteria do not judge it.
  - d(0.5 Gyr): +0.0073 ± 0.0025, t = 2.97, p ≈ 0.10.
  - d(4 Gyr): t = −1.44, p ≈ 0.29.
  - The first version of this report called −0.0132 "2.7 standard errors from zero". The ratio is right, but it is
    not a significance with only 2 degrees of freedom.
- **The noise floor at late times.** An isotropic sample of n bodies gives an expected R of about 0.89/√n (Q2 of the
  criteria).
  - At 4 Gyr the long runs have about 417 distant survivors per run on average (window 3.9–4 Gyr; 412 at 4 Gyr
    itself), so the noise floor is about 0.044.
  - That is as large as R of the production run at 4 Gyr (0.052).
  - So the long runs cannot test the late-time strength, whatever the methods do. They are informative up to about
    1–2 Gyr: at 1 Gyr about 705 distant survivors (floor 0.034), at 2 Gyr about 576 (floor 0.037), against S of
    0.08–0.15.
  - The production run, with 14,196 bodies in S_BB at 4 Gyr, has a floor of 0.0075. Its R(4 Gyr) = 0.052 lies about
    7 times above it (`docs/production-result-20261110.md`).
- **Taken together:** the data are compatible with no difference, and with a difference of a few hundredths in R at
  late times. Three pairs cannot tell these apart, and after about 2 Gyr their own noise floor reaches the size of
  the signal. The production report states this as the limit of the long-time check.

## The runs and the checks before the evaluation

- **V5:** `p9long-v5-ac47329` on the A100, p9gpu `7666c5ba…`, three runs at once, 40 segments of 100 Myr. Ended
  2026-11-10 04:27Z without errors.
- **M:** `p9long-merc-ac47329` on CPU 1, p9sim `b14f7956…`, 24 slices of 250, 200 segments of 20 Myr.
- **Archives:** sha256 equal to the reported ones. Backed up encrypted at three places and restore-checked by the
  project lead (2026-11-10 09:12).
- **Checksum lists:** 1,188 and 28,987 files, timestamped before the evaluation.
- **All segments consistent:** 120 of V5 and 4,800 of M. The hashes in `DONE` equal the files, the result lines equal
  `segments.tsv`, `final.state` equals `final_state_sha256`, N runs on continuously, and the state of each last
  snapshot equals the next segment's input.
- **Start values paired:** at t = 0 the slices of each seed hold exactly the 2,000 test bodies of the V5 run, with
  the same values.
- **Model counters:** steps at the sub-step cap in 5 V5 segments; one collision with Saturn (V5 s110 segment 29);
  no encounter removal in M.

## Deviations (reported; none changes the evaluation)

1. **The evaluation tool was written after the runs.** Entry 3 fixed the criteria but no program. `tools/long_eval.py`
   was written on 2026-11-10, before anyone looked at R.
   - It was tested on synthetic job trees and on the equivalence runs, where it reproduces the published S of seed 101
     exactly.
   - It was committed (6a69854) and timestamped before the evaluation.
2. **Two cases the criteria left open** (L1, L2) were decided by the project lead before the evaluation. They did not
   arise.
3. **No resume test of a V5 run** (interim check, criteria section 5).
   - The V5 runs went through without interruption, so no V5 run was stopped and resumed.
   - The M run was stopped once and resumed (2026-11-04 17:10Z; 17 lines "stopped (signal)" in `run.log`, one per
     running slice and the run script). Its chains are consistent, and one segment recomputed on the laptop gave the
     server's hash.
   - For V5, the bit reproducibility rests on the package check (42 cases `ALL SAME`) and on the resume rule of the
     package, without a test in the run itself.
4. **The V5 part ran on the A100**, not the L40S (addendum of 2026-11-04, section 9 of the criteria, before any run).
5. **Correction to the procedure** (af2e058, section 1). It says the bytes of a snapshot written again by `p9sim last`
   differ because of "pointer fields of the archive format". The reason is in `docs/reproducibility.md` of
   medas-p9-search-bb2021: REBOUND writes wall times, a random seed and platform-dependent fields into the archive.
   The states are equal, so the check is unaffected.
   Section 1 also counts "17 stops". It was one stop of the M run on 2026-11-04 17:10Z, which wrote 17 lines in the log.
