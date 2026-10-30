# AGENTS.md – Codex-Anweisungen für neuro-fly

Diese Datei gilt für das gesamte Repository `dj-nic/neuro-fly`. Sie ist die verbindliche Einstiegshilfe für neue Coding-Agenten. Lies **vor jeder Änderung** zuerst `README.md`, `STATUS.md`, `CONTRIBUTING.md` und bei Bedarf `docs/UMSETZUNG.md` sowie `docs/PI_3B_PROXY.md`. Prüfe immer den tatsächlichen Codebestand: ältere Planungstexte können überholt sein.

## Projektziel

Das Berufsschulprojekt **neuro-fly / FlyBrain Reflex** soll einen biologisch begründeten Fluchtreflex einer Fruchtfliege auf einem **Raspberry Pi 3 Model B+ (1 GB RAM)** demonstrieren:

```text
Annäherung → Sensor → normierter Reiz (0..1)
           → Spiking Neural Network (Brian2 / NeuroHex-Referenz)
           → escape_magnitude → Schutzlogik → LED/einfacher physischer Ausgang
```

Mindestanforderung: **mindestens 1 realer Sensor und 1 realer Aktor**. Kamera und Servo sind für den Demonstrator ausgeschlossen. Als Sensor stehen ein laserbasierter ToF-Abstandssensor oder Ultraschall zur Wahl; als einfacher Ausgang voraussichtlich eine LED oder eine andere geeignete Lösung. Die konkrete Auswahl ist offen. Klären, ob eine LED die schulische Aktoranforderung erfüllt. Der Fluchtimpuls muss nachweisbar aus der **Ausgabe des neuronalen Modells** kommen, nicht aus einer direkten `if distance < threshold: switch_output()`-Abkürzung.

Das Fliegennetz ist ein **aus echten Connectome-Daten rekonstruierter neuronaler Teilschaltkreis** (Giant-Fiber-Fluchtweg). Behaupte weder ein vollständiges Gehirn noch ein physiologisch exaktes Fliegenauge: Die Übersetzung eines Abstandssignals auf `visual_input` ist eine technische Annäherung.

## Verifizierter Stand am 30.10.2026

- Eigenes Repository vorhanden; NeuroHex bleibt ein **separater Referenz-Checkout**, nicht ein verschachteltes zweites Git-Repo.
- Referenz: https://github.com/shakeabhishek/project-neurohex, festgehaltener Commit `5d1052b995db12fa1baf8d42f6a94c3f0695817d`.
- `scripts/setup.sh` bereitet Referenz, lokale `.venv`, Daten und Check vor; `scripts/validate_brain.py` validiert den Datensatz und prüft den Reflex.
- Verifiziert auf **Linux x86_64 / Python 3.12**: **992 Neuronen**, **1.308 gerichtete Verbindungen**; die 9 dokumentierten Testläufe mit insgesamt 315 Schritten bestanden die Reflexprüfungen.
- Cloud-Messwerte: durchschnittlich ~69,5 ms für einen simulierten 20-ms-Step ohne künstliches CPU-Limit, ~310,3 ms und ~554,5 ms in zwei gedrosselten Versuchsbedingungen. Siehe `STATUS.md` und `docs/PI_3B_PROXY.md`.
- **Keine Hardware vorhanden/getestet:** weder Pi 3B+ noch Sensor, LED/anderer Ausgang oder GPIO. Auch die ARM-Paketinstallation ist **nicht** nachgewiesen. Cloud-CPU-Drosselung ist **keine** Pi-Emulation. Reaktionszeit <1 s ist ein **Ziel**, kein Messwert.
- `neuro_fly/` enthält einen hardwarefreien Sensor → Brainadapter → Mock-Ausgang-Pfad mit Schutzlogik. 33 schnelle Unit-Tests bestanden unter Windows und WSL/Python 3.12; der separate WSL-Integrationstest bestand mit echtem Kern und 992 Neuronen/1.308 Verbindungen. Testdoubles sind keine neuronalen Nachweise.

## Geplante Hardware

