# Checklist for publishing the repository (2026-11-10)

Builds on `docs/publication-commits.md` (what is published, and in which order) and `docs/data-package-proposal.md`
section 7 (secret scan, private details, history unchanged). Each point is ticked off with its date. Nothing of this
has been done yet, except where a date is given.

**Rule:** no merge into `main`, no tag and no push until point E. The repository has no remote yet.

## A. Before anything else

- [ ] All evaluations covered by the publication are done, with their result reports committed and stamped:
  - production run;
  - long runs 110–112;
  - paired tests A and B;
  - sets A and B, if released (or a later e7, `docs/data-package-e6.md` section 2).
- [ ] Entry e6 is on chain, and `docs/notary.md` is updated.
- [ ] `docs/publication-commits.md` is regenerated with e6 (`tools/notary_refs.py`). The tips and the closure are
      known.
- [ ] All pending OTS stamps are upgraded and checked against two block explorers (only block heights sent).
- [ ] The decisions still open in `docs/data-package-proposal.md` are made: ORCID, wording of the methods section.

## B. Content of the published state

- [ ] **README.md rewritten.** Today it still says "Pilot, local only … no chain entries", which is no longer true.
      New content:
  - what the project is;
  - the status ("not peer-reviewed", the research note);
  - how to build, the run packages, and how to verify one segment;
  - the notary entries with links to `docs/notary.md`;
  - the data records (DOIs);
  - the licence;
  - the use of AI tools (wording as in the methods section).
- [ ] `CITATION.cff` of the software (author Eike Janßen, MEDAS Computers GmbH, ORCID).
- [ ] `LICENSE` (GPL-3.0-or-later) and `third_party/README.md` (REBOUND 5.2.2, checksum, licence) present in the
      published tree.
- [ ] New documents name no host names, home paths or GPU UUIDs ("the GPU server", relative paths). Notarised files
      stay unchanged (option 7.1); the README says so.
- [ ] `runs/`, `build/` and `.env`-like files are ignored and appear in no published tree: `git ls-tree -r` of the
      state to be published, checked for `runs/`, `build/`, `*.env` and `*receipt*`.

## C. Branches and tags

- [ ] **Published:** only `main` and the tags of the list (`notary-<entry>-<commit>`, one per referenced commit). The
      existing tags inside the closure, `bb2021-criteria-draft-1`, `make-ic-v1` and `prod-eval-v1`, are published
      with them.
- [ ] **Not published:**
  - all other branches, among them the worktree branches (`feat/plate-pilot`, `feat/own-images`, `feat/new-etnos`,
    `feat/c3-bundle`, `run/*` …);
  - the tags outside the closure (`plates-core-*`, `own-images-*`, `etno-tier2-v1`).
- [ ] The medas-p9-search worktrees share **one** repository with all branches. A push therefore names every ref
      explicitly, and never uses `--all`, `--tags` or `--mirror`.

## D. Merge into `main`, only right before the push

- [ ] **Dry run, done 2026-11-10 for the tips after e5** (`e83d960`, `d4dadd9`, `fed221a`): `git merge-tree
      --write-tree`, pairwise and all three together, gives no conflict. Repeat it with the tips after e6.
- [ ] **Merge commit** on `main` of the tips: a new commit, no rebase and no rewrite. Message: "Publication: the state
      of the campaign (tips …)".
- [ ] Afterwards, every referenced commit is an ancestor of `main` or of a tag:
      `git merge-base --is-ancestor <commit> main` for each line of the list.
- [ ] Set the tags of the list (lightweight or annotated, decided at that time) on exactly the referenced commits.

## E. Scans over exactly the state to be published

Run after D, and before the push:
- [ ] **gitleaks** (v8.18.4, built from source as on 2026-11-04, checked against sum.golang.org) over the history of
      `main` and the tags. Expected: no leaks. A control repository with planted keys proves the scanner works.
- [ ] **`tools/publish_scan.py --git <rev>`** over the tree of `main` and of every tag. Expected: 0 blocking findings
      (secrets, Gaia data).
- [ ] **`tools/publish_scan.py --history`** over the published state. Reported private details are compared with the
      known list (data package proposal section 7: host name, home path, GPU UUID, author address), and anything new
      is decided before the push.
- [ ] `git count-objects` and the size of a fresh `git clone --mirror` of only the published refs (in a temporary
      directory), as a check that nothing large or private comes along.

## F. Push

- [ ] Create the remote (host and organisation are decided at that time) and set it, without a push.
- [ ] `git push <remote> main` and then `git push <remote> refs/tags/<tag> …` for every tag of the list, each named.
- [ ] Clone it fresh from the remote, then check:
  - `git log --oneline main | wc -l` equals the closure of the list;
  - the tags are present;
  - `git show <commit>:<path>` of three manifest lines (a3, e3, e5) works, and their sha256 equals the manifest.
- [ ] Software record on Zenodo (GitHub integration or upload of `git archive`) at the published commit.

## G. Afterwards

- [ ] Upload the data records (`docs/data-package-e6.md` section 4) and reveal the entries.
- [ ] The research note gets the DOIs and links.
- [ ] Any later change comes as new commits and new versions of the records, never as rewrites.
