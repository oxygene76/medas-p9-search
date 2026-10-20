#!/bin/sh
# Builds the GPU check package for a second machine (check/README-gpu.txt) from
# the jobs in runs/gpkg/ (control, repro, repro-df64, bench). Expected hashes:
# result-cpu.json of control, repro and repro-df64 (p9gpu's CPU twin, which
# gives the GPU's bits) and result.json of bench (the reference GPU).
#   tools/make_gpu_check_package.sh  ->  build/p9gpucheck-<commit>.tar.gz (+ .sha256)
set -eu
cd "$(dirname "$0")/.."
REV=$(git rev-parse --short HEAD)
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "commit first" >&2; exit 1; }
PY=build/venv/bin/python
OUT=build/p9gpucheck-$REV
rm -rf "$OUT" && mkdir -p "$OUT/src" "$OUT/gpu/probe" "$OUT/third_party-src" "$OUT/jobs" "$OUT/bin"
cp Makefile LICENSE "$OUT/"
echo "$REV" > "$OUT/VERSION"
echo "$REV ($(git log -1 --format=%cs))" > "$OUT/PACKAGE-VERSION"
cp src/*.c src/*.h "$OUT/src/"
cp gpu/*.c gpu/*.cu gpu/*.cpp gpu/*.h "$OUT/gpu/"
cp gpu/probe/* "$OUT/gpu/probe/"
cp check/run-gpucheck.sh check/Dockerfile.gpu "$OUT/"
cp check/README-gpu.txt "$OUT/README.txt"
cp third_party/README.md third_party/rebound-5.2.2.tar.gz "$OUT/third_party-src/"

# EXPECTED: name mode real t_end snapshots input_sha256 expected_result_sha256 encounter_radii
$PY -I - "$OUT" <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, "tools")
import p9job
out = Path(sys.argv[1])
rows = [("control", "gpu", "result-cpu.json"), ("control", "cpu", "result-cpu.json"), ("repro", "gpu", "result-cpu.json"),
        ("repro", "cpu", "result-cpu.json"), ("repro-df64", "gpu", "result-cpu.json"), ("bench", "gpu", "result.json"),
        ("bench-df64", "gpu", "result.json")]
lines = ["# name mode real t_end snapshots input_sha256 expected_result_sha256 encounter_radii (id=au)",
         "# expected: control, repro, repro-df64 from p9gpu's CPU twin (the GPU's bits), bench and bench-df64 from the reference GPU",
         "# no removal at the planets in any job (only the distance rules); '-': no encounter radii"]
for name, mode, res in rows:
    d = Path("runs/gpkg") / name
    job = json.loads((d / "job.json").read_text())
    r = json.loads((d / res).read_text())
    if r["job_id"] != job["id"]:
        sys.exit(f"{d}/{res} belongs to another job")
    p = job["params"]
    lines.append(" ".join([name, mode, p.get("real", "double"), repr(float(p["t_end_yr"])), str(p["snapshots"]), job["input"]["sha256"],
                           r["result_sha256"], p9job.encounter_env(job) or "-"]))
    (out / "jobs" / name).mkdir(exist_ok=True)
    for f in ("job.json", "input.sa"):
        (out / "jobs" / name / f).write_bytes((d / f).read_bytes())
(out / "EXPECTED").write_text("\n".join(lines) + "\n")
PY

# prebuilt binaries for machines without a CUDA toolkit, built in NVIDIA's
# CUDA 13.3 image on Ubuntu 22.04 (glibc 2.35, gcc 11): they run on Ubuntu
# 22.04 and newer; libstdc++ and libgcc linked statically. The glibc they need
# is recorded in bin/REQUIRES-glibc (run-gpucheck.sh checks it first).
IMG=nvidia/cuda:13.3.0-devel-ubuntu22.04
ARCH="-gencode arch=compute_80,code=sm_80 -gencode arch=compute_89,code=sm_89 -gencode arch=compute_90,code=sm_90 -gencode arch=compute_120,code=sm_120 -gencode arch=compute_80,code=compute_80"
rm -rf "$OUT-build" && mkdir -p "$OUT-build"
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD/$OUT:/pkg:ro" -v "$PWD/$OUT-build:/out" "$IMG" sh -c "
  set -e; cp -r /pkg /tmp/w; cd /tmp/w; mkdir -p third_party; tar -xzf third_party-src/rebound-5.2.2.tar.gz -C third_party
  make -s gpu NVCC=/usr/local/cuda/bin/nvcc CUDA_LIB=/usr/local/cuda/lib64 GPU_ARCH='$ARCH' GPU_DIR=/tmp/b GPU_STDCXX='-Wl,-Bstatic -lstdc++ -Wl,-Bdynamic' GPU_LDFLAGS=-static-libgcc >/dev/null
  /usr/local/cuda/bin/nvcc -O3 --fmad=false -prec-div=true -prec-sqrt=true $ARCH -c gpu/probe/peak.cu -o /tmp/b/peak.o
  g++ -static-libstdc++ -static-libgcc -o /tmp/b/peak /tmp/b/peak.o -L/usr/local/cuda/lib64 -lcudart_static -ldl -lpthread -lrt
  cp /tmp/b/p9gpu /tmp/b/peak /out/; /usr/local/cuda/bin/nvcc --version | tail -n 2 | head -n 1 > /out/NVCC-VERSION; ldd --version | head -n 1 > /out/BUILD-GLIBC"
# no symbol may need a newer glibc than Ubuntu 22.04 has (2.35), none any libstdc++ (GLIBCXX)
REQ=$(objdump -T "$OUT-build/p9gpu" "$OUT-build/peak" | grep -oE 'GLIBC_[0-9.]+' | sed 's/GLIBC_//' | sort -uV | tail -n 1)
if objdump -T "$OUT-build/p9gpu" "$OUT-build/peak" | grep -q GLIBCXX; then echo "prebuilt binaries need libstdc++ (GLIBCXX)" >&2; exit 1; fi
[ "$(printf '%s\n' "$REQ" 2.35 | sort -V | tail -n 1)" = 2.35 ] || { echo "prebuilt binaries need glibc $REQ, more than Ubuntu 22.04's 2.35" >&2; exit 1; }
echo "$REQ" > "$OUT/bin/REQUIRES-glibc"
cp "$OUT-build/NVCC-VERSION" "$OUT-build/BUILD-GLIBC" "$OUT/bin/"
echo "prebuilt: glibc >= $REQ needed; built with $(cat "$OUT-build/NVCC-VERSION"), $(cat "$OUT-build/BUILD-GLIBC")"
cp "$OUT-build/p9gpu" "$OUT-build/peak" "$OUT/bin/"
( cd "$OUT/bin" && sha256sum p9gpu > SHA256-p9gpu && sha256sum peak > SHA256-peak )
rm -rf "$OUT-build"

tar --sort=name --owner=0 --group=0 --numeric-owner -C build -czf "$OUT.tar.gz" "p9gpucheck-$REV"
( cd build && sha256sum "p9gpucheck-$REV.tar.gz" > "p9gpucheck-$REV.tar.gz.sha256" )
cat "$OUT.tar.gz.sha256"
ls -la "$OUT.tar.gz"
