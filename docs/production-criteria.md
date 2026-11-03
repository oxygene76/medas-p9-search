# Production run: criteria, fixed before its start (draft 2026-11-02; decisions P1 and P2 of 2026-11-03 in section 6)

Part of entry 3. **Nothing is started.** The run starts only:
- after the acceptance test of the A100 and the speed benchmark there;
- on the project lead's explicit word.

## 1. What runs

- **Package:** `p9prod-9a084ed.tar.gz` (medas-p9-search-bb2021 `build/`), **unchanged**.
  - SHA-256 `caff48128882982a4a11affe7111f33f950d2e2027e633e6002aed0c04d9b12e`.
  - Built and documented in `docs/production-package.md` of medas-p9-search-bb2021.
  - Its p9gpu (SHA-256 `7666c5ba4560a8c2…`) contains machine code for sm_80, sm_89, sm_90 and sm_120 and PTX for
    compute_80 (`tools/make_prod_package.sh`). The A100 (sm_80) runs its own machine code, so the package needs no
    rebuild.
- **Method:** p9gpu v5 (Wisdom–Holman in democratic heliocentric coordinates, dt 0.5 yr, smooth transition for
  close encounters, planets with 8 inner steps, collisions at the planets' radii, FP64).
  - **Why v5:** the equivalence test. Both comparisons were equivalent (`docs/equivalence-result-20261102/`,
    commit ee3d621):
    - (1) V5 − M: +0.0033, 95 % interval [−0.0055, +0.0121];
    - (2) WH − M: +0.0061, 95 % interval [−0.0036, +0.0158];
    - margin ±0.035.
  - The table fixed beforehand (`docs/equivalence-criteria.md`, "What follows from each outcome") then prescribes
    v5 with p9prod-9a084ed unchanged.
  - Additional check: the planets of the 16 MERCURIUS slices per seed are bit-identical
    (`docs/equivalence-planet-hash-20261102.md`).
- **Job** (`runs/prod/job.json`, start values `runs/prod/input.sa` from `tools/make_ic.py`, ic sha256
  `f8c07307…`):
  - Planet Nine as the posterior of Brown & Batygin (2021): 6.2 Earth masses, a 380 au, perihelion 300 au
    (e 0.2105), i 16°.
  - 64,000 test particles, seed 21: a 150–500 au, q 30–50 au, i 0–25°.
  - Removal at r < 4.5 au and r > 10,000 au, and at collisions.
  - 4 Gyr in 40 segments of 100 Myr, 400 snapshots (one per 10 Myr).
- **Where:** the A100 in appmdp-05, as user p9sim, with nice. The L40S is not used for it.

## 2. Before the start (all must hold)

- **G1:** The A100 acceptance test is passed, including `check.sh` of the package on the A100: **ALL SAME**, all
  38 cases bit for bit as on the reference machine. A single difference stops everything.
- **G2:** The speed benchmark on the A100 is done.
- **G3:** Entry 3 (this file, the package, the equivalence result, the comparison criteria with Brown & Batygin)
  is on the chain.
- **G4:** The project lead's explicit word.

## 3. During the run

- Every segment writes its result hash and its log; the chain of segments is checked as in the package
  (`status.sh`).
- An interruption is resumed from the last finished segment (`start.sh` resumes). A resumed segment must give the
  same result hash as an uninterrupted one would. This was tested in the package
  (`tools/test_prod_package.sh`).
- **No change** to the package, the job or these criteria after the start. A problem that needs a change stops the
  run and is reported. A new run needs a new entry.

## 4. Evaluation (fixed now)

- **Measures:** those of `docs/bb2021-comparison-criteria.md` section 4, applied to this run:
  - M1 (direction of the Δϖ cluster), M2 (its strength), M3 (mean pole relative to Planet Nine), M4 (wall),
    M5 (width);
  - selection S_BB (150 < a < 1000 au, q > 42 au);
  - window 1–4 Gyr (301 snapshots);
  - elements barycentric, angles in the frame of Jupiter's orbital plane at each snapshot (prerequisite V3 there).
- **Precision:** 4 subsets of 16,000 test particles (0–15,999, …), whose scatter is the statistical error.
- **Information, not judged:**
  - the time series of M1–M3;
  - the selections S1–S3 of `docs/night-20261024.md`;
  - the survivors over time;
  - the position of the 11 observed objects of Brown & Batygin's Table 1 relative to the distribution (section 8
    there).
- **Not judged against Brown & Batygin values:** the paper has no distribution for this set (decision D1). The
  comparison with their published results is made with sets A and B (`docs/bb2021-comparison-criteria.md`), as
  separate runs.

## 5. What follows

- **Report:** the clustering of this run over 1–4 Gyr, with its scope:
  - the equivalence holds for 0–200 Myr;
  - the residual risk over 4 Gyr as in `docs/equivalence-criteria.md` "Scope and residual risk".
- **Not decided:** if the subsets disagree among themselves, the result counts as not decided (decision P1,
  section 6):
  - the scatter is the largest angular distance between the M1 of a subset and the pooled M1, each over the window
    1–4 Gyr;
  - more than 10°: not decided;
  - a subset that deviates is reported and not excluded; the evaluation runs in full in any case.
- **Reading it together with sets A and B:**
  - If A and B agree with Brown & Batygin (outcome 1 there), this run stands as the long-term behaviour of their
    posterior Planet Nine with our method.
  - Otherwise it is reported as not confirmed at long times, with the outcome of A and B.
- **Check of the long-time residual risk:** the 3 paired long runs (seeds 110–112) of
  `docs/equivalence-criteria.md`. By decision of 2026-11-03 their criteria are part of entry 3
  (`docs/long-runs-110-112-criteria.md`).

## 6. Decisions of the project lead (2026-11-03)

The open points of the draft, as they were put:
- P1: the threshold "> 10°" for the subsets (section 5), and whether one not decided subset should stop the
  evaluation or only be reported.
- P2: the order on the A100: production run first, or sets A and B first (both need the A100; sets A and B need the
  code prerequisites V1–V3 beforehand).

Decided:
- **P1:** 10°, measured as the largest angular distance between the M1 of a subset and the pooled M1, both over
  1–4 Gyr. A subset that deviates is only reported, not excluded. More than 10° means "not decided". Written into
  section 5.
- **P2:** the production run first on the A100 (p9prod-9a084ed, v5, unchanged). It starts directly after entry 3 and
  the maintenance window, under the conditions of section 2.
- **Seeds 110–112:** their criteria go into entry 3. The V5 part runs on the L40S (with the AI services there
  running on), the MERCURIUS part on appmdp-05's CPU, pinned and with nice.
- **Sets A and B** follow as soon as the prerequisites V1–V3 are done and checked: if possible in parallel on the
  L40S (addendum to D3 in `docs/bb2021-comparison-criteria.md`), otherwise after the production run on the A100.
