#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Median, 99 % value and maximum of the sub-steps per step with sub-steps, from P9_SUBSTEPS_OUT of p9gpu.

  python tools/substeps_hist.py hist.tsv [more.tsv ...]
"""

import sys

for path in sys.argv[1:]:
    rows = [tuple(map(int, l.split("\t"))) for l in open(path).read().splitlines()[1:]]
    total = sum(c for _, c in rows)
    work = sum(n * c for n, c in rows)

    def q(f):
        acc = 0
        for n, c in rows:
            acc += c
            if acc >= f * total:
                return n
        return rows[-1][0]

    big = sum(n * c for n, c in rows if n >= 4096)
    print(f"{path}: {total} steps with sub-steps, {work} sub-steps; n median {q(0.5)}, 99 % {q(0.99)}, maximum {rows[-1][0] if rows else 0}; "
          f"share of the sub-steps in steps with n >= 4096: {big / work if work else 0:.1%}")
