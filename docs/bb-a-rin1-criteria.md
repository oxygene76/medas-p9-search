# Run BB-A-rin1: set A with the inner removal in every step (criteria, fixed 2026-11-18)

**Status:**
- **Fixed** on 2026-11-18, after the review by the Claude chat (draft 38c7a0b, version 2 ca87c80 with expectation and
  prediction, counters e3f7a0e). Entered on medasdigital-2, as its hash only, **before** the run starts.
- **Done before the entry:**
  - the proof run on the A100 has passed (`p9rinproof-0b8971f`: segments 0–5 of BB-A bit for bit, `PROOF.ok`);
  - the timing test (section 2).
- **Still to come:** the entry, then the project lead's go. Nothing is started before.
- Exploratory, after outcome 4. **It changes nothing:** not the criteria of the sets, not their verdicts, not outcome 4,
  not the consequences of section 6 of `docs/bb2021-comparison-criteria.md`. The mercury6 counter-run of set A stays
  prescribed.

## 1. The question

Does the stricter inner removal explain the difference of set A from Brown & Batygin 2021? The difference sits
beyond the wall:
- weak clustering of all of S_BB;
- many highly inclined particles, compared with Figs. 1, 3 and 4 of the paper.

**The two rules:**
- **Ours:** r < 4.5 au on the synchronous state, checked only every 1000 steps (500 yr; `CHECK_EVERY`, fixed in p9gpu).
  A passage inside 4.5 au lasts about 0.5–2 yr, so most single passages are not seen. That holds per passage, not per
  particle (see "Expectation" below).
- **MERCURIUS (p9sim) has the same rule and cadence** (heartbeat every 1000 steps, dt 0.5 yr, no collisions with the
  Sun). The comparisons of p9gpu with MERCURIUS therefore say nothing about the cadence (addendum 4).
- **The paper's:** "reach r < 4.5 … AU are removed" (p. 8). mercury6 removes a body at its first perihelion passage
  inside 4.5 au (own mercury6 study of 2026-11-11, section 3).

**Expectation, computed before the run:**
- **The old rule delays a removal, it does not prevent it.** For a parabolic passage with perihelion q the time inside
  4.5 au is 2√(2q³/μ)(D + D³/3), D = √(4.5/q − 1).
  - It is 1.65 yr at q = 0.5 au, 2.0 yr at 2 au, 1.3 yr at 4 au and 0.5 yr at 4.44 au.
  - The chance that the check every 500 yr hits a passage is 0.27–0.40 % for q = 0.5–4 au, and 0.1 % at 4.44 au.
  - With orbital periods of about 5,000–15,000 yr (a = 300–600 au), an orbit that keeps q < 4.5 au is removed on
    average after about 1.3–5.5 Myr; near q = 4.44 au after up to about 15 Myr.
  - Such orbits also cross Jupiter's and Saturn's and are often ejected before that.
- **The new rule removes these particles at their first passage.** Since BB-A-rin1 can only lose particles against BB-A
  (section 2), its effect is bounded by what removing the particles that came close to the Sun can do. Addendum 4 (c)
  measures that bound on set A (`docs/sets-decomposition-4-20261118.md`):
  - excluding the particles whose q was ever below 4.5 au at a snapshot removes nothing;
  - below 10 au: M2 0.051, R beyond the wall 0.098 (set A: 0.050, 0.097);
  - below 30 au, the conservative bound: M2 0.131, M1 154.5°, R beyond the wall 0.166, share below 30° at q > 42 au 0.72.
- **How much the 10-Myr cadence of the snapshots can underestimate this:**
  - It misses only particles that dip below 4.5 au and come back between two snapshots.
  - To stay out of the X = 30 au bound, a particle would have to go from q > 30 au to below 4.5 au and back above 30 au
    within 10 Myr. With periods of thousands of years and secular changes of q over tens to hundreds of Myr, that needs
    close planet encounters and is not expected to be common. It is not excluded.

**Prediction, fixed before the run:**
- **Most likely:** "the removal rule is not the cause". M2 and the inclination shares stay within the tolerance band
  around set A, as for X = 10 au.
- **Less likely:** "unclear", if many particles dip below 4.5 au between snapshots. The bound for X = 30 au (M2 0.13,
  M1 155°) would then be reached at most.
