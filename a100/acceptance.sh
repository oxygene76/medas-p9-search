#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Acceptance test of the A100 in appmdp-05 (passed through to the VM), before the speed benchmark and any production
# run. Run as the user that will compute (p9sim); stages marked (root) need sudo or report NOT RUN with the command.
#
#   bash acceptance.sh inventory            nvidia-smi -q and the key facts of the card                (1 min)
#   bash acceptance.sh dcgm                  DCGM diagnostics level 3 (needs dcgmi)                       (about 30-60 min)
#   bash acceptance.sh check PROD_DIR        the 38 check cases of p9prod-9a084ed on sm_80 (check.sh)     (about 3-5 min)
#   bash acceptance.sh throughput            FP64 operations per second against the expected rate        (1 min)
#   bash acceptance.sh burn [HOURS]          FP64 load with result check, temperature/clock/ECC log      (default 1.5 h)
#   bash acceptance.sh reboot-before         record the card's identity and error counters, then reboot appmdp-05
#   bash acceptance.sh reboot-after PROD_DIR after the reboot: same card, driver, counters; peak; check.sh again
#   bash acceptance.sh report                SUMMARY.txt: every stage PASS / FAIL / NOT RUN
#   bash acceptance.sh all PROD_DIR [HOURS]  inventory, dcgm, check, throughput, burn, report (then the reboot test)
#
# The A100 is chosen by name (GPU_UUID=... to choose another card); the other GPUs (the L40S) are not touched: every
# CUDA program runs with CUDA_VISIBLE_DEVICES set to the A100's UUID. Results go to $ACC (default: ./acc-<host>),
# one directory for all stages, so the stages can run on different days.
set -uo pipefail
cd "$(dirname "$0")"
HERE=$PWD
ACC=${ACC:-$HERE/acc-$(hostname -s)}
mkdir -p "$ACC"
SUM=$ACC/SUMMARY.txt
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$ACC/acceptance.log"; }
result() { # stage verdict reason
	grep -v "^$1 " "$SUM" 2>/dev/null > "$SUM.tmp"; echo "$1 $2 $3" >> "$SUM.tmp"; mv "$SUM.tmp" "$SUM"; log "== $1: $2 ($3)"; }

command -v nvidia-smi >/dev/null || { echo "nvidia-smi not found: driver not installed or card not passed through"; exit 2; }
if [ -z "${GPU_UUID:-}" ]; then
	GPU_UUID=$(nvidia-smi --query-gpu=uuid,name --format=csv,noheader | awk -F', ' '$2 ~ /A100/ {print $1; exit}')
fi
[ -n "$GPU_UUID" ] || { echo "no A100 found by nvidia-smi (set GPU_UUID=...)"; nvidia-smi -L; exit 2; }
GPU_INDEX=$(nvidia-smi --query-gpu=index,uuid --format=csv,noheader | awk -F', ' -v u="$GPU_UUID" '$2 == u {print $1}')
export CUDA_VISIBLE_DEVICES=$GPU_UUID
q() { nvidia-smi -i "$GPU_UUID" --query-gpu="$1" --format=csv,noheader,nounits 2>/dev/null; }

# the monitoring fields this driver knows (names differ between driver versions)
fields() {
	local f out=timestamp
	for f in temperature.gpu temperature.memory clocks.sm clocks.mem clocks.max.sm power.draw power.limit pstate utilization.gpu \
		clocks_event_reasons.active clocks_throttle_reasons.active \
		clocks_event_reasons.hw_slowdown clocks_event_reasons.hw_thermal_slowdown clocks_event_reasons.sw_thermal_slowdown \
		clocks_event_reasons.hw_power_brake_slowdown clocks_throttle_reasons.hw_slowdown clocks_throttle_reasons.hw_thermal_slowdown \
		clocks_throttle_reasons.sw_thermal_slowdown clocks_throttle_reasons.hw_power_brake_slowdown \
		ecc.errors.corrected.volatile.total ecc.errors.uncorrected.volatile.total ecc.errors.uncorrected.aggregate.total \
		remapped_rows.correctable remapped_rows.uncorrectable remapped_rows.pending remapped_rows.failure \
		pcie.link.gen.current pcie.link.width.current; do
		nvidia-smi -i "$GPU_UUID" --query-gpu="$f" --format=csv,noheader >/dev/null 2>&1 && out="$out,$f"
	done
	echo "$out"
}

