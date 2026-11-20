#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""The exception list of the host-name rule (2026-11-18) and the account-name rule (2026-11-20): every file that holds a
known host name or the account name in an account context, and cannot change.

  python3 -I tools/host_exceptions.py OUT.tsv --manifest ENTRY=MANIFEST ... --repo NAME=DIR ... --history REV ...

Two kinds of files, matched later by the sha256 of their bytes (tools/publish_scan.py, class host-listed):
- **notarised:** each manifest itself (its bytes are the content of the entry), each file of it, and each member of a
  tar file in it (also tars inside tars), exactly as listed (git files from their commit);
- **published history:** each file version reachable from the given commits (the tips of the last entry), as it is
  there; publishing them publishes these versions, and the history is not rewritten.
A host name in a path is written as <host>; the list itself holds none. Columns: sha256, entry, repo, path.
"""
import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_scan import HOSTS, host_matches  # noqa: E402


def has_host(data):
    return any(True for _ in host_matches(data))


def mask(path):
    for _, _, rx in HOSTS:
        path = rx.sub(b"<host>", path.encode()).decode()
    return path


def members(name, data, depth=0):
    """(name, bytes) of the file and, for a tar, of every member (recursively, up to 4 levels)."""
    yield name, data
    if depth < 4 and len(data) >= 18:
        try:
            t = tarfile.open(fileobj=io.BytesIO(data), mode="r:*")
        except (tarfile.TarError, EOFError, OSError):
            return
        with t:
            for m in t.getmembers():
                if m.isfile():
                    yield from members(f"{name}!{m.name}", t.extractfile(m).read(), depth + 1)


def git(d, *a):
    return subprocess.run(["git", "-C", str(d), *a], capture_output=True, check=True).stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--manifest", action="append", default=[], metavar="ENTRY=MANIFEST")
    ap.add_argument("--repo", action="append", default=[], metavar="NAME=DIR")
    ap.add_argument("--history", nargs="*", default=[], metavar="REV")
    ap.add_argument("--history-repo", default=".")
    a = ap.parse_args()
    dirs = dict(x.split("=", 1) for x in a.repo)
    rows = {}
    for spec in a.manifest:
        entry, mpath = spec.split("=", 1)
        mbytes = Path(mpath).read_bytes()
        if has_host(mbytes):
            rows.setdefault(hashlib.sha256(mbytes).hexdigest(), (entry, "medas-p9-search", "runs/notary/" + mask(Path(mpath).name)))
        for f in json.loads(mbytes)["files"]:
            d = Path(dirs[f["repo"]])
            data = git(d, "show", f"{f['git']['commit']}:{f['path']}") if f["git"] else (d / f["path"]).read_bytes()
            for name, b in members(f["path"], data):
                if has_host(b):
                    rows.setdefault(hashlib.sha256(b).hexdigest(), (entry, f["repo"], mask(name)))
    if a.history:
        objs = git(a.history_repo, "rev-list", "--objects", *a.history)
        cat = subprocess.Popen(["git", "-C", a.history_repo, "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        for oid, path in (l.split(b" ", 1) for l in objs.splitlines() if b" " in l):
            cat.stdin.write(oid + b"\n"); cat.stdin.flush()
            hdr = cat.stdout.readline().split(); data = cat.stdout.read(int(hdr[2])); cat.stdout.read(1)
            if hdr[1] != b"blob":
                continue
            for name, b in members(path.decode(errors="replace"), data):
                if has_host(b):
                    rows.setdefault(hashlib.sha256(b).hexdigest(), ("history", "medas-p9-search", mask(name)))
        cat.stdin.close(); cat.wait()
    with open(a.out, "w") as o:
        o.write("# Files that hold a known host name (rule of 2026-11-18) or the account name (rule of 2026-11-20) and stay unchanged.\n")
        o.write("# Made by tools/host_exceptions.py; matched by the sha256 of the bytes (tools/publish_scan.py, host-listed).\n")
        o.write(f"# entries: {', '.join(s.split('=')[0] for s in a.manifest)}; history: every file version reachable from "
                f"{' '.join(a.history)}. A host name in a path is written as <host>.\n")
        o.write("# sha256\tentry\trepo\tpath\n")
        order = {s.split("=")[0]: i for i, s in enumerate(a.manifest)}
        for sha, (entry, repo, path) in sorted(rows.items(), key=lambda kv: (order.get(kv[1][0], 99), kv[1][1], kv[1][2])):
            o.write(f"{sha}\t{entry}\t{repo}\t{path}\n")
    print(f"{a.out}: {len(rows)} files")


if __name__ == "__main__":
    main()
