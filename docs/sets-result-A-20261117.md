# Set A of the comparison with Brown & Batygin 2021, 4 Gyr: result (2026-11-17)

**Status addendum of 2026-11-22** (the text below is unchanged as entered):
- Entered with entry r2 (#12) on 2026-11-21.
- Contrary to the status line below, it was not reviewed independently before the entry.
- On 2026-11-22, after the entry, an AI session (p9-review-82) read this report independently and compared it with the result files; it found no computing error. The limitations it found are taken up in the research note (`docs/research-note.md`) and on the result pages of the website.
- The count "three of the four" measures outside counts M4 as the criteria do. The research note and the result pages treat the inner edge as no separate miss: with a strength this weak it follows from the strength (`docs/code-review-20261121.md`, point C3).

**Status:** result report, for independent review. The verdict is not final before that review. Nothing goes into the
research note, onto the website or into a notary entry before it.
- **Criteria:** `docs/bb2021-comparison-criteria.md` sections 4–6, as entered with entries e3 and e4, with the release
  of set A by its paired test (entry e5; `docs/paired-result-A-20261112.md`).
- **Steps:** `docs/sets-evaluation-procedure.md` (12ab70b, fixed and timestamped before any look at either run).
- **Files:** `docs/sets-result-A-20261117/` as the tool wrote them (commit 28bfcc6).
- **The outcome over both sets** (section 6 of the criteria): `docs/sets-outcome-20261117.md`.

## Verdict

**Does not agree with B&B** (criteria section 5). Set A agrees only if M1, M2, M3 and M4 are within tolerance. Three of
the four are outside:

| measure | B&B | tolerance | set A | |
|---|---|---|---|---|
| M1 direction of the Δϖ cluster, pooled | 180° | 160–200° | 127.3° | outside |
| M1 per subset (4) | | 160–200° each | 133.8°, 124.7°, 123.2°, 126.5° | all outside |
| M2 strength, mean R | cluster clearly present | ≥ 0.20 | 0.050 | outside |
| M3 pole, ψ | ≈ 0° | within ±30° | 3.2° | within |
| M4 wall | 256 au | 226–286 au | 165 au | outside |

- **Decided, not "not decided":** The scatter of M1 over the 4 subsets is 6.5°, below the limit of 10°. No subset was
  reported as deviating.
- **The run is complete to 4 Gyr:** 301 snapshots in the window 1–4 Gyr, the last at 4 Gyr.
- The tool states it as `does not agree: M1 pooled 127.3 outside 160-200; M1 subset 0 … 3 outside 160-200; M2
  0.0496 < 0.2; M4 165.0 outside 226-286 au` (`report.txt`).

## Information (reported, not deciding)

- **M5, width at 850–950 au:** 203° (from 40.5° to 242.5°). B&B mark 134° for this panel; the criteria judge M5 not,
  because the paper does not define where a bar ends.
- **Variants:** ecliptic frame M1 127.9°, ψ 7.5°; heliocentric elements M1 127.3°, ψ 3.1°. Neither changes the
  picture.
- **The time series** of M1–M3 per snapshot are in `timeseries.csv`. They were not used for the verdict.

## The run

- **Package:** `p9bbsets-5b05cc3`, job `BB-A` (seed 311), 64,000 test particles, 0–4 Gyr in 40 segments of 100 Myr.
- **Where:** on the A100, p9gpu v5 (sha256 `7666c5ba…`), CPUs 16–31.
- **When:** from 2026-11-12 09:08:14Z to 2026-11-14 15:57:46Z, without interruption.
- **End:** seg039 to 4,000 Myr, 17,616 test particles left, result `e9e711fb…81fe`.

## Checks before the evaluation

- **Archive and list:** sha256 equal to the server's. The archive was backed up encrypted at three places and
  restore-checked by the project lead on 2026-11-17. The list was timestamped with OpenTimestamps before the evaluation.
- **`sha256sum -c`:** 534 of 534 OK, as many files as lines.
- **Segment hashes against their DONE files:** 80 of 80, on the server.
- **Package files:** equal to `p9bbsets-5b05cc3.tar.gz` (e4), apart from the run outputs and the job of set B, which the
  procedure excludes.
- **Release file:** `v2/BB-A.ok` is the file of the paired test (`09c1771a…89c6`).
- **Segment chains:** `tools/check_segments.py` (= 31ed973) gave 0 failures and 40 of 40 segments.
- **Package check, a note:**
  - `check/report.txt` in the archive of set A is the check of the restart of 2026-11-15 (ALL SAME). The archive was
    made on 2026-11-17, and each start of the package writes that file again.
  - The check of set A's own start on 2026-11-12 survives only as the line `check: ALL SAME` (09:09:24Z) in
    `run.log`.
- **The restart of 2026-11-15** for set B ran with the job list "BB-A BB-B". `run-job.sh BB-A` skipped all 40 done
  segments and wrote nothing. No file of `jobs/BB-A` in the archive is newer than 2026-11-14 15:57:46Z (325 files).
- **libc6** was held on the server from 2026-11-12 08:05 UTC throughout the run (2.35-0ubuntu3.15).

All values are in `environment.txt`.

## What follows

The verdict on set A alone decides nothing about the consequences. Those follow from section 6 of the criteria over both
sets: `docs/sets-outcome-20261117.md`.