- **Not expected:** "the removal rule is the cause" (M2 ≥ 0.20 with M1 within 160–200°). It would need many particles of
  the kind the bound does not cover.

## 2. The run

**Identical to BB-A:**
- package `p9bbsets-5b05cc3`, its `input.sa` (sha256 `7699d0bf…66c4`), seed 311, 64,000 test particles;
- `params.env` of BB-A, 0–4 Gyr in 40 segments of 100 Myr, 10 snapshots per segment;
- the A100, CPUs 16–31.

**The only difference:**
- p9gpu of commit 0b8971f (branch `feat/rin-every`) with `P9_R_IN_EVERY=1`: the rule r < 4.5 au also in every step, on
  the synchronous state;
- with a prefilter (synchronous state only within 14.5 au) that changes no decision.

**The removal rules of the package** (p9gpu, method smooth, as in BB-A and BB-B):

| rule | condition | cadence | set by | in BB-A/BB-B | in BB-A-rin1 |
|---|---|---|---|---|---|
| inner distance | r < R_IN = 4.5 au, heliocentric, synchronous state | every 1000 steps (500 yr) | `P9_R_IN` in `params.env`; cadence `CHECK_EVERY` fixed in the program | active | **every step** (`P9_R_IN_EVERY=1`), otherwise unchanged |
| outer distance | r > 10,000 au | every 1000 steps | `R_OUT`, fixed in the program | active | unchanged |
| collision with a planet | closer than the planet's physical radius at the kick | every step | `P9_COLLISION_RADII` | active (`removed_encounter`, `removed_by`) | unchanged |
| close encounter | within the encounter radius | every step | `P9_ENCOUNTER_REMOVE` | **off**: method smooth follows encounters with sub-steps and does not remove them | unchanged (off) |
| model j2, inner radius | r < r_remove (absorbed planets merged into the Sun) | every step, at the kick | 5th value of `P9_J2` | **off**: model full, `P9_J2` unset by `run-job.sh`; `removed_inner` 0 in all 40 segments of both sets | unchanged (off) |

**The outer rule (r > 10,000 au) stays every 1000 steps.** Reason:
- A body near 10,000 au moves a few au per 500 yr, and on a bound or barely unbound orbit it stays beyond 10,000 au far
  longer than 500 yr.
- A check in every step would remove the same particles at most a few hundred years earlier. No later state changes.
- The paper removes both; for the question only the inner rule matters.

**What remains of the gap to mercury6 (named as a limit):**
- A passage with perihelion between about 4.44 and 4.5 au stays inside 4.5 au for less than one step (0.5 yr), so a
  check in every step can miss it.
  - Parabolic estimate: time inside R for perihelion q is 2√(2q³/μ)(D + D³/3) with D = √(R/q − 1); it is 0.5 yr at
    q ≈ 4.44 au.
- If perihelia are spread evenly below 4.5 au, about 1.3 % of the passages inside 4.5 au fall into this band. About
  half of those are missed, so about 0.7 %.
- A missed particle usually comes back at its next perihelion with nearly the same q and is removed then: the removal is
  delayed, not avoided.
- A check of the osculating perihelion within the step is therefore not needed. It would also be a second change to the
  program.

**What follows from the program, and is checked in the run:**
- The check never changes a particle's state, and the test particles do not act on each other or on the planets.
- So every particle that never comes within 4.5 au in BB-A-rin1 has bit for bit the same state as in BB-A. The
  population of BB-A-rin1 is, at every snapshot, a subset of that of BB-A.
- **Early check after segment 0** (not a look at any measure; `early-check.sh` of the package):
  - every particle present in both runs at the snapshots of segment 0 has the same state (`p9sim dump`, per particle,
    bit for bit);
  - the particles of BB-A-rin1 are a subset of those of BB-A;
  - every missing particle is removed with the distance rule (alive 0), with a state at removal inside 1000 au
    (`removed_r_in` of the result line).
  - **If this fails, the run is stopped** and nothing is evaluated. The same holds for the counters of segments 0–5
    (section 3, point 5).

**Timing test** (A100, 2026-11-18, 1 Myr from `input.sa` of BB-A, before the entry):
- cadence 1000: `result_sha256` `fda499f969ab97489c0f0af0099058c964ada3f147de1ddb52264c4b2e0d3e8b`, 64.241 s, `removed_r_in` 0;
- cadence 1: the same hash, 65.034 s, `removed_r_in` 0, `r_in_every=1`;
- extra cost 1.2 %. With BB-A's 54.8 h the run takes about 55.5 h.

