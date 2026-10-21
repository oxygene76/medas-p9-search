# Acceptance criteria: an ensemble of p9gpu and MERCURIUS runs up to 200 Myr

Recorded 2026-10-20, **before** any of the runs below is started. Decision of
the project lead of 2026-10-20, after the comparison of
`docs/validation-smooth-200myr.md` failed by one criterion at 200 Myr
(R(Δϖ) of the distant particles, 0.545 against 0.608): that comparison stays
documented as failed and its criteria are not changed afterwards; instead of a
single repetition, a small ensemble, so that the run-to-run scatter of R is
measured instead of assumed.

## Runs

The 2,000 test particles of the earlier comparisons (`tools/make_ic.py`, seed
9). Ensemble members (`make_ic.py --members`): member 0 is the set itself;
member m ≥ 1 has each test particle's barycentric start position multiplied,
per component, by 1 + 1e-12 u, u uniform in [−1, 1] from the seed (9, m, i).

- **p9gpu, G0–G3**: members 0, 1, 2, 3 in one job (`runs/val/ens-gpu`,
  `p9job make --program p9gpu --encounter-method smooth --n-tp 2000 --seed 9
  --members 0,1,2,3`), 0 to 200 Myr, a snapshot every 1 Myr, the smooth
  transition of the version accepted by the tests of `docs/substeps-plan.md`
  (its commit is in job.json), with collisions at the physical radii. The test
  particles do not interact, so the members of one job are four independent
  runs; G0 is the repetition of `runs/val/gpu-2000-smooth` with the new
  version.
- **MERCURIUS, M0**: the existing run (`runs/val/merc` 0–50 Myr and
  `runs/val/merc2` 50–200 Myr, member 0).
- **MERCURIUS, M1**: member 4, the same settings as M0 (p9sim, MERCURIUS,
  r_crit 3 Hill radii, dt 0.5 yr, no encounter removal; 16 slices of 125
  particles on 16 CPU cores), 0 to 200 Myr in one job per slice
  (`runs/val/ens-merc`), a snapshot every 1 Myr. Started after the CPU tests
  of the new version.

## Measures

For each run k and each time t = 5, 10, …, 200 Myr: R_k(Δϖ) and R_k(ΔΩ) of
the distant survivors (a > 230 au, q > 42 au; as `tools/eval_mercurius.py`).
Per integrator the mean over its runs (m_G over G0–G3, m_M over M0–M1); the
run-to-run scatter s is the pooled standard deviation of the six runs about
their own integrator's mean, s² = (Σ_G (R_k − m_G)² + Σ_M (R_k − m_M)²) / 4.

## Criteria

1. **R**: |m_G − m_M| ≤ 2 s, for R(Δϖ) and for R(ΔΩ), at each of 100, 150 and
   200 Myr. The course every 5 Myr is reported.
2. **Systematic**: if at 200 Myr all four p9gpu values of R(Δϖ) lie below both
   MERCURIUS values (or the same for R(ΔΩ)), the difference counts as
   systematic and its cause is searched, whatever criterion 1 says. (Without a
   real difference, this happens with probability 1/15 for one measure.)

The ensemble passes if criterion 1 holds and criterion 2 does not apply.

Also reported, per run and not part of the decision: the criteria of
`docs/validation-mercurius-200myr.md` (survivors, KS tests, R within 2
bootstrap standard errors, losses paired by test particle with McNemar) for
each G_k against M0 and against M1, and M1 against M0, at 100, 150 and
200 Myr; the collisions per planet and the steps at the cap.

## Result (2026-10-21, `runs/val/eval-ensemble.txt`): **not passed**, the difference is systematic

Runs: G0–G3 `runs/val/ens-gpu` (v5, 79c16e2; result 5345318f…, 36,045 s on
the RTX 5080 Laptop GPU, 8,000 test particles, 6,022 left at 200 Myr), M0
(`runs/val/merc`, `merc2`), M1 (`runs/val/ens-merc`, 3.2 h on 16 cores).

| t | R(Δϖ) G0, G1, G2, G3 | M0, M1 | m_G − m_M | 2 s | R(ΔΩ): m_G − m_M, 2 s |
|---|---|---|---|---|---|
| 100 Myr | 0.690, 0.678, 0.692, 0.686 | 0.695, 0.686 | −0.004 | 0.012 | +0.013, 0.028 |
| 150 Myr | 0.669, 0.667, 0.679, 0.661 | 0.686, 0.695 | **−0.022** | 0.014 | −0.011, 0.017 |
| 200 Myr | 0.545, 0.575, 0.574, 0.581 | 0.608, 0.610 | **−0.040** | 0.028 | −0.020, 0.026 |

- Criterion 1 fails: R(Δϖ) at 150 and 200 Myr (d = (m_G − m_M) / 2 s =
  −1.52 and −1.45); R(ΔΩ) holds at all three times.
- Criterion 2 applies: at 200 Myr all four p9gpu values of R(Δϖ) lie below
  both MERCURIUS values. Not an accident of the last time: from 135 Myr on all
  G lie below all M at every time, 14 times in a row (d down to −3.1 at
  165 Myr). Up to 130 Myr the two agree within the scatter: |d| ≤ 1 but for
  +1.02 (R(Δϖ), 20 Myr), +1.02 (R(ΔΩ), 25 Myr) and −1.35 (R(ΔΩ), 35 Myr), and
  all G below all M only twice, at 15 and 35 Myr, not in a row.
- The per-run criteria (27 comparisons: each G against M0 and M1, M1 against
  M0, at 100, 150, 200 Myr): survivors, KS and McNemar (p 0.21 to 1.00) hold in
  all; R within 2 bootstrap SE fails in 4: G2–M1 R(ΔΩ) distant at 100 Myr,
  G0–M0 R(Δϖ) distant, G0–M1 R(Δϖ) distant and all, G3–M0 R(ΔΩ) distant at
  200 Myr. M1 against M0 passes everything.

As decided, the cause is searched with cheap analyses only (no new long runs
without the project lead); see below.
