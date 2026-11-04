#!/bin/sh
# MEDAS p9-search: Telegram watcher of the runs on the GPU server, next to chain-a100.sh (same chain.env, same
# Telegram file). It starts and stops nothing.
#
#   sh run-watch.sh tick       one check (the systemd timer: every 5 min)
#   sh run-watch.sh loop       a check every INTERVAL s until stopped (for tmux)
#   sh run-watch.sh report     send the status report now
#   sh run-watch.sh stop       stop the loop started with "loop"
#   DRY_RUN=1 sh run-watch.sh tick|report   test mode: messages to outbox.txt, nothing sent, own state (state-dry/)
#
# What it watches:
#   - the chain itself: an alarm when chain-a100.sh has not checked for 3 x INTERVAL (tmux session or timer gone);
#   - the MERCURIUS part of seeds 110-112 on CPU 1 (MERC_DIR, optional): stopped but not complete, no new file for
#     STALL_MERC_MIN minutes, fail/stop/error in run.log after "chain-a100.sh ack merc", and once when it is complete;
#   - at the hours REPORT_HOURS (UTC; default 07 and 19) a report: the four A100 runs, the A100, MERCURIUS, disk.
# The A100 runs themselves are watched by chain-a100.sh (halt signals, progress, logs, transitions).
set -u
cmd=${1:-}
PROG=watch
CHAIN_DIR=$(cd "$(dirname "$0")" && pwd)
. "$CHAIN_DIR/lib.sh"
if [ "$DRY_RUN" = 1 ]; then STATE=$CHAIN_DIR/state-dry; mkdir -p "$STATE"; fi
[ "$(id -u)" != 0 ] || { echo "please run as the user of the runs, not as root"; exit 1; }

merc_status() {   # MST (notstarted | running | complete | stopped), MINFO, MLAST
  D=$MERC_DIR; MLOG=$D/run.log
  tot=0; d=0; slices=0; full=0
  for J in "$D"/jobs/*/; do
    t=$(segs_total "$J/params.env"); n=$(segs_done "$J")
    tot=$((tot + t)); d=$((d + n)); slices=$((slices + 1)); [ "$n" -eq "$t" ] && full=$((full + 1))
  done
  MINFO="MERCURIUS 110–112: $d von $tot Segmenten, $full von $slices Stücken fertig"
  MLAST=$(cat "$D"/jobs/*/segments.tsv 2>/dev/null | wc -l)
  if alive "$D/run.pid"; then MST=running
  elif [ "$tot" -gt 0 ] && [ "$d" -eq "$tot" ] && grep -q "all slices ended" "$MLOG" 2>/dev/null; then MST=complete
  elif [ ! -f "$MLOG" ]; then MST=notstarted
  else MST=stopped; fi
}

report() {
  READONLY=1
  r="Bericht $(ts)"
  for s in $STAGES; do stage_status "$s"; r="$r
- $(stage_name "$s"): $ST; $INFO${LAST:+; zuletzt $LAST}"; done
  # the A100 without holds or Xid side effects (report runs in a subshell: these overrides end with it)
  hold() { :; }; once() { :; }
  gpu_health
  r="$r
- A100: $HEALTH; $HEALTH_TEXT"
  [ -n "$(holds)" ] && r="$r
- Halt-Sperre: $(holds)"
  if [ -n "$MERC_DIR" ]; then merc_status; r="$r
- $MINFO ($MST)"; fi
  r="$r
- Platte: $(df -h "$PROD_DIR" | tail -n 1 | awk '{ print $4 " frei von " $2 }')"
  [ -f "$CHAIN_DIR/PAUSE" ] && r="$r
- Kette pausiert"
  printf '%s\n' "$r"
}

tick() {
  exec 8> "$STATE/watch.lock"
  flock -n 8 || return 0
  # the chain
  CS=$CHAIN_DIR/state; [ "$DRY_RUN" = 1 ] && CS=$CHAIN_DIR/state-dry
  lt=$(cat "$CS/last-tick" 2>/dev/null || echo 0)
  age=$(( ($(now) - lt) / 60 ))
  if [ "$age" -gt $(( 3 * INTERVAL / 60 )) ]; then alarm chain-dead "chain-a100.sh hat seit $age min nicht geprüft (tmux-Sitzung oder Timer weg?)"
  else clear_alarm chain-dead "chain-a100.sh prüft wieder"; fi
  # MERCURIUS
  if [ -n "$MERC_DIR" ]; then
    merc_status
    case $MST in
      running)
        errs=$(log_errors "$MLOG" merc)
        if [ -n "$errs" ]; then alarm merc-log "Protokoll von MERCURIUS: $errs (nach Prüfung: chain-a100.sh ack merc)"
        else clear_alarm merc-log "Protokoll von MERCURIUS wieder ohne Fehlerzeilen"; fi
        t=$(newest "$MERC_DIR"); [ -n "$t" ] || t=$(stat -c %Y "$MLOG" 2>/dev/null || now)
        a=$(( ($(now) - t) / 60 ))
        if [ "$a" -gt "$STALL_MERC_MIN" ]; then alarm merc-stall "MERCURIUS: seit $a min keine neue Ausgabe ($MINFO)"
        else clear_alarm merc-stall "MERCURIUS schreibt wieder"; fi
        clear_alarm merc-stopped "MERCURIUS läuft wieder" ;;
      complete) once merc-done "MERCURIUS 110–112 fertig: $MINFO; $MLAST Segmentzeilen in den segments.tsv. Bitte run.log, start.log und jobs/*/segments.tsv sichern." ;;
      stopped) alarm merc-stopped "MERCURIUS läuft nicht und ist nicht fertig: $MINFO. $(log_errors "$MLOG" merc)" ;;
      notstarted) : ;;
    esac
  fi
  # reports
  hh=$(date -u +%H)
  for want in $REPORT_HOURS; do
    [ "$hh" = "$want" ] || continue
    key=$(date -u +%Y%m%d)-$want
    [ -f "$STATE/report.$key" ] && continue
    : > "$STATE/report.$key"
    tg "$(report)"
  done
  return 0
}

case $cmd in
  tick) tick ;;
  report) tg "$(report)"; [ "$DRY_RUN" = 1 ] && tail -n 12 "${TG_OUTBOX:-$CHAIN_DIR/outbox.txt}" ;;
  loop)
    if alive "$CHAIN_DIR/watch.pid"; then echo "watcher already running (pid $(cat "$CHAIN_DIR/watch.pid"))"; exit 1; fi
    echo $$ > "$CHAIN_DIR/watch.pid"
    trap 'rm -f "$CHAIN_DIR/watch.pid"; log "watch loop stopped"; exit 0' INT TERM HUP
    log "watch loop started (every $INTERVAL s)"
    while :; do tick; sleep "$INTERVAL" & wait $!; done ;;
  stop)
    if alive "$CHAIN_DIR/watch.pid"; then kill -TERM "$(cat "$CHAIN_DIR/watch.pid")"; echo "watcher stopped"
    else echo "no watcher loop running here; with systemd: systemctl --user stop p9-watch.timer"; fi ;;
  *) sed -n '2,17p' "$0"; exit 2 ;;
esac
