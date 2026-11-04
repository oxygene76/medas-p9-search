#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Copies RESULTS.tsv of a speed comparison written under a German locale (decimal commas) into a file with decimal
points; the original stays untouched.

  python3 -I convert_results.py results-<host>/RESULTS.tsv          -> results-<host>/RESULTS-C.tsv

Only fields that are a number with a decimal comma ("474,000") are changed, to "474.000"; every other byte stays.
Checks: same number of lines and of fields per line, no other field changed. Reports per column how many fields
were changed, and how many of them end in ",000": speed.sh wrote those with bash printf, which under that locale could
not read its decimal-point input and kept whole seconds only (wall_shell_s, t_start, t_end). wall_s (the program's
own wall time, the measured value) was written as text and is unaffected.
"""
import hashlib
import re
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = src.with_name(src.stem + "-C" + src.suffix)
if dst.exists():
    sys.exit(f"{dst} exists already")
text = src.read_text()
lines = text.split("\n")
head = lines[0].split("\t")
comma = re.compile(r"^-?\d+,\d+$")
changed, whole = {}, {}
out = [lines[0]]
for ln in lines[1:]:
    if not ln:
        out.append(ln)
        continue
    f = ln.split("\t")
    if len(f) != len(head):
        sys.exit(f"a line with {len(f)} fields instead of {len(head)}: {ln[:80]}")
    g = []
    for name, x in zip(head, f):
        if comma.match(x):
            changed[name] = changed.get(name, 0) + 1
            whole[name] = whole.get(name, 0) + x.endswith(",000")
            x = x.replace(",", ".")
        g.append(x)
    out.append("\t".join(g))
new = "\n".join(out)
assert len(new) == len(text) and new.count("\t") == text.count("\t") and new.count("\n") == text.count("\n")
assert re.sub(r"(?<=\d),(?=\d)", ".", text) == new          # nothing but those commas changed
dst.write_text(new)
print(f"{src} (sha256 {hashlib.sha256(text.encode()).hexdigest()[:16]}…, unchanged) -> {dst}")
print(f"{len(lines) - 2} data lines, {len(head)} columns")
for name in head:
    if name in changed:
        print(f"  {name}: {changed[name]} fields with a decimal comma, {whole[name]} of them ',000' (whole seconds only)")
