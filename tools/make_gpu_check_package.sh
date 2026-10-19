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
        ("repro", "cpu", "result-cpu.json"), ("repro-df64", "gpu", "result-cpu.json"), ("bench", "gpu", "result.json")]
lines = ["# name mode real t_end snapshots input_sha256 expected_result_sha256 encounter_radii (id=au)",
         "# expected: control, repro, repro-df64 from p9gpu's CPU twin (the GPU's bits), bench from the reference GPU"]
for name, mode, res in rows:
    d = Path("runs/gpkg") / name
    job = json.loads((d / "job.json").read_text())
    r = json.loads((d / res).read_text())
    if r["job_id"] != job["id"]:
        sys.exit(f"{d}/{res} belongs to another job")
    p = job["params"]
    lines.append(" ".join([name, mode, p.get("real", "double"), repr(float(p["t_end_yr"])), str(p["snapshots"]), job["input"]["sha256"],
                           r["result_sha256"], p9job.encounter_env(job)]))
    (out / "jobs" / name).mkdir(exist_ok=True)
    for f in ("job.json", "input.sa"):
        (out / "jobs" / name / f).write_bytes((d / f).read_bytes())
(out / "EXPECTED").write_text("\n".join(lines) + "\n")
PY

# prebuilt binaries for machines without a CUDA toolkit
ARCH="-gencode arch=compute_80,code=sm_80 -gencode arch=compute_89,code=sm_89 -gencode arch=compute_90,code=sm_90 -gencode arch=compute_120,code=sm_120 -gencode arch=compute_80,code=compute_80"
make -s gpu GPU_DIR="$OUT-build" GPU_ARCH="$ARCH" >/dev/null
make -s "$OUT-build/peak" -f - <<EOF >/dev/null
include Makefile
$OUT-build/peak: gpu/probe/peak.cu
	\$(NVCC) -O3 --fmad=false -prec-div=true -prec-sqrt=true $ARCH -o \$@ gpu/probe/peak.cu
EOF
cp "$OUT-build/p9gpu" "$OUT-build/peak" "$OUT/bin/"
( cd "$OUT/bin" && sha256sum p9gpu > SHA256-p9gpu && sha256sum peak > SHA256-peak )
rm -rf "$OUT-build"

tar --sort=name --owner=0 --group=0 --numeric-owner -C build -czf "$OUT.tar.gz" "p9gpucheck-$REV"
( cd build && sha256sum "p9gpucheck-$REV.tar.gz" > "p9gpucheck-$REV.tar.gz.sha256" )
cat "$OUT.tar.gz.sha256"
ls -la "$OUT.tar.gz"
