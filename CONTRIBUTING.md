# Zu neuro-fly beitragen

Das Projekt befindet sich in der Vorbereitung ohne Hardware. Gute erste
Beiträge sind nachvollziehbare Messungen, Dokumentationskorrekturen und
kleine Adapter mit klaren Schnittstellen. Offene Aufgaben: [STATUS.md](STATUS.md).

## Entwicklung

1. [Setup in der README](README.md#schnellstart) ausführen.
2. NeuroHex als separaten, unveränderten Referenz-Checkout behalten.
3. Eine überschaubare Änderung entwickeln und passende Checks ausführen.
4. Im Pull Request Verhalten, Validierung und verbleibende Grenzen beschreiben.

Cloud-Tasks laufen bereits isoliert. Bestehende Checkouts verwenden und keine
zusätzlichen Git-Worktrees ohne ausdrücklichen Auftrag erstellen.

## Anforderungen an Messungen und Änderungen

- **Daten:** Quelle, Referenzcommit, Filter und neuronale Gruppen nennen.
  Keine Dummy-Ergebnisse als biologische Messung darstellen.
- **Messungen:** CPU/Board, OS, Python-/Paketversionen, Backend, Stimulus,
  Wiederholungen und Messgrenzen dokumentieren. Kalte Kompilierung und
  laufende Simulation unterscheiden.
- **Hardware:** Mock-Läufe, Cloud-Budgets und echte Pi-Messungen kennzeichnen.
  Eine Sysbench-Übereinstimmung ist keine ARM-Emulation.
- **Modell:** Parameteränderungen und Auswirkungen auf Reflexverhalten,
  Laufzeit und RAM begründen.

Der funktionale Check `scripts/validate_brain.py` braucht echte Daten und prüft
35 Schritte mit Ruhe- und Fluchtverhalten, siehe README. Schnelle Unit-Tests
laufen mit `python -m unittest discover -s tests/unit -v`; der separate
Integrationstest benötigt den gepinnten Referenz-Checkout und echte Daten unter
Linux/WSL. Neue Adapter sollten gezielte Verhaltenstests erhalten. Eine
automatisierte CI-Suite ist noch nicht eingerichtet.

## Dateien und Quellen

Keine virtuellen Umgebungen, heruntergeladenen Connectome-Daten, Caches oder
Sysbench-Binärdateien committen. Abgeleitete Messberichte dürfen unter
`results/` liegen, wenn Quelle und Methodik dokumentiert sind.

Vor Übernahme fremden Codes Lizenz und Attribution klären. Für dieses
Repository wurde noch keine eigene Open-Source-Lizenz festgelegt.

## Fehler und Ideen

Für Probleme die [Fehlervorlage](https://github.com/dj-nic/neuro-fly/issues/new?template=bug_report.yml)
verwenden. Für Adapter, Messungen oder Funktionen gibt es eine
[Ideenvorlage](https://github.com/dj-nic/neuro-fly/issues/new?template=feature_request.yml).
Bitte keine Zugangsdaten oder privaten Umgebungswerte in Logs veröffentlichen.
