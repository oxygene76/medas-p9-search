# Set B of the comparison with Brown & Batygin 2021, 4 Gyr: result (2026-11-17)

**Status addendum of 2026-11-22** (the text below is unchanged as entered):
- Entered with entry r2 (#12) on 2026-11-21.
- Contrary to the status line below, it was not reviewed independently before the entry.
- On 2026-11-22, after the entry, an AI session (p9-review-82) read this report independently and compared it with the result files; it found no computing error. The limitations it found are taken up in the research note (`docs/research-note.md`) and on the result pages of the website.

**Status:** result report, for independent review. The verdict is not final before that review. Nothing goes into the
research note, onto the website or into a notary entry before it.
- **Criteria:** `docs/bb2021-comparison-criteria.md` sections 4–6, as entered with entries e3 and e4, with the release
  of set B by its paired test (entry e5; `docs/paired-result-B-20261113.md`).
- **Steps:** `docs/sets-evaluation-procedure.md` (12ab70b, fixed and timestamped before any look at either run).
- **Files:** `docs/sets-result-B-20261117/` as the tool wrote them (commit 28bfcc6).
- **The outcome over both sets** (section 6 of the criteria): `docs/sets-outcome-20261117.md`.

## Verdict

**Does not agree with B&B** (criteria section 5). Set B agrees only if M1, M2 and M3 are within tolerance; M4 is judged
for set A only. One of the three is outside:

| measure | B&B | tolerance | set B | |
|---|---|---|---|---|
| M1 direction of the Δϖ cluster, pooled | 180° | 160–200° | 166.7° | within |
| M1 per subset (4) | | 160–200° each | 166.6°, 166.6°, 166.7°, 167.1° | all within |
| M2 strength, mean R | cluster clearly present | ≥ 0.20 | 0.127 | outside |
| M3 pole, ψ | ≈ 0° | within ±30° | 18.0° | within |

- **Decided, not "not decided":** The scatter of M1 over the 4 subsets is 0.4°, below the limit of 10°.
- **The run is complete to 4 Gyr:** 301 snapshots in the window 1–4 Gyr, the last at 4 Gyr.
- The tool states it as `does not agree: M2 0.1273 < 0.2` (`report.txt`).

## Information (reported, not deciding)

- **M4, wall:** 185 au (not judged for set B).
- **M5, width at 850–950 au:** 152° (from 99.5° to 250.5°).
- **Variants:** ecliptic frame M1 167.0°, ψ 20.1°; heliocentric elements M1 166.7°, ψ 18.0°.
- **The time series** of M1–M3 are in `timeseries.csv`. They were not used for the verdict.

## The run

- **Package:** `p9bbsets-5b05cc3`, job `BB-B` (seed 312), 64,000 test particles, 0–4 Gyr in 40 segments of 100 Myr.
- **Where:** on the A100, p9gpu v5 (sha256 `7666c5ba…566f`), CPUs 16–31, at each of its two starts.
- **When:** from 2026-11-14 16:00:44Z to 2026-11-16 21:24:06Z.
- **End:** seg039 to 4,000 Myr, 20,723 test particles left, result `fec7ed63…9c62`.

**Pause of 2026-11-15, from 15:42:39Z to 16:11:48Z:**
- **Reason:** an uncorrectable memory error on the other card of the server, the L40S (Xid 48, 63, 154), not on the
  A100. That card could only be reset after p9gpu on the A100 had stopped.
- **Where it stopped:** at the segment boundary after segment 11. Segment 12 had run for 6 s and was computed again from
  its start, from the same input. No result was lost.
- **Restart:** with the same package 5b05cc3 and the same p9gpu checksum, and the package check before it was ALL SAME
  (16:12:57Z).
- **The A100:** 0 uncorrectable ECC errors, volatile and aggregate, before and after the reset of the L40S.
- **Driver state at the restart:** For the reset, `nvidia-persistenced` was stopped and `nvidia_drm`/`nvidia_modeset`
  were unloaded. The modules were loaded again at 16:07:59Z (driver 580.178.04), and `nvidia-persistenced` ran again
  from 16:08:01Z. At the restart (16:11:48Z) the driver state was thus restored.
- **The job list at the restart** was "BB-A BB-B" instead of "BB-B" alone. `run-job.sh BB-A` skipped the 40 done
  segments of set A and wrote nothing (report of set A); then set B went on.

**Another process during set B:** the project lead's own service docling-serve (pid 2386348), started on 2026-11-15 at
16:08:02Z and still running at the end of set B.
- It ran during segments 12 to 39, on the L40S, with a CPU affinity of 0–31, so also on set B's CPUs 16–31.
- **Effect:** it can lengthen wall times; it cannot change the bits. p9gpu computes deterministically, as the segment
  chain and the package check show.

## Checks before the evaluation

- **Archive and list:** sha256 equal to the server's. The archive was backed up encrypted at three places and
  restore-checked by the project lead on 2026-11-17. The list was timestamped with OpenTimestamps before the evaluation.
- **`sha256sum -c`:** 535 of 535 OK, as many files as lines.
- **Segment hashes against their DONE files:** 80 of 80, on the server.
- **Package files:** equal to `p9bbsets-5b05cc3.tar.gz` (e4), apart from the run outputs and the job of set A, which the
  procedure excludes. Equal to those in the archive of set A.
- **Release file:** `v2/BB-B.ok` is the file of the paired test (`18de161a…aae1`).
- **Segment chains:** `tools/check_segments.py` (= 31ed973) gave 0 failures and 40 of 40 segments. `segments.tsv` has
  exactly one row for segment 12.
- **Package checks:** `check/report.txt` in the archive is the check of the restart of 2026-11-15, ALL SAME.

> **Deviation from the wording of the procedure** (section 2): The list and the archive of set B also hold
> `check-report-vor-reset-20261115T1525Z.txt`. That is the package check of set B's start on 2026-11-14 (ALL SAME),
> copied before the restart overwrote `check/report.txt`.
> - The procedure's commands do not name this file. It was added so that the check of set B's start is kept.
> - It has no effect on the criteria or the evaluation.

- **libc6** was held on the server throughout the run (2.35-0ubuntu3.15).

All values are in `environment.txt` and in the private record of the pause.

## What follows

The verdict on set B alone decides nothing about the consequences. Those follow from section 6 of the criteria over both
sets: `docs/sets-outcome-20261117.md`.
