#!/bin/sh
# Test of chain-a100.sh and run-watch.sh with stand-ins, on any Linux machine without a GPU:
# fake nvidia-smi, journalctl and curl in front of PATH, small fake packages whose start.sh starts "sleep" instead of
# p9gpu. Plays the whole chain: production run -> V5 -> set A -> set B, with every gate, alarm and the test mode.
#   sh test/test-chain.sh        (from the chain directory; leaves nothing behind but a temporary directory it removes)
set -u
export LC_ALL=C
HERE=$(cd "$(dirname "$0")/.." && pwd)
T=$(mktemp -d)
pids=""
cleanup() { for p in $pids $(cat "$T"/*/run.pid "$T"/prod/production.pid 2>/dev/null); do kill "$p" 2>/dev/null; done; rm -rf "$T"; }
trap cleanup EXIT
fails=0; n=0
ok() { n=$((n + 1)); if eval "$2"; then echo "ok   $1"; else echo "FAIL $1"; fails=$((fails + 1)); tail -n 2 "$T/outbox.txt" 2>/dev/null | sed "s/^/     outbox: /"; tail -n 3 "$T/chain/chain.log" 2>/dev/null | sed "s/^/     log: /"; fi; }
U=GPU-00000000-1111-2222-3333-444444444444

# --- stand-ins ------------------------------------------------------------------------------------------------------
mkdir -p "$T/bin" "$T/fake" "$T/chain" "$T/home/.config/p9chain"
cat > "$T/bin/nvidia-smi" <<EOF
#!/bin/sh
case "\$*" in
  *--query-gpu=uuid,name*) printf '%s, NVIDIA L40S\n$U, NVIDIA A100-PCIE-40GB\n' GPU-99999999-1111-2222-3333-444444444444 ;;
  *--query-compute-apps*) cat "$T/fake/apps.txt" 2>/dev/null ;;
  *--query-gpu=name,temperature*) cat "$T/fake/gpu.txt" ;;
  *) exit 1 ;;
esac
EOF
cat > "$T/bin/journalctl" <<EOF
#!/bin/sh
cat "$T/fake/kern.txt" 2>/dev/null
EOF
cat > "$T/bin/curl" <<EOF
#!/bin/sh
# records the command line and the config from stdin separately; answers 200
printf '%s\n' "\$*" >> "$T/fake/curl-argv.txt"
cat >> "$T/fake/curl-stdin.txt"
printf 200
EOF
# only the p9gpu processes of this test (working under $T): the real runs of the machine stay invisible to it
cat > "$T/bin/p9gpu-pids" <<EOF
#!/bin/sh
for p in \$(ps -C p9gpu -o pid=); do
  case "\$(readlink /proc/\$p/cwd 2>/dev/null)/" in "$T"/*) echo \$p ;; esac
done
EOF
chmod +x "$T/bin/"*
echo "NVIDIA A100-PCIE-40GB, 45, 0x0000000000000000, 0, 1410, 198.5" > "$T/fake/gpu.txt"
: > "$T/fake/apps.txt"; : > "$T/fake/kern.txt"

FAKESTART='#!/bin/sh
cd "$(dirname "$0")"
[ -z "${FAKE_REFUSE:-}" ] || { echo "STOP: compute processes on the card"; exit 1; }
j=${JOBS:-$(ls jobs | tr "\n" " " | sed "s/ $//")}
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start: GPU $CUDA_VISIBLE_DEVICES (NVIDIA A100-PCIE-40GB), jobs $j" >> start.log
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start, package fake, p9gpu sha256 x, 1 at once, jobs: $j" >> run.log
sleep 600 > /dev/null 2>&1 &
echo $! > run.pid
echo "started (pid $(cat run.pid)); first the check (a few minutes), then the jobs. Status: sh status.sh"'
mkpkg() {   # mkpkg DIR SEGMENTS JOB...
  d=$1; s=$2; shift 2
  mkdir -p "$d/jobs" "$d/v2"
  for j in "$@"; do mkdir -p "$d/jobs/$j"; printf 'SEGMENT_YR=100000000\nSEGMENTS=%s\n' "$s" > "$d/jobs/$j/params.env"; done
  printf '%s\n' "$FAKESTART" > "$d/start.sh"
}
finish_job() {   # finish_job PKGDIR JOB (all segments done, completion line)
  J=$1/jobs/$2; s=$(sed -n 's/^SEGMENTS=//p' "$J/params.env")
  k=0; while [ $k -lt "$s" ]; do mkdir -p "$J/segments/seg00$k"; : > "$J/segments/seg00$k/DONE"
    printf '%s\t%s\t%s\t1.0\t%064d\t-\n' $k $(( (k + 1) * 100000000 )) 1006 $k >> "$J/segments.tsv"; k=$((k + 1)); done
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $2 complete: $s segments" >> "$1/run.log"
}
end_pkg() { kill "$(cat "$1/run.pid")" 2>/dev/null; rm -f "$1/run.pid"; echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) all jobs ended" >> "$1/run.log"; }

# production run: 3 segments, running
P=$T/prod; mkdir -p "$P/segments/seg000"
printf 'SEGMENT_YR=100000000\nSEGMENTS=3\n' > "$P/params.env"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start, package 9a084ed" > "$P/production.log"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) check: ALL SAME" >> "$P/production.log"
sleep 600 > /dev/null 2>&1 & echo $! > "$P/production.pid"
: > "$P/segments/seg000/stderr.txt"
mkpkg "$T/v5" 2 V5-s110 V5-s111 V5-s112
mkpkg "$T/sets" 2 BB-A BB-B
mkpkg "$T/merc" 2 M-s110-part00 M-s110-part01

cp "$HERE/lib.sh" "$HERE/chain-a100.sh" "$HERE/run-watch.sh" "$T/chain/"
cat > "$T/chain/chain.env" <<EOF
PROD_DIR=$P
V5_DIR=$T/v5
SETS_DIR=$T/sets
MERC_DIR=$T/merc
V2_DIR=$T/v2
GPU_NAME=A100
GPU_UUID=
E4_OK=$T/chain/e4-on-chain.ok
TELEGRAM_FILE=$T/home/.config/p9chain/telegram.env
INTERVAL=300
STALL_MIN=30
STALL_MERC_MIN=30
REPEAT_H=6
TEMP_MAX=85
REPORT_HOURS="99"
XID_CMD=journalctl
EOF
export PATH="$T/bin:$PATH" TG_OUTBOX="$T/outbox.txt" P9GPU_PIDS_CMD="$T/bin/p9gpu-pids"
C="sh $T/chain/chain-a100.sh"; W="sh $T/chain/run-watch.sh"
out() { cat "$T/outbox.txt" 2>/dev/null; }
here() { (CHAIN_DIR=$T/chain PROG=test; . "$T/chain/lib.sh"; p9gpu_here); }   # the gate's process search, as the chain sees it
last() { tail -n 1 "$T/outbox.txt" 2>/dev/null; }
msgs() { if [ -f "$T/outbox.txt" ]; then wc -l < "$T/outbox.txt"; else echo 0; fi; }

# --- 1. production run running: nothing starts, no alarm ------------------------------------------------------------
$C tick
ok "running production run: V5 not started" '[ ! -f "$T/v5/run.pid" ]'
ok "running production run: no message" '[ "$(msgs)" -eq 0 ]'

# --- 2. production run stalls: alarm, once (no repeat within REPEAT_H) -----------------------------------------------
touch -d '-45 min' "$P/segments/seg000/stderr.txt" "$P/production.log"
$C tick; $C tick
ok "stall: one alarm" '[ "$(grep -c "keine neue Ausgabe" "$T/outbox.txt")" -eq 1 ]'
touch "$P/segments/seg000/stderr.txt"; $C tick
ok "stall over: cleared" 'last | grep -q "erledigt: Hauptlauf schreibt wieder"'

# --- 3. production run complete, but a compute process on the A100: V5 waits --------------------------------------
kill "$(cat "$P/production.pid")"; rm -f "$P/production.pid"
for k in 0 1 2; do mkdir -p "$P/segments/seg00$k"; : > "$P/segments/seg00$k/DONE"
  printf '%s\t%s\t%s\t10273.785\t%064d\t-\n' $k $(( (k + 1) * 100000000 )) 58519 7 >> "$P/segments.tsv"; done
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) production run complete: 3 segments" >> "$P/production.log"
echo "$U, 4242, ollama" > "$T/fake/apps.txt"
$C tick
ok "busy A100: V5 not started" '[ ! -f "$T/v5/run.pid" ]'
ok "busy A100: message names the finished run, its last hash and the reason" 'last | grep -q "Hauptlauf fertig: .*Hash 0\{63\}7.*V5 der Seeds 110–112 wird nicht gestartet: Rechenprozesse auf der A100: ollama(4242)"'

# --- 4. test mode: would start, starts nothing, own state ----------------------------------------------------------
: > "$T/fake/apps.txt"
$C dry-run > "$T/dry.txt"
ok "dry-run: V5 not started" '[ ! -f "$T/v5/run.pid" ]'
ok "dry-run: says what it would run" 'grep -q "Testmodus, würde ausführen: cd $T/v5 && CUDA_VISIBLE_DEVICES=$U sh start.sh" "$T/outbox.txt"'
ok "dry-run: own state directory" '[ -d "$T/chain/state-dry" ]'

# --- 5. the A100 free: V5 starts on the A100 (by UUID); the V2 short runs on the L40S do not block it ------------
# a process named p9gpu: perl sets the process name (a copy of sleep is not portable: multi-call coreutils)
fakep9() { (cd "$1" && exec perl -e '$0 = "p9gpu"; sleep 600') & }
mkdir -p "$T/v2" "$T/other"
fakep9 "$T/v2"; V2PID=$!; pids="$pids $V2PID"
echo "GPU-99999999-1111-2222-3333-444444444444, $V2PID, $T/v2/bin/p9gpu" > "$T/fake/apps.txt"
$C tick
ok "V5 started" '[ -f "$T/v5/run.pid" ] && kill -0 "$(cat "$T/v5/run.pid")"'
ok "V5 on the A100 UUID" 'grep -q "start: GPU $U" "$T/v5/start.log"'
ok "message: V5 gestartet" 'last | grep -q "V5 der Seeds 110–112 gestartet: started (pid"'
echo "$U, 77777, $T/v5/bin/p9gpu" >> "$T/fake/apps.txt"     # V5 on the A100
sleep 0.3; $C tick
ok "no second start while V5 runs" '[ "$(wc -l < "$T/v5/start.log")" -eq 1 ]'
ok "V2 run on the L40S: no wrong-card alarm" '! grep -q "anderen Karte" "$T/outbox.txt"'
fakep9 "$T/other"; OPID=$!; pids="$pids $OPID"; sleep 0.3
echo "GPU-99999999-1111-2222-3333-444444444444, $OPID, $T/other/bin/p9gpu" >> "$T/fake/apps.txt"
$C tick
ok "a p9gpu elsewhere outside the V2 package: alarm" 'last | grep -q "ALARM: p9gpu auf einer anderen Karte als der A100:  *p9gpu($OPID)"'
ok "process search of the test: sees the foreign p9gpu, which blocks a start" '"$T/bin/p9gpu-pids" | grep -qx "$OPID" && here | grep -qw "$OPID"'
kill $OPID; grep -v "$OPID" "$T/fake/apps.txt" > "$T/fake/apps2.txt"; mv "$T/fake/apps2.txt" "$T/fake/apps.txt"
sleep 0.3
ok "process search of the test: sees the V2 p9gpu, which is allowed" '"$T/bin/p9gpu-pids" | grep -qx "$V2PID" && [ -z "$(here)" ]'
$C tick
ok "foreign p9gpu gone: cleared" 'last | grep -q "erledigt: p9gpu nur noch auf der A100"'

# --- 6. halt signal while V5 runs: alarm, hold latched ----------------------------------------------------------------
echo "NVIDIA A100-PCIE-40GB, 66, 0x0000000000000040, 0, 1200, 250.0" > "$T/fake/gpu.txt"
$C tick
ok "halt: alarm with the reason" 'last | grep -q "ALARM: Halt-Signal der A100: Gründe 0x0000000000000040"'
ok "halt: hold latched" 'ls "$T/chain/state/hold.gpu" > /dev/null'
echo "NVIDIA A100-PCIE-40GB, 45, 0x0000000000000004, 0, 1395, 200.0" > "$T/fake/gpu.txt"
$C tick
ok "halt over: cleared, hold stays" 'last | grep -q "die Sperre bleibt" && [ -f "$T/chain/state/hold.gpu" ]'

# --- 7. V5 complete while the hold stands: set A does not start ---------------------------------------------------
for j in V5-s110 V5-s111 V5-s112; do finish_job "$T/v5" $j; done; end_pkg "$T/v5"
grep -v 77777 "$T/fake/apps.txt" > "$T/fake/apps2.txt"; mv "$T/fake/apps2.txt" "$T/fake/apps.txt"
echo "2026-11-10T00:00:00Z V5-s110 stopped (signal)" >> "$T/v5/run.log"   # the resume test
$C tick
ok "V5 complete, hold: set A not started" '[ ! -f "$T/sets/run.pid" ]'
ok "message: V5 fertig with the hashes of all three jobs" 'last | grep -q "V5 der Seeds 110–112 fertig: .*V5-s110: seg001.*V5-s111: seg001.*V5-s112: seg001"'
ok "message: the log line of the resume test blocks first" 'last | grep -q "Protokoll von V5 der Seeds 110–112 enthält: .*stopped (signal)"'
$C ack v5 > /dev/null; $C tick
ok "after ack v5: the hold blocks" '[ ! -f "$T/sets/run.pid" ] && last | grep -q "Halt-Sperre"'
$C ack hold > /dev/null
ok "ack hold: reported" 'last | grep -q "Halt-Sperre aufgehoben"'

# --- 8. set A: verdict and entry 4 ----------------------------------------------------------------------------------
$C tick
ok "no BB-A.ok, no e4: set A waits, the new reason reported" '[ ! -f "$T/sets/run.pid" ] && last | grep -q "Satz A wartet: v2/BB-A.ok enthält nicht.*e4-on-chain.ok fehlt"'
k=$(msgs); $C tick
ok "the same reason: not repeated" '[ "$(msgs)" -eq "$k" ]'
echo "outside the limits" > "$T/sets/v2/BB-A.ok"; : > "$T/chain/e4-on-chain.ok"
$C tick
ok "BB-A outside the limits: set A waits" '[ ! -f "$T/sets/run.pid" ] && last | grep -q "v2/BB-A.ok enthält nicht"'
echo "within the limits" > "$T/sets/v2/BB-A.ok"; rm -f "$T/chain/e4-on-chain.ok"
$C tick
ok "no e4-on-chain.ok: set A waits" '[ ! -f "$T/sets/run.pid" ] && last | grep -q "e4-on-chain.ok fehlt"'
: > "$T/chain/e4-on-chain.ok"; $C tick
ok "set A started with JOBS=BB-A" '[ -f "$T/sets/run.pid" ] && grep -q "jobs BB-A$" "$T/sets/start.log"'
$C tick
ok "set B not started while A runs" '[ "$(wc -l < "$T/sets/start.log")" -eq 1 ]'

# --- 9. set A stopped but not complete: alarm, nothing starts ------------------------------------------------------
kill "$(cat "$T/sets/run.pid")"; rm -f "$T/sets/run.pid"; mkdir -p "$T/sets/jobs/BB-A/segments/seg000"
$C tick
ok "stopped set A: alarm, no start" 'last | grep -q "Satz A läuft nicht und ist nicht fertig" && [ ! -f "$T/sets/run.pid" ]'

# --- 10. set A complete, error line, then set B -----------------------------------------------------------------------
rm -rf "$T/sets/jobs/BB-A/segments"; finish_job "$T/sets" BB-A
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) BB-A segment 3: p9gpu FAILED (see x)" >> "$T/sets/run.log"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) all jobs ended" >> "$T/sets/run.log"
echo "within the limits" > "$T/sets/v2/BB-B.ok"
$C tick
ok "error line in the sets log: set B not started" '[ ! -f "$T/sets/run.pid" ] && last | grep -q "p9gpu FAILED"'
$C ack sets > /dev/null; $C tick
ok "set B started with JOBS=BB-B" '[ -f "$T/sets/run.pid" ] && tail -n 1 "$T/sets/start.log" | grep -q "jobs BB-B$"'
finish_job "$T/sets" BB-B; end_pkg "$T/sets"; $C tick
ok "all done: final message" 'last | grep -q "Alle vier A100-Läufe sind fertig"'
k=$(msgs); $C tick
ok "all done: no further message" '[ "$(msgs)" -eq "$k" ]'

# --- 11. status is read only ------------------------------------------------------------------------------------------
k=$(msgs); $C status > "$T/status.txt"
ok "status: shows the four runs, sends nothing" 'grep -q "^Satz B: complete" "$T/status.txt" && [ "$(msgs)" -eq "$k" ]'

# --- 12. run-watch: chain heartbeat, MERCURIUS --------------------------------------------------------------------------
echo $(( $(date -u +%s) - 3600 )) > "$T/chain/state/last-tick"
$W tick
ok "watch: chain silent for 60 min -> alarm" 'last | grep -q "chain-a100.sh hat seit 60 min nicht geprüft"'
$C tick; $W tick
ok "watch: chain back -> cleared" 'last | grep -q "chain-a100.sh prüft wieder"'
(cd "$T/merc" && sh start.sh > /dev/null); mkdir -p "$T/merc/jobs/M-s110-part00/segments/seg000"
touch -d '-45 min' "$T/merc/run.log"; : > "$T/merc/jobs/M-s110-part00/segments/seg000/stderr.txt"
touch -d '-45 min' "$T/merc/jobs/M-s110-part00/segments/seg000/stderr.txt"
$W tick
ok "watch: MERCURIUS stalled -> alarm" 'last | grep -q "MERCURIUS: seit 4[5-9] min keine neue Ausgabe"'
rm -rf "$T/merc/jobs/M-s110-part00/segments"
finish_job "$T/merc" M-s110-part00; finish_job "$T/merc" M-s110-part01
kill "$(cat "$T/merc/run.pid")"; rm -f "$T/merc/run.pid"; echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) all slices ended" >> "$T/merc/run.log"
$W tick
ok "watch: MERCURIUS complete -> message" 'grep -q "MERCURIUS 110–112 fertig: MERCURIUS 110–112: 4 von 4 Segmenten" "$T/outbox.txt"'
$W report > /dev/null
ok "watch: report lists the four runs and the A100" 'grep -q "Bericht" "$T/outbox.txt" && grep -q "Satz B: complete" "$T/outbox.txt" && grep -q "A100: ok" "$T/outbox.txt"'

# --- 13. Telegram: file mode, token never on a command line ---------------------------------------------------------
unset TG_OUTBOX
F=$T/home/.config/p9chain/telegram.env
printf 'TELEGRAM_TOKEN=123456:ABC-def_GHI\nTELEGRAM_CHAT_ID=-1001234\n' > "$F"; chmod 644 "$F"
$C test-telegram > /dev/null 2>&1
ok "telegram: file with mode 644 refused" 'grep -q "must have mode 600" "$T/chain/chain.log" && [ ! -s "$T/fake/curl-argv.txt" ]'
chmod 600 "$F"
ok "telegram: sent with mode 600" '$C test-telegram > /dev/null 2>&1'
ok "telegram: the token is not on curl's command line" '! grep -q "ABC-def_GHI" "$T/fake/curl-argv.txt" && grep -q "bot123456:ABC-def_GHI/sendMessage" "$T/fake/curl-stdin.txt"'
ok "telegram: the token is in no log" '! grep -rq "ABC-def_GHI" "$T/chain/chain.log" "$T/chain/state"'

echo "== $n checks, $fails failed"
[ "$fails" -eq 0 ]
