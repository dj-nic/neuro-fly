# Projektstand und offene Aufgaben

Stand: 30.10.2026. Projekt: `dj-nic/neuro-fly`, Arbeitstitel FlyBrain Reflex.

## Aktuelle Hardwareplanung

- Eine Kamera und ein Servo sind für den Demonstrator ausgeschlossen.
- Als realer Abstandssensor stehen ein laserbasierter ToF-Sensor (z. B. VL53L4CD oder VL53L0X) und Ultraschall (z. B. HC-SR04) zur Auswahl. Noch ist kein Modell festgelegt oder angeschlossen.
- Als einfacher physischer Ausgang kommt voraussichtlich eine LED oder eine andere geeignete Lösung infrage. Ob eine LED die schulische Aktoranforderung erfüllt, ist noch zu klären.
- Raspberry Pi, Sensor und Ausgang wurden nicht als Hardware getestet; die ARM-Installation ist weiterhin offen.

## Neuer Softwarepfad ohne Hardware

- `neuro_fly` enthält Abstandsschnittstelle, deterministische Mock-Messreihen,
  Annäherungsencoder, Adapter für den gepinnten NeuroHex-Kern, Schutzlogik und Mock-Ausgang.
- Der Encoder nutzt relative Annäherungsrate `v/d`; Filter und Skalierung sind
  konfigurierbare Demo-Werte und noch nicht an einem realen Sensor kalibriert.
- Der Ausgang wird ausschließlich über `escape_magnitude` angesteuert:
  Schwellwert über 0,5, 250-ms-Impuls, Rücksetzen unter 0,3 und 1 s Cooldown.
  Ungültige Sensordaten und Fehler deaktivieren den Mock-Ausgang.
- 33 schnelle Unit-Tests auf Windows/Python 3.12 bestanden, darunter Tests mit
  ausdrücklich gekennzeichnetem Brain-Testdouble. Diese belegen die Logik,
  aber keinen Echtlauf mit dem neuronalen Modell.
- Unter Ubuntu/WSL/Python 3.12 bestanden alle 33 Tests in einer temporären
  Umgebung mit NumPy. Ohne NumPy werden fünf Strukturtests übersprungen.
- Der separate Integrationstest bestand unter WSL mit echtem NeuroHex-Kern,
  Mock-Sensor und Mock-Ausgang: Stillstand blieb ohne Impuls; Annäherung
  erzeugte eine Auslösung aus `escape_magnitude > 0,5`.
- Der gepinnte Referenz-Checkout und die am 30.10.2026 über Virtual Fly Brain
  abgerufenen Daten liegen lokal als Nachbarverzeichnis. Das WSL-Setup bestand
  nach Einrichtung der Projektumgebung; beim ersten Versuch fehlte Ubuntus
  `ensurepip`, daher wurde Pip nur in der lokalen Umgebung ergänzt. Für eine
  neue Umgebung bleibt das passende `python3-venv`-Paket Voraussetzung.

Ein zusätzlicher Demo-Lauf vom 30.10.2026 nutzte WSL2/x86_64 auf einem Intel
Core i9-12900H, Python 3.12.3, NumPy 2.5.4, Brian2 2.10.1 und Cython 3.1.3
mit warmem Cache und auf einen Thread begrenzten BLAS/OpenMP-Einstellungen.
Bei 60 synthetischen 20-ms-Schritten entstand ein Mock-Impuls: 1,2 s
Simulationszeit benötigten 18,49 s Wandzeit einschließlich 13,47 s
Initialisierung; der mittlere Brain-Step nach dem ersten lag bei 79,6 ms,
alle 60 Zyklen überschritten 20 ms. Peak-RSS des Prozesses: rund 137 MiB.
Dies ist ein einzelner Softwarelauf, keine Pi-Messung und keine physische
End-to-End-Latenz. Der lokale JSON-Bericht liegt unter
`artifacts/mock-demo-final-wsl.json` und wird nicht versioniert.

## Erledigt und überprüft

- Eigenes Repository vorhanden; NeuroHex als separater, unveränderter Referenz-Checkout.
- Referenzcommit: `5d1052b995db12fa1baf8d42f6a94c3f0695817d`.
- Python 3.12, NumPy, Brian2/Cython und vfb-connect auf Cloud-x86_64 installiert.
- Datenabruf über das unveränderte Upstream-Skript ohne protokollierte Abfragefehler.
- 992 Neuronen und 1308 gerichtete Verbindungen; Matrix und Verbindungsliste konsistent.
- Beide GF-Neuronen vorhanden; LC4: 126, LPLC2: 182, DN: 35, TTMn: 2.
- Neun Messläufe, insgesamt 315 Schritte, bestanden: Ruhezustand ohne
  Motorausgabe, Fluchtwert bei starkem Reiz bis 1,0. Keine Dummy-Daten.
