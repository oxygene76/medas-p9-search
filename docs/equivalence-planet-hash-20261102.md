# Equivalence test, group M: are the planets of the 16 MERCURIUS slices bit-identical? (2026-11-02)

**An additional check. It is not part of the evaluation**: that ran by `docs/equivalence-evaluation-procedure.md`
from c45833a, see `docs/equivalence-result-20261102/`. Asked for by the project lead on 2026-10-25, to be run once
entry 2 (manifest e2) was on the chain; that entry is #3 of 2026-11-02.

## Why

Group M runs each seed as 16 slices of 250 test particles with the same planets. `tools/equiv_eval.py` measures the
Δϖ of every slice against that slice's own Planet Nine and pools the slices.

With MERCURIUS a close encounter of a test particle with a planet is integrated with IAS15. If that changed a
planet, the slices of one seed would have slightly different planets. The pooled statistic would then mix 16
slightly different planetary systems.

In the exploratory night run M2 (`docs/night-20261024.md`) the planets stayed bit-identical. REBOUND 5.2.2
restores the massive bodies after encounters in which only test particles take part, and p9sim sets
`testparticle_type = 0`. This check repeats that on the real data of the equivalence test.

## How

- **Data:** `p9equiv-merc-47c7381/jobs/M-s<seed>-part00 … part15` from the appmdp-05 tarball
  (`1d6c1c0bb55f7fba24db5d118bcc65a31577b9dee6cc615df4eada1648629d3b`). All 10,423 files had been checked against
  the stamped list `c5f55d82…955d` before.
- **Tool:** `tools/planet_hash.py` at 9900cb5. That commit adds jobs of an equivalence package, with the snapshot
  times of `equiv_eval.py`.
- **Program:** p9sim of p9prod-9a084ed (`b14f7956…`), the same as for the runs and the evaluation.
- **What is compared:** at each of the 200 snapshots (1-200 Myr, one per Myr), the SHA-256 of the masses,
  positions and velocities as float64 of all massive bodies (Sun with the inner planets, Jupiter to Neptune,
  Planet Nine), per slice. Also the largest position difference between slices, per body.

## Result

| seed | slices | times | distinct hashes per time (max) | largest position difference | first time with differing planets |
|---|---|---|---|---|---|
| 101-109 (each) | 16 | 200 | 1 | 0 au (every body) | none |

- **All 9 seeds × 16 slices × 200 times have the same planets bit for bit.**
- Measuring Δϖ against each slice's own Planet Nine is therefore the same as against any slice's Planet Nine.
- The pooling in `equiv_eval.py` mixes no different planetary systems.

As in the night report, this holds for this configuration and REBOUND 5.2.2: no two massive bodies come close, and
REBOUND handles encounters that involve only test particles this way.

Outputs: `runs/equiv-planet-hash-20261102/` (not in git), `s<seed>.txt` and `s<seed>.json`, read-only. SHA-256 of
the JSON files:

```
aa3f90f2268a6ddc3eadacc20d7d217568677961b9f555a3b652038f7b69f468  s101.json
92e35286af5f5db365394ecc263282f41a7e576081bd98c2cdaa14a778429546  s102.json
46c245e9919a5ce47ddc0d66861f2a87bf712ed92ee0a9b44688c93683643a77  s103.json
2abf0a03a11a0671d26ba206f35b7fdc7422951917f29b66738b2a412c4ab0c5  s104.json
1211e180ead3f785ad02da89f9dd126e98be50713fe4939cec470dff2bdfc893  s105.json
44c4fb1ae6f8d3be68302a87fa8260b30adee58bcaaa35c54ce6a8809c891492  s106.json
5a4836da84019759ad67f5f74c9ee36841a99ca923e3cb495b742b9e61a6bb55  s107.json
470106a090a92553ccd4236d9679f8cf472f54a1799a1bb5bc975162f7f08997  s108.json
309d7b24cf0be8c789541799447dd65b03a1e042d24ffceb3d17a83626a76842  s109.json
```