## 3. What is measured (window 1–4 Gyr, 301 snapshots, elements as `prod_eval.py`)

1. **M1–M5** with `tools/prod_eval.py --criteria bb2021-A` (= `prod-eval-v1`), the same limits as for set A
   (`docs/bb2021-comparison-criteria.md` section 5). They are information and enter the scale (section 4).
2. **R per 10 au beyond the wall, 260–700 au, all of S_BB** (150 < a < 1000 au, q > 42 au), pooled, bins with at least
   10 particle-snapshots, unweighted mean over the bins. The tool is that of addendum 1 (`tools/sets_decompose.py`,
   2d10dae).
3. **The inclinations, 150 < a < 1000 au, 1–4 Gyr:**
   - shares < 30°, 30–40°, 40–50°, 50–70°, normalised to 0–70°, and the retrograde share (i > 90°) of all;
   - for q > 42 au and for 42 ≤ q ≤ 100 au;
   - the tool is that of addendum 3 (`tools/sets_subset_spread.py`, 4eec855).
4. **Survivors** at 1, 2, 3, 4 Gyr (all, and in S_BB beyond the wall).
5. **Removals per segment** from the result line: `removed_r_in`, `removed_r_out`, `removed_collision` (new in 0b8971f;
   `removed_inner` counts only the j2 model and stays 0).
   - **Segments 6–39:** BB-A has only the sum (`removed`, `removed_encounter`). There the comparison with BB-A is made
     for the sum per segment; the split is reported for BB-A-rin1 alone.
   - **Segments 0–5: the split of BB-A is known** from the proof run `p9rinproof-0b8971f` (BB-A with cadence 1000,
     bit-identical to set A in all 6 segments, `PROOF.ok`):

     | segment | `removed_r_in` | `removed_r_out` | `removed_collision` | sum | N_end of set A |
     |---|---|---|---|---|---|
     | 0 | 147 | 6951 | 6 | 7104 | 56,902 |
     | 1 | 178 | 6571 | 6 | 6755 | 50,147 |
     | 2 | 132 | 3504 | 3 | 3639 | 46,508 |
     | 3 | 94 | 2375 | 2 | 2471 | 44,037 |
     | 4 | 75 | 2176 | 2 | 2253 | 41,784 |
     | 5 | 66 | 2071 | 1 | 2138 | 39,646 |
     | 0–5 | 692 | 23,648 | 20 | 24,360 | |

     Each sum is the decrease of N_end (from 64,006 bodies: 64,000 test particles and 6 massive bodies).
   - **What must hold for these six segments,** as a consequence of section 2: up to its own removal, a particle runs
     bit-identically in both runs, and BB-A-rin1 only adds removals inside 4.5 au. Hence, summed over segments 0..k
     for every k = 0..5:
     - `removed_r_in` of BB-A-rin1 ≥ that of BB-A: every particle that BB-A removes inside is removed inside by
       BB-A-rin1 too, at the same time or earlier;
     - `removed_r_out` and `removed_collision` of BB-A-rin1 ≤ those of BB-A: each of these removals in BB-A-rin1 is
       also one in BB-A, at the same step;
     - N_end of BB-A-rin1 ≤ N_end of BB-A. The difference equals the excess of all removals of BB-A-rin1 over those of
       BB-A: the particles that BB-A-rin1 removes inside while BB-A still keeps them.
     - A violation is treated like a failed early check: `sh stop.sh`, evaluate nothing.
   - **Reported for segments 0–5** (information, not judged), per segment and summed over 0–5:
     - the excess of `removed_r_in` over BB-A;
     - how much of it are particles that BB-A removes outside or by a collision in the same or a later of these
       segments;
     - how much are particles that BB-A still keeps at the end of segment 5.

## 4. The scale, fixed before the run

**Comparison values:** set A (`docs/sets-result-A-20261117/`; addendum 3, `docs/sets-decomposition-addendum-3-20261117.md`).

| quantity | set A |
|---|---|
| M2 | 0.050 |
| M1 | 127.3° |
| shares q > 42 au | 0.622 / 0.134 / 0.095 / 0.149, retrograde 0.171 |
| shares 42 ≤ q ≤ 100 au | 0.794 / 0.109 / 0.045 / 0.053, retrograde 0.069 |

