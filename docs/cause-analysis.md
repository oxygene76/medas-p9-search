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
- Package for the GPU server: `p9cause-008aaae.tar.gz` (sha256
  `6c5dffd4239efaaf30934865e1a89693190edd32c639e7e9f653fc7497ea6fbf`, branch
  feat/cause-package, worktree medas-p9-search-cause): the ensemble with half
  the time step (J1) and with a 20.95-au transition zone around Planet Nine
  (J2), with the unchanged binary of p9prod-9a084ed (integrator identical to
  v5; on the ensemble's settings it gives the ensemble's bits, checked at
  1 Myr). Tested locally from an unpacked copy: check ALL SAME (40 of 40),
  both jobs write snapshots, stop.sh stops at once. Measured on the laptop with
  both jobs at once: J1 552 s/Myr, J2 305 s/Myr; on the L40S with the FP64
  factor 2.0 about 15 h and 8.5 h (with 8,000 particles the factor may be
  smaller, down to about 1).

## 6. The fixed-step run shows the deviation too: not caused by v5

The validation's run with a fixed step (`runs/val/gpu-2000-count`,
`-count2`: p9gpu without sub-steps, planets with 1 step, dt 0.5, the start
values of G0 and M0), measured against the ensemble's MERCURIUS runs in units
of the ensemble's run-to-run scatter s (`tools/fixed_vs_ensemble.py`, output
`runs/cause/fixed-vs-ensemble.txt`; d_F = (R_F − m_M) / 2s):

| t (Myr) | R_F | m_M | m_G | d_F | d_G |
|---|---|---|---|---|---|
| 100 | 0.688 | 0.691 | 0.687 | −0.22 | −0.33 |
| 125 | 0.680 | 0.695 | 0.694 | −4.56 | −0.30 |
| 140 | 0.676 | 0.693 | 0.682 | −2.73 | −1.71 |
| 165 | 0.653 | 0.674 | 0.647 | −2.40 | −3.12 |
| 200 | 0.578 | 0.609 | 0.569 | −1.12 | −1.45 |

R(Δϖ) of the fixed-step run lies below both MERCURIUS runs at every time from
105 Myr on (and at most times from 40 Myr), with d_F of the same size as the
ensemble's d_G. R(ΔΩ) stays within the scatter (d_F −1.75 to +0.35). So the
deviation does not come from the sub-steps of v5 (smooth transition, collision
radii). What remains common to all p9gpu runs and absent in MERCURIUS: the
Wisdom–Holman step without an encounter zone around the planets (MERCURIUS
switches to IAS15 within a few Hill radii). The planets of the fixed-step run
use one step per dt (like REBOUND WHFast), those of v5 eight; that it deviates
alike points away from the planets' secular frequencies as well.

## 7. REBOUND WHFast without an encounter zone follows MERCURIUS in R(Δϖ)

`runs/cause/wh05`: member 0 with p9sim WHFast (democratic heliocentric,
dt 0.5 yr, no encounter zone, like p9gpu's fixed step), 0–200 Myr, 16 slices
(2.3 h). Against the ensemble (`tools/fixed_vs_ensemble.py`, output
`runs/cause/wh05-vs-ensemble.txt`; d_W = (R_W − m_M) / 2s, and the same against
the p9gpu mean m_G):

| t (Myr) | R_W | m_M | m_G | d_W against M | (R_W − m_G) / 2s |
|---|---|---|---|---|---|
| 100 | 0.684 | 0.691 | 0.687 | −0.53 | −0.25 |
| 140 | 0.695 | 0.693 | 0.682 | +0.28 | +2.17 |
| 150 | 0.688 | 0.691 | 0.669 | −0.20 | +1.36 |
| 165 | 0.662 | 0.674 | 0.647 | −1.34 | +1.67 |
| 180 | 0.641 | 0.650 | 0.612 | −0.44 | +1.45 |
| 200 | 0.599 | 0.609 | 0.569 | −0.34 | +1.07 |

R(Δϖ) of WHFast stays with MERCURIUS up to 150 Myr and slightly below it
afterwards (within 1.34 limits; the p9gpu runs reach −3.1), and from 140 Myr it
lies 1.1 to 2.2 limits above the p9gpu mean; at 200 Myr 0.599, above all four
p9gpu runs (at most 0.581). Without an encounter zone WHFast loses more
particles (survivors 1,454 against 1,504 at 200 Myr; McNemar fails at 100, 150
and 200 Myr) and has a lower R(ΔΩ) at 50–75 Myr (to −5 limits, where 2s is
only 0.004–0.006). One run only.

So a Wisdom–Holman step of the same size without an encounter zone does not by
itself give p9gpu's lower R(Δϖ): the missing encounter zone is not the
explanation. The deviation comes from something p9gpu does differently from
WHFast, in its fixed step as well as in v5. Next: a direct comparison of p9gpu
(fixed step, planets 1 step) with WHFast on identical start values and step,
step by step from the start.

## 8. Direct comparison p9gpu against WHFast: the same integrator

`tools/direct_wh.c` runs p9gpu's integrator (gpu/whdh.h and the planets of
gpu/p9gpu.c, included unchanged; fixed step, planets one step per dt, no
removal at the planets) and REBOUND 5.2.2 WHFast (democratic heliocentric,
safe_mode 1, as p9sim) on the same start file (`runs/val/ens-gpu/input.sa`,
member 0, dt 0.5 yr) in lockstep and compares the synchronous states
(outputs `runs/cause/direct/`; evaluation `tools/direct_wh_eval.py`).

