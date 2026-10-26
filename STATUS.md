# Projektstand und offene Aufgaben

Stand: 26.10.2026. Projekt: `dj-nic/neuro-fly`, Arbeitstitel FlyBrain Reflex.

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
Reaktion enthält eine synthetische Reizrampe, keine reale Sensor-/Servolatenz.
Das Ziel einer Reaktion unter einer Sekunde ist für die Hardware unbestätigt.

## Nächste Schritte ohne Hardware

- [ ] Lizenztext und Attribution mit NeuroHex klären, bevor Code übernommen wird.
- [ ] Datenprovenienz, Filter, Abrufzeitpunkt und Weitergabebedingungen nachvollziehbar sichern.
- [ ] Kern-Schnittstelle festlegen; fehlende/ungültige Daten im späteren Produkt hart ablehnen.
- [ ] Sensoradapter für normiertes `looming_strength` entwickeln, zunächst mit Testwerten.
- [ ] Mock-Servo mit Schwellwert, Hysterese und Cooldown implementieren.
- [ ] Eigene Kopplung Sensor → SNN → Aktor mit gezielten Verhaltenstests absichern.
- [ ] Brain-Profiling: Python-/Brian2-Verwaltungsaufwand, Stepgröße und Monitoring
  untersuchen; Modelländerungen separat messen und biologisch begründen.
- [ ] Längere Läufe prüfen: RAM-Wachstum, Spike-Monitor, Reaktionsfähigkeit nach Ruhe.

Ein Abstandssignal als `visual_input` ist eine technische Annäherung,
keine Simulation eines vollständigen Fliegenauges.

## Sobald die Hardware verfügbar ist

- [ ] Pi 3B+ mit 64-Bit-OS einrichten; Python-/Paketkompatibilität prüfen.
- [ ] Gleichen Referenzcommit und echte Daten auf dem Pi testen.
- [ ] Takt, Temperatur, Stromversorgung, CPU, RAM und Step-Laufzeiten protokollieren.
- [ ] Sensor auswählen, bevorzugt VL53L0X; Messrauschen und Annäherungsgeschwindigkeit kalibrieren.
- [ ] Servo mit geeigneter Stromversorgung separat testen; mechanisch sichere Positionen bestimmen.
- [ ] Hardwareadapter koppeln; Auslösung muss von der SNN-Ausgabe abhängen.
- [ ] Sensorlatenz, Brain-Zeit, Aktorlatenz, End-to-End-Reaktion und Fehlalarme messen.
- [ ] Schaltplan, Quellen, Eigenleistung und Abschlussdokumentation ergänzen.

Es existiert derzeit keine eigene Hardwaresteuerung und kein auf dem Pi
validiertes Echtzeitsystem. Daten und Upstream-Code werden nicht in dieses
Repository kopiert; Messberichte und eigene Prüfwerkzeuge sind enthalten.
