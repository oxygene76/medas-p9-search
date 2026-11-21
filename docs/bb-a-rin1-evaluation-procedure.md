# Run BB-A-rin1: the procedure of its evaluation (2026-11-20, before the run ends)

Fixed, committed and stamped with OpenTimestamps while the run is still computing, before any of its results beyond
the counters of segments 0–5 is known. As `docs/sets-evaluation-procedure.md` (12ab70b) did for sets A and B.

**Basis:**
- **Criteria:** `docs/bb-a-rin1-criteria.md` (f80681f), entered as e6, entry #9 (2026-11-18 16:12:49 UTC,
  block 10942017).
- **Package:** `p9rin-0b8971f` (sha256 `a4441456e4c6571702236d715c96e7d45e4e4cdd7dd36d23297918e70cc85e42`), job
  `BB-A-rin1`, 40 segments.
- **Known so far:**
  - the early check after segment 0 (passed);
  - the counters of segments 0–5 (COUNTERS OK);
  - the run times;
  - no measure of section 3 of the criteria.

**Changed against the criteria:** the purely informative look after 2 Gyr (criteria, section 5) is not made
(decision of the project lead, 2026-11-20). It had no consequence for the run or the outcome. Nothing else is changed.

## 1. On the GPU server, after the end (read only)

The end is the line "BB-A-rin1 complete: 40 segments" in `run.log`; `status.sh` shows 40 of 40.
```sh
cd ~/runs/rin1 && T=$(date -u +%Y%m%dT%H%MZ)
cp p9rin-0b8971f/run.log rin1-run-$T.log
nice -n 19 ionice -c 3 sh -c "find p9rin-0b8971f rin1-run-$T.log -type f ! -name '*.pid' \
    ! -path p9rin-0b8971f/run.log ! -path p9rin-0b8971f/run.out ! -path 'p9rin-0b8971f/.rin-watch/*' -print0 \
  | LC_ALL=C sort -z | xargs -0 sha256sum" > ~/runs/rin1-results-sha256-$T.txt \
  && wc -l ~/runs/rin1-results-sha256-$T.txt && sha256sum ~/runs/rin1-results-sha256-$T.txt
nice -n 19 ionice -c 3 tar -czf ~/runs/rin1-p9rin-0b8971f.tar.gz --exclude='*.pid' --exclude='p9rin-0b8971f/run.log' \
  --exclude='p9rin-0b8971f/run.out' --exclude='p9rin-0b8971f/.rin-watch' p9rin-0b8971f rin1-run-$T.log \
  && sha256sum ~/runs/rin1-p9rin-0b8971f.tar.gz
```
- The project lead reports the number of lines and the sha256 of the list, and the sha256 of the archive.
- List and archive hold the same files.

## 2. On the laptop: checks, backup, timestamp (before any evaluation)

1. **Archive and list:**
   - the sha256 of the archive equals the reported one;
   - the archive is unpacked into a new, empty directory;
   - `sha256sum -c` of the list there gives every line OK, and the number of files equals the number of lines.
2. **Package files:** unchanged against `p9rin-0b8971f.tar.gz`, apart from the outputs of the run.
3. **Package check:** `check/report.txt` shows ALL SAME, 40 cases.
4. **Segments:** `tools/check_segments.py --p9sim PKG/bin/p9sim --jobs RUN`. Expected: 0 failures, 40 of 40 segments.
5. **Early check and counters:** `early-check.sh` and the counter block of the start guide, run on the unpacked
   archive. They must give the same as during the run: EARLY CHECK PASSED, COUNTERS OK for segments 0–5.
6. **Backup** of the archive, by the project lead:
   - `runs/notary/notary-archive-backup.sh`, name `rin1`, to `~/backups`, OneDrive and the second target;
   - then `runs/notary/notary-restore-check.sh` on one copy.
7. **Timestamp:** the list is copied unchanged to `runs/notary/rin1-results/` and stamped with OpenTimestamps; only its
   hash leaves the laptop.

