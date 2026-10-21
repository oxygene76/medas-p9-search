# Group comparison of R(Δϖ): plan and sample size (proposal)

Written 2026-10-22, 00:00, **before** any result of the runs started on
2026-10-21 23:48 (`docs/cause-analysis.md` section 9) was looked at. A
proposal to the project lead; it becomes binding only when accepted, and is
not changed afterwards.

## Groups

| group | method | runs (after the night) |
|---|---|---|
| WH | plain Wisdom–Holman, dt 0.5 yr, no encounter zone: p9gpu fixed step (F = member 0, F1–F3) and REBOUND WHFast (W, member 0); the same integrator (section 8) | 5 |
| M | MERCURIUS, r_crit 3 Hill radii, dt 0.5 yr (M0 = member 0, M1 = 4, M2 = 5, M3 = 6) | 4 |
| V5 | p9gpu v5, smooth transition (G0–G3, members 0–3) | 4 |

Runs of the same member in different groups count as independent: they
separate at the chaos rate within about 0.2 Myr (section 8).

## Statistic and test

- Per run: R(Δϖ) of the distant survivors (a > 230 au, q > 42 au) at 200 Myr
  (`tools/eval_ensemble.py`). Secondary, for information: the mean of R(Δϖ)
  over 160–200 Myr in steps of 5 Myr.
- Per pair of groups: difference of the group means with a Welch t-test,
  two-sided, α = 0.05, and its 95 % interval.
- Comparisons: (A) WH against M, (B) V5 against WH, (C) V5 against M.

## Sample size

Run-to-run scatter σ ≈ 0.015 (pooled s of the ensemble at 200 Myr: 0.014; G
alone 0.016). Detecting a difference δ with power 1 − β needs about
n = 2 (z₁₋α/₂ + z₁₋β)² (σ/δ)² runs per group (plus about one for the t
distribution):

| δ | power 0.8 | power 0.9 |
|---|---|---|
| 0.02 (A, B: WH lies about 0.02 from each) | 9–10 per group | 12–13 per group |
| 0.04 (C: V5 against M) | 3–4 per group | 4–5 per group |

With 5 against 4 runs a difference of 0.02 is found with a power of only
about 0.5. For (A) and (B) at power 0.8: about 10 runs per group, i.e. 5 more
WH, 6 more M and 6 more V5.

## What follows from the outcome

- (A) significant, (B) not: plain WH without an encounter zone deviates from
  MERCURIUS by itself; the treatment of encounters (MERCURIUS' IAS15 zone,
  20.95 au around Planet Nine) is the candidate; J2 of `p9cause-008aaae` (v5
  with a 20.95-au zone around Planet Nine) tests it directly.
- (B) significant, (A) not: v5's smooth transition causes the deviation;
  search inside v5 (a fix only on its own branch, after the notary entry of
  manifest (a3)).
- Neither, with about 10 runs per group: differences below about 0.02 are not
  resolvable; (C) decides whether v5 against MERCURIUS stays systematic.
