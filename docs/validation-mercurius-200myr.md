# Acceptance criteria: p9gpu without removal against MERCURIUS up to 200 Myr

Recorded 2026-10-19 22:45, **before** any result of the runs below exists
(they are started after this commit). Specified by the project lead:
"Kriterien wie vereinbart bei 100, 150 und 200 Mio. Jahren, zusätzlich Verluste
paarweise mit McNemar p ≥ 0,05."

## Runs

- MERCURIUS: the 16 slices of `runs/val/merc` continued from their state at
  50 Myr (the last snapshot of each, `p9job next`) to 200 Myr, a snapshot
  every 1 Myr; CPU, no removal at the planets (as before).
- p9gpu without removal: the 2,000 test particles of `runs/val/gpu-2000-noenc`
  run again with flyby counting (`p9job make --no-removal`; the trajectories
  are bit-identical to the run without counting: checked by its result hash),
  then continued from 50 Myr to 200 Myr the same way.

## Criteria (all must hold at each of 100, 150 and 200 Myr)

As in `docs/validation-mercurius.md` (same tool, same readings):

1. Survivors: |N_MERCURIUS − N_p9gpu| ≤ n_rule + 2σ, with n_rule = 0 (p9gpu
   removes nothing at the planets) and σ the combined binomial standard
   deviation.
2. KS tests of a, q, i, ϖ, Ω over all survivors: each p ≥ 0.01.
3. R(Δϖ) and R(ΔΩ): |R_M − R_G| ≤ 2 bootstrap standard errors, for the
   distant particles (a > 230 au, q > 42 au) and for all survivors.
4. **New:** losses paired by test particle: b = lost by T only in p9gpu, c =
   lost by T only in MERCURIUS; exact two-sided McNemar test (binomial test of
   b against b + c with p = 1/2); p ≥ 0.05.

Tool: `tools/eval_mercurius.py` with `--mcnemar`; results below, added when
the runs are done.

## Result (2026-10-20, `runs/val/eval-mercurius-200myr.txt`): **all criteria met**

p9gpu without removal and **without sub-steps** (fixed step 0.5 yr;
`runs/val/gpu-2000-count` and its continuation `gpu-2000-count2`) against
MERCURIUS (`runs/val/merc`, `merc2`):

| t | survivors M / G (limit) | KS p a, q, i, ϖ, Ω | losses only G / only M / both, McNemar p | R(Δϖ) distant, all | R(ΔΩ) distant, all |
|---|---|---|---|---|---|
| 100 Myr | 1,783 / 1,756 (27 ≤ 40.4) | 0.43, 0.76, 0.87, 0.99, 0.89 | 145 / 118 / 99, 0.11 | 0.695/0.688, 0.242/0.238 | 0.727/0.718, 0.537/0.543 |
| 150 Myr | 1,617 / 1,611 (6 ≤ 49.9) | 0.75, 0.98, 0.94, 0.35, 0.63 | 165 / 159 / 224, 0.78 | 0.686/0.672, 0.344/0.330 | 0.754/0.762, 0.586/0.564 |
| 200 Myr | 1,504 / 1,500 (4 ≤ 54.7) | 0.95, 0.79, 0.26, 0.74, 0.11 | 161 / 157 / 339, 0.87 | 0.608/0.578, 0.340/0.344 | 0.769/0.768, 0.615/0.596 |

All R differences within 2 bootstrap standard errors. The excess of losses
seen at 50 Myr (74 against 53, McNemar p = 0.076, explained by 32 numerical
losses at close flybys, `docs/validation-mercurius.md`) has disappeared in the
noise by 100 Myr. The decision of 2026-10-20 stands regardless: close flybys
get sub-steps; this comparison is repeated with them as part of their
acceptance.
