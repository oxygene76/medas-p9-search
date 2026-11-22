# Decomposition of sets A and B, addendum 2 (selection of Batygin et al. 2019): result (2026-11-17)

**Status addendum of 2026-11-22** (the text below is unchanged as entered):
- Entered with entry r2 (#12) on 2026-11-21.
- Contrary to the status line below, it was not reviewed independently before the entry.
- On 2026-11-22, after the entry, an AI session (p9-review-82) read this report independently and compared it with the result files; it found no computing error. The limitations it found are taken up in the research note (`docs/research-note.md`) and on the result pages of the website.

**Status:**
- Exploratory, after outcome 4, as fixed by `docs/sets-decomposition-addendum-2-20261117.md` (843438e, timestamped
  before this computation; not blind, see there).
- **It changes nothing:** not the criteria, not the verdicts, not outcome 4. It makes no statement about the paper of
  2021 or about Planet Nine.
- For independent review.

**How it was computed:**
- `tools/sets_decompose2.py`, committed before it ran (199211e), from a clean detached checkout of 199211e.
- 301 snapshots of the window 1–4 Gyr.
- 4-Gyr survivors: 17,616 (A) and 20,723 (B).
- Beyond the wall: 260–700 au (A), 200–700 au (B).
- **Files:** `docs/sets-decomposition-2-20261117/`.

## R per 10 au beyond the wall and anti-aligned share

| selection | set A: mean R | A: share 90–270° | A: verdict | set B: mean R | B: share 90–270° | B: verdict |
|---|---|---|---|---|---|---|
| (a) 30 ≤ q ≤ 100 au, i < 40°, all | 0.548 | 0.813 | cluster as in the figures | 0.482 | 0.788 | cluster as in the figures |
| (a) survivors | 0.640 | 0.867 | cluster as in the figures | 0.560 | 0.846 | cluster as in the figures |
| (b) 42 ≤ q ≤ 100 au, i < 40°, all | 0.546 | 0.817 | cluster as in the figures | 0.467 | 0.782 | cluster as in the figures |
| (b) survivors | 0.636 | 0.870 | cluster as in the figures | 0.543 | 0.839 | cluster as in the figures |
| (c) q > 42 au, all | 0.097 | 0.496 | no cluster | 0.154 | 0.575 | no cluster |
| (c) survivors | 0.091 | 0.506 | no cluster | 0.149 | 0.578 | no cluster |

- **Scale of the addendum:** ≥ 0.4 "cluster as in the figures", ≤ 0.2 "no cluster".
- **For information:**
  - The measured figures give 0.61 (Fig. 3, third panel) and 0.52 (Fig. 1), and anti-aligned shares of 0.87 and 0.83.
  - The preliminary values of the Claude chat from the exports (32 snapshots) agree within 0.002 in R.

## Inclinations, 150 < a < 1000 au

| selection | set A: i < 30° (q cut only) | A: i > 50° | A: i > 90° | A: i < 30° within the selection | set B: i < 30° (q cut only) | B: i > 50° | B: i > 90° | B: i < 30° within the selection |
|---|---|---|---|---|---|---|---|---|
| (a) all | 0.713 | 0.150 | 0.069 | 0.880 | 0.800 | 0.033 | 0.002 | 0.865 |
| (a) survivors | 0.728 | 0.145 | 0.070 | 0.890 | 0.807 | 0.039 | 0.002 | 0.879 |
| (b) all | 0.710 | 0.153 | 0.069 | 0.880 | 0.797 | 0.036 | 0.002 | 0.865 |
| (b) survivors | 0.730 | 0.145 | 0.068 | 0.891 | 0.803 | 0.041 | 0.003 | 0.878 |
| (c) all | 0.462 | 0.368 | 0.171 | 0.462 | 0.532 | 0.223 | 0.008 | 0.532 |
| (c) survivors | 0.462 | 0.374 | 0.177 | 0.462 | 0.507 | 0.251 | 0.010 | 0.507 |

- "q cut only" means the q range of the selection without its i cut. The histograms in 5° classes are in
  `inc_hist.csv`.
- For information: Fig. 4 of B&B (m9 7, a9 500, e9 0.33, i9 15°) shows 94 % of the pole density at i < 30°.

## Image

`bild-auswahl-a-ueberlebende.png`: selection (a), 4-Gyr survivors only, in the format of Fig. 1 (a against Δϖ,
normalised per a column, 1–4 Gyr pooled, square root shown).

## What this shows, and what not

- **What it shows:** Under the selection of 2019 (and with 42 au as lower limit instead of 30 au), both runs show beyond
  the wall a cluster of the strength and anti-aligned share that the figures of 2021 show. With the 4-Gyr survivors it
  is somewhat stronger. Over all of q > 42 au they show none.
- **What it does not show:** that the figures of 2021 were made with the cuts of 2019. The paper of 2021 does not state
  its selection (to be checked against the PDF).
- **What it does not change:** outcome 4, which the criteria fix for all of S_BB (q > 42 au). It is no judgement on the
  paper or on Planet Nine.
