#!/bin/sh
# MEDAS p9-search: the chain of the A100 runs on the GPU server (decisions of 2026-11-04 and 2026-11-06): production
# run -> V5 of seeds 110-112 -> CPU-2 measurement -> V5 half of the paired tests -> set A -> set B, one at a time.
# Runs as the user of the runs (p9sim), never as root.
#
#   sh chain-a100.sh tick          one check (what the systemd timer runs every 5 min)
#   sh chain-a100.sh loop          a check every INTERVAL s (300) until stopped (for tmux)
#   sh chain-a100.sh dry-run       one check in the test mode: starts nothing, sends nothing (messages to outbox.txt),
#                                  own state (state-dry/); shows what it would do
#   sh chain-a100.sh status        the state, read only: runs, A100, holds, what the next start waits for
#   sh chain-a100.sh ack prod|v5|cpu2|pair|sets|merc   the lines in that run's log so far are checked (fail/stop/error after
#                                  them stop the chain again); after a deliberate stop/start, e.g. the resume test
#   sh chain-a100.sh ack hold      lift the hold after a halt signal of the A100, once it is checked
#   sh chain-a100.sh pause|resume  no starts while paused (monitoring and alarms go on)
#   sh chain-a100.sh stop          stop the loop started with "loop" (the runs go on; systemd: see README)
#   sh chain-a100.sh test-telegram send a test message
#
# A transition, at each check: the current run is complete (all segments DONE, its completion line in the log, its
# process ended) -> the next run is started only if
#   - no hold: no halt signal of the A100 since the last "ack hold" (clock event reasons 0x8, 0x20, 0x40, 0x80,
#     more than TEMP_MAX deg C, uncorrected ECC errors, an Xid in the kernel log);
#   - the A100 answers and has no compute process, no run of the three packages is alive, no p9gpu runs;
#   - the log of the finished run has no fail/stop/error after the last "ack";
#   - for the V5 half of the paired tests: the file PAIR_OK (pair-on-chain.ok: their criteria, entry e5, on chain);
#   - for set A / set B: v2/BB-A.ok / v2/BB-B.ok in the sets package holds the line "within the limits", and the
#     file E4_OK (e4-on-chain.ok) exists;
# The CPU-2 measurement (CPU2_DIR) and the paired V5 half (PAIR_V5_DIR) are skipped if their directory is not set; a
# set is skipped if the operator created skip-setA / skip-setB in the chain directory (a set that is not run).
#   - the chain is not paused and not in the test mode.
# Otherwise it waits and reports why (Telegram, again every REPEAT_H hours). Every transition is reported: the run
# that finished, the hash of its last segment, the run started or why not. While a run is running: alarms for a halt
# signal, no new file for STALL_MIN minutes, fail/stop/error in its log, the run stopped but not complete, p9gpu on
# another card. The chain never stops a run and never starts one twice: stopping is the operator's decision.
set -u
cmd=${1:-}
case $cmd in ""|-h|--help|help) sed -n '2,30p' "$0"; exit 2 ;; esac
[ "$cmd" = dry-run ] && DRY_RUN=1
PROG=chain
CHAIN_DIR=$(cd "$(dirname "$0")" && pwd)
[ "${DRY_RUN:-0}" = 1 ] && STATE_SUFFIX=-dry || STATE_SUFFIX=""
. "$CHAIN_DIR/lib.sh"
if [ -n "$STATE_SUFFIX" ]; then STATE=$CHAIN_DIR/state$STATE_SUFFIX; mkdir -p "$STATE"; fi
[ "$(id -u)" != 0 ] || { echo "please run as the user of the runs, not as root"; exit 1; }

