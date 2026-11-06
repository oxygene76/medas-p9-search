# A100-Kette und Lauf-Wächter: Einrichtung und Betrieb

Paket `p9chain`. Es enthält:
- `chain-a100.sh`: verkettet die A100-Läufe;
- `run-watch.sh`: ein Telegram-Wächter;
- gemeinsam `lib.sh`, eine Beispiel-Einstellung, systemd-Units und einen Test mit Attrappen.

Alles läuft als **p9sim**, nie als root, mit `LC_ALL=C`. Befehle mit „root“ davor brauchen root.

**Was die Kette tut:**
- Alle 5 Minuten prüft sie die Läufe in dieser Reihenfolge: Hauptlauf → V5 der Seeds 110–112 → CPU-2-Messung →
  V5-Hälfte der Paartests → Satz A → Satz B (Erweiterung vom 06.11., Abschnitt 9).
- Ist der aktuelle Lauf fertig, startet sie den nächsten. Bedingungen:
  - keine Halt-Sperre;
  - die A100 ist in Ordnung und frei, kein Lauf eines Pakets der Kette lebt, kein p9gpu-Prozess läuft;
  - das Protokoll des fertigen Laufs ist ohne `fail`/`stop`/`error`;
  - für die V5-Hälfte der Paartests: `pair-on-chain.ok` existiert (Kriterien, Eintrag e5, auf der Chain);
  - für Satz A und B: `v2/BB-A.ok` bzw. `v2/BB-B.ok` enthält „within the limits“, **und** `e4-on-chain.ok` existiert.
- Jeder Übergang kommt per Telegram: welcher Lauf fertig ist, der Hash seines letzten Segments, und welcher Lauf
  gestartet wurde oder warum nicht.

**Was sie nie tut:**
- den Hauptlauf starten;
- einen Lauf anhalten;
- zwei Läufe gleichzeitig auf der A100 starten;
- etwas als root tun.

**Der Wächter** meldet:
- wenn die Kette selbst nicht mehr prüft;
- MERCURIUS auf CPU 1: angehalten, kein Fortschritt, Fehler im Protokoll, fertig;
- zweimal am Tag einen Bericht (07 und 19 Uhr UTC).

## 0. Übertragen und prüfen

Die Dateien kommen auf dem gewohnten Weg nach `~/runs/` von p9sim:

| Datei | SHA-256 |
|---|---|
| `p9chain-<commit>.tar.gz` (dieses Paket) | siehe `p9chain-<commit>.tar.gz.sha256` |
| `p9long-v5-ac47329.tar.gz` | `fe5d2aa1e081a7946865fe61a9ebced829e23e2fc4b7867769115d03e1d99d0d` |
| `p9bbsets-5b05cc3.tar.gz` | `6d7da4654bb1f19d4f044ed7ea83acad3e34bb6d3e5ff8ea462d686369573476` |

```sh
cd ~/runs && sha256sum p9chain-*.tar.gz p9long-v5-ac47329.tar.gz p9bbsets-5b05cc3.tar.gz
```
Erwartet: die Hashes der Tabelle.

```sh
mkdir -p ~/runs/chain && tar -xzf ~/runs/p9chain-*.tar.gz -C ~/runs/chain --strip-components=1
mkdir -p ~/runs/v5 ~/runs/sets
tar -xzf ~/runs/p9long-v5-ac47329.tar.gz -C ~/runs/v5
tar -xzf ~/runs/p9bbsets-5b05cc3.tar.gz -C ~/runs/sets
```
Die V5- und Satz-Pakete werden nur ausgepackt, nicht gestartet: Das macht später die Kette.

## 1. Einstellungen

```sh
cd ~/runs/chain && cp chain.env.example chain.env && nano chain.env
```
- Pfade prüfen: `PROD_DIR`, `V5_DIR`, `SETS_DIR`, `MERC_DIR` und `V2_DIR`. Die Vorgaben passen zu den Startanleitungen vom 04.11. Prozesse von p9gpu im V2-Paket sind auf der L40S erlaubt; jedes andere p9gpu außerhalb der A100 meldet die Kette und es blockiert einen Start.
- `GPU_UUID=` mit der UUID der A100 füllen (`nvidia-smi -L`, die Zeile „NVIDIA A100-PCIE-40GB“). Mit UUID wählt die Kette die Karte
  eindeutig; ohne UUID nimmt sie die erste Karte mit „A100“ im Namen.
- `E4_OK` bleibt `~/runs/chain/e4-on-chain.ok`.

