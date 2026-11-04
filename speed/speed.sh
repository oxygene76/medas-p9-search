#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Speed comparison p9gpu (GPU) against REBOUND in p9sim (CPU cores), with pinned cores and a scaling series on the
# GPUs. Every run is the same job as on the reference machine and counts only if it gives the reference result
# hash (jobs/<job>/EXPECTED). Results go to $RES (default ./results-<host>); nothing outside this directory changes.
#
#   bash speed.sh env              the conditions: CPU, NUMA, SMT, governor, turbo, load, GPUs, driver, versions (1 min)
#   bash speed.sh gpu NAME         on the GPU whose name contains NAME (A100, L40S, H100 ...): the two 4,000-body
#                                  jobs over 10 Myr and the scaling series 4k/16k/64k/256k over 1 Myr, both
#                                  methods, REPS times each; host thread pinned to one core     (A100 ~1.5 h, L40S ~3.5 h)
#   bash speed.sh cpu1             one core per process: WHFast and MERCURIUS over 10 Myr, REPS times each, all at
#                                  once, each on its own physical core of one NUMA node                 (~4-6 h)
#   bash speed.sh native           p9sim built here twice from the sources (standard flags and -march=native, both
#                                  -ffp-contract=off): hash against the reference, time difference (1-Myr jobs) (~40 min)
#   bash speed.sh cpuall           the whole CPU: the 1-Myr slice on every physical core at once, WHFast then
#                                  MERCURIUS                                                             (~1-2 h)
#   bash speed.sh report           REPORT.txt: throughput in test-body steps per second, ratios
#   bash speed.sh start day        in the background (nohup): env, native, gpu A100, cpu1        (~6-9 h)
#   bash speed.sh start night      in the background: env, gpu L40S, cpuall, report               (~5-6 h)
#                                  (or start STAGE...: env native cpu1 cpuall report gpu:NAME); log in $RES/speed.log
#   bash speed.sh status | stop
#
# Before each stage: no compute process on the GPU being measured (by UUID), and the background load over 60 s at
# most LOAD_MAX busy logical CPUs (default 2); both are logged.
# Settings (environment): REPS (3), NICE (10), LOAD_MAX (2), FORCE=1 (measure although the checks fail, noted),
# SMT=1 (cpuall also on the second hardware thread of each core), NODE (NUMA node for cpu1 and native, default 0),
# CPUS (use only these logical CPUs; for tests), RES (result directory).
set -uo pipefail
export LC_ALL=C   # numbers with a decimal point in every file: bash printf (and mawk) follow LC_NUMERIC, e.g. de_DE writes 474,000
cd "$(dirname "$0")"
HERE=$PWD
RES=${RES:-$HERE/results-$(hostname -s)}
REPS=${REPS:-3}
NICE=${NICE:-10}
mkdir -p "$RES"
TSV=$RES/RESULTS.tsv
[ -s "$TSV" ] || printf 'stage\tdevice\tjob\tbuild\trep\tcpu\tn_tp\tsteps\twall_s\twall_shell_s\tt_start\tt_end\tresult_sha256\tverdict\n' > "$TSV"
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$RES/speed.log"; }
for v in $(env | grep -o '^P9[A-Z0-9_]*' || true); do unset "$v"; done   # only the job's settings reach the programs

sha() { sha256sum "$1" | cut -d' ' -f1; }
for f in bin/p9gpu bin/p9sim; do
	[ "$(sha "$f")" = "$(cut -d' ' -f1 "bin/SHA256-$(basename "$f")")" ] || { echo "$f does not match its sha256"; exit 2; }
done

# logical CPUs, one per physical core (the first hardware thread), on NUMA node $1 or on all nodes ("all");
# CPUS="a b c" keeps only those (for a test on a machine that is also used otherwise)
only() { if [ -n "${CPUS:-}" ]; then grep -x -F -f <(echo "$CPUS" | tr ' ' '\n'); else cat; fi; }
cores() {
	lscpu -p=CPU,CORE,SOCKET,NODE | grep -v '^#' | awk -F, -v n="$1" '{ node = ($4 == "" ? 0 : $4) }
		(n == "all" || node == n) && !seen[$2 "," $3]++ { print $1 }' | only
}
all_threads() { lscpu -p=CPU | grep -v '^#' | only; }
node_of() { lscpu -p=CPU,NODE | grep -v '^#' | awk -F, -v c="$1" '$1 == c { print ($2 == "" ? 0 : $2) }'; }
pin() { # cpu -> the command prefix that pins to it (and its node's memory, with numactl)
	if command -v numactl >/dev/null && numactl -H >/dev/null 2>&1; then echo "numactl --physcpubind=$1 --membind=$(node_of "$1")"
	else echo "taskset -c $1"; fi
}