start_stage() {   # start_stage STAGE: 0 if started; WHY says what happened
  case $1 in v5) dir=$V5_DIR; jobs="" ;; cpu2) dir=$CPU2_DIR; jobs="" ;; pairV5) dir=$PAIR_V5_DIR; jobs="" ;;
    setA) dir=$SETS_DIR; jobs=BB-A ;; setB) dir=$SETS_DIR; jobs=BB-B ;; esac
  U=$(gpu_uuid)
  what="cd $dir && CUDA_VISIBLE_DEVICES=$U ${jobs:+JOBS=$jobs }sh start.sh"
  if [ "$DRY_RUN" = 1 ]; then WHY="Testmodus, würde ausführen: $what"; return 1; fi
  # 9>&-: the run must not inherit the lock of the chain (it would hold it for days and block every later check)
  out=$(cd "$dir" && env CUDA_VISIBLE_DEVICES="$U" ${jobs:+JOBS=$jobs} sh start.sh 9>&- 2>&1); rc=$?
  printf '%s %s: %s\n%s\n' "$(ts)" "$1" "$what" "$out" >> "$STATE/start.out"
  if [ $rc -eq 0 ] && printf '%s\n' "$out" | grep -q '^started (pid'; then
    WHY="$(printf '%s\n' "$out" | grep '^started (pid' | cut -d';' -f1); $(tail -n 1 "$dir/start.log" 2>/dev/null | cut -d' ' -f2-)"
    return 0
  fi
  WHY="start.sh hat nicht gestartet (rc $rc): $(printf '%s\n' "$out" | tail -n 2 | tr '\n' ' ')"
  return 1
}

gate() {          # gate STAGE: 0 if it may start now; else WHY
  WHY=""
  h=$(holds)
  [ -z "$h" ] || { WHY="Halt-Sperre seit: $h (nach Prüfung: chain-a100.sh ack hold)"; return 1; }
  [ "$HEALTH" = ok ] || { WHY="A100 nicht in Ordnung: $HEALTH_TEXT"; return 1; }
  [ ! -f "$CHAIN_DIR/PAUSE" ] || { WHY="Kette pausiert (chain-a100.sh resume)"; return 1; }
  ! any_run_alive || { WHY="ein Lauf eines Pakets der Kette ist noch aktiv"; return 1; }
  gpu_apps
  [ -z "$A100_APPS" ] || { WHY="Rechenprozesse auf der A100: $A100_APPS"; return 1; }
  p=$(p9gpu_here)
  [ -z "$p" ] || { WHY="p9gpu läuft noch (pid $p)"; return 1; }
  case $1 in
    pairV5)
      [ -f "$PAIR_OK" ] || { WHY="$PAIR_OK fehlt (Kriterien der Paartests, Eintrag e5, auf der Chain)"; return 1; } ;;
    setA|setB)
      j=BB-${1#set}
      grep -qx "within the limits" "$SETS_DIR/v2/$j.ok" 2>/dev/null || WHY="v2/$j.ok enthält nicht die Zeile 'within the limits';"
      [ -f "$E4_OK" ] || WHY="$WHY $E4_OK fehlt (Eintrag 4 auf der Chain);"
      [ -z "$WHY" ] || return 1 ;;
  esac
  return 0
}

monitor() {       # monitor STAGE (running): alarms
  n=$(stage_name "$1")
  errs=$(log_errors "$LOG" "$ERRKEY")
  if [ -n "$errs" ]; then alarm "logerr-$1" "Protokoll von $n: $errs (nach Prüfung: chain-a100.sh ack $ERRKEY)"
  else clear_alarm "logerr-$1" "Protokoll von $n wieder ohne Fehlerzeilen"; fi
  t=$(newest "$DIR"); [ -n "$t" ] || t=$(stat -c %Y "$LOG" 2>/dev/null || now)
  age=$(( ($(now) - t) / 60 ))
  if [ "$age" -gt "$STALL_MIN" ]; then alarm "stall-$1" "$n: seit $age min keine neue Ausgabe ($INFO)"
  else clear_alarm "stall-$1" "$n schreibt wieder ($INFO)"; fi
  gpu_apps
  if [ -n "$P9_ELSEWHERE" ]; then alarm wrongcard "p9gpu auf einer anderen Karte als der A100: $P9_ELSEWHERE"; else clear_alarm wrongcard "p9gpu nur noch auf der A100"; fi
  if [ -z "$A100_APPS" ]; then
    c=$(( $(cat "$STATE/noapp" 2>/dev/null || echo 0) + 1 )); echo "$c" > "$STATE/noapp"
    [ "$c" -ge 3 ] && alarm "noapp-$1" "$n läuft, aber seit $c Prüfungen ist kein Prozess auf der A100"
  else
    echo 0 > "$STATE/noapp"; clear_alarm "noapp-$1" "$n wieder auf der A100"
  fi
}

