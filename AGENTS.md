# AGENTS.md – Codex-Anweisungen für neuro-fly

Diese Datei gilt für das gesamte Repository `dj-nic/neuro-fly`. Sie ist die verbindliche Einstiegshilfe für neue Coding-Agenten. Lies **vor jeder Änderung** zuerst `README.md`, `STATUS.md`, `CONTRIBUTING.md` und bei Bedarf `docs/UMSETZUNG.md` sowie `docs/PI_3B_PROXY.md`. Prüfe immer den tatsächlichen Codebestand: ältere Planungstexte können überholt sein.

## Projektziel

Das Berufsschulprojekt **neuro-fly / FlyBrain Reflex** soll einen biologisch begründeten Fluchtreflex einer Fruchtfliege auf einem **Raspberry Pi 3 Model B+ (1 GB RAM)** demonstrieren:

```text
Annäherung → Sensor → normierter Reiz (0..1)
           → Spiking Neural Network (Brian2 / NeuroHex-Referenz)
           → escape_magnitude → Schutzlogik → Servo
```

Mindestanforderung: **mindestens 1 realer Sensor und 1 realer Aktor**. Ziel ist zunächst **ein** Servo, **nicht** der vollständige NeuroHex-Roboter mit 18 Servos. Optional sind LED und eine Webansicht. Der Fluchtimpuls muss nachweisbar aus der **Ausgabe des neuronalen Modells** kommen, nicht aus einer direkten `if distance < threshold: move_servo()`-Abkürzung.

Das Fliegennetz ist ein **aus echten Connectome-Daten rekonstruierter neuronaler Teilschaltkreis** (Giant-Fiber-Fluchtweg). Behaupte weder ein vollständiges Gehirn noch ein physiologisch exaktes Fliegenauge: Die Übersetzung eines Abstandssignals auf `visual_input` ist eine technische Annäherung.

## Verifizierter Stand am 30.10.2026

- Eigenes Repository vorhanden; NeuroHex bleibt ein **separater Referenz-Checkout**, nicht ein verschachteltes zweites Git-Repo.
- Referenz: https://github.com/shakeabhishek/project-neurohex, festgehaltener Commit `5d1052b995db12fa1baf8d42f6a94c3f0695817d`.
- `scripts/setup.sh` bereitet Referenz, lokale `.venv`, Daten und Check vor; `scripts/validate_brain.py` validiert den Datensatz und prüft den Reflex.
- Verifiziert auf **Linux x86_64 / Python 3.12**: **992 Neuronen**, **1.308 gerichtete Verbindungen**; die 9 dokumentierten Testläufe mit insgesamt 315 Schritten bestanden die Reflexprüfungen.
- Cloud-Messwerte: durchschnittlich ~69,5 ms für einen simulierten 20-ms-Step ohne künstliches CPU-Limit, ~310,3 ms und ~554,5 ms in zwei gedrosselten Versuchsbedingungen. Siehe `STATUS.md` und `docs/PI_3B_PROXY.md`.
- **Keine Hardware vorhanden/getestet:** weder Pi 3B+ noch Sensor, Servo oder GPIO. Auch die ARM-Paketinstallation ist **nicht** nachgewiesen. Cloud-CPU-Drosselung ist **keine** Pi-Emulation. Reaktionszeit <1 s ist ein **Ziel**, kein Messwert.
- Bislang gibt es noch **keine eigene Sensor-Servo-Anwendung**. Die nächsten Schritte sind Softwareadapter und Mock-Tests.

## Geplante Hardware

- **Pi 3B+**, 64-Bit-Raspberry-Pi-OS nach Kompatibilitätsprüfung.
- **Bevorzugter Abstandssensor: VL53L4CD (I²C)**, als inzwischen ins Auge gefasste Alternative zum schwer verfügbaren VL53L0X. **Noch nicht gekauft / angeschlossen / validiert.**
- Weitere Optionen: VL53L1X, VL53L0X, HC-SR04 (5-V-ECHO-Pegel vor Pi-GPIO auf 3,3 V anpassen), optional Pi-Kamera; die Kamera beansprucht mehr Rechenleistung.
- **Ein Servo** als einfacher Fluchtaktor, zunächst per Mock; bei echter Hardware geeignete separate Versorgung, gemeinsame Masse und ungefährliche Winkel/Mechanik beachten. Servo nicht ungeprüft aus einem Pi-GPIO speisen.
- Hardwarewahl darf nicht ohne Rücksprache als endgültig ausgegeben werden.

