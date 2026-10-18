#!/bin/sh
# MEDAS p9-search: reproducibility check on a second machine.
#
#   sh run-check.sh            (in the unpacked package; needs sh, make, a C
#                               compiler (cc, gcc or clang) and tar)
#   CC=clang OPT=-O2 sh run-check.sh   (other compiler or optimisation level)
#
# Builds p9sim from the included sources (REBOUND 5.2.2, checked by sha256),
# runs the jobs in jobs/ and compares each result with the hash expected in
# EXPECTED. Prints a report to send back; exit code 0 if every hash matches.
# Nothing is sent anywhere, nothing outside this directory is changed.
set -eu
cd "$(dirname "$0")"
CC=${CC:-cc}
OPT=${OPT:--O3}
REPORT=report.txt
: > "$REPORT"
say() { printf '%s\n' "$*" | tee -a "$REPORT"; }

say "== MEDAS p9-search check, package $(cat PACKAGE-VERSION)"
say "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "system: $(uname -s) $(uname -r) $(uname -m)"
if [ -r /proc/cpuinfo ]; then say "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//')"; fi
if command -v sysctl >/dev/null 2>&1; then c=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || true); [ -n "$c" ] && say "cpu: $c"; fi
say "compiler: $($CC --version 2>&1 | head -1)"
say "flags: OPT=$OPT (always -fno-fast-math -ffp-contract=off, see Makefile)"

# REBOUND sources, checked
mkdir -p third_party
tar -xzf third_party-src/rebound-5.2.2.tar.gz -C third_party
make -s CC="$CC" OPT="$OPT" VARIANT=check >/dev/null
P=./build/check/p9sim
say "rebound tarball: $($P sha256 third_party-src/rebound-5.2.2.tar.gz | cut -d' ' -f1) (expected 86038080c4392c8c19c4df2004d1804b30ca2aebd3c0329bfd1b02afc41d6eda)"
[ "$($P sha256 third_party-src/rebound-5.2.2.tar.gz | cut -d' ' -f1)" = 86038080c4392c8c19c4df2004d1804b30ca2aebd3c0329bfd1b02afc41d6eda ] || { say "REBOUND archive does not match"; exit 2; }

fail=0
# EXPECTED: name t_end snapshots input_sha256 expected_result_sha256
while read -r name t_end snaps input_sha expected; do
  case "$name" in ''|'#'*) continue ;; esac
  got_in=$($P sha256 "jobs/$name/input.sa" | cut -d' ' -f1)
  if [ "$got_in" != "$input_sha" ]; then say "$name: input.sa does not match its sha256"; fail=1; continue; fi
  line=$($P run "jobs/$name/input.sa" "$t_end" "$snaps" "jobs/$name/output.sa" 2>/dev/null | grep '^result_sha256=')
  got=$(printf '%s' "$line" | sed 's/^result_sha256=\([0-9a-f]*\).*/\1/')
  wall=$(printf '%s' "$line" | sed 's/.*wall_s=\([0-9.]*\).*/\1/')
  if [ "$got" = "$expected" ]; then verdict=SAME; else verdict=DIFFERENT; fail=1; fi
  say "$name: $verdict result_sha256=$got wall_s=$wall"
  [ "$verdict" = SAME ] || say "  expected $expected"
done < EXPECTED

if [ $fail = 0 ]; then say "== ALL SAME"; else say "== DIFFERENCES (see above)"; fi
say "(this report is also in $REPORT)"
exit $fail
