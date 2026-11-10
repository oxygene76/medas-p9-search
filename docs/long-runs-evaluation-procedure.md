# How the paired long runs 110–112 are evaluated (fixed 2026-11-10, before the evaluation)

New file. The criteria are `docs/long-runs-110-112-criteria.md` as entered with entry 3 (chain entry #4, block
10723643, commit 7302607, sha256 `2934f040…602c`, unchanged since); nothing of them is changed here. This file fixes
the steps, in this order: the checks of the results, the backup of the archives, the checksum lists and their
timestamps, then the evaluation. It also fixes how the tool reads two cases the criteria leave open (section 3).

**The evaluation tool was written after the runs**, on 2026-11-10, and before anyone looked at R. It is
`tools/long_eval.py` at commit 6a69854 (sha256 `6c881acf6296b9211cf533d956b47572e23c8f93e0433beb7120aad9e8aaa30b`).
Entry 3 fixed the criteria but no program. The tool is committed and timestamped with this file before the
evaluation, and the report says so.

## 1. The runs and their results (checked 2026-11-10)

| | V5 | M (MERCURIUS) |
|---|---|---|
| package | `p9long-v5-ac47329`, p9gpu `7666c5ba…` on the A100 | `p9long-merc-ac47329`, p9sim `b14f7956…` on CPU 1 |
| jobs | `V5-s110`, `V5-s111`, `V5-s112`, 40 segments of 100 Myr, 10 snapshots each | `M-s110-part00` … `M-s112-part07`, 24 slices of 250, 200 segments of 20 Myr, 2 snapshots each |
| end | `run.log`: "all jobs ended" 2026-11-10 04:27:17Z | complete, as reported on 2026-11-09 |
| archive | `v5-full-ac47329.tar.gz`, sha256 `9c196d33a83c41f7d9efc1666d6267ad1f7a990c3562492c871c714055722d0b` | `merc-full-ac47329.tar.gz`, sha256 `bd9ceac88e2ecd777bb62ec79a524dc0a0c619624e16c6a8a11c1ba7d00fe144` (and `merc-results-ac47329.tar.gz`, `295d19d5…f93e`) |
| test particles left at 4 Gyr | s110 541, s111 570, s112 561 | s110 553, s111 544, s112 572 (1,669 in all) |

**Checks of the unpacked archives, on the laptop, without R:**
- **Archive:** sha256 equal to the reported one; unpacked into a new, empty directory.
- **Package:** the package files unchanged; the package check `ALL SAME` on the GPU it ran on (V5).
- **Every segment** (120 V5, 4,800 M):
  - `DONE` written;
  - input and output hashes in `DONE` equal to the files;
  - the result line equal to `result.txt` and to the row of `segments.tsv`;
  - `final.state` equal to `final_state_sha256`;
  - the time of the segment's end;
  - the program, its version, mode and precision.
- **Chain of segments:**
  - N continuous from segment to segment;
  - removals counted correctly;
  - the state of the last snapshot of each segment equal to its `final_state_sha256` and to the state of the next
    segment's input.
  - The bytes of a snapshot written again by `p9sim last` differ from the stored input (pointer fields of the
    archive format); the states are equal, which is what counts.
- **Start values paired:** at t = 0 the 8 slices of each seed hold exactly the 2,000 test particles of the V5 run,
  with the same values, and the same Sun and planets (`long_eval.py` checks this again before evaluating).
- **Last rows:** V5 s110 `48f1414b…8079`, s111 `d327ca05…9a5a`, s112 `8150e82b…c5a4c`, as reported.

**Model counters, not errors:**
- Steps at the sub-step cap: V5 s110 segment 29 (1), s111 segments 1 and 4 (1, 2), s112 segments 1 and 11 (1 each).
  The production run had such steps as well.
- One test particle collided with Saturn (V5 s110 segment 29, `removed_encounter=1`, `collisions=2:1`): collisions
  at the planets' radii are part of the V5 model.
- No encounter removal in M (`removed_encounter=0` in all 4,800 segments).

**Deviation from section 5 of the criteria (interim check):**
- **M:** the slices were stopped and started again (17 stops in `run.log`, the first 2026-11-04 17:10Z). The chain
  of segments stays consistent. Segment 5 of one slice, computed again on the laptop from its stored input, gave the
  server's result hash (2026-11-05, `merc-resume-seg005`).
- The resume test of a V5 run did not take place: `run.log` has no stop. The V5 runs went through without
  interruption.
- The bit reproducibility of the V5 package rests on its check (42 cases `ALL SAME`) and the package's resume rule.
- The report names the deviation; it does not change the evaluation.

