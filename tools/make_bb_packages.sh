#!/bin/sh
# Builds the two packages of the comparison with Brown & Batygin 2021 (docs/bb2021-comparison-criteria.md in
# medas-p9-search, addenda 13-16) from the jobs that medas-p9-search-bb2021 made (runs/bb2021, p9job make with
# make-ic-v1: Planet Nine of the set relative to the invariable plane, the radii of addendum 13):
#   build/p9bbv2-<commit>.tar.gz     the V2 short runs, for the L40S: V2-A (seed 321), V2-B (seed 322), 16,000 test
#                                    particles, 0-60 Myr in 3 segments of 20 Myr, flyby logs
#   build/p9bbsets-<commit>.tar.gz   the 4-Gyr runs, for the A100: BB-A (seed 311), BB-B (seed 312), 64,000 test
#                                    particles, 40 segments of 100 Myr, a snapshot every 10 Myr; a job starts only with
#                                    its V2 verdict
# The binaries are those of the production package p9prod-9a084ed (PROD, checked by sha256); expected hashes of the
# check as in tools/make_long_packages.sh (p9gpu's CPU twin of this commit).
#   commit, then: PROD=../medas-p9-search-bb2021/build/p9prod-9a084ed BBJOBS=../medas-p9-search-bb2021/runs/bb2021 tools/make_bb_packages.sh
set -eu
cd "$(dirname "$0")/.."
REV=$(git rev-parse --short HEAD)
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "commit first" >&2; exit 1; }
PROD=${PROD:-../medas-p9-search-bb2021/build/p9prod-9a084ed}
BBJOBS=${BBJOBS:-../medas-p9-search-bb2021/runs/bb2021}
PY=build/venv/bin/python
make -s gpu-cpu > /dev/null && make -s VARIANT=test > /dev/null
CPU=build/gpu-cpu/p9gpu
[ "$($CPU version)" = "program=p9gpu version=$REV" ] || { echo "build/gpu-cpu/p9gpu is not $REV" >&2; exit 1; }
for f in p9gpu p9sim; do
  [ "$(sha256sum "$PROD/bin/$f" | cut -d' ' -f1)" = "$(cut -d' ' -f1 "$PROD/bin/SHA256-$f")" ] || { echo "$PROD/bin/$f does not match its sha256" >&2; exit 1; }
done

