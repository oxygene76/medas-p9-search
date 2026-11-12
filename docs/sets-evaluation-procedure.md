# How the 4-Gyr runs of sets A and B are evaluated (fixed 2026-11-12, before any look at either run)

New file. The criteria are `docs/bb2021-comparison-criteria.md` sections 4–6, as entered with entries e3 and e4, with
the release of each set by its paired test (entry e5; set A: `docs/paired-result-A-20261112.md`). Nothing of them is
changed here. This file fixes the steps, the same as for the production run (`docs/production-evaluation-procedure.md`):
the checksum list and its timestamp, the backup, then the evaluation with the tool of entry e3.

**The runs:**
- **Package:** `p9bbsets-5b05cc3` on the A100, one job per set: `jobs/BB-A` (seed 311), `jobs/BB-B`.
- **Size:** 64,000 test particles each, 0–4 Gyr, 40 segments of 100 Myr with 10 snapshots each.
- **Order:** set A started on 2026-11-12 at 09:08 UTC; set B follows on the A100 after set A (addendum 15).
- **Release:** each set is released by its file `v2/BB-<set>.ok`, written by `tools/pair_eval.py`.

## 1. Each set as soon as it is complete

- **Set A** is evaluated as soon as its 40 segments are done, while set B is computed. Its measures and its own
  verdict ("agrees with B&B" or not, and "not decided" by the subset scatter) are reported in its own report.
- **The outcome of section 6**, which needs both sets, is evaluated when set B is done.
- **Set B is not touched:**
  - Its run and its evaluation are fixed by the criteria. Nothing about them is decided after set A.
  - The partial archive of set A excludes `jobs/BB-B`.

## 2. On the server: checksum list and archive of a set (read only)

After `status.sh` of p9bbsets (or the chain's status) shows the set complete. `<S>` is A or B.
```sh
cd ~/runs/sets && T=$(date -u +%Y%m%dT%H%MZ)
cp p9bbsets-5b05cc3/run.log sets<S>-run-$T.log
nice -n 19 ionice -c 3 sh -c "find p9bbsets-5b05cc3 sets<S>-run-$T.log -type f ! -name '*.pid' \
    ! -path '*/jobs/BB-<other>/*' ! -path p9bbsets-5b05cc3/run.log ! -path p9bbsets-5b05cc3/run.out -print0 \
  | LC_ALL=C sort -z | xargs -0 sha256sum" > ~/runs/sets<S>-results-sha256-$T.txt \
  && wc -l ~/runs/sets<S>-results-sha256-$T.txt && sha256sum ~/runs/sets<S>-results-sha256-$T.txt
nice -n 19 ionice -c 3 tar -czf ~/runs/sets<S>-p9bbsets-5b05cc3.tar.gz --exclude='*.pid' \
  --exclude='p9bbsets-5b05cc3/jobs/BB-<other>' --exclude='p9bbsets-5b05cc3/run.log' --exclude='p9bbsets-5b05cc3/run.out' \
  p9bbsets-5b05cc3 sets<S>-run-$T.log && sha256sum ~/runs/sets<S>-p9bbsets-5b05cc3.tar.gz
```
- **While the other set runs** in the same package directory, its job is excluded, and `run.log` is taken only as a
  copy made at the time of the archive. List and archive hold the same files.
- **For set B,** after it is complete: the same with `<other>` = A. The files of `jobs/BB-A` are fixed by the list
  of set A.
- **The project lead reports** the number of lines and the sha256 of the list and of the archive.

## 3. On the laptop: checks, backup, timestamp (before any evaluation)

1. **Archive and list:**
   - the sha256 of the archive equals the reported one;
   - the archive is unpacked into a new, empty directory;
   - `sha256sum -c` of the list in that directory gives every line OK, and the number of files equals the number of
     lines.
2. **Package files:** unchanged against `p9bbsets-5b05cc3.tar.gz` (sha256 in e4), apart from the run outputs.
3. **Package check:** `check/report.txt` shows ALL SAME on the A100.
4. **Segments:** `tools/check_segments.py` (31ed973) over the job of the set. Expected: 0 failures, 40 of 40 segments.
5. **Backup** of the archive, by the project lead: `runs/notary/sicherung-ergebnisse-20261110.sh` with `ARCHIVE_LISTE`,
   name `setsa` or `setsb`.
6. **Timestamp:** the list is copied unchanged to `runs/notary/sets-results/` and stamped with OpenTimestamps; only
   its hash leaves the laptop.

## 4. The evaluation

- **From what:** a clean, detached checkout of medas-p9-search at the commit of this file (`git status` empty).
  - `tools/prod_eval.py` there is byte-identical to the file of entry e3: sha256
    `1ebb2d45c47ea0bb465b67f95d1d9b3a766678b4230fc89cad7d01c4b2c65cbb`, tag `prod-eval-v1`.
  - Check: `git diff --stat prod-eval-v1 HEAD -- tools/prod_eval.py tools/analyze.py` is empty.
- **Program:** `bin/p9sim` of the unpacked package, checked against `bin/SHA256-p9sim` (`b14f7956…`).
- **Observed objects:** `docs/bb2021-observed-table1.tsv`, checked against Table 1 of the paper on 2026-11-10.
- **Command per set**, with relative paths so that no local path enters the outputs. RUN is the unpacked
  `p9bbsets-5b05cc3/jobs/BB-A` (or `BB-B`), PKG is the unpacked package directory, OUT is a new directory:
  ```sh
  ../medas-p9-search/build/venv/bin/python -I tools/prod_eval.py RUN --out OUT --p9sim PKG/bin/p9sim \
    --criteria bb2021-A --window 1e9 4e9 --t-end 4e9 --n-tp 64000 --subsets 4 --observed docs/bb2021-observed-table1.tsv
  ```
  For set B: `--criteria bb2021-B`.
- **The outcome**, after both sets:
  ```sh
  ../medas-p9-search/build/venv/bin/python -I tools/prod_eval.py --outcome OUT_A/result.json OUT_B/result.json > OUT_AB/outcome.txt
  ```
- **Verdicts:** as `docs/bb2021-comparison-criteria.md` sections 5 and 6 fix them.
  - **Per set:** agreement if M1, M2 and M3 are within tolerance, and for set A also M4; "not decided" if the subsets
    scatter more than 10°.
  - **Both sets:** outcomes 1–5 of section 6.

## 5. What is committed (unchanged)

- **`docs/sets-result-<S>-<date>/`:** `result.json`, `timeseries.csv` and `report.txt` as the tool wrote them; an
  `environment.txt` with date, checkout, versions and the sha256 of tool, p9sim, archive and list; the list with its
  `.ots`.
- **After set B:** `docs/sets-outcome-<date>/outcome.txt`.
- **Reports:** one result report per set and one for the outcome, each its own commit, stamped, and independently
  reviewed before anything goes into the research note.
- **Notary entry:** the outcome is entered as `result` referring to the entry that fixes the criteria (section 6 of
  the criteria: e4, #5).
