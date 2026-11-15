#!/bin/sh
# Read-only estimate of the end of set A and set B (package p9bbsets) on the A100, from the per-segment wall times
# (column 4 of segments.tsv). POSIX sh and awk (also mawk). No load: reads three small files and one mtime, nothing
# on the GPU.
#
#   sh tools/estimate_sets.sh [PROD_TSV] [A_TSV] [A_START_UTC] [B_TSV]
#
# Set A: against the production run (same number of test particles, same A100), as before.
# Set B, once it has done segments: the ratio of its wall times so far to the SAME segments of set A and of the
# production run, and from each the end of B in the three variants used for A:
#   [ratio 1.0]          the rest of B takes as long as the reference;
#   [as the last segm.]  the ratio of the last (up to) 3 segments;
#   [as so far]          the ratio of all segments so far.
# The clock for B starts at the end of its last done segment (mtime of its segments.tsv); the running segment is
# counted in full. Before B has a segment: 1.0 to 1.4 times the production run, right after A.
# Of set B only columns 1 (segment) and 4 (wall time) are read, nothing else (no particle numbers, no hashes).
P=${1:-$HOME/runs/prod/p9prod-9a084ed/segments.tsv}
A=${2:-$HOME/runs/sets/p9bbsets-5b05cc3/jobs/BB-A/segments.tsv}
START=${3:-2026-11-12T09:08:16Z}
B=${4:-$HOME/runs/sets/p9bbsets-5b05cc3/jobs/BB-B/segments.tsv}
LATE=${LATE:-2026-11-20T00:00:00Z}
d() { date -u -d "@$1" +"%Y-%m-%d %H:%M UTC"; }
if [ -s "$B" ]; then BFILE=$B; BMTIME=$(date -u -r "$B" +%s); else BFILE=/dev/null; BMTIME=0; fi
awk -F'\t' -v start="$(date -u -d "$START" +%s)" -v bm="$BMTIME" '
  f == 1 { p[$1] = $4; np = $1; next }
  f == 2 { a[$1] = $4; na = $1; next }
  f == 3 { b[$1] = $4; nb = $1; hb = 1; next }
  END {
    for (k = 0; k <= np; k++) P += p[k]
    sa = 0; sp = 0
    for (k = 0; k <= na; k++) { sa += a[k]; sp += p[k] }
    r = sa / sp; m = (na >= 2) ? 3 : na + 1
    for (k = na - m + 1; k <= na; k++) { ra += a[k]; rp += p[k] }
    rr = ra / rp
    rest = 0; for (k = na + 1; k <= np; k++) rest += p[k]
    t0 = start + sa
    printf "info %d %d %.1f %.2f %d %.2f %.2f\n", na + 1, np + 1, sa / 3600, r, m, rr, P / 86400
    if (na < np) {
      printf "A1 %d\nA2 %d\nA3 %d\n", t0 + rest, t0 + rest * rr, t0 + rest * r
    } else printf "Adone %d\n", t0
    aend = t0 + rest
    if (!hb) {
      lo = aend; hi = t0 + rest * (rr > r ? rr : r)
      printf "B %d %d\n", lo + P, hi + 1.4 * P
      exit
    }
    sb = 0; for (k = 0; k <= nb; k++) sb += b[k]
    mb = (nb >= 2) ? 3 : nb + 1
    printf "Binfo %d %d %.1f %d\n", nb + 1, np + 1, sb / 3600, mb
    # reference A: only as far as A has segments
    if (na >= nb) {
      s1 = 0; s2 = 0; for (k = 0; k <= nb; k++) s1 += a[k]
      for (k = nb - mb + 1; k <= nb; k++) { s2 += a[k]; l2 += b[k] }
      ar = sb / s1; arr = l2 / s2
      ra2 = 0; for (k = nb + 1; k <= na; k++) ra2 += a[k]
      if (na == np) printf "BA %.3f %.3f %d %d %d\n", ar, arr, bm + ra2, bm + ra2 * arr, bm + ra2 * ar
      else printf "BAx %.3f %.3f\n", ar, arr
    }
    s1 = 0; s2 = 0; l2 = 0; for (k = 0; k <= nb; k++) s1 += p[k]
    for (k = nb - mb + 1; k <= nb; k++) { s2 += p[k]; l2 += b[k] }
    pr = sb / s1; prr = l2 / s2
    rp2 = 0; for (k = nb + 1; k <= np; k++) rp2 += p[k]
    printf "BP %.3f %.3f %d %d %d\n", pr, prr, bm + rp2, bm + rp2 * prr, bm + rp2 * pr
  }' f=1 "$P" f=2 "$A" f=3 "$BFILE" | while read -r k x y z u v w q; do
  case $k in
    info) echo "set A: $x of $y segments, $z h computed; ratio to the production run: overall $u, last $v segments $w" ;;
    Adone) echo "  A complete (start + computed time: $(d "$x"))" ;;
    A1) echo "  A ends $(d "$x")  [excess gone, ratio 1.0]" ;;
    A2) echo "  A ends $(d "$x")  [as the last segments]" ;;
    A3) echo "  A ends $(d "$x")  [as so far]" ;;
    B) echo "set B right after A (1.0 to 1.4 times the production run): ends between $(d "$x") and $(d "$y")"
       [ "$y" -gt "$(date -u -d "$LATE" +%s)" ] && echo "  NOTE: the late end of B is after $LATE" ;;
    Binfo) echo "set B: $x of $y segments, $z h computed; last done segment ended $(d "$BMTIME")"; MB=$u ;;
    BA) echo "  against set A (same segments): ratio overall $x, last $MB segments $y"
        echo "    B ends $(d "$z")  [ratio 1.0]"
        echo "    B ends $(d "$u")  [as the last segments]"
        echo "    B ends $(d "$v")  [as so far]"
        [ "$z" -gt "$(date -u -d "$LATE" +%s)" ] || [ "$u" -gt "$(date -u -d "$LATE" +%s)" ] || [ "$v" -gt "$(date -u -d "$LATE" +%s)" ] \
          && echo "    NOTE: an end after $LATE" ;;
    BAx) echo "  against set A (same segments): ratio overall $x, last $MB segments $y; no end estimate, A is not complete" ;;
    BP) echo "  against the production run (same segments): ratio overall $x, last $MB segments $y"
        echo "    B ends $(d "$z")  [ratio 1.0]"
        echo "    B ends $(d "$u")  [as the last segments]"
        echo "    B ends $(d "$v")  [as so far]"
        [ "$z" -gt "$(date -u -d "$LATE" +%s)" ] || [ "$u" -gt "$(date -u -d "$LATE" +%s)" ] || [ "$v" -gt "$(date -u -d "$LATE" +%s)" ] \
          && echo "    NOTE: an end after $LATE" ;;
  esac
done