build() {  # $1 = package name, $2 = bb/<kind>, $3 = job kind (v2short or sets)
  out=build/$1-$REV
  rm -rf "$out" && mkdir -p "$out/src" "$out/gpu" "$out/third_party-src" "$out/bin" "$out/jobs" "$out/check/jobs" "$out/v2"
  cp Makefile LICENSE "$out/"
  echo "$REV" > "$out/VERSION"
  echo "$REV ($(git log -1 --format=%cs))" > "$out/PACKAGE-VERSION"
  cp src/*.c src/*.h "$out/src/"; cp gpu/*.c gpu/*.cu gpu/*.cpp gpu/*.h "$out/gpu/"
  cp third_party/README.md third_party/rebound-5.2.2.tar.gz "$out/third_party-src/"
  for f in run-all.sh run-job.sh check.sh start.sh stop.sh status.sh select-gpu.sh; do cp "bb/v5/$f" "$out/"; done
  cp "$2/README.txt" "$out/README.txt"; cp "$2/EXPECTED-TIME.txt" "$out/EXPECTED-TIME"; cp "$2/defaults.env" "$out/defaults.env"
  cp "$PROD/bin/p9sim" "$PROD/bin/SHA256-p9sim" "$PROD/bin/REQUIRES-glibc" "$PROD/bin/BUILD-GLIBC" "$PROD/bin/p9gpu" "$PROD/bin/SHA256-p9gpu" "$PROD/bin/NVCC-VERSION" "$out/bin/"
  grep '^REG_' "$PROD/params.env" > "$out/check/regression.env"
  grep -E '^(regression|deep)-' "$PROD/check/EXPECTED" > "$out/check/EXPECTED.prod"
  for f in $(awk '{ print $3 }' "$out/check/EXPECTED.prod"); do cp "$PROD/$f" "$out/check/jobs/"; done
  $PY -I - "$out" "$CPU" "$BBJOBS" "$3" <<'PY'
import json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, "tools")
import p9job
out, cpu, src_root, kind = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), sys.argv[4]
SETS = {"A": {"p9": "m_earth=7,a=500,e=0.33,inc=17,varpi=250,Omega=100,M=0", "r_p9": "2.0824", "col_p9": "17248.4"},
        "B": {"p9": "m_earth=5,a=300,e=0.15,inc=17,varpi=254,Omega=108,M=0", "r_p9": "1.8616", "col_p9": "15418.4"}}
KIND = {"v2short": {"prefix": "V2", "seeds": {"A": 321, "B": 322}, "n_tp": 16000, "t_end": 6e7, "snapshots": 3,
                    "segments": "SEGMENT_YR=20000000\nSEGMENTS=3\nSNAPSHOTS_PER_SEGMENT=1\n"},
        "sets": {"prefix": "BB", "seeds": {"A": 311, "B": 312}, "n_tp": 64000, "t_end": 4e9, "snapshots": 400,
                 "segments": "SEGMENT_YR=100000000\nSEGMENTS=40\nSNAPSHOTS_PER_SEGMENT=10\n"}}[kind]
rows = ["# name profile input t_mid t_end expected_result_sha256 (regression, deep: the production package's check; jobs: p9gpu's CPU twin)"]
rows += (out / "check/EXPECTED.prod").read_text().splitlines()
(out / "check/EXPECTED.prod").unlink()
def run(sa, t_end, e):
    full = dict(os.environ, P9GPU_MODE="cpu", P9GPU_REAL="double", **e)
    for k in ("P9_ENCOUNTER_REMOVE", "P9_FLYBY_OUT", "P9_REMOVED_OUT", "P9_J2", "P9_CAPPED_OUT", "P9_SUBSTEPS_OUT"):
        full.pop(k, None)
    o = Path(str(sa) + ".o.sa")
    r = subprocess.run([cpu, "run", str(sa), repr(float(t_end)), "1", str(o)], env=full, capture_output=True, text=True, check=True)
    return [l for l in r.stdout.splitlines() if l.startswith("result_sha256=")][-1].split()[0].split("=")[1], o
for s in ("A", "B"):
    name, src = f"{KIND['prefix']}-{s}", src_root / kind / s
    dst = out / "jobs" / name
    dst.mkdir(parents=True)
    job = json.loads((src / "job.json").read_text()); p = job["params"]; enc = p["removal"]["encounter"]
    assert enc["method"] == "smooth" and enc["planet_substeps"] == 8 and float(p["dt_yr"]) == 0.5 and float(p["removal"]["r_in_au"]) == 4.5
    assert p["ic"]["seed"] == KIND["seeds"][s] and p["ic"]["n_tp"] == KIND["n_tp"] and float(p["t_end_yr"]) == KIND["t_end"] and int(p["snapshots"]) == KIND["snapshots"]
    assert p["ic"]["p9"] == SETS[s]["p9"] and p["ic"]["p9_plane"] == "invariable"
    assert enc["radii_au"] == {"Jupiter": "7.4300", "Saturn": "4.9708", "Uranus": "2.6572", "Neptune": "3.1036", "P9": SETS[s]["r_p9"]}, enc["radii_au"]
    assert enc["collision"]["radii_km"]["P9"] == SETS[s]["col_p9"] and enc["collision"]["radii_km"]["Neptune"] == "24764.0"
    env = {"P9_ENCOUNTER_METHOD": "smooth", "P9_ENCOUNTER_RADII": p9job.encounter_env(job), "P9_COLLISION_RADII": p9job.collision_env(job),
           "P9_PLANET_SUBSTEPS": str(enc["planet_substeps"]), "P9_R_IN": repr(float(p["removal"]["r_in_au"]))}
    (dst / "params.env").write_text(f"# the settings of jobs/{name}/job.json ({job['id'][:16]}...), dt {p['dt_yr']} yr (in input.sa)\n"
                                    + "".join(f"{k}={v}\n" for k, v in env.items()) + "P9GPU_REAL=double\n" + KIND["segments"])
    for f in ("job.json", "input.sa"):
        (dst / f).write_bytes((src / f).read_bytes())
    (dst / "INPUT-SHA256").write_text(subprocess.run(["sha256sum", str(src / "input.sa")], capture_output=True, text=True).stdout.split()[0] + "\n")
    inp = dst / "input.sa"
    h, o = run(inp, 1e4, env); o.unlink()
    rows.append(f"{name} job:{name} jobs/{name}/input.sa - 10000.0 {h}")
    ha, oa = run(inp, 5e3, env)
    b_in = out / "check/jobs" / f"{name}-chain-b-in.sa"
    subprocess.run(["build/test/p9sim", "last", str(oa), str(b_in)], check=True, stdout=subprocess.DEVNULL)
    hb, ob = run(b_in, 1e4, env)
    for f in (oa, ob, b_in):
        f.unlink()
    rows.append(f"{name}-chain job:{name} jobs/{name}/input.sa 5000.0 10000.0 {hb}")
(out / "check/EXPECTED").write_text("\n".join(rows) + "\n")
print(f"{out.name} check/EXPECTED: {len(rows) - 1} check cases")
PY
  tar --sort=name --owner=0 --group=0 --numeric-owner -C build -czf "build/$1-$REV.tar.gz" "$1-$REV"
  ( cd build && sha256sum "$1-$REV.tar.gz" > "$1-$REV.tar.gz.sha256" )
  cat "build/$1-$REV.tar.gz.sha256"
}
build p9bbv2 bb/v2short v2short
build p9bbsets bb/sets sets
