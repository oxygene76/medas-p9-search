# Research note, version 1 (2026-11-22): the long-term clustering of distant trans-Neptunian bodies under the Planet Nine of Brown & Batygin (2021), with a pre-registered, notarised protocol

**Status:** version 1, not peer-reviewed. Planet Nine is a hypothesis; this note reports what our computations show
about published simulations of it, nothing about whether the planet exists.
- **Where the results come from:** from result reports entered on the chain:
  - production run and long runs 110–112: entry r1 (#7);
  - paired tests for sets A and B: entry rp (#11);
  - sets A and B and the outcome: entry r2 (#12);
  - the equivalence result: entry e3 (#4, revealed with the data package); the V2 result: entry e5 (#6).
  - Not entered, but timestamped with OpenTimestamps: the reproduction check (section 11), and addendum 5 of the
    decomposition with its result (section 10.3), which came after entry #12.
  - Computed for this note from the entered result files: t and p at 1 and 2 Gyr (section 9) and the spans of M1 and
    ψ over all snapshots (section 8).
- **Exploratory and marked as such:** what was looked at after the outcome (section 10.3), each step fixed and
  timestamped before it was computed, with the exceptions named there.
- **Announced, without results here:** the check run BB-A-rin1 (#9), the run BB-A2 with a second seed (#10) and the
  mercury6 counter-run. They follow in a later version.
- **Earlier versions:** the draft `docs/research-note-draft.md` up to ba5a62f, in the history.
- **Revised on 2026-11-22** after a reading of version 1 and the readings of the result reports by an AI session
  (p9-review-82, 2026-11-22). The result pages of the website say the same, with the same numbers.

**Author:** Eike Janßen, MEDAS Computers GmbH.

---

## Abstract

We recomputed the long-term clustering of distant trans-Neptunian test bodies under the Planet Nine hypothesis of
Brown & Batygin (2021) with our own GPU integrator, and compared two of their published simulation sets with our
method. The criteria, tools and run packages were fixed before the runs they concern and entered as notarised
commitments on the blockchain medasdigital-2, with OpenTimestamps as a second anchor (exceptions: the equivalence test
was entered before its evaluation; the evaluation tool of the long runs was written after the runs and timestamped
before their evaluation).
- **The integrator** is equivalent to MERCURIUS (REBOUND) over 200 Myr: within ±0.035 in the strength of the
  clustering, in the general test and in paired tests for both sets. Over 4 Gyr, checked only for the Planet Nine of
  the production run, no growing difference was found; the long runs can test this clearly to 1 Gyr, with limits to
  2 Gyr, and not at 4 Gyr. For sets A and B the check covers 0–200 Myr.
- **The comparison with Brown & Batygin (2021)** gives outcome 4 of five, "no cluster", by the criteria entered
  beforehand: the strength of the clustering is 0.050 (set A) and 0.127 (set B), below the limit of 0.20.
  - Set B clusters in the expected direction (166.7°), set A does not (127.3°).
  - The outcome does not depend on the definition of the longitude of perihelion.
- **Afterwards, exploratory:** the orbits a survey could observe cluster far more strongly, 0.03–0.08 below the
  values read from the published figures on a scale from 0 to 1; with only the bodies that survive 4 Gyr, as
  Batygin et al. (2019) show them, 0.64 and 0.56, above them. Our set A holds more highly inclined orbits than one figure of the paper
  shows. Why, we cannot explain.
- **Announced:** a check run, a second random start of set A and a counter-run with mercury6.

## 1. Question

1. **Main question:** does the Planet Nine of the posterior of Brown & Batygin (2021) keep a cluster in the
   longitudes of perihelion (Δϖ = ϖ − ϖ9) of the distant test bodies (selection S_BB: 150 < a < 1,000 au, q > 42 au)
   over 1–4 Gyr? If so, in which direction, how strong and how stable is it?
   - Measures M1–M5 of `docs/bb2021-comparison-criteria.md` section 4, over the window 1–4 Gyr.
   - Production run, `docs/production-criteria.md`.
2. **Method question:** do the results of our GPU integrator (p9gpu v5) agree with MERCURIUS (REBOUND)?
   - Over 200 Myr: equivalence test, `docs/equivalence-criteria.md`.
   - Over 4 Gyr: paired long runs of seeds 110–112, `docs/long-runs-110-112-criteria.md`.
   - For the Planet Nines of sets A and B: paired tests, `docs/bb2021-paired-test-proposal.md`.
3. **Comparison question:** do two parameter sets of Brown & Batygin (sets A and B) reproduce their published
   clustering with our method? (`docs/bb2021-comparison-criteria.md`)

## 2. Method

### 2.1 Model

- **Bodies:**
  - the Sun, carrying the masses of Mercury to Mars;
  - Jupiter, Saturn, Uranus and Neptune from JPL DE440s at JD 2458270.0;
  - Planet Nine with the posterior values of Brown & Batygin (2021): 6.2 Earth masses, a 380 au, q 300 au, i 16°;
  - in sets A and B, one of two parameter sets of the same paper each (`docs/bb2021-comparison-criteria.md`): set A
    7 Earth masses, a 500 au, e 0.33 (q 335 au), i 17°; set B 5 Earth masses, a 300 au, e 0.15 (q 255 au), i 17°, as
    the paper's table (the caption of its figure names 16°);
  - massless test bodies: a 150–500 au, q 30–50 au, i 0–25°, made by `tools/make_ic.py`, in the production run and in
    both sets. The paper does not state how its starting orbits are distributed.
  - All known differences of the setup from the paper: `docs/bb2021-article-vs-package.md`.
- **Integrator:** Wisdom–Holman in democratic heliocentric coordinates, dt 0.5 yr.
  - Close encounters with a smooth transition to sub-steps.
  - The planets with 8 inner steps, in FP64.
  - Removal beyond 10,000 au and within 4.5 au of the Sun, both checked only every 1,000 steps (500 yr), and on
    collision with a planet's physical radius. MERCURIUS (p9sim) removes with the same rule and cadence, so the
    comparisons with it say nothing about the cadence. The 4.5 au come from the job parameters of the packages
    (`r_in_au`); the program's default is 5 au (`docs/code-review-20261121.md`, C1).
  - The details: `docs/gpu-integrator.md`, `docs/close-encounters.md`.
- **Reference:** MERCURIUS (REBOUND 5.2.2), r_crit 3 Hill radii, the same start values.
- **Production run:** 64,000 test bodies, 0–4 Gyr, a snapshot every 10 Myr, as 40 segments of 100 Myr.
- **Bit reproducibility:**
  - every segment has a result hash over the canonical states of all its snapshots (`docs/reproducibility.md`);
  - bit-identical on every platform: WHFast, and p9gpu with its CPU twin;
  - MERCURIUS (p9sim) so far only with glibc on x86-64, where all runs were made, because REBOUND's MERCURIUS calls the
    libm function `cbrt` and libms round it differently. A new p9sim binary fixes this for future packages
    (correction of 2026-11-11 in `docs/reproducibility.md`);
  - every package checks its machine against known hashes before it computes (`check.sh`, "ALL SAME");
  - a resumed segment gives the same bits.

### 2.2 Statistics

- **Clustering:** M1 (direction), M2 (strength), M3 (mean pole), M4 (wall) and M5 (width) of the Δϖ distribution.
  - Elements barycentric, angles in Jupiter's orbital plane at each snapshot.
  - The tool: `tools/prod_eval.py`, tag `prod-eval-v1`.
- **Precision:** four disjoint subsets of 16,000 bodies. "Not decided" if the M1 of one subset lies more than 10°
  from the pooled M1 (decision P1).
- **Method comparisons:** R(Δϖ) of the distant survivors (a > 230 au, q > 42 au).
  - Equivalence: paired differences over 9 seeds, margin ±0.035, 95 % interval (`tools/equiv_eval.py`).
  - Long runs: d(t) over three seeds at 0.5, 1, 2 and 4 Gyr (`tools/long_eval.py`).

### 2.3 Hardware and software

- **Production run and V5 runs:** on an NVIDIA A100 (PCIe, 40 GB) of the GPU server.
- **MERCURIUS:** on the server's CPU, pinned and at low priority.
- **Speed:** the production run took 53.0 h on one GPU. In the paired tests the same task took 1.7 h with our
  integrator on one GPU, 109 h with MERCURIUS on one processor core and 7 h on 16 cores: about 60 and 4 times faster.
  The earlier speed comparison of 2026-11-03/04 is in `speed/`.
- **Program versions:** p9gpu and p9sim of commit 9a084ed (sha256 `7666c5ba…`, `b14f7956…`), REBOUND 5.2.2, CUDA
  build as in `docs/production-package.md` (commit 801fb20).
- **Packages:** production run p9prod-9a084ed (entry e3); sets A and B p9bbsets-5b05cc3 (entry e4). Which run was
  computed from which commit and package is in the table of the README.

### 2.4 Methods and tools, including AI tools

- An AI assistant (Claude, by Anthropic) did much of the work under the direction of the author. It wrote and
  revised the integrator, the evaluation programs, the tests and the computing packages, drafted the criteria, the
  reports, this note and the result pages of the website, ran evaluations by the procedures fixed beforehand, and
  checked texts and numbers.
- Further AI sessions read the code and the texts of the website independently and, on 2026-11-22, after their
  entries, the result reports of entries r1, rp and r2 (#7, #11, #12), compared with the result files. The reports of entry r1 (#7) were reviewed twice before their entry; who wrote these
  reviews is not documented. The author read the result pages of the website.
- The author made the decisions: the questions, the criteria and their limits, the order of the runs, the acceptance
  of every result and every text, and every entry on the chain, which only the author can sign.
- The results rest on deterministic programs, their tests and the checks described here, not on the judgement of an
  AI.

## 3. Model assumptions and limits

From `docs/production-criteria.md` section 7 and `docs/bb2021-comparison-criteria.md` addendum 14, stated before the
runs:
- **Gravity of the Sun and the planets only.** No galactic tide, no passing stars, no birth cluster.
  - The galactic tide matters for a > 1,000–2,000 au; S_BB ends at 1,000 au.
  - Bodies that pass through larger a and come back can still carry its effect, which is not modelled.
  - **Brown & Batygin 2021 likewise:** their section 4.1 (p. 8) integrates "the 5 giant planets and test particles"
    with mercury6 and removes bodies at r > 10,000 au. Their paper mentions no galactic tide, and passing stars only
    in the introduction (p. 2) as an earlier explanation of Sedna. The check is in the production report.
  - **Limit of that check:** the paper names what is integrated and does not state the absence of a tide
    explicitly. The arXiv version (v2) was checked, not the journal version.
  - **Differences of the setup** include their integrator (mercury6, hybrid, 300 days; Chambers 1999) against ours,
    our Sun carrying the inner planets, the cadence of the inner removal, the reference plane of the test bodies and
    their number. The full list is `docs/bb2021-article-vs-package.md`.
  - **A direct comparison with mercury6, their program, has not been computed yet.** For outcome 4, which was reached
    (section 10.2), the criteria (`docs/bb2021-comparison-criteria.md` section 6) call for a counter-run of set A with
    mercury6. It follows as an announced addendum, with its own entry before the run. A feasibility study exists
    (about 790 core hours for a paired test as in the equivalence test).
- **Massless test bodies:** no self-gravity of the disk, no collisions among them.
- **No observational bias.** M1–M5 describe the simulated distribution, not what surveys would see. The 10 observed
  objects of their Table 1 are shown for information only and are not judged (`docs/bb2021-observed-table1.tsv`,
  ϖ9 = 254°; the Planet Nine of the production run starts at ϖ = 248.5°).
- **Method:** the equivalence with MERCURIUS was shown for 0–200 Myr, for the Planet Nine of the production run and,
  in the paired tests, for those of sets A and B. Over 4 Gyr it rests on three paired long runs with the Planet Nine
  of the production run only, which can find only large biases (about 0.05 in R). For sets A and B, whose encounter
  regime differs (section 6), there is no check beyond 200 Myr.
- **One posterior point:** the production run uses one Planet Nine, and sets A and B two more. It is not a sample of
  the posterior.

## 4. Pre-registration: notary entries and timestamps

The criteria, tools and packages were fixed before the runs they concern (exceptions: the equivalence test was
entered before its evaluation, and the evaluation tool of the long runs was written after the runs; see the
deviations below) and entered on the chain medasdigital-2 in the notary contract `medas1ghd753shjuwexxywmgs4xz7x2q732vcnkm6h2pyv9s6ah3hylvrqejyaze`. Each entry is a commitment to
a manifest that lists every file by sha256 and git commit.

| entry | chain entry | time (UTC) | block | content |
|---|---|---|---|---|
| a3 | #2 | 2026-11-02 12:08:31 | 10694917 | validation status up to 2026-10-21, with the addendum on single runs and means |
| e2 | #3 (refers to #2) | 2026-11-02 12:14:09 | 10694977 | the equivalence test, fixed before its evaluation |
| e3 | #4 (refers to #3) | 2026-11-04 09:31:02 | 10723643 | equivalence result; criteria of the production run, of the long runs 110–112 and of the order on the A100; the comparison criteria with Brown & Batygin at 224b7a1; the packages |
| e4 | #5 (refers to #4) | 2026-11-04 17:06:01 | 10728476 | the comparison criteria with Brown & Batygin at 1c5f2ba, with addendum 16 (V2 short runs), and the packages of sets A and B |
| e5 | #6 (refers to #5) | 2026-11-10 07:18:02 | 10814015 | the V2 result and the criteria of the paired tests V5 against MERCURIUS for sets A and B |
| r1 | #7 (refers to #4, result) | 2026-11-11 07:30:03 | 10829443 | results of the production run and of the long runs 110–112: the two reports (version 3, versions 1 and 2 as stamped copies), the result files, the checksum lists, procedures and tools |
| e6 | #9 (refers to #5, job) | 2026-11-18 16:12:49 | 10942017 | criteria of the check run BB-A-rin1 (set A with the inner removal checked in every step), before the run |
| e9 | #10 (refers to #5, job) | 2026-11-21 12:46:24 | 10986124 | criteria of the run BB-A2 (set A with a second seed for the test bodies), before the run |
| rp | #11 (refers to #6, result) | 2026-11-21 13:22:09 | 10986511 | results of the paired tests for sets A and B |
| r2 | #12 (refers to #5, note) | 2026-11-21 13:26:07 | 10986554 | result of sets A and B: outcome report, set reports, procedures, addenda 1–4 of the decomposition (addendum 5 and its result came after this entry; they are timestamped, not entered). A result, entered as a note because the contract accepts the type result only with a reference to a job, and #5 is a note |
| e7 | planned | – | – | the data package |

The transactions, commitments and the SHA-256 of each manifest are in `docs/notary.md`.

**Reveals:**
- #3, #5, #6, #7, #11 and #12 were revealed on 2026-11-22 (blocks 11001405–11001457).
- Their manifests and the files outside git are attached to the release `notary-reveal-1` of the repository.
- #2 and #4 are revealed with the data package, #9 and #10 with their results.
- Documents under version control can be read in the repository already, even for entries not yet revealed; only the
  reveal proves that they are the ones entered.

**OpenTimestamps (Bitcoin), a second, independent anchor:**

| file | Bitcoin block |
|---|---|
| manifests a3 and e2 | 973126 (2026-10-25 21:00:34 UTC), 973129, 973151 |
| checksum list of the equivalence runs | 974272 (2026-11-02 15:49:32 UTC) |
| comparison criteria with Brown & Batygin at 224b7a1 | 974281 (2026-11-02 17:58:45 UTC) |
| IRAS/AKARI criteria at 0b0c773 and f0cc090 | 974431, 974437 |
| comparison criteria with Brown & Batygin at 1c5f2ba | 974519 |
| V2 result at 4d42c89 | 974792 |
| checksum list of the production run | 975191 |
| checksum lists of the long runs and their evaluation tool (`tools/long_eval.py` at 6a69854) | 975278 |
| evaluation procedure of the long runs at af2e058 | 975284 |
| result reports of the production run and of the long runs, version 1 (cce5b92, ea38f05) | 975282 |
| the same, version 2 (85d4061, 2e21864) | 975284 |
| the same, version 3 (ea21771) | 975288 |

The first Bitcoin block of each stamp, from `ots info` after `ots upgrade` on 2026-11-22. The first three rows were
checked against the block headers without a Bitcoin node; the others not yet.

**Deviations from the registered protocol** (all reported, none changes a criterion):
- The evaluation tool of the long runs (`tools/long_eval.py`) was written after the runs and before any look at R. It
  was committed and timestamped before the evaluation, and two cases the criteria left open were decided beforehand
  (`docs/long-runs-evaluation-procedure.md`).
- The resume test of a V5 long run (interim check, criteria section 5) did not take place, because the runs went
  through without interruption.
- The V5 part of seeds 110–112 ran on the A100 instead of the L40S (addendum of 2026-11-04, before any run).
- The production evaluation was run twice with the same tool and data, the second time with a relative path, so that
  the committed outputs hold no local path. The outputs differ only in that path (`environment.txt` of the result).

## 5. Equivalence test (0–200 Myr)

- **Fixed in:** e2 (criteria), result in e3. 9 seeds × 4,000 test bodies, groups WH, V5 and M.
- **Result** (already evaluated, `docs/equivalence-result-20261102/`):
  - V5 − M: +0.0033, 95 % interval [−0.0055, +0.0121];
  - WH − M: +0.0061, 95 % interval [−0.0036, +0.0158];
  - both **equivalent** within ±0.035.
- **Consequence fixed beforehand:** the production run with v5 and the package p9prod-9a084ed unchanged.
- The planets of the 16 MERCURIUS slices per seed are bit-identical (`docs/equivalence-planet-hash-20261102.md`).

## 6. V2 finding: the encounter regime of sets A and B

- **Fixed in:** e4 (addendum 16).
- **Runs:** one short run per set, 16,000 test bodies, 0–60 Myr, compared with the encounter shares of the equivalence
  runs.
- **Result** (`docs/bb2021-v2-result-20261106.md`): **both sets are outside the limits.**
  - Set A: Uranus fast flybys × 2.02, close flybys × 1.66.
  - Set B: Uranus fast flybys × 0.62.
  - Seed-to-seed spread about ±8 %.
- **Consequence fixed beforehand:** no 4-Gyr run of a set before a paired test V5 against MERCURIUS for that set.

## 7. Paired tests for sets A and B

- **Fixed in:** e5.
- **Design:** per set 9 pairs, seeds 331–339 (A) and 341–349 (B), 4,000 test bodies, 0–200 Myr. Statistic, margin
  and test as in the equivalence test, one decision per set.
- The encounter shares of V5 are reported and do not decide.
- **Release:** a set's 4-Gyr run starts only with the release file `BB-<set>.ok` that `tools/pair_eval.py` writes
  for "equivalent".
- **Results** (entry rp, #11; `docs/paired-result-A-20261112.md`, `docs/paired-result-B-20261113.md`):
  - **Set A: equivalent.** Mean of the 9 paired differences S(V5) − S(M) +0.0067, 95 % interval [−0.0017, +0.0151]
    (t, 8 degrees of freedom).
  - **Set B: equivalent.** Mean +0.0002, 95 % interval [−0.0075, +0.0079].
- **Consequence fixed beforehand:** both sets released for their 4-Gyr runs.
- **Reported, not deciding:** for set A, only the interval of S with the observed cut excludes zero, and barely
  ([+0.0001, +0.0153]). Set B shows nothing of the kind.

## 8. Production run: clustering over 1–4 Gyr

- Run p9prod-9a084ed, complete: 40 of 40 segments, 17,798 of 64,000 test bodies left at 4 Gyr. Result hash of the
  last segment: `d41152221b3dfc9ff490a21eb0120896b9bfce95a6a2bb0378c8005b0527f1c3`.
- The checksum list of all 517 result files was timestamped before the evaluation.
- The archive was backed up encrypted and restore-checked before the evaluation. `tools/prod_eval.py` is
  byte-identical with `prod-eval-v1` of entry 3, run from a clean checkout of the procedure commit 0ca9595.

**Verdict: decided.** The largest distance of the M1 of the four subsets of 16,000 bodies from the pooled M1 is 1.41°
(limit 10°). No subset deviates.

| measure, 1–4 Gyr (301 snapshots, S_BB) | pooled | subsets |
|---|---|---|
| M1, direction of the Δϖ cluster | 154.1° | 152.8°–155.5° |
| M2, strength (mean R per snapshot) | 0.076 | R pooled 0.076–0.080 |
| M3, mean pole relative to Planet Nine's, ψ | 1.5° | – |
| M4, wall | 155 au | – |
| M5, width at 850–950 au | 135° (106.5°–240.5°) | – |

- **Variants**, reported, not judged: ecliptic frame M1 154.2°, ψ 3.9°; heliocentric elements M1 154.1°, ψ 1.6°.
- **Not judged against values of Brown & Batygin:** the paper has no distribution for this set (decision D1).

**Information** (reported, not judged):
- **Strength:** R in S_BB falls from 0.57 at 0.1 Gyr to 0.10 at 1 Gyr and 0.05 at 4 Gyr.
- **Direction:** after an early phase (270° at 0.1 Gyr, 135° at 0.5 Gyr), M1 stays between 138° and 174° from 1 to
  4 Gyr.
- **Pole:** ψ stays within 8° of Planet Nine's pole from 0.5 Gyr on.
- These two spans are taken over all 301 snapshots (`timeseries.csv` of the result). Version 1 and the result report
  gave 141°–173° and 7° from a sample of snapshots (corrected 2026-11-22).
- **Planet Nine:** its ϖ precesses from 248.5° to 354.6° over 4 Gyr. Δϖ is always taken against its value at the same
  snapshot.
- **Survivors:** 63,911 test bodies at 10 Myr, 25,864 at 2.01 Gyr, 17,798 at 4 Gyr.
- **Observed objects:** for the 10 objects of Table 1, the share of simulated bodies near their a that lie within
  ±15° of their Δϖ is 0.072–0.119, against 0.083 for an even distribution. The table is in the production report.

## 9. Long-time check: paired long runs, seeds 110–112

- V5 on the A100 and MERCURIUS on the CPU, 0–4 Gyr, 3 × 2,000 test bodies. All 120 V5 and 4,800 MERCURIUS segments
  were checked as consistent, and the start values are paired.
- The archives were backed up and restore-checked, and the checksum lists timestamped, before the evaluation.
- The evaluation tool `tools/long_eval.py` was written after the runs and before any look at R; it was committed and
  timestamped first (section 4, deviations).

**Verdict: no growing bias found** (criteria section 3).
- "Growing bias found" needs all four conditions. The two size conditions fail: |d(4 Gyr)| = 0.045 < 0.05, and
  ≤ 2 standard errors (0.063).
- The two others hold: the same sign at 1, 2 and 4 Gyr, and |d(4)| > |d(0.5)|.
- At least 382 distant survivors in every snapshot (limit 100), so all four times are used.

| t | d̄ = S(V5) − S(M), mean over 3 seeds | standard error | t (2 degrees of freedom) | p (two-sided) |
|---|---|---|---|---|
| 0.5 Gyr | +0.0073 | 0.0025 | 2.97 | ≈ 0.10 |
| 1 Gyr | −0.0084 | 0.0177 | −0.48 | ≈ 0.68 |
| 2 Gyr | −0.0006 | 0.0230 | −0.03 | ≈ 0.98 |
| 4 Gyr | −0.0450 | 0.0313 | −1.44 | ≈ 0.29 |
| 1–4 Gyr (reported, not deciding) | −0.0132 | 0.0049 | −2.68 | ≈ 0.12 |

S(t) per run and the single differences are in the long-run report.

**Power and noise floor** (assessment, not part of the criteria):
- **Low power:** three pairs can find only large biases, about 0.05 in R. "No growing bias found" is not evidence that
  there is none.
- **No difference is significant**, with t at 2 degrees of freedom.
- **Noise floor:** an isotropic sample of n bodies gives an expected R of about 0.89/√n.
  - **1 Gyr: clearly informative.** About 705 distant survivors per run, floor 0.034, S 0.08–0.15.
  - **2 Gyr: informative only with limits.** About 576, floor 0.037, S 0.045–0.15. One of six runs (seed 110 V5,
    S(2) = 0.045) lies near the floor.
  - **4 Gyr: not testable.** About 417 per run, floor 0.044, as large as R of the production run at 4 Gyr (0.052).
- **Taken together:** the data are compatible with no difference, and with a difference of a few hundredths in R at
  late times.

## 10. Sets A and B: comparison with Brown & Batygin (2021)

### 10.1 The runs

- Both sets were released by their paired tests (section 7) and computed over 4 Gyr on the A100. Their check against
  MERCURIUS covers 0–200 Myr; beyond that there is none for these Planet Nines (section 3).
  - Set A: 12–14 Nov, 54.8 h.
  - Set B: 14–16 Nov, 52.9 h, with a pause of 29 min on 15 Nov at a segment boundary, without loss.
- They were evaluated by the procedure fixed before any look (`docs/sets-evaluation-procedure.md`, 12ab70b), with
  `tools/prod_eval.py` at prod-eval-v1.

### 10.2 The outcome (entry r2, #12; `docs/sets-outcome-20261117.md`)

**Outcome 4 of five, "no cluster"** (`docs/bb2021-comparison-criteria.md` section 6: M2 < 0.20 in at least one set).
It holds in both sets.

| | set A | set B |
|---|---|---|
| M2 strength (limit ≥ 0.20) | 0.050 | 0.127 |
| M1 direction (160–200°) | 127.3°, every subset outside | 166.7°, every subset within |
| M3 pole (±30°) | 3.2° | 18.0° |
| M4 inner edge, A only (226–286 au) | 165 au | – |

- **Set B** has a cluster in the expected direction, stable over all four subsets (scatter 0.4°). Its strength lies
  below the limit.
- **Set A** misses its limit for the strength. Its direction lies outside its limit as well, consistent over all four
  subsets. Its inner edge is no separate miss: it is measured against the strength of the outer orbits and, with a
  strength this weak, follows from it.
- **What the criteria fix for this outcome:**
  - In the words of the criteria, it "contradicts Fig. 1 or Fig. 3 for that set".
  - A counter-run of set A with mercury6, the program of the paper, follows as an announced addendum with its own
    entry before the run.
  - The authors are asked about the details of their runs. This has not been done yet.
  - The production run (section 8) is "reported as not confirmed at long times, together with the outcome of A and B"
    (`docs/production-criteria.md` section 5). If mercury6 shows a cluster, it is held.

### 10.3 Looked at afterwards (exploratory; changes nothing of the outcome)

Each computation on our runs was fixed and timestamped before it was run (addenda 1–5 of the decomposition), with one
exception: the spread over the four subsets of set A (addendum 3) was written down after it was computed.
- The selection of the observable orbits (addendum 2) was fixed when preliminary values from 32 snapshots were
  already known.
- The readings of the paper's figures were not registered beforehand, nor was the comparison of set A with Fig. 4,
  formed afterwards from the inclination histogram of addendum 2.
- Addendum 5 and its result came after entry #12; they are timestamped, not entered on the chain.
- **Observable orbits** (perihelion 30–100 au, inclination below 40°, the selection of Batygin et al. 2019) cluster
  far more strongly than all orbits beyond the inner edge (0.10 and 0.15, simple means):
  - weighted 0.53 (A) and 0.45 (B), unweighted 0.55 and 0.48;
  - figures of the paper 0.60–0.61 and 0.51–0.52;
  - with only the bodies that survive 4 Gyr, as Batygin et al. (2019) show them: simple means 0.64 and 0.56
    (addendum 2), above the values read from the paper's figures;
  - the comparison formed the same way as the figures is the unweighted one.
  - The paper does not state this selection.
- **One figure speaks against it.** Fig. 4 of the paper shows about 0.92–0.94 of the pole density below 30°
  inclination for orbits with a perihelion beyond 42 au. Our set A has 0.57–0.62, counted like the figure over inclinations up to
  about 70° (over all inclinations 0.46), and 0.76 when weighted the way the paper weights simulated objects.
- **Inclination matters** (announced in addendum 5 before computing): with the registered measure and only orbits
  inclined below 40°, the strength is 0.21 (A; 0.207, at the limit, against a spread of the registered M2 over the
  four subsets of 0.046–0.056) and 0.28 (B), above it. Beyond the inner edge these orbits reach
  0.27 and 0.34, still well below the figures. The registered criterion counts all inclinations, so the outcome stays.
- **Not a matter of the definition of ϖ** (addendum 5, after an independent reading of the code,
  `docs/code-review-20261121.md`): with the azimuth of the eccentricity vector, or with Ω − ω for retrograde orbits,
  the strength is 0.053 and 0.052, respectively (A), and 0.122 and 0.130 (B); the direction of set A moves to 136°
  and 139° and stays outside its limit.

### 10.4 Announced, without results here

- **BB-A-rin1** (#9): set A with the inner removal checked in every step. It tests whether this rule of our program
  explains the difference. Prediction entered beforehand: most likely not the cause. MERCURIUS removes with the same
  rule and cadence, so the comparisons with it say nothing about this.
- **BB-A2** (#10): set A with a second, independent seed for the test bodies. It measures the spread between two
  realisations.
- **The mercury6 counter-run of set A** (10.2).

## 11. Reproducibility check

Six stored segments, computed again on the same A100 from their stored inputs with the run's own program (package
p9repro-d3c2363, 2026-11-11), gave their stored result hashes again: **6 of 6**
(`docs/reproduction-result-20261112.md`).
- **Which segments:** segments 0, 19 and 39 of the production run, and segment 19 of each V5 long run.
- **Also identical:** the flyby and removal logs.
- **Tied to the evaluations:** the recomputed hashes equal the `DONE` files of the stored runs, whose lines are in the
  checksum lists timestamped before the evaluations.
- **Scope:** reproducibility on the same hardware. Across machines, the package checks and `docs/reproducibility.md`
  apply (section 2.1).

## 12. Discussion

What the results so far say, within the limits of section 3.

**Question 1 (production run), as classified in the result reports:**
- **Direction (M1) and pole (M3): robust in the sense of the evaluation.**
  - The four subsets agree within 1.41° (limit 10°). In the frame and element variants M1 changes by at most 0.1°, and
    ψ lies between 1.5° and 3.9°.
  - From 1 to 4 Gyr M1 stays between 138° and 174°, and ψ stays within 8° of Planet Nine's pole from 0.5 Gyr on.
  - The check against MERCURIUS does not cover the direction: the equivalence test, the paired tests and the long runs
    compare the strength R, not M1.
- **Strength (M2): limited by the long-time check.**
  - R falls to 0.05 at 4 Gyr. That lies about 7 times above this run's own noise floor (0.0075 at n = 14,196), so it is
    not noise.
  - Whether MERCURIUS gives the same strength is checked by the long runs clearly at 1 Gyr, only with limits at 2 Gyr,
    and not at 4 Gyr, where their noise floor reaches the signal.
- **No significant difference between the methods:** none of the long-run differences is significant (t, 2 degrees of
  freedom: p ≈ 0.10–0.98).
- **Model of Brown & Batygin:** like ours, it contains no galactic tide and no passing stars, as far as their text
  says (section 3, with the limits of that check).

**Question 2 (method):** equivalent over 0–200 Myr (section 5). Over 4 Gyr: no growing bias found, with the power and
noise floor of section 9.

**Question 3 (comparison):**
- With our method, the two published simulation sets do not show the clustering of the published figures by the
  criteria fixed beforehand: outcome 4.
- Set B comes closer than set A: a cluster in the right direction, about two thirds of the required strength.
- **How far a late difference between the methods could reach:** in the long runs our integrator lay 0.045 below
  MERCURIUS at 4 Gyr (not significant; the same sign at 1, 2 and 4 Gyr), as large as the M2 of set A (0.050). Over the
  window 1–4 Gyr, over which M2 is formed, the difference of our integrator from MERCURIUS is −0.013 ± 0.005
  (standard error, three pairs), small against the distance of sets A and B from the limit (0.150 and 0.073). This
  holds only by analogy: the long runs used the Planet Nine of the production run (section 3) and measure the bodies
  with a > 230 au, M2 of the sets those with 150–1,000 au.
- **What this does not mean:**
  - no statement about Planet Nine;
  - no judgement on the paper, because the cause of the difference is not known.
  - Each set is one realisation.
  - Values of the paper are read from figures.
- **Where the difference lies, as far as seen afterwards:** in orbits with a high perihelion or a high inclination,
  which remain in our runs. The observable orbits come within 0.03–0.08 of the values read from the figures; with only
  the bodies that survive 4 Gyr they lie above them (0.64 and 0.56). Which orbits the figures count, only
  the authors can say.

**The combined reading** that `docs/production-criteria.md` section 5 fixes for the production run together with sets
A and B:
- It requires outcome 1, which is not reached.
- The production run is therefore "reported as not confirmed at long times, together with the outcome of A and B":
  its values stand as computed (section 8), but not as the long-term behaviour of their Planet Nine with our method.

## 13. Data and code availability

- **Code and documents:** https://github.com/oxygene76/medas-p9-search, GPL-3.0-or-later, public from 2026-11-24.
  - Which run was computed from which commit and package is in the README.
  - Run packages with binaries and the REBOUND 5.2.2 source.
- **Notary entries:** the manifests and the files outside git of the revealed entries are attachments of the release
  `notary-reveal-1`.
- **Data:** Zenodo records per campaign, CC BY 4.0 (`docs/data-package-proposal.md`). The DOI follows with entry e7.
- **Verification:**
  - the SHA-256 of a manifest equals the content digest the chain shows for the revealed entry;
  - every file has the SHA-256 that its line names (`tools/manifest.py verify`);
  - one segment rerun gives its result hash.

## References

- Brown, M. E., & Batygin, K. 2021, AJ, 162, 219.
- Rein, H., & Liu, S.-F. 2012, A&A, 537, A128 (REBOUND).
- Rein, H., Hernandez, D. M., Tamayo, D., et al. 2019, MNRAS, 485, 5490 (MERCURIUS).
- Batygin, K., Adams, F. C., Brown, M. E., & Becker, J. C. 2019, Physics Reports, 805, 1.
- Chambers, J. E. 1999, MNRAS, 304, 793 (mercury6).
- Wisdom, J., & Holman, M. 1991, AJ, 102, 1528.
- Park, R. S., Folkner, W. M., Williams, J. G., & Boggs, D. H. 2021, AJ, 161, 105 (DE440).
- OpenTimestamps, https://opentimestamps.org.
