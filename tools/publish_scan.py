#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Scan of what is to be published (a directory, a tar file, or a git tree) for content that must not go out.

  python3 -I tools/publish_scan.py PATH [PATH ...]          directories or .tar / .tar.gz files
  python3 -I tools/publish_scan.py --git REV [--repo DIR]    the tracked files of a commit (what git archive gives)
  python3 -I tools/publish_scan.py --history [--repo DIR]    every line ever added or removed, all branches

Findings, by class (exit 1 if there is any of the classes that block, 0 otherwise):
  secret     private key blocks, tokens of common services, assignments of passwords, secrets, API keys and tokens,
             mnemonics, receipt salts                                                                      (blocks)
  gaia       Gaia-derived data: Gaia column names (source_id with phot_g_mean_mag, bp_rp, parallax), gaiadr2/3
             table names, VizieR I/345, I/350, I/355; files under runs/plates or runs/ownimg (licence: the package
             is CC BY 4.0, Gaia-derived catalogues are not to be redistributed in it)                       (blocks)
  gaia-code  the same in programs and documents (.py, .sh, .md, .txt, .c, .h, .cu): a query, not data      (reported)
  private    (text files only) home and root paths (/home/<user>, /root/), internal host names (appmdp-NN), private IPv4 addresses,
             GPU UUIDs and serial numbers, e-mail addresses other than the author's                        (reported)
Binary files are scanned as text too (REBOUND archives hold no text, so they give no hits). Only text matches are
found: a check of what goes out, not a proof that nothing else does.
"""

import argparse
import io
import re
import subprocess
import sys
import tarfile
from pathlib import Path

AUTHOR_EMAIL = "e.janssen@medas-computers.de"
RULES = [
    ("secret", "private key block", re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("secret", "service token", re.compile(rb"\b(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|xox[abpr]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|[0-9]{8,10}:AA[A-Za-z0-9_-]{33})\b")),
    ("secret", "secret assignment", re.compile(rb"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)\b[\"']?\s*[=:]\s*[\"']?[A-Za-z0-9/+_.-]{12,}")),
    ("secret", "mnemonic or salt", re.compile(rb"(?i)\b(mnemonic|seed phrase)\b\s*[=:]|\"salt\"\s*:\s*\"[0-9a-f]{16,}\"")),
    ("gaia", "Gaia columns", re.compile(rb"(?i)\bsource_id\b.{0,200}\b(phot_g_mean_mag|bp_rp|parallax_error)\b")),
    ("gaia", "Gaia table", re.compile(rb"(?i)\bgaia(e?dr[23])\.gaia_source\b|\bI/(345|350|355)/")),
    ("private", "home or root path", re.compile(rb"/home/[a-z_][a-z0-9_-]*/|/root/\.[A-Za-z]")),
    ("private", "internal host", re.compile(rb"(?i)\bappmdp-?[0-9]+\b")),
    ("private", "private IPv4", re.compile(rb"\b(10\.(?:[0-9]{1,3}\.){2}[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3})\b(?![.0-9])")),
    ("private", "GPU UUID", re.compile(rb"\bGPU-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")),
    ("private", "e-mail", re.compile(rb"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[a-z]{2,}\b")),
]
GAIA_PATHS = re.compile(r"(^|/)runs/(plates|ownimg)(/|$)")
# the planted test strings of this scanner's own tests: reported as "fixture" (not blocking), only in exactly that file
# and only these exact strings, so that a real secret there would still block
FIXTURES = {"tests/test_publish_scan.py": {b"-----BEGIN OPENSSH PRIVATE KEY-----", b"API_KEY=abcdef0123456789xyz"}}
# version strings of astropy-iers-data look like private IPv4 addresses: 0.2026.10.19.0.52.1
IERS = re.compile(rb"astropy-iers-data==[0-9.]+")


def scan_bytes(name, data, out):
    if GAIA_PATHS.search(name):
        out.append(("gaia", "file of the plate or own-images tools", name, ""))
    data = IERS.sub(b"", data)
    text = b"\0" not in data[:8192]
    code = name.endswith((".py", ".sh", ".md", ".txt", ".c", ".h", ".cu"))
    for cls, what, rx in RULES:
        if cls == "private" and not text:
            continue                          # binary archives: their bytes match e-mail and IP patterns by chance
        for m in rx.finditer(data):
            s = m.group(0)
            if what == "e-mail" and (s.decode(errors="replace") == AUTHOR_EMAIL or s.startswith(b"+@")):
                continue
            line = data.count(b"\n", 0, m.start()) + 1
            c = "gaia-code" if cls == "gaia" and code else cls      # a query in a program is not Gaia data
            if cls == "secret" and any(name.endswith(f) and s in fx for f, fx in FIXTURES.items()):
                c = "fixture"
            out.append((c, what, f"{name}:{line}", s[:80].decode(errors="replace")))


def scan_archive_or_bytes(name, data, out, depth=0):
    """Tar files (also .tar.gz and tars inside tars, up to 4 levels) are opened and their files scanned one by one;
    anything else is scanned as bytes. A record directory holds its data in tar files (tools/pack_record.py), so a tar
    must never be scanned as raw bytes: its binary headers would switch off the checks for private details."""
    if depth < 4 and len(data) >= 18:          # the smallest gzip stream
        try:
            t = tarfile.open(fileobj=io.BytesIO(data), mode="r:*")
        except (tarfile.TarError, EOFError, OSError):
            t = None
        if t is not None:
            with t:
                for m in t.getmembers():
                    if m.isfile():
                        scan_archive_or_bytes(f"{name}:{m.name}", t.extractfile(m).read(), out, depth + 1)
            return
    scan_bytes(name, data, out)


def scan_path(p, out):
    p = Path(p)
    if p.is_dir():
        for f in sorted(p.rglob("*")):
            if f.is_file():
                scan_archive_or_bytes(str(f.relative_to(p.parent)), f.read_bytes(), out)
    else:
        scan_archive_or_bytes(p.name if tarfile.is_tarfile(p) else str(p), p.read_bytes(), out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--git")
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    out = []
    if a.git:
        tar = subprocess.run(["git", "-C", a.repo, "archive", "--format=tar", a.git], capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(tar)) as t:
            for m in t.getmembers():
                if m.isfile():
                    scan_bytes(f"{a.git}:{m.name}", t.extractfile(m).read(), out)
    if a.history:
        log = subprocess.run(["git", "-C", a.repo, "log", "--all", "-p", "--text", "--no-color", "--no-ext-diff", "--format=commit %h"],
                             capture_output=True, check=True).stdout
        commit, path = "?", "?"
        for raw in log.split(b"\n"):
            if raw.startswith(b"commit "):
                commit = raw[7:].decode()
            elif raw.startswith(b"+++ b/"):
                path = raw[6:].decode(errors="replace")
            elif raw[:1] in (b"+", b"-") and not raw.startswith((b"+++", b"---")):
                scan_bytes(f"{commit}:{path}", raw[1:], out)
    for p in a.paths:
        scan_path(p, out)
    blocking = [x for x in out if x[0] in ("secret", "gaia")]
    seen = {}
    for cls, what, where, text in out:
        seen.setdefault((cls, what, text), []).append(where)
    for (cls, what, text), wheres in sorted(seen.items()):
        print(f"{cls:8s} {what:22s} {text!r:60.60s} {len(wheres):4d}x  e.g. {wheres[0]}")
    print(f"== {len(out)} findings, {len(blocking)} blocking (secret, gaia)")
    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
