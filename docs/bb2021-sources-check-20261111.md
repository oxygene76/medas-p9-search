# What sets A and B are compared with: check against the paper text (2026-11-11)

**What was checked:** the statements of `docs/bb2021-comparison-criteria.md` sections 1 and 2 (entered with entries
e3 and e4) about the sources of the comparison, against the text of Brown & Batygin (2021), arXiv:2108.09868v2
(26 Aug 2021). The text was extracted with pypdf from the arXiv PDF (sha256 `bc44f092…27fa`). Printed page numbers
equal the PDF pages.

**Result:** every page, section, number and quotation below agrees with the criteria. Nothing in the criteria has to
change. The journal version (AJ 162, 219) was not compared.

## Set A: m9 7, a9 500 au, i9 17°, e9 0.33, ϖ9 250°, Ω9 100°

| what | where | text |
|---|---|---|
| distribution with wall and width | Fig. 3, third panel, p. 10 | caption: "Probability density of a versus ∆ϖ for a variety of simulated Planets Nine, in the same format as Fig.1. At the lowest masses the cluster appears double-peaked … The dashed line labeled "wall" shows the transition between the nearby uniform population and the more distant clustered population. This transition distance decrease with increasing m9 and decreasing a9 and q9. The width of the cluster decreases with increasing m9." |
| the simulation's row | Table 2, p. 24 | `7 500 17 0.33 250 100 -175.4 -2.5 17500` (m9, a9, i9, e9, ϖ9, Ω9, ℓ, Δℓ, particles) |
| wall and width values | read from the figure, criteria section 2 (256 au; 124°–258°) | not in the text: drawn by eye in the figure, as the criteria say |

## Set B: m9 5, a9 300 au, i9 17°, e9 0.15, ϖ9 254°, Ω9 108° (the maximum-likelihood simulation)

| what | where | text |
|---|---|---|
| distribution a against Δϖ | Fig. 1, p. 5 | caption: "… the probability density of ϖ versus semimajor axis in the maximum likelihood model with m9 = 5 Me, a9 = 300 AU, e9 = 0.15 and i9 = 16◦ (red)"; Δϖ for "an assumed value of ϖ9 = 254◦" |
| pole positions | Fig. 2, p. 6 | caption: "… ∆Ω is the difference between the longitude of ascending node of the observed object and of the modeled Planet Nine, assumed to be 108◦ here … in the maximum likelihood model" |
| the parameters in the text | §4.3, p. 12 | "the model with the maximum likelihood, M9 = 5 M earth, a9 = 300 AU, i9 = 17◦, e9 = 0.15, ϖ9 = 254◦, and Ω9 = 108◦" |
| the simulation's row | Table 2, p. 22 | `5 300 17 0.15 254 108 -172.9 0.0 25600` |

## The inconsistencies of the paper (as in the criteria, section 1)

1. **i9 of the maximum-likelihood simulation:**
   - 16° in the caption of Fig. 1 (p. 5);
   - 17° in §4.3 (p. 12) and in Table 2 (p. 22).
   - 16 ± 5° is also the posterior inclination of the abstract (p. 1), which may be the source of the 16 in the
     caption.
   - The criteria follow Table 2 and §4.3, so set B uses 17°.
2. **Where the maximum lies:** the note to Table 2 (p. 25) says "the maximum value, which occurs at m9 = 5, a9 = 310,
   i9 = 15, and e9 = 0.10". The row with Δℓ = 0.0 is the simulation of p. 22 (5, 300, 17, 0.15).
3. **The time span:** §6 (p. 19) has "within the 200 Myr of our simulations", while §4.2 (p. 9) uses 4 Gyr: "The early
   times of the simulations contain a transient state that appears to reach something like a steady-state in
   orbital distribution after ∼1 Gyr. We thus discard these initial time steps and only include the final 3 Gyr in
   our analysis."

## The general statements used as checks (criteria section 1)

- **Cluster about 180° from Planet Nine's perihelion:** §1, p. 2 ("180 degrees removed from those of the
  cluster…"), and Figs. 1 and 3.
- **Mass narrows the cluster, and the wall moves inwards with larger m9 and smaller a9 and q9:** Fig. 3 caption,
  p. 10 (quoted above).
- **The simulations themselves** (§4.1, p. 8): "the 5 giant planets and test particles … mercury6", 16,800–64,900
  test particles with a 150–500 au, q 30–50 au, i 0–25°. The model check (tide, passing stars) is in
  `docs/production-result-20261110.md`.
