# Independent code reading by an AI model (2026-11-21)

**What this is:**
- A reading of the code of this repository by an AI model in its own session, separate from the session that wrote
  the code.
- Only reading: from a fresh clone of `feat/pilot` at 5455b3b, without the run data and without running the
  integrators; only a few existing tests were run.
- **It is not a peer review** by scientists of the field.
- The text below is reproduced **unchanged**, in its original German, from the file `GUTACHTEN.md`
  (SHA-256 `2a48d93a9ca8466cbf43f1afc6ab3877de489273e422216e1035d1c5d3c6cd64`). Its word "Gutachten" is the
  reviewer's; it is not an expert opinion in a formal sense.

**What was done with it:** see the end of this file.

---

# Gutachten: Code-Durchsicht p9gpu, Startwerte und Auswertung

Datum: 2026-11-21. Gegenstand: das Repository im Ordner `p9-review`, Zweig `feat/pilot`, Commit `5455b3b`.
Nur gelesen; im Repository wurde nichts geändert (`git status` danach leer).

## 0. Kurzfassung

- **In der Auswertung (`tools/prod_eval.py`) habe ich keinen Rechenfehler gefunden, der das Urteil „Outcome 4“ erzeugt.**
  Geometrie, Bezugsebene, Auswahl, Fenster, M1–M5 und die Urteilslogik tun, was die Kriterien festlegen. Die
  gespeicherten `result.json` stimmen mit den Berichten überein.
- **Zwei Punkte können veröffentlichte Zahlen ändern:**
  1. Die Definition von ϖ (Ω + ω) ist für stark geneigte und rückläufige Bahnen keine Richtung des Perihels. In Satz A
     sind 17 % der gewerteten Teilchen rückläufig. Ob das Urteil davon abhängt, ist nicht gerechnet (A1).
  2. Die innere Entfernung (r < 4,5 au) wird nur alle 1000 Schritte geprüft. Das ist in den Berichten bekannt, steht
     aber nicht in den Kriterien (A2).
- **Der ausgecheckte Zweig enthält nicht den Code der Läufe.** Rechenkern und Startwerte der Läufe liegen auf anderen
  Zweigen (`9a084ed`, `c531f3b`/`4d8ec5c`, `5b05cc3`). Die Unterschiede sind klein und wurden mitgeprüft (C1).
- **Nicht prüfen konnte ich** alles, was Rechnen verlangt: REBOUND fehlt, numpy fehlt, die Laufdaten liegen nicht im
  Repository. Die numerische Genauigkeit des Rechenkerns ist deshalb nur am Quelltext geprüft (Abschnitt 5).

## 1. Was geprüft wurde und womit

- **Gelesen, Zeile für Zeile:** `tools/prod_eval.py`, `tools/analyze.py`, `tools/sets_decompose.py`,
  `tools/sets_decompose2.py`, `tools/sets_subset_spread.py`, `tools/make_ic.py`, `tools/p9job.py`, `src/p9sim.c`,
  `src/p9state.c`, `src/p9encounter.c`, `gpu/whdh.h`, `gpu/p9gpu.c`, `gpu/kernel.cu`, `gpu/p9gpu_api.h`,
  `gpu/p9gpu_real.h`, `Makefile`, `tests/test_prod_eval.py`.
- **Aus der Git-Historie desselben Repositorys:** die Unterschiede von `HEAD` zu `9a084ed` (Produktionspaket), zu
  `4d8ec5c` (`make_ic.py`, `p9job.py` der Sätze A und B), zu `5b05cc3` (Paket der Sätze) und zu `0b8971f`
  (Entfernung in jedem Schritt, Lauf BB-A-rin1); dazu `prod/run-production.sh` und `tools/make_prod_package.sh` bei
  `9a084ed`.
- **Dokumente:** `docs/bb2021-comparison-criteria.md`, `docs/production-criteria.md`, `docs/sets-outcome-20261117.md`,
  `docs/bb2021-article-vs-package.md`, `docs/sets-evaluation-procedure.md`, `docs/gpu-integrator.md`, und die
  gespeicherten Ergebnisdateien unter `docs/sets-result-*`, `docs/production-result-20261110`,
  `docs/sets-decomposition-*`.
- **Ausgeführt** (Abschnitt 6): drei vorhandene C-Tests und zwei vorhandene Python-Tests; sonst nur Lesebefehle.

Zeilennummern beziehen sich auf `HEAD` (`5455b3b`), wenn nichts anderes dasteht.

## 2. Befunde, Klasse 1: kann ein veröffentlichtes Ergebnis ändern

### A1. ϖ = Ω + ω auch für stark geneigte und rückläufige Bahnen; M1 und M2 werden darüber gebildet

