# Decomposition of set A, addendum 3: spread over the four subsets, for the scale of BB-A-rin1 (2026-11-17)

**Status, stated plainly:** This addendum is written **after** the computation it describes, not before.
- The script `tools/sets_subset_spread.py` was committed before it ran (4eec855). It was run on 2026-11-17 at about
  23:15 local time, before this addendum existed. The project lead's request for a prior addendum came in afterwards.
- The numbers below were therefore seen before the tolerance rule of the BB-A-rin1 criteria draft was set.
- It happens after the knowledge of outcome 4, of the decomposition (addenda 1 and 2) and of the measurement of Fig. 4.
- Exploratory. **It changes nothing:** not the criteria of the sets, not the verdicts, not outcome 4.

## What, and what for

- **What:** for set A (job `BB-A`, checked archive `1c3c9f40…a9e0`), per subset of the evaluation (index blocks of 16,000
  as in `prod_eval.py`) and for the whole set, over all 301 snapshots of the window 1–4 Gyr:
  - M2: the mean over the snapshots of R of Δϖ in S_BB;
  - the inclination shares for 150 < a < 1000 au: < 30°, 30–40°, 40–50°, 50–70°, normalised to 0–70°; and the
    retrograde share (i > 90°) of all;
  - each for q > 42 au and for 42 ≤ q ≤ 100 au.
- **What for:** the spread band of the scale "the removal rule is not the cause" in the criteria draft of the run
  BB-A-rin1.

## Result (as computed, 4eec855, from a clean detached checkout)

| group | M2 | q > 42 au: < 30° / 30–40° / 40–50° / 50–70° / retrograde | 42 ≤ q ≤ 100 au: < 30° / 30–40° / 40–50° / 50–70° / retrograde |
|---|---|---|---|
| subset 0 | 0.0556 | 0.626 / 0.134 / 0.092 / 0.148 / 0.160 | 0.794 / 0.112 / 0.043 / 0.051 / 0.064 |
| subset 1 | 0.0455 | 0.619 / 0.135 / 0.095 / 0.150 / 0.173 | 0.792 / 0.107 / 0.046 / 0.055 / 0.073 |
| subset 2 | 0.0498 | 0.622 / 0.134 / 0.096 / 0.148 / 0.172 | 0.796 / 0.107 / 0.044 / 0.053 / 0.071 |
| subset 3 | 0.0504 | 0.622 / 0.134 / 0.095 / 0.149 / 0.178 | 0.793 / 0.109 / 0.045 / 0.052 / 0.070 |
| all | 0.0496 | 0.622 / 0.134 / 0.095 / 0.149 / 0.171 | 0.794 / 0.109 / 0.045 / 0.053 / 0.069 |

- M2 of the whole set (0.0496) equals M2 of the evaluation (0.050).
- The full values are in `docs/sets-decomposition-3-20261117/spread-A.json`.

## How the criteria draft uses it

The tolerance of each quantity is twice the largest deviation of a subset from the whole set:
- M2: 2 × 0.0060 = 0.012;
- each inclination share: 2 × 0.004 = 0.008;
- the retrograde shares: 2 × 0.011 = 0.022 (q > 42 au) and 2 × 0.0053 = 0.011 (42 ≤ q ≤ 100 au).

This rule was set after the numbers were seen (see the status above). The criteria draft says so.
