#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Acceptance test of the A100 in appmdp-05 (passed through to the VM), before the speed benchmark and any production
# run. Run as the user that will compute (p9sim); stages marked (root) need sudo or report NOT RUN with the command.
#
#   bash acceptance.sh inventory            nvidia-smi -q and the key facts of the card                (1 min)
#   bash acceptance.sh dcgm                  DCGM diagnostics level 3 (needs dcgmi)                       (about 30-60 min)
#   bash acceptance.sh check PROD_DIR        the 38 check cases of p9prod-9a084ed on sm_80 (check.sh)     (about 3-5 min)
#   bash acceptance.sh throughput            FP64 operations per second against the expected rate        (1 min)
#   bash acceptance.sh throughput-warm       addendum 2026-11-03: the same after 5 s warm-up, with clock log (1 min)
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
# addenda (measurements added after a result) go to their own file; SUMMARY.txt and its verdict stay as fixed beforehand
ADD=$ACC/ADDENDUM.txt
addendum() { # name verdict reason
	grep -v "^$1 " "$ADD" 2>/dev/null > "$ADD.tmp"; echo "$1 $2 $3" >> "$ADD.tmp"; mv "$ADD.tmp" "$ADD"; log "== addendum $1: $2 ($3)"; }

command -v nvidia-smi >/dev/null || { echo "nvidia-smi not found: driver not installed or card not passed through"; exit 2; }
if [ -z "${GPU_UUID:-}" ]; then
	GPU_UUID=$(nvidia-smi --query-gpu=uuid,name --format=csv,noheader | awk -F', ' '$2 ~ /A100/ {print $1; exit}')
fi
[ -n "$GPU_UUID" ] || { echo "no A100 found by nvidia-smi (set GPU_UUID=...)"; nvidia-smi -L; exit 2; }
GPU_INDEX=$(nvidia-smi --query-gpu=index,uuid --format=csv,noheader | awk -F', ' -v u="$GPU_UUID" '$2 == u {print $1}')
export CUDA_VISIBLE_DEVICES=$GPU_UUID
q() { nvidia-smi -i "$GPU_UUID" --query-gpu="$1" --format=csv,noheader,nounits 2>/dev/null; }

known() { # field -> exit 0 if this driver knows it (three tries: a single query can fail while the card wakes up)
	local n
	for n in 1 2 3; do nvidia-smi -i "$GPU_UUID" --query-gpu="$1" --format=csv,noheader >/dev/null 2>&1 && return 0; sleep 1; done
	return 1
}