**The tolerance band** (from addendum 3: the largest deviation of one of the four subsets from the whole set, times 2):

| quantity | tolerance |
|---|---|
| M2 | ± 0.012 |
| each inclination share | ± 0.008 |
| retrograde share | ± 0.022 (q > 42 au), ± 0.011 (42 ≤ q ≤ 100 au) |

**Why a multiple, and why 2:**
- **A lower bound:** The four subsets share the same planets and the same Planet Nine. Their spread measures only the
  scatter from the choice of particles, not that of another realisation of the planets. It is therefore a lower bound
  of the uncertainty of a single run.
- **Why that is still the right scale here:** BB-A-rin1 and BB-A have the same planets and the same particles. They
  differ only by the removed particles. So the scale that matters is that of the particle choice.
- **The factor 2** leaves room for the fact that the removed particles are not a random choice.
- **Said openly:** The rule "2 × the largest subset deviation" was set after the numbers of addendum 3 were known (see
  there).

**The three outcomes:**
- **"The removal rule is the cause":** M2 ≥ 0.20 **and** the pooled M1 within 160–200°.
- **"The removal rule is not the cause":** M2 and all inclination shares of both selections lie within the tolerance band
  around set A.
- **"Unclear":** everything else.

**How "unclear" is read:**
- **Stronger than tolerance, below 0.20:** If M2 or the shares leave the tolerance band towards the paper (M2 higher,
  fewer highly inclined particles) without reaching M2 ≥ 0.20 with M1 in 160–200°, the rule has an effect but does not
  explain the difference alone.
- **What is reported then:**
  - how far the run moves from set A towards the comparison values, as a share of the distance;
  - for R beyond the wall, the comparison values are 0.10 (set A) and 0.61 (Fig. 3, third panel);
  - for the share below 30° at q > 42 au, 0.62 (set A) and about 0.92–0.94 (Fig. 4, i9 = 15°).
- **The other direction:** If the run leaves the band away from the paper, that is reported as such.
- **In every case "unclear" decides nothing.** The scope of the mercury6 counter-run is set after it.

**Comparison values from the paper:** Fig. 3, third panel (R beyond the wall 0.61) and Fig. 4 (pole density) are
information, not part of the scale. Their measurement by the Claude chat is recomputed (`runs/notary`, 2026-11-17).

## 5. A look during the run

The run takes about 55.5 h (timing test, section 2), more than 30 h. Therefore one announced, purely informative status after 2 Gyr (segment 19):
- R beyond the wall and the inclination shares for the window 1–2 Gyr;
- no outcome, no consequence for the run; it is not stopped or changed because of it.
- Otherwise during the run only the status: segments, particle numbers, hashes, the removal counters.

## 6. What the run does not decide

- **Not tested:** integrator and time step (Wisdom–Holman, 0.5 yr against mercury6, hybrid, 300 days), the reference
  plane of the test particles (ecliptic against the plane of the giant planets, about 1.6°), the selection of the
  particles drawn in the paper's figures.
- **Not touched:** the verdicts on sets A and B, outcome 4 and its consequences.

## 7. Why the preview f of addendum 1 could not decide this

1. **Cadence:** It could only see q at the snapshots, every 10 Myr. A dip of q below 4.5 au between two snapshots stays
   invisible.
2. **Osculating q:** A q below 4.5 au at a snapshot does not say whether, and when, the particle would actually have been
   inside 4.5 au.
3. **What follows:** Its result ("does not explain", no particle-snapshot lost at X = 4.5 au) makes a large effect
   unlikely but does not rule it out. The run applies the rule itself.

## 8. Entry

- **Type:** `job`, referring to entry #5 (e4, which holds the package of sets A and B).
- **Content:** a manifest of
  - this file (as committed);
  - `docs/sets-decomposition-addendum-3-20261117.md` and the result of addendum 4 (basis of the tolerance and the
    prediction);
  - the package `p9rin-0b8971f` with its job BB-A-rin1;
  - the proof `p9rinproof-0b8971f` with its result `PROOF.ok`;
  - the program change 0b8971f;
  - the tools named in section 3.
- **After the run:** its result as `result` referring to this entry.