- **Fundstelle:** `tools/prod_eval.py:122–127` (Ω, ω, `varpi = (Omega + omega) % 360`), verwendet in
  `frame_elements` (`:158–161`) für alle Teilchen ohne Neigungsgrenze; Auswahl `select` (`:179–181`) kennt nur a und q.
- **Was dort geschieht:** Δϖ wird für jedes Teilchen aus Ω + ω gebildet, auch bei i > 90°.
- **Warum fraglich:**
  - Ω + ω ist nur für kleine Neigungen die Länge des Perihels. Die Abweichung von der Richtung des projizierten
    Exzentrizitätsvektors beträgt für rechtläufige Bahnen höchstens arcsin(tan²(i/2)): 1,1° bei 16°, 4,1° bei 30°,
    12,6° bei 50°, 90° bei 90°. Für rückläufige Bahnen liegt die projizierte Richtung bei Ω − ω; Ω + ω weicht davon
    um bis zu 180° ab.
  - Der Kommentar in `prod_eval.py:123–124` nennt nur „about 1 deg at 16 deg inclination“. Das gilt für Planet Nine,
    nicht für die gewertete Population.
  - Die gewertete Population ist stark geneigt. Aus `docs/sets-decomposition-2-20261117/*/summary.json`
    (`c_q>42/all`, `inc_q_cut_only`): Satz A 17,1 % rückläufig, 36,8 % über 50°; Satz B 0,8 % und 22,3 %.
  - `tools/analyze.py:62–63` bildet ϖ anders (Richtung des projizierten Exzentrizitätsvektors). Die Kriterien
    (`docs/bb2021-comparison-criteria.md:145`) sagen „as in `tools/analyze.py`“; der Nachtrag 13 (`:383`) legt
    Ω + ω fest. Beide Festlegungen stammen von vor den Läufen, sie widersprechen sich aber für diese Population.
  - Die Kriterien und Berichte enthalten keine Regel für rückläufige Bahnen (Suche nach „retrograde“ in den beiden
    Kriteriendateien: kein Treffer).
- **Was das ändern kann:** die Zahlen M1, M2, M4 und die Werte „R beyond the wall“ für ganz S_BB. Ob M2 von Satz B
  (0,127 gegen die Grenze 0,20) oder das Urteil davon abhängt, ist nicht belegt.
- **Wie prüfen:** auf den vorhandenen Schnappschüssen M1 und M2 dreimal bilden: (a) wie jetzt, (b) mit der Definition
  von `analyze.py`, (c) mit Ω − ω für i > 90°. Zusätzlich M2 getrennt für i < 90° und i > 90° ausgeben. Die Tests
  (`tests/test_prod_eval.py:75`) ziehen nur i zwischen 5° und 25°; ein Testfall mit rückläufigen Bahnen fehlt.
- **Sicherheit:** dass der Code so rechnet und dass die Definitionen auseinanderlaufen: sicher. Größe der Wirkung auf
  M2: unbekannt. Welche Definition Brown & Batygin verwenden: nicht geprüft.

### A2. Die Entfernungsregeln greifen nur alle 1000 Schritte (500 Jahre); die Kriterien nennen keine Taktung

- **Fundstelle:** `gpu/p9gpu.c:78` (`CHECK_EVERY 1000`), `:360–368` (CPU-Pfad), `gpu/kernel.cu:177–185` (GPU-Pfad),
  `src/p9sim.c:65, 152–163` (p9sim, auch MERCURIUS).
- **Was dort geschieht:** Nur wenn die Schrittzahl durch 1000 teilbar ist, wird der Abstand zur Sonne am synchronen
  Zustand geprüft (r < R_IN oder r > 10 000 au). Dazwischen läuft ein Teilchen innerhalb von R_IN weiter.
- **Warum fraglich:**
  - Die Kriterien sagen nur „Removal at r < 4.5 au“ (`docs/production-criteria.md:31`,
    `docs/bb2021-comparison-criteria.md:119`), ohne Taktung.
  - Ein Teilchen auf nahezu parabolischer Bahn ist je Periheldurchgang höchstens etwa 2 Jahre innerhalb von 4,5 au
    (eigene Abschätzung aus der Parabelzeit, q zwischen 0 und 4,5 au). Die Regel erfasst einen Durchgang also mit
    weniger als 0,5 % Wahrscheinlichkeit. Solche Teilchen bleiben im Mittel einige hundert Umläufe im Lauf, sofern
    sie nicht vorher gestreut werden.
- **Stand in den Dokumenten:** Der Unterschied ist bekannt und beschrieben (`docs/bb2021-article-vs-package.md`, Zeile
  „Inner removal“; `docs/sets-outcome-20261117.md:114–119`). Der Lauf BB-A-rin1 (`0b8971f`, `P9_R_IN_EVERY=1`) prüft
  ihn; sein Ergebnis liegt hier nicht vor.
