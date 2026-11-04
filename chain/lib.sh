# MEDAS p9-search, A100 chain and run watcher: common functions (sourced by chain-a100.sh and run-watch.sh).
# POSIX sh (dash). Reads chain.env next to the scripts (or CHAIN_CONF). Never prints or logs the Telegram token.

export LC_ALL=C
CHAIN_DIR=${CHAIN_DIR:-$(cd "$(dirname "$0")" && pwd)}
CONF=${CHAIN_CONF:-$CHAIN_DIR/chain.env}
[ -f "$CONF" ] || { echo "no $CONF: cp chain.env.example chain.env and fill in the paths"; exit 2; }
. "$CONF"
: "${PROD_DIR:?}" "${V5_DIR:?}" "${SETS_DIR:?}"
MERC_DIR=${MERC_DIR:-}
GPU_NAME=${GPU_NAME:-A100}
GPU_UUID=${GPU_UUID:-}
E4_OK=${E4_OK:-$CHAIN_DIR/e4-on-chain.ok}
TELEGRAM_FILE=${TELEGRAM_FILE:-$HOME/.config/p9chain/telegram.env}
INTERVAL=${INTERVAL:-300}
STALL_MIN=${STALL_MIN:-90}
STALL_MERC_MIN=${STALL_MERC_MIN:-120}
REPEAT_H=${REPEAT_H:-6}
TEMP_MAX=${TEMP_MAX:-85}
REPORT_HOURS=${REPORT_HOURS:-"07 19"}
XID_CMD=${XID_CMD:-journalctl -k -q --no-pager -o short-iso}
DRY_RUN=${DRY_RUN:-0}
STATE=$CHAIN_DIR/state
mkdir -p "$STATE"
HALT_MASK=232            # clock event reasons 0x8 hw_slowdown | 0x20 sw_thermal | 0x40 hw_thermal | 0x80 hw_power_brake

now() { date -u +%s; }
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { printf '%s %s %s\n' "$(ts)" "$PROG" "$*" >> "$CHAIN_DIR/chain.log"; }
say() { printf '%s\n' "$*"; log "$*"; }

# --- Telegram ----------------------------------------------------------------------------------------------------
# The token file: two lines TELEGRAM_TOKEN=<bot token> and TELEGRAM_CHAT_ID=<chat id>, mode 600, owned by this user.
# It is read, not sourced. The token goes to curl through its config on stdin, never on a command line.
tg_creds() {
  f=$TELEGRAM_FILE
  [ -f "$f" ] || { log "telegram: no $f"; return 1; }
  [ "$(stat -c %a "$f")" = 600 ] && [ "$(stat -c %u "$f")" = "$(id -u)" ] || { log "telegram: $f must have mode 600 and belong to $(id -un)"; return 1; }
  TG_TOKEN=$(sed -n 's/^TELEGRAM_TOKEN=//p' "$f" | head -n 1 | tr -d '"'"'"' \r')
  TG_CHAT=$(sed -n 's/^TELEGRAM_CHAT_ID=//p' "$f" | head -n 1 | tr -d '"'"'"' \r')
  printf '%s' "$TG_TOKEN" | grep -Eq '^[0-9]+:[A-Za-z0-9_-]+$' || { log "telegram: TELEGRAM_TOKEN missing or malformed in $f"; return 1; }
  printf '%s' "$TG_CHAT" | grep -Eq '^-?[0-9]+$' || { log "telegram: TELEGRAM_CHAT_ID missing or malformed in $f"; return 1; }
}

tg_send() {   # $1: text; returns 0 if Telegram accepted it
  tg_creds || return 1
  code=$(printf 'url = "https://api.telegram.org/bot%s/sendMessage"\ndata-urlencode = "chat_id=%s"\n' "$TG_TOKEN" "$TG_CHAT" |
    curl -s --max-time 20 -K - --data-urlencode "text=$1" -o /dev/null -w '%{http_code}' 2>/dev/null)
  TG_TOKEN=""
  [ "$code" = 200 ] || { log "telegram: HTTP ${code:-none}"; return 1; }
}

