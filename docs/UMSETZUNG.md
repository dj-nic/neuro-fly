# Ursprüngliche Umsetzungsanleitung

Archiv der vom Projekt bereitgestellten Planung. Maßgeblich für den tatsächlichen
Stand sind [STATUS.md](../STATUS.md) und [README.md](../README.md).
Wir verwenden bereits `dj-nic/neuro-fly`; kein weiteres eigenes Repository anlegen.
Die unten genannten ursprünglichen Namen und die Checkliste sind Planungsstand,
keine aktuellen Nachweise. NeuroHex bleibt ein separates Referenz-Repository.

---

Umsetzungsanleitung – FlyBrain Reflex
Status: Vorbereitung. Hardware fehlt noch.
Die folgenden Befehle sind anhand der Repository-Struktur geplant, nicht auf eurem Pi 3B+ getestet. Änderungen am Upstream sind möglich.

0. Grundsatz: Eigenes Repo + NeuroHex als Referenz
Wir klonen nicht einfach den fertigen NeuroHex-Roboter in unser Projekt. Stattdessen:
1. Ein eigenes Git-Repository flybrain-reflex für unsere Dokumentation, Adapter und Steuerung anlegen.
2. NeuroHex als separates Referenz-Repository daneben auschecken.
3. Zunächst nur den neuronalen Kern und das Beschaffungsskript untersuchen.
4. Nur die tatsächlich benötigten Teile später – unter Beachtung der Lizenz/Attribution – in unser Projekt integrieren.
Geplantes Arbeitsverzeichnis:
Projekte/
├── flybrain-reflex/       # Unser eigenes Git-Repo mit README.md und UMSETZUNG.md
└── neurohex-reference/    # Separater, unveränderter Upstream-Checkout
Original: https://github.com/shakeabhishek/project-neurohex
Nicht den in der Upstream-README teils noch genannten ColumbiaRobotics-Klonbefehl übernehmen.
1. Eigenes Repository vorbereiten (geht schon jetzt)
mkdir flybrain-reflex
cd flybrain-reflex
git init -b main
Die beiden mitgelieferten Dokumente README.md und UMSETZUNG.md in dieses Verzeichnis legen. Das eigentliche Projekt auf GitHub erstellen, wenn ihr dafür bereit seid. Namen und Teammitglieder sind noch offen.

Eine .gitignore sollte mindestens .venv/, __pycache__/, .pytest_cache/ und *.pyc ausschließen. Connectome-Daten erst nach Prüfung der Größe und der Weitergabebedingungen versionieren.
2. NeuroHex teilweise auschecken (geht schon jetzt)
Aus dem übergeordneten Verzeichnis Projekte/ ausführen, damit kein verschachteltes Git-Repository entsteht:
git clone --depth 1 --filter=blob:none --sparse https://github.com/shakeabhishek/project-neurohex.git neurohex-reference
cd neurohex-reference
git sparse-checkout set --no-cone /snn_brain.py /fetch_connectome.py /vision.py /main.py /requirements.txt /README.md /AGENT_INSTRUCTIONS.md
git rev-parse HEAD
Die letzte Ausgabe (Commit-SHA) in der Projektdokumentation festhalten. --sparse plus sparse-checkout sorgt dafür, dass nur die angegebenen Dateien im Arbeitsverzeichnis ausgecheckt werden; der Git-Verlauf ist wegen --depth 1 ebenfalls begrenzt.

Hinweis: Falls euer Git-Client partielles Klonen nicht unterstützt, reicht bei diesem kleinen Repository alternativ:
git clone --depth 1 https://github.com/shakeabhishek/project-neurohex.git neurohex-reference
Dann die nicht benötigten Dateien einfach ignorieren. Nicht versehentlich den Upstream-Ordner inklusive eigener .git-Dateien in euer Git-Repository kopieren.
Was wird wie verwendet?
Datei	Vorgehen
snn_brain.py	Erst testen, später in src/brain/ adaptieren
fetch_connectome.py	Am Entwicklungs-PC ausführen, nicht unbedingt auf dem Pi
vision.py	Nur als optionale Kamera-Variante vormerken
main.py	Schnittstellen nachvollziehen, eigene Pi-3B+-Variante schreiben
requirements.txt	Abhängigkeiten prüfen; nicht blind pip install -r ... auf dem Pi
AGENT_INSTRUCTIONS.md	Entwicklungsstand und Warnung vor älteren Connectome-Versionen prüfen
motor_control.py	Für unser 1-Servo-Projekt nicht benötigt (18-Servo-Hexapod)