# the monitoring fields this driver knows (names differ between driver versions)
fields() {
	local f out=timestamp
	for f in temperature.gpu temperature.memory clocks.sm clocks.mem clocks.max.sm power.draw power.limit pstate utilization.gpu \
		clocks_event_reasons.active clocks_throttle_reasons.active \
		clocks_event_reasons.sw_power_cap clocks_throttle_reasons.sw_power_cap \
		clocks_event_reasons.hw_slowdown clocks_event_reasons.hw_thermal_slowdown clocks_event_reasons.sw_thermal_slowdown \
		clocks_event_reasons.hw_power_brake_slowdown clocks_throttle_reasons.hw_slowdown clocks_throttle_reasons.hw_thermal_slowdown \
		clocks_throttle_reasons.sw_thermal_slowdown clocks_throttle_reasons.hw_power_brake_slowdown \
		ecc.errors.corrected.volatile.total ecc.errors.uncorrected.volatile.total ecc.errors.uncorrected.aggregate.total \
		remapped_rows.correctable remapped_rows.uncorrectable remapped_rows.pending remapped_rows.failure \
		pcie.link.gen.current pcie.link.width.current; do
		known "$f" && out="$out,$f"
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
	# dcgmi runs without CUDA_VISIBLE_DEVICES (it warns when the variable is set: the host engine does not see it);
	# the card is chosen by -i alone, so its DCGM id is taken from dcgmi discovery by the UUID (fallback: the index)
	local id rc res
	env -u CUDA_VISIBLE_DEVICES dcgmi discovery -l > "$ACC/dcgm-discovery.txt" 2>&1
	id=$(awk -v u="$GPU_UUID" -F'|' '$2 ~ /^ *[0-9]+ *$/ {g = $2; gsub(/ /, "", g)} index($0, u) {print g; exit}' "$ACC/dcgm-discovery.txt")
	if [ -z "$id" ]; then id=$GPU_INDEX; log "note: DCGM id of $GPU_UUID not found in dcgmi discovery -l; using the nvidia-smi index $id"; fi
	log "DCGM diagnostics level 3 on DCGM GPU $id ($GPU_UUID) (about 30-60 min)"
	env -u CUDA_VISIBLE_DEVICES dcgmi diag -r 3 -i "$id" 2>&1 | tee "$ACC/dcgm-r3.txt"
	rc=${PIPESTATUS[0]}
	# judged are only the result lines of the table, "| <test> | <result> ...", whose result begins with Pass, Fail,
	# Skip or Warn (also the per-GPU lines "GPU0: Fail"); other text such as environment warnings is not judged
	res=$(awk -F'|' 'NF >= 3 { r = $3; sub(/^ +/, "", r); sub(/^GPU[0-9]+: */, "", r)
		if (r ~ /^(Pass|Fail|Skip|Warn)/) { split(r, w, /[ -]/); n[w[1]]++ } }
		END { for (k in n) printf "%s %d ", k, n[k] }' "$ACC/dcgm-r3.txt")
	log "dcgm result lines: ${res:-none}"
	if [ "$rc" = 0 ] && [ -n "$res" ] && ! echo "$res" | grep -q 'Fail'; then result dcgm PASS "dcgmi diag -r 3 on DCGM GPU $id: no failure ($res)"
	else result dcgm FAIL "dcgmi diag -r 3 on DCGM GPU $id: exit $rc, result lines: ${res:-none}; see dcgm-r3.txt"; fi
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

stage_throughput_warm() { # addendum 2026-11-03: the throughput stage after a warm-up, with the SM clock logged
	# bin/peak without arguments measures each operation over 5 launches right after one launch (tens of ms), so on
	# a card coming from idle it measures at the base clock. Here: 5 s of double add first, then every operation over
	# at least 2 s, SM clock and clock event reasons every 100 ms. Limit unchanged: >= 80 % of 32 x SMs x max SM clock.
	log "addendum: FP64 throughput after 5 s warm-up (bin/peak 5 2), SM clock logged every 100 ms"
	local f c mon clk out rc
	f=timestamp
	for c in clocks.sm clocks_event_reasons.active clocks_throttle_reasons.active power.draw temperature.gpu; do
		known "$c" && f="$f,$c"
	done
	TZ=UTC nvidia-smi -i "$GPU_UUID" --query-gpu="$f" --format=csv,nounits -lms 100 > "$ACC/peak-warm-clocks.csv" 2>&1 &
	mon=$!
	sleep 2
	bin/peak 5 2 2>&1 | tee "$ACC/peak-warm.txt"
	sleep 1; kill "$mon" 2>/dev/null; wait "$mon" 2>/dev/null
	clk=$(q clocks.max.sm)
	out=$(python3 -I - "$ACC/peak-warm.txt" "$ACC/peak-warm-clocks.csv" "$clk" <<'PY'
import csv, datetime, statistics, sys
peak, clocks, clk = sys.argv[1], sys.argv[2], float(sys.argv[3])
lines = open(peak).read().splitlines()
sms = int(next(l for l in lines if l.startswith("device:")).split(" SMs")[0].split()[-1])
exp = sms * 32 * clk * 1e6
win = {}
for l in lines:
    for name in ("double add", "double mul"):
        if l.startswith(name + " ") and "window" in l:
            w = l.split()
            win[name] = (float(w[2]), float(w[w.index("window") + 1]), float(w[w.index("window") + 2]))
rows = list(csv.reader(open(clocks), skipinitialspace=True))
head = [h.split(" [")[0] for h in rows[0]]
ci = next(i for i, h in enumerate(head) if h in ("clocks.sm", "clocks.current.sm"))
ri = next((i for i, h in enumerate(head) if h.endswith("reasons.active")), None)
t = lambda s: datetime.datetime.strptime(s, "%Y/%m/%d %H:%M:%S.%f").replace(tzinfo=datetime.timezone.utc).timestamp()
samples = [(t(r[0]), r) for r in rows[1:] if len(r) == len(head) and r[ci].isdigit()]
ok, parts = True, []
for name in ("double add", "double mul"):
    if name not in win: print(f"FAIL no measurement of {name}"); sys.exit(1)
    v, t0, t1 = win[name]
    inside = [r for ts, r in samples if t0 <= ts <= t1]
    cl = [float(r[ci]) for r in inside]
    reasons = sorted({r[ri] for r in inside}) if ri is not None else ["n/a"]
    ok = ok and v >= 0.8 * exp
    parts.append(f"{name.split()[1]} {v:.3e} ops/s ({100 * v / exp:.1f} %), SM clock in the window "
                 + (f"min {min(cl):.0f} median {statistics.median(cl):.0f} MHz over {len(cl)} samples" if cl else "not logged")
                 + f", reasons {'/'.join(reasons)}")
print(("PASS " if ok else "FAIL ") + f"expected {exp:.4e} ops/s ({sms} SMs, {clk:.0f} MHz), limit 80 %: " + "; ".join(parts))
sys.exit(0 if ok else 1)
PY
)
	rc=$?
	log "$out"
	if [ "$rc" = 0 ]; then addendum throughput-warm PASS "${out#PASS }"; else addendum throughput-warm FAIL "${out#FAIL }"; fi
}

stage_burn() { # [HOURS]
	local hours=${1:-1.5} secs start f mon pid rc
	secs=$(awk -v h="$hours" 'BEGIN { printf "%d", h * 3600 }')
	start=$(date -u '+%F %T')
	f=$(fields)
	log "FP64 burn for $hours h ($secs s); monitoring every 10 s: $f"
	local u0 r0
	u0=$(q ecc.errors.uncorrected.aggregate.total); r0=$(q remapped_rows.uncorrectable)
	# for information, not judged: the driver's time counters per clock event reason (microseconds), before and after;
	# they also catch events between the 10 s samples
	local cf="" c
	for c in sw_power_cap sw_thermal_slowdown hw_thermal_slowdown hw_power_brake_slowdown; do
		known "clocks_event_reasons_counters.$c" && cf="$cf${cf:+,}clocks_event_reasons_counters.$c"
	done
	[ -n "$cf" ] && nvidia-smi -i "$GPU_UUID" --query-gpu="$cf" --format=csv,nounits > "$ACC/burn-reason-counters-before.csv" 2>&1
	nvidia-smi -i "$GPU_UUID" --query-gpu="$f" --format=csv,nounits -l 10 > "$ACC/burn-monitor.csv" 2>&1 &
	mon=$!
	bin/fp64burn "$secs" 300 2>&1 | tee "$ACC/burn.txt"
	rc=${PIPESTATUS[0]}
	sleep 11; kill "$mon" 2>/dev/null; wait "$mon" 2>/dev/null
	if [ -n "$cf" ]; then
		nvidia-smi -i "$GPU_UUID" --query-gpu="$cf" --format=csv,nounits > "$ACC/burn-reason-counters-after.csv" 2>&1
		log "info (not judged), clock event reason time during the burn: $(paste -d, "$ACC/burn-reason-counters-before.csv" "$ACC/burn-reason-counters-after.csv" | awk -F', *' -v n="$(echo "$cf" | tr ',' '\n' | wc -l)" '
			NR == 1 { for (i = 1; i <= n; i++) { h[i] = $i; sub(/^clocks_event_reasons_counters\./, "", h[i]); sub(/ \[.*/, "", h[i]) } next }
			{ for (i = 1; i <= n; i++) if ($(i + n) >= $i) printf "%s %.1f s; ", h[i], ($(i + n) - $i) / 1e6
			  else printf "%s reset during the burn (before %.1f s, after %.1f s); ", h[i], $i / 1e6, $(i + n) / 1e6 }')"
	else log "info: this driver has no clock event reason counters"; fi
	xid_since "$start" > "$ACC/burn-xid.txt"
	# evaluation of the monitor log: maximum temperature, slowdown reasons, ECC and remapping changes.
	# Judged slowdowns: HW slowdown (0x8), SW thermal (0x20), HW thermal (0x40), HW power brake (0x80), from their
	# own columns and from the bit mask of clocks_event_reasons.active. SW power cap (0x4) is normal under FP64 load
	# at the power limit: it is counted for information and not judged.
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
JUDGED = {"hw_slowdown": 0x8, "sw_thermal_slowdown": 0x20, "hw_thermal_slowdown": 0x40, "hw_power_brake_slowdown": 0x80}
INFO = {"sw_power_cap": 0x4}
reason = lambda h: h.split(" [")[0].split(".")[-1] if h.startswith(("clocks_event_reasons.", "clocks_throttle_reasons.")) else None
by_col = {k: [i for i, h in enumerate(head) if reason(h) == k] for k in {**JUDGED, **INFO}}
mask_cols = [i for i, h in enumerate(head) if reason(h) == "active"]
def active(r, k, bit):
    if any("Active" in r[i] and "Not" not in r[i] for i in by_col[k]): return True
    return any(r[i].startswith("0x") and int(r[i], 16) & bit for i in mask_cols)
readable = bool(mask_cols) or all(by_col[k] for k in JUDGED)
slow = {k: sum(1 for r in data if active(r, k, b)) for k, b in JUDGED.items()}
slow = {k: v for k, v in slow.items() if v}
power_cap = sum(1 for r in data if active(r, "sw_power_cap", 0x4))
last = lambda name: (col(name) or ["n/a"])[-1]
print(f"tmax={max(temps, default=0):.0f} clock_min={min(clocks, default=0):.0f} "
      f"clock_median={statistics.median(clocks) if clocks else 0:.0f} samples={len(data)} "
      f"ecc_corrected={last('ecc.errors.corrected.volatile.total')} ecc_uncorrected={last('ecc.errors.uncorrected.volatile.total')} "
      f"slowdowns={' '.join(f'{k}:{v}' for k, v in slow.items()) or ('none' if readable else 'unreadable')} "
      f"sw_power_cap_samples={power_cap}(not_judged)")
PY
)
	log "burn monitor: $stats"
	echo "$stats" > "$ACC/burn-stats.txt"
	[ "$rc" = 0 ] || why="$why fp64burn: differing results or CUDA error (exit $rc);"
	if echo "$stats" | grep -q 'slowdowns=unreadable'; then why="$why slowdown reasons not readable from the monitor log;"
	elif ! echo "$stats" | grep -q 'slowdowns=none'; then why="$why hardware or thermal slowdown active;"; fi
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
	if [ -s "$ADD" ]; then
		echo "== addenda (measured after a result; the verdict above follows the rules fixed beforehand, the project lead decides what an addendum means for it)"
		cat "$ADD"
	fi
}

case "${1:-}" in
inventory) stage_inventory ;;
dcgm) stage_dcgm ;;
check) stage_check "${2:-}" ;;
throughput) stage_throughput ;;
throughput-warm) stage_throughput_warm ;;
burn) stage_burn "${2:-1.5}" ;;
reboot-before) stage_reboot_before ;;
reboot-after) stage_reboot_after "${2:-}" ;;
report) stage_report ;;
all) stage_inventory; stage_dcgm; stage_check "${2:-}"; stage_throughput; stage_burn "${3:-1.5}"; stage_report
     echo "next: bash acceptance.sh reboot-before, reboot appmdp-05, bash acceptance.sh reboot-after ${2:-PROD_DIR}, bash acceptance.sh report" ;;
*) sed -n '2,21p' "$0"; exit 2 ;;
esac