- **Wie prüfen:** das Ergebnis von BB-A-rin1 nach den eingetragenen Kriterien. Unabhängig davon: aus `removed.tsv` und
  den Schnappschüssen zählen, wie viele Teilchen von S_BB je einen Schnappschuss mit q < 4,5 au hatten (die Zerlegung
  gibt für „qmin>=4.5“ dieselbe Zahl wie für S_BB: keines, auf dem 10-Myr-Raster).
- **Sicherheit:** Taktung im Code: sicher. Wirkung auf M1–M5: offen.
- **Zum Code von `0b8971f` (gelesen):** Die Prüfung in jedem Schritt steht im `else`-Zweig der regulären Prüfung und
  nutzt denselben synchronen Zustand. Der Vorfilter (R_IN + 10 au am vorausgedrifteten Zustand) ändert keine
  Entscheidung, solange ein Teilchen in einem Viertel Jahr weniger als 10 au zurücklegt; bei 4,5 au sind es etwa 1 au.
  Ein Teilchen mit q knapp unter 4,5 au kann zwischen zwei Schritten durch die Kugel laufen (Aufenthalt unter 0,5 a
  für q über etwa 4,44 au, aus der Parabelzeit); die wirksame Grenze liegt also bis etwa 0,06 au tiefer.

## 3. Befunde, Klasse 2: kann ein Ergebnis in Randfällen ändern

### B1. Der Kepler-Löser hat eine feste Zahl von Iterationen und keine Konvergenzprüfung; seine Begründung deckt den Bereich innerhalb von R_IN nicht

- **Fundstelle:** `gpu/whdh.h:43–47` (Begründung: dt/P ≤ 1/24), `:97–107` (Startwert, drei Halley-Schritte).
- **Warum fraglich:** Zwischen zwei Entfernungsprüfungen (A2) kann ein Teilchen beliebig nahe an die Sonne kommen.
  Dort ist dt = 0,5 a nicht mehr klein gegen die lokale Umlaufzeit (bei 1 au: ein halber Umlauf je Schritt). Ob drei
  Iterationen dann reichen, prüft der Code nicht.
- **Was mildert:** Mit den Radien des Nachtrags 13 ist r_out von Jupiter 7,43 au, also größer als Jupiters Abstand
  von der Sonne (4,95–5,46 au). Ein Teilchen innerhalb von etwa 2 au um die Sonne liegt immer innerhalb von r_out und
  wird in Teilschritten gerechnet (`whdh.h:543–555, 590, 607–639`), in denen auch der Kepler-Drift um die Sonne mit
  dt/n läuft. Für etwa 2–4,5 au auf der Jupiter abgewandten Seite gilt das nicht.
- **Wie prüfen:** `tools/kepler_energy.py` (Planeten masselos) mit Testteilchen, deren Perihel bei 0,05 bis 4 au liegt,
  und der Energiefehler je Periheldurchgang; dazu in einem Lauf die Zahl der Teilchen mit r < 4,5 au je Schnappschuss.
- **Sicherheit:** Fehlen der Prüfung und Lücke der Begründung: sicher. Dass tatsächlich Fehler entstehen: nicht belegt.
  Betroffen wären nur Teilchen mit q < 4,5 au, die nicht zu S_BB gehören, solange sie dort sind.

### B2. Teilchen mit nicht endlichem Zustand werden nie entfernt und in der Auswertung stillschweigend übergangen

- **Fundstelle:** `gpu/p9gpu.c:362–363`, `gpu/kernel.cu:179–180` (`r2 > rout2 || r2 < rin2`: mit NaN beide falsch);
  `gpu/whdh.h:330` (NaN-Abstand ergibt in jedem Schritt die Höchstzahl an Teilschritten); `gpu/whdh.h:59` (für
  z = ±∞ endet die Schleife nicht).
- **In der Auswertung:** `tools/prod_eval.py:179–181` schließt NaN aus jeder Auswahl aus; `:240` zählt das Teilchen
  aber unter `n_tp` (Überlebende). `tools/sets_decompose.py:109` trägt NaN in das laufende Minimum von q ein.
- **Wie prüfen:** in den Schnappschüssen die Zeilen mit nicht endlichen Werten zählen; erwartet: null.
- **Sicherheit:** Verhalten bei NaN: sicher (am Code). Ob in den Läufen je ein NaN entstand: nicht geprüft.

### B3. `prod_eval.py`: ein Schnappschuss ohne Teilchen in S_BB geht mit R = 0 in M2 ein

- **Fundstelle:** `tools/prod_eval.py:167–172` (`circ_mean` gibt für leere Eingabe `(None, 0.0)` zurück), `:248`
  (`R_snap.append(r_t)`), `:271` (Mittel). `tools/sets_subset_spread.py:164, 168` behandelt denselben Fall mit NaN und
  `nanmean`, also anders.
