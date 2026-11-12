# Paired test of set A, V5 against MERCURIUS: result (2026-11-12)

**Status:** result report, for independent review. The release file goes to the server only after the independent
recomputation of `result.json`, and nothing goes into the research note before the review.
- **Criteria:** `docs/bb2021-paired-test-proposal.md` as entered in entry e5 (chain entry #6, block 10814015,
  commit e83d960).
- **Steps:** `docs/paired-tests-evaluation-procedure.md` (80be9a5, timestamped before any look at R).
- **Files:** in `docs/paired-result-A-20261112/` as the tool wrote them (commit 6b6ca59).
- **Set B** was still running when set A was evaluated. Nothing of set B was read (procedure, section 1).

## Verdict

**Equivalent** (criteria section 4): the mean of the 9 paired differences S(V5) − S(M) is +0.0067. Its two-sided
95 % interval, [−0.0017, +0.0151] (t, 8 degrees of freedom, sd 0.0109), lies inside the margin (−0.035, +0.035).

| seed | S(V5) | S(M) | d = S(V5) − S(M) |
|---|---|---|---|
| 331 | 0.4869 | 0.4966 | −0.0097 |
| 332 | 0.4667 | 0.4568 | +0.0099 |
| 333 | 0.4743 | 0.4722 | +0.0021 |
| 334 | 0.4947 | 0.4737 | +0.0210 |
| 335 | 0.4860 | 0.4744 | +0.0116 |
| 336 | 0.5002 | 0.4964 | +0.0038 |
| 337 | 0.4554 | 0.4582 | −0.0028 |
| 338 | 0.4825 | 0.4588 | +0.0237 |
| 339 | 0.4692 | 0.4689 | +0.0003 |

S is the mean over 160, 165, …, 200 Myr of R(Δϖ) of the distant survivors (a > 230 au, q > 42 au), as in the
equivalence test. The values per seed are rounded to 4 decimals, and d is computed from the exact values in
`result.json`.

## Information (reported, not deciding)

- **R at 200 Myr:** mean +0.0048, 95 % [−0.0067, +0.0163].
- **S with the observed cut** (150 < a < 1,000 au, q > 42 au): mean +0.0077, 95 % [+0.0001, +0.0153].
- **Test particles left at 200 Myr:** V5 28,369, M 28,373 (of 36,000).
- **Encounter shares of the V5 half**, percent of the test particles with at least one fast flyby (< 1.5 steps) or
  one close flyby (< 0.1 au). For M there are none, because p9sim keeps no flyby log per particle (criteria,
  decision 6).

| planet, kind | V5 0–60 Myr | V5 0–200 Myr | V2 reference 0–60 Myr (equivalence runs) |
|---|---|---|---|
| Neptune fast / close | 19.95 / 4.14 | 33.23 / 10.33 | 17.61 / 4.47 |
| Uranus fast / close | 5.44 / 1.26 | 18.12 / 6.02 | 2.75 / 0.84 |
| Planet Nine fast / close | 0.56 / 0.15 | 1.67 / 0.52 | 1.09 / 0.26 |

The Uranus shares over 0–60 Myr are again about twice the reference: ×1.98 for fast and ×1.50 for close flybys. That
is close to the V2 short run of set A (×2.02 and ×1.66). This is the encounter regime that made the paired test
necessary. It does not decide anything.

## What follows (criteria section 5)

- **Set A "equivalent":** its 4-Gyr run with `p9bbsets-5b05cc3`, unchanged.
- **Release:** the tool wrote `BB-A.ok` (sha256 `09c1771a2b637570edd234b25cdc7332756f03bd69cb8015ad16a7e487fa89c6`).
  - Line 1 is `within the limits`, which `start.sh` of p9bbsets and the A100 chain check.
  - Line 2 is the release by the paired test, with the mean, the interval and the tool version 80be9a5.
  - The project lead copies it unchanged to `v2/BB-A.ok` of p9bbsets, keeping the V2 file as `v2/BB-A.v2`, after the
    independent recomputation. Nobody writes the release line by hand.
- **Named as the criteria require:**
  - The V2 deviation: the short run of set A was outside the limits of addenda 13 and 16 (Uranus fast ×2.02, close
    ×1.66; `docs/bb2021-v2-result-20261106.md`).
  - The paired test covers 0–200 Myr only. It shows that v5 and MERCURIUS give the same clustering statistic for this
    Planet Nine over 0–200 Myr within ±0.035. It does not cover the 4 Gyr of the set's run. The paired long runs
    110–112 (r1) are the only check over 4 Gyr, for the production Planet Nine and with their limits.
- **Set B:** decided separately when its runs are complete.

## Checks before the evaluation

- **Archives:** sha256 as reported. Backed up encrypted at three places and restore-checked by the project lead
  (2026-11-12 09:15).
- **Package files:** unchanged; only the files of the set-B jobs were absent.
- **Package checks:** ALL SAME (V5 72 cases, M 38 cases).
- **Segment chains:** `tools/check_segments.py` gave 153 of 153 jobs consistent, with the start values of the 16 slices
  paired with their V5 job for all 9 seeds.
- **Checksum lists:** 1,099 and 9,549 files, timestamped with OpenTimestamps before the evaluation.
- **libc6 on the server** has been held since 2026-11-12 08:05 UTC (2.35-0ubuntu3.15), until the end of the MERCURIUS
  half. `cbrt` comes from the system libm (`docs/reproducibility.md`, correction of 2026-11-11). The check at the end
  of the MERCURIUS half repeats the 38 cases, which include the masses of sets A and B.
