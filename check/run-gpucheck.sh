#!/bin/sh
# MEDAS p9-search: GPU check of p9gpu (CUDA) on a second machine.
#
#   sh run-gpucheck.sh                 (in the unpacked package)
#
# Needs: sh, make, gcc and g++ (C++17), tar, sha256sum, an NVIDIA GPU with its
# driver (nvidia-smi), and either the CUDA toolkit (nvcc; any version that
# knows the GPU, e.g. 12.x for an L40S) or a driver new enough for the
# included prebuilt binary (CUDA 13.4: driver 580 or newer).
#
# Environment (all optional):
#   NVCC=/usr/local/cuda/bin/nvcc   the CUDA compiler (default: nvcc in PATH, then /usr/local/cuda/bin/nvcc)
#   CUDA_LIB=/usr/local/cuda/lib64  its libraries (default: next to nvcc)
#   USE_PREBUILT=1                  use bin/p9gpu instead of building
#   SKIP_BENCH=1                    leave out the 64,000-particle benchmark
#
# Builds p9gpu from the included sources (REBOUND 5.2.2, checked by sha256),
# runs the jobs in EXPECTED on the GPU (and two of them on the CPU) and
# compares each result with the hash computed on the reference machine; then
# the benchmark and a short speed probe. Prints a report to send back
# (report-gpu.txt); exit code 0 if every hash matches. Nothing is sent
# anywhere, nothing outside this directory is changed.
set -eu
cd "$(dirname "$0")"
REPORT=report-gpu.txt
: > "$REPORT"
say() { printf '%s\n' "$*" | tee -a "$REPORT"; }
sha() { sha256sum "$1" | cut -d' ' -f1; }

say "== MEDAS p9-search GPU check, package $(cat PACKAGE-VERSION)"
say "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "system: $(uname -s) $(uname -r) $(uname -m)"
[ -r /proc/cpuinfo ] && say "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//') ($(grep -c ^processor /proc/cpuinfo) threads)"
say "gcc: $(gcc --version 2>&1 | head -1)"
say "g++: $(g++ --version 2>&1 | head -1)"
command -v nvidia-smi >/dev/null 2>&1 || { say "no nvidia-smi: is the NVIDIA driver installed?"; exit 2; }
say "gpu: $(nvidia-smi --query-gpu=name,driver_version,compute_cap,memory.total,clocks.max.sm,power.limit,ecc.mode.current,persistence_mode --format=csv,noheader | head -1)"
say "     (name, driver, compute capability, memory, max SM clock, power limit, ECC, persistence)"
[ "$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)" -gt 1 ] && say "note: several GPUs; CUDA uses device 0 (set CUDA_VISIBLE_DEVICES to choose)"

# REBOUND sources, checked
REB_SHA=86038080c4392c8c19c4df2004d1804b30ca2aebd3c0329bfd1b02afc41d6eda
[ "$(sha third_party-src/rebound-5.2.2.tar.gz)" = "$REB_SHA" ] || { say "REBOUND archive does not match its sha256"; exit 2; }
mkdir -p third_party
tar -xzf third_party-src/rebound-5.2.2.tar.gz -C third_party

# CPU reference (the same integrator on the CPU: must give the GPU's bits)
make -s gpu-cpu CC=gcc CXX=g++ >/dev/null
CPU=./build/gpu-cpu/p9gpu

# GPU build
NVCC=${NVCC:-$(command -v nvcc || echo /usr/local/cuda/bin/nvcc)}
GPU=""
if [ "${USE_PREBUILT:-0}" != 1 ] && [ -x "$NVCC" ]; then
  CUDA_LIB=${CUDA_LIB:-$(dirname "$(dirname "$NVCC")")/lib64}
  CC_=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1 | tr -d .)
  ARCH="-gencode arch=compute_${CC_},code=sm_${CC_}"
  say "nvcc: $("$NVCC" --version | tail -2 | head -1)"
  say "build: from source, $ARCH, --fmad=false (see Makefile)"
  make -s gpu NVCC="$NVCC" CUDA_LIB="$CUDA_LIB" GPU_ARCH="$ARCH" GPU_DIR=build/gpu >/dev/null
  make -s build/probe/peak NVCC="$NVCC" GPU_ARCH="$ARCH" >/dev/null
  GPU=./build/gpu/p9gpu
  PEAK=./build/probe/peak
else
  say "build: prebuilt bin/p9gpu (CUDA 13.4; sm_80, sm_89, sm_90, sm_120 and PTX)"
  [ "$(sha bin/p9gpu)" = "$(cut -d' ' -f1 bin/SHA256-p9gpu)" ] || { say "bin/p9gpu does not match its sha256"; exit 2; }
  GPU=./bin/p9gpu
  PEAK=./bin/peak
fi
say "p9gpu: $($GPU version) sha256 $(sha $GPU)"