- **Wirkung:** nur bei leeren Schnappschüssen; in den drei Läufen nicht der Fall (`n_SBB` in `timeseries.csv` ist
  fünfstellig).
- **Sicherheit:** sicher.

### B4. `prod_eval.py --outcome`: Rangfolge der Ausgänge 3 und 4, und Ausgang 3 nur über das gepoolte M1

- **Fundstelle:** `tools/prod_eval.py:331–337`.
- **Was dort geschieht:** „No cluster“ wird vor „wrong direction“ geprüft. Erfüllt ein Satz Bedingung 3 und der andere
  Bedingung 4, meldet das Programm 4; die Kriterien (Abschnitt 6) legen dafür keine Rangfolge fest. Für Ausgang 3
  zählt nur das gepoolte M1; das Urteil je Satz (`judge_bb`, `:308–310`) verlangt auch jede Teilmenge. Liegt nur eine
  Teilmenge außerhalb, lautet der Ausgang „2/other“.
- **Wirkung auf das veröffentlichte Ergebnis:** keine; M2 liegt in beiden Sätzen unter 0,20.
- **Sicherheit:** sicher.

### B5. `prod_eval.py`: exakt ebene Bahnen (i = 0 im Bezugssystem)

- **Fundstelle:** `tools/prod_eval.py:122, 125–127`.
- **Was dort geschieht:** Der Knotenvektor ist null; `arctan2(0, ∓0)` liefert je nach Vorzeichen der Null 0° oder 180°,
  ω wird 0. ϖ enthält dann die Richtung des Perihels nicht mehr.
- **Wirkung:** nur für Bahnen mit h_x = h_y = 0 exakt; in den Läufen praktisch ausgeschlossen, in synthetischen
  Tests möglich.
- **Sicherheit:** sicher.

### B6. Die Zeit eines Schnappschusses wird errechnet, nicht aus der Datei gelesen

- **Fundstelle:** `tools/prod_eval.py:95` (Zeit aus Segment- und Schnappschussnummer), `:233–235` (das von `dump`
  gelesene t geht nur in eine Fehlermeldung, `:139`).
- **Warum fraglich:** Enthielte ein `output.sa` mehr oder weniger Schnappschüsse als `SNAPSHOTS_PER_SEGMENT`, würden
  Zeiten und Fenster falsch zugeordnet, ohne Meldung.
- **Was dagegen steht:** `prod/run-production.sh` (bei `9a084ed`) löscht `output.sa` vor jedem Segment, p9gpu schreibt
  genau einen Schnappschuss je Ausgabezeit (`gpu/p9gpu.c:563–613`), und `tools/check_segments.py` prüft t des letzten.
- **Wie prüfen:** in `snapshots()` das gelesene t mit dem errechneten vergleichen (ein `assert`).
- **Sicherheit:** sicher; für die vorliegenden Läufe sehe ich keinen Hinweis auf eine Fehlzuordnung (400 Schnappschüsse,
  301 im Fenster, letzter bei 4 Gyr).

### B7. Synchroner Zustand von Teilchen, die gerade in Teilschritten laufen

- **Fundstelle:** `gpu/whdh.h:649–652` (`p9_synchronous`: reiner Kepler-Drift um −dt/2), verwendet für Ausgaben
  (`gpu/p9gpu.c:608`) und die Entfernungsprüfung (`:361`, `gpu/kernel.cu:178`).
- **Was dort geschieht:** Im Verfahren smooth enthält der gespeicherte Zustand bereits den nahen Kraftanteil des ganzen
  Intervalls bis zum nächsten Kick (`whdh.h:607–639`). Der Rückdrift nimmt nur den Kepler-Anteil zurück. Der
  ausgegebene Zustand eines Teilchens innerhalb von r_out eines Planeten ist daher nicht genau der Zustand zur
  Ausgabezeit.
- **Wirkung:** nur auf Ausgabe und Entfernungsprüfung, nicht auf die Integration (sie läuft vom ungeänderten Zustand
  weiter; auch über Segmentgrenzen, da Hin- und Rückdrift sich bis auf Rundung aufheben). Teilchen von S_BB
  (q > 42 au) können nur bei Planet Nine innerhalb von r_out sein.
- **Sicherheit:** sicher; Größe nicht gerechnet, nach der Bauart klein.

### B8. Zerlegung: „R jenseits der Wand“ ist ein ungewichtetes Mittel über 10-au-Klassen aus abhängigen Stichproben

- **Fundstelle:** `tools/sets_decompose.py:128–141`, `tools/sets_decompose2.py:68–82`.
- **Was dort geschieht:** R wird je Klasse aus allen Teilchen-Schnappschüssen des Fensters gebildet (ab 10 Stück) und
  dann über die Klassen gemittelt, jede Klasse mit gleichem Gewicht. Dasselbe Teilchen zählt bis zu 301-mal.
