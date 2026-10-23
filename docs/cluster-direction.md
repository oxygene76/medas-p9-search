# Direction of the apsidal clustering over time

Question: do the distant particles move towards anti-alignment with Planet Nine
(mean Δϖ = ϖ − ϖ_P9 near 180°) as time goes on, or does the direction depend on the
selection?

Tool: `tools/cluster_direction.py` (barycentric elements as in `tools/analyze.py`;
n, R and circular mean of Δϖ; Rayleigh p). Run script and output:
`runs/cluster-direction/` (not in git). All runs use the Brown & Batygin (2021) case
with seed 9 (`tools/make_ic.py`), dt = 0.5 yr.

## Runs and removal rules

| run | integrator | members | to | removal |
|---|---|---|---|---|
| M5, M6 (`runs/cause/ensmerc/`) | REBOUND MERCURIUS | 5, 6 | 200 Myr | r < 5 au, r > 10,000 au |
| M0 (`runs/val/merc`, `merc2`), M1 (`runs/val/ens-merc`) | REBOUND MERCURIUS | 0, 4 | 200 Myr | as M5 |
| V5 (`runs/val/ens-gpu`) | p9gpu v5 (`smooth`) | 0–3 | 200 Myr | as M5, plus collisions (physical radii) |
| FIX (`runs/cause/ensfix/m123`) | p9gpu fixed step (`step`, `--no-removal`) | 1–3 | 200 Myr | as M5; encounters counted, not removed |
| L (`runs/long-20261018`, first long run) | REBOUND WHFast | 4,000 particles, 16 chains | 360 Myr (all chains), 420 Myr (4 chains) | r < 5 au, r > 10,000 au, every 1,000 steps; no treatment of close encounters |

Members of the 2,000-particle ensembles: the web page shows M5, V5 member 0 and FIX member 1.

## Result

Selections:

- S1: a ≥ 250 au.
- S2: a ≥ 250 au and q > 30 au.
- S3: a > 230 au and q > 30 au (Brown & Batygin 2019).
- For reference, S4: a > 230 au and q > 42 au (`tools/analyze.py`).

Values are the mean Δϖ in degrees, with R in brackets.

| run | t | S1 | S2 | S3 | S4 |
|---|---|---|---|---|---|
| M5 | 50 Myr | 261 (0.15) | 266 (0.33) | 268 (0.33) | 283 (0.63) |
| M5 | 100 Myr | 257 (0.32) | 262 (0.57) | 263 (0.55) | 272 (0.70) |
| M5 | 150 Myr | 250 (0.45) | 253 (0.64) | 254 (0.61) | 259 (0.67) |
| M5 | 200 Myr | 238 (0.48) | 240 (0.59) | 240 (0.56) | 242 (0.59) |
| V5/0 | 200 Myr | 238 (0.45) | 240 (0.57) | 241 (0.52) | 243 (0.55) |
| FIX/1 | 200 Myr | 240 (0.51) | 242 (0.61) | 242 (0.56) | 243 (0.59) |
| L | 100 Myr | 263 (0.36) | 265 (0.58) | 266 (0.56) | 272 (0.71) |
| L | 200 Myr | 239 (0.48) | 241 (0.59) | 241 (0.56) | 242 (0.60) |
| L | 300 Myr | 198 (0.35) | 201 (0.39) | 199 (0.37) | 200 (0.38) |
| L | 360 Myr | 171 (0.33) | 175 (0.35) | 175 (0.34) | 176 (0.35) |
| L, 4 chains | 360 Myr | 179 (0.29) | 185 (0.31) | 183 (0.30) | 185 (0.31) |
| L, 4 chains | 420 Myr | 162 (0.31) | 168 (0.31) | 164 (0.31) | 166 (0.32) |

At 200 Myr the 11 members of the 200-Myr runs lie within 5° of each other for each selection: S1 235.6–240.5°, S2 238.9–242.0°, S3 239.3–242.4°, S4 241.2–244.7°.
From 30 Myr on, every value in the table has a Rayleigh p below 0.01.

## Interpretation

1. **The direction changes with time; the selection hardly matters.**
   - The direction moves steadily away from about 265° (20–50 Myr) towards smaller values:
     - about 0.25° per Myr between 100 and 200 Myr;
     - about 0.4° per Myr between 200 and 360 Myr.
   - The four selections differ by at most 10° (S4 early on) and by at most 4° from 200 Myr on.
   - Integrator (MERCURIUS, v5, fixed step, WHFast without encounter treatment) and member change the value by at most ±3°.
2. **180° is passed, not reached and held.**
   - In the long run the mean passes 180° at about 340–350 Myr and keeps decreasing: 162–168° at 420 Myr.
   - The 4 chains that reached 420 Myr show the same thing alone: 185° → 168° (S2).
   - The concentration does not grow during this drift. R peaks at about 0.64 (S2, 140–160 Myr) and falls to about 0.35 by 360 Myr.
   - So 420 Myr shows no stable anti-aligned cluster. The "176° at 360 Myr" in `docs/pilot-run-2026-10-18.md` is a moment on this drift.
3. **Limits.**
   - Brown & Batygin compare after 4 Gyr. Whether the drift ends in libration about 180° cannot be decided from 420 Myr.
   - The long run removes nothing at planet encounters, and WHFast does not resolve them. Its agreement with MERCURIUS up to 200 Myr (241° against 240°, S2) suggests that the direction does not depend on that choice.
