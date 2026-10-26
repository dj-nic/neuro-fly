# FlyBrain Reflex / neuro-fly

Ein geplanter Demonstrator auf Raspberry Pi 3B+: Ein Abstandssensor liefert
einen Annäherungsreiz an ein neuronales Modell. Erst dessen motorische Ausgabe
soll eine kurze Servo-Fluchtbewegung auslösen. Hardware ist noch nicht vorhanden.

**Stand und nächste Schritte:** [STATUS.md](STATUS.md).
Die vorhandenen Arbeiten prüfen bisher den separaten NeuroHex-Referenzkern,
noch keine eigene Sensor–SNN–Servo-Steuerung.

## Struktur

- `scripts/`: eigener Daten-/Brain-Prüfer und CPU-Budget-Limiter.
- `requirements-dev.lock`: exakt installierte Python-Versionen des Cloud-Tests.
- `docs/UMSETZUNG.md`: ursprüngliche Planung, mit Hinweis auf den aktuellen Stand.
- `docs/PI_3B_PROXY.md`: Quellen, Methode, Messwerte und Grenzen der CPU-Drosselung.
- `results/`: archivierte Messdaten ohne Connectome-Datendateien.

NeuroHex bleibt neben diesem Repository; es wurde kein Upstream-Anwendungscode
übernommen. Referenz: https://github.com/shakeabhishek/project-neurohex,
Commit `5d1052b995db12fa1baf8d42f6a94c3f0695817d`.
Upstream nennt MIT, enthielt aber keine eigenständige LICENSE-Datei.
Vor späterer Codeübernahme Lizenztext und Attribution klären.

## Hardwarefreier Test unter Linux

Voraussetzungen: Git, Python 3.12 mit `venv`, GCC/G++, Internet für PyPI,
GitHub und die öffentlichen Virtual-Fly-Brain-Dienste. Diese Paketkombination
ist auf Cloud-x86_64 getestet; ARM/Pi-Kompatibilität ist noch offen.
Das Setup installiert ausschließlich die für Datenabruf und Brain-Test
verwendeten Pakete, keine Kamera-/18-Servo-Abhängigkeiten.

```bash
bash scripts/setup.sh
```

Das Skript verwendet oder erstellt `../neurohex-reference` am festgehaltenen
Commit, installiert die Pakete in `.venv`, beschafft bei fehlenden Dateien
Connectome-Daten und prüft den Brain. Existierende abweichende Referenzstände
werden nicht zurückgesetzt. Optional sind `REFERENCE_DIR` und `VENV_DIR` setzbar.
Jeder Cloud-Task ist bereits isoliert; bestehende Checkouts verwenden und keine
zusätzlichen Git-Worktrees ohne ausdrücklichen Auftrag anlegen.

Ein vorhandenes Setup erneut prüfen:

```bash
export CC=gcc CXX=g++ OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export MPLBACKEND=Agg MPLCONFIGDIR="$PWD/artifacts/matplotlib"
.venv/bin/python scripts/validate_brain.py --reference ../neurohex-reference --output artifacts/benchmark.json
```

Die Prüfung akzeptiert keine Dummy-Daten, vergleicht Matrix und Verbindungsliste
und verlangt einen ruhigen Ausgang ohne Reiz sowie einen Fluchtwert >0,5 bei
Annäherung. Ein Lauf enthält 35 Schritte à 20 ms. Fehler führen zu einem
Exitcode ungleich null; Python nicht mit `-O` starten, da Prüfungen Assertions nutzen.
Das bestätigt interne Konsistenz und Modellreaktion, keine unabhängige biologische
Vollständigkeit. Generierte Daten, Umgebungen und Caches werden nicht committed.

## Bisheriges Ergebnis

992 echte Neuronen, 1308 gerichtete Verbindungen; neun Cloud-Budget-Läufe
bestanden die Reflexprüfung. Die Pi-Kalibrierung blieb wegen schwankender
Cloud-Leistung erfolglos. Ein CPU-Budget ist keine Pi-Emulation.
Siehe [Messbericht](docs/PI_3B_PROXY.md) und [JSON-Messreihe](results/cloud-pi-budget-2026-10-26.json).
