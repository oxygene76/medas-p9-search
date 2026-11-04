#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The commits and tags the notary entries refer to, and what publishing them makes public.

  python3 -I tools/notary_refs.py ENTRY=MANIFEST [ENTRY=MANIFEST ...] [--pending ENTRY ...] [--repo DIR]

For each manifest (tools/manifest.py): the commits of "repositories", of the files with "git", and every commit id
named in its text (7 to 40 hex digits that git resolves to a commit). Prints Markdown:
- per commit: date, the entries that refer to it and how, whether main contains it, the branches that do, the tags on
  it, and a proposed tag name (notary-<first entry>-<commit>);
- the tips: the referenced commits that no other referenced commit contains. Publishing main and these makes every
  referenced commit reachable;
- the closure: how many commits become public with main and the referenced commits (all their ancestors), how many
  stay private, and the existing tags in the closure.
--pending marks entries that are prepared but not yet on chain.
"""

import argparse
import json
import re
import subprocess


def git(repo, *a):
    r = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifests", nargs="+", metavar="ENTRY=MANIFEST")
    ap.add_argument("--pending", nargs="*", default=[])
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    R = a.repo
    refs = {}                                           # full commit -> {entry: set(how)}
    order = []
    for spec in a.manifests:
        entry, path = spec.split("=", 1)
        order.append(entry)
        m = json.load(open(path))

        def add(c, how):
            rc, full = git(R, "rev-parse", "--verify", "-q", c + "^{commit}")
            if rc == 0:
                refs.setdefault(full, {}).setdefault(entry, set()).add(how)
        for repo, r in (m.get("repositories") or {}).items():
            add(r["commit"], f"repository {repo}")
        for f in m["files"]:
            if f.get("git"):
                add(f["git"]["commit"], "files")
        text = json.dumps({k: v for k, v in m.items() if k != "files"}) + " " + " ".join(f"{f.get('role', '')} {f['path']}" for f in m["files"])
        for h in set(re.findall(r"\b[0-9a-f]{7,40}\b", text)):
            add(h, "named")
    tags = {}
    for t in git(R, "tag", "-l")[1].split():
        tags.setdefault(git(R, "rev-list", "-n1", t)[1], []).append(t)

    def date(c):
        return int(git(R, "log", "-1", "--format=%ct", c)[1])
    commits = sorted(refs, key=date)
    pend = set(a.pending)
    print("| commit | date | entries (how) | in main | branches | tags | proposed tag |")
    print("|---|---|---|---|---|---|---|")
    for c in commits:
        ents = [e for e in order if e in refs[c]]
        how = "; ".join(f"{e}{' (pending)' if e in pend else ''}: {', '.join(sorted(refs[c][e]))}" for e in ents)
        in_main = git(R, "merge-base", "--is-ancestor", c, "main")[0] == 0
        br = sorted(b.strip("*+ ").strip() for b in git(R, "branch", "--contains", c)[1].splitlines())
        d = git(R, "log", "-1", "--format=%cs", c)[1]
        print(f"| `{c[:12]}` | {d} | {how} | {'yes' if in_main else 'no'} | {', '.join(br)} | {', '.join(tags.get(c, [])) or '–'} | `notary-{ents[0].split()[0]}-{c[:7]}` |")
    tips = [c for c in commits if not any(c != d and git(R, "merge-base", "--is-ancestor", c, d)[0] == 0 for d in commits)]
    print()
    print("Tips (each referenced commit is one of these or an ancestor of one):")
    for c in tips:
        print(f"- `{c[:12]}` {git(R, 'log', '-1', '--format=%cs %s', c)[1][:100]}")
    pub = set(git(R, "rev-list", "main", *commits)[1].split())
    allc = set(git(R, "rev-list", "--all")[1].split())
    print()
    print(f"Closure: main and the referenced commits with all their ancestors are {len(pub)} of {len(allc)} commits; "
          f"{len(allc - pub)} stay private.")
    in_closure = sorted(t for c, ts in tags.items() if c in pub for t in ts)
    print(f"Existing tags in the closure: {', '.join(in_closure) or '–'}; outside: "
          f"{', '.join(sorted(t for c, ts in tags.items() if c not in pub for t in ts)) or '–'}.")


if __name__ == "__main__":
    main()
