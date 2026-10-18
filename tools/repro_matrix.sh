#!/bin/sh
# Reproducibility matrix: one job, many builds; every result_sha256 must be equal.
#
#   tools/repro_matrix.sh [JOB_DIR]
#
# Toolchains (paths or names on PATH): CLANG, ZIG, QEMU_AARCH64, NODE, PY.
# Builds: gcc and clang at -O2 and -O3 (x86-64, glibc), zig ARM64 (musl,
# under qemu-user) and zig WebAssembly (WASI, in Node) at -O2 and -O3, and two
# counter-examples (FMA, -ffast-math) that are expected to differ.
set -eu
cd "$(dirname "$0")/.."
CLANG=${CLANG:-clang}
ZIG=${ZIG:-zig}
QEMU_AARCH64=${QEMU_AARCH64:-qemu-aarch64}
NODE=${NODE:-node}
PY=${PY:-python3}
JOB=${1:-runs/repro}

for o in -O2 -O3; do
  make -s CC=gcc OPT=$o
  make -s CC="$CLANG" OPT=$o VARIANT=clang$o
  make -s aarch64 ZIG="$ZIG" OPT=$o
  make -s wasm ZIG="$ZIG" OPT=$o
done
make -s counterexamples

if [ ! -f "$JOB/job.json" ]; then
  "$PY" -I tools/p9job.py make --out "$JOB" --t-end 1e6 --snapshots 10 --tp-to 100 --p9sim build/gcc-O3/p9sim
fi

run() { # name p9sim [prefix]
  echo "== $1" >&2
  "$PY" -I tools/p9job.py run "$JOB" --p9sim "$2" --prefix "${3:-}" --output "output-$1.sa" --result-name "result-$1.json" >/dev/null
}
run gcc-O3 build/gcc-O3/p9sim
run gcc-O3-again build/gcc-O3/p9sim
run gcc-O2 build/gcc-O2/p9sim
run clang-O3 build/clang-O3/p9sim
run clang-O2 build/clang-O2/p9sim
run wasm32-O3 build/zig-wasm32-O3/p9sim "$NODE --no-warnings tools/run_wasm.mjs"
run wasm32-O2 build/zig-wasm32-O2/p9sim "$NODE --no-warnings tools/run_wasm.mjs"
run aarch64-O3 build/zig-aarch64-O3/p9sim "$QEMU_AARCH64"
run aarch64-O2 build/zig-aarch64-O2/p9sim "$QEMU_AARCH64"
run counter-fma build/gcc-O3-fma/p9sim
run counter-fastmath build/gcc-O3-fastmath/p9sim

"$PY" - "$JOB" <<'PYEOF'
import json, sys, glob, os
job = sys.argv[1]
ref = json.load(open(f"{job}/result-gcc-O3.json"))["result_sha256"]
print(f"job {json.load(open(f'{job}/job.json'))['id']}")
print(f"{'variant':18} {'result_sha256':66} {'same':5} {'wall_s':>8}")
for f in sorted(glob.glob(f"{job}/result-*.json")):
    r = json.load(open(f))
    name = os.path.basename(f)[7:-5]
    print(f"{name:18} {r['result_sha256']:66} {'yes' if r['result_sha256'] == ref else 'NO':5} {r['wall_s']:8.1f}")
PYEOF