busy() { # seconds -> logical CPUs busy on average over that time (from /proc/stat: all but idle and iowait)
	local a b
	a=$(head -n 1 /proc/stat); sleep "$1"; b=$(head -n 1 /proc/stat)
	echo "$a $b" | awk -v n="$(nproc --all)" '{ for (i = 2; i <= 9; i++) { t1 += $i; t2 += $(i + 11) }   # user..steal (guest is inside user)
		i1 = $5 + $6; i2 = $16 + $17; printf "%.2f", n * (1 - (i2 - i1) / (t2 - t1)) }'
}

quiet() { # stage [GPU UUID] -> refuse to measure while other work runs (FORCE=1: measure anyway, noted)
	# GPU: only the card being measured is checked, by its UUID: no compute process on it. CPU: the background load
	# (other services, e.g. the notary or a read node) is measured over 60 s and logged; the stage starts if it is at
	# most LOAD_MAX busy logical CPUs.
	local stage=$1 uuid=${2:-} why="" apps bg
	if [ -n "$uuid" ]; then
		apps=$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader 2>/dev/null | awk -F', ' -v u="$uuid" '$1 == u')
		log "$stage: on $uuid $(nvidia-smi -i "$uuid" --query-gpu=memory.used,utilization.gpu,power.draw,temperature.gpu --format=csv,noheader 2>/dev/null) (memory, utilisation, power, temperature)"
		[ -n "$apps" ] && why="$why processes on the measured GPU: $(echo "$apps" | cut -d, -f2- | tr '\n' ';')"
		other=$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name --format=csv,noheader 2>/dev/null | awk -F', ' -v u="$uuid" '$1 != u' | cut -d, -f2- | tr '\n' ';')
		[ -n "$other" ] && log "$stage: note: processes on the other GPUs (not checked):$other"
	fi
	bg=$(busy 60)
	{ date -u +%FT%TZ; top -b -n 1 -o %CPU -w 200 2>/dev/null | head -n 25 || ps -eo pid,user,pcpu,etime,comm --sort=-pcpu | head -n 20; } > "$RES/background-$stage.txt"
	log "$stage: background load before the stage: $bg busy logical CPUs over 60 s (of $(nproc --all); limit LOAD_MAX ${LOAD_MAX:-2}); load average $(cut -d' ' -f1-3 /proc/loadavg)"
	awk -v l="$bg" -v m="${LOAD_MAX:-2}" 'BEGIN { exit !(l > m) }' && why="$why background load $bg busy CPUs > ${LOAD_MAX:-2};"
	if [ -n "$why" ]; then
		if [ "${FORCE:-0}" = 1 ]; then log "note: $stage runs although:$why (FORCE=1)"
		else log "$stage NOT STARTED:$why (FORCE=1 to measure anyway)"; return 1; fi
	fi
	return 0
}