Warum keine komplette Übernahme? Die originale Steuerung koppelt Kamera, Giant-Fiber-Netz und 18 Beinservos. Wir ersetzen Kamera ggf. durch einen ToF-/Ultraschallsensor und benötigen eine neue, einfache 1-Servo-Ansteuerung.
3. Echte neuronale Daten erzeugen (vorzugsweise am PC)
Der Quellcode benötigt für die reale Netzstruktur insbesondere:
connectome_data/
├── adjacency_matrix.npy
├── neuron_metadata.json
└── connection_list.json
Diese Dateien entstehen erst durch fetch_connectome.py. Der Datendownload nutzt die API von Virtual Fly Brain. Die Abhängigkeit vfb-connect kann auf ARM umständlich sein; darum zunächst am normalen Entwicklungsrechner vorbereiten.

Beispiel unter Linux/macOS im Verzeichnis neurohex-reference/:
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy vfb-connect
python fetch_connectome.py
Unter Windows: py -m venv .venv und anschließend .venv\Scripts\Activate.ps1; danach dieselben python -m pip-Befehle.

Validieren, bevor es weitergeht:
python -c "import json, pathlib; p=pathlib.Path('connectome_data/neuron_metadata.json'); print('Neuronen:', len(json.loads(p.read_text(encoding='utf-8'))))"
Die Upstream-Dokumentation beschreibt ungefähr 992 Neuronen. Eine andere Zahl muss untersucht werden: Datenquelle, API-Verhalten oder Filter können sich geändert haben. Wenn nur 20 Neuronen auftauchen, ist das sehr wahrscheinlich das zufällige Fallback, nicht der echte Datensatz.

Wichtig: Das Skript kann bei API-Problemen einzelne Abfragen überspringen. Die bloße Existenz der Dateien ist kein Nachweis für einen vollständigen, sinnvollen Datensatz. Neuronengruppen wie GF, LC4/LPLC2 und DN/TTMn ebenfalls prüfen.
4. Simulation ohne echte Hardware testen
Noch im Referenzordner und in der virtuellen Python-Umgebung:
python -m pip install brian2
python snn_brain.py
Das Originalskript führt einen synthetischen Annäherungsreiz durch und gibt escape_magnitude aus. Vor einem erfolgreichen Test muss die Ausgabe ohne Using dummy data-Warnung starten. Ein durchlaufender Prozess allein beweist keine biologische Datenbasis.

Erwartetes Ziel: Der berechnete Fluchtwert steigt bei ausreichend starkem Reiz. Ob die Schwelle für den echten Datensatz erreicht wird, ist zu prüfen; bei Bedarf Stimulus und Modellparameter nachvollziehbar kalibrieren.
Was wir benchmarken wollen
- Startzeit und maximaler RAM-Verbrauch
- Laufzeit pro brain.step(..., duration_ms=20.0)
- Simulierte Zeit vs. reale Zeit (Echtzeitfaktor)
- Anzahl gültiger Neuronen, Synapsen und motorischer Ausgabegruppen
- Fehler und notwendige Änderungen an Python-/Paketversionen
Ein 20-ms-Simulationsschritt muss für echte Echtzeitverarbeitung im Mittel deutlich unter 20 ms tatsächlicher Berechnungszeit bleiben; bei langsameren Schritten wird die Simulation verzögert. Ein Schul-Demonstrator darf langsamer sein, aber wir messen das transparent.
5. Erst wenn der Raspberry Pi 3B+ verfügbar ist
1. Raspberry Pi OS (möglichst 64-Bit, Paketkompatibilität prüfen) frisch installieren.
2. Python-Version und freien RAM dokumentieren.
3. Nur für den neuronalen Kern erforderliche Pakete installieren (numpy, brian2, weitere Importabhängigkeiten nach Bedarf).
4. Echte connectome_data/ vom PC übertragen.
5. snn_brain.py ohne Sensor und Servo starten.
6. CPU, Peak-RAM und Berechnungszeit messen; Ergebnisse festhalten.
7. Wenn die Simulation zu langsam/instabil ist: SNN-Parameter, Auflösung der Zeitschritte, Monitoring und Alternativen prüfen. Keine künstlich schnellen Benchmarks mit Dummy-Daten angeben.
Auf dem Pi nicht sofort die komplette Upstream-requirements.txt installieren: Dort stehen u. a. Kamera-, Servo- und vfb-connect-Pakete, die in unserer ersten Phase nicht nötig sind.
6. Eigene Sensor-Schnittstelle implementieren
Jeder Sensor-Adapter soll ein gleichartiges, normiertes Signal liefern:
looming_strength: float  # 0.0 = keine Annäherung, 1.0 = starker Annäherungsreiz
Option A (bevorzugter Einstieg): VL53L0X über I²C. Aus aufeinanderfolgenden Entfernungen Annäherungsgeschwindigkeit berechnen, Messrauschen glätten und in 0..1 umrechnen.

