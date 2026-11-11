#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Packs one record of the data package (docs/data-package-proposal.md section 2, docs/data-package-e6.md) and checks
it: uncompressed tar files, one per part, written reproducibly, and MANIFEST.sha256 over the files inside them and over
the tar files and top files themselves.

  build/venv/bin/python -I tools/pack_record.py pack SPEC.json OUTDIR
  build/venv/bin/python -I tools/pack_record.py verify OUTDIR

SPEC.json:
  {"record": "medas-p9-search-production-1.0.0",
   "top": [{"src": "path/README.md", "name": "README.md"}, ...],                  files next to the tar files
   "parts": [{"tar": "runs-production.tar",
              "add": [{"src": "dir or file", "arcname": "runs/production", "exclude": ["*.pid"]}, ...]}, ...]}
Paths in SPEC are relative to the SPEC file. OUTDIR must not exist.

Reproducible tar: members sorted by path, mtime fixed to SOURCE_DATE (default 2026-01-01T00:00:00Z), owner and group 0
with empty names, modes 0644 for files and 0755 for directories (0755 for files that were executable), no other
metadata. The same sources give the same bytes.

MANIFEST.sha256 (sha256sum format, sorted):
  <sha256>  <part.tar>:<path inside>      every file inside every tar
  <sha256>  <part.tar>                    every tar file
  <sha256>  <top file>                    every top file
verify reads every tar without unpacking to disk and checks every line, and that nothing is unlisted.
"""

import argparse
import datetime
import fnmatch
import hashlib
import json
import os
import sys
import tarfile
from pathlib import Path

SOURCE_DATE = int(datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc).timestamp())


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def members(add, base):
    """(arcname, path) for one "add" entry, files only, sorted."""
    src = (base / add["src"]).resolve()
    excl = add.get("exclude", [])
    out = []
    if src.is_file():
        out.append((add["arcname"], src))
    else:
        for root, dirs, files in os.walk(src):
            dirs.sort()
            for f in sorted(files):
                p = Path(root) / f
                rel = p.relative_to(src).as_posix()
                if any(fnmatch.fnmatch(f, e) or fnmatch.fnmatch(rel, e) for e in excl):
                    continue
                if p.is_symlink():
                    sys.exit(f"{p}: symbolic links are not packed")
                out.append((f"{add['arcname']}/{rel}", p))
    return out


def write_tar(path, items, mtime):
    """items: [(arcname, path)]; directories are added implicitly, sorted with the files."""
    names = {}
    for arc, p in items:
        if arc in names:
            sys.exit(f"{arc} twice in {path.name}")
        names[arc] = p
        parts = arc.split("/")
        for i in range(1, len(parts)):
            names.setdefault("/".join(parts[:i]) + "/", None)
    lines = []
    with tarfile.open(path, "w", format=tarfile.PAX_FORMAT) as t:
        for arc in sorted(names):
            p = names[arc]
            ti = tarfile.TarInfo(arc.rstrip("/"))
            ti.mtime, ti.uid, ti.gid, ti.uname, ti.gname = mtime, 0, 0, "", ""
            if p is None:
                ti.type, ti.mode = tarfile.DIRTYPE, 0o755
                t.addfile(ti)
                continue
            ti.size = p.stat().st_size
            ti.mode = 0o755 if os.access(p, os.X_OK) else 0o644
            with open(p, "rb") as f:
                t.addfile(ti, f)
            lines.append((sha_file(p), f"{path.name}:{arc}"))
    return lines


def pack(a):
    spec_path = Path(a.spec).resolve()
    base = spec_path.parent
    spec = json.loads(spec_path.read_text())
    out = Path(a.outdir)
    if out.exists():
        sys.exit(f"{out} exists")
    out.mkdir(parents=True)
    mtime = int(os.environ.get("SOURCE_DATE_EPOCH", SOURCE_DATE))
    lines = []
    for part in spec["parts"]:
        items = [m for add in part["add"] for m in members(add, base)]
        tpath = out / part["tar"]
        lines += write_tar(tpath, items, mtime)
        lines.append((sha_file(tpath), part["tar"]))
        print(f"{part['tar']}: {len(items)} files, {tpath.stat().st_size:,} bytes", flush=True)
    for top in spec.get("top", []):
        dst = out / top["name"]
        dst.write_bytes((base / top["src"]).read_bytes())
        lines.append((sha_file(dst), top["name"]))
    text = "".join(f"{h}  {n}\n" for h, n in sorted(lines, key=lambda x: x[1]))
    (out / "MANIFEST.sha256").write_text(text)
    print(f"MANIFEST.sha256: {len(lines)} lines, sha256 {hashlib.sha256(text.encode()).hexdigest()}")


def verify(a):
    out = Path(a.outdir)
    want = {}
    for line in (out / "MANIFEST.sha256").read_text().splitlines():
        h, n = line.split("  ", 1)
        want[n] = h
    bad, seen = 0, set()
    for f in sorted(out.iterdir()):
        if f.name == "MANIFEST.sha256":
            continue
        seen.add(f.name)
        if want.get(f.name) != sha_file(f):
            print(f"FAIL {f.name}"); bad += 1
        if f.suffix == ".tar":
            with tarfile.open(f) as t:
                for m in t:
                    if not m.isfile():
                        continue
                    key = f"{f.name}:{m.name}"
                    seen.add(key)
                    h = hashlib.sha256(t.extractfile(m).read()).hexdigest()
                    if want.get(key) != h:
                        print(f"FAIL {key}"); bad += 1
    for n in sorted(set(want) - seen):
        print(f"MISSING {n}"); bad += 1
    print(f"{len(want) - bad} of {len(want)} lines match" if bad == 0 else f"{bad} problems")
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("spec"); p.add_argument("outdir")
    v = sub.add_parser("verify"); v.add_argument("outdir")
    a = ap.parse_args()
    {"pack": pack, "verify": verify}[a.cmd](a)


if __name__ == "__main__":
    main()
