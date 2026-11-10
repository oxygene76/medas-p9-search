# Research note (draft skeleton, 2026-11-10): the long-term clustering of distant trans-Neptunian bodies under the Planet Nine of Brown & Batygin (2021), with a pre-registered, notarised protocol

**Status:** skeleton without results. Sections marked **[RESULT]** stay empty until the evaluation of the run they
belong to, as fixed in its criteria ("no result before its evaluation"). Nothing here is to be read as a finding.
Not peer-reviewed.

**Author:** Eike Janßen, MEDAS Computers GmbH (ORCID to follow).

---

## Abstract

**[RESULT]** To be written last, from the result sections.

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
  - massless test bodies: a 150–500 au, q 30–50 au, i 0–25°, made by `tools/make_ic.py`.
- **Integrator:** Wisdom–Holman in democratic heliocentric coordinates, dt 0.5 yr.
  - Close encounters with a smooth transition to sub-steps.
  - The planets with 8 inner steps, in FP64.
  - Removal beyond 10,000 au, within 4.5 au of the Sun, and on collision with a planet's physical radius.
  - The details: `docs/gpu-integrator.md`, `docs/close-encounters.md`.
- **Reference:** MERCURIUS (REBOUND 5.2.2), r_crit 3 Hill radii, the same start values.
- **Production run:** 64,000 test bodies, 0–4 Gyr, a snapshot every 10 Myr, as 40 segments of 100 Myr.
- **Bit reproducibility:**
  - every segment has a result hash over the canonical states of all its snapshots (`docs/reproducibility.md` of
    medas-p9-search-bb2021);
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
- **Speed comparison:** that of 2026-11-03/04 in medas-p9-search-bb2021 (`docs/`, `speed/`).
- **Program versions:** p9gpu and p9sim of commit 9a084ed (sha256 `7666c5ba…`, `b14f7956…`), REBOUND 5.2.2, CUDA
  build as in `docs/production-package.md`.

### 2.4 Methods and tools, including AI tools

To be agreed with the author before publication (`docs/data-package-proposal.md` section 5):
- An AI coding assistant (Claude, Anthropic) wrote and revised code, tests, packages and documents under the
  direction of the author.
- The author made the scientific decisions: questions, criteria, thresholds, the order of the runs, and the
  acceptance of each evaluation.
- Every result rests on deterministic programs and their tests, not on the assistant.
- The criteria were fixed and notarised before the runs (section 4).

## 3. Model assumptions and limits

From `docs/production-criteria.md` section 7 and `docs/bb2021-comparison-criteria.md` addendum 14, stated before the
runs:
- **Gravity of the Sun and the planets only.** No galactic tide, no passing stars, no birth cluster.
  - The galactic tide matters for a > 1,000–2,000 au; S_BB ends at 1,000 au.
  - Bodies that pass through larger a and come back can still carry its effect, which is not modelled.
  - Whether Brown & Batygin included the tide is to be checked against their text before this note is final.
- **Massless test bodies:** no self-gravity of the disk, no collisions among them.
- **No observational bias.** M1–M5 describe the simulated distribution, not what surveys would see. The 10 observed
  objects of their Table 1 are shown for information only and are not judged (`docs/bb2021-observed-table1.tsv`,
  ϖ9 = 254°; the Planet Nine of the production run starts at ϖ = 248.5°).
- **Method:** the equivalence with MERCURIUS was shown for 0–200 Myr. Over 4 Gyr it rests on three paired long runs,
  which can find only large biases (about 0.05 in R).
- **One posterior point:** the production run uses one Planet Nine, and sets A and B two more. It is not a sample of
  the posterior.

## 4. Pre-registration: notary entries and timestamps

All criteria, tools and packages were fixed before the runs they concern and entered on the chain medasdigital-2 in
the notary contract `medas1ghd753shjuwexxywmgs4xz7x2q732vcnkm6h2pyv9s6ah3hylvrqejyaze`. Each entry is a commitment to
a manifest that lists every file by sha256 and git commit.

| entry | chain entry | time (UTC) | block | content |
|---|---|---|---|---|
| a3 | #2 | 2026-11-02 12:08:31 | 10694917 | validation status up to 2026-10-21, with the addendum on single runs and means |
| e2 | #3 (refers to #2) | 2026-11-02 12:14:09 | 10694977 | the equivalence test, fixed before its evaluation |
| e3 | #4 (refers to #3) | 2026-11-04 09:31:02 | 10723643 | equivalence result; criteria of the production run, of the long runs 110–112 and of the order on the A100; the packages |
| e4 | #5 (refers to #4) | 2026-11-04 17:06:01 | 10728476 | addendum 16 (V2 short runs) and the packages of sets A and B |
| e5 | #6 (refers to #5) | 2026-11-10 07:18:02 | 10814015 | criteria of the paired tests V5 against MERCURIUS for sets A and B |
| e6 | planned | – | – | the data package (`MANIFEST.sha256` of each record, every `segments.tsv`, the `result.json` files) |