- **Warum fraglich:** R ist für wenige unabhängige Richtungen nach oben verzerrt (bei N gleichverteilten Richtungen
  etwa 0,89/√N). Die Dateien geben die Zahl der Teilchen-Schnappschüsse je Klasse an, nicht die Zahl verschiedener
  Teilchen. In Satz A, Auswahl `q42-100_i<30`, hat die Klasse 665 au 4 131 Teilchen-Schnappschüsse, also im Mittel 14
  je Schnappschuss.
- **Betroffen:** die erkundenden Werte 0,63 / 0,50 / 0,55 / 0,48 / 0,64 / 0,56 in
  `docs/sets-outcome-20261117.md:76, 82–83`; nicht M1–M5.
- **Wie prüfen:** je Klasse die Zahl verschiedener Teilchen ausgeben; Bootstrap über Teilchen (nicht über
  Teilchen-Schnappschüsse); zusätzlich das mit n gewichtete Mittel.
- **Sicherheit:** Rechenweg sicher; Größe der Verzerrung nicht bestimmt. Die Klassen von 295 bis 395 au (je rund
  20 000 Teilchen-Schnappschüsse, R 0,58–0,69) sind davon kaum berührt.

### B9. `sets_decompose.py`: Division durch null, wenn der erste Fensterschnappschuss jenseits der Wand leer ist

- **Fundstelle:** `tools/sets_decompose.py:216–217` (`base = base or n`, dann `n / base`).
- **Wirkung:** Abbruch statt falscher Zahl; in den Läufen nicht eingetreten.
- **Sicherheit:** sicher.

## 4. Befunde, Klasse 3: Klarheit, Wartung, Abgleich von Dokumenten und Code

### C1. Der ausgecheckte Stand ist nicht der Code der Läufe [Abgleich]

- **Rechenkern:** `gpu/p9gpu.c:77` und `src/p9sim.c:64` setzen `R_IN 5.0` fest; der Kommentar `gpu/p9gpu.c:58–59` und
  `docs/gpu-integrator.md:84` sagen „within 5 au“. Die Kriterien sagen 4,5 au. Die Umgebungsvariable `P9_R_IN` gibt es
  erst ab `9a084ed` (dort `gpu/p9gpu.c`, `src/p9sim.c`, `tools/p9job.py --r-in`); dieser Commit liegt nicht auf
  `feat/pilot`.
- **Startwerte:** `tools/make_ic.py:67–68` kennt an `HEAD` nur a 150–550 au, i 0–10° und das Planet Nine des
  Posteriors in der Ekliptik. Die Kriterien verlangen `--a-range 150 500 --q-range 30 50 --inc-range 0 25`
  (`docs/bb2021-comparison-criteria.md:118`) und `--p9 … --p9-plane invariable` (`:358`). Diese Optionen gibt es ab
  `9a084ed` (Bereiche) und `c531f3b`/`4d8ec5c` (Planet Nine, Marke `make-ic-v1`), beide nicht auf `feat/pilot`.
  `tests/test_make_ic.py` (`:359`) fehlt an `HEAD`.
- **Jobs:** `tools/p9job.py:303` schreibt an `HEAD` `"r_in_au": 5`; `:163` kennt für Planet Nine nur den festen Radius
  von 2,6 Erdradien (die Skalierung mit der Masse erst ab `4d8ec5c`).
- **Was gleich ist:** `gpu/whdh.h`, `gpu/kernel.cu`, `gpu/whdh_t.h`, `gpu/cpu_t.cpp` sind zwischen `HEAD` und `9a084ed`
  identisch; `gpu/` und `src/` sind zwischen `9a084ed` und `5b05cc3` identisch. `tools/prod_eval.py` ist seit der Marke
  `prod-eval-v1` unverändert und hat die in `docs/sets-result-A-20261117/environment.txt` genannte Prüfsumme
  (`1ebb2d45…`).
- **Folge:** Wer das README befolgt (`tools/make_ic.py`, `tools/p9job.py make`), erzeugt an `HEAD` andere Startwerte und
  eine andere Entfernungsgrenze als die Läufe. `docs/publication-commits.md` führt die Commits auf, sagt aber nicht,
  dass `HEAD` selbst die Läufe nicht nachbilden kann.
- **Sicherheit:** sicher.

### C2. Kriterien verweisen für die Elemente auf `analyze.py`, das Werkzeug rechnet ϖ anders [Abgleich]

- `docs/bb2021-comparison-criteria.md:145` gegen `tools/prod_eval.py:123–127` und `tools/analyze.py:62–63`; siehe A1.
- Der Kommentar `tools/analyze.py:62` nennt die projizierte Richtung „Omega + omega, for prograde orbits“; das gilt
  nur näherungsweise und nur für kleine Neigungen.

