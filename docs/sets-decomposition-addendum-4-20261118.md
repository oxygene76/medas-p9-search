# Decomposition of sets A and B, addendum 4: weighted reading of Fig. 4, and bounds for BB-A-rin1 (2026-11-18)

**Status:**
- Fixed and timestamped before the computation. Written after outcome 4, the decompositions of addenda 1–3 and the
  measurement of Fig. 4.
- Exploratory, on the existing snapshots; no new run. **It changes nothing:** not the criteria of the sets, not their
  verdicts, not outcome 4.
- Computed with the project lead's go.

**Item (a) of the request is not computed.** It asked for V5 against MERCURIUS in the long runs 110–112, in case their
removal cadence differs. It does not:
- p9sim (MERCURIUS) applies r < 4.5 au and r > 10,000 au in its heartbeat every 1000 steps (`src/p9sim.c`, `CHECK_EVERY`;
  `job.json` of the long runs and of the paired tests: `every_steps` 1000, dt 0.5 yr);
- REBOUND's collisions are off.
- So V5 and MERCURIUS had the same rule and cadence, and their comparisons say nothing about the cadence.

## (b) The reading "weighted Fig. 4"

The question: do sets A and B reproduce Fig. 4 and Figs. 1/3 if their particles are weighted the way the paper's
likelihood selects simulated objects?

**The weighting** (paper, pp. 9–10):
- **Per observed object j** (a_j, q_j) of `docs/bb2021-observed-table1.tsv`: the 10 objects used by the criteria
  (section 8), and as a variant all 11 including 2013 FT28.
- **Selection:** particle-snapshots with |a − a_j| ≤ s_a,j and |q − q_j| ≤ 10 au and q ≥ 42 au, where
  s_a,j = 0.05 a_j for a_j < 230 au, rising linearly to 0.30 a_j at a_j = 730 au.
- **Weight:** two Gaussian kernels with σ equal to half of the smoothing distances (σ_a = s_a,j / 2, σ_q = 5 au).
- **Normalisation:** each object's weights to a sum of 1, then summed over the objects.

**Window and elements:** 1–4 Gyr, 301 snapshots, elements as `frame_elements` of `tools/prod_eval.py`.

**Quantities:**
1. **Inclination shares of the weighted particle-snapshots:** < 30°, 30–40°, 40–50°, 50–70°, normalised to 0–70°
   (prograde), and the retrograde share (i > 90°) of all. For sets A and B.
   - For comparison: Fig. 4, panel i9 = 15° (m9 7, a9 500, e9 0.33), 0.92–0.94 below 30°.
   - Strictly comparable only for set A (i9 17°); for set B it is information.
2. **R per 10 au beyond the wall** (A 260–700 au, B 200–700 au) with the q weighting alone:
   - weight w(q) = Σ_j exp(−(q − q_j)² / (2 · 5²)) for |q − q_j| ≤ 10 au and q ≥ 42 au;
   - weighted circular mean per bin, unweighted mean over the bins.
   - For comparison: Fig. 3, third panel (0.60–0.61) and Fig. 1 (0.51–0.52).

**Scale, fixed before:** for the weighted share below 30° of set A (10 objects):
- ≥ 0.88: **"the reading fits"**;
- < 0.80: **"the reading does not fit"**;
- in between: **"unclear"**.

## (c) Bounds for BB-A-rin1 from the history of q

**Why a bound exists:** BB-A-rin1 can only lose particles against BB-A, and only those that come within 4.5 au. Its
population at every snapshot is a subset of BB-A's (criteria draft, section 2).

**The bound:**
- Removing in addition all particle-snapshots whose particle had q < X at any snapshot since t = 0 bounds what such a loss
  can do, under one assumption.
- **The assumption:** a particle that dips below 4.5 au between two snapshots (10 Myr apart) has q < X at one of them.
- For set A, for X = 4.5, 10, 20 and 30 au:
  - M2 (mean over the snapshots of R in S_BB);
  - the pooled M1;
  - R per 10 au beyond the wall (260–700 au);
  - the inclination shares as in (b) 1, unweighted, for q > 42 au and for 42 ≤ q ≤ 100 au;
  - the number of particle-snapshots.

**What X = 30 au bounds, and what not:**
- It bounds every particle that went below 4.5 au with q < 30 au at a neighbouring snapshot.
- It does not bound a particle that came from q > 30 au to below 4.5 au and back above 30 au within 10 Myr.

**The prediction for BB-A-rin1 is written into the criteria from these numbers.**

## Code

`tools/sets_addendum4.py`, committed before it runs. It imports `frame_elements` and the snapshot readers of
`tools/prod_eval.py` unchanged.