Option B: HC-SR04 über Trigger/Echo-GPIO, dabei den 5-V-ECHO-Pegel zum Pi passend reduzieren.

Option C: Kamera, angelehnt an vision.py, mit Optical Flow bei niedriger Auflösung. Höhere CPU-Auslastung erwarten.

Im angepassten Hauptprogramm rufen wir den vorhandenen Brain-Kern ungefähr so auf:
output = brain.step(
    visual_input=looming_strength,
    mechanosensory_input=0.0,
    duration_ms=20.0,
)
escape_strength = output["escape_magnitude"]
Achtung: Ein Abstandssensor im visuellen visual_input ist eine technische Annäherung, keine biologische Simulation eines echten Fliegenauges. Diesen Unterschied in der Dokumentation deutlich machen.
7. Eigene Aktor-Schnittstelle implementieren
- Ein Servo führt eine kurze Flucht-/Sprungbewegung aus.
- Ein Schwellwert der SNN-Motorausgabe löst die Bewegung aus, nicht direkt der Abstandssensor.
- Hysterese und Cooldown verhindern hektisches Flattern.
- Servo zunächst über Mock/Testausgabe entwickeln, später sichere Stromversorgung und GPIO-Ansteuerung ergänzen.
- Optional: Status-LED oder Weboberfläche mit Messwerten und SNN-Status.
8. Messtests und Abschluss
Messung	Warum?
Sensorauslesung in ms	Eingabelatenz
Gehirn-Step in ms	Haupteinfluss auf Echtzeitfähigkeit
GPIO bis Bewegung in ms	Physische Aktorlatenz
Gesamtzeit Reiz → Bewegung	Aussagekräftige End-to-End-Metrik
CPU/Peak-RAM	Eignung des Pi 3B+
Auslösungen/Fehlalarme	Robustheit des Fluchtreflexes


Ziel: Nachweisbares Cyber-physisches System mit mindestens einem Sensor und einem Aktor, dessen Verhalten durch das neuronale Modell gesteuert wird. Zielwert: möglichst unter 1 s Reaktionszeit; keine Garantie vor den Benchmarks.
9. Checkliste
Jetzt, ohne Hardware
- [ ] Eigenes GitHub-Repo anlegen
- [ ] README.md und UMSETZUNG.md committen
- [ ] NeuroHex-Checkout als separate Referenz anlegen und Commit-SHA notieren
- [ ] Lizenz/Attribution für spätere Übernahme prüfen (README nennt MIT)
- [ ] fetch_connectome.py auf dem PC testen
- [ ] Echtes Connectome validieren (keine Dummy-Daten)
- [ ] Optional: Brain-Benchmark schon auf dem PC erstellen
Sobald die Hardware da ist
- [ ] Pi 3B+ einrichten und Baseline messen
- [ ] Reales Connectome + Brian2 auf Pi testen
- [ ] Sensor auswählen und anschließen
- [ ] Servo sicher anschließen und separat testen
- [ ] Sensor → SNN → Servo koppeln
- [ ] Reaktionszeit / RAM / CPU messen und dokumentieren
- [ ] Diagramm, Schaltplan, Quellennachweise und Eigenleistung abschließen
10. Quellen / wichtige Hinweise
- Upstream-Code: https://github.com/shakeabhishek/project-neurohex
- API/Schaltkreis: https://github.com/shakeabhishek/project-neurohex/blob/main/fetch_connectome.py
- Brian2-Simulation: https://github.com/shakeabhishek/project-neurohex/blob/main/snn_brain.py
- NeuroHex-Entwicklernotizen: https://github.com/shakeabhishek/project-neurohex/blob/main/AGENT_INSTRUCTIONS.md
- Die Upstream-README bezeichnet das Projekt als MIT-lizenziert; eine eigenständige LICENSE-Datei war bei Sichtprüfung am 26.10.2026 nicht im Repo-Hauptverzeichnis ersichtlich. Vor Veröffentlichung von übernommenen Dateien Lizenztext und Namensnennung überprüfen.