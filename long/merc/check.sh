#!/bin/sh
# MEDAS p9-search, paired long runs (seeds 110-112), group M: the check before the slices (run by run-all.sh, or alone: sh check.sh).
# Runs the cases of check/EXPECTED with bin/p9sim (MERCURIUS) and compares each result hash with the one computed
# on the reference machine with the same binary. Exit code 0 only if all match.
#   <job>       the start values of the first slice of each seed over 10,000 years
#   <job>-chain the same 10,000 years as two segments of 5,000 years joined by bin/p9sim last
#   <job>-1myr  the first slice of seed 110 over 1 million years (close encounters in MERCURIUS' IAS15 zone)
set -u
cd "$(dirname "$0")"
SIM=bin/p9sim
sha() { sha256sum "$1" | cut -d' ' -f1; }
say() { printf '%s\n' "$*"; }
child=""
trap '[ -n "$child" ] && kill -TERM "$child" 2>/dev/null; exit 130' INT TERM HUP
runbg() { "$@" & child=$!; wait "$child"; rc=$?; child=""; return $rc; }
fail=0
mkdir -p check/out
say "== check, package $(cat PACKAGE-VERSION), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//'), $(nproc) threads; glibc $(getconf GNU_LIBC_VERSION 2>/dev/null | awk '{print $2}')"
say "p9sim: sha256 $(sha $SIM)"
[ "$(sha $SIM)" = "$(cut -d' ' -f1 bin/SHA256-p9sim)" ] || { say "bin/p9sim does not match its sha256"; exit 2; }
# check/EXPECTED: name job t_mid t_end expected_result_sha256 (t_mid "-": one segment; else two joined)
while read -r name job t_mid t_end expected; do
  case "$name" in ''|'#'*) continue ;; esac
  ( . "jobs/$job/params.env"; export P9_R_IN P9_ENCOUNTER_METHOD P9_ENCOUNTER_REMOVE
    unset P9_ENCOUNTER_RADII P9_COLLISION_RADII P9_PLANET_SUBSTEPS P9_J2 P9_FLYBY_OUT P9_REMOVED_OUT
    o=check/out/$name
    rm -f "$o.out" "$o.sa" "$o-a.sa" "$o-b-in.sa"
    if [ "$t_mid" = - ]; then
      "$SIM" run "jobs/$job/input.sa" "$t_end" 1 "$o.sa" > "$o.out" 2> "$o.err"
    else
      "$SIM" run "jobs/$job/input.sa" "$t_mid" 1 "$o-a.sa" > /dev/null 2> "$o.err" &&
        "$SIM" last "$o-a.sa" "$o-b-in.sa" > /dev/null &&
        "$SIM" run "$o-b-in.sa" "$t_end" 1 "$o.sa" > "$o.out" 2>> "$o.err"
    fi ) &
  child=$!; wait "$child"; child=""
  o=check/out/$name
  line=$(grep '^result_sha256=' "$o.out" 2> /dev/null) || line=""
  if [ -z "$line" ]; then say "$name: FAILED (see $o.err)"; fail=1; continue; fi
  got=$(printf '%s' "$line" | sed 's/^result_sha256=\([0-9a-f]*\).*/\1/')
  wall=$(printf '%s' "$line" | sed 's/.*wall_s=\([0-9.]*\).*/\1/')
  if [ "$got" = "$expected" ]; then say "$name: SAME ($got, $wall s)"; else say "$name: DIFFERENT $got, expected $expected"; fail=1; fi
done < check/EXPECTED
if [ $fail = 0 ]; then say "== ALL SAME"; else say "== DIFFERENCES OR FAILURES"; fi
exit $fail