### C3. M4 ist bei schwachem Plateau kein eigenständiges Maß

- **Fundstelle:** `tools/prod_eval.py:192–202`; Werte in `docs/sets-result-A-20261117/result.json` (`M4_bins`).
- **Was dort geschieht:** Die Wand ist die erste Klasse, ab der vier Klassen R ≥ R_plat/2 haben. In Satz A ist
  R_plat = 0,087 (Median der Klassen 405–695 au), die Schwelle also 0,043. Die Klassen 165–195 au haben 0,050 bis
  0,076 und liegen damit darüber. Das größte R (0,27) steht bei 285–295 au, außerhalb des Plateaubereichs der
  Kriterien.
- **Folge für den Text:** `docs/sets-outcome-20261117.md:58` zählt für Satz A „three of its four judged measures“
  außerhalb. M4 = 165 au folgt hier aus dem niedrigen Plateau und ist keine von M2 unabhängige Aussage.
- **Sicherheit:** sicher (aus den gespeicherten Klassen nachgerechnet). Der Code setzt die Definition der Kriterien
  richtig um.

### C4. „401 Schnappschüsse von 0 bis 4,0 Gyr“ [Abgleich]

- `docs/bb2021-comparison-criteria.md:123`. Die Programme schreiben keinen Schnappschuss bei t = 0
  (`gpu/p9gpu.c:563`: k ab 1); es sind 400. Das Fenster (301) ist davon nicht berührt.

### C5. „Jenseits der Wand“ ist in der Zerlegung zweifach abgegrenzt

- `tools/sets_decompose.py:126, 140` (Klassen mit Untergrenze ≥ Wand: ab 260 au bei Wand 256) gegen `:170`
  (a ≥ 256); ebenso `tools/sets_decompose2.py:74` gegen `:76`. In `summary.json` von Satz A stehen deshalb 3 513 343
  und 3 553 817 Teilchen-Schnappschüsse nebeneinander.

### C6. Tests der Auswertung decken den Lesepfad der Läufe und geneigte Bahnen nicht ab

- `tests/test_prod_eval.py:51–89` erzeugt nur `snap-*.npz` (nicht den Pfad über `p9sim dump` und `params.env`,
  `tools/prod_eval.py:58–70, 85–96`) und nur Neigungen von 5° bis 25°.

### C7. Zähler der Entfernungen

- `gpu/p9gpu.c:630–633`: `removed_inner` zählt nur die Regel des Modells j2, nicht r < R_IN; innere und äußere
  Entfernung sind bei `9a084ed` und `5b05cc3` nicht getrennt ausgewiesen (erst ab `0b8971f`). In
  `docs/bb2021-article-vs-package.md` richtig beschrieben.

## 5. Geprüft und für richtig befunden

**Auswertung (`tools/prod_eval.py`):**
- Ebene aus dem Drehimpuls (`plane_of`), Drehmatrix Rz(N)·Rx(I) und ihre Anwendung auf Zeilenvektoren
  (`rot_from_plane`, `:152`): Koordinaten im System der Jupiterbahn, x zum aufsteigenden Knoten.
- Dog-leg-Längen: Addition von N zu Ω und ϖ (`:153, 160`); in Δϖ und ΔΩ hebt sich N heraus.
- Jupiters Ebene aus seiner heliozentrischen Bahn je Schnappschuss (`:150`).
- Formeln für a, e, i, Ω, ω (`:112–128`); q = a(1 − e), auch für hyperbolische Bahnen positiv; diese fallen über
  a > 150 heraus.
- Baryzentrum und μ = G·M aller massiven Körper; heliozentrische Variante mit μ = G·m_Sonne (`:141–148`).
- Auswahl S_BB mit strengen Ungleichungen; Fenster 1–4 Gyr einschließlich beider Enden: 301 Schnappschüsse.
- M1 (gepooltes Kreismittel), M2 (Mittel der R je Schnappschuss), M3 (Azimut des mit sin i gewichteten Mittels), M4
  (Klassen, Plateau, Schwelle, vier Klassen in Folge, Klassen unter 10 Teilchen zählen als fehlend), M5 (zirkulare
  Glättung, Halbwertsbreite über 0°/360° hinweg).
- Teilmengen nach Index (Block 16 000), Streuung als größter Winkelabstand, Reihenfolge der Urteile, Toleranzen wie in
  Abschnitt 5 der Kriterien.
- Zuordnung der Teilchen: Kennung 6 + i im Startfile (`make_ic.py:186`), Name `tp<Kennung − N_active>` in
  `p9sim dump` (`src/p9sim.c:382`), Index daraus (`prod_eval.py:157`).
