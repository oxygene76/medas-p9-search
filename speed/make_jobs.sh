#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Jobs of the speed comparison on appmdp-05 (speed/README.txt) into runs/speed2/jobs/:
#   the four jobs of the notebook comparison (runs/speed, 2026-10-23), unchanged: 4,000 test bodies, 10 Myr
#     cpu-whfast-4k-10m  cpu-merc-4k-10m  gpu-wh-4k-10m  gpu-v5-4k-10m
#   whole CPU (one copy of the same slice per core): cpu-whfast-4k-1m  cpu-merc-4k-1m
#   GPU scaling series, 1 Myr: gpu-wh-{4k,16k,64k,256k}-1m  gpu-v5-{4k,16k,64k,256k}-1m
# All as runs/speed: Brown & Batygin (2021) configuration, seed 101, a 150-500 au, q 30-50 au, i 0-25 deg,
# r_in 4.5 au, dt 0.5 yr. 1-Myr jobs write one snapshot (the end).
set -eu
cd "$(dirname "$0")/.."
J=runs/speed2/jobs
mkdir -p "$J"
for p in whfast-cpu:cpu-whfast-4k-10m merc-cpu:cpu-merc-4k-10m wh-gpu:gpu-wh-4k-10m v5-gpu:gpu-v5-4k-10m; do
	src=runs/speed/${p%%:*}; dst=$J/${p#*:}
	[ -d "$dst" ] || { mkdir -p "$dst"; cp "$src/job.json" "$src/input.sa" "$src/ic.txt" "$dst/"; }
done
mk() { # name n_tp args...
	n=$1; shift; tp=$1; shift
	[ -d "$J/$n" ] && return 0
	build/venv/bin/python -I tools/p9job.py make --out "$J/$n" --t-end 1e6 --snapshots 1 --n-tp "$tp" --seed 101 \
		--a-range 150 500 --q-range 30 50 --inc-range 0 25 --r-in 4.5 "$@" > /dev/null
}
mk cpu-whfast-4k-1m 4000 --no-encounters --p9sim build/equiv-bin/p9sim
mk cpu-merc-4k-1m 4000 --no-encounters --integrator mercurius --p9sim build/equiv-bin/p9sim
for s in 4k:4000 16k:16000 64k:64000 256k:256000; do
	mk gpu-wh-${s%%:*}-1m ${s#*:} --program p9gpu --p9sim build/equiv-bin/p9gpu --encounter-method step --no-removal
	mk gpu-v5-${s%%:*}-1m ${s#*:} --program p9gpu --p9sim build/equiv-bin/p9gpu --encounter-method smooth --planet-substeps 8
done
ls "$J"