## Architekturvorgaben für neue Implementierungen

Entwickle kleine, separat testbare Module; die Struktur darf passend zum bestehenden Repo gewählt werden:

1. **Sensoradapter**: austauschbar zwischen Mock-Sensor, später VL53L4CD und optional Kamera. Erzeugt `looming_strength: float` in `[0.0, 1.0]` aus **Annäherung**, nicht nur aus einem starren Distanzschwellwert. Messfehler, ungültige Werte, Glättung, Richtung und Zeitabstand von Messungen berücksichtigen.
2. **Brainadapter**: kapselt `NeuroHexBrain.step(visual_input=looming_strength, mechanosensory_input=0.0, duration_ms=20.0)` und dessen `escape_magnitude`. Benutze echte validierte Connectome-Daten; kein unbemerktes Dummy-/Zufallsnetz. Fehler bei fehlenden Daten explizit machen.
3. **Aktoradapter**: Mock-Servo mit Ereignislog/Zeiten; später echte GPIO-/Servo-Implementierung. Ein Schwellwert **auf der Motorausgabe des SNN**, Hysterese, Cooldown, sichere Start- und Endpositionen sowie definierte Fehlerreaktion schützen vor Dauerzucken.
4. **Orchestrierung**: Sensor → SNN → Aktor, mit klarer Messung von Sensorauslesung, Brain-Step und Aktorzeit. Sensor und Aktor müssen ohne reale Hardware ersetzbar bleiben.
5. **Messung**: CPU, Peak-RAM, Initialisierung, Step-Latenz, Reaktionsdauer und Fehlalarme protokollieren. Für Benchmarks Warm- und Kaltstart unterscheiden; Board/CPU/OS/Python/Backend/Stimulus/Versionen angeben.

Wichtig: Ein berechneter 20-ms-Neuronenschritt ist **nicht** automatisch in 20 ms Echtzeit fertig. Keine künstlich geschönten Latenzzahlen, keine Vermischung von Simulationszeit und Wandzeit.

## Referenzcode, Daten und Installation

- Upstream **nicht blind kopieren** oder in diesem Repository als Sub-Git-Repo einchecken. Ursprünglich relevant: `snn_brain.py`, `fetch_connectome.py`, ggf. `vision.py` und `main.py` als Referenz. `motor_control.py` ist für den großen Hexapod und nicht für unseren Ein-Servo-Demonstrator gedacht.
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

1. Bestehende Dateien und offenen Stand überprüfen; keine bereits erledigten Schritte erneut als neu verkaufen.
2. **Kleine eigene Schnittstellen** für Sensorinput, Brainoutput und Servooutput definieren; nach Möglichkeit Typen und stabile API dokumentieren.
3. **Mock-Sensor** (z. B. reproduzierbare Annäherungskurve) und **Mock-Servo** implementieren, ohne GPIO-Abhängigkeiten.
4. Einen durchgehenden **Software-Testpfad** schaffen, bei dem der Mock-Sensor den realen NeuroHex-Kern speist und dessen `escape_magnitude` über Schutzlogik den Mock-Servo auslöst.
5. Automatisierte Tests für Normalfall, keine Annäherung, entfernte/ungültige Messwerte, Jitter, Auslöse-/Rücksetzschwelle, Cooldown, fehlende Connectome-Daten und wiederholte Reize schreiben. Trenne Tests, die echte Daten brauchen, von schnellen Unit-Tests.
6. Wenn möglich reproduzierbare Profiling-Verbesserungen untersuchen; **Biologie/Parameter nicht still ändern**. Vorher/nachher mit gleichem Datensatz und Stimulus testen.
7. `README.md`, `STATUS.md` und ggf. `docs/` auf den nachgewiesenen Stand bringen; Hardwareintegration ausdrücklich offen lassen.

## Sobald der Pi und die Bauteile verfügbar sind

- ARM-/Python-/Brian2-Cython-Kompatibilität, verfügbare CPU/RAM, Thermik, Stromversorgung und Startup prüfen.
- Unveränderte Referenz mit validierten Connectome-Daten benchmarken.
- Erst Sensor und Servo **einzeln** und sicher prüfen, dann Kopplung testen.
- End-to-End-Latenz **vom äußeren Reiz bis zur tatsächlichen Bewegung** messen; Ergebnisse getrennt von Cloud-/Mock-Messungen ausweisen.
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