## 2. Telegram

Die Datei enthält das Bot-Token. Sie muss Modus 600 haben und p9sim gehören, sonst sendet die Kette nicht. Das Token
nicht auf der Befehlszeile eingeben (es landet sonst in der Shell-Historie), sondern im Editor:
```sh
mkdir -p ~/.config/p9chain && chmod 700 ~/.config/p9chain
install -m 600 /dev/null ~/.config/p9chain/telegram.env
nano ~/.config/p9chain/telegram.env
```
Inhalt, zwei Zeilen:
```
TELEGRAM_TOKEN=<Bot-Token>
TELEGRAM_CHAT_ID=<Chat-ID>
```
Die Kette liest die Datei, statt sie auszuführen. Das Token gibt sie curl über die Standardeingabe; es steht nie in
der Prozessliste, in einem Protokoll oder in einer Meldung.

```sh
sh ~/runs/chain/chain-a100.sh test-telegram
```
Erwartet: `sent`, und die Meldung „[A100-Kette] Test von p9sim, …“ kommt an. Bei `not sent`: `tail ~/runs/chain/chain.log`
nennt den Grund, zum Beispiel Modus, Format oder HTTP-Code, ohne das Token.

## 3. Xid im Kernel-Log

p9sim darf das Kernel-Log normalerweise nicht lesen. Einmalig als root:
```sh
usermod -aG systemd-journal p9sim
```
Die neue Gruppe gilt erst für eine neue Anmeldung. **Laufende Prozesse und tmux-Sitzungen von p9sim nicht anfassen**:
Hauptlauf und MERCURIUS laufen weiter und brauchen die Gruppe nicht. Ein tmux-Neustart würde sie beenden.

Neu anmelden, als root:
```sh
sudo -iu p9sim
```
Dann als p9sim:
```sh
id
```
Erwartet: In der Liste `groups=…` steht `systemd-journal`.

Ein schon laufender tmux-Server von p9sim behält die alten Gruppen. Die Kette läuft deshalb in einer eigenen
tmux-Instanz (`tmux -L p9chain`, Schritt 6), die aus dieser neuen Anmeldung startet.

```sh
journalctl -k -n 3
```
Erwartet: drei Kernel-Zeilen, nicht „insufficient permissions“. Ohne diese Gruppe läuft die Kette trotzdem, prüft
aber keine Xid und meldet das einmal.

## 4. Test mit Attrappen (auf dem Server, ohne Wirkung)

```sh
cd ~/runs/chain && sh test/test-chain.sh
```
Der Test nutzt ein gefälschtes `nvidia-smi`, `journalctl` und `curl` und eigene Mini-Pakete in einem temporären
Verzeichnis. Er fasst weder die A100, noch die echten Läufe, noch Telegram an.

Erwartet: 55 Zeilen `ok …`, am Ende `== 55 checks, 0 failed`. Das gilt auch neben den laufenden Läufen: Die
Prozesssuche des Tests sieht nur p9gpu-Prozesse in seinem eigenen temporären Verzeichnis, nicht den echten Hauptlauf.

## 5. Trockenlauf mit den echten Läufen

```sh
sh ~/runs/chain/chain-a100.sh status
```
Erwartet, solange der Hauptlauf läuft:
- `A100: ok; NVIDIA A100-PCIE-40GB, … °C, … MHz, … W, Gründe 0x0000000000000000` (oder `…04`), `ECC unkorrigiert 0`;
- `Hauptlauf: running; Hauptlauf: N von 40 Segmenten; zuletzt segNNN …, Hash …`;
- `V5 der Seeds 110–112: notstarted`, `Satz A: notstarted`, `Satz B: notstarted`;
- `nächster Start: V5 der Seeds 110–112 wartet: ein Lauf eines Pakets der Kette ist noch aktiv`.

```sh
sh ~/runs/chain/chain-a100.sh dry-run
```
Der Testmodus startet nichts und sendet nichts; Meldungen gehen nach `outbox.txt`. Er hat einen eigenen Zustand in
`state-dry/`. Während der Hauptlauf läuft, entsteht keine Meldung, und am Ende steht der Zustand wie bei `status`.

## 6. Einschalten: eine der beiden Arten