xid_since() { # ISO time -> Xid lines since then, or NOT CHECKED
	local out
	if out=$(journalctl -k --since "$1" 2>/dev/null) && [ -n "$out" ]; then echo "$out" | grep -i 'NVRM: Xid' || true
	elif out=$(dmesg 2>/dev/null); then echo "$out" | grep -i 'NVRM: Xid' || true
	else echo "NOT CHECKED (no access to the kernel log; run: sudo dmesg | grep -i xid)"; fi
}

stage_inventory() {
	log "inventory of $GPU_UUID (index $GPU_INDEX)"
	nvidia-smi -q -i "$GPU_UUID" > "$ACC/nvidia-smi-q.txt"
	nvidia-smi > "$ACC/nvidia-smi.txt"
	{ for f in name serial uuid pci.bus_id vbios_version driver_version memory.total ecc.mode.current persistence_mode \
		power.limit power.max_limit clocks.max.sm clocks.max.mem pcie.link.gen.max pcie.link.width.max pcie.link.gen.current \
		pcie.link.width.current ecc.errors.uncorrected.aggregate.total remapped_rows.pending remapped_rows.failure; do
		printf '%-40s %s\n' "$f" "$(q "$f")"; done; } | tee "$ACC/inventory.txt"
	lspci -vv -s "$(q pci.bus_id | sed 's/^0000//' | tr 'A-F' 'a-f')" > "$ACC/lspci.txt" 2>&1 || true   # 00000000:81:00.0 -> 0000:81:00.0
	local why=""
	[ "$(q ecc.mode.current)" = "Enabled" ] || why="$why ECC not enabled;"
	[ "$(q remapped_rows.pending)" = "No" ] || [ -z "$(q remapped_rows.pending)" ] || why="$why remapped rows pending;"
	[ "$(q remapped_rows.failure)" = "No" ] || [ -z "$(q remapped_rows.failure)" ] || why="$why row remapping failure;"
	[ "$(q ecc.errors.uncorrected.aggregate.total)" = "0" ] || why="$why uncorrected ECC errors in the aggregate counter;"
	[ "$(q pcie.link.width.max)" = "16" ] || why="$why PCIe link narrower than x16;"
	[ -z "$why" ] && result inventory PASS "ECC on, no remapping pending or failed, no uncorrected errors, x16" || result inventory FAIL "$why"
	[ "$(q persistence_mode)" = "Enabled" ] || log "note: persistence mode is off (root: nvidia-smi -i $GPU_UUID -pm 1, or nvidia-persistenced)"
}

stage_dcgm() {
	if ! command -v dcgmi >/dev/null; then
		result dcgm "NOT RUN" "dcgmi not installed (root: apt install datacenter-gpu-manager-4-cuda13 or -cuda12; systemctl enable --now nvidia-dcgm)"
		return
	fi
	log "DCGM diagnostics level 3 on GPU $GPU_INDEX (about 30-60 min)"
	dcgmi diag -r 3 -i "$GPU_INDEX" 2>&1 | tee "$ACC/dcgm-r3.txt"
	local rc=${PIPESTATUS[0]}
	if [ "$rc" = 0 ] && ! grep -q -i 'fail' "$ACC/dcgm-r3.txt"; then result dcgm PASS "dcgmi diag -r 3: no failure"
	else result dcgm FAIL "dcgmi diag -r 3: exit $rc, see dcgm-r3.txt"; fi
}

stage_check() { # PROD_DIR
	local prod=${1:?the unpacked package p9prod-9a084ed}
	[ -f "$prod/check.sh" ] || { result check "NOT RUN" "no check.sh in $prod"; return; }
	log "the 38 check cases of $(basename "$prod") on $(q name) ($(q pci.bus_id))"
	(cd "$prod" && sh check.sh) 2>&1 | tee "$ACC/check.txt"
	if grep -q '^== ALL SAME' "$ACC/check.txt"; then result check PASS "check.sh: ALL SAME on $(q name)"
	else result check FAIL "check.sh: not ALL SAME, see check.txt"; fi
}

