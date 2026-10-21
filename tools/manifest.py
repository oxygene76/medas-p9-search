#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Manifests for the MEDAS notary: one JSON file with the SHA-256 of every file that belongs to a statement.

  python tools/manifest.py make SPEC.json OUT.json      write the manifest (and print its SHA-256)
  python tools/manifest.py verify MANIFEST.json [--root DIR] [--repo NAME=DIR ...]
                                                         check every listed file against its hash

The SHA-256 of the manifest file (its exact bytes) is what goes into the notary as the entry's
content (the web app: Submit, "A file"; docs/notary.md). After the reveal anyone checks each file on
its own: its sha256 is in the manifest, and the manifest's sha256 is the revealed content digest.

SPEC.json:
  {"title": "...", "statement": "...",
   "repositories": {"medas-p9-search": {"dir": ".", "url": "https://..."}},   (dir relative to SPEC)
   "files": [{"repo": "medas-p9-search", "path": "docs/x.md", "role": "...", "at": "47127ba"},  (git: the
              file as committed at that commit; default: the commit the repository is at, file unchanged)
             {"repo": "medas-p9-search", "path": "runs/val/x/result.json", "role": "...", "git": false},
             {"glob": "runs/val/merc/part*/result.json", "repo": "...", "role": "...", "git": false}]}
Files with "git": false (results, packages, reports) are not in the repository; they are published as
an archive at the reveal, under the same paths.

The manifest lists per file: repo, path, role, sha256, bytes, and for files from git the full commit and
the git blob id (git show <commit>:<path> gives the bytes). Paths are relative to their repository; no
local paths, user or host names. JSON with sorted keys, one space indent, UTF-8, a final newline; the
file is written once and must not be re-saved (any change changes its hash).
"""

import argparse
import datetime
import glob as globmod
import hashlib
import json
import subprocess
import sys
from pathlib import Path

VERSION = 1


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def git(repo_dir, *args, binary=False):
    r = subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode().strip()


def make(a):
    spec_path = Path(a.spec).resolve()
    spec = json.loads(spec_path.read_text())
    repos = {}
    for name, r in spec["repositories"].items():
        d = (spec_path.parent / r["dir"]).resolve()
        head = git(d, "rev-parse", "HEAD")
        dirty = git(d, "status", "--porcelain", "--untracked-files=no")
        repos[name] = {"dir": d, "head": head, "dirty": bool(dirty)}
    files = []
    for item in spec["files"]:
        repo = item["repo"]
        d = repos[repo]["dir"]
        paths = sorted(str(Path(p).relative_to(d)) for p in globmod.glob(str(d / item["glob"]))) if "glob" in item else [item["path"]]
        if not paths:
            sys.exit(f"no file for {item}")
        for path in paths:
            entry = {"repo": repo, "path": path, "role": item["role"]}
            if item.get("git", True):
                commit = git(d, "rev-parse", item.get("at", "HEAD"))
                data = git(d, "show", f"{commit}:{path}", binary=True)
                if "at" not in item:
                    if (d / path).read_bytes() != data:
                        sys.exit(f"{repo}/{path} differs from its committed version: commit first")
                entry["git"] = {"commit": commit, "blob": git(d, "rev-parse", f"{commit}:{path}")}
            else:
                data = (d / path).read_bytes()
                if git(d, "ls-files", path):
                    sys.exit(f"{repo}/{path} is in git: list it with git")
                entry["git"] = None
            entry["sha256"] = sha256_bytes(data)
            entry["bytes"] = len(data)
            files.append(entry)
    dirty = [n for n, r in repos.items() if r["dirty"]]
    if dirty:
        sys.exit(f"uncommitted changes in {dirty}: commit first")
    manifest = {
        "manifest": "medas-p9-search notary manifest",
        "manifest_version": VERSION,
        "title": spec["title"],
        "statement": spec["statement"],
        "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hash": "sha256",
        "how_to_verify": ("For each file: sha256 of its bytes must equal 'sha256'. Files with 'git' are in the repository: "
                          "'git show <commit>:<path>' gives them (their git blob id is 'blob'). Files without 'git' are in "
                          "the archive published with the reveal, under the same path. The SHA-256 of this manifest file "
                          "is the content digest of the notary entry. Tool: tools/manifest.py verify."),
        "repositories": {n: {"url": spec["repositories"][n].get("url"), "commit": r["head"]} for n, r in repos.items()},
        "files": files,
    }
    text = json.dumps(manifest, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists: a manifest is written once")
    out.write_bytes(text.encode("utf-8"))
    print(f"{out}: {len(files)} files, {sum(f['bytes'] for f in files)} bytes listed")
    print(f"manifest sha256 {sha256_bytes(text.encode('utf-8'))}")


def verify(a):
    raw = Path(a.manifest).read_bytes()
    m = json.loads(raw)
    print(f"manifest sha256 {sha256_bytes(raw)} ({m['title']})")
    dirs = {k: Path(v) for k, v in (x.split("=", 1) for x in a.repo)}
    bad = 0
    for f in m["files"]:
        d = dirs.get(f["repo"], Path(a.root))
        if f["git"]:
            try:
                data = git(d, "show", f"{f['git']['commit']}:{f['path']}", binary=True)
            except subprocess.CalledProcessError:
                data = (d / f["path"]).read_bytes() if (d / f["path"]).exists() else None
        else:
            p = d / f["path"]
            data = p.read_bytes() if p.exists() else None
        ok = data is not None and sha256_bytes(data) == f["sha256"] and len(data) == f["bytes"]
        bad += not ok
        if not ok or a.verbose:
            print(f"{'OK  ' if ok else 'MISSING' if data is None else 'DIFFERENT'} {f['repo']}/{f['path']}")
    print(f"{len(m['files']) - bad} of {len(m['files'])} files match")
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make"); m.add_argument("spec"); m.add_argument("out")
    v = sub.add_parser("verify"); v.add_argument("manifest"); v.add_argument("--root", default=".")
    v.add_argument("--repo", action="append", default=[], metavar="NAME=DIR"); v.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    {"make": make, "verify": verify}[a.cmd](a)


if __name__ == "__main__":
    main()
