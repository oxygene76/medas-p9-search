# Overall rule for acceptances with many single tests (proposal, decision pending)

Asked for by the project lead on 2026-10-20 (point 4), for future acceptances,
to be fixed before their runs.

## The problem

An acceptance like `docs/validation-smooth-200myr.md` checks about 30 single
criteria (at 3 times: survivors, 5 KS tests, 4 R comparisons, McNemar). A
limit of 2 standard errors lets a correct integrator fail a single comparison
with probability about 4.6 %. With N independent tests the number of such
failures is binomial (the tests are in fact correlated, which changes the
numbers somewhat, not the point):

| N | expected false failures | P(≥ 1) | P(≥ 2) | P(≥ 3) | P(≥ 4) |
|---|---|---|---|---|---|
| 12 | 0.55 | 43 % | 10 % | 1.5 % | 0.2 % |
| 20 | 0.91 | 61 % | 23 % | 6 % | 1.2 % |
| 30 | 1.36 | 75 % | 40 % | 15 % | 4.6 % |
| 40 | 1.82 | 85 % | 55 % | 27 % | 11 % |

So a single failure among 30 says almost nothing by itself.

## Proposal

For a series of N single tests, each with its own limit as before:

1. **Count**: the series passes if the number of failed single tests is below
   the smallest k with P(≥ k) ≤ 5 % under the binomial law above (N = 30: at
   most 3 failures; N = 12: at most 2).
2. **No large miss**: no single test beyond a limit corrected for the number
   of tests (Bonferroni at 5 %: for N = 30, 3.1 standard errors instead of 2;
   for KS and McNemar p ≥ 0.05 / N instead of 0.01 or 0.05).
3. **No pattern**: failures of the same measure at successive times count as
   one excursion, not several; a measure that fails at the last two times is
   followed up regardless of 1 and 2 (an ensemble, as in
   `docs/validation-ensemble-200myr.md`).

The rule is fixed in the criteria file of each acceptance before its runs,
with N counted there.
