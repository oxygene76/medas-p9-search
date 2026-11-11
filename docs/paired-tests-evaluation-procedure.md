# How the paired tests of sets A and B are evaluated (fixed 2026-11-11, before any look at R)

New file. The criteria are `docs/bb2021-paired-test-proposal.md` as entered in entry e5 (chain entry #6, block
10814015, commit e83d960). Nothing of them is changed here. This file fixes the steps, the same for each set: checks,
backup, checksum list and timestamp, then the evaluation with `tools/pair_eval.py`. Each set is evaluated on its own
as soon as all its runs are complete.

## 1. Each set on its own

- **The criteria decide per set:** "one decision per set" (section 1); "one evaluation per set, without a
  multiplicity correction" (section 8, decision 2 of 2026-11-06).
- **The rule against an interim look is per set:** "no look at R before all runs of a set are complete, and no change
  of the number of runs after a look" (section 2).
- **Set A** (seeds 331–339) is therefore evaluated as soon as its 9 V5 jobs `PV5-s331` … `PV5-s339` and its 144
  MERCURIUS slices `PM-s331-part00` … `PM-s339-part15` are complete. This holds even while the slices of set B are
  still running.
- **Set B** (seeds 341–349) follows the same steps when its runs are complete.
- **Looking at set A does not inform set B.** Set B's runs are fixed by e5 and already started, and its number of
  runs is not changed. The report of set A is written before set B is complete and says so.
- `tools/pair_eval.py --set A` refuses as long as one segment of set A is missing.

## 2. The partial archive of a set, on the server (read only)

Only after `status.sh` of both packages shows every job of the set complete. The commands only read the run
directories and write under `~/runs/`.
- **V5:** the package `p9pair-v5-fed221a` without the jobs of the other set.
- **M:** the package `p9pair-merc-fed221a` without the jobs of the other set and without the growing `run.log` and
  `run.out`. Instead, a copy of `run.log` is made at the time of the archive and packed with it.

The commands are in the guide of the project lead (not in git). The project lead reports the sha256 of both archives
and the counts of the `DONE` files: 90 for V5 and 1,440 for M per set.

## 3. Checks, backup, checksum list and timestamp, on the laptop

1. **Archives:** sha256 equal to the reported ones. Each is unpacked into a new, empty directory, never into a
   repository.
2. **Package files:** unchanged against the package archive of fed221a, apart from the run outputs (`jobs/`, logs,
   `check/`).
3. **Package check:** `check/report.txt` shows ALL SAME (V5: on the A100; M: on CPU 1).
4. **Segments:** `tools/check_segments.py` (31ed973, sha256
   `c0aeb99d7220b647e4fde823db324dc967aab421909d09af2110b9b972961b6f`) over the 9 V5 jobs and 144 slices of the set,
   with `--pair` for each seed. Expected: 0 failures, the 16 slices of each seed holding exactly the start values of
   its V5 job. The tool looks at no result measure. It was tested on the long runs 110–112 (0 failures) and against
   4 injected faults (all found).
5. **Backup:** both archives encrypted, to three places, each restore-checked
   (`runs/notary/sicherung-ergebnisse-20261110.sh` with `ARCHIVE_LISTE`; names `pairav5` and `pairam` for set A,
   `pairbv5` and `pairbm` for set B). This step is done by the project lead.
6. **Checksum lists** of the unpacked run directories, made as for the long runs, copied unchanged to
   `runs/notary/pair-results/`.
7. **Timestamps:** both lists stamped with OpenTimestamps; only their hashes leave the laptop.

Only after that the evaluation starts.

## 4. The evaluation

- **From what:** a clean, detached checkout of medas-p9-search at the commit of this file (`git worktree add
  --detach`, `git status` empty).
  - `tools/pair_eval.py` there has sha256 `4eecce185558127701da639d10985c24559962ecc76fe1ecbbd0f7c3f96c45c9`, equal to
    its entry in the manifest of e5.
  - `tools/equiv_eval.py`, `tools/analyze.py` and `tools/v2_encounter_check.py` equal their entries in e5:
    `git diff --stat e83d960 HEAD` over the four files is empty.
- **Program:** the p9sim of p9prod-9a084ed, sha256 `b14f7956…`: `bin/p9sim` of the unpacked M package, checked
  against `bin/SHA256-p9sim`.
- **Python:** `build/venv` of the laptop; Python and numpy versions recorded.
- **Command**, in the detached checkout, with relative paths (so that no local path enters the outputs). V5 and M are
  the unpacked package directories of the set, and OUT is a new directory:
  ```sh
  ../medas-p9-search/build/venv/bin/python -I tools/pair_eval.py --set A --v5 V5 --m M --p9sim M/bin/p9sim \
    --json OUT/result.json --release-dir OUT/release > OUT/report.txt
  ```
- **Verdict:** as section 4 of the criteria: "equivalent", "not shown" or "different", from the 95 % interval of the
  mean of the 9 paired differences against ±0.035.
  - Reported, not deciding: R at 200 Myr, S with the observed cut, the test particles left, and the six encounter
    shares (V5 only).
- **Release** (criteria section 5): only for "equivalent", the tool writes `OUT/release/BB-A.ok` with both lines and
  prints its sha256.
  - The project lead copies it unchanged to `~/runs/sets/p9bbsets-5b05cc3/v2/BB-A.ok`, after keeping the V2 file as
    `v2/BB-A.v2`.
  - Nobody writes the release line by hand.
  - For "not shown" or "different" there is no release file, and the outcome tables of section 5 apply.

## 5. What is committed (unchanged)

`docs/paired-result-<set>-<date>/`:
- `result.json` and `report.txt` as the tool wrote them, and the release file if there is one;
- `environment.txt`:
  - date and checkout commit;
  - Python and numpy versions;
  - sha256 of `pair_eval.py`, of the p9sim, of both archives and of both lists;
- the lists, with their `.ots` files.

The result report of the set is written afterwards, as its own commit, and stamped with OpenTimestamps. It goes into
the research note only after the independent review, as for r1.