tick() {
  exec 9> "$STATE/lock"
  flock -n 9 || { log "the previous check still runs"; return 0; }
  now > "$STATE/last-tick"
  gpu_health
  case $HEALTH in
    ok) [ -f "$STATE/hold.gpu" ] && clear_alarm gpu "kein Halt-Signal mehr ($HEALTH_TEXT); die Sperre bleibt bis chain-a100.sh ack hold"
        [ -f "$STATE/hold.gpu" ] || clear_alarm gpu "A100 wieder in Ordnung ($HEALTH_TEXT)" ;;
    halt) alarm gpu "$HEALTH_TEXT. Nichts Neues wird gestartet. Laufende Läufe laufen weiter: prüfen und ggf. stop.sh des Laufs (Anleitung)." ;;
    *) alarm gpu "A100 nicht prüfbar: $HEALTH_TEXT. Nichts Neues wird gestartet." ;;
  esac
  prev=""
  for s in $STAGES; do
    stage_status "$s"
    case $ST in
      complete) prev=$s; prev_info=$INFO; prev_last=$LAST; prev_log=$LOG; prev_key=$ERRKEY; continue ;;
      skipped)
        case $s in setA|setB) once "skip-$s" "$INFO: die Kette geht zum nächsten Lauf weiter." ;; esac
        skipped="${skipped:-}${skipped:+, }$(stage_name "$s")"
        continue ;;
      running) monitor "$s"; return 0 ;;
      stopped)
        alarm "stopped-$s" "$(stage_name "$s") läuft nicht und ist nicht fertig: $INFO. $(log_errors "$LOG" "$ERRKEY") Die Kette startet nichts; weiter mit start.sh des Laufs (sie erkennt ihn dann als laufend)."
        return 0 ;;
      notstarted)
        if [ -z "$prev" ]; then alarm "notstarted-$s" "$(stage_name "$s") ist nicht gestartet ($DIR); die Kette startet den Hauptlauf nicht selbst."; return 0; fi
        fin=""
        if [ ! -f "$STATE/once.done-$prev" ]; then
          : > "$STATE/once.done-$prev"
          fin="$(stage_name "$prev") fertig: $prev_info. Letztes Segment: $prev_last. "
        fi
        errs=$(log_errors "$prev_log" "$prev_key")
        if [ -n "$errs" ]; then
          WHY="Protokoll von $(stage_name "$prev") enthält: $errs (nach Prüfung: chain-a100.sh ack $prev_key)"
        elif gate "$s"; then
          if start_stage "$s"; then
            rm -f "$STATE/alarm.wait-$s"
            tg "$fin$(stage_name "$s") gestartet: $WHY"
            return 0
          fi
        fi
        # a new reason is reported at once; the same one again only every REPEAT_H hours (digits ignored: pids, minutes)
        sig=$(printf '%s' "$WHY" | tr -d '0-9')
        [ "$sig" = "$(cat "$STATE/why.wait-$s" 2>/dev/null)" ] || rm -f "$STATE/alarm.wait-$s"
        printf '%s' "$sig" > "$STATE/why.wait-$s"
        if [ -n "$fin" ]; then now > "$STATE/alarm.wait-$s"; log "waiting: $WHY"; tg "$fin$(stage_name "$s") wird nicht gestartet: $WHY"
        else alarm "wait-$s" "$(stage_name "$s") wartet: $WHY"; fi
        return 0 ;;
    esac
  done
  if [ ! -f "$STATE/once.done-all" ]; then
    : > "$STATE/once.done-all"
    fin=""
    if [ -n "$prev" ] && [ ! -f "$STATE/once.done-$prev" ]; then
      : > "$STATE/once.done-$prev"
      fin="$(stage_name "$prev") fertig: $prev_info. Letztes Segment: $prev_last. "
    fi
    tg "${fin}Alle A100-Läufe der Kette sind abgeschlossen${skipped:+ (übersprungen: $skipped)}; die Kette startet nichts mehr."
  fi
}

