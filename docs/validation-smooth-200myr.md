# Acceptance criteria: p9gpu with the smooth transition against MERCURIUS up to 200 Myr

Recorded 2026-10-20, **before** the p9gpu run below is started (part of the
acceptance of the sub-steps, `docs/substeps-plan.md`; decision of the project
lead of 2026-10-20: "Abnahme mit unveränderten Kriterien").

## Runs

- MERCURIUS: as in `docs/validation-mercurius-200myr.md` (`runs/val/merc`,
  0–50 Myr, and `runs/val/merc2`, 50–200 Myr; the same 2,000 test particles,
  seed 9).
- p9gpu: `runs/val/gpu-2000-smooth`, one job from 0 to 200 Myr, a snapshot
  every 1 Myr, `p9job make --encounter-method smooth` (no removal at the
  planets; r_out 4 times the rule's radius, r_in = r_out / 10; the planets
  with 8 inner steps), the program of commit dadc425 or later with the same
  integrator.

## Criteria (all must hold at each of 100, 150 and 200 Myr)

Unchanged from `docs/validation-mercurius-200myr.md`, same tool
(`tools/eval_mercurius.py --mcnemar --n-rule 0`):

1. Survivors: |N_MERCURIUS − N_p9gpu| ≤ 0 + 2σ (combined binomial σ).
2. KS tests of a, q, i, ϖ, Ω over all survivors: each p ≥ 0.01.
3. R(Δϖ) and R(ΔΩ): |R_M − R_G| ≤ 2 bootstrap standard errors, for the distant
   particles (a > 230 au, q > 42 au) and for all survivors.
4. Losses paired by test particle: exact two-sided McNemar test, p ≥ 0.05.

Also reported, for information: the same at 50 Myr, and the pairing of the
losses of the fixed-step run of `docs/validation-mercurius.md` that were
numerical (are they kept now?).

## Result

(added by the evaluation)
