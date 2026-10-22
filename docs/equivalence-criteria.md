# Criteria: is the production method equivalent to MERCURIUS? (draft)

Written 2026-10-22, before any of the runs below exists. A draft for the
project lead; binding only once accepted, and not changed afterwards. All
earlier runs (`docs/cause-analysis.md`, `docs/validation-*.md`) count as
hypothesis; this decision rests only on the new runs below.

## Question

Does the method of the production run (p9gpu v5, smooth transition) give the
same clustering of the distant bodies as MERCURIUS, within a margin that is
small against the uncertainty of the observed clustering? The same question
for plain Wisdom–Holman (p9gpu's fixed step). Two equivalence tests:

- (1) V5 against M
- (2) WH against M

## Margin: Δ = ±0.035

The observed clustering rests on about a dozen objects (Brown & Batygin 2021:
11 objects with 150 < a < 1,000 au, q > 42 au). For 11–12 angles from a von
Mises distribution with R between 0.6 and 0.7, the sample R scatters with an
sd of 0.11–0.14 (simulated, 200,000 samples; at R = 0.6 and 12 objects
0.137): about **±0.14 for one standard deviation**. An integrator bias of Δ
shifts the comparison of a model with the observation by Δ / 0.14 of that
standard deviation. Δ = 0.035 = 0.14 / 4 allows at most a quarter of a
standard deviation (e.g. a 2.0σ difference would read as between 1.75σ and
2.25σ). The models' own sampling noise (about 0.01 per run) is not part of
this margin.

## Runs

Configuration of the production run (medas-p9-search-bb2021,
`feat/bb2021-setup`; `runs/prod/job.json`): Brown & Batygin (2021) start
conditions, a 150–500 au, q 30–50 au, i 0–25°, inner removal at 4.5 au,
dt 0.5 yr, 0 to 200 Myr, a snapshot every 1 Myr.

- **Start values:** 9 new sets, seeds 101 to 109, 4,000 test particles each,
  member 0 (no perturbation). Not used before; neither the validation's seed 9
  nor the production run's seed 21.
- **Each set in all three groups** (paired by seed):

| group | method | program |
|---|---|---|
| V5 | p9gpu v5 as in the production job (smooth transition, planets with 8 inner steps, collisions at the planets' radii, FP64) | the p9gpu binary of the production package p9prod-9a084ed (L40S) |
| WH | p9gpu fixed step (`--encounter-method step --no-removal`, planets one step per dt) | the same binary (laptop GPU) |
| M | MERCURIUS, r_crit 3 Hill radii, no encounter removal (as M1 of the ensemble) | p9sim of `feat/bb2021-setup` (CPU; slices of the 4,000 particles) |

- Before the runs: each program is checked bit for bit against the reference
  machine on a short piece of its jobs (as the check of p9prod-9a084ed).
- No interim look at R, no change of the number of runs after a look. A run
  that fails for technical reasons is repeated with the same job; no run is
  left out because of its result.

## Statistic

Per run S = the mean of R(Δϖ) of the distant survivors (a > 230 au,
q > 42 au; Δϖ relative to Planet Nine) over 160, 165, …, 200 Myr (9 times).
Chosen before the runs instead of R at 200 Myr alone: the same late phase,
less noise (between runs 0.012 instead of 0.017 with 2,000 particles,
`docs/cause-analysis.md` section 12). For information only (no decision):
R at 200 Myr, and S with the cut of the observed sample (150 < a < 1,000 au,
q > 42 au).

## Test

Per seed s: d_s = S(V5, s) − S(M, s) and e_s = S(WH, s) − S(M, s). For each
of the two comparisons, the mean of the 9 differences and its two-sided 95 %
interval (t distribution, 8 degrees of freedom). That is the two one-sided
tests at α = 0.025 each, i.e. α = 0.05 split over the two comparisons
(Bonferroni).

- **Equivalent:** the interval lies inside (−0.035, +0.035).
- **Different:** the interval lies entirely outside it.
- **Not shown:** otherwise.

The production run is accepted on the method side only if (1) is
"equivalent". (2) decides nothing for the production run; it shows whether
plain Wisdom–Holman would be equivalent too.

## Size, power, cost

Noise model from section 12 of `docs/cause-analysis.md`: the sd between runs
of S is 0.012 at 2,000 particles and falls as 1/√N. A pair difference has
√2 times the sd of one run. Power of the test (Monte Carlo, 200,000 trials;
in brackets with an sd of 0.015 instead of 0.012):

| design | particles per group | true difference 0 | 0.01 | 0.02 | 0.025 |
|---|---|---|---|---|---|
| 18 × 2,000 | 36,000 | 1.00 (1.00) | 1.00 (1.00) | 0.94 (0.81) | 0.66 (0.47) |
| **9 × 4,000** | **36,000** | **1.00 (1.00)** | **1.00 (0.99)** | **0.91 (0.75)** | **0.59 (0.42)** |
| 6 × 6,000 | 36,000 | 1.00 (1.00) | 1.00 (0.98) | 0.85 (0.67) | 0.52 (0.37) |
| 6 × 8,000 | 48,000 | 1.00 (1.00) | 1.00 (0.99) | 0.93 (0.79) | 0.64 (0.46) |

9 × 4,000: with a true bias of v5 up to 0.02 (the hypothesis from the earlier
runs: about −0.022), equivalence is found with a probability of 0.75–0.91.
Fewer, larger runs lose degrees of freedom at the same cost.

Cost (estimates; the first segment of each kind gives the real rate):

| group | 9 × 4,000 | where |
|---|---|---|
| WH | about 2.5–3 h per run, about 25 h | laptop GPU (fixed step: 43 s per Myr up to 6,000 particles) |
| V5 | about 3–10 h per run, about 1–4 days | L40S, as a package (v5 on the laptop: 180 s per Myr for 8,000 particles; L40S factor 1–2) |
| M | about 100 core hours per run, 900 core hours | appmdp-05, as a CPU package: with 16 threads about 2.3–3.5 days |

(18 × 2,000 costs the same for M and about twice the GPU time, because the
GPU time per run hardly depends on the number of particles up to 6,000.)
