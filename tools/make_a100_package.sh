#!/bin/sh
# Builds the A100 acceptance package (a100/README.txt) from a clean checkout:
#   tools/make_a100_package.sh  ->  build/a100acc-<commit>.tar.gz (+ .sha256)
# bin/peak and bin/fp64burn are built in NVIDIA's CUDA 13.3 image on Ubuntu 22.04, --fmad=false, sm_80 and sm_120
# machine code plus compute_80 PTX, libgcc static (the CUDA runtime is linked statically by nvcc by default).
set -eu
cd "$(dirname "$0")/.."
[ -z "$(git status --porcelain -- a100 gpu/probe tools/make_a100_package.sh)" ] || { echo "a100/, gpu/probe/ or this script not committed"; exit 1; }
c=$(git rev-parse --short HEAD)
name=a100acc-$c
out=build/$name
rm -rf "$out"; mkdir -p "$out/bin" "$out/src"
cp a100/acceptance.sh a100/README.txt "$out/"
cp gpu/probe/peak.cu gpu/probe/fp64burn.cu "$out/src/"
IMG=nvidia/cuda:13.3.0-devel-ubuntu22.04
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD/$out/src:/src:ro" -v "$PWD/$out/bin:/out" "$IMG" sh -c '
  A="-gencode arch=compute_80,code=sm_80 -gencode arch=compute_120,code=sm_120 -gencode arch=compute_80,code=compute_80"
  nvcc -O3 --fmad=false $A -Xcompiler -static-libgcc -o /out/peak /src/peak.cu &&
  nvcc -O3 --fmad=false $A -Xcompiler -static-libgcc -o /out/fp64burn /src/fp64burn.cu &&
  nvcc --version | tail -n 2 | head -n 1 > /out/NVCC-VERSION && ldd --version | head -n 1 > /out/BUILD-GLIBC' > /dev/null
git rev-parse HEAD > "$out/VERSION"
(cd "$out" && find . -type f ! -name SHA256SUMS | LC_ALL=C sort | xargs sha256sum > SHA256SUMS)
(cd build && find "$name" -print0 | LC_ALL=C sort -z | tar --null --no-recursion -T - --owner=0 --group=0 --mtime=@0 -cf - | gzip -n -9 > "$name.tar.gz" && sha256sum "$name.tar.gz" > "$name.tar.gz.sha256")
cat "build/$name.tar.gz.sha256"
