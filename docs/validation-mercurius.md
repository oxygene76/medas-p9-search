# Acceptance criteria: p9gpu with the radius rule against REBOUND MERCURIUS

Recorded 2026-10-19 evening, as specified by the project lead (wording below).
**Note on timing:** the MERCURIUS control (`runs/val/merc`) and the p9gpu run
(`runs/val/gpu-2000`) had already finished (19:45) and a first comparison had
been reported (`docs/close-encounters.md`, evidence 2) when these criteria
were written down; they were not chosen with knowledge of a pass or fail
beyond that report, and are applied unchanged.

## The criteria (verbatim)

> Die Zahl der Überlebenden weicht höchstens um die in der GPU-Rechnung per
> Regel entfernten Körper plus 2σ ab; KS-Tests für a, q, i, ϖ, Ω der
> Überlebenden je p ≥ 0,01; R(Δϖ) und R(ΔΩ) innerhalb von 2
> Bootstrap-Standardfehlern. Wird ein Kriterium verfehlt: 4-Gyr-Lauf
> weiterlaufen lassen, als vorläufig markieren, Simulationsseite bleibt leer,
> Entscheidung morgen mit mir.

## How they are applied (where the wording leaves a choice: the stricter reading)

Runs: the same 2,000 test particles (make_ic, seed 9), 50 Myr; MERCURIUS =
`runs/val/merc/part00..15` pooled, p9gpu = `runs/val/gpu-2000`. Evaluated at
the end, 50 Myr (also reported, for information, at 10, 20 and 30 Myr).
Barycentric osculating elements (as `tools/analyze.py`); ϖ = Ω + ω, Δ relative
to Planet Nine in the same run and snapshot.

1. **Survivors**: |N_MERCURIUS − N_p9gpu| ≤ n_rule + 2σ, with n_rule the
   test particles p9gpu removed by close encounter (all planets, from
   result.json), σ = sqrt(σ_M² + σ_G²) and σ_X = sqrt(N₀ f (1 − f)) the
   binomial standard deviation of each survivor count (N₀ = 2,000, f the
   surviving fraction of that run).
2. **KS**: two-sample Kolmogorov–Smirnov tests of a, q, i, ϖ and Ω over **all
   survivors** of each run (angles as values in [0°, 360°)); each p ≥ 0.01.
3. **R**: for Δϖ and ΔΩ, |R_M − R_G| ≤ 2 sqrt(SE_M² + SE_G²), SE from 2,000
   bootstrap resamples per run (numpy default_rng(1)). Applied to **both** the
   distant particles (a > 230 au, q > 42 au, as in all clustering analyses here)
   and all survivors; the criterion holds only if it holds for both.

All three must hold. Tool: `tools/eval_mercurius.py`; output in
`runs/val/eval-mercurius.txt` and below.

## Result (2026-10-19, `runs/val/eval-mercurius.txt`): **criteria missed**

At 50 Myr:

| criterion | MERCURIUS | p9gpu, rule | limit | |
|---|---|---|---|---|
| survivors | 1,933 | 1,521 | \|diff\| 412 ≤ 472 + 2σ (41.4) = 513 | pass |
| KS a / i / Ω (all survivors) | | | p ≥ 0.01 | pass (0.117 / 0.126 / 0.171) |
| KS q | | | p ≥ 0.01 | **fail** (p = 1.8e-14; already at 10 Myr: 0.0028) |
| KS ϖ | | | p ≥ 0.01 | **fail** (p = 0.0019) |
| R(Δϖ), distant (a > 230, q > 42) | 0.624 (n 793) | 0.629 (n 753) | ≤ 0.040 | pass (0.004) |
| R(ΔΩ), distant | 0.709 | 0.700 | ≤ 0.036 | pass (0.009) |
| R(Δϖ), all survivors | 0.095 | 0.192 | ≤ 0.048 | **fail** (0.097) |
| R(ΔΩ), all survivors | 0.551 | 0.622 | ≤ 0.034 | **fail** (0.071) |

Reading: the removal at Neptune (its Hill radius, 389 of the 472 removals)
takes out the particles that MERCURIUS follows through their encounters; the
perihelion distribution of the survivors changes and **the whole surviving
population appears more strongly clustered than with MERCURIUS** (R(Δϖ) twice
as large). The distant population (a > 230 au, q > 42 au), on which the
clustering analyses here are based, agrees within the noise.

Consequence as specified: the corrected 4-Gyr run (`runs/gpu-4gyr-b`, started
2026-10-19 18:50) continues, **marked provisional**; the page "Simulations"
stays empty; decision with the project lead on 2026-10-20.

## Additional result for the decision: p9gpu without encounter removal

The same 2,000 test particles with p9gpu **without** any removal at the planets
(`runs/val/gpu-2000-noenc`: encounters are followed with the fixed step of
0.5 yr; only the distance rules remove, 88 in 50 Myr), evaluated with the same
tool and criteria (`runs/val/eval-mercurius-noenc.txt`): **all criteria hold
at every time** (10, 20, 30, 50 Myr). At 50 Myr: survivors 1,933 / 1,912
(|diff| 21 ≤ 0 + 2σ = 24.4); KS a, q, i, ϖ, Ω p = 0.83, 0.96, 1.00, 0.94,
0.91; R(Δϖ) distant 0.624 / 0.624, all 0.095 / 0.092; R(ΔΩ) distant
0.709 / 0.692, all 0.551 / 0.560. So, statistically, following the encounters
with the fixed step comes much closer to MERCURIUS than removing them at the
rule's radii. Not decided here; input for the decision of 2026-10-20 (with
the flyby check: the encounters below 1.5 steps per flyby are then integrated
inaccurately, and how many there are is what method "step" counts).

## Where the rule removed the 412 (2026-10-20)

The rule run computed again with the fate of every test particle
(`runs/val/gpu-2000-rerun`, `P9_REMOVED_OUT`; the same result hash as
`runs/val/gpu-2000`, so the same run), paired with MERCURIUS at 50 Myr:

| removed by the rule at | removed | of them alive in MERCURIUS at 50 Myr |
|---|---|---|
| Neptune (0.7759 au) | 389 | 333 |
| Planet Nine (0.5 au) | 82 | 80 |
| Uranus (0.6643 au) | 1 | 1 |
| distance rules | 7 | 6 |

Alive in the rule run but lost in MERCURIUS: 8. Difference of the survivors:
333 + 80 + 1 + 6 − 8 = 412. Mostly Neptune, then Planet Nine.
