# Raspberry Pi 3B+: Online-Referenzen und gedrosselter Cloud-Test

Recherche und Messung: 26.10.2026. Dies ist ein CPU-Budget-Test auf x86_64,
keine Messung auf einem Raspberry Pi und keine ARM-Emulation.

## Dokumentierte Referenzen

1. Herstellerdaten: https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/
   nennt vier Cortex-A53-Kerne mit 1,4 GHz und 1 GB LPDDR2-RAM.
2. https://leoncode.co.uk/articles/raspberry-pi-benchmarks/ dokumentiert für
   „Raspberry Pi 3+“, in der Spezifikation ausdrücklich „Model B Plus Rev 1.3“,
   1,4 GHz, 1 GB, 64-Bit-Bookworm:
   **687,45 Ereignisse/s auf einem Kern**, 2459,22 auf vier Kernen.
   Test: Sysbench **1.0.20**, Primzahlgrenze **10000**,
   `sysbench cpu --threads=1 --time=60 run`.
   Die Seite nennt keine Streuung oder belastbaren Fehlergrenzen für diesen Wert.
3. https://www.jeffgeerling.com/blog/2018/raspberry-pi-3-b-review-and-performance-comparison/
   zeigt die Bedeutung der Stromversorgung: Ein älterer Vier-Thread-Sysbench-Test
   mit Primzahlgrenze 2000 brauchte zunächst 6,9920 s, mit geeigneter Versorgung
   3,1718 s. Diese ältere Messung wird **nicht** zur Kalibrierung verwendet;
   Version, Parameter und Betriebssystem sind nicht mit dem gewählten Test identisch.

Eine andere gefundene Sysbench-Anleitung von Pi bits nennt 580,36 Ereignisse/s
bei Primzahlgrenze 20000, identifiziert aber das Pi-Modell nicht ausreichend.
Dieser Wert wird deshalb ebenfalls nicht als Pi-3B+-Referenz verwendet.

## Methode

- Tatsächliche CPU: Intel Xeon Platinum 8573C, Cloud-VM, x86_64.
- Debian-Paket Sysbench 1.0.20+ds-7 und benötigte Bibliotheken lokal entpackt,
  ohne globale Installation. Paketdownloads durch APT anhand signierter
  Debian-Repository-Metadaten geprüft; TLS- und Signaturprüfung blieben aktiv.
- Derselbe CPU-Test mit einem Thread und explizit Primzahlgrenze 10000.
  Je Einzelmessung 10 s statt der 60 s der Quelle; mehrere Wiederholungen.
- Zielprozess und seine Kinder auf eine CPU gebunden. NumPy/BLAS/OpenMP
  auf einen Thread begrenzt. Die übrigen Pi-Kerne werden nicht mitgerechnet,
  weil hier die weitgehend serielle Brain-Schleife untersucht wird.
- `cpu_limit.py` hält die Prozessgruppe periodisch mittels SIGSTOP/SIGCONT an
  (10-ms-Periode). Der Regler selbst darf auf den anderen CPUs laufen.
  Der Duty-Anteil bezeichnet ein nominelles Zeitbudget, keine CPU-Taktfrequenz.
- Anpassung des Zeitbudgets anhand der tatsächlich gemessenen Sysbench-Rate.
  Die erste Kalibrierung wurde verworfen: Die Kontrollwerte 1002,85 / 998,81 /
  1040,79 Ereignisse/s lagen deutlich über dem Ziel 687,45.
- Je drei Brain-Läufe auf einem Kern ohne zusätzliches Zeitlimit sowie mit
  zwei unterschiedlichen CPU-Budgets. Es läuft jeweils der unveränderte Upstream-Brain mit Cython,
  echten 992 Neuronen und 1308 gerichteten Verbindungen.
- Je Lauf 35 Schritte à 20 ms: Ruhe, ansteigender Reiz und starker Reiz.
  Prüfung: Ruheausgabe 0, Fluchtwert bei Reiz >0,5. Keine Dummy-Daten.
- Kalter Compilerstart wird nicht als Steady-State-Leistung ausgegeben.
  Importzeit liegt außerhalb der Step-Messung. Prozessstart und Importe sind
  unter der Drosselung ebenfalls verlangsamt.

## Grenzen der Übertragbarkeit

Eine passende Sysbench-Rate gleicht nur einen synthetischen Integer-Test an.
Python, Cython, Gleitkomma, Speicherbandbreite, Cachegrößen, ARM/NEON gegenüber
x86/SIMD und Betriebssystem-Scheduling können ganz andere Verhältnisse haben.
Die Cloud-Maschine zeigte deutliche Leistungsschwankungen. Die Messwerte sind
daher ein nachvollziehbarer Belastungstest mit einer Pi-Referenz als Anker,
keine Laufzeitvorhersage mit garantierter Genauigkeit.

Die künstlichen Pausen erzeugen bis zu etwa eine Periode zusätzliche
Scheduling-Latenz. Sie gehören zum Testverfahren und sind kein Modell des
Pi-Schedulers. Keine RAM-Begrenzung, keine Emulation von SD-Karte, GPIO,
Sensor/Servo, Kühlung, Unterspannung oder thermischer Drosselung.
Peak-RSS betrifft den Testprozess einschließlich Python/Brian2, nicht den
gesamten RAM-Bedarf von Betriebssystem und späterer Roboteranwendung.

