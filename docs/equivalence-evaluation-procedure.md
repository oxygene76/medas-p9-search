# How the equivalence test is evaluated (fixed 2026-10-23, before the evaluation)

New file; the files of manifest (e2) are not changed.

- **When:** only after the notary entry of manifest (e2) (sha256
  `89ddbf2fb75c0c1e38f571a09a17658f4536592c50fe34c936a670a99f8a227e`) is on
  the chain (the project lead says so), and only when all three groups are
  complete (`tools/equiv_eval.py` refuses otherwise).
- **From what:** a clean, detached checkout of medas-p9-search at
  `c45833a6e5ec11c26ee51b4e50ddd5b1adbab84a` (a new `git worktree add --detach`,
  `git status` empty), not from the working tree. `tools/equiv_eval.py` and the
  `tools/analyze.py` it imports are taken from there; both are in manifest (e2)
  and unchanged since c45833a (checked 2026-10-23: `git diff --stat c45833a HEAD`
  touches neither; the later commits b238800 and f135490 change only
  `docs/notary.md` and `tools/solar_obliquity.py`).
- **Programs:** snapshots are read with the p9sim binary of p9prod-9a084ed listed
  in manifest (e2) (`medas-p9-search-bb2021/build/equiv-bin/p9sim`, sha256
  `b14f7956…`), passed as `--p9sim`; Python and numpy of `build/venv`
  (Python 3.14, numpy as installed on 2026-10-23, recorded with the result).
- **Data:** WH from `medas-p9-search-bb2021/runs/equiv/wh`, checked against
  `docs/equivalence-wh-sha256.txt` first (568 of 568); V5 and M from the result
  tarball of appmdp-05, unpacked into a new directory, its sha256 recorded.
- **Command** (in the detached checkout):
  `build/venv/bin/python -I tools/equiv_eval.py --wh <WH> --v5 <V5> --m <M>
  --p9sim <p9sim of p9prod-9a084ed> --json <out>`; the output and the JSON are
  committed unchanged.
- **Source and binary:** the p9gpu binary of groups WH and V5 is that of
  p9prod-9a084ed; `git diff --stat 9a084ed 69b8412 -- gpu src Makefile` is
  empty (checked 2026-10-23), so the source in manifest (e2) (69b8412) is the
  source of that binary.