**A) tmux** (einfach; endet bei einem Neustart des Servers). Eine eigene tmux-Instanz mit dem Socket `p9chain`,
gestartet aus der neuen Anmeldung von Schritt 3. Die bestehenden tmux-Sitzungen bleiben unberührt.
```sh
id | grep -q systemd-journal && echo "Gruppe ok"
tmux -L p9chain new -d -s chain 'sh ~/runs/chain/chain-a100.sh loop'
tmux -L p9chain new -d -s watch 'sh ~/runs/chain/run-watch.sh loop'
tmux -L p9chain ls
```
Erwartet:
- `Gruppe ok`;
- zwei Sitzungen, `chain:` und `watch:`.

Hineinschauen mit `tmux -L p9chain attach -t chain`; verlassen mit Strg-b d. Nur `-L p9chain` gehört der Kette;
Befehle wie `tmux kill-server` ohne `-L p9chain` würden die anderen Sitzungen treffen und sind hier nie nötig.

**B) systemd --user** (läuft auch nach einem Neustart weiter):
1. Einmalig als root:
   ```sh
   loginctl enable-linger p9sim
   ```
2. Als p9sim:
   ```sh
   mkdir -p ~/.config/systemd/user && cp ~/runs/chain/systemd/* ~/.config/systemd/user/
   systemctl --user daemon-reload && systemctl --user enable --now p9-chain.timer p9-watch.timer
   systemctl --user list-timers
   ```
   Erwartet: `p9-chain.timer` und `p9-watch.timer` mit dem nächsten Lauf in höchstens 5 min.
3. Wer mit `sudo -iu p9sim` arbeitet, braucht für `systemctl --user` vorher
   `export XDG_RUNTIME_DIR=/run/user/$(id -u)`.
4. Der systemd-Benutzerdienst von p9sim behält die Gruppen, mit denen er gestartet wurde. Lief er schon vor Schritt 3,
   bleibt die Xid-Prüfung aus, bis er neu startet, etwa beim nächsten Neustart des Servers; die Kette meldet das
   einmal. Ihn nicht von Hand neu starten, solange Läufe laufen. Wer die Xid-Prüfung sofort will, nimmt Variante A.

Nicht beides zugleich. Eine Sperre verhindert doppelte Prüfungen, aber zwei Taktgeber sind unnötig.

Kontrolle nach 5–10 min:
```sh
sh ~/runs/chain/chain-a100.sh status
```
Die Zeile `letzte Prüfung: vor 0…5 min` sollte erscheinen.

## 7. Ausschalten

| Was | tmux | systemd |
|---|---|---|
| Kette anhalten (die Läufe laufen weiter) | `sh ~/runs/chain/chain-a100.sh stop` | `systemctl --user disable --now p9-chain.timer` |
| Wächter anhalten | `sh ~/runs/chain/run-watch.sh stop` | `systemctl --user disable --now p9-watch.timer` |
| nur keine Starts mehr, Überwachung weiter | `sh ~/runs/chain/chain-a100.sh pause` (zurück: `resume`) | dasselbe |

Einen Lauf selbst hält nur sein `stop.sh` an:
- Hauptlauf: `sh ~/runs/prod/p9prod-9a084ed/stop.sh`;
- V5: `sh ~/runs/v5/p9long-v5-ac47329/stop.sh`;
- Sätze: `sh ~/runs/sets/p9bbsets-5b05cc3/stop.sh`.

## 8. Im Betrieb

**Eintrag 4:** Sobald er auf der Chain ist:
```sh
: > ~/runs/chain/e4-on-chain.ok
```
Ohne diese Datei startet Satz A nicht. Satz A und B starten außerdem nur mit dem V2-Urteil.

**V2-Urteil:** Die Kurzläufe `p9bbv2` laufen auf der L40S. `tools/v2_encounter_check.py --ok-dir` schreibt
`BB-A.ok` und `BB-B.ok`. Beide gehören nach `~/runs/sets/p9bbsets-5b05cc3/v2/`. Gezählt wird nur genau die Zeile
`within the limits`.

**Nach einem gewollten Anhalten:** Ein Beispiel ist der Wiederaufnahmetest von V5 oder MERCURIUS. Das Protokoll
enthält danach `stopped (signal)`, und die Kette blockiert den nächsten Start, bis du die Zeilen bestätigst:
```sh
sh ~/runs/chain/chain-a100.sh ack v5      # bzw. ack prod, ack sets, ack merc
```
Bestätigt sind nur die Zeilen bis jetzt; spätere Fehlerzeilen blockieren wieder. Während ein Lauf angehalten ist,
meldet die Kette „läuft nicht und ist nicht fertig“. Nach `start.sh` des Laufs gilt er wieder als laufend.

