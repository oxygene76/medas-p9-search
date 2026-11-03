#!/bin/sh
# Builds the two packages of the paired long runs, seeds 110-112 (docs/long-runs-110-112-criteria.md in
# medas-p9-search, part of entry 3) from the jobs in runs/long (p9job make, the same settings as the equivalence
# jobs; made by tools/make_long_jobs.sh):
#   build/p9long-v5-<commit>.tar.gz    group V5 for the L40S: runs/long/v5/s110 ... s112 (p9gpu v5, smooth; 2,000
#                                      test particles, 0-4 Gyr, segments of 100 Myr, a snapshot every 10 Myr)
#   build/p9long-merc-<commit>.tar.gz  group M for CPU 1: runs/long/m/s110/part00 ... s112/part07
#                                      (MERCURIUS, slices of 250 test particles, segments of 20 Myr)
# The binaries are those of the production package p9prod-9a084ed (PROD, checked by sha256). Expected hashes of
# the checks: V5 jobs with p9gpu's CPU twin of this commit (the GPU's bits), regression and deep cases from the
# production package's check; M with the package's own p9sim on this machine (glibc-independent: same bits in
# ubuntu:22.04, docs/cause-analysis.md section 13 in medas-p9-search).
#   tools/make_long_jobs.sh, commit, then: PROD=../medas-p9-search-bb2021/build/p9prod-9a084ed tools/make_long_packages.sh
set -eu
cd "$(dirname "$0")/.."
REV=$(git rev-parse --short HEAD)
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "commit first" >&2; exit 1; }
PROD=${PROD:-../medas-p9-search-bb2021/build/p9prod-9a084ed}
PY=build/venv/bin/python
make -s gpu-cpu > /dev/null && make -s VARIANT=test > /dev/null
CPU=build/gpu-cpu/p9gpu
[ "$($CPU version)" = "program=p9gpu version=$REV" ] || { echo "build/gpu-cpu/p9gpu is not $REV" >&2; exit 1; }
for f in p9gpu p9sim; do
  [ "$(sha256sum "$PROD/bin/$f" | cut -d' ' -f1)" = "$(cut -d' ' -f1 "$PROD/bin/SHA256-$f")" ] || { echo "$PROD/bin/$f does not match its sha256" >&2; exit 1; }
done