# tg TEXT: send (or, in the test mode, write to the outbox); unsent messages are queued and sent with the next one
tg() {
  msg="[A100-Kette] $1"
  if [ "$DRY_RUN" = 1 ] || [ -n "${TG_OUTBOX:-}" ]; then
    printf '%s %s\n' "$(ts)" "$msg" >> "${TG_OUTBOX:-$CHAIN_DIR/outbox.txt}"
    log "message (test mode, not sent): $1"
    return 0
  fi
  if [ -s "$STATE/tg-queue" ]; then
    q=$(cat "$STATE/tg-queue")
    tg_send "(nachgereicht) $q" && : > "$STATE/tg-queue"
  fi
  if tg_send "$msg"; then log "message sent: $1"; else printf '%s %s\n' "$(ts)" "$msg" >> "$STATE/tg-queue"; log "message queued: $1"; fi
}

# alarm KEY TEXT: sent at once, then again every REPEAT_H hours while it lasts; clear KEY TEXT: once when it is over
alarm() {
  k=$1; shift
  f=$STATE/alarm.$k
  if [ -f "$f" ] && [ $(( $(now) - $(cat "$f") )) -lt $(( REPEAT_H * 3600 )) ]; then return 0; fi
  now > "$f"
  log "ALARM $k: $*"
  tg "ALARM: $*"
}
clear_alarm() {
  k=$1; shift
  [ -f "$STATE/alarm.$k" ] || return 0
  rm -f "$STATE/alarm.$k"
  log "cleared $k"
  tg "erledigt: $*"
}
once() {      # once KEY TEXT: a message only the first time
  k=$1; shift
  [ -f "$STATE/once.$k" ] && return 0
  : > "$STATE/once.$k"
  tg "$*"
}
hold() {      # hold KEY TEXT: latch that blocks every start until "chain-a100.sh ack hold"
  k=$1; shift
  [ -f "$STATE/hold.$k" ] || { printf '%s %s\n' "$(ts)" "$*" > "$STATE/hold.$k"; log "HOLD $k: $*"; }
}
holds() { cat "$STATE"/hold.* 2>/dev/null; }

