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

## Result (2026-10-20, `runs/val/eval-smooth-200myr.txt`): **not met at 200 Myr** (one criterion)

p9gpu with the smooth transition (`runs/val/gpu-2000-smooth`, program 47127ba,
cap 4,096; result 701b3c67…, 17,303 s on the RTX 5080 Laptop GPU, 1,542 steps
at the cap) against MERCURIUS (`runs/val/merc2`):

| t | survivors M / G (limit) | KS p a, q, i, ϖ, Ω | losses only G / only M / both, McNemar p | R(Δϖ) distant, all | R(ΔΩ) distant, all |
|---|---|---|---|---|---|
| 100 Myr | 1,783 / 1,766 (17 ≤ 40.0) | 0.30, 0.92, 0.92, 1.00, 0.69 | 138 / 121 / 96, 0.32 | 0.695/0.690, 0.242/0.239 | 0.727/0.727, 0.537/0.541 |
| 150 Myr | 1,617 / 1,612 (5 ≤ 49.9) | 0.98, 0.90, 0.23, 0.84, 0.16 | 171 / 166 / 217, 0.83 | 0.686/0.669, 0.344/0.333 | 0.754/0.745, 0.586/0.561 |
| 200 Myr | 1,504 / 1,502 (2 ≤ 54.7) | 0.98, 0.82, 0.94, 0.58, 0.33 | 173 / 171 / 325, 0.96 | **0.608/0.545** (0.063 > 2 SE 0.051), 0.340/0.306 | 0.769/0.745, 0.615/0.596 |

At 100 and 150 Myr all criteria hold; at 200 Myr all but R(Δϖ) of the distant
particles (a > 230 au, q > 42 au).

**Do the steps at the cap cause it?** (decision of 2026-10-20: check with the
counter of capped steps.) No: of the 955 distant survivors at 200 Myr only 3
had a step at the cap (`flybys.tsv`, sub_capped); without them R = 0.5446
(with them 0.5451). Without all 27 that had a flyby closer than 0.1 au,
0.5526.

**Its course** (`runs/val/r-series-smooth.txt`, every 5 Myr from 55 Myr;
difference to MERCURIUS in units of the 2-SE limit): the fixed-step run
(`gpu-2000-count2`) stays below MERCURIUS throughout, −0.05 to −0.69 limits;
the smooth run within −0.3 limits up to 145 Myr, then lower, beyond the limit
from 175 Myr (−1.09 to −1.24). R falls in all three runs after about 140 Myr
(MERCURIUS 0.693 → 0.608), faster in both p9gpu runs. The differences at
successive times are not independent (the same particles), so this is one
excursion, not several.
