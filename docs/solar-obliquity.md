# Solar obliquity from Planet Nine (additional evaluation, 2026-10-23)

Independent of the running equivalence test and of its criteria.

`tools/solar_obliquity.py`: secular model of Lai (2016, arXiv:1608.01421,
eqs. 1–5): the planets as one plane, Planet Nine's orbit outside
(quadrupole, orbit-averaged), both precessing about the total angular
momentum; the solar spin axis fixed and parallel to the planets' plane at the
start; the obliquity after 4.5 Gyr.

## Check against the literature (`solar_obliquity.py check`: ALL OK)

- Lai's normalisations: L = 1.625 L_J (Lai 1.624), L_p = 0.276 L_J for
  10 M_E at a~ = 400 au, 2π/Ω_L = 87.8 Gyr (Lai 87.5), Ω_L/Ω_Jp = 2.725 (2.74).
- The integration agrees with the exact rigid precession to 1e-9 deg, and
  Lai's small-angle formula (eqs. 12–16) with it to 0.1 %.
- Orbits from Lai's eqs. 17–18 (fixed spin, 6°, ΔΩ = 45°) give 5.99° and
  ΔΩ = 45.0° after 4.5 Gyr.
- Bailey, Batygin & Brown (2016, arXiv:1607.03963; their solar axis precesses
  and spins down, so only for comparison): 15 M_E, 500 au, e 0.5, i 20° gives
  6.1° (theirs: about 6° today, Fig. 4); 10 M_E, 700 au, e 0.6, i 30° gives
  2.9° (theirs: 3–5°).

## N-body cross-check

p9gpu (the binary of p9prod-9a084ed, CPU twin) with only Jupiter–Neptune and
Planet Nine (the Sun carrying the inner planets), dt 0.5 yr, backward over
4.5 Gyr (a forward run of the state with all velocities reversed;
`runs/obliquity`, about 65 min per candidate, relative energy error below
5e-7); obliquity = angle of the giants' total angular momentum against its
direction at the start. Planet Nine's inclination is relative to the giants'
plane.

| Planet Nine | secular | N-body | difference |
|---|---|---|---|
| 6.2 M_E, 380 au, e 0.21, i 16° (Brown & Batygin 2021, the production run's) | 2.79° | 2.75° | −1.4 % |
| 15 M_E, 500 au, e 0.5, i 20° (Bailey et al. 2016, Fig. 4) | 6.12° | 5.86° | −4.3 % |
| 10 M_E, 700 au, e 0.6, i 30° (Batygin & Brown 2016) | 2.86° | 2.66° | −7.3 % |

The N-body values lie a few per cent below the secular ones, growing with
a_p; Planet Nine's osculating a in the N-body runs lies a few au to 20 au above
its start (380 → about 385, 500 → up to 520, 700 → about 710), which slows the
precession (Ω_L ∝ a~^-3), and the quadrupole truncation drops the higher
orders. For the comparison with the observed 6° this is small.

## Result

With a fixed solar axis, the Planet Nine of the production run (Brown &
Batygin 2021) tilts the planets' plane by about 2.8° in 4.5 Gyr, about half
of the observed 6°; more massive or more inclined orbits reach 6° (e.g.
15 M_E, 500 au, e 0.5, i 20°).