# --- the A100 -----------------------------------------------------------------------------------------------------
nvq() {       # nvidia-smi with 3 tries (transient query failures were seen)
  for i in 1 2 3; do out=$(nvidia-smi "$@" 2>/dev/null) && [ -n "$out" ] && { printf '%s\n' "$out"; return 0; }; sleep 2; done
  return 1
}
gpu_uuid() {
  if [ -n "$GPU_UUID" ]; then echo "$GPU_UUID"; return 0; fi
  nvq --query-gpu=uuid,name --format=csv,noheader | awk -F', ' -v n="$GPU_NAME" 'index($2, n) { print $1; exit }'
}
# gpu_health: HEALTH (ok | halt | unknown) and HEALTH_TEXT; latches a hold for every halt signal
gpu_health() {
  U=$(gpu_uuid)
  if [ -z "$U" ]; then HEALTH=unknown; HEALTH_TEXT="keine Karte mit dem Namen $GPU_NAME gefunden"; return; fi
  q=$(nvq -i "$U" --query-gpu=name,temperature.gpu,clocks_event_reasons.active,ecc.errors.uncorrected.volatile.total,clocks.sm,power.draw --format=csv,noheader,nounits) ||
    { HEALTH=unknown; HEALTH_TEXT="nvidia-smi gibt für $U keine Werte"; return; }
  name=$(echo "$q" | cut -d, -f1 | sed 's/^ *//'); temp=$(echo "$q" | cut -d, -f2 | tr -d ' ')
  reasons=$(echo "$q" | cut -d, -f3 | tr -d ' '); ecc=$(echo "$q" | cut -d, -f4 | tr -d ' ')
  clk=$(echo "$q" | cut -d, -f5 | tr -d ' '); pwr=$(echo "$q" | cut -d, -f6 | tr -d ' ')
  GPU_LINE="$name, ${temp} °C, ${clk} MHz, ${pwr} W, Gründe $reasons, ECC unkorrigiert $ecc"
  case "$name" in *"$GPU_NAME"*) ;; *) HEALTH=unknown; HEALTH_TEXT="Karte $U heißt '$name', nicht $GPU_NAME"; return ;; esac
  printf '%s' "$temp" | grep -Eq '^[0-9]+$' && printf '%s' "$ecc" | grep -Eq '^[0-9]+$' && printf '%s' "$reasons" | grep -Eq '^0x[0-9a-fA-F]+$' ||
    { HEALTH=unknown; HEALTH_TEXT="nicht lesbar: $GPU_LINE"; return; }
  why=""
  [ $(( reasons & HALT_MASK )) -ne 0 ] && why="$why Gründe $reasons (0x8/0x20/0x40/0x80);"
  [ "$temp" -gt "$TEMP_MAX" ] && why="$why Temperatur $temp °C > $TEMP_MAX;"
  [ "$ecc" -gt 0 ] && why="$why unkorrigierte ECC-Fehler $ecc;"
  xid_check
  [ -n "$XID" ] && why="$why Xid im Kernel-Log: $XID;"
  if [ -n "$why" ]; then
    HEALTH=halt; HEALTH_TEXT="Halt-Signal der A100:$why ($GPU_LINE)"
    hold gpu "$HEALTH_TEXT"
  else
    HEALTH=ok; HEALTH_TEXT=$GPU_LINE
  fi
}
# xid_check: XID = new Xid lines in the kernel log since the last check (empty if none); XID_READABLE = yes | no
xid_check() {
  XID=""
  since=$(cat "$STATE/xid-since" 2>/dev/null || echo "-1h")
  out=$($XID_CMD --since "$since" 2>&1); rc=$?
  if [ $rc -ne 0 ] || printf '%s' "$out" | grep -qi -E 'insufficient permissions|not seeing messages|no journal files'; then
    XID_READABLE=no
    once xid-unreadable "Hinweis: Das Kernel-Log ist für $(id -un) nicht lesbar, Xid wird nicht geprüft (Anleitung: Gruppe systemd-journal)."
    return
  fi
  XID_READABLE=yes
  [ "${READONLY:-0}" = 1 ] || date -u +'%Y-%m-%d %H:%M:%S UTC' > "$STATE/xid-since"
  XID=$(printf '%s\n' "$out" | grep -i 'NVRM: Xid' | head -n 3 | tr '\n' ' ')
}
# compute processes: on the A100 (A100_APPS) and p9gpu on any other card (P9_ELSEWHERE)
gpu_apps() {
  U=$(gpu_uuid)
  apps=$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name --format=csv,noheader 2>/dev/null)
  A100_APPS=$(printf '%s\n' "$apps" | awk -F', ' -v u="$U" '$1 == u { printf "%s(%s) ", $3, $2 }')
  P9_ELSEWHERE=$(printf '%s\n' "$apps" | awk -F', ' -v u="$U" '$1 != u && $3 ~ /p9gpu/ { printf "%s(%s) on %s ", $3, $2, $1 }')
}