If one of 1–5 fails, nothing is evaluated, and the failure is reported.

## 3. The evaluation

**From what:**
- **Checkout:** a clean, detached checkout of medas-p9-search at the commit of this file (`git status` empty).
  - `tools/prod_eval.py` is byte-identical to `prod-eval-v1`: sha256
    `1ebb2d45c47ea0bb465b67f95d1d9b3a766678b4230fc89cad7d01c4b2c65cbb`.
  - `tools/sets_decompose.py` as in 2d10dae, `tools/sets_subset_spread.py` as in 4eec855.
  - Check: `git diff --stat prod-eval-v1 HEAD -- tools/prod_eval.py tools/analyze.py`,
    `git diff --stat 2d10dae HEAD -- tools/sets_decompose.py` and `git diff --stat 4eec855 HEAD --
    tools/sets_subset_spread.py` are empty.
- **Program:** `bin/p9sim` of the unpacked package, checked against `bin/SHA256-p9sim`.
- **Observed objects:** `docs/bb2021-observed-table1.tsv`.
- **Names:** RUN is the unpacked `p9rin-0b8971f/jobs/BB-A-rin1`, PKG the unpacked package directory, OUT a new
  directory. Relative paths throughout, so that no local path enters the outputs.

**The measures** (criteria, section 3):
1. **M1–M5:**
   ```sh
   ../medas-p9-search/build/venv/bin/python -I tools/prod_eval.py RUN --out OUT/eval --p9sim PKG/bin/p9sim \
     --criteria bb2021-A --window 1e9 4e9 --t-end 4e9 --n-tp 64000 --subsets 4 --observed docs/bb2021-observed-table1.tsv
   ```
2. **R per 10 au beyond the wall, 260–700 au, all of S_BB:**
   ```sh
   ../medas-p9-search/build/venv/bin/python -I tools/sets_decompose.py RUN --p9sim PKG/bin/p9sim --wall 256 --out OUT/decomp --name A
   ```
   The value is `OUT/decomp/summary.json` → `means_beyond_wall.S_BB.mean_R` (set A: 0.0974).
3. **The inclination shares** (< 30°, 30–40°, 40–50°, 50–70°, normalised to 0–70°; retrograde of all), for q > 42 au
   and for 42 ≤ q ≤ 100 au, and M2 per subset:
   ```sh
   ../medas-p9-search/build/venv/bin/python -I tools/sets_subset_spread.py RUN --p9sim PKG/bin/p9sim --subsets 4 --n-tp 64000 > OUT/spread.json
   ```
   The values are `OUT/spread.json` → `all` → `inc_q>42`, `inc_q42-100`, `M2`.
4. **Survivors** at 1, 2, 3 and 4 Gyr:
   - all: `OUT/eval/result.json` → `survivors`;
   - in S_BB beyond the wall: `OUT/decomp/survival.csv`.
5. **Removals per segment:** `removed_r_in`, `removed_r_out`, `removed_collision` from each `result.txt`.
   - Segments 0–5: compared with BB-A, split by kind, as in section 3, point 5 of the criteria.
   - Segments 6–39: the sum per segment compared with BB-A, through N_end in `segments.tsv` of both runs.
   - Reported, not judged.

**The outcome** (criteria, section 4), against set A: M2 0.050; shares at q > 42 au 0.622 / 0.134 / 0.095 / 0.149,
retrograde 0.171; at 42 ≤ q ≤ 100 au 0.794 / 0.109 / 0.045 / 0.053, retrograde 0.069.
- **"The removal rule is the cause":** M2 ≥ 0.20 and the pooled M1 within 160–200°.
- **"The removal rule is not the cause":** M2 and all inclination shares of both selections within the tolerance band
  around set A: M2 ± 0.012, each share ± 0.008, retrograde ± 0.022 (q > 42 au) and ± 0.011 (42 ≤ q ≤ 100 au).
