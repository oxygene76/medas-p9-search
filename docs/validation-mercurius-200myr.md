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

## Result

(added by the evaluation)