**Halt-Signal der A100** (Gründe 0x8/0x20/0x40/0x80, mehr als 85 °C, ECC-Fehler, Xid):
- Die Kette meldet einen Alarm und setzt eine Sperre. Bis zur Aufhebung startet sie nichts.
- Den laufenden Lauf hält sie nicht an. Prüfen und, wie in der Startanleitung, ggf. `stop.sh` des Laufs.
- Nach der Prüfung:
  ```sh
  sh ~/runs/chain/chain-a100.sh ack hold
  ```

**Neustart des Servers:** Die Läufe sind danach aus. Die Kette meldet „läuft nicht und ist nicht fertig“ und startet
nichts.
- Hauptlauf neu starten mit `start-a100.sh` wie in der Startanleitung.
- Andere Läufe mit ihrem `start.sh`.
- Die Kette erkennt den Lauf dann wieder.

**Meldungen** (alle beginnen mit „[A100-Kette]“):

| Meldung | Bedeutung |
|---|---|
| „X fertig: … Letztes Segment: segNNN …, Hash …. Y gestartet: started (pid …); start: GPU …“ | Übergang |
| „X fertig: …. Y wird nicht gestartet: <Grund>“, später „Y wartet: <Grund>“ | wartet; neuer Grund sofort, gleicher alle 6 h |
| „ALARM: Halt-Signal der A100: …“ | Sperre gesetzt, nichts startet |
| „ALARM: X: seit N min keine neue Ausgabe“ | kein Fortschritt (Hauptlauf/Sätze: 90 min, MERCURIUS: 120 min) |
| „ALARM: Protokoll von X: …“ | fail/stop/error im Protokoll |
| „ALARM: X läuft nicht und ist nicht fertig“ | angehalten oder abgestürzt |
| „ALARM: chain-a100.sh hat seit N min nicht geprüft“ | Kette steht (tmux/Timer) |
| „erledigt: …“ | ein Alarm ist vorbei |
| „Bericht …“ | 07 und 19 Uhr UTC: Stand aller Läufe, A100, MERCURIUS, Platte |

Offene Alarme wiederholen sich alle 6 h (`REPEAT_H`). Nicht zugestellte Meldungen werden mit der nächsten
nachgereicht.

**Protokoll der Kette:** `~/runs/chain/chain.log`. Ausgaben der Starts: `~/runs/chain/state/start.out`.

## 9. Erweiterung vom 06.11.: CPU-2-Messung und Paartests

Nach V5 110–112 kommen zwei neue Stufen, beide auf der A100 und beide von der Kette gestartet:

| Stufe | Paket (Verzeichnis in `chain.env`) | startet nur, wenn |
|---|---|---|
| CPU-2-Messung, etwa 20 min | `p9cpu2-c0ce0d9` (`CPU2_DIR`) | V5 110–112 fertig, A100 frei; keine Freigabedatei nötig (nur Leistungsmessung) |
| V5-Hälfte der Paartests, etwa 29 h | `p9pair-v5-8862e1b` (`PAIR_V5_DIR`) | die Messung fertig und `~/runs/chain/pair-on-chain.ok` vorhanden |

Danach wie bisher Satz A und Satz B, jeweils nur mit ihrer Freigabe in `v2/BB-<Satz>.ok` und mit `e4-on-chain.ok`.

**Neue Dateien, die du anlegst:**
- `: > ~/runs/chain/pair-on-chain.ok`, sobald der Eintrag der Paartest-Kriterien (e5) auf der Chain ist.
- `: > ~/runs/chain/skip-setA` (bzw. `skip-setB`), wenn ein Satz endgültig nicht gerechnet wird, etwa nach einem nicht
  bestandenen Paartest. Die Kette meldet das einmal und geht zum nächsten Satz weiter. Löschen macht es rückgängig,
  solange der Satz nicht begonnen hat.

**Die MERCURIUS-Hälfte startet nicht die Kette**, sondern du, auf CPU 1:
```sh
THREADS=8 sh ~/runs/pair/p9pair-merc-8862e1b/start.sh
```
Das geht, sobald e5 auf der Chain ist. Wenn MERCURIUS 110–112 fertig ist:
```sh
sh ~/runs/pair/p9pair-merc-8862e1b/stop.sh && THREADS=16 sh ~/runs/pair/p9pair-merc-8862e1b/start.sh
```
Kerne von CPU 2 nur, wenn `RESULT/VERDICT.txt` der Messung sie erlaubt.

