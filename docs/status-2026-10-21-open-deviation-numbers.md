# Addendum 2026-10-21 to the status note: single runs and means

This addendum is a new file. It changes neither
`docs/status-2026-10-21-open-deviation.md` nor the documents it refers to; it
states for each R(Δϖ) value named there whether it belongs to a single run or
is a mean.

R(Δϖ) of the distant test particles (a > 230 au, q > 42 au) at 200 Myr
(`docs/validation-smooth-200myr.md`, `docs/validation-ensemble-200myr.md`,
`runs/val/eval-ensemble.json`):

- **0.545 against 0.608** (the status note's first point): two single runs,
  both member 0 of the 2,000 test particles: the p9gpu run
  `gpu-2000-smooth` (smooth transition of 47127ba, 0.5451) against the
  MERCURIUS run M0 (`merc` + `merc2`, 0.6083).
- **Ensemble, single runs**: p9gpu v5 (79c16e2) G0 0.5449 (member 0, the
  repetition of `gpu-2000-smooth`), G1 0.5746, G2 0.5744, G3 0.5806;
  MERCURIUS M0 0.6083, M1 0.6095.
- **Ensemble, means**: m_G = 0.569 (G0–G3), m_M = 0.609 (M0–M1),
  m_G − m_M = −0.040 against the limit 2 s = 0.028. The ensemble's criterion
  compares these means; it fails.

So 0.545 is a single run (the lowest of the four p9gpu runs at 200 Myr), and
0.569 is the mean of the four. The finding of the status note is unchanged:
the deviation is open and not explained.
