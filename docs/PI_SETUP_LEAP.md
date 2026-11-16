# Raspberry Pi und Leap Motion: Einrichtungs- und Prüfplan

Stand: 16.11.2026. Das ist ein Arbeitsplan, keine bestätigte Pi- oder
Hardwareinstallation. Noch ist weder ein Raspberry Pi noch ein Leap-Motion-
Controller mit diesem Projekt getestet.

## Was für den Leap Motion bekannt ist

Der Leap Motion ist ein optischer Hand- und Fingertracker. Er liefert
Handpositionen und Tracking-Frames, aber keine allgemeine Abstandsmessung wie
ein ToF- oder Ultraschallsensor. Für einen ersten Versuch kann eine definierte
Handbewegung als Annäherungsreiz dienen. Das ist eine technische
Ersatzmessung, kein Nachweis für einen späteren Abstandssensor.

Der Betrieb ist nicht grundsätzlich auf Windows beschränkt. Ultraleap nennt
für Linux offiziell Ubuntu 22.04 auf x86_64. Die LeapC-Dokumentation führt
außerdem SDK-Pfade auf Raspberry Pi OS auf, und das offizielle Python-Binding
kennt Linux ARM. Die dort angegebene Liste vorgefertigter Python-Module für
Linux ARM umfasst in Version 5.17 Python 3.8 bis 3.11. Daraus folgt noch keine
bestätigte Kombination aus Raspberry Pi 3B+, dessen 64-Bit-OS, installiertem
Tracking-Service, konkretem Leap-Modell und unserem Python 3.12-Projekt.

Quellen:

