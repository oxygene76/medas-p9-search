# Run BB-A2: the procedure of its evaluation (2026-11-21, before the run ends)

Fixed, committed and stamped with OpenTimestamps while the run is computing (started 2026-11-21T12:48:16Z), before any
of its results is known. As `docs/bb-a-rin1-evaluation-procedure.md` for BB-A-rin1.

**Basis:**
- **Criteria:** `docs/bb-a2-criteria.md` (0003408), entered as e9, entry #10 (2026-11-21 12:46:24 UTC,
  block 10986124).
- **Package:** `p9bbA2-5b05cc3` (sha256 `3c756a15dd362ace993f9c4b7722b8e311a95a679280aa1514dac8a2ebcdf267`), job
  `BB-A2`, 40 segments.
- **Known so far:** the start and the package check (ALL SAME, 40). No result of BB-A2.

## 1. On the GPU server, after the end (read only)

The end is the line "BB-A2 complete: 40 segments" in `run.log`; `status.sh` shows 40 of 40.
```sh
cd ~/runs/a2 && T=$(date -u +%Y%m%dT%H%MZ)
cp p9bbA2-5b05cc3/run.log a2-run-$T.log
nice -n 19 ionice -c 3 sh -c "find p9bbA2-5b05cc3 a2-run-$T.log -type f ! -name '*.pid' \
    ! -path p9bbA2-5b05cc3/run.log ! -path p9bbA2-5b05cc3/run.out ! -path 'p9bbA2-5b05cc3/.a2-watch/*' -print0 \
  | LC_ALL=C sort -z | xargs -0 sha256sum" > ~/runs/a2-results-sha256-$T.txt \
  && wc -l ~/runs/a2-results-sha256-$T.txt && sha256sum ~/runs/a2-results-sha256-$T.txt
nice -n 19 ionice -c 3 tar -czf ~/runs/a2-p9bbA2-5b05cc3.tar.gz --exclude='*.pid' --exclude='p9bbA2-5b05cc3/run.log' \
  --exclude='p9bbA2-5b05cc3/run.out' --exclude='p9bbA2-5b05cc3/.a2-watch' p9bbA2-5b05cc3 a2-run-$T.log \
  && sha256sum ~/runs/a2-p9bbA2-5b05cc3.tar.gz
```
- The project lead reports the number of lines and the sha256 of the list, and the sha256 of the archive.
- List and archive hold the same files.

## 2. On the laptop: checks, backup, timestamp (before any evaluation)

1. **Archive and list:**
   - the sha256 of the archive equals the reported one;
   - the archive is unpacked into a new, empty directory;
   - `sha256sum -c` of the list there gives every line OK, and the number of files equals the number of lines.
2. **Package files:** unchanged against `p9bbA2-5b05cc3.tar.gz`, apart from the outputs of the run.
3. **Package check:** `check/report.txt` shows ALL SAME, 40 cases.
4. **Segments:** `tools/check_segments.py --p9sim PKG/bin/p9sim --jobs RUN`. Expected: 0 failures, 40 of 40 segments.
5. **Backup** of the archive, by the project lead:
   - `runs/notary/notary-archive-backup.sh`, name `a2`, to `~/backups`, OneDrive and the second target;
   - then `runs/notary/notary-restore-check.sh` on one copy.
6. **Timestamp:** the list is copied unchanged to `runs/notary/a2-results/` and stamped with OpenTimestamps.

If one of 1–4 fails, nothing is evaluated, and the failure is reported.

## 3. The evaluation

**From what:**
- **Checkout:** a clean, detached checkout of medas-p9-search at the commit of this file.
  - `tools/prod_eval.py` byte-identical to `prod-eval-v1` (sha256 `1ebb2d45…5cbb`);
  - `tools/sets_decompose.py` as in 2d10dae, `tools/sets_subset_spread.py` as in 4eec855;
  - checked as in `docs/bb-a-rin1-evaluation-procedure.md`, section 3.
- **Program:** `bin/p9sim` of the unpacked package, checked against `bin/SHA256-p9sim`.
- **Names:** RUN is the unpacked `p9bbA2-5b05cc3/jobs/BB-A2`, PKG the unpacked package directory, OUT a new directory.
  Relative paths.

**The measures** (criteria, section 3), with exactly the calls that gave the values of BB-A:
1. **M1–M5:**
   ```sh
   ../medas-p9-search/build/venv/bin/python -I tools/prod_eval.py RUN --out OUT/eval --p9sim PKG/bin/p9sim \
     --criteria bb2021-A --window 1e9 4e9 --t-end 4e9 --n-tp 64000 --subsets 4 --observed docs/bb2021-observed-table1.tsv
   ```
2. **R beyond the wall:**
   ```sh
   ../medas-p9-search/build/venv/bin/python -I tools/sets_decompose.py RUN --p9sim PKG/bin/p9sim --wall 256 --out OUT/decomp --name A
   ```
   → `means_beyond_wall.S_BB.mean_R`.
3. **Inclination shares and M2 per subset:**
   ```sh
   ../medas-p9-search/build/venv/bin/python -I tools/sets_subset_spread.py RUN --p9sim PKG/bin/p9sim --subsets 4 --n-tp 64000 > OUT/spread.json
   ```
   → `all` → `inc_q>42`, `inc_q42-100`, `M2`.
4. **Survivors** at 1, 2, 3, 4 Gyr: `OUT/eval/result.json` (`survivors`) and `OUT/decomp/survival.csv`.

**The comparison with BB-A** (criteria, section 4):
- **Values of BB-A,** from the files in this repository:
  - M1–M5 and survivors from `docs/sets-result-A-20261117/result.json`;
  - R beyond the wall from `docs/sets-decomposition-20261117/A/summary.json`;
  - shares and M2 from `docs/sets-decomposition-3-20261117/spread-A.json`.
- **Per measure:** the difference BB-A2 − BB-A, with sign; for M1 the angular difference in −180°…180°.
- **For M2 and the ten shares:** "within" or "outside" the tolerance of addendum 3:
  - M2 ± 0.012;
  - each prograde share ± 0.008;
  - retrograde ± 0.022 (q > 42 au) and ± 0.011 (42 ≤ q ≤ 100 au).
  - The number outside is reported.
- **Against the prediction** of section 4 of the criteria: all within; M1 within ± 15°; survivors at 4 Gyr within ± 2 %.
- **For information:** the verdict of BB-A2 by the comparison criteria of set A (`OUT/eval/result.json` → `verdict`).
  It changes nothing of outcome 4.

**Afterwards:**
- **Report:** `docs/bb-a2-result-<date>.md` with the files of the tools as written, committed and stamped.
- **Review:** an independent review.
- **Entry:** with the project lead's go, the entry r4: `result`, referring to entry #10.
