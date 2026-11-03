# Paired long runs, seeds 110–112: criteria, fixed before the runs (2026-11-03; decisions Q1–Q3 in section 7)

Part of entry 3 (decision of 2026-11-03, `docs/production-criteria.md` section 6). They check the residual risk that
`docs/equivalence-criteria.md` names under "Scope and residual risk": the equivalence of v5 and MERCURIUS was shown
for 0–200 Myr, and a small bias per unit time could grow over 4 Gyr. **Nothing is started** before entry 3 is on the
chain and the project lead gives the word.

## 1. Runs

- **Start values:** seeds 110, 111, 112 (not used before), 2,000 test particles each, member 0, made as the
  equivalence runs: `tools/make_ic.py` with the configuration of the production run (Brown & Batygin 2021 posterior
  Planet Nine: 6.2 Earth masses, a 380 au, q 300 au, i 16°; test particles a 150–500 au, q 30–50 au, i 0–25°;
  inner removal at 4.5 au, outer at 10,000 au).
- **Pairs:** each seed in both groups, as in the equivalence test:

| group | method | program | where |
|---|---|---|---|
| V5 | p9gpu v5 (smooth transition, planets with 8 inner steps, collisions at the planets' radii, FP64) | `bin/p9gpu` of p9prod-9a084ed, unchanged | the L40S of appmdp-05 (the AI services keep running there) |
| M | MERCURIUS, r_crit 3 Hill radii, no encounter removal | `bin/p9sim` of p9prod-9a084ed (the binary of the equivalence group M) | appmdp-05, CPU 1 (socket 0), pinned, nice 10; each seed in slices of 250 test particles |

- 0 to 4 Gyr, dt 0.5 yr, a snapshot every 10 Myr (401 snapshots), as chains of segments of 100 Myr (V5) and
  20 Myr (M slices), each segment resumable with the same bits.
- Before the runs, each package passes its check on its machine (known hashes, as `check.sh` of the production and
  equivalence packages).
- No look at R before all six runs reach 4 Gyr, apart from the interim check below, which looks only at hashes,
  logs, temperatures and the resume test. A run that fails for technical reasons is repeated from its last finished
  segment; no run is left out because of its result.

## 2. Statistic

As in `docs/equivalence-criteria.md`: R(Δϖ) of the distant survivors (a > 230 au, q > 42 au; Δϖ = ϖ − ϖ9,
barycentric), per snapshot.

- **Per run and time:** S(t) = the mean of R over the 11 snapshots from t − 100 Myr to t, for t = 0.5, 1, 2 and
  4 Gyr; and S(1–4) = the mean over all snapshots from 1 to 4 Gyr (the statistic named in the equivalence criteria).
- **Per seed:** d_s(t) = S(V5, s, t) − S(M, s, t).
- **Over the three seeds:** the mean d̄(t) and its standard error from the three differences.

## 3. Decision

- **A bias growing with time is found** if both hold:
  - |d̄(4 Gyr)| ≥ 0.05, and |d̄(4 Gyr)| > 2 standard errors; and
  - d̄ has the same sign at 1, 2 and 4 Gyr, and |d̄(4 Gyr)| > |d̄(0.5 Gyr)|.
- **Otherwise: no growing bias found** within what three pairs can see (about 0.05, `docs/equivalence-criteria.md`).
- **Power:** three pairs can find only large biases. "No growing bias found" is not evidence that there is none; the
  report states this explicitly, with d̄(t) and its standard errors.
- **Too few survivors:** if a run has fewer than 100 distant survivors in more than half of the snapshots of a window,
  S(t) of that window is not computed and the decision uses the remaining times; with fewer than three times left,
  the result is "not decided".

## 4. What follows

- **No growing bias found:** the production run's 1–4-Gyr result stands with the scope of
  `docs/production-criteria.md` section 5, now with this check of the long-time residual risk.
- **Growing bias found:** the production run's late-time clustering is reported with d̄(t) as a known systematic
  difference between v5 and MERCURIUS; no statement about 1–4 Gyr is made beyond it. The cause is looked for
  separately, with new criteria.
- **Not decided:** reported as such; the production result keeps the residual risk as stated before.

## 5. Interim check after about 100 Myr (no look at R)

When the V5 runs have finished their first segment and the M slices their fifth:
- the result hashes of every finished segment are recorded and the chain of segments is consistent (`status.sh`);
- logs without errors; GPU temperature and clocks (V5), CPU load (M) as expected;
- the resume test: one V5 run and one M slice are stopped in a running segment and started again; the resumed
  segment must give the same result hash as before the stop would have (the package's resume rule).
- Then the runs continue unchanged.

## 6. Run time (estimate, 2026-11-03)

- **V5 on the L40S:** the equivalence runs on the L40S (4,000 test particles, one at a time) took 5.3–7.9 h per
  200 Myr, about 50 µs per step; at 2,000 test particles a step costs about the same (the GPU is far from filled).
  4 Gyr = 20 × 200 Myr: **about 4–5 days per seed, about 12–15 days for all three.** Three at once on one GPU are
  not faster in total without NVIDIA MPS (the GPU alternates between the processes): on the laptop GPU (2,000 test
  particles, 1 Myr) 247 s one after the other against 253 s at once, with the same result hashes. They run at once
  (decision Q3). The AI services on the L40S can add some 10–30 %.
- **M on CPU 1:** the equivalence slices on appmdp-05 (250 test particles, 14 at once) needed 1,665–2,476 s per
  20 Myr, about 245 ns per test-particle step at the start; 80 % of the bodies survived 200 Myr. With about 50 % of
  the test particles still present on average over 4 Gyr (40–65 %): **about 440–710 core hours per seed,
  1,300–2,100 for all three.** Split into 24 slices of 250 on the cores of socket 0: with 14 cores about
  5–7 days, with 16 cores about 4–6 days. The real rate comes from the first segments (`status.sh`).
- The speed comparison of 2026-11-03/04 (`speed/` in medas-p9-search-bb2021) gives the measured rates of both
  machines; this section is updated from it before entry 3 (marked as an update).

## 7. Decisions of the project lead (2026-11-03)

The open points of the draft, as they were put:
- Q1: the thresholds of section 3 (0.05 and 2 standard errors; sign at 1, 2 and 4 Gyr).
- Q2: the 30 distant survivors per snapshot as the lower limit for S(t).
- Q3: the three V5 runs one after the other or at once on the L40S (after the measurement on the first segment).

Decided:
- **Q1:** the thresholds as proposed: |d̄(4 Gyr)| ≥ 0.05 and more than 2 standard errors; the same sign at 1, 2 and
  4 Gyr; at 4 Gyr larger than at 0.5 Gyr. The low power of three pairs is stated explicitly in the report
  (section 3).
- **Q2:** 100 instead of 30 distant survivors per snapshot. Expected: about 900 at 200 Myr (57–58 % of the survivors
  were distant in the equivalence runs) and about 400 at 4 Gyr; the noise of R of an isotropic sample, about
  0.89/√n, is 0.16 for 30 and 0.09 for 100.
- **Q3:** the three V5 runs at once on the L40S. The first segment is measured; if running at once is slower in
  total than one after the other, the runs continue one after the other.

## 8. Model assumptions

The model of the production package, in both groups (V5 and MERCURIUS), with the assumptions and limits of
`docs/production-criteria.md` section 7: gravity of the Sun and the planets only, the planets integrated together,
massless test particles, no galactic tide and no passing stars. The pairs compare two integrators in the same model.
The model itself is not tested by them.