- Zuordnung der Zeiten zu den Segmenten, verglichen mit `prod/run-production.sh` bei `9a084ed`.

**Gespeicherte Ergebnisse gegen Berichte:**
- `docs/sets-result-A/B-20261117/result.json` gegen `docs/sets-outcome-20261117.md`: M1 127,3° / 166,7°, M2 0,050 /
  0,127, M3 3,2° / 18,0°, M4 165 au, Streuung 6,5° / 0,4°, Urteile und Ausgang 4 stimmen.
- Von Hand aus `M4_bins` nachgerechnet: Mittel 150–230 au Satz A 0,0735, 150–190 au Satz B 0,0746, 270–700 au Satz A
  0,096; sie stimmen mit den Angaben 0,074, 0,075 und 0,10 überein.

**Zerlegungen:** `sets_decompose.py`, `sets_decompose2.py`, `sets_subset_spread.py` verwenden `frame_elements` und
`snapshots` unverändert; Auswahlen, laufendes Minimum von q, Überlebende des letzten Schnappschusses und
Neigungsanteile sind so gerechnet, wie die Docstrings sagen (Ausnahmen: B8, B9, C5).

**Startwerte (`make_ic.py`, an `HEAD` und bei `make-ic-v1`):**
- Einheiten (au, Jahr zu 365,25 d, Sonnenmasse), G = (k·365,25)², Massenverhältnisse, Schiefe 84381,448″ und Drehung
  in die Ekliptik.
- Sonne mit den inneren Planeten in deren gemeinsamem Schwerpunkt; baryzentrisches System der massiven Körper.
- Elemente zu Zuständen (Drehmatrix, Geschwindigkeiten), Kepler-Gleichung.
- Reihenfolge der Zufallszüge (a, q, i, Ω, ω, M); alle Teilchen werden gezogen und dann geschnitten, die Teilmengen
  sind also unabhängige Züge und hängen nicht vom Ausschnitt ab.
- `--p9-plane invariable`: Ebene aus dem heliozentrischen Drehimpuls von Jupiter bis Neptun, Ω9 − N im System der
  Ebene, Drehung zurück; dieselbe Konvention wie in der Auswertung.
- Skalierte Radien für die Sätze: 17 248,4 km und 15 418,4 km, 0,5206 au und 0,4654 au (nachgerechnet).
- Bestätigt und dokumentiert, nicht als Fehler gewertet: Testteilchen in der Ekliptik statt in der invariablen Ebene;
  a, q, i gleichverteilt (i in Grad).

**Rechenkern:**
- Umrechnung in demokratisch-heliozentrische Koordinaten und zurück (`gpu/p9gpu.c:237–289`).
- Schrittfolge Drift–Sprung–Kick–Sprung–Drift, Sprunggeschwindigkeit, Kick, μ = G·m_Sonne für Planeten und
  Testteilchen (`gpu/whdh.h`, `gpu/p9gpu.c:99–209`).
- Kepler-Löser: Gleichung, Ableitungen, Halley-Schritt, f- und g-Funktionen; Stumpff-Reihen (Koeffizienten) und
  Verdopplungsformeln (`gpu/whdh.h:57–122`).
- Verfahren smooth: Polynom C5 mit Wert 1 am Rand; ferner und naher Anteil ergänzen sich zur vollen Kraft; die
  Teilschritte ergeben zusammen genau dt Drift; die Planeten in den Teilschritten treffen ihre Lage an beiden Kicks;
  Sprungterm (h·wb) richtig berücksichtigt; Regel für die Zahl der Teilschritte; Kollisionsprüfung an jedem
  Teilschritt-Kick (`gpu/whdh.h:443–641`).
- Entfernung: absolute Schrittzählung über Blöcke und Segmente; dieselbe Regel in CPU-Pfad, GPU-Kern und p9sim.
- Schnappschüsse: Reihenfolge der Teilchen bleibt die des Starts (`drop_dead`, `from_dh`); Zeit t += dt ist für
  dt = 0,5 exakt.
- CPU- und GPU-Pfad rufen für `double` dieselben Funktionen mit denselben Argumenten; die Diagnosen des CPU-Pfads
  ändern den Zustand nicht. Tabellenübergabe an die GPU (zwei Puffer, ein Stream) ohne Wettlauf.
- Gleitkomma: `-fno-fast-math -ffp-contract=off` für C und C++, `--fmad=false -prec-div=true -prec-sqrt=true` für nvcc
  (`Makefile:37, 86–87, 95`); im Kern nur + − × ÷ und sqrt.
- Kanonischer Zustand und Prüfsumme (`src/p9state.c`), Radien nach Kennung statt nach Reihenfolge
  (`src/p9encounter.c`, `tools/p9job.py:189–253`).

