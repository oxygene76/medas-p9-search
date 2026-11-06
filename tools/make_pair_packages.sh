#!/bin/sh
# Builds the two packages of the paired tests V5 against MERCURIUS for sets A and B (docs/bb2021-paired-test-proposal.md
# in medas-p9-search) from the jobs that medas-p9-search-bb2021 made (tools/make_pair_jobs.sh, runs/pair):
#   build/p9pair-v5-<commit>.tar.gz    group V5 for the A100: PV5-s331 ... s339 (set A), PV5-s341 ... s349 (set B);
#                                      4,000 test particles, 0-200 Myr, 10 segments of 20 Myr, a snapshot every 1 Myr,
#                                      flyby logs; one job at a time
#   build/p9pair-merc-<commit>.tar.gz  group M for CPU 1: PM-s331-part00 ... PM-s349-part15 (MERCURIUS, slices of 250;
#                                      scripts of pair/merc: nice 19, idle I/O, socket 0)
# The binaries are those of the production package p9prod-9a084ed (PROD, checked by sha256). Expected hashes of the
# checks: V5 jobs with p9gpu's CPU twin of this commit (the GPU's bits), regression and deep cases from the production
# package's check; M with the package's own p9sim on this machine (glibc-independent).
#   commit, then: PROD=../medas-p9-search-bb2021/build/p9prod-9a084ed PAIRJOBS=../medas-p9-search-bb2021/runs/pair tools/make_pair_packages.sh
set -eu
cd "$(dirname "$0")/.."
REV=$(git rev-parse --short HEAD)
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "commit first" >&2; exit 1; }
PROD=${PROD:-../medas-p9-search-bb2021/build/p9prod-9a084ed}
PAIRJOBS=${PAIRJOBS:-../medas-p9-search-bb2021/runs/pair}
PY=build/venv/bin/python
make -s gpu-cpu > /dev/null && make -s VARIANT=test > /dev/null
CPU=build/gpu-cpu/p9gpu
[ "$($CPU version)" = "program=p9gpu version=$REV" ] || { echo "build/gpu-cpu/p9gpu is not $REV" >&2; exit 1; }
for f in p9gpu p9sim; do
  [ "$(sha256sum "$PROD/bin/$f" | cut -d' ' -f1)" = "$(cut -d' ' -f1 "$PROD/bin/SHA256-$f")" ] || { echo "$PROD/bin/$f does not match its sha256" >&2; exit 1; }
done
SEEDS="331 332 333 334 335 336 337 338 339 341 342 343 344 345 346 347 348 349"