fail=0
# EXPECTED: name mode real t_end snapshots input_sha256 expected_result_sha256 encounter_radii
run_job() {  # name mode real t_end snaps radii -> result line
  [ "$6" = - ] && radii="" || radii=$6
  P9GPU_MODE=$2 P9GPU_REAL=$3 P9_ENCOUNTER_RADII=$radii "$( [ "$2" = cpu ] && echo $CPU || echo $GPU )" run "jobs/$1/input.sa" "$4" "$5" "jobs/$1/output-$2-$3.sa" 2>"jobs/$1/stderr-$2-$3.txt" | grep '^result_sha256='
}
while read -r name mode real t_end snaps input_sha expected radii; do
  case "$name" in ''|'#'*) continue ;; esac
  case "$name" in bench*) continue ;; esac
  if [ "$(sha "jobs/$name/input.sa")" != "$input_sha" ]; then say "$name: input.sa does not match its sha256"; fail=1; continue; fi
  line=$(run_job "$name" "$mode" "$real" "$t_end" "$snaps" "$radii") || { say "$name ($mode, $real): FAILED, see jobs/$name/stderr-$mode-$real.txt"; fail=1; continue; }
  got=$(printf '%s' "$line" | sed 's/^result_sha256=\([0-9a-f]*\).*/\1/')
  wall=$(printf '%s' "$line" | sed 's/.*wall_s=\([0-9.]*\).*/\1/')
  if [ "$got" = "$expected" ]; then verdict=SAME; else verdict=DIFFERENT; fail=1; fi
  say "$name ($mode, $real): $verdict result_sha256=$got wall_s=$wall"
  [ "$verdict" = SAME ] || say "  expected $expected"
done < EXPECTED

if [ "${SKIP_BENCH:-0}" != 1 ]; then
  say "bench: 64,000 test particles, 10 million years (20 million steps), in double (FP64) and in double-float (df64)"
  W_DOUBLE=""; W_DF64=""
  for b in bench bench-df64; do
    set -- $(grep "^$b " EXPECTED)
    [ $# -ge 8 ] || continue
    nvidia-smi --query-gpu=utilization.gpu,clocks.sm,power.draw,memory.used,temperature.gpu --format=csv,noheader,nounits -l 5 > gpu-samples-$b.csv &
    SMI=$!
    line=$(run_job "$b" "$2" "$3" "$4" "$5" "$8") || line=""
    kill $SMI 2>/dev/null || true
    if [ -z "$line" ]; then say "$b: FAILED, see jobs/$b/stderr-gpu-$3.txt"; fail=1; continue; fi
    got=$(printf '%s' "$line" | sed 's/^result_sha256=\([0-9a-f]*\).*/\1/')
    wall=$(printf '%s' "$line" | sed 's/.*wall_s=\([0-9.]*\).*/\1/')
    if [ "$got" = "$7" ]; then verdict=SAME; else verdict=DIFFERENT; fail=1; fi
    say "$b (gpu, $3): $verdict result_sha256=$got wall_s=$wall particle-steps/s $(awk -v w="$wall" 'BEGIN { printf "%.3g", 64000 * 2e7 / w }')"
    [ "$verdict" = SAME ] || say "  expected $7"
    [ "$3" = double ] && W_DOUBLE=$wall || W_DF64=$wall
    awk -F', ' -v b="$b" '{ n++; u += $1; c += $2; if ($3 > p) p = $3; if ($4 > m) m = $4; if ($5 > t) t = $5 }
      END { if (n) printf "%s gpu: mean utilisation %.0f %%, mean SM clock %.0f MHz, max power %.0f W, max memory %.0f MiB, max temperature %.0f C (%d samples)\n", b, u/n, c/n, p, m, t, n }' gpu-samples-$b.csv | tee -a "$REPORT"
  done
  [ -n "$W_DOUBLE" ] && [ -n "$W_DF64" ] && say "bench: df64 is $(awk -v a="$W_DOUBLE" -v b="$W_DF64" 'BEGIN { printf "%.2f", a / b }') times as fast as double on this GPU"
fi

say "probe: throughput per operation (gpu/probe/peak.cu)"
$PEAK 2>&1 | tee -a "$REPORT" || say "probe: failed"
say "probe: the bench input for 20,000 steps in double, df64 and float (particle-steps per second; float is a probe only)"
for real in double df64 float; do
  line=$(P9GPU_REAL=$real $GPU run jobs/bench/input.sa 10000 1 jobs/bench/probe.sa 2>/dev/null | grep '^result_sha256=') || line=""
  wall=$(printf '%s' "$line" | sed 's/.*wall_s=\([0-9.]*\).*/\1/')
  [ -n "$line" ] && say "  $real: wall_s=$wall particle-steps/s $(awk -v w="$wall" 'BEGIN { printf "%.3g", 64000 * 20000 / w }')" || say "  $real: failed"
done
rm -f jobs/bench/probe.sa

if [ $fail = 0 ]; then say "== ALL SAME"; else say "== DIFFERENCES OR FAILURES (see above)"; fi
say "(this report is also in $REPORT)"
exit $fail