The transactions and commitments are in `docs/notary.md`. The manifests and the files without git are published with
the data package, and the reveal follows the publication.

**OpenTimestamps (Bitcoin), a second, independent anchor:**

| file | Bitcoin block |
|---|---|
| manifests a3 and e2 | 973126 (2026-10-25 21:00:34 UTC), 973129, 973151 |
| checksum list of the equivalence runs | 974272 (2026-11-02 15:49:32 UTC) |
| comparison criteria with Brown & Batygin at 224b7a1 | 974281 (2026-11-02 17:58:45 UTC) |
| IRAS/AKARI criteria, comparison criteria at 1c5f2ba, V2 result, checksum list of the production run, checksum lists and evaluation tool and procedure of the long runs | pending upgrade; to be filled in |

**Deviations from the registered protocol** (all reported, none changes a criterion):
- The evaluation tool of the long runs (`tools/long_eval.py`) was written after the runs and before any look at R. It
  was committed and timestamped before the evaluation, and two cases the criteria left open were decided beforehand
  (`docs/long-runs-evaluation-procedure.md`).
- The resume test of a V5 long run (interim check, criteria section 5) did not take place, because the runs went
  through without interruption.
- The V5 part of seeds 110–112 ran on the A100 instead of the L40S (addendum of 2026-11-04, before any run).

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
- **[RESULT]** Set A: verdict, mean, 95 % interval.
- **[RESULT]** Set B: verdict, mean, 95 % interval.

## 8. Production run: clustering over 1–4 Gyr

- Run p9prod-9a084ed, complete: 40 of 40 segments, 17,798 of 64,000 test bodies left at 4 Gyr. Result hash of the
  last segment: `d41152221b3dfc9ff490a21eb0120896b9bfce95a6a2bb0378c8005b0527f1c3`.
- The checksum list of all 517 result files was timestamped before the evaluation.
- **[RESULT]** M1–M5 pooled and per subset; the verdict (decided / not decided).
- **[RESULT]** Information: time series of M1–M3, selections S1–S3, survivors, position of the observed objects.

## 9. Long-time check: paired long runs, seeds 110–112

- V5 on the A100 and MERCURIUS on the CPU, 0–4 Gyr, 3 × 2,000 test bodies. All 120 V5 and 4,800 MERCURIUS segments
  were checked as consistent, and the start values are paired.
- **[RESULT]** S(t) per run; d(t) with standard errors at 0.5, 1, 2 and 4 Gyr; the decision (growing bias found / no
  growing bias found / not decided), stated with the low power of three pairs.

## 10. Sets A and B: comparison with Brown & Batygin (2021)

- **[RESULT]** Only if released by the paired tests: the 4-Gyr runs, measures and outcome as in
  `docs/bb2021-comparison-criteria.md` section 6. Otherwise: not computed, with the reason.

## 11. Reproducibility check

- **[RESULT]** Six stored segments (production run segments 0, 19 and 39, and segment 19 of each V5 long run) computed
  again on the same card from their stored inputs: result hashes compared (package p9repro-d3c2363).

## 12. Discussion

**[RESULT]** What the results say about questions 1–3, within the limits of section 3. The decision table of
`docs/production-criteria.md` section 5 says how the production run reads together with sets A and B and the long
runs.

## 13. Data and code availability

- **Data:** Zenodo records per campaign, CC BY 4.0 (`docs/data-package-proposal.md`), DOIs to follow. Fixed by entry
  e6 before the upload.
- **Code:** medas-p9-search, GPL-3.0-or-later (public at publication; `docs/publication-commits.md`). Run packages
  with binaries and REBOUND 5.2.2 source.
- **Verification:** sha256 of `MANIFEST.sha256` equal to entry e6; files equal to the manifest; one segment rerun gives
  its result hash.

## References

- Brown, M. E., & Batygin, K. 2021, AJ, 162, 219.
- Rein, H., & Liu, S.-F. 2012, A&A, 537, A128 (REBOUND).
- Rein, H., Tamayo, D., et al. 2019, MNRAS, 485, 5490 (MERCURIUS). *To be checked.*
- Wisdom, J., & Holman, M. 1991, AJ, 102, 1528.
- Park, R. S., Folkner, W. M., Williams, J. G., & Boggs, D. H. 2021, AJ, 161, 105 (DE440).
- OpenTimestamps, https://opentimestamps.org.