stage_env() {
	local f=$RES/env.txt
	{
		echo "== $(date -u +%FT%TZ) $(hostname -s), package $(cat VERSION), p9gpu $(sha bin/p9gpu), p9sim $(sha bin/p9sim)"
		echo "== kernel: $(uname -r); virtualisation: $(systemd-detect-virt 2>/dev/null || echo unknown)"
		echo "== lscpu"; lscpu
		echo "== topology (CPU,CORE,SOCKET,NODE)"; lscpu -p=CPU,CORE,SOCKET,NODE | grep -v '^#' | tr '\n' ' '; echo
		echo "== numactl -H"; numactl -H 2>&1 || echo "numactl not installed"
		echo "== SMT: $(cat /sys/devices/system/cpu/smt/active 2>/dev/null || echo n/a) (control: $(cat /sys/devices/system/cpu/smt/control 2>/dev/null || echo n/a))"
		echo "== governor: $(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null | sort | uniq -c | tr '\n' ' ' || true)"
		echo "== driver: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver 2>/dev/null || echo n/a)"
		echo "== turbo: intel_pstate no_turbo=$(cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || echo n/a), cpufreq boost=$(cat /sys/devices/system/cpu/cpufreq/boost 2>/dev/null || echo n/a)"
		echo "== MHz now: $(grep MHz /proc/cpuinfo | awk '{ print $4 }' | sort -n | awk '{ a[NR] = $1 } END { print "min", a[1], "median", a[int((NR + 1) / 2)], "max", a[NR] }')"
		echo "== memory"; free -m
		echo "== load: $(cat /proc/loadavg)"
		echo "== top processes"; ps -eo pid,user,pcpu,pmem,etime,comm --sort=-pcpu | head -n 15
		if command -v nvidia-smi >/dev/null; then
			echo "== nvidia-smi"; nvidia-smi
			echo "== GPUs"; nvidia-smi --query-gpu=index,name,uuid,pci.bus_id,driver_version,vbios_version,persistence_mode,power.limit,power.max_limit,clocks.max.sm,clocks.sm,clocks.applications.graphics,temperature.gpu,ecc.mode.current,pcie.link.gen.current,pcie.link.width.current --format=csv
			echo "== compute processes"; nvidia-smi --query-compute-apps=gpu_name,gpu_uuid,pid,process_name,used_memory --format=csv
		fi
		echo "== GPU NUMA nodes"; for d in /sys/bus/pci/drivers/nvidia/0000:*; do [ -e "$d/numa_node" ] && echo "$(basename "$d") $(cat "$d/numa_node")"; done
	} > "$f" 2>&1
	log "conditions written to $f"
	grep -E '^== (SMT|governor|turbo|load|virtualisation|kernel)' "$f" | tee -a "$RES/speed.log"
}

# one run: stage device job build rep cpu binary [extra prefix] -> one line in RESULTS.tsv
run_job() {
	local stage=$1 dev=$2 j=$3 build=$4 rep=$5 cpu=$6 bin=$7 d envs args t snaps t0 t1 rc line got exp verdict n steps wall
	d=$RES/runs/$stage/$dev/$j-$build-r$rep
	rm -rf "$d"; mkdir -p "$d"
	envs=$(grep '^P9' "jobs/$j/run.env" | sed "s|^P9_FLYBY_OUT=.*|P9_FLYBY_OUT=$d/flybys.tsv|")
	args=$(sed -n 's/^ARGS=//p' "jobs/$j/run.env")   # run input.sa T_END SNAPSHOTS output.sa final.state
	t=$(echo "$args" | cut -d' ' -f3); snaps=$(echo "$args" | cut -d' ' -f4)
	t0=$(date +%s.%N)
	# shellcheck disable=SC2046,SC2086
	env $envs $(pin "$cpu") nice -n "$NICE" "$bin" run "jobs/$j/input.sa" "$t" "$snaps" "$d/output.sa" "$d/final.state" > "$d/result.txt" 2> "$d/stderr.txt"
	rc=$?
	t1=$(date +%s.%N)
	line=$(grep '^result_sha256=' "$d/result.txt" | tail -n 1)
	got=$(echo "$line" | sed -n 's/^result_sha256=\([0-9a-f]*\).*/\1/p')
	exp=$(cat "jobs/$j/EXPECTED")
	if [ "$rc" != 0 ] || [ -z "$got" ]; then verdict=FAILED; elif [ "$got" = "$exp" ]; then verdict=SAME; else verdict=DIFFERENT; fi
	n=$(cat "jobs/$j/N_TP")
	steps=$(echo "$line" | tr ' ' '\n' | sed -n 's/^steps=//p')
	wall=$(echo "$line" | tr ' ' '\n' | sed -n 's/^wall_s=//p')
	rm -f "$d/output.sa"   # the result hash covers it; the runs of 256,000 bodies would fill the disk
	printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%.3f\t%.3f\t%.3f\t%s\t%s\n' "$stage" "$dev" "$j" "$build" "$rep" "$cpu" "$n" "${steps:-0}" "${wall:-0}" \
		"$(awk -v a="$t0" -v b="$t1" 'BEGIN { print b - a }')" "$t0" "$t1" "${got:-none}" "$verdict" >> "$TSV"
	log "$stage $dev $j $build r$rep cpu $cpu: $verdict, wall ${wall:-?} s"
}

cpu_sampler() { # file -> background: MHz of every logical CPU every 10 s (as the kernel reports it)
	while :; do echo "$(date +%s) $(grep MHz /proc/cpuinfo | awk '{ printf "%s ", $4 }')" >> "$1"; sleep 10; done
}

