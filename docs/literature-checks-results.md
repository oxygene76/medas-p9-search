# Results of the literature checks (2026-10-23)

Criteria: `docs/literature-checks.md` (7554880, written before the runs). Runs and outputs: `runs/litcheck`
(`frequencies.txt`, `frequencies.json`, `obl-*/eval.txt`). All runs complete; relative energy errors below 6e-7
(model C: 2e-9).

## 1. Fundamental frequencies g5–g8, s6–s8 (over 50 Myr; relative to La2004)

| | La2004 ("/yr) | A (giants, inner planets in the Sun) | B (A plus Planet Nine) | C (all eight planets) |
|---|---|---|---|---|
| g5 | 4.257452 | −3.23e-3 | −3.23e-3 | −1.28e-4 |
| g6 | 28.2450 | −5.06e-4 | −5.06e-4 | +9.0e-6 |
| g7 | 3.087951 | −2.24e-5 | −1.40e-5 | −7.2e-6 |
| g8 | 0.673021 | +2.03e-4 | +2.78e-4 | −2.6e-6 |
| s6 | −26.347855 | −3.12e-4 | −3.12e-4 | +4.0e-7 |
| s7 | −2.9925259 | +3.28e-4 | +3.37e-4 | +1.01e-5 |
| s8 | −0.691736 | +3.57e-4 | +4.24e-4 | +6.6e-5 |

Against the expectations fixed before the runs:
- (a) p9gpu against WHFast (A, B): at most 4e-9 relative (expected ≤ 1e-6): **met**.
- (b) A against La2004: at most 3.2e-3 (g5), the others at most 5.1e-4 (expected ≤ 5e-3): **met**.
- (c) C against La2004: at most 1.3e-4 (expected ≤ 1e-3): **met**. The inner planets as separate bodies (and
  the smaller step) explain nearly all of A's difference: g5 from −3.2e-3 to −1.3e-4, g6, s6 and g8 to below
  1e-5. What remains is of the size of the model differences (general relativity, the Moon, Pluto) and of
  La2004–La2010a.
- (d) Planet Nine (B − A): g8 +7.6e-5, s8 +6.7e-5, g7 and s7 +8.6e-6, g5, g6, s6 ≤ 1.4e-6; the outer
  planets' frequencies shift by a few times Laskar's Δ100.

For the production runs (model A, dt 0.5 yr): the giants' secular frequencies are within 3.2e-3 of La2004, almost
all of it from merging the inner planets into the Sun, a known and intended simplification.

## 2. Solar obliquity, the cases of Bailey, Batygin & Brown (2016) (fixed solar axis, after 4.5 Gyr)

| Planet Nine | N-body (p9gpu) | secular (Lai 2016) | Lai's formula | N-body vs secular |
|---|---|---|---|---|
| 15 M_E, 500 au, e 0.5, i 10° | 3.07° | 3.20° | 3.20° | −4.2 % |
| 15 M_E, 500 au, e 0.5, i 20° | 5.86° | 6.12° | 6.12° | −4.3 % |
| 15 M_E, 500 au, e 0.5, i 30° | 8.09° | 8.45° | 8.45° | −4.3 % |
| 10 M_E, 700 au, e 0.6, i 30° | 2.66° | 2.86° | 2.86° | −7.3 % |

All within the 10 % fixed before the runs: **met**. The i = 20° case gives the same result hash as the run of
2026-10-23 03:18 (`docs/solar-obliquity.md`).

Against Bailey, Batygin & Brown (reported, not judged; their solar axis precesses and spins down): their Fig. 4
(15 M_E, 500 au, e 0.5) gives the smallest primordial misalignment for i9 = 20°; here i9 = 20° turns an aligned start
into 5.9°, close to the observed 6°, while i9 = 10° gives 3.1° and 30° gives 8.1°, the same ordering. For the case of
Batygin & Brown (2016) they find 3–5°; with a fixed axis 2.7° here.
