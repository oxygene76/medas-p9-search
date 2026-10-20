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

## Result

(added by the evaluation)
