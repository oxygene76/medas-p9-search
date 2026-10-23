# Two comparisons with the literature, planets only (criteria, 2026-10-23)

Written before any of the runs below. Planets only, on the laptop; the
equivalence test (`runs/equiv`, `tools/equiv_eval.py`, `tools/analyze.py`, the
packages) is not touched. Both comparisons check the setup of the planets; they
decide nothing about the production run.

## 1. Fundamental frequencies g5–g8, s6–s8

**Literature:** Laskar et al. 2011 (A&A 532, A89; arXiv:1103.1084v1), Table 6
"Main secular frequencies g_i and s_i of La2004 and La2010a", determined over
50 Ma for the outer planets (arcsec/yr; read from the arXiv PDF, sha256
`0e0103a8…c75a45`; Δ100 = their variation over 100 Myr):

| | La2004 | La2010a | Δ100 |
|---|---|---|---|
| g5 | 4.257452 | 4.257482 | 0.000030 |
| g6 | 28.2450 | 28.2449 | 0.001 |
| g7 | 3.087951 | 3.087946 | 0.000034 |
| g8 | 0.673021 | 0.673019 | 0.000015 |
| s6 | −26.347855 | −26.347841 | 0.000076 |
| s7 | −2.9925259 | −2.9925258 | 0.000025 |
| s8 | −0.691736 | −0.691740 | 0.000010 |

Both are models of the whole solar system (all planets, general relativity,
the Moon, Pluto as the ninth body).

**Runs** (`tools/planet_frequencies.py`, `runs/litcheck`), 0–50 Myr, a snapshot
every 1,000 yr (50,000):

| model | bodies | integrators, dt |
|---|---|---|
| A | the four giants; the inner planets' masses and momenta in the Sun (as the start files of all runs) | p9gpu (the binary of p9prod-9a084ed, CPU twin, planets one step per dt) and p9sim WHFast, dt 0.5 yr |
| B | A plus Planet Nine (Brown & Batygin 2021: 6.2 M_E, a 380 au, q 300 au, i 16°) | the same |
| C | all eight planets, the Sun alone, no Planet Nine | p9sim WHFast, dt 0.01 yr (about 24 steps per orbit of Mercury) |

**Frequencies:** for g_j the strongest line of e exp(iϖ), for s_j of
sin(i/2) exp(iΩ) of the planet (j = 5..8: Jupiter..Neptune; s6..s8), within
10 % of the literature value; heliocentric elements, ecliptic J2000; Hann
window, FFT zero-padded 8 times, the maximum refined by a golden-section
search; over the whole 50 Myr.

**What is compared, and the expectations fixed now:**
- (a) p9gpu against WHFast (A, B): the same integrator
  (`docs/cause-analysis.md` section 8). Expected: relative difference
  ≤ 1e-6 for every frequency.
- (b) A against La2004: our model lacks the inner planets as bodies, general
  relativity, the Moon and Pluto, and dt 0.5 yr adds the integrator's error.
  Expected: within 5e-3 relative for every frequency; larger is a finding to
  be explained.
- (c) C against A: the effect of the inner planets as separate bodies (and of
  the smaller step). C against La2004: expected within 1e-3 relative for
  every frequency, i.e. the inner planets explain most of (b); larger is a
  finding.
- (d) B against A: the effect of Planet Nine on the planets' frequencies,
  reported.
For scale: the difference La2004–La2010a and Δ100.

## 2. Solar obliquity, the cases of Bailey, Batygin & Brown (2016)

**Cases** (Bailey, Batygin & Brown 2016, AJ 152, 126; arXiv:1607.03963):
their Fig. 4, m9 = 15 M_E, a9 = 500 au, e9 = 0.5, i9 = 10°, 20°, 30°; and
the case of Batygin & Brown (2016) they discuss, 10 M_E, 700 au, e 0.6,
i 30°.

**Runs:** the four giants and Planet Nine only (the inner planets in the Sun),
the p9gpu binary of p9prod-9a084ed on the CPU, dt 0.5 yr, 4.5 Gyr backward
(a forward run of the start values with all velocities reversed, from a start
where the solar axis is parallel to the giants' plane), a snapshot every
10 Myr (`runs/litcheck/obl-*`); evaluated with `tools/solar_obliquity.py
nbody-eval`. The two cases computed on 2026-10-23 (`docs/solar-obliquity.md`)
are run again here with the same inputs.

**Compared:** the N-body obliquity after 4.5 Gyr against
- the secular model of Lai (2016) for the same geometry (`solar_obliquity.py`,
  fixed solar axis). Expected: within 10 %.
- Lai's small-angle formula (his eqs. 12–16). Expected: within 10 %.
- Bailey, Batygin & Brown: their Fig. 4 runs backward from today (i☉ = 6°) and
  gives a primordial obliquity of about 1–6°, smallest for i9 = 20°; the case
  of Batygin & Brown gives 3–5° in their model. Their solar axis precesses
  (solar J2, spin-down) and ours is fixed, so this comparison is reported, not
  judged.
