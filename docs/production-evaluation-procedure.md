# How the production run is evaluated (fixed 2026-11-06, before the evaluation)

New file. The criteria are `docs/production-criteria.md` section 4 as entered in entry 3 (chain entry #4, block
10723643); nothing of them is changed here. This file fixes only the steps, in this order: first the checksum list of
all result files and its timestamp, then the evaluation.

**The run:** `p9prod-9a084ed` on the A100 of the GPU server, complete on 2026-11-06 (reported by the project lead):
- 40 of 40 segments, `seg039` to 4,000 Myr;
- 17,798 test particles left;
- result hash of `seg039`: `d41152221b3dfc9ff490a21eb0120896b9bfce95a6a2bb0378c8005b0527f1c3`.

## 1. The checksum list, on the server (read only)

As the user of the run, after `status-a100.sh` reports it as no longer running. The commands only read the run
directory; the list is written next to it, under `~/runs/`.
```sh
cd ~/runs/prod && T=$(date -u +%Y%m%dT%H%MZ) && nice -n 19 ionice -c 3 sh -c \
  'find p9prod-9a084ed -type f ! -name "*.pid" -print0 | LC_ALL=C sort -z | xargs -0 sha256sum' > ~/runs/prod-results-sha256-$T.txt \
  && wc -l ~/runs/prod-results-sha256-$T.txt && sha256sum ~/runs/prod-results-sha256-$T.txt
```
- **Paths:** relative to `~/runs/prod`, with the prefix `p9prod-9a084ed/`, as the list of the equivalence test.
- **Content:** every file of the run directory: the package, `params.env`, `run/`, `check/`, `production.log`,
  `segments.tsv`, and per segment `input.sa`, `output.sa`, `final.state`, `flybys.tsv`, `removed.tsv`,
  `result.txt`, `stderr.txt`, `DONE`.
- The project lead reports the number of lines and the sha256 of the list.

## 2. The archive, on the server

```sh
cd ~/runs/prod && nice -n 19 ionice -c 3 tar -czf ~/runs/prod-results-p9prod-9a084ed.tar.gz p9prod-9a084ed \
  && sha256sum ~/runs/prod-results-p9prod-9a084ed.tar.gz
```
- About 2–3 GB, unpacked to the same relative paths as the list.
- Transferred to the laptop with the list, by the usual way.

## 3. The timestamp, on the laptop (before any evaluation)

1. **Archive:** sha256 of the archive equal to the reported one. Unpacked into a new, empty directory, never into a
   repository.
2. **List:** `sha256sum -c` of the list in that directory. Every line OK, and the number of files equal to the number
   of lines.
3. **Copy:** the list is copied unchanged to `runs/notary/prod-results/prod-results-sha256-<T>.txt`.
4. **Timestamp:** stamped with OpenTimestamps (`build/ots-venv/bin/ots stamp`); only its hash leaves the laptop.
5. **Record:** list, its sha256 and the `.ots` file are recorded in the result (section 5).

Only after that the evaluation starts.

## 4. The evaluation

- **From what:** a clean, detached checkout of medas-p9-search at the commit of this file (a new
  `git worktree add --detach`, `git status` empty), not from the working tree.
  - `tools/prod_eval.py` there is byte-identical to the file of entry 3: sha256
    `1ebb2d45c47ea0bb465b67f95d1d9b3a766678b4230fc89cad7d01c4b2c65cbb`, blob `b9ccd3a…`, commit 7302607, the tag
    `prod-eval-v1` of the criteria.
  - Checked before the run with `sha256sum`, and with `git diff --stat prod-eval-v1 HEAD -- tools/prod_eval.py`
    (empty).
- **Program:** snapshots are read with the p9sim of p9prod-9a084ed (sha256 `b14f7956…`; `bin/p9sim` in the unpacked
  run, checked against `bin/SHA256-p9sim`), passed as `--p9sim`.
- **Python:** `build/venv` of the laptop; Python and numpy versions are recorded (section 5).
- **Observed objects (information only):** `docs/bb2021-observed-table1.tsv` of this commit.
  - Brown & Batygin (2021), Table 1, with Δϖ against ϖ9 = 254° as `docs/bb2021-comparison-criteria.md` section 8
    fixes it; 10 objects, without 2013 FT28.
  - The Planet Nine of the production run starts with ϖ = 248.5°. The 254° of section 8 are kept; the difference is
    noted in the report, and nothing is judged on it.
- **Command**, in the detached checkout, with RUN = the unpacked `p9prod-9a084ed`:
  ```sh
  ../medas-p9-search/build/venv/bin/python -I tools/prod_eval.py RUN --out OUT --p9sim RUN/bin/p9sim \
    --criteria production --window 1e9 4e9 --t-end 4e9 --n-tp 64000 --subsets 4 --observed docs/bb2021-observed-table1.tsv
  ```
- **Output:** the tool writes `result.json`, `timeseries.csv` and `report.txt`. It refuses an incomplete run
  ("not decided (run not complete over the window)") and an existing output directory.
- **Verdict:** as fixed in section 5 of the criteria.
  - "decided" if the largest angular distance of the M1 of the four subsets from the pooled M1 is at most 10°;
  - "not decided" if it is more;
  - a deviating subset is reported, never excluded.

## 5. What is committed (unchanged)

`docs/production-result-<date>/`:
- `result.json`, `timeseries.csv` and `report.txt` as the tool wrote them;
- `environment.txt`: date, checkout commit, Python and numpy versions, sha256 of `prod_eval.py`, of the p9sim, of the
  archive and of the list;
- the list itself, with its `.ots` file.

The result report is written afterwards, as its own commit, and stamped with OpenTimestamps.
