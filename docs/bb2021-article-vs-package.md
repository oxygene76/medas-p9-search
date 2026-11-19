# Brown & Batygin 2021 against our package, sets A and B (2026-11-19)

The setup of the paper as printed, set against the run package of sets A and B. Taken over from the draft of
2026-11-17 after its review. The pages and quotes were checked again against the PDF on 2026-11-19. The state of
the run BB-A-rin1 was updated on the same day.

**Sources:**
- **Paper:** Brown & Batygin 2021, arXiv:2108.09868v2, PDF sha256
  `bc44f09280147a6c9f454d7395020ae5c897e6c41f70536b79e15d088bb527fa`. Pages are those of the PDF.
- **Package:**
  - `p9bbsets-5b05cc3`: `jobs/BB-A/job.json`, `params.env`, source;
  - `tools/make_ic.py` as of `make-ic-v1`;
  - `tools/prod_eval.py` (`prod-eval-v1`);
  - `docs/bb2021-comparison-criteria.md` (as of entry e4, 1c5f2ba).
- **For context:** Batygin et al. 2019 (arXiv:1902.10103v1), checked against the PDF.

**Verdict per row:** same / different / not stated in the paper.

| quantity | paper (place) | package (place) | verdict |
|---|---|---|---|
| Planet Nine, set A: mass, a, i, e | 7 Earth masses, 500 au, 17°, 0.33 (Fig. 3, third panel, p. 10; Table 2, p. 24) | the same (`job.json` BB-A: `m_earth=7, a=500, e=0.33, inc=17`; criteria section 2) | same |
| Planet Nine, set A: ϖ9, Ω9 | 250°, 100° (Table 2, p. 24) | 250°, 100°, M = 0 (`job.json`) | same; the paper does not give the anomaly M9 ("unused", p. 7) |
| Planet Nine, set B: mass, a, e | 5 Earth masses, 300 au, 0.15 (Fig. 1, p. 5; section 4.3, p. 12; Table 2, p. 22) | the same (criteria section 2) | same |
| Planet Nine, set B: i9 | not uniform: 16° in the caption of Fig. 1 (p. 5), 17° in section 4.3 (p. 12) and Table 2 (p. 22) | 17° | same as Table 2 and section 4.3; 1° from the caption of Fig. 1 (noted in the criteria) |
| Planet Nine, set B: ϖ9, Ω9 | 254°, 108° (Table 2, p. 22; ϖ9 = 254° also in section 4.3) | 254°, 108° | same |
| Number of test particles | 16,800–64,900 per simulation (p. 8); set A 17,500 (Table 2, p. 24), set B 25,600 (Table 2, p. 22) | 64,000 each (seeds 311 and 312) | different (more particles) |
| Reference plane of Planet Nine's orbit | "referenced to the initial plane of the four interior giant planets" (p. 8) | invariable plane of Jupiter to Neptune from DE440s, I = 1.579°, N = 107.63°, dog-leg longitudes (`make_ic.py --p9-plane invariable`) | same |
| Reference plane of the test particles' inclinations | the same plane; the sentence holds for "all objects" (p. 8) | **ecliptic J2000.** The docstring of `make_ic.py` says: "The test particles stay in the ecliptic frame". | **different:** tilted by up to 1.6°; the angles are uniform |
| Initial distribution of the test particles | a 150–500 au, q 30–50 au, i 0–25°, "all other orbital angles randomly distributed" (p. 8). The shape of the distribution is not stated. | a, q, i uniform (i in degrees), Ω, ω, M uniform (`make_ic.py`; ranges in `job.json`) | ranges the same; shape not stated in the paper |
| Planets | "the 5 giant planets" (p. 8) | Jupiter to Neptune from DE440s plus Planet Nine | same |
| Inner planets | not stated | the masses of Mercury to Mars in the Sun (`make_ic.py`) | not stated in the paper |
| Integrator and time step | mercury6, dt 300 days, "adaptively reduced to directly resolve close encounters" (p. 8) | p9gpu v5: Wisdom–Holman, democratic heliocentric, dt 0.5 yr (182.6 days), close encounters with a smooth transition to sub-steps, planets with 8 inner steps, FP64 (`job.json`) | different; checked against MERCURIUS over 0–200 Myr (paired tests) |
| Inner removal | "reach r < 4.5 … AU are removed" (p. 8). mercury6 checks this at every step or perihelion passage (own mercury6 study of 2026-11-11, section 3). | r < 4.5 au on the synchronous state, **only every 1000 steps** (500 yr; `CHECK_EVERY`, fixed in the program). MERCURIUS (p9sim) in our paired and long runs: the same rule and cadence. | **different in cadence.** Tested by the run BB-A-rin1 (criteria entry e6, #9); result pending. |
| Outer removal | r > 10,000 au (p. 8) | r > 10,000 au, every 1000 steps | limit the same, cadence different |
| Further removal rules of the package | – | Removal at close encounters: off (method smooth follows them with sub-steps). Model j2 with r_remove: off (model full, `P9_J2` cleared by `run-job.sh`). The counter `removed_inner` belongs to that j2 rule and is 0 in all 40 segments of both sets; it does **not** count the rule r < 4.5 au. | does not apply (not active in the package) |
| Removal counters | not stated | BB-A/BB-B: only `removed` (inner and outer together) and `removed_encounter` (collisions). From p9gpu 0b8971f also `removed_r_in`, `removed_r_out`, `removed_collision`. | not stated in the paper |
| Collisions | "Objects that collide with planets … are removed" (p. 8); radii not stated | collision with the physical radius (IAU radii; Planet Nine assumed 2.707 Earth radii for 7 Earth masses), at every step (`job.json`) | rule the same; radii not stated in the paper |
| Duration and window | 4 Gyr, analysed over "the final 3 Gyr" (p. 9) | 0–4 Gyr, window 1–4 Gyr (criteria section 4) | same |
| Snapshots | not stated | every 10 Myr, 301 in the window | not stated in the paper |
| Frame of the angles in the analysis | rotated after the run to a frame "aligned with the orbital pole of Jupiter … keep the longitude zero-point fixed" (p. 8) | plane of Jupiter at each snapshot, dog-leg longitudes (`prod_eval.py`, `frame_elements`) | same in intent (criteria, condition V3) |
| Elements | not stated (barycentric or heliocentric) | barycentric; heliocentric as a variant that does not judge | not stated in the paper (noted in the criteria) |
| Selection for the analysis | "a > 150 AU … q > 42 AU for analysis for both the data and for the simulations" (p. 4); for the likelihood, per observed object q ± 10 au (lower limit 42 au) and a ± 5–30 %, with Gaussian weights (pp. 9–10) | S_BB: 150 < a < 1000 au, q > 42 au, all particles (criteria section 4) | same as the text of p. 4 |
| Selection of the particles in Figs. 1 and 3 | **not stated in the paper.** The captions say only "normalized at every semimajor axis" (p. 5, p. 10). In 2019 such figures were built with cuts: 30 ≤ q ≤ 100 au (text: < 100), i < 40°, only particles stable over 4 Gyr, the last 2 Gyr (1902.10103, Fig. 14, pp. 41–42, footnote 16). | the criteria compare all of S_BB | not stated in the paper; 2019 with cuts |
| Selection of the particles in Fig. 4 | "pole positions of KBOs with a > 150 AU and q > 42 AU" (caption, p. 11); no inclination cut, no upper limit in q; weighting and the treatment of retrograde poles not stated | the criteria compare all of S_BB; Fig. 4 is information | same selection as stated; weighting not stated in the paper |
| Galactic tide, passing stars | not stated (only "5 giant planets" and test particles) | not included (criteria, addendum 14) | same as far as the paper describes |

## For attention

**Differences that can affect the population beyond the wall,** as far as we can check:
1. **The selection of the particles in the figures** (not stated). Addendum 2 shows a clustering like the figures
   under the selection of 2019. Under the a,q weighting of the likelihood, the weighted reading of Fig. 4 does not
   fit for set A (addendum 4).
2. **The cadence of the inner removal.** The run BB-A-rin1 tests it (criteria entry e6, #9, 2026-11-18); its result
   is pending.
3. **The reference plane of the test particles.** About 1.6° against an initial spread of up to 25°; the effect is
   not tested.
4. **Integrator and time step.** Checked against MERCURIUS over 0–200 Myr; over 4 Gyr only with limits.

**What the table does not say:** which of these differences acts how strongly. It is no judgement on the paper.
