#!/bin/sh
# Builds tools/direct_wh.c into build/direct/direct_wh with the flags of the Makefile (p9sim and p9gpu's CPU build).
set -eu
cd "$(dirname "$0")/.."
R=third_party/rebound-5.2.2
mkdir -p build/direct
REB_SRC=$(ls $R/src/*.c | grep -v -e '/glad.c$' -e '/communication_mpi.c$' -e '/server.c$' -e '/integrator_whfast512.c$')
gcc -std=c99 -fno-fast-math -O3 -ffp-contract=off -D_GNU_SOURCE -DLIBREBOUND -DP9_VERSION='"direct"' -DP9_NO_CUDA -DP9_NO_REAL_T \
  -I$R/src -Isrc -Igpu -w -o build/direct/direct_wh tools/direct_wh.c src/p9state.c src/p9encounter.c src/sha256.c src/whfast512_stub.c $REB_SRC -lm
echo build/direct/direct_wh
