# Decomposition, addendum 4: result (2026-11-18)

**Status addendum of 2026-11-22** (the text below is unchanged as entered):
- Entered with entry r2 (#12) on 2026-11-21.
- A review of this report before the entry is not documented.
- On 2026-11-22, after the entry, an AI session (p9-review-82) read this report independently and compared it with the result files; it found no computing error. The limitations it found are taken up in the research note (`docs/research-note.md`) and on the result pages of the website.

Exploratory, as fixed by `docs/sets-decomposition-addendum-4-20261118.md` (22f70fd, timestamped before). Script
`tools/sets_addendum4.py` (0a13208, committed before it ran, run from a clean detached checkout), 301 snapshots
(1–4 Gyr). **It changes nothing:** not the criteria of the sets, not their verdicts, not outcome 4. Files:
`docs/sets-decomposition-4-20261118/`. For review.

## (a) Not computed

MERCURIUS (p9sim) removes with the same rule and cadence as p9gpu: r < 4.5 au and r > 10,000 au every 1000 steps, dt
0.5 yr, no collisions with the Sun. The comparisons of V5 with MERCURIUS (equivalence test, paired tests, long runs) say
nothing about the cadence.

## (b) The reading "weighted Fig. 4": does not fit (set A)

Weighting of the paper's likelihood (pp. 9–10), 10 objects of `docs/bb2021-observed-table1.tsv`; variant with 11
objects.

| | < 30° | 30–40° | 40–50° | 50–70° | retrograde |
|---|---|---|---|---|---|
| set A, weighted (10 objects) | **0.761** | 0.119 | 0.055 | 0.066 | 0.097 |
| set A, weighted (11 objects) | 0.761 | 0.119 | 0.055 | 0.066 | 0.098 |
| set B, weighted (10 objects), information | 0.844 | 0.104 | 0.034 | 0.018 | 0.001 |
| Fig. 4, panel i9 = 15° (measurement) | 0.92–0.94 | | | | |

- **Scale (set A, < 30°):** ≥ 0.88 fits, < 0.80 does not fit. With 0.761 the verdict is **"the reading does not fit"**.
- **R beyond the wall with the q weighting:** set A 0.274 (Fig. 3, third panel: 0.60–0.61), set B 0.467 (Fig. 1:
  0.51–0.52). Information.

## (c) Bounds for BB-A-rin1 (set A without the particles whose q was ever below X since t = 0)

| X | particle-snapshots in S_BB | M2 | M1 | R beyond the wall | q > 42 au: < 30° / 30–40° / 40–50° / 50–70° / retro | 42 ≤ q ≤ 100 au: same |
|---|---|---|---|---|---|---|
| (none, set A) | 5,518,578 | 0.0496 | 127.3° | 0.097 | 0.622 / 0.134 / 0.095 / 0.149 / 0.171 | 0.794 / 0.109 / 0.045 / 0.053 / 0.069 |
| 4.5 au | 5,518,578 | 0.0496 | 127.3° | 0.097 | the same | the same |
| 10 au | 5,489,881 | 0.0506 | 127.4° | 0.098 | 0.623 / 0.134 / 0.095 / 0.148 / 0.168 | 0.794 / 0.109 / 0.045 / 0.053 / 0.067 |
| 20 au | 4,583,291 | 0.0827 | 142.9° | 0.118 | 0.669 / 0.130 / 0.083 / 0.117 / 0.139 | 0.823 / 0.105 / 0.037 / 0.035 / 0.046 |
| 30 au | 3,603,402 | 0.1311 | 154.5° | 0.166 | 0.721 / 0.120 / 0.068 / 0.090 / 0.109 | 0.853 / 0.096 / 0.028 / 0.023 / 0.031 |

**What follows:**
- No particle-snapshot of S_BB in the window ever had q < 4.5 au at a snapshot.
- Excluding those ever below 10 au changes nothing beyond the tolerance band of the BB-A-rin1 draft.
- Even the conservative bound X = 30 au gives M2 0.131 and M1 154.5°, still below 0.20 and outside 160–200°.
- **The assumption behind the bound:** a particle that dips below 4.5 au between two snapshots has q < 30 au at one of
  them. It is plausible, because q cannot go from above 30 au to below 4.5 au and back within 10 Myr without close planet
  encounters, but it is not proved.

**No judgement** on the paper or on Planet Nine.