## 2. Backup and timestamps, before the evaluation

1. **Backup** of both archives, encrypted to the backup key, by the project lead (as for the production run):
   ```sh
   bash runs/notary/notary-archive-backup.sh v5long <FINGERPRINT> <USB_DIR> \
     ../medas-p9-search-equiv/build/v5-full-ac47329.tar.gz 9c196d33a83c41f7d9efc1666d6267ad1f7a990c3562492c871c714055722d0b
   bash runs/notary/notary-archive-backup.sh merclong <FINGERPRINT> <USB_DIR> \
     ../medas-p9-search-equiv/build/merc-full-ac47329.tar.gz bd9ceac88e2ecd777bb62ec79a524dc0a0c619624e16c6a8a11c1ba7d00fe144
   ```
   Then for each, `notary-restore-check.sh <USB_DIR>/p9-<name>-<date>.tar.gz.gpg <key file>`; the passphrase is
   entered by hand.
2. **Checksum lists** of both unpacked run directories, made on the laptop as the list of the production run
   (`find … -type f ! -name "*.pid" -print0 | LC_ALL=C sort -z | xargs -0 sha256sum`, paths with the prefix
   `p9long-v5-ac47329/` or `p9long-merc-ac47329/`), copied unchanged to `runs/notary/long-results/`.
3. **Timestamps** with OpenTimestamps (`build/ots-venv/bin/ots stamp`) of:
   - both lists;
   - this file;
   - `tools/long_eval.py`.

   Only their hashes leave the laptop.

## 3. Two cases the criteria leave open (to be confirmed by the project lead before the evaluation)

Section 3 says that a window with too few distant survivors gets no S, that "the decision uses the remaining times",
and that with fewer than three times left the result is "not decided". It does not say:
- **L1, a run without S at a time:** d(t) is used only if all six runs have S(t), so d(t) always comes from three
  differences ("the mean and its standard error from the three differences", section 2). A time that one run lacks
  is dropped for all.
- **L2, a missing time that a condition names:**
  - without d(4 Gyr) the result is "not decided", because every condition is about 4 Gyr;
  - without d(0.5 Gyr) it is also "not decided", because the growth condition cannot be checked;
  - without d(1 Gyr) or d(2 Gyr), the sign condition uses the times that are left.

Expected: at 4 Gyr about 540–570 test particles per run are left; with 57 % distant, about 310 distant survivors,
well above 100. The cases L1 and L2 are therefore not likely to arise. The counts of snapshots below 100 are reported.

## 4. The evaluation

- **From what:** a clean, detached checkout of medas-p9-search at the commit of this file (`git worktree add
  --detach`, `git status` empty).
  - `tools/long_eval.py` there has sha256 `6c881acf6296b9211cf533d956b47572e23c8f93e0433beb7120aad9e8aaa30b`.
  - `tools/equiv_eval.py` and `tools/analyze.py`, which it imports, are unchanged since the equivalence result
    (`git diff --stat 7302607 HEAD -- tools/equiv_eval.py tools/analyze.py` empty).
- **Program:** the snapshots of both groups are read with the p9sim of p9prod-9a084ed (sha256 `b14f7956…`;
  `bin/p9sim` in the unpacked V5 run, checked against `bin/SHA256-p9sim`).
- **Python:** `build/venv` of the laptop; Python and numpy versions are recorded.
- **Command**, in the detached checkout, with V5 = the unpacked `p9long-v5-ac47329` and M = the unpacked
  `p9long-merc-ac47329` (full archive):
  ```sh
  ../medas-p9-search/build/venv/bin/python -I tools/long_eval.py --v5 V5 --m M --p9sim V5/bin/p9sim --out OUT --jobs 4
  ```
- **Output:** `result.json`, `timeseries.csv` (R, distant survivors and test particles per run and snapshot) and
  `report.txt`. The tool refuses an incomplete run, unpaired start values and an existing output directory.
- **Verdict:** as fixed in section 3 of the criteria, with L1 and L2 of section 3 above:
  - "growing bias found";
  - "no growing bias found", stated with d(t), its standard errors and the low power of three pairs;
  - or "not decided".

## 5. What is committed (unchanged)

`docs/long-runs-result-<date>/`:
- `result.json`, `timeseries.csv` and `report.txt` as the tool wrote them;
- `environment.txt`:
  - date and checkout commit;
  - Python and numpy versions;
  - sha256 of `long_eval.py`, of the p9sim, of both archives and of both lists;
- the lists, with their `.ots` files.

The result report is written afterwards, as its own commit, with what follows from it (section 4 of the criteria) and
the deviation of section 1, and stamped with OpenTimestamps.
