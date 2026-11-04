#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# State of the production run (read only): the package's status.sh, and which card p9gpu really uses (nvidia-smi
# by process; check.sh's header line names the first card whatever is used). After the check, the check times
# against those of the L40S (runs/l40s/check-p9prod-9a084ed.txt) and of the A100 acceptance test (2026-11-03).
#   sh status-a100.sh ../p9prod-9a084ed
export LC_ALL=C
PROD=$(cd "${1:?the unpacked package p9prod-9a084ed}" && pwd)
sh "$PROD/status.sh"
echo "== cards with p9gpu:"
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader |
	while IFS=, read -r u pid mem; do
		[ "$(ps -o comm= -p $pid 2>/dev/null)" = p9gpu ] && echo "  pid$pid on $(nvidia-smi -i "$u" --query-gpu=name --format=csv,noheader) ($u),$mem"
	done
[ -s "$PROD/a100-start.log" ] && echo "== started with: $(tail -n 1 "$PROD/a100-start.log")"
if [ -f "$PROD/check/report.txt" ]; then
	echo "== check times (s): this run | A100 acceptance 2026-11-03 | L40S"
	for c in deep-57:14.487:33.085 deep-147:14.250:32.541 prod:0.688:3.198 chain:0.376:1.628; do
		n=${c%%:*}; r=${c#*:}
		t=$(sed -n "s/^$n: SAME ([0-9a-f]*, \([0-9.]*\) s)/\1/p" "$PROD/check/report.txt")
		echo "  $n: ${t:-?} | ${r%%:*} | ${r#*:}"
	done
fi