- **Pi 3B+**, 64-Bit-Raspberry-Pi-OS nach Kompatibilitätsprüfung.
- **Sensoroptionen:** laserbasierter ToF-Abstandssensor (z. B. VL53L4CD oder VL53L0X) oder Ultraschall (z. B. HC-SR04). Noch nicht ausgewählt, gekauft, angeschlossen oder validiert. Bei HC-SR04 den 5-V-ECHO-Pegel vor dem Pi-GPIO auf 3,3 V anpassen.
- **Ausgang:** LED mit geeignetem Vorwiderstand ist die aktuelle einfache Möglichkeit; eine andere geeignete physische Ausgabe bleibt möglich. Noch nicht ausgewählt oder getestet; die Erfüllung der schulischen Aktoranforderung ist zu klären.
- Hardwarewahl darf nicht ohne Rücksprache als endgültig ausgegeben werden. Kamera und Servo sind nicht Teil der aktuellen Planung.

## Architekturvorgaben für neue Implementierungen

Entwickle kleine, separat testbare Module; die Struktur darf passend zum bestehenden Repo gewählt werden:

1. **Sensoradapter**: austauschbar zwischen Mock-Sensor, später ToF- und Ultraschallsensor. Erzeugt `looming_strength: float` in `[0.0, 1.0]` aus **Annäherung**, nicht nur aus einem starren Distanzschwellwert. Messfehler, ungültige Werte, Glättung, Richtung und Zeitabstand von Messungen berücksichtigen.
2. **Brainadapter**: kapselt `NeuroHexBrain.step(visual_input=looming_strength, mechanosensory_input=0.0, duration_ms=20.0)` und dessen `escape_magnitude`. Benutze echte validierte Connectome-Daten; kein unbemerktes Dummy-/Zufallsnetz. Fehler bei fehlenden Daten explizit machen.
3. **Aktoradapter**: Mock-Ausgang mit Ereignislog/Zeiten; später eine geeignete GPIO-Ausgabe wie LED. Ein Schwellwert **auf `escape_magnitude` des SNN**, Hysterese, Cooldown und definierte Fehlerreaktion schützen vor Dauerleuchten oder Flattern.
4. **Orchestrierung**: Sensor → SNN → einfacher Aktor, mit klarer Messung von Sensorauslesung, Brain-Step und Ausgangszeit. Sensor und Aktor müssen ohne reale Hardware ersetzbar bleiben.
5. **Messung**: CPU, Peak-RAM, Initialisierung, Step-Latenz, Reaktionsdauer und Fehlalarme protokollieren. Für Benchmarks Warm- und Kaltstart unterscheiden; Board/CPU/OS/Python/Backend/Stimulus/Versionen angeben.

Wichtig: Ein berechneter 20-ms-Neuronenschritt ist **nicht** automatisch in 20 ms Echtzeit fertig. Keine künstlich geschönten Latenzzahlen, keine Vermischung von Simulationszeit und Wandzeit.

## Referenzcode, Daten und Installation

- Upstream **nicht blind kopieren** oder in diesem Repository als Sub-Git-Repo einchecken. Relevant sind `snn_brain.py`, `fetch_connectome.py` und `main.py` als Referenz. `vision.py` und `motor_control.py` gehören zu anderen Hardwarevarianten und sind für unseren Demonstrator nicht eingeplant.
- Der festgehaltene Checkout wird durch `scripts/setup.sh` als **Nachbarverzeichnis** `../neurohex-reference` eingerichtet. Behalte diesen Stand reproduzierbar; Upstream nicht ungefragt aktualisieren oder dort arbeiten.
- Echte Daten werden durch die Referenz bezogen. Relevante Dateien sind `connectome_data/adjacency_matrix.npy`, `neuron_metadata.json` und `connection_list.json`. `scripts/validate_brain.py` prüft Struktur, Gruppen, Matrix und Reflexantwort.
- **Lizenz/Attribution zuerst klären**, bevor fremder Quellcode direkt übernommen oder neu veröffentlicht wird. Upstream nennt MIT, eine eigenständige LICENSE-Datei war beim bisherigen Check nicht gesichert. Datenherkunft, Abrufzeit und Nutzungsbedingungen dokumentieren.
- Auf Linux x86_64 lautet der dokumentierte Start:
  ```bash
  git clone https://github.com/dj-nic/neuro-fly.git
  cd neuro-fly
  bash scripts/setup.sh
  ```
  Dieser Vorgang kann Downloads und Compiler benötigen. `requirements-dev.lock` ist ein **x86_64-Entwicklungsstand**, keine fertige ARM-Lockdatei. Auf dem Pi nur benötigte Pakete installieren und zuerst Kompatibilität messen.