stage_throughput() {
	log "FP64 throughput (bin/peak)"
	bin/peak 2>&1 | tee "$ACC/peak.txt"
	local sms clk exp add mul
	sms=$(awk '/^device:/ {for (i = 1; i <= NF; i++) if ($i == "SMs") print $(i-1)}' "$ACC/peak.txt" | tr -d ,)
	clk=$(q clocks.max.sm)
	# A100 (sm_80): 32 FP64 units per SM, one add or multiply each per cycle (not fused, as p9gpu is built)
	exp=$(awk -v s="$sms" -v c="$clk" 'BEGIN { printf "%.4e", s * 32 * c * 1e6 }')
	add=$(awk '/^double add/ {print $3}' "$ACC/peak.txt"); mul=$(awk '/^double mul/ {print $3}' "$ACC/peak.txt")
	log "expected at $clk MHz with $sms SMs: $exp ops/s; measured add $add, mul $mul"
	if awk -v a="$add" -v m="$mul" -v e="$exp" 'BEGIN { exit !(a >= 0.8 * e && m >= 0.8 * e) }'; then
		result throughput PASS "double add $add, mul $mul ops/s, at least 80 % of $exp"
	else result throughput FAIL "double add $add, mul $mul ops/s, below 80 % of $exp"; fi
}

stage_burn() { # [HOURS]
	local hours=${1:-1.5} secs start f mon pid rc
	secs=$(awk -v h="$hours" 'BEGIN { printf "%d", h * 3600 }')
	start=$(date -u '+%F %T')
	f=$(fields)
	log "FP64 burn for $hours h ($secs s); monitoring every 10 s: $f"
	local u0 r0
	u0=$(q ecc.errors.uncorrected.aggregate.total); r0=$(q remapped_rows.uncorrectable)
	nvidia-smi -i "$GPU_UUID" --query-gpu="$f" --format=csv,nounits -l 10 > "$ACC/burn-monitor.csv" 2>&1 &
	mon=$!
	bin/fp64burn "$secs" 300 2>&1 | tee "$ACC/burn.txt"
	rc=${PIPESTATUS[0]}
	sleep 11; kill "$mon" 2>/dev/null; wait "$mon" 2>/dev/null
	xid_since "$start" > "$ACC/burn-xid.txt"
	# evaluation of the monitor log: maximum temperature, slowdown reasons, ECC and remapping changes
	local stats why=""
	stats=$(python3 -I - "$ACC/burn-monitor.csv" <<'PY'
import csv, statistics, sys
rows = list(csv.reader(open(sys.argv[1]), skipinitialspace=True))
head, data = rows[0], [r for r in rows[1:] if len(r) == len(rows[0])]
# nvidia-smi names some columns differently than the query (clocks.sm -> clocks.current.sm)
col = lambda name: [r[i] for i, h in enumerate(head) if h.split(" [")[0] in (name, name.replace("clocks.", "clocks.current.")) for r in data]
num = lambda v: float(v) if v.replace(".", "", 1).isdigit() else None
temps = [x for x in map(num, col("temperature.gpu")) if x is not None]
clocks = [x for x in map(num, col("clocks.sm")) if x is not None]
slow = {h.split(" [")[0]: sum(1 for r in data if "Active" in r[i] and "Not" not in r[i])
        for i, h in enumerate(head) if any(k in h for k in ("hw_slowdown", "thermal_slowdown", "power_brake"))}
slow = {k: v for k, v in slow.items() if v}
last = lambda name: (col(name) or ["n/a"])[-1]
print(f"tmax={max(temps, default=0):.0f} clock_min={min(clocks, default=0):.0f} "
      f"clock_median={statistics.median(clocks) if clocks else 0:.0f} samples={len(data)} "
      f"ecc_corrected={last('ecc.errors.corrected.volatile.total')} ecc_uncorrected={last('ecc.errors.uncorrected.volatile.total')} "
      f"slowdowns={' '.join(f'{k}:{v}' for k, v in slow.items()) or 'none'}")
PY
)
	log "burn monitor: $stats"
	echo "$stats" > "$ACC/burn-stats.txt"
	[ "$rc" = 0 ] || why="$why fp64burn: differing results or CUDA error (exit $rc);"
	echo "$stats" | grep -q 'slowdowns=none' || why="$why hardware or thermal slowdown active;"
	echo "$stats" | awk -F'tmax=' '{ split($2, a, " "); exit !(a[1] <= 85) }' || why="$why temperature above 85 C;"
	echo "$stats" | grep -q 'ecc_uncorrected=0' || why="$why uncorrected ECC errors;"
	[ "$(q ecc.errors.uncorrected.aggregate.total)" = "$u0" ] || why="$why aggregate uncorrected ECC counter rose;"
	[ "$(q remapped_rows.uncorrectable)" = "$r0" ] || why="$why new remapped rows (uncorrectable);"
	grep -q 'NVRM: Xid' "$ACC/burn-xid.txt" && why="$why Xid errors in the kernel log;"
	grep -q 'NOT CHECKED' "$ACC/burn-xid.txt" && log "note: Xid not checked (no kernel log access)"
	[ -z "$why" ] && result burn PASS "$hours h, no differing result, $stats" || result burn FAIL "$why $stats"
}

stage_reboot_before() {
	{ for f in uuid serial pci.bus_id driver_version vbios_version ecc.mode.current ecc.errors.uncorrected.aggregate.total \
		remapped_rows.correctable remapped_rows.uncorrectable remapped_rows.pending remapped_rows.failure; do echo "$f=$(q "$f")"; done; } > "$ACC/reboot-before.txt"
	cat "$ACC/reboot-before.txt"
	log "recorded; now reboot appmdp-05 (sudo reboot), then: bash acceptance.sh reboot-after PROD_DIR"
	result reboot "PENDING" "recorded before the reboot $(date -u +%FT%TZ)"
}

stage_reboot_after() { # PROD_DIR
	[ -f "$ACC/reboot-before.txt" ] || { echo "run reboot-before first"; exit 2; }
	local why="" k v now
	GPU_UUID=$(grep '^uuid=' "$ACC/reboot-before.txt" | cut -d= -f2)
	export CUDA_VISIBLE_DEVICES=$GPU_UUID
	[ -n "$(q name)" ] || { result reboot FAIL "the card $GPU_UUID is not visible after the reboot"; return; }
	while IFS='=' read -r k v; do
		now=$(q "$k")
		[ "$now" = "$v" ] || why="$why $k: before $v, now $now;"
	done < "$ACC/reboot-before.txt"
	echo "uptime: $(uptime -s 2>/dev/null)" | tee -a "$ACC/acceptance.log"
	bin/peak > "$ACC/peak-after-reboot.txt" 2>&1 || why="$why peak failed after the reboot;"
	if [ -n "${1:-}" ] && [ -f "$1/check.sh" ]; then
		(cd "$1" && sh check.sh) > "$ACC/check-after-reboot.txt" 2>&1
		grep -q '^== ALL SAME' "$ACC/check-after-reboot.txt" || why="$why check.sh not ALL SAME after the reboot;"
	else why="$why check.sh not run (PROD_DIR missing);"; fi
	[ -z "$why" ] && result reboot PASS "same card, driver and counters after the reboot; peak runs; check.sh ALL SAME" || result reboot FAIL "$why"
}

stage_report() {
	local s
	for s in inventory dcgm check throughput burn reboot; do grep -q "^$s " "$SUM" 2>/dev/null || echo "$s NOT RUN -" >> "$SUM"; done
	echo "== acceptance of $GPU_UUID ($(q name), $(q serial)) on $(hostname -s), $(date -u +%FT%TZ)"
	cat "$SUM"
	if grep -q -v -E '^[a-z]+ PASS ' "$SUM"; then echo "== NOT PASSED (every stage must be PASS)"; else echo "== PASSED"; fi
}

case "${1:-}" in
inventory) stage_inventory ;;
dcgm) stage_dcgm ;;
check) stage_check "${2:-}" ;;
throughput) stage_throughput ;;
burn) stage_burn "${2:-1.5}" ;;
reboot-before) stage_reboot_before ;;
reboot-after) stage_reboot_after "${2:-}" ;;
report) stage_report ;;
all) stage_inventory; stage_dcgm; stage_check "${2:-}"; stage_throughput; stage_burn "${3:-1.5}"; stage_report
     echo "next: bash acceptance.sh reboot-before, reboot appmdp-05, bash acceptance.sh reboot-after ${2:-PROD_DIR}, bash acceptance.sh report" ;;
*) sed -n '2,20p' "$0"; exit 2 ;;
esac