- **"Unclear":** everything else, reported as section 4 fixes:
  - how far the run moves from set A towards the comparison values, as a share of the distance;
  - R beyond the wall against 0.10 (set A) and 0.61 (Fig. 3, third panel);
  - the share below 30° at q > 42 au against 0.62 (set A) and 0.92–0.94 (Fig. 4, i9 = 15°);
  - the direction of the change.
- **The prediction** of section 1 (most likely "not the cause") is set against the outcome, with no further
  consequence.

**Afterwards:**
- **Report:** `docs/bb-a-rin1-result-<date>.md`, with the files of the tools as written, committed and stamped.
- **Review:** an independent review.
- **Entry:** only then, with the project lead's go, the entry r3: `result`, referring to entry #9.

## Addendum 1 (2026-11-21): what was known before the evaluation, and the comparison of the segment hashes

Written after step 2 and before any part of step 3. Decided by the project lead on 2026-11-21. Nothing of section 3 is
changed.

**What was known before the evaluation, and from where:**
1. **During the run,** as section "Basis" above:
   - the early check after segment 0 (passed);
   - the counters of segments 0–5 with N_end of these segments (COUNTERS OK, 2026-11-19);
   - the run times.
   - The Telegram messages of `rin-watch.sh` reported N_end and the run time of each finished segment to the project
     lead. They were not passed on for comparison; this addendum does not use them.
2. **In step 2, check 4,** on 2026-11-21:
   - The project lead ran `tools/check_segments.py --p9sim PKG/bin/p9sim --jobs RUN` on the unpacked archive (list
     `rin1-results-sha256-20261121T0912Z.txt`, archive `cc1891bd…0b0a`).
   - He reported its line `BB-A-rin1: ok; last row N 17622, result e9e711fb…81fe`, that is N and the result hash of
     the last row of `segments.tsv` (segment 39, 4 Gyr).
   - On 2026-11-21, at about 12:20 UTC, this was compared with the line of the segment check of set A of 2026-11-17
     (`runs/notary/sets-results/check_segments-setsA-20261117.txt`):
     `BB-A: ok; last row N 17622, result e9e711fbb683b41e02c939535bf421bb11e7b4ee857b38366a6203b97cab81fe`.
   - **Both N (17,622 bodies: 17,616 test particles and 6 massive bodies) and the result hash of segment 39 are the
     same.** At 4 Gyr the two runs are therefore bit for bit the same.
   - Nothing else of the output of BB-A-rin1 was looked at: no other row of its `segments.tsv`, no snapshot, no
     measure.

**The comparison added by this addendum** (step 3, before the measures; reported, not judged):
- **Per segment 0–39:** N_end and the result hash of the row of `jobs/BB-A-rin1/segments.tsv` (unpacked archive of
  step 2), against the same row of `jobs/BB-A/segments.tsv` (the checked archive of set A, list
  `setsA-results-sha256-20261117T1515Z.txt`).
- **Reported:**
  - the table of both columns, side by side;
  - the first segment from which the hashes are the same;
  - whether all later ones are the same as well;
  - the segments with different N_end.
- **Command,** from the clean checkout of section 3, with RUN as there and A the unpacked
  `p9bbsets-5b05cc3/jobs/BB-A` of set A:
  ```sh
  join -t "$(printf '\t')" -j 1 <(cut -f1,3,5 RUN/segments.tsv) <(cut -f1,3,5 A/segments.tsv) > OUT/segments-compare.tsv
  awk -F'\t' '{ s = ($3 == $5) ? "same" : "different"; print $1, $2, $4, s }' OUT/segments-compare.tsv
  ```
- **What it can say:**
  - From the first segment with the same hash on, the two runs hold the same particles in the same states.
  - Every snapshot in such segments is the same in both runs.
  - The measures of section 3 then differ only through the snapshots before it.
- **The outcome stays as section 3 fixes it,** from the measures.