status() {        # read only: no messages, no holds
  tg() { :; }; alarm() { :; }; clear_alarm() { :; }; once() { :; }; hold() { :; }
  READONLY=1
  echo "Kette: $CHAIN_DIR ($( [ -f "$CHAIN_DIR/PAUSE" ] && echo pausiert || echo aktiv); letzte Prüfung: $( [ -f "$STATE/last-tick" ] && echo "vor $(( ($(now) - $(cat "$STATE/last-tick")) / 60 )) min" || echo nie))"
  gpu_health; echo "A100: $HEALTH; $HEALTH_TEXT"
  [ "${XID_READABLE:-}" = no ] && echo "Xid: Kernel-Log nicht lesbar"
  h=$(holds); [ -n "$h" ] && echo "Halt-Sperre: $h"
  for s in $STAGES; do
    stage_status "$s"
    echo "$(stage_name "$s"): $ST; $INFO${LAST:+; zuletzt $LAST}"
    e=$(log_errors "$LOG" "$ERRKEY"); [ -n "$e" ] && echo "   Fehlerzeilen im Protokoll: $e"
  done
  for s in $STAGES; do
    [ "$s" = prod ] && continue
    stage_status "$s"
    [ "$ST" = notstarted ] || continue
    if gate "$s"; then echo "nächster Start: $(stage_name "$s") wäre jetzt möglich"; else echo "nächster Start: $(stage_name "$s") wartet: $WHY"; fi
    break
  done
  ls "$STATE"/alarm.* > /dev/null 2>&1 && echo "offene Alarme: $(cd "$STATE" && ls alarm.* | sed 's/alarm\.//' | tr '\n' ' ')"
  [ -s "$STATE/tg-queue" ] && echo "nicht gesendete Meldungen: $(wc -l < "$STATE/tg-queue")"
  return 0
}

case $cmd in
  tick) tick ;;
  dry-run) tick; echo "== Testmodus: Meldungen (outbox.txt, die letzten 5):"; tail -n 5 "${TG_OUTBOX:-$CHAIN_DIR/outbox.txt}" 2>/dev/null; echo "== Zustand:"; status ;;
  loop)
    if alive "$CHAIN_DIR/loop.pid"; then echo "loop already running (pid $(cat "$CHAIN_DIR/loop.pid"))"; exit 1; fi
    echo $$ > "$CHAIN_DIR/loop.pid"
    trap 'rm -f "$CHAIN_DIR/loop.pid"; log "loop stopped"; exit 0' INT TERM HUP
    log "loop started (every $INTERVAL s)"
    while :; do tick; sleep "$INTERVAL" & wait $!; done ;;
  stop)
    if alive "$CHAIN_DIR/loop.pid"; then kill -TERM "$(cat "$CHAIN_DIR/loop.pid")"; echo "loop stopped (the runs go on)"
    else echo "no loop running here; with systemd: systemctl --user stop p9-chain.timer"; fi ;;
  status) status ;;
  ack)
    case ${2:-} in
      prod) f=$PROD_DIR/production.log ;; v5) f=$V5_DIR/run.log ;; sets) f=$SETS_DIR/run.log ;; merc) f=${MERC_DIR:+$MERC_DIR/run.log} ;;
      cpu2) f=${CPU2_DIR:+$CPU2_DIR/run.log} ;; pair) f=${PAIR_V5_DIR:+$PAIR_V5_DIR/run.log} ;;
      hold) h=$(holds); rm -f "$STATE"/hold.*; [ -n "$h" ] && { log "hold lifted: $h"; tg "Halt-Sperre aufgehoben (ack): $h"; }; echo "hold lifted"; exit 0 ;;
      *) echo "ack prod|v5|cpu2|pair|sets|merc|hold"; exit 2 ;;
    esac
    [ -n "$f" ] && [ -f "$f" ] || { echo "no log $f"; exit 2; }
    n=$(wc -l < "$f"); echo "$n" > "$STATE/ack.$2"; log "ack $2: $n lines of $f checked"; echo "ack $2: the $n lines of $f so far are checked" ;;
  pause) : > "$CHAIN_DIR/PAUSE"; log paused; echo "paused: no starts; monitoring goes on" ;;
  resume) rm -f "$CHAIN_DIR/PAUSE"; log resumed; echo "resumed" ;;
  test-telegram) if [ "$DRY_RUN" = 1 ]; then tg "Test"; else tg_send "[A100-Kette] Test von $(id -un), $(ts)" && echo "sent" || { echo "not sent; see chain.log"; exit 1; }; fi ;;
  *) sed -n '2,20p' "$0"; exit 2 ;;
esac