Der gemessene Zeitraum „Annäherung bis Fluchtschwelle“ beginnt beim ersten
positiven synthetischen Eingang und endet bei `escape_magnitude > 0.5`.
Er enthält die Stimulusrampe, Rechenzeit und Scheduling, aber keine physische
Sensor- oder Aktorlatenz. Er ist abhängig von diesem Testreiz.

## Reproduktion und archivierte Daten

Der portable Basistest ist in der [README](../README.md) beschrieben.
Die historische Messreihe ist als
[`results/cloud-pi-budget-2026-10-26.json`](../results/cloud-pi-budget-2026-10-26.json)
archiviert; sie enthält Kalibrierung, Kontrollmessungen und alle neun Einzelläufe.
Die damaligen Cloud-Rohlogs und automatisch entpackten Sysbench-Binärdateien
werden nicht versioniert.

Für neue Budgettests unter Linux aus dem Projektverzeichnis, nach Einrichtung:

```bash
export CC=gcc CXX=g++
export MPLBACKEND=Agg MPLCONFIGDIR="$PWD/artifacts/matplotlib"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
python3 scripts/cpu_limit.py 0.35 .venv/bin/python scripts/validate_brain.py --output artifacts/budget-35.json
python3 scripts/cpu_limit.py 0.22243338795351664 .venv/bin/python scripts/validate_brain.py --output artifacts/budget-22.json
```

Das sind Wiederholungen der Zeitbudgets; die Prozentwerte kalibrieren eine neue
Maschine nicht automatisch auf einen Pi. Mit installiertem Sysbench 1.0.20
vorher und nachher dasselbe Budget mit
`sysbench cpu --threads=1 --cpu-max-prime=10000 --time=10 run` kontrollieren.
Die Quelldateien des Gehirns werden nicht verändert. Es werden keine dauerhaften
CPU-Limits gesetzt. Der Limiter benötigt Linux, `taskset` und POSIX-Signale.

## Tatsächliche Ergebnisse

Alle neun Brain-Läufe bestanden die Daten- und Reflexprüfungen. Je Lauf wurden
35 Schritte ausgeführt: insgesamt **315 Schritte**, ausschließlich echte Daten.
Alle Läufe nutzten einen warmen Cython-Cache. Drei Wiederholungen pro Bedingung.

| CPU-Budget | Sysbench vorher/nachher (Ereignisse/s) | Mittlerer 20-ms-Step in ms (Spanne der Laufmittel) | Wandzeit/simulierte Zeit, Mittel | Reiz bis Fluchtschwelle in s | höchster Prozess-RSS in MiB |
|---|---:|---:|---:|---:|---:|
| 1 Kern, ohne Zusatzlimit | 1398.21 / 2031.02 | 69.5 (64.9–73.6) | 3.62 | 0.51–0.80 | 139.8 |
| 22.24 % eines Kerns | 474.23 / 408.82 | 554.5 (500.9–632.5) | 28.28 | 4.51–5.15 | 139.8 |
| 35.00 % eines Kerns | 608.36 / 902.52 | 310.3 (268.5–366.7) | 15.92 | 2.63–3.60 | 139.8 |

Der Zeitquotient berücksichtigt die gesamte 700-ms-Simulationsschleife, also
auch Pausen zwischen den Steps. Ein Wert >1 bedeutet langsamer als Echtzeit.
Die mittlere Stepzeit lässt den ersten Schritt je Lauf aus; die Quotienten
und Reflexlatenzen enthalten ihn, sofern er im jeweiligen Messfenster liegt.

**Kalibrierung nicht bestanden:** Die zuletzt drei Kontrollmessungen bei
festem Budget lagen bei 387.73, 415.03, 418.20 Ereignissen/s.
Das Ziel war 687,45 ±10 %. Auch die Kontrollmessungen um die Brain-Läufe zeigen
die wechselnde Cloud-Leistung. Die Bedingungen dürfen daher nicht als
„Pi-3B+-Geschwindigkeit“ bezeichnet werden. Sie sind reale Messungen unter
den angegebenen CPU-Zeitbudgets. Aus Sysbench lässt sich keine sichere
Ober- oder Untergrenze für Brian2 auf dem Pi ableiten.

Für den vorhandenen unveränderten Brain ist ein 20-ms-Echtzeittakt in diesen
gedrosselten Tests nicht erreicht. Der biologische Datenpfad und die
Reflexfunktion bleiben unter CPU-Knappheit funktionsfähig. Das 1-s-Ziel kann
aus diesem synthetischen Cloud-Test nicht für die reale Hardware zugesagt werden.
Für eine belastbare Pi-Aussage denselben Datenstand und dasselbe Stimulusprofil
auf dem echten Pi 3B+ unter 64-Bit-OS messen; Stromversorgung, Temperatur,
Takt, RAM und Softwareversionen dabei protokollieren.

Maschinenlesbare Ergebnisse: [archivierte JSON-Messreihe](../results/cloud-pi-budget-2026-10-26.json).
Die Kalibrierung ist darin ausdrücklich als nicht bestanden markiert.