**Ergebnis der Messung:** Die Kette nennt die Zeile `VERDICT: …` in ihrer Übergangsmeldung. Die Einzelwerte stehen in
`~/runs/cpu2/p9cpu2-c0ce0d9/RESULT/`.

**Bestätigen nach gewolltem Anhalten:** `ack cpu2` und `ack pair` kommen zu `ack prod|v5|sets|merc` hinzu.

## 10. Tausch im laufenden Betrieb (von p9chain-0ecadee auf dieses Paket)

Am besten während V5 110–112 läuft (bis etwa 10./11.11.). Dann steht kein Übergang an. Die Läufe selbst werden nicht
berührt; die Kette prüft für ein paar Minuten nicht.

**1. Stand festhalten:**
```sh
sh ~/runs/chain/chain-a100.sh status
```
Erwartet: `V5 der Seeds 110–112: running`, kein offener Alarm außer bekannten.

**2. Kette und Wächter anhalten**, nur ihre Schleifen:
- tmux:
  ```sh
  sh ~/runs/chain/chain-a100.sh stop && sh ~/runs/chain/run-watch.sh stop
  ```
  Erwartet: `loop stopped (the runs go on)` und `watcher stopped`. Die Sitzungen von `tmux -L p9chain` enden damit von
  selbst; die anderen tmux-Sitzungen nicht anfassen.
- systemd:
  ```sh
  systemctl --user stop p9-chain.timer p9-watch.timer
  ```

**3. Sichern:**
```sh
cp -a ~/runs/chain ~/runs/chain-0ecadee
```
Darin bleiben `chain.env`, `state/`, `e4-on-chain.ok` und `chain.log` erhalten.

**4. Pakete prüfen und auspacken:**
```sh
cd ~/runs && sha256sum p9chain-*.tar.gz p9cpu2-c0ce0d9.tar.gz p9pair-v5-8862e1b.tar.gz p9pair-merc-8862e1b.tar.gz
```
Erwartet: die Hashes aus der Nachricht bzw. den `.sha256`-Dateien.
```sh
tar -xzf ~/runs/p9chain-<commit>.tar.gz -C ~/runs/chain --strip-components=1
mkdir -p ~/runs/cpu2 ~/runs/pair
tar -xzf ~/runs/p9cpu2-c0ce0d9.tar.gz -C ~/runs/cpu2
tar -xzf ~/runs/p9pair-v5-8862e1b.tar.gz -C ~/runs/pair
tar -xzf ~/runs/p9pair-merc-8862e1b.tar.gz -C ~/runs/pair
```
Das Kettenpaket überschreibt nur Skripte, Anleitung, Test, systemd-Units und `chain.env.example`. `chain.env` und der
Zustand bleiben.

**5. `chain.env` ergänzen** (die drei Zeilen aus `chain.env.example`):
```sh
grep -E '^(CPU2_DIR|PAIR_V5_DIR|PAIR_OK)=' ~/runs/chain/chain.env.example >> ~/runs/chain/chain.env
```

**6. Test und Trockenlauf:**
```sh
cd ~/runs/chain && sh test/test-chain.sh | tail -n 1
```
Erwartet: `== 55 checks, 0 failed`.
```sh
sh ~/runs/chain/chain-a100.sh status
```
Erwartet:
- `V5 der Seeds 110–112: running`;
- `CPU-2-Messung: notstarted`, `V5-Hälfte der Paartests: notstarted`, `Satz A: notstarted`, `Satz B: notstarted`;
- `nächster Start: CPU-2-Messung wartet: ein Lauf eines Pakets der Kette ist noch aktiv`.

```sh
sh ~/runs/chain/chain-a100.sh dry-run
```
Erwartet: keine neue Meldung.

**7. Wieder einschalten**, wie vorher:
- tmux:
  ```sh
  tmux -L p9chain new -d -s chain 'sh ~/runs/chain/chain-a100.sh loop'
  tmux -L p9chain new -d -s watch 'sh ~/runs/chain/run-watch.sh loop'
  ```
- systemd:
  ```sh
  systemctl --user start p9-chain.timer p9-watch.timer
  ```
  Ein `daemon-reload` ist nicht nötig; die Units sind unverändert.

**Zurück zur alten Fassung,** falls nötig: Schleifen anhalten, dann
```sh
rm -rf ~/runs/chain && mv ~/runs/chain-0ecadee ~/runs/chain
```
und wieder einschalten.
