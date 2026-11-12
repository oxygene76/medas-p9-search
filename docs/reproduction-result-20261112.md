# Reproduction of stored segments: result (2026-11-12)

Point 3 of the A100 window (`docs/a100-window-proposal-20261106.md`, decision of 2026-11-06). Six finished segments
were computed again on the same card, from their stored inputs, with the run's own program. Only hashes were compared,
and nothing of the content was looked at. The files are in `docs/reproduction-result-20261112/`.

## Result

**6 of 6 segments give their stored result hash again.** Their flyby and removal logs are byte-identical as well.

| segment | stored run | result hash (recomputed = stored) | wall time |
|---|---|---|---|
| production run, segment 0 | p9prod-9a084ed | `082589539b0ca51a…17573889` | 10,278 s |
| production run, segment 19 | p9prod-9a084ed | `821484c5371cc083…f14aa447` | 4,076 s |
| production run, segment 39 | p9prod-9a084ed | `d41152221b3dfc9f…0527f1c3` | 3,221 s |
| V5 s110, segment 19 | p9long-v5-ac47329 | `04257cb0917431f0…401737d0` | 2,223 s |
| V5 s111, segment 19 | p9long-v5-ac47329 | `dc7bd906aceb44ae…0cd84d2a` | 2,193 s |
| V5 s112, segment 19 | p9long-v5-ac47329 | `2ecf9a06b08f7baa…18c89b4a` | 2,167 s |

The full hashes are in `REPRO.tsv`.
- Segment 39 is the last segment of the production run. Its hash, `d41152221b3dfc9f…0527f1c3`, is the one the evaluation and
  entry r1 name.

## How it was checked

1. **On the server** (`p9repro-d3c2363`, `repro.sh`), before each segment:
   - the stored input against `input_sha256` in its `DONE`;
   - the program against the sha256 of the production binary (`7666c5ba…`).

   After the segment, the recomputed result hash was compared with `DONE` and `segments.tsv`, and for information
   the flyby and removal logs.
2. **On the laptop, independently** (2026-11-12), the archive of the reproduction (sha256 `52642db9…d047`) against
   the result archives verified on 2026-11-09/10:
   - every recomputed hash equals the `DONE` file and the row of `segments.tsv` of the stored run;
   - every one of these `DONE` files equals its line in the checksum list timestamped with OpenTimestamps before the
     evaluations.

   So the reproduced hashes are tied to the state that the evaluations and entry r1 used.

## What it shows, and what not

- **It shows:** the runs are reproducible bit for bit on the hardware they ran on. The same stored input and the same
  binary give the same final states and the same logs again, days later and with other load on the machine. This
  includes segment 0 of the production run, which has the most close encounters.
- **It does not test another machine.** The package checks of the runs (`check.sh`, ALL SAME on the A100 and on the
  laptop GPU against known hashes) and `docs/reproducibility.md` cover that.
  - WHFast and p9gpu with its CPU twin are bit-identical on every platform tested.
  - MERCURIUS so far only with glibc on x86-64, because of the libm function `cbrt`, until the new p9sim binary.
- **No MERCURIUS segment was recomputed here.** A segment of the long runs (one slice, segment 5) was recomputed on
  the laptop on 2026-11-05 and gave the server's hash.

## For the data package and the research note

- **Data package e6:** `checks.tar` of the records `production` and `long-110-112` takes `REPRO.tsv`, `VERDICT.txt`,
  the six `result.txt` and `environment.txt`, and the README names the result.
- **Research note:** section 11 states it as above.
