#!/bin/sh
# MEDAS p9-search, paired long runs (seeds 110-112), group V5: the check before the jobs (run by run-all.sh, or alone: sh check.sh).
# Runs the jobs of check/EXPECTED on the GPU with bin/p9gpu and compares each result hash with the one computed
# on the reference machine (p9gpu's CPU twin, which gives the GPU's bits). Exit code 0 only if all match.
#   regression  the 32 confirmed numerical losses of the fixed step (close flybys) with the smooth transition
#   deep        4 Neptune flybys at 0.1 to 1.6 planet radii (up to 2^21 sub-steps, 2 collisions)
#   <job>       the start values of each job over 10,000 years (with the job's settings)
#   <job>-chain the same 10,000 years as two segments of 5,000 years joined by bin/p9sim last (the
#               segment mechanism of the jobs)
set -u
cd "$(dirname "$0")"
. check/regression.env
export P9GPU_MODE=${P9EQUIV_MODE:-gpu} P9GPU_REAL=double  # P9EQUIV_MODE=cpu: for testing the package only
unset P9_ENCOUNTER_REMOVE P9_J2 P9_CAPPED_OUT P9_SUBSTEPS_OUT P9_FLYBY_OUT P9_REMOVED_OUT
GPU=bin/p9gpu
SIM=bin/p9sim
sha() { sha256sum "$1" | cut -d' ' -f1; }
say() { printf '%s\n' "$*"; }
child=""
trap '[ -n "$child" ] && kill -TERM "$child" 2>/dev/null; exit 130' INT TERM HUP
runbg() { "$@" & child=$!; wait "$child"; rc=$?; child=""; return $rc; }
fail=0
mkdir -p check/out
say "== check, package $(cat PACKAGE-VERSION), $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "mode: $P9GPU_MODE"
. ./select-gpu.sh
[ "$P9GPU_MODE" = cpu ] || say "gpu: $(nvidia-smi -i "$CUDA_VISIBLE_DEVICES" --query-gpu=name,uuid,driver_version,compute_cap --format=csv,noheader)"
say "p9gpu: $($GPU version) sha256 $(sha $GPU)"
for f in bin/p9gpu bin/p9sim; do
  [ "$(sha "$f")" = "$(cut -d' ' -f1 "bin/SHA256-$(basename "$f")")" ] || { say "$f does not match its sha256"; exit 2; }
done
# profile -> environment (job:<name>: jobs/<name>/params.env)
envfor() {
  case "$1" in
    regression) echo "P9_ENCOUNTER_METHOD=smooth P9_ENCOUNTER_RADII=$REG_RADII P9_COLLISION_RADII=$REG_COLLISION P9_PLANET_SUBSTEPS=8 P9_R_IN=5" ;;
    deep) echo "P9_ENCOUNTER_METHOD=smooth P9_ENCOUNTER_RADII=1=3.1036 P9_COLLISION_RADII=1=1.655371e-04 P9_PLANET_SUBSTEPS=8 P9_R_IN=5" ;;
    job:*) ( . "jobs/${1#job:}/params.env"; echo "P9_ENCOUNTER_METHOD=$P9_ENCOUNTER_METHOD P9_ENCOUNTER_RADII=$P9_ENCOUNTER_RADII P9_COLLISION_RADII=$P9_COLLISION_RADII P9_PLANET_SUBSTEPS=$P9_PLANET_SUBSTEPS P9_R_IN=$P9_R_IN" ) ;;
  esac
}
# check/EXPECTED: name profile input t_mid t_end expected_result_sha256 (t_mid "-": one segment; else two joined)
while read -r name profile input t_mid t_end expected; do
  case "$name" in ''|'#'*) continue ;; esac
  o=check/out/$name
  rm -f "$o.out" "$o.sa" "$o-a.sa" "$o-b-in.sa"
  if [ "$t_mid" = - ]; then
    runbg env $(envfor "$profile") "$GPU" run "$input" "$t_end" 1 "$o.sa" > "$o.out" 2> "$o.err"
  else
    runbg env $(envfor "$profile") "$GPU" run "$input" "$t_mid" 1 "$o-a.sa" > /dev/null 2> "$o.err" &&
      runbg "$SIM" last "$o-a.sa" "$o-b-in.sa" > /dev/null &&
      runbg env $(envfor "$profile") "$GPU" run "$o-b-in.sa" "$t_end" 1 "$o.sa" > "$o.out" 2>> "$o.err"
  fi
  line=$(grep '^result_sha256=' "$o.out" 2> /dev/null) || line=""
  if [ -z "$line" ]; then say "$name: FAILED (see $o.err)"; fail=1; continue; fi
  got=$(printf '%s' "$line" | sed 's/^result_sha256=\([0-9a-f]*\).*/\1/')
  wall=$(printf '%s' "$line" | sed 's/.*wall_s=\([0-9.]*\).*/\1/')
  if [ "$got" = "$expected" ]; then say "$name: SAME ($got, $wall s)"; else say "$name: DIFFERENT $got, expected $expected"; fail=1; fi
done < check/EXPECTED
if [ $fail = 0 ]; then say "== ALL SAME"; else say "== DIFFERENCES OR FAILURES"; fi
exit $fail