stage_gpu() { # NAME
	local name=${1:?a GPU name, e.g. A100 or L40S} uuid bus node cpu dev mon j r n
	uuid=$(nvidia-smi --query-gpu=uuid,name --format=csv,noheader | awk -F', ' -v n="$name" 'index($2, n) { print $1; exit }')
	[ -n "$uuid" ] || { log "gpu $name: no such GPU"; nvidia-smi -L; return 1; }
	quiet "gpu-$name" "$uuid" || return 1
	dev=$(nvidia-smi -i "$uuid" --query-gpu=name --format=csv,noheader | tr ' ' '_')
	bus=$(nvidia-smi -i "$uuid" --query-gpu=pci.bus_id --format=csv,noheader | sed 's/^0000//' | tr 'A-F' 'a-f')
	node=$(cat "/sys/bus/pci/devices/$bus/numa_node" 2>/dev/null || echo -1); [ "$node" -ge 0 ] 2>/dev/null || node=0
	cpu=$(cores "$node" | tail -n 1)   # the host part (the planets) runs on one core near the GPU
	export CUDA_VISIBLE_DEVICES=$uuid
	log "gpu $name: $dev $uuid (bus $bus, node $node), host thread on CPU $cpu, $REPS repetitions"
	TZ=UTC nvidia-smi -i "$uuid" --query-gpu=timestamp,clocks.sm,clocks_event_reasons.active,power.draw,temperature.gpu,utilization.gpu,memory.used \
		--format=csv,nounits -l 1 > "$RES/gpu-$dev-monitor.csv" 2>&1 &
	mon=$!
	for j in gpu-wh-4k-10m gpu-v5-4k-10m; do
		for r in $(seq "$REPS"); do run_job gpu "$dev" "$j" bin "$r" "$cpu" bin/p9gpu; done
	done
	for n in 4k 16k 64k 256k; do
		for j in gpu-wh-$n-1m gpu-v5-$n-1m; do
			for r in $(seq "$REPS"); do run_job gpu "$dev" "$j" bin "$r" "$cpu" bin/p9gpu; done
		done
	done
	kill "$mon" 2>/dev/null; wait "$mon" 2>/dev/null
	unset CUDA_VISIBLE_DEVICES
	log "gpu $name: done"
}

batch() { # stage label job:build:binary... -> one process per entry, each on its own core of $CORES, all at once
	local stage=$1 label=$2 i=0 e pids="" cpu mon
	shift 2
	local list=($CORES)
	[ "${#list[@]}" -ge "$#" ] || { log "$stage: $# processes but only ${#list[@]} cores ($CORES)"; return 1; }
	cpu_sampler "$RES/cpu-$stage-$label-mhz.txt" & mon=$!
	for e in "$@"; do
		IFS=: read -r j build bin rep <<< "$e"
		run_job "$stage" "$label" "$j" "$build" "$rep" "${list[$i]}" "$bin" &
		pids="$pids $!"; i=$((i + 1))
	done
	# shellcheck disable=SC2086
	wait $pids
	kill "$mon" 2>/dev/null; wait "$mon" 2>/dev/null
}

stage_cpu1() {
	quiet cpu1 || return 1
	local r e=()
	CORES=$(cores "${NODE:-0}" | tac | tr '\n' ' ')   # from the last core on: CPU 0 takes most interrupts
	for r in $(seq "$REPS"); do e+=("cpu-whfast-4k-10m:bin:bin/p9sim:$r" "cpu-merc-4k-10m:bin:bin/p9sim:$r"); done
	log "cpu1: ${#e[@]} single-core runs over 10 Myr at once on node ${NODE:-0}, one per physical core"
	batch cpu1 node${NODE:-0} "${e[@]}"
	log "cpu1: done"
}

