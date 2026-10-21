#!/bin/sh
# Builds the package of the cause search for the GPU server (cause/README-cause.txt) from the jobs in runs/J1-dt025 and
# runs/J2-p9zone21 (p9job make). The binaries are those of the production package p9prod-9a084ed (PROD, checked by
# sha256; integrator identical to v5). Expected hashes of the job checks: p9gpu's CPU twin of this commit; regression
# and deep cases from the production package's check.
#   PROD=../medas-p9-search-bb2021/build/p9prod-9a084ed tools/make_cause_package.sh -> build/p9cause-<commit>.tar.gz
set -eu
cd "$(dirname "$0")/.."
REV=$(git rev-parse --short HEAD)
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "commit first" >&2; exit 1; }
PROD=${PROD:-../medas-p9-search-bb2021/build/p9prod-9a084ed}
PY=build/venv/bin/python
make -s gpu-cpu > /dev/null && make -s VARIANT=test > /dev/null
CPU=build/gpu-cpu/p9gpu
[ "$($CPU version)" = "program=p9gpu version=$REV" ] || { echo "build/gpu-cpu/p9gpu is not $REV" >&2; exit 1; }
OUT=build/p9cause-$REV
rm -rf "$OUT" && mkdir -p "$OUT/src" "$OUT/gpu" "$OUT/third_party-src" "$OUT/bin" "$OUT/jobs" "$OUT/check/jobs"
cp Makefile LICENSE "$OUT/"
echo "$REV" > "$OUT/VERSION"
echo "$REV ($(git log -1 --format=%cs))" > "$OUT/PACKAGE-VERSION"
cp src/*.c src/*.h "$OUT/src/"; cp gpu/*.c gpu/*.cu gpu/*.cpp gpu/*.h "$OUT/gpu/"
cp third_party/README.md third_party/rebound-5.2.2.tar.gz "$OUT/third_party-src/"
cp cause/run-all.sh cause/run-job.sh cause/check.sh cause/start.sh cause/stop.sh cause/status.sh "$OUT/"
cp cause/README-cause.txt "$OUT/README.txt"; cp cause/EXPECTED-TIME.txt "$OUT/EXPECTED-TIME"
for f in p9gpu p9sim; do
  [ "$(sha256sum "$PROD/bin/$f" | cut -d' ' -f1)" = "$(cut -d' ' -f1 "$PROD/bin/SHA256-$f")" ] || { echo "$PROD/bin/$f does not match its sha256" >&2; exit 1; }
done
cp "$PROD/bin/p9gpu" "$PROD/bin/p9sim" "$PROD/bin/SHA256-p9gpu" "$PROD/bin/SHA256-p9sim" "$PROD/bin/REQUIRES-glibc" "$PROD/bin/NVCC-VERSION" "$PROD/bin/BUILD-GLIBC" "$OUT/bin/"
grep '^REG_' "$PROD/params.env" > "$OUT/check/regression.env"
grep -E '^(regression|deep)-' "$PROD/check/EXPECTED" > "$OUT/check/EXPECTED.prod"
for f in $(awk '{ print $3 }' "$OUT/check/EXPECTED.prod"); do cp "$PROD/$f" "$OUT/check/jobs/"; done
$PY -I - "$OUT" "$CPU" <<'PY'
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
for name in ("J1-dt025", "J2-p9zone21"):
    src, dst = Path("runs") / name, out / "jobs" / name
    dst.mkdir(parents=True)
    job = json.loads((src / "job.json").read_text()); p = job["params"]; enc = p["removal"]["encounter"]
    assert enc["method"] == "smooth" and float(p["t_end_yr"]) == 2e8 and int(p["snapshots"]) == 200
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
print(f"check/EXPECTED: {len(rows) - 1} check jobs")
PY
tar --sort=name --owner=0 --group=0 --numeric-owner -C build -czf "$OUT.tar.gz" "p9cause-$REV"
( cd build && sha256sum "p9cause-$REV.tar.gz" > "p9cause-$REV.tar.gz.sha256" )
cat "$OUT.tar.gz.sha256"
ls -la "$OUT.tar.gz"