- Pi-Referenzen online recherchiert; CPU-Budget-Tests mit Quellen und Einzeldaten archiviert.

## Was die Tests aussagen

| Cloud-Bedingung, jeweils ein Kern | Ø Zeit je 20-ms-Step | Synthetischer Reiz bis Fluchtschwelle |
|---|---:|---:|
| Ohne zusätzliches CPU-Limit | 69,5 ms | 0,51–0,80 s |
| 35 % CPU-Zeitbudget | 310,3 ms | 2,63–3,60 s |
| 22,24 % CPU-Zeitbudget | 554,5 ms | 4,51–5,15 s |

Je drei Wiederholungen. Prozess-Peak-RSS in dieser Serie ca. 140 MiB;
das ist nicht der RAM-Verbrauch eines vollständigen Pi-Systems.
Die Zeitbudgets ließen sich nicht stabil auf den dokumentierten
Pi-Sysbench-Wert kalibrieren. **Dies sind keine Pi-3B+-Messwerte.**
Der 20-ms-Echtzeittakt wurde in diesen Tests nicht erreicht. Die gemessene
Reaktion enthält eine synthetische Reizrampe, keine reale Sensor- oder Ausgangslatenz.
Das Ziel einer Reaktion unter einer Sekunde ist für die Hardware unbestätigt.

## Nächste Schritte ohne Hardware

- [ ] Lizenztext und Attribution mit NeuroHex klären, bevor Code übernommen wird.
- [ ] Datenprovenienz, Filter, Abrufzeitpunkt und Weitergabebedingungen nachvollziehbar sichern.
- [x] Kern-Schnittstelle mit expliziter Prüfung von Referenz und Connectome-Dateien implementieren.
- [x] Annäherungsencoder und Mock-Abstandssensor für normiertes `looming_strength` implementieren.
- [x] Mock-Ausgang mit Schwellwert, Hysterese, Impuls und Cooldown implementieren.
- [x] Kopplung und Fehlerfälle mit schnellen Unit-Tests und Brain-Testdouble absichern.
- [x] Durchgehenden Mock-Pfad mit echtem NeuroHex-Kern und validierten Daten unter Linux/WSL ausführen.
- [ ] Brain-Profiling: Python-/Brian2-Verwaltungsaufwand, Stepgröße und Monitoring
  untersuchen; Modelländerungen separat messen und biologisch begründen.
- [ ] Längere Läufe prüfen: RAM-Wachstum, Spike-Monitor, Reaktionsfähigkeit nach Ruhe.

Ein Abstandssignal als `visual_input` ist eine technische Annäherung,
keine Simulation eines vollständigen Fliegenauges.

## Sobald die Hardware verfügbar ist

- [ ] Pi 3B+ mit 64-Bit-OS einrichten; Python-/Paketkompatibilität prüfen.
- [ ] Gleichen Referenzcommit und echte Daten auf dem Pi testen.
- [ ] Takt, Temperatur, Stromversorgung, CPU, RAM und Step-Laufzeiten protokollieren.
- [ ] Zwischen ToF/Laser und Ultraschall wählen; Messrauschen und Annäherungsgeschwindigkeit kalibrieren.
- [ ] LED oder einen anderen geeigneten einfachen Ausgang festlegen und separat prüfen; bei LED Vorwiderstand und GPIO-Grenzwerte beachten.
- [ ] Prüfen, ob der gewählte Ausgang die schulische Aktoranforderung erfüllt.
- [ ] Hardwareadapter koppeln; Auslösung muss von der SNN-Ausgabe abhängen.
- [ ] Sensorlatenz, Brain-Zeit, Ausgangslatenz, End-to-End-Reaktion und Fehlalarme messen.
- [ ] Schaltplan, Quellen, Eigenleistung und Abschlussdokumentation ergänzen.

Es existiert derzeit keine eigene Hardwaresteuerung und kein auf dem Pi
validiertes Echtzeitsystem. Kamera und Servo gehören nicht mehr zur aktuellen
Planung; die konkrete Sensor- und Ausgangswahl bleibt offen. Daten und
Upstream-Code werden nicht in dieses Repository kopiert; Messberichte und
eigene Prüfwerkzeuge sind enthalten.