- `scripts/validate_brain.py` ist ein funktionaler Check mit echten Daten, **keine** End-to-End-Hardwareprüfung. Mit `python -O` nicht ausführen, da die Checks Assertions verwenden.

## Konkreter nächster Arbeitsauftrag (solange Hardware fehlt)

Arbeite inkrementell und dokumentiere Resultate:

1. Bestehenden Softwarepfad und offenen Stand prüfen; die vorhandenen Mock-Adapter und Unit-Tests nicht erneut als neue Arbeit behandeln.
2. Den separaten Integrationstest mit gepinntem NeuroHex-Kern und echten Daten bei Änderungen erneut unter Linux/WSL ausführen; fehlende Voraussetzungen und Ergebnisse dokumentieren.
3. Datenprovenienz und Lizenz/Attribution klären; Filter- und Schwellwerte später mit dem gewählten Sensor kalibrieren.
4. Wenn möglich reproduzierbare Profiling-Verbesserungen untersuchen; **Biologie/Parameter nicht still ändern**. Vorher/nachher mit gleichem Datensatz und Stimulus testen.
5. `README.md`, `STATUS.md` und ggf. `docs/` auf den nachgewiesenen Stand bringen; Hardwareintegration ausdrücklich offen lassen.

## Sobald der Pi und die Bauteile verfügbar sind

- ARM-/Python-/Brian2-Cython-Kompatibilität, verfügbare CPU/RAM, Thermik, Stromversorgung und Startup prüfen.
- Unveränderte Referenz mit validierten Connectome-Daten benchmarken.
- Erst Sensor und LED/anderen Ausgang **einzeln** und sicher prüfen, dann Kopplung testen.
- End-to-End-Latenz **vom äußeren Reiz bis zur tatsächlichen Ausgabe** messen; Ergebnisse getrennt von Cloud-/Mock-Messungen ausweisen.
- Hardwareverdrahtung und Wahl des Sensors dokumentieren; Korrektheit und Stabilität sind wichtiger als unbelegte Echtzeitversprechen.

## Arbeits- und Git-Regeln

- **Kleine, gut nachvollziehbare Änderungen** statt großem Umbau; vorhandene Repo-Struktur respektieren.
- Bestehende Nutzeränderungen und den Referenz-Checkout nicht verwerfen. Keine Force-Pushes, kein ungefragtes Umschreiben der Historie.
- `.venv/`, Caches, generierte Connectome-Daten, Secrets, große Binärdateien und lokale Hardware-/Benchmark-Artefakte nicht committen. Reproduzierbare Messberichte dürfen mit Methode unter `results/` landen.
- Vor dem Commit relevante Tests ausführen; fehlende Voraussetzungen und nicht durchgeführte Tests transparent nennen.
- Bei Bedarf für neue Features einen separaten Branch/PR nutzen und klar beschreiben: geändert, getestet, nicht getestet, verbleibende Risiken.
- Keine neue `codex.md` anlegen. **Diese `AGENTS.md` ist die maßgebliche Agentenanweisung.**

## Definition of Done für den nächsten Agenten

Eine Änderung gilt erst als fertig, wenn sie eine konkrete Funktion oder ein überprüfbares Dokumentationsergebnis liefert, mit passenden Tests nachgewiesen ist, keine echten Hardwaretests vortäuscht und `STATUS.md` sachlich aktualisiert wurde. Am Ende kurz berichten: Änderungen, Befehle/Tests, Ergebnisse und nächster sinnvoller Schritt.