**Step 0** (the state after reading and converting the start file, before the
first step; REBOUND's `from_inertial` against p9gpu's `to_dh`): bit-identical
for all 2,005 bodies (also for all 8,005 of the four members): masses, G,
G m_Sun as Kepler mass, the centre-of-mass velocity, Q and u. The setup that
WHFast and MERCURIUS share with p9gpu has no difference.

**Operator order.** Both: kepler(dt/2), jump(dt/2), kick(dt), jump(dt/2),
kepler(dt/2) (drift-kick-drift with the Kepler parts outside). WHFast with
safe_mode 1 does both Kepler halves and converts from and to the inertial
frame in every step; p9gpu joins the two halves into one Kepler step of dt and
keeps the state half a drift ahead (synchronised for outputs with
kepler(−dt/2)). Same operators, one at a time from the same state:
- Kepler drift: Kepler mass G m_Sun in both (test particles and planets);
  results differ by at most 2.2e-16 relative (one rounding unit; REBOUND's
  solver iterates to convergence, p9gpu's does three Halley iterations), in
  1,774 of 2,005 bodies in some bit.
- Jump (P/m_Sun from the planets' barycentric momenta, test particles
  massless): bit-identical.
- Kick (planets on each other and on the test particles, not the Sun;
  Planet Nine a massive planet in both): bit-identical for all bodies.

**Step by step** (1,000 steps, every step): after step 1 the test particles
differ by 1.3e-16 (median) and 4.8e-16 (max) relative in position, after
1,000 steps by 2.9e-15 (median) and 9.1e-14 (max); none above 1e-12. Planets
and Planet Nine after 1,000 steps: 1.6e-15 (Planet Nine) to 1.5e-12
(Jupiter) in position; elements equal to 1e-14 (a, e) and 1e-11 deg (ϖ, Ω).

**Over 10 Myr** (2,000 test particles, compared every 10 yr): the first time
the position difference of a test particle exceeds a threshold, against the
chaos baseline of the same code with start positions 1e-12 apart (member 0
against member 1):

| pair | > 1e-8 by 1 Myr | median time to 1e-8 | to 1e-4 | median time 1e-12 → 1e-4 |
|---|---|---|---|---|
| p9gpu against WHFast (member 0) | 96.7 % | 0.100 Myr | 0.236 Myr | 0.227 Myr |
| p9gpu, member 0 against 1 | 96.0 % | 0.074 Myr | 0.215 Myr | 0.212 Myr |
| WHFast, member 0 against 1 | 96.3 % | 0.074 Myr | 0.215 Myr | 0.212 Myr |

p9gpu and WHFast separate exactly as fast as either code from itself after a
1e-12 perturbation; they start from a 1e-16 difference instead of 1e-12, so
they reach each threshold a little later. 99.5 % of the separations (1e-8 and
1e-4) happen away from close approaches (Neptune farther than 5 au and Planet
Nine farther than 21 au in the 1 to 2 kyr before), spread over q like the
population (q < 42 au 60 %, 42–50 au 36 %, > 50 au 4 %): the ordinary
chaotic growth of rounding differences, not a difference at encounters.
Planets and Planet Nine over 10 Myr: no systematic drift; Jupiter's position
differs by 1.8e-6 at 1 Myr and 1.3e-4 at 10 Myr (the phase of the rounding
differences), elements by at most |Δa/a| 3e-6, |Δe| 2e-6, |Δϖ| 0.03 deg
(Neptune), 7e-4 deg (Planet Nine).

**Consequence.** p9gpu's fixed step and WHFast are the same integrator; their
trajectories differ only by rounding, amplified by the chaos at the same rate
as between ensemble members. The fixed-step run F (0.578 at 200 Myr) and the
WHFast run W (0.599) are therefore two realisations of one method; their
difference (0.021) is within the ensemble's 2s (0.028). The conclusion of
section 7 (the deviation is particular to p9gpu) does not hold: single runs
can not separate p9gpu's fixed step from WHFast. What stands: the four v5 runs
(mean 0.569) lie below both MERCURIUS runs (mean 0.609); the two fixed-step
Wisdom–Holman runs lie between (0.578, 0.599; mean 0.589). Whether the plain
Wisdom–Holman step (without an encounter zone) deviates from MERCURIUS, and
whether v5 deviates from the plain step, needs an ensemble of fixed-step runs
(members 1–3; p9gpu fixed step on the GPU or WHFast, which are equivalent).
No cause in p9gpu's integrator was found; nothing to fix.

## 9. Night of 2026-10-21/22: more runs for the group comparison

Started 23:48–23:50 on the laptop (decision of the project lead; nothing on
appmdp-05, p9gpu unchanged):

- **Fixed step, members 1–3** (`runs/cause/ensfix/m123`, one p9gpu job with
  6,000 test particles on the GPU, 10 segments of 20 Myr, `tools/chain_run.sh`):
  binary `build/gpu-v5/p9gpu` (79c16e2) with `--encounter-method step
  --no-removal`, planets one step per dt, the settings of `gpu-2000-count`.
  Checked first: member 0 over 1 Myr with these settings gives the state of
  `gpu-2000-count` at 1 Myr bit for bit (state sha256 `5e4dc9cb…a36a2`).
- **MERCURIUS M2 = member 5, M3 = member 6** (`runs/cause/ensmerc`, settings
  of M1, `runs/val/ens-merc`): 15 single-core jobs with nice (member 5 in 8
  slices of 250, member 6 in 7 slices of 285–286). MERCURIUS cost is linear in
  the number of particles (1 Myr: 37 s for 125, 78 s for 250), about 50 core
  hours per member under full load (M1); two members fit into the night, three
  do not.

With them: plain Wisdom–Holman F, W, F1–F3 (5 runs), MERCURIUS M0–M3
(4 runs), v5 G0–G3 (4 runs).