common() {  # $1 = output directory, $2 = script directory, $3 = doc directory
  rm -rf "$1" && mkdir -p "$1/src" "$1/gpu" "$1/third_party-src" "$1/bin" "$1/jobs" "$1/check/jobs"
  cp Makefile LICENSE "$1/"
  echo "$REV" > "$1/VERSION"
  echo "$REV ($(git log -1 --format=%cs))" > "$1/PACKAGE-VERSION"
  cp src/*.c src/*.h "$1/src/"; cp gpu/*.c gpu/*.cu gpu/*.cpp gpu/*.h "$1/gpu/"
  cp third_party/README.md third_party/rebound-5.2.2.tar.gz "$1/third_party-src/"
  for f in run-all.sh run-job.sh check.sh start.sh stop.sh status.sh; do cp "$2/$f" "$1/"; done
  [ -f "$2/select-gpu.sh" ] && cp "$2/select-gpu.sh" "$1/"
  cp "$3/README.txt" "$1/README.txt"; cp "$3/EXPECTED-TIME.txt" "$1/EXPECTED-TIME"
  [ -f "$3/defaults.env" ] && cp "$3/defaults.env" "$1/defaults.env"
  cp "$PROD/bin/p9sim" "$PROD/bin/SHA256-p9sim" "$PROD/bin/REQUIRES-glibc" "$PROD/bin/BUILD-GLIBC" "$1/bin/"
}
pack() {  # $1 = name
  tar --sort=name --owner=0 --group=0 --numeric-owner -C build -czf "build/$1.tar.gz" "$1"
  ( cd build && sha256sum "$1.tar.gz" > "$1.tar.gz.sha256" )
  cat "build/$1.tar.gz.sha256"
}

# group V5 (A100)
V5=build/p9pair-v5-$REV
common "$V5" bb/v5 pair/v5
cp "$PROD/bin/p9gpu" "$PROD/bin/SHA256-p9gpu" "$PROD/bin/NVCC-VERSION" "$V5/bin/"
grep '^REG_' "$PROD/params.env" > "$V5/check/regression.env"
grep -E '^(regression|deep)-' "$PROD/check/EXPECTED" > "$V5/check/EXPECTED.prod"
for f in $(awk '{ print $3 }' "$V5/check/EXPECTED.prod"); do cp "$PROD/$f" "$V5/check/jobs/"; done
$PY -I - "$V5" "$CPU" "$PAIRJOBS" "$SEEDS" <<'PY'
import json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, "tools")
import p9job
out, cpu, src_root, seeds = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), [int(s) for s in sys.argv[4].split()]
SETS = {"A": {"p9": "m_earth=7,a=500,e=0.33,inc=17,varpi=250,Omega=100,M=0", "r_p9": "2.0824", "col_p9": "17248.4"},
        "B": {"p9": "m_earth=5,a=300,e=0.15,inc=17,varpi=254,Omega=108,M=0", "r_p9": "1.8616", "col_p9": "15418.4"}}
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
for s in seeds:
    st = "A" if s < 340 else "B"
    name, src = f"PV5-s{s}", src_root / "v5" / f"s{s}"
    dst = out / "jobs" / name
    dst.mkdir(parents=True)
    job = json.loads((src / "job.json").read_text()); p = job["params"]; enc = p["removal"]["encounter"]
    assert enc["method"] == "smooth" and enc["planet_substeps"] == 8 and float(p["dt_yr"]) == 0.5 and float(p["removal"]["r_in_au"]) == 4.5
    assert p["ic"]["seed"] == s and p["ic"]["n_tp"] == 4000 and float(p["t_end_yr"]) == 2e8 and int(p["snapshots"]) == 200
    assert p["ic"]["p9"] == SETS[st]["p9"] and p["ic"]["p9_plane"] == "invariable"
    assert enc["radii_au"] == {"Jupiter": "7.4300", "Saturn": "4.9708", "Uranus": "2.6572", "Neptune": "3.1036", "P9": SETS[st]["r_p9"]}, enc["radii_au"]
    assert enc["collision"]["radii_km"]["P9"] == SETS[st]["col_p9"] and enc["collision"]["radii_km"]["Neptune"] == "24764.0"
    env = {"P9_ENCOUNTER_METHOD": "smooth", "P9_ENCOUNTER_RADII": p9job.encounter_env(job), "P9_COLLISION_RADII": p9job.collision_env(job),
           "P9_PLANET_SUBSTEPS": str(enc["planet_substeps"]), "P9_R_IN": repr(float(p["removal"]["r_in_au"]))}
    (dst / "params.env").write_text(f"# the settings of jobs/{name}/job.json ({job['id'][:16]}...), dt {p['dt_yr']} yr (in input.sa)\n"
                                    + "".join(f"{k}={v}\n" for k, v in env.items()) + "P9GPU_REAL=double\nSEGMENT_YR=20000000\nSEGMENTS=10\nSNAPSHOTS_PER_SEGMENT=20\n")
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
print(f"V5 check/EXPECTED: {len(rows) - 1} check cases")
PY
pack "p9pair-v5-$REV"

# group M (CPU)
M=build/p9pair-merc-$REV
common "$M" pair/merc pair/merc
rmdir "$M/check/jobs"
$PY -I - "$M" "$PAIRJOBS" "$SEEDS" <<'PY'
import json, os, subprocess, sys
from pathlib import Path
out, src_root, seeds = Path(sys.argv[1]), Path(sys.argv[2]), [int(s) for s in sys.argv[3].split()]
sim = str(out / "bin/p9sim")
SETS = {"A": "m_earth=7,a=500,e=0.33,inc=17,varpi=250,Omega=100,M=0", "B": "m_earth=5,a=300,e=0.15,inc=17,varpi=254,Omega=108,M=0"}
ENV = {"P9_R_IN": "4.5", "P9_ENCOUNTER_METHOD": "kick", "P9_ENCOUNTER_REMOVE": "1"}  # as p9job run sets them for these jobs
def run(sa, t_end, o):
    full = dict(os.environ, **ENV)
    for k in ("P9_ENCOUNTER_RADII", "P9_COLLISION_RADII", "P9_PLANET_SUBSTEPS", "P9_J2", "P9_FLYBY_OUT", "P9_REMOVED_OUT"):
        full.pop(k, None)
    r = subprocess.run([sim, "run", str(sa), repr(float(t_end)), "1", str(o)], env=full, capture_output=True, text=True, check=True)
    return [l for l in r.stdout.splitlines() if l.startswith("result_sha256=")][-1].split()[0].split("=")[1]
rows = ["# name job t_mid t_end expected_result_sha256 (bin/p9sim on the reference machine)"]
tmp = out / "check/tmp"; tmp.mkdir(parents=True)
for s in seeds:
    st = "A" if s < 340 else "B"
    for k in range(16):
        name, src = f"PM-s{s}-part{k:02d}", src_root / "m" / f"s{s}" / f"part{k:02d}"
        dst = out / "jobs" / name
        dst.mkdir(parents=True)
        job = json.loads((src / "job.json").read_text()); p = job["params"]
        assert p["integrator"] == "mercurius" and p["r_crit_hill"] == 3 and float(p["dt_yr"]) == 0.5
        assert p["ic"]["seed"] == s and p["ic"]["n_tp"] == 4000 and p["ic"]["tp_from"] == 250 * k and p["ic"]["tp_to"] == 250 * (k + 1)
        assert p["ic"]["p9"] == SETS[st] and p["ic"]["p9_plane"] == "invariable"
        assert float(p["removal"]["r_in_au"]) == 4.5 and not p["removal"]["encounter"]["radii_au"] and "method" not in p["removal"]["encounter"]
        assert float(p["t_end_yr"]) == 2e8 and int(p["snapshots"]) == 200
        (dst / "params.env").write_text(f"# the settings of jobs/{name}/job.json ({job['id'][:16]}...), MERCURIUS and dt in input.sa\n"
                                        + "".join(f"{a}={b}\n" for a, b in ENV.items()) + "SEGMENT_YR=20000000\nSEGMENTS=10\nSNAPSHOTS_PER_SEGMENT=20\n")
        for f in ("job.json", "input.sa"):
            (dst / f).write_bytes((src / f).read_bytes())
        (dst / "INPUT-SHA256").write_text(subprocess.run(["sha256sum", str(src / "input.sa")], capture_output=True, text=True).stdout.split()[0] + "\n")
    name = f"PM-s{s}-part00"; inp = out / "jobs" / name / "input.sa"
    rows.append(f"{name} {name} - 10000.0 {run(inp, 1e4, tmp / 'a.sa')}")
    run(inp, 5e3, tmp / "b.sa")
    subprocess.run([sim, "last", str(tmp / "b.sa"), str(tmp / "b-in.sa")], check=True, stdout=subprocess.DEVNULL)
    rows.append(f"{name}-chain {name} 5000.0 10000.0 {run(tmp / 'b-in.sa', 1e4, tmp / 'c.sa')}")
for s in (331, 341):
    inp = out / f"jobs/PM-s{s}-part00/input.sa"
    rows.append(f"PM-s{s}-part00-1myr PM-s{s}-part00 - 1000000.0 {run(inp, 1e6, tmp / 'd.sa')}")
for f in tmp.iterdir():
    f.unlink()
tmp.rmdir()
(out / "check/EXPECTED").write_text("\n".join(rows) + "\n")
print(f"M check/EXPECTED: {len(rows) - 1} check cases, {len(list((out / 'jobs').iterdir()))} slices")
PY
pack "p9pair-merc-$REV"
ls -la "build/p9pair-v5-$REV.tar.gz" "build/p9pair-merc-$REV.tar.gz"
