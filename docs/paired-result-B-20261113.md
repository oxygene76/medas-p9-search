# Paired test of set B, V5 against MERCURIUS: result (2026-11-13)

**Status:** result report, for independent review. The release file goes to the server only after the independent
recomputation of `result.json`, and nothing goes into the research note before the review.
- **Criteria:** `docs/bb2021-paired-test-proposal.md` as entered in entry e5 (chain entry #6, block 10814015,
  commit e83d960).
- **Steps:** `docs/paired-tests-evaluation-procedure.md` (80be9a5, timestamped before any look at R).
- **Files:** in `docs/paired-result-B-20261113/` as the tool wrote them (commit 26deff7).

## Verdict

**Equivalent** (criteria section 4): the mean of the 9 paired differences S(V5) − S(M) is +0.0002. Its two-sided
95 % interval, [−0.0075, +0.0079] (t, 8 degrees of freedom, sd 0.0100), lies inside the margin (−0.035, +0.035).

| seed | S(V5) | S(M) | d = S(V5) − S(M) |
|---|---|---|---|
| 341 | 0.6736 | 0.6788 | −0.0053 |
| 342 | 0.6992 | 0.6782 | +0.0210 |
| 343 | 0.7050 | 0.6917 | +0.0134 |
| 344 | 0.6860 | 0.6888 | −0.0028 |
| 345 | 0.6873 | 0.6936 | −0.0063 |
| 346 | 0.6909 | 0.6924 | −0.0015 |
| 347 | 0.6896 | 0.6923 | −0.0027 |
| 348 | 0.6885 | 0.6941 | −0.0056 |
| 349 | 0.6900 | 0.6983 | −0.0083 |

S is the mean over 160, 165, …, 200 Myr of R(Δϖ) of the distant survivors (a > 230 au, q > 42 au), as in the
equivalence test. The values per seed are rounded to 4 decimals, and d is computed from the exact values in
`result.json`.

## Information (reported, not deciding)

- **R at 200 Myr:** mean −0.0009, 95 % [−0.0088, +0.0069].
- **S with the observed cut** (150 < a < 1,000 au, q > 42 au): mean +0.0025, 95 % [−0.0072, +0.0122].
- **Test particles left at 200 Myr:** V5 29,930, M 29,885 (of 36,000).
- **Encounter shares of the V5 half** (percent of the test particles with at least one fast or close flyby; none for
  M, because p9sim keeps no flyby log per particle):

| planet, kind | V5 0–60 Myr | V5 0–200 Myr | V2 reference 0–60 Myr (equivalence runs) |
|---|---|---|---|
| Neptune fast / close | 13.60 / 3.86 | 30.40 / 11.58 | 17.61 / 4.47 |
| Uranus fast / close | 1.53 / 0.64 | 11.50 / 5.58 | 2.75 / 0.84 |
| Planet Nine fast / close | 2.14 / 0.43 | 6.38 / 1.37 | 1.09 / 0.26 |

Over 0–60 Myr:
- **Uranus:** fast flybys ×0.56 of the reference, close ×0.76, near the V2 short run of set B (×0.62 and ×0.86).
- **Planet Nine:** fast ×1.96 and close ×1.65, likewise as in V2 (2.14 % against the limit of 2.18 %).

This is the encounter regime that made the paired test necessary. It does not decide anything.

## Set A and set B side by side (assessment, not part of the criteria)

| | set A | set B |
|---|---|---|
| S(V5) − S(M), 95 % | +0.0067 [−0.0017, +0.0151] | +0.0002 [−0.0075, +0.0079] |
| R at 200 Myr | +0.0048 [−0.0067, +0.0163] | −0.0009 [−0.0088, +0.0069] |
| S with the observed cut | +0.0077 [+0.0001, +0.0153] | +0.0025 [−0.0072, +0.0122] |

- **Set A suggested a small offset,** of V5 about 0.007 above MERCURIUS (`docs/paired-result-A-20261112.md`, version 2).
- **Set B does not show it:** its mean is +0.0002, and every interval includes zero. Over both sets the differences
  scatter around zero, within the scatter of the single seeds (sd about 0.010).
- This weakens the reading of a systematic difference of v5 against MERCURIUS, but does not rule out a difference
  that depends on the configuration. Both sets are well inside the margin of ±0.035.
- This comparison was not registered and decides nothing.

## What follows (criteria section 5)

- **Set B "equivalent":** its 4-Gyr run with `p9bbsets-5b05cc3`, unchanged.
- **Both sets "equivalent":** set A, then set B on the A100, as ordered on 2026-11-04 (addendum 15). Set A has been
  running since 2026-11-12 09:08 UTC.
- **Release:** the tool wrote `BB-B.ok` (sha256 `18de161a4617849f982d2fe5e090d0a8b2cac49d4bad4c03212aab6ed84eaae1`).
  - Line 1 is `within the limits`. Line 2 is the release by the paired test, with the mean, the interval and the tool
    version 80be9a5.
  - The project lead copies it unchanged to `v2/BB-B.ok` of p9bbsets, keeping the V2 file as `v2/BB-B.v2`, after the
    independent recomputation.
  - The chain starts set B on its own after set A.
- **Named as the criteria require:**
  - The V2 deviation: the short run of set B was outside the limits of addenda 13 and 16 (Uranus fast ×0.62;
    `docs/bb2021-v2-result-20261106.md`).
  - The paired test covers 0–200 Myr only. It shows that v5 and MERCURIUS give the same clustering statistic for this
    Planet Nine over 0–200 Myr within ±0.035. It does not cover the 4 Gyr of the set's run.

## Checks before the evaluation

- **Archives:** sha256 equal to the server's. Backed up encrypted at three places and restore-checked by the project
  lead (2026-11-13).
- **Checksum lists:** made on the server; `sha256sum -c` over the unpacked archives gave all lines OK, with as many
  files as lines. Timestamped with OpenTimestamps before the evaluation.
- **Package files:** unchanged; only the files of the set-A jobs were absent.
- **Package checks:** ALL SAME (V5 72 cases, M 38 cases). The MERCURIUS half ended on 2026-11-13 at 10:09:08 UTC.
- **Segment chains:** `tools/check_segments.py` gave 153 of 153 jobs consistent, with the start values paired for all
  9 seeds.
- **libc6 on the server:** held since 2026-11-12 08:05 UTC; no libc update in the apt history; `check.sh` of the
  MERCURIUS half repeated after its end, ALL SAME. The hold stays until the end of set B.
