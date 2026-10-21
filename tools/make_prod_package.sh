#!/bin/sh
# Builds the production package for the GPU server (prod/README-prod.txt) from the job in runs/prod (p9job make;
# docs/production-proposal.md). Expected hashes of the check: p9gpu's CPU twin of this commit (the GPU's bits).
#   tools/make_prod_package.sh  ->  build/p9prod-<commit>.tar.gz (+ .sha256)
# DEEP=dir: the restarted deep Neptune flybys (tools/deep_flyby_test.py; default the main checkout's runs/jacobi-lost/deep)
set -eu
cd "$(dirname "$0")/.."
REV=$(git rev-parse --short HEAD)
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "commit first" >&2; exit 1; }
DEEP=${DEEP:-../medas-p9-search/runs/jacobi-lost/deep}
PY=build/venv/bin/python
make -s gpu-cpu VARIANT=test > /dev/null && make -s VARIANT=test > /dev/null
CPU=build/gpu-cpu/p9gpu
[ "$($CPU version)" = "program=p9gpu version=$REV" ] || { echo "build/gpu-cpu/p9gpu is not $REV" >&2; exit 1; }
OUT=build/p9prod-$REV
rm -rf "$OUT" && mkdir -p "$OUT/src" "$OUT/gpu" "$OUT/third_party-src" "$OUT/bin" "$OUT/run" "$OUT/check/jobs"
cp Makefile LICENSE "$OUT/"
echo "$REV" > "$OUT/VERSION"
echo "$REV ($(git log -1 --format=%cs))" > "$OUT/PACKAGE-VERSION"
cp src/*.c src/*.h "$OUT/src/"
cp gpu/*.c gpu/*.cu gpu/*.cpp gpu/*.h "$OUT/gpu/"
cp third_party/README.md third_party/rebound-5.2.2.tar.gz "$OUT/third_party-src/"
cp prod/run-production.sh prod/check.sh prod/start.sh prod/stop.sh prod/status.sh "$OUT/"
cp prod/README-prod.txt "$OUT/README.txt"
cp runs/prod/job.json runs/prod/input.sa "$OUT/run/"
sha256sum runs/prod/input.sa | cut -d' ' -f1 > "$OUT/run/INPUT-SHA256"

# params.env (the job's settings) and check/EXPECTED (hashes of the CPU twin)
$PY -I - "$OUT" "$CPU" "$DEEP" <<'PY'
import json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, "tools"); sys.path.insert(0, "tests")
import p9job
import test_flyby_regression as tr
out, cpu, deep = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
job = json.loads(Path("runs/prod/job.json").read_text())
p, enc = job["params"], job["params"]["removal"]["encounter"]
assert enc["method"] == "smooth" and p.get("real", "double") == "double"
seg_yr, n_seg = 1e8, int(round(float(p["t_end_yr"]) / 1e8))
assert n_seg * seg_yr == float(p["t_end_yr"]) and int(p["snapshots"]) % n_seg == 0
env = {"P9_ENCOUNTER_METHOD": "smooth", "P9_ENCOUNTER_RADII": p9job.encounter_env(job), "P9_COLLISION_RADII": p9job.collision_env(job),
       "P9_PLANET_SUBSTEPS": str(enc["planet_substeps"]), "P9_R_IN": repr(float(p["removal"]["r_in_au"])), "P9GPU_REAL": "double"}
lines = [f"# the settings of run/job.json ({job['id'][:16]}...)"] + [f"{k}={v}" for k, v in env.items()]
lines += [f"SEGMENT_YR={seg_yr:.0f}", f"SEGMENTS={n_seg}", f"SNAPSHOTS_PER_SEGMENT={int(p['snapshots']) // n_seg}",
          "# the settings of the regression cases of the check (tests/test_flyby_regression.py)", f"REG_RADII={tr.RADII}", f"REG_COLLISION={tr.COLLISION}"]
(out / "params.env").write_text("\n".join(lines) + "\n")

def run(sa, t_end, e):
    full = dict(os.environ, P9GPU_MODE="cpu", P9GPU_REAL="double", **e)
    for k in ("P9_ENCOUNTER_REMOVE", "P9_FLYBY_OUT", "P9_REMOVED_OUT", "P9_J2", "P9_CAPPED_OUT", "P9_SUBSTEPS_OUT"):
        full.pop(k, None)
    o = Path(str(sa) + ".o.sa")
    r = subprocess.run([cpu, "run", str(sa), repr(float(t_end)), "1", str(o)], env=full, capture_output=True, text=True, check=True)
    return [l for l in r.stdout.splitlines() if l.startswith("result_sha256=")][-1].split()[0].split("=")[1], o
reg = {"P9_ENCOUNTER_METHOD": "smooth", "P9_ENCOUNTER_RADII": tr.RADII, "P9_COLLISION_RADII": tr.COLLISION, "P9_PLANET_SUBSTEPS": "8", "P9_R_IN": "5"}
dee = {"P9_ENCOUNTER_METHOD": "smooth", "P9_ENCOUNTER_RADII": "1=3.1036", "P9_COLLISION_RADII": "1=1.655371e-04", "P9_PLANET_SUBSTEPS": "8", "P9_R_IN": "5"}
prod = {k: v for k, v in env.items() if k != "P9GPU_REAL"}
rows = ["# name profile input t_mid t_end expected_result_sha256 (p9gpu's CPU twin of the package commit)"]
for c in json.loads((tr.DATA / "index.json").read_text())["cases"]:
    sa = out / "check/jobs" / f"regression-{c['id']}.sa"
    subprocess.run(["build/test/p9sim", "init", str(tr.DATA / c["file"]), str(sa)], check=True, stdout=subprocess.DEVNULL)
    t = c["steps"] * c["dt_yr"]
    h, o = run(sa, t, reg); o.unlink()
    rows.append(f"regression-{c['id']} regression check/jobs/{sa.name} - {t!r} {h}")
rep = {r["id"]: r for r in json.loads((deep / "report.json").read_text())}
for i, r in sorted(rep.items()):
    sa = out / "check/jobs" / f"deep-{i}.sa"
    sa.write_bytes((deep / f"p{i}" / "input.sa").read_bytes())
    h, o = run(sa, r["t_end"], dee); o.unlink()
    rows.append(f"deep-{i} deep check/jobs/{sa.name} - {float(r['t_end'])!r} {h}")
inp = out / "run/input.sa"
h, o = run(inp, 1e4, prod); o.unlink()
rows.append(f"prod prod run/input.sa - 10000.0 {h}")
ha, oa = run(inp, 5e3, prod)
b_in = out / "check/jobs/chain-b-in.sa"
subprocess.run(["build/test/p9sim", "last", str(oa), str(b_in)], check=True, stdout=subprocess.DEVNULL)
hb, ob = run(b_in, 1e4, prod)
for f in (oa, ob, b_in):
    f.unlink()
rows.append(f"chain prod run/input.sa 5000.0 10000.0 {hb}")
(out / "check/EXPECTED").write_text("\n".join(rows) + "\n")
print(f"params.env and check/EXPECTED: {len(rows) - 1} check jobs")
PY

# prebuilt binaries (as tools/make_gpu_check_package.sh): CUDA 13.3 on Ubuntu 22.04, libstdc++/libgcc static
IMG=nvidia/cuda:13.3.0-devel-ubuntu22.04
ARCH="-gencode arch=compute_80,code=sm_80 -gencode arch=compute_89,code=sm_89 -gencode arch=compute_90,code=sm_90 -gencode arch=compute_120,code=sm_120 -gencode arch=compute_80,code=compute_80"
rm -rf "$OUT-build" && mkdir -p "$OUT-build"
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD/$OUT:/pkg:ro" -v "$PWD/$OUT-build:/out" "$IMG" sh -c "
  set -e; mkdir -p /tmp/w; cd /pkg; cp -r Makefile LICENSE VERSION src gpu third_party-src /tmp/w/; cd /tmp/w; mkdir -p third_party
  tar -xzf third_party-src/rebound-5.2.2.tar.gz -C third_party
  make -s gpu NVCC=/usr/local/cuda/bin/nvcc CUDA_LIB=/usr/local/cuda/lib64 GPU_ARCH='$ARCH' GPU_DIR=/tmp/b GPU_STDCXX='-Wl,-Bstatic -lstdc++ -Wl,-Bdynamic' GPU_LDFLAGS=-static-libgcc >/dev/null
  make -s CC=gcc VARIANT=srv >/dev/null
  cp /tmp/b/p9gpu /out/; cp build/srv/p9sim /out/; /usr/local/cuda/bin/nvcc --version | tail -n 2 | head -n 1 > /out/NVCC-VERSION; ldd --version | head -n 1 > /out/BUILD-GLIBC"
REQ=$(objdump -T "$OUT-build/p9gpu" "$OUT-build/p9sim" | grep -oE 'GLIBC_[0-9.]+' | sed 's/GLIBC_//' | sort -uV | tail -n 1)
if objdump -T "$OUT-build/p9gpu" "$OUT-build/p9sim" | grep -q GLIBCXX; then echo "prebuilt binaries need libstdc++ (GLIBCXX)" >&2; exit 1; fi
[ "$(printf '%s\n' "$REQ" 2.35 | sort -V | tail -n 1)" = 2.35 ] || { echo "prebuilt binaries need glibc $REQ, more than Ubuntu 22.04's 2.35" >&2; exit 1; }
echo "$REQ" > "$OUT/bin/REQUIRES-glibc"
cp "$OUT-build/NVCC-VERSION" "$OUT-build/BUILD-GLIBC" "$OUT-build/p9gpu" "$OUT-build/p9sim" "$OUT/bin/"
( cd "$OUT/bin" && sha256sum p9gpu > SHA256-p9gpu && sha256sum p9sim > SHA256-p9sim )
rm -rf "$OUT-build"
echo "prebuilt: glibc >= $REQ; $(cat "$OUT/bin/NVCC-VERSION"); p9gpu $(cut -c1-16 "$OUT/bin/SHA256-p9gpu")"

tar --sort=name --owner=0 --group=0 --numeric-owner -C build -czf "$OUT.tar.gz" "p9prod-$REV"
( cd build && sha256sum "p9prod-$REV.tar.gz" > "p9prod-$REV.tar.gz.sha256" )
cat "$OUT.tar.gz.sha256"
ls -la "$OUT.tar.gz"