stage_native() {
	if ! command -v make >/dev/null || ! command -v gcc >/dev/null; then
		log "native NOT RUN: no gcc or make here (e.g. apt install build-essential)"; return 1
	fi
	quiet native || return 1
	local b r extra e=()
	[ -d native/third_party/rebound-5.2.2 ] || tar -xzf native/third_party/rebound-5.2.2.tar.gz -C native/third_party
	for b in std native; do
		extra=""; [ "$b" = native ] && extra=-march=native
		rm -rf "native/build/$b"
		make -s -C native VARIANT="$b" CC=gcc CFLAGS_EXTRA="$extra" > "$RES/native-build-$b.txt" 2>&1 ||
			{ log "native: build $b failed (see $RES/native-build-$b.txt)"; return 1; }
		log "native: built $b: $(cat "native/build/$b/BUILD-FLAGS"), $(gcc --version | head -n 1), sha256 $(sha "native/build/$b/p9sim")"
	done
	CORES=$(cores "${NODE:-0}" | tac | tr '\n' ' ')   # from the last core on: CPU 0 takes most interrupts
	for r in $(seq "$REPS"); do
		for b in std native; do e+=("cpu-whfast-4k-1m:$b:native/build/$b/p9sim:$r" "cpu-merc-4k-1m:$b:native/build/$b/p9sim:$r"); done
	done
	log "native: ${#e[@]} single-core runs over 1 Myr at once on node ${NODE:-0}"
	batch native node${NODE:-0} "${e[@]}"
	log "native: done"
}

stage_cpuall() {
	local j c e r label=all
	if [ "${SMT:-0}" = 1 ]; then CORES=$(all_threads | tr '\n' ' '); label=all-smt; else CORES=$(cores all | tr '\n' ' '); fi
	for j in cpu-whfast-4k-1m cpu-merc-4k-1m; do
		quiet "cpuall-$j" || return 1
		e=(); r=1
		for c in $CORES; do e+=("$j:bin:bin/p9sim:$r"); r=$((r + 1)); done
		log "cpuall: $j on ${#e[@]} cores at once (SMT=${SMT:-0})"
		batch cpuall "$label" "${e[@]}"
	done
	log "cpuall: done"
}

stage_report() {
	python3 -I report.py "$TSV" "$RES" | tee "$RES/REPORT.txt"
}

case "${1:-}" in
env) stage_env ;;
gpu) stage_gpu "${2:-}" ;;
cpu1) stage_cpu1 ;;
native) stage_native ;;
cpuall) stage_cpuall ;;
report) stage_report ;;
run-block)
	shift
	echo $$ > "$RES/speed.pid"   # started by "start" through setsid: this PID is also the process group
	trap 'rm -f "$RES/speed.pid"' EXIT
	log "== block: $*"
	for s in "$@"; do
		case "$s" in
		env) stage_env ;; native) stage_native ;; cpu1) stage_cpu1 ;; cpuall) stage_cpuall ;; report) stage_report ;;
		gpu:*) stage_gpu "${s#gpu:}" ;;
		*) log "unknown stage $s" ;;
		esac || log "block: stage $s did not complete"
	done
	log "== block done: $*" ;;
start)
	shift
	case "${1:-}" in
	day) set -- env native gpu:A100 cpu1 ;;
	night) set -- env gpu:L40S cpuall report ;;
	'') echo "start day | start night | start STAGE... (env native cpu1 cpuall report gpu:NAME)"; exit 2 ;;
	esac
	[ -s "$RES/speed.pid" ] && kill -0 "$(cat "$RES/speed.pid")" 2>/dev/null && { echo "already running: PID $(cat "$RES/speed.pid")"; exit 1; }
	nohup setsid bash "$0" run-block "$@" >> "$RES/speed.out" 2>&1 < /dev/null &
	sleep 2
	echo "started: $*; PID $(cat "$RES/speed.pid" 2>/dev/null) (= its process group); log: $RES/speed.log" ;;
status)
	if [ -s "$RES/speed.pid" ] && kill -0 "$(cat "$RES/speed.pid")" 2>/dev/null; then echo "running: PID $(cat "$RES/speed.pid")"; else echo "not running"; fi
	tail -n 5 "$RES/speed.log" 2>/dev/null
	echo "runs: $(($(wc -l < "$TSV") - 1)), not SAME: $(awk -F'\t' 'NR > 1 && $14 != "SAME"' "$TSV" | wc -l)" ;;
stop)
	[ -s "$RES/speed.pid" ] || { echo "no PID file"; exit 1; }
	pid=$(cat "$RES/speed.pid")
	ps -o pid,pgid,etime,args -g "$pid" 2>/dev/null
	kill -TERM -"$pid" && echo "stopped process group $pid" && rm -f "$RES/speed.pid" ;;
*) sed -n '2,27p' "$0"; exit 2 ;;
esac