common() {  # $1 = output directory, $2 = script directory
  rm -rf "$1" && mkdir -p "$1/src" "$1/gpu" "$1/third_party-src" "$1/bin" "$1/jobs" "$1/check/jobs"
  cp Makefile LICENSE "$1/"
  echo "$REV" > "$1/VERSION"
  echo "$REV ($(git log -1 --format=%cs))" > "$1/PACKAGE-VERSION"
  cp src/*.c src/*.h "$1/src/"; cp gpu/*.c gpu/*.cu gpu/*.cpp gpu/*.h "$1/gpu/"
  cp third_party/README.md third_party/rebound-5.2.2.tar.gz "$1/third_party-src/"
  for f in run-all.sh run-job.sh check.sh start.sh stop.sh status.sh; do cp "$2/$f" "$1/"; done
  [ -f "$2/select-gpu.sh" ] && cp "$2/select-gpu.sh" "$1/"
  cp "$2/README.txt" "$1/README.txt"; cp "$2/EXPECTED-TIME.txt" "$1/EXPECTED-TIME"
  cp "$PROD/bin/p9sim" "$PROD/bin/SHA256-p9sim" "$PROD/bin/REQUIRES-glibc" "$PROD/bin/BUILD-GLIBC" "$1/bin/"
}
pack() {  # $1 = name
  tar --sort=name --owner=0 --group=0 --numeric-owner -C build -czf "build/$1.tar.gz" "$1"
  ( cd build && sha256sum "$1.tar.gz" > "$1.tar.gz.sha256" )
  cat "build/$1.tar.gz.sha256"
}

# group V5 (GPU)
V5=build/p9long-v5-$REV
common "$V5" long/v5
cp "$PROD/bin/p9gpu" "$PROD/bin/SHA256-p9gpu" "$PROD/bin/NVCC-VERSION" "$V5/bin/"
grep '^REG_' "$PROD/params.env" > "$V5/check/regression.env"
grep -E '^(regression|deep)-' "$PROD/check/EXPECTED" > "$V5/check/EXPECTED.prod"
for f in $(awk '{ print $3 }' "$V5/check/EXPECTED.prod"); do cp "$PROD/$f" "$V5/check/jobs/"; done
$PY -I - "$V5" "$CPU" <<'PY'
import json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, "tools")
import p9job
out, cpu = Path(sys.argv[1]), sys.argv[2]
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
for s in range(110, 113):
    name, src = f"V5-s{s}", Path("runs/long/v5") / f"s{s}"
    dst = out / "jobs" / name
    dst.mkdir(parents=True)
    job = json.loads((src / "job.json").read_text()); p = job["params"]; enc = p["removal"]["encounter"]
    assert enc["method"] == "smooth" and "collision" in enc and float(p["t_end_yr"]) == 4e9 and int(p["snapshots"]) == 400
    assert p["ic"]["seed"] == s and p["ic"]["n_tp"] == 2000 and float(p["removal"]["r_in_au"]) == 4.5 and float(p["dt_yr"]) == 0.5
    # the encounter and collision radii of the production package (docs/bb2021-comparison-criteria.md, addendum 13)
    assert enc["radii_au"] == {"Jupiter": "7.4300", "Saturn": "4.9708", "Uranus": "2.6572", "Neptune": "3.1036", "P9": "2.0000"}
    assert enc["collision"]["radii_km"]["P9"] == "16564.6"
    env = {"P9_ENCOUNTER_METHOD": "smooth", "P9_ENCOUNTER_RADII": p9job.encounter_env(job), "P9_COLLISION_RADII": p9job.collision_env(job),
           "P9_PLANET_SUBSTEPS": str(enc["planet_substeps"]), "P9_R_IN": repr(float(p["removal"]["r_in_au"]))}
    (dst / "params.env").write_text(f"# the settings of jobs/{name}/job.json ({job['id'][:16]}...), dt {p['dt_yr']} yr (in input.sa)\n"
                                    + "".join(f"{k}={v}\n" for k, v in env.items()) + "P9GPU_REAL=double\nSEGMENT_YR=100000000\nSEGMENTS=40\nSNAPSHOTS_PER_SEGMENT=10\n")
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
print(f"V5 check/EXPECTED: {len(rows) - 1} check jobs")
PY
pack "p9long-v5-$REV"

# group M (CPU)
M=build/p9long-merc-$REV
common "$M" long/merc
rmdir "$M/check/jobs"
$PY -I - "$M" <<'PY'
import json, os, subprocess, sys
from pathlib import Path
out = Path(sys.argv[1]); sim = str(out / "bin/p9sim")
ENV = {"P9_R_IN": "4.5", "P9_ENCOUNTER_METHOD": "kick", "P9_ENCOUNTER_REMOVE": "1"}  # as p9job run sets them for these jobs
def run(sa, t_end, o):
    full = dict(os.environ, **ENV)
    for k in ("P9_ENCOUNTER_RADII", "P9_COLLISION_RADII", "P9_PLANET_SUBSTEPS", "P9_J2", "P9_FLYBY_OUT", "P9_REMOVED_OUT"):
        full.pop(k, None)
    r = subprocess.run([sim, "run", str(sa), repr(float(t_end)), "1", str(o)], env=full, capture_output=True, text=True, check=True)
    return [l for l in r.stdout.splitlines() if l.startswith("result_sha256=")][-1].split()[0].split("=")[1]
rows = ["# name job t_mid t_end expected_result_sha256 (bin/p9sim on the reference machine)"]
tmp = out / "check/tmp"; tmp.mkdir(parents=True)
for s in range(110, 113):
    for k in range(8):
        name, src = f"M-s{s}-part{k:02d}", Path("runs/long/m") / f"s{s}" / f"part{k:02d}"
        dst = out / "jobs" / name
        dst.mkdir(parents=True)
        job = json.loads((src / "job.json").read_text()); p = job["params"]
        assert p["integrator"] == "mercurius" and p["r_crit_hill"] == 3 and float(p["dt_yr"]) == 0.5
        assert p["ic"]["seed"] == s and p["ic"]["n_tp"] == 2000 and p["ic"]["tp_from"] == 250 * k and p["ic"]["tp_to"] == 250 * (k + 1)
        assert float(p["removal"]["r_in_au"]) == 4.5 and not p["removal"]["encounter"]["radii_au"] and "method" not in p["removal"]["encounter"]
        assert float(p["t_end_yr"]) == 4e9 and int(p["snapshots"]) == 400
        (dst / "params.env").write_text(f"# the settings of jobs/{name}/job.json ({job['id'][:16]}...), MERCURIUS and dt in input.sa\n"
                                        + "".join(f"{a}={b}\n" for a, b in ENV.items()) + "SEGMENT_YR=20000000\nSEGMENTS=200\nSNAPSHOTS_PER_SEGMENT=2\n")
        for f in ("job.json", "input.sa"):
            (dst / f).write_bytes((src / f).read_bytes())
        (dst / "INPUT-SHA256").write_text(subprocess.run(["sha256sum", str(src / "input.sa")], capture_output=True, text=True).stdout.split()[0] + "\n")
    name = f"M-s{s}-part00"; inp = out / "jobs" / name / "input.sa"
    rows.append(f"{name} {name} - 10000.0 {run(inp, 1e4, tmp / 'a.sa')}")
    run(inp, 5e3, tmp / "b.sa")
    subprocess.run([sim, "last", str(tmp / "b.sa"), str(tmp / "b-in.sa")], check=True, stdout=subprocess.DEVNULL)
    rows.append(f"{name}-chain {name} 5000.0 10000.0 {run(tmp / 'b-in.sa', 1e4, tmp / 'c.sa')}")
inp = out / "jobs/M-s110-part00/input.sa"
rows.append(f"M-s110-part00-1myr M-s110-part00 - 1000000.0 {run(inp, 1e6, tmp / 'd.sa')}")
for f in tmp.iterdir():
    f.unlink()
tmp.rmdir()
(out / "check/EXPECTED").write_text("\n".join(rows) + "\n")
print(f"M check/EXPECTED: {len(rows) - 1} check cases, {len(list((out / 'jobs').iterdir()))} slices")
PY
pack "p9long-merc-$REV"
ls -la "build/p9long-v5-$REV.tar.gz" "build/p9long-merc-$REV.tar.gz"