# --- the runs -----------------------------------------------------------------------------------------------------
alive() { [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null; }
segs_done() { ls "$1"/segments/seg*/DONE 2>/dev/null | wc -l; }
segs_total() { sed -n 's/^SEGMENTS=//p' "$1" | tail -n 1; }

# log_errors LOG KEY: the lines matching fail|stop|error after the acknowledged line (chain-a100.sh ack KEY)
log_errors() {
  [ -f "$1" ] || return 0
  from=$(cat "$STATE/ack.$2" 2>/dev/null || echo 0)
  awk -v from="$from" 'NR > from && tolower($0) ~ /fail|stop|error/' "$1" | tail -n 3
}
# newest file change (epoch) under the segments of a run directory
newest() { find "$@" -path '*/segments/*' -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -n 1 | cut -d. -f1; }

# stage_status STAGE: ST (notstarted | running | complete | stopped), DIR, LOG, ERRKEY, PIDF, INFO (summary), LAST (hashes)
stage_status() {
  case $1 in
    prod)
      DIR=$PROD_DIR; LOG=$DIR/production.log; ERRKEY=prod; PIDF=$DIR/production.pid
      tot=$(segs_total "$DIR/params.env"); d=$(segs_done "$DIR")
      INFO="Hauptlauf: $d von $tot Segmenten"
      LAST=""
      [ -s "$DIR/segments.tsv" ] && LAST=$(tail -n 1 "$DIR/segments.tsv" | awk -F'\t' '{ printf "seg%03d bis %.0f Myr, %d Testteilchen übrig, Hash %s", $1, $2 / 1e6, $3 - 6, $5 }')
      if alive "$PIDF"; then ST=running
      elif [ "$d" -eq "$tot" ] && grep -q "production run complete" "$LOG" 2>/dev/null; then ST=complete
      elif [ ! -f "$LOG" ]; then ST=notstarted
      else ST=stopped; fi ;;
    v5)
      DIR=$V5_DIR; LOG=$DIR/run.log; ERRKEY=v5; PIDF=$DIR/run.pid
      all=1; INFO="V5 110–112:"; LAST=""
      for J in "$DIR"/jobs/*/; do
        j=$(basename "$J"); tot=$(segs_total "$J/params.env"); d=$(segs_done "$J")
        INFO="$INFO $j $d/$tot;"
        [ "$d" -eq "$tot" ] || all=0
        [ -s "$J/segments.tsv" ] && LAST="$LAST $j: $(tail -n 1 "$J/segments.tsv" | awk -F'\t' '{ printf "seg%03d, %d übrig, Hash %s;", $1, $3 - 6, $5 }')"
      done
      if alive "$PIDF"; then ST=running
      elif [ $all = 1 ] && grep -q "all jobs ended" "$LOG" 2>/dev/null; then ST=complete
      elif [ ! -f "$LOG" ]; then ST=notstarted
      else ST=stopped; fi ;;
    setA|setB)
      DIR=$SETS_DIR; LOG=$DIR/run.log; ERRKEY=sets; PIDF=$DIR/run.pid
      j=BB-${1#set}; J=$DIR/jobs/$j
      tot=$(segs_total "$J/params.env"); d=$(segs_done "$J")
      INFO="Satz ${1#set} ($j): $d von $tot Segmenten"
      LAST=""
      [ -s "$J/segments.tsv" ] && LAST=$(tail -n 1 "$J/segments.tsv" | awk -F'\t' '{ printf "seg%03d bis %.0f Myr, %d Testteilchen übrig, Hash %s", $1, $2 / 1e6, $3 - 6, $5 }')
      cur=$(grep 'start, package' "$LOG" 2>/dev/null | tail -n 1 | sed 's/.*jobs: //')
      if alive "$PIDF" && [ "$cur" = "$j" ]; then ST=running
      elif [ "$d" -eq "$tot" ] && grep -q "$j complete: $tot segments" "$LOG" 2>/dev/null; then ST=complete
      elif [ ! -d "$J/segments" ]; then ST=notstarted
      else ST=stopped; fi ;;
  esac
}
STAGES="prod v5 setA setB"
stage_name() { case $1 in prod) echo "Hauptlauf";; v5) echo "V5 der Seeds 110–112";; setA) echo "Satz A";; setB) echo "Satz B";; esac; }
any_run_alive() { alive "$PROD_DIR/production.pid" || alive "$V5_DIR/run.pid" || alive "$SETS_DIR/run.pid"; }
