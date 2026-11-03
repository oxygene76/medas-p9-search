#!/bin/sh
# Builds the speed comparison package (speed/README.txt) from a clean checkout:
#   tools/make_speed_package.sh  ->  build/p9speed-<commit>.tar.gz (+ .sha256)
# Needs: the jobs (speed/make_jobs.sh) with their reference results (speed/reference.sh, and runs/speed for the four
# jobs of the notebook comparison), and the unpacked production package build/p9prod-9a084ed (its binaries and
# sources are used unchanged).
set -eu
cd "$(dirname "$0")/.."
[ -z "$(git status --porcelain -- speed tools/make_speed_package.sh)" ] || { echo "speed/ or this script not committed"; exit 1; }
PROD=build/p9prod-9a084ed
J=runs/speed2/jobs
c=$(git rev-parse --short HEAD)
name=p9speed-$c
out=build/$name
rm -rf "$out"; mkdir -p "$out/bin" "$out/jobs" "$out/native/third_party"
for f in p9gpu p9sim; do
	[ "$(sha256sum "$PROD/bin/$f" | cut -d' ' -f1)" = "$(cut -d' ' -f1 "$PROD/bin/SHA256-$f")" ] || { echo "$PROD/bin/$f: sha256"; exit 1; }
	cp "$PROD/bin/$f" "$PROD/bin/SHA256-$f" "$out/bin/"
done
cp "$PROD/bin/NVCC-VERSION" "$PROD/bin/BUILD-GLIBC" "$PROD/bin/REQUIRES-glibc" "$out/bin/"
cp "$PROD/LICENSE" "$out/"
# the sources of the package's p9sim, to build it here with other flags (stage native)
cp "$PROD/Makefile" "$PROD/VERSION" "$out/native/"
cp -r "$PROD/src" "$out/native/src"
cp "$PROD/third_party-src/rebound-5.2.2.tar.gz" "$out/native/third_party/"
[ "$(sha256sum "$out/native/third_party/rebound-5.2.2.tar.gz" | cut -d' ' -f1)" = 86038080c4392c8c19c4df2004d1804b30ca2aebd3c0329bfd1b02afc41d6eda ] || { echo "rebound tarball: sha256"; exit 1; }
cp speed/speed.sh speed/report.py speed/README.txt "$out/"
# jobs: input, job, the settings p9job.py gives the program (run.env), the reference result hash (EXPECTED)
python3 -I - "$J" "$out/jobs" <<'PY'
import glob, hashlib, json, os, shutil, sys
src, dst = sys.argv[1], sys.argv[2]
notebook = {"cpu-whfast-4k-10m": "runs/speed/whfast-cpu-r*/result.json", "cpu-merc-4k-10m": "runs/speed/merc-cpu-r*/result.json",
            "gpu-wh-4k-10m": "runs/speed/wh-gpu/result-*.json", "gpu-v5-4k-10m": "runs/speed/v5-gpu/result-*.json"}
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
for d in sorted(glob.glob(os.path.join(src, "*"))):
    n = os.path.basename(d)
    job = json.load(open(os.path.join(d, "job.json")))
    assert sha(os.path.join(d, "input.sa")) == job["input"]["sha256"], n
    results = [json.load(open(p)) for p in sorted(glob.glob(notebook[n]))] if n in notebook else [json.load(open(os.path.join(d, "result.json")))]
    assert results and all(r["job_id"] == job["id"] for r in results), n
    hashes = {r["result_sha256"] for r in results}
    assert len(hashes) == 1, (n, hashes)
    o = os.path.join(dst, n)
    os.makedirs(o)
    for f in ("input.sa", "job.json", "run.env"):
        shutil.copy(os.path.join(d, f), o)
    open(os.path.join(o, "EXPECTED"), "w").write(hashes.pop() + "\n")
    open(os.path.join(o, "N_TP"), "w").write(f"{job['params']['ic']['n_tp']}\n")
    where = (f"notebook comparison 2026-10-23 ({notebook[n]}), {len(results)} runs alike" if n in notebook else
             "reference run on the notebook (RTX 5080 Laptop GPU / its CPU), speed/reference.sh")
    open(os.path.join(o, "REFERENCE"), "w").write(f"{where}; wall {', '.join(str(r['wall_s']) for r in results)} s\n")
    print(n, open(os.path.join(o, "EXPECTED")).read().strip()[:16], job["params"]["ic"]["n_tp"], job["params"]["t_end_yr"])
PY
git rev-parse HEAD > "$out/VERSION"
(cd "$out" && find . -type f ! -name SHA256SUMS | LC_ALL=C sort | xargs sha256sum > SHA256SUMS)
(cd build && find "$name" -print0 | LC_ALL=C sort -z | tar --null --no-recursion -T - --owner=0 --group=0 --mtime=@0 -cf - | gzip -n -9 > "$name.tar.gz" && sha256sum "$name.tar.gz" > "$name.tar.gz.sha256")
cat "build/$name.tar.gz.sha256"