- [Ultraleap: Linux-Unterstützung und Pakete](https://docs.ultraleap.com/linux/index.html)
- [Ultraleap: LeapC-SDK-Pfade einschließlich Raspberry Pi OS](https://docs.ultraleap.com/api-reference/tracking-api/leapc-guide.html)
- [Ultraleap: offizielle LeapC-Python-Bindings, ARM- und Python-Versionen](https://github.com/ultraleap/leapc-python-bindings)
- [Ultraleap: Beispiel für Connection und Tracking-Frames](https://github.com/ultraleap/leapc-python-bindings/blob/main/examples/tracking_event_example.py)

## Reihenfolge für den nächsten Agenten

1. **Pi-Grunddaten sichern.** Raspberry Pi OS 64-Bit verwenden und Ausgabe
   dieser Befehle im Arbeitsbericht festhalten:

   ```bash
   cat /etc/os-release
   uname -a
   uname -m
   python3 --version
   free -h
   df -h /
   ```

   Falls Grundwerkzeuge fehlen, installiere sie über die Paketverwaltung:

   ```bash
   sudo apt update
   sudo apt install git python3 python3-venv python3-dev build-essential pkg-config
   ```

   Erwartete Architektur für 64-Bit-ARM ist meist `aarch64`. OS-Version,
   Python, freien RAM und freien Speicher dokumentieren, bevor Pakete
   installiert werden.

2. **Hardwaremodell identifizieren.** Modell/Generation des Leap-Controllers
   vom Gehäuse oder Beleg ablesen. Unterschiedliche Generationen können
   andere Runtime- und USB-Anforderungen haben. Leap zunächst direkt an einen
   Pi-USB-Port anschließen; bei Verbindungsproblemen einen geeigneten,
   ausreichend versorgten USB-Hub oder ein anderes Kabel gegenprüfen.

   Falls das Projekt noch nicht auf dem Pi liegt, den vorhandenen Checkout
   verwenden oder einmalig klonen:

   ```bash
   mkdir -p ~/projects
   cd ~/projects
   git clone https://github.com/dj-nic/neuro-fly.git
   cd neuro-fly
   ```

   Keine zweite Kopie anlegen, wenn bereits am Repository gearbeitet wird.

3. **USB-Erkennung ohne SDK prüfen.** Im Projektverzeichnis:

   ```bash
   python3 scripts/check_leap_motion.py --verbose-usb
   ```

   Das Skript nutzt nur die Python-Standardbibliothek. Es versucht, bekannte
   Leap/Ultraleap-USB-Einträge zu finden und zeigt System, Architektur,
   Python, SDK-Bibliotheken und `leap`-Binding getrennt an. Wird kein Name
   erkannt, `lsusb` vor und nach dem Anstecken vergleichen. USB-Erkennung
   allein beweist nicht, dass der Tracking-Service funktioniert.

4. **Runtime und SDK nur passend zum Modell installieren.** Vor einer
   Installation prüfen, ob der Hersteller für genau dieses Modell und
   Raspberry Pi OS/ARM-Paketquellen, Runtime und Lizenzbedingungen angibt.
   Keine amd64/Ubuntu-Pakete auf ARM installieren. Die allgemeine Ultraleap-
   Linux-Anleitung nennt Ubuntu x86_64; der Raspberry-Pi-SDK-Pfad allein
   garantiert nicht, dass der Tracking-Service auf dem Pi 3B+ unterstützt
   wird. EULA und kommerzielle/nichtkommerzielle Nutzungsbedingungen beachten.

5. **Live-SDK-Test durchführen.** Erst wenn Service und offizielle Python-
   Bindings installiert sind, Hand über dem Sensor bewegen und ausführen:

   ```bash
   python3 scripts/check_leap_motion.py --smoke-seconds 10
   ```

   Erfolg bedeutet, dass die LeapC-Verbindung echte Tracking-Frames erhalten
   hat. `0 Hand-Erkennungen` heißt: Frames kommen an, aber während des Tests
   wurde keine Hand getrackt. USB erkannt bei fehlender Runtime, SDK-Bibliothek,
   Binding, Serviceverbindung oder Frames jeweils als eigenen Fehler
   protokollieren. Exitcode `2` bedeutet, dass der angeforderte Live-Test nicht
   bestätigt werden konnte.

6. **Ergebnis pro Ebene festhalten:**

   | Ebene | Nachweis |
   |---|---|
   | USB | Gerät erscheint in sysfs/`lsusb` oder Windows-Geräteliste |
   | Runtime/SDK | LeapC-Bibliothek am installierten Ort gefunden |
   | Python | passendes `leap`-Binding importierbar |
   | Verbindung | Verbindung zum Ultraleap-Tracking-Service geöffnet |
   | Tracking | Tracking-Frames und bei Handbewegung mindestens eine Hand empfangen |
   | Projekt | Leap-Daten speisen den SNN-Pfad und `escape_magnitude` steuert den Mock-Ausgang |

   Nur die letzte Ebene ist ein Projekt-End-to-End-Test. Keine Ebene auf Basis
   eines Screenshots, eines USB-Eintrags oder eines übersprungenen Tests als
   bestanden ausgeben.

7. **Leap-Eingabe an den bestehenden Sensoradapter anbinden.** Zuerst bei
   fester Geräteausrichtung Rohposition, Zeitstempel, Frame-ID, Handanzahl und
   Trackingverlust protokollieren. Dann eine Achse/Kalibrierung für eine
   reproduzierbare Handannäherung auswählen. Koordinatenrichtung nicht
   ungeprüft annehmen. Keine Hand, ungültige oder veraltete Frames müssen einen
   sicheren Nullreiz erzeugen und den Ausgang sperren. Die Ausgabe muss weiter
   vom neuronalen `escape_magnitude` kommen, nicht direkt von einer
   Positionsschwelle.

8. **Falls Runtime nur auf einem Windows-PC funktioniert:** Leap auf dem PC
   betreiben und zunächst nur einen normierten Reiz samt Zeitstempel an den Pi
   übertragen. Auf dem Pi SNN und Ausgang ausführen. Netzwerkverzögerung,
   Verbindungsverlust und veraltete Werte messen und sicher behandeln. Das als
   PC-Sensor/Pi-Ausführung kennzeichnen; es belegt keine direkt am Pi
   angeschlossene Leap-Hardware. Mit der Schule klären, ob diese Aufteilung für
   den Hardwareanteil zählt.

## Pi und neuronaler Kern einrichten

Das vorhandene `requirements-dev.lock` ist der x86_64-Entwicklungsstand. Das
Skript `scripts/setup.sh` installiert diesen vollständigen Lock und bezieht
fehlende Daten; weder dieser vollständige Installationsweg noch die
ARM-Paketkombination sind auf einem Pi 3B+ bestätigt. Daher:

1. Vor einer Installation die tatsächlichen Imports von `snn_brain.py` im
   festgehaltenen Referenz-Checkout prüfen. Prüfen, welche Wheels für
   Raspberry Pi OS, ARM64 und die Pi-Python-Version verfügbar sind.
2. Für Pi-Experimente eine eigene virtuelle Umgebung anlegen. Die
   System-Python-Installation nicht überschreiben und nicht `sudo pip`
   verwenden. Beispiel:

   ```bash
   mkdir -p ~/venvs
   python3 -m venv ~/venvs/neuro-fly-pi
   source ~/venvs/neuro-fly-pi/bin/activate
   python -m pip --version
   ```

   Erst nach Prüfung der ARM-Kompatibilität gezielt Pakete in diese Umgebung
   installieren.
3. Daten bevorzugt auf einem Entwicklungsrechner mit dem unveränderten
   Upstream-Skript abrufen und nach einer Integritäts-/Strukturprüfung zum Pi
   übertragen. Keine fremden Connectome-Dateien ins Git-Repository committen.
4. Nur die benötigten Laufzeitpakete installieren; `vfb-connect` und
   Download-/Analysepakete müssen nicht auf dem Pi laufen, wenn die Daten
   übertragen werden.
5. Referenzcommit `5d1052b995db12fa1baf8d42f6a94c3f0695817d` und echte Daten
   verwenden. `scripts/validate_brain.py` ausführen, danach den SNN ohne
   Sensor und Ausgang messen. Import- oder Installationsfehler nicht mit
   Dummy-Daten umgehen.
6. Für denselben Stimulus Initialisierungszeit, Brain-Step-Zeit, CPU, Peak-RAM,
   OS, Python, Architektur und Backend notieren. Simulationszeit von Wandzeit
   trennen. Erst danach Leap-Sensor und physischen Ausgang einzeln prüfen und
   koppeln.

Wenn der Pi-SNN-Test eine ARM-spezifische Abhängigkeitsdatei oder ein
Installationsskript erfordert, diese erst nach erfolgreichem Versuch erstellen
und die nachgewiesenen Paketversionen samt Befehlen in `STATUS.md` festhalten.
Die Sensorwahl bleibt vorläufig; Leap Motion ersetzt nicht automatisch den
noch zu entscheidenden Abstandssensor oder den schulisch geforderten Aktor.