**Abgleich, übereinstimmend:** Auswahl, Fenster, Toleranzen, Teilmengenregel (P1), Konventionen des Nachtrags 13,
„MERCURIUS removed with the same rule and cadence“ (`docs/sets-outcome-20261117.md:114`, `src/p9sim.c:152–163`),
Angaben von `docs/bb2021-article-vs-package.md` zu Entfernung, Zählern und Kollisionen.

## 6. Nicht geprüft

- **REBOUND 5.2.2.** Die Quelle liegt nicht im Repository (kein Netz). Ungeprüft sind damit: Schreiben und Lesen der
  Archive, ob `reb_simulation_remove_particle` die Reihenfolge erhält (davon hängt die Zuordnung der Kennungen in
  p9gpu ab, `gpu/p9gpu.c:292–304`), Zeitpunkt des Heartbeats, MERCURIUS.
- **Alles, was Rechnen verlangt.** p9sim und p9gpu ließen sich nicht bauen; numpy fehlt. Nicht gelaufen sind
  `tests/test_prod_eval.py`, `test_pair_eval.py`, `test_long_eval.py`, `test_flyby.py`, `test_flyby_regression.py`,
  `test_export_timelapse.py`, `test_iras_akari.py` und der Teil von `test_p9job.py`, der `make_ic.py` aufruft.
- **Numerische Genauigkeit des Rechenkerns:** Konvergenz des Kepler-Lösers nahe der Sonne (B1), Fehler des Verfahrens
  smooth bei Vorbeiflügen, Vergleich mit MERCURIUS. Nur die Formeln sind geprüft.
- **GPU:** kein nvcc, keine Karte; die Bitgleichheit von GPU und CPU ist nur am Quelltext geprüft.
- **Laufdaten.** Schnappschüsse, `job.json`, `params.env` und `removed.tsv` der Läufe liegen nicht im Repository.
  Nicht geprüft sind deshalb: dass die Läufe mit R_IN = 4,5 au, den Radien des Nachtrags 13 und den Seeds 21, 311,
  312 liefen; M1–M5 selbst; die Wirkung von A1; das Auftreten von B2.
- **Paketskripte der Sätze A und B** (`tools/make_bb_packages.sh`, in einem anderen Repository) und der Quelltext des
  Pakets `p9bbsets-5b05cc3` über `gpu/` und `src/` hinaus.
- **Ephemeride:** die Werte aus DE440s (astropy nicht vorhanden).
- **Der Artikel:** welche Definition von ϖ, welche Elemente und welche Auswahl Brown & Batygin in den Abbildungen
  verwenden; die Messungen der Abbildungen.
- **Nicht gelesen:** `tools/sets_addendum4.py`, `equiv_eval.py`, `pair_eval.py`, `long_eval.py`, die übrigen
  Werkzeuge; `gpu/whdh_t.h`, `gpu/cpu_t.cpp`, `gpu/df64.h` nur auf Gleichheit mit dem Laufstand, nicht Zeile für Zeile
  (sie gelten für andere Zahlentypen als `double`).

## 7. Was ausgeführt wurde

- Lesebefehle (`cat`, `grep`, `git log/diff/show/ls-tree`, `sha256sum`); Ausgabe der gespeicherten JSON-Dateien mit
  Python, ohne eigene Rechnung an Laufdaten.
- Vorhandene Tests, in ein temporäres Verzeichnis außerhalb des Repositorys gebaut: `tests/test_encounter.c`,
  `tests/test_j2.c`, `tests/test_step_encounter.c`: alle drei „ok“. `tests/test_pack_record.py` (3 Tests) und
  `tests/test_publish_scan.py` (8 Tests): OK. `tests/test_p9job.py`: 16 Tests, 4 übersprungen, 2 Fehler; beide
  Fehler sind Abbrüche des Aufrufs von `make_ic.py`, das numpy braucht (hier nicht vorhanden).
- Kein Netzzugriff. Keine Datei im Repository angelegt oder geändert.

---

## What was done with it (2026-11-21)

- **A1 and C2** (the definition of ϖ) and **B8, C3 and C5** (R beyond the wall): addendum 5,
  `docs/sets-decomposition-addendum-5-20261121.md`, fixed and timestamped before any computation. It changes nothing
  of the registered outcome; it measures how far the numbers depend on these choices.
- **C1** (the checked-out branch is not the code of the runs): the README of the published state lists, per run, its
  commit or tag and its package.
- **The other points** (A2 as far as not covered by the run BB-A-rin1, B1–B9, C4, C6, C7, NaN in the result files, a
  test of the Kepler solver over the range of the orbits): `docs/open-points-20261121.md`, to be worked on after
  2026-11-24.
- Nothing of it was taken over unchecked; each point is checked against the code and the files before it is acted on.
