# Cause of the R(Δϖ) deviation between p9gpu and MERCURIUS (in progress)

A new file (`docs/status-2026-10-21-open-deviation.md` states the open
deviation; the documents of the manifests are not changed). Steps are
resumable; data in `runs/cause/` and `runs/freq/`.

## 1. Setup of both programs (2026-10-21)

Identical: start file (masses, the inner planets in the Sun, Planet Nine, G,
year of 365.25 days, dt 0.5 yr, the test particles), elements and selection of
the distant particles (the same tools). The only difference is the integrator,
also for the planets: MERCURIUS (REBOUND, democratic heliocentric WH with dt
0.5 yr, IAS15 within 3 Hill radii of a planet: about 21 au around Planet Nine)
against p9gpu (own WH, the planets with 8 inner steps, smooth transition
within 2 au of Planet Nine, 2.7–7.4 au of the giant planets).

## 2. Secular frequencies of the planets (`runs/freq`, `tools/freq_compare.py`)

Planets alone, 50 Myr, against IAS15 (relative difference; phase drift over
200 Myr):

| | p9gpu v5 (8 inner steps) | WHFast dt 0.5 = p9gpu with 1 inner step | MERCURIUS dt 0.5 |
|---|---|---|---|
| g5 | −4.9e-6 (−1°) | −3.3e-4 (−78°) | −3.0e-4 (−70°) |
| g6 | −3.2e-6 (−5°) | −2.9e-4 (−449°) | +1.3e-4 (+204°) |
| s6 | −1.7e-7 | −1.4e-6 | −3.9e-5 (+57°) |
| g7, s7, g8, s8 | ≤ 2.5e-6 | ≤ 2.2e-5 | ≤ 4.1e-5 |

The planets alone are not chaotic (a 1e-12 perturbation of Jupiter stays at
0.001° in 200 Myr); the phase differences between the integrations are step
size effects. IAS15 against the literature (Laskar et al. 2011, without
Planet Nine): g7 to 8e-7, g6, g8, s6–s8 to 2–3e-4, g5 −2.9e-3 (the model:
inner planets in the Sun, no relativity), so the literature anchors the setup
to about 3e-4, not finer. Planet Nine's own precession is the same in all
integrations (to 1e-3° in 200 Myr).

## 3. Precession rates over 10 Myr (`runs/freq/tp-rates-bootstrap.txt`)

200 distant particles, the same start values, against IAS15: no integrator
differs significantly in the median rate, the spread or the slope of the rate
against ln a (all bootstrap intervals include zero). 10 Myr are too short.

## 4. Decomposition with the ensemble data (`runs/cause/decompose.txt`, `rates.txt`)

`tools/cause_extract.py`, `cause_decompose.py`, `cause_rates.py`; pairs of runs
across the groups (G–M, 8 pairs) against pairs within a group (6 G–G, M1–M0:
chaos only).

- Which bodies are distant: the same numbers (951 against 948 at 200 Myr) and
  the same overlap of the selection in G–M pairs as within the groups (0.84 to
  0.86 of the bodies).
- The difference of R, 200 Myr: −0.040, of it −0.028 from the angles of the
  same bodies and −0.012 from the composition; the pairs within a group have
  |angles| 0.016, |composition| 0.013. From about 135 Myr the angle part of
  G–M is negative at every time and grows.
- The mean direction of the cluster is the same (243° against 244° at
  200 Myr): no common rotation.
- By orbit: lower in G in every bin of a (200 Myr: a 230–300 au 0.166 against
  0.236, 300–400 au 0.676 against 0.701, > 400 au 0.749 against 0.774), and
  only for q > 50 au (0.577 against 0.619); q 42–50 au, the bodies close to
  Neptune, agree.
- Precession rates of the same bodies over 100 Myr: in 100–200 Myr the spread
  of the rates is 15 ± 7.5 % larger in G than in M (within the groups −6.5 % and
  −0.7 %); in 50–150 and 20–120 Myr no difference. No common offset.
- Neptune's heliocentric longitude drifts by about −2.6°/Myr between G and M
  (M1–M0: 0); its varpi differs by up to ±20°.

So the deviation is a faster dispersal of the longitudes of perihelion of the
same detached bodies (q > 50 au) in p9gpu after about 100 Myr, not a
different selection, a rotation of the cluster or Planet Nine's orbit.

## 5. Open: which integrator is right

Tests that separate the hypotheses:
- REBOUND WHFast (dt 0.5, democratic heliocentric, no encounter zone) for
  member 0 on the laptop (`runs/cause/wh05`, running): like p9gpu → the
  difference lies in MERCURIUS' treatment of encounters (IAS15 zone);
  like MERCURIUS → something particular to p9gpu.
- Package for the GPU server (`build/p9cause-*` on branch feat/cause-package):
  the ensemble with half the time step (J1) and with a 20.95-au transition
  zone around Planet Nine (J2), unchanged p9gpu v5.
