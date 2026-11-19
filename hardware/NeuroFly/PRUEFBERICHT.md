# NeuroFly · Konstruktionsprüfung

Geprüfter Aufbau: WS-15299, Pi 3 Model B+, Adafruit 5396, 150-mm-Arm, 6 mm Armstärke, 15° Ruhe und 75° Flucht. Alle Angaben beziehen sich auf die ausgelieferten Nennmaße. Fertigungsstreuung, Reibung, Servoelektronik und Kabelverformung sind Gegenstand der Inbetriebnahme.

## Bewegungsraum und Montage

| Prüfung | Ergebnis im Modell |
|---|---|
| Kinematik | Die Mitte der beiden Spitzenbohrungen beschreibt einen Kreis von 150 mm Radius. Von 15° auf 75° gewinnt sie 106,1 mm Höhe und bewegt sich 106,1 mm nach hinten. Die Bauchfläche der Fliege sitzt zusätzlich 12 mm oberhalb der Armlinie und folgt einer leicht versetzten Bahn. |
| Kollisionslauf | Die exportierten Druckteile wurden aus ihrer Drucklage in die Einbaulage zurücktransformiert. Geprüft wurden 121 Stellungen im Abstand von 0,5°. Zwischen bewegter Gruppe und feststehendem Modell ergab sich kein Überschneidungsvolumen über der numerischen Prüfschwelle von 0,005 mm³. |
| Einbezogene Hardware | Servo mit Laschen und Nase, angenommene Doppelhornkontur, Außenhüllen der bewegten Schrauben und Muttern, Lager, glatter Stift, Anschlagbolzen, Gummihülsen, Pi-Platine, vereinfachte Pi-Buchsen, Sensorplatine und Steckerkörper. Die koaxiale 5-mm-Passung zwischen Stift und Lager wurde separat bei gleicher Facettenausrichtung geprüft, weil der reale runde Stift rotationssymmetrisch ist. |
| Statische Verschraubung | Die festen Bauteile überdecken einander im Nennmodell nicht. Bei den bewegten Teilen verbleiben gezielte Überdeckungen der nominellen Schraubengewinde mit den gedruckten Kernlöchern im Sattel und im Fliegenkörper. |
| Arm und Puffer | Im Normalhub beträgt der kleinste Abstand des Arms zur Deckeloberseite etwa 31,5 mm. Am unteren Softwareende verbleiben 4,2 mm zur jeweiligen Pufferoberfläche, am oberen 4,7 mm. Beim Weiterschwenken bis zum ersten Kontakt, geprüft in 0,25°-Schritten, ergeben sich rund 6,25° und 84,75°. Weiche Hülsen verformen sich nach diesem Erstkontakt. |
| Weg bis zum Puffer | Ein zweiter Lauf zwischen 6,25° und 84,75° in 0,25°-Schritten überprüfte die harten Strukturen ohne Silikon. Auch auf dem Weg vom Softwareende bis zum jeweiligen Puffer trat im Nennmodell kein harter Kontakt der bewegten Gruppe auf. |
| Bauraum | In Ruhe ragt die bewegte Gruppe rund 66 mm über die Front hinaus. Die oberste Stelle liegt bei ca. 180 mm, in Fluchtstellung bei ca. 287 mm ab Gehäuseunterseite. Die Flügel liegen quer zwischen X = 87,4 und 158,6 mm. |
| Optik | Der Sensor liegt bei X = 44 mm, Z = 33 mm. Ein nach vorne gerichteter Prüfkegel mit 9° Halbwinkel und 82 mm Länge überdeckt den gesamten vorne erreichbaren Auslegerbereich. Keine Schnittmenge mit den bewegten Teilen in den untersuchten Stellungen. Das reale Rücksignal hängt auch von Tischplatte, Licht und Hand ab. |
| Elektronik | 15 mm Auflagehöhe des Pi ergeben 11,8 mm zwischen Platinenunterseite und Innenboden. Die hohen USB-Buchsen liegen unter Z = 34 mm. Innen liegt die Deckelunterseite bei 60 mm, die Unterseite der Rippen bei 56 mm. HDMI und Micro-USB sind über ein gemeinsames Heckfenster erreichbar. |
| Gegenlager | Der 16-mm-Stift steckt 7 mm in der Nabe und durchspannt die 5-mm-Lagerbreite. Die Nabe wahrt axial 1 mm Abstand zum Lager. Der ruhende Außenring sitzt an der Schulter. Die Ausrichtung beider Füße muss am gelieferten Servo spannungsfrei erfolgen. |
| Einbauweg Pi | 93 Positionen mit Platine und Buchsenkörpern. Um 4 mm nach rechts und zur Front versetzt absenken, 0,5 mm über den Domen zur Ecke verschieben, anschließend auflegen. Das linke Gehäusefenster gibt den seitlichen Einfahrweg frei. |
| Einbauweg Antrieb | Servokörper axial durch die Laschenplatte in 111 Positionen geprüft. Anschließend Lagerschild mit eingesetztem Lager axial auf den 5-mm-Stift, geprüft über 24 mm in 97 Positionen. Kein Volumenkonflikt oberhalb der Prüfschwelle. |
| Deckelwartung | An allen fünf Deckelschrauben passt in Ruhestellung ein gerader Ø-5-mm-Werkzeugschaft über 180 mm von oben an den Kopf. Die hintere Schraube liegt zwischen Servobock und Schutzscheibe. Für die Fußmuttern wird der Deckel abgenommen. |

Die Prüfung erfasst diskrete Positionen mit ideal starren Bauteilen. Das Hornmodell vereinfacht das Original auf Befestigungs- und Bewegungskontur. Die Schrauben besitzen keine modellierten Gewindegänge. Drucktoleranzen, eine am Horn abweichende Zahnteilung, Fertigungsfehler, exakte Steckerummantelungen, Überschwingen, Quetschkräfte und Dauerfestigkeit wurden nicht experimentell bestimmt.

## Masse und Antrieb

Für eine obere Abschätzung wurden alle bewegten Druckteile als vollständig mit PETG der angenommenen Dichte 1,27 g/cm³ gefüllt gerechnet. Der tatsächliche Slicerwert hängt vom Profil ab.

| Bestandteil | Rechnerische Vollmaterialmasse |
|---|---:|
| Arm | 16,23 g |
| Körper mit integriertem Kopf | 7,82 g |
| Beide Flügel zusammen | 1,33 g |
| Sattel | 2,69 g |
| Hornadapter und Stiftnabe zusammen | 5,92 g |
| **Bewegte Druckteile gesamt** | **33,98 g** |

Fliege mit Flügeln und ohne Sattel: rund 9,15 g. Die montierte Einheit wiegen. Für die folgende Rechnung sind zusätzlich bis zu 6 g Kaufteile an höchstens 180 mm Radius und 12 g an höchstens 20 mm Radius angesetzt. Bei Überschreitung oder Verlängerung des Arms die Lastrechnung erneuern.

Für jedes Druckteil wurde seine gesamte Masse an den größten Achsabstand seiner STL-Eckpunkte gesetzt. Mit den beiden Kaufteilreserven ergeben sich obere Rechenwerte von **0,00601 kg·m** für das erste Massenmoment und **0,000953 kg·m²** für das Trägheitsmoment um die Servoachse. Daraus folgen bis zu **0,059 N·m** statisches Gewichtsmoment.

Für den 60°-Hub in 0,45 s mit der in der Anleitung angegebenen Rampe liegt die rechnerische Spitzengeschwindigkeit bei 250°/s und die Spitzenbeschleunigung bei rund 29,9 rad/s². Das zusätzliche Trägheitsmoment als Antriebslast beträgt rund **0,0285 N·m**. Die konservative Summe aus Beschleunigungs- und Gewichtsmoment beträgt **0,088 N·m** vor Reibung und Getriebeverlusten. Die von Waveshare genannten 9 kgf·cm bei 4,8 V entsprechen ca. 0,88 N·m. Die ebenfalls genannten 0,19 s pro 60° sind ein Servo-Kennwert. Daraus folgt kein garantierter Fahrverlauf unter Last. [Waveshare MG996R, technische Daten](https://www.waveshare.com/product/robotics/motors-servos/servos/mg996r-servo.htm)

## Stand und Abschalten

Für die angenommene Rampe ergibt sich aus dem ersten Massenmoment und den Maxima von Winkelbeschleunigung und Winkelgeschwindigkeit eine konservative dynamische Reaktionskraft von rund 0,294 N. Bei der 113 mm hohen Querachse und maximal ca. 100 mm Abstand zur vorderen oder hinteren Kippkante ist ein Hebelarm von 0,152 m konservativ. Zusammen mit dem Antriebslastmoment liefert das eine Momentenabschätzung von rund **0,133 N·m** um diese Kanten. Positive Gewichtswirkung des bewegten Aufbaus am innerhalb der Basis liegenden Drehpunkt ist hierbei unberücksichtigt.

Ein Rechenbeispiel für den frei stehenden Aufbau: Eine **gemessene** feststehende Masse von mindestens 450 g mit Schwerpunktlot mindestens 50 mm innerhalb der vorderen und hinteren Aufstandskante ergibt mindestens **0,221 N·m** rückstellendes Moment. Beim realen Aufbau Masse und Aufstandsfläche kontrollieren. Der Abstand bezieht sich auf die tatsächlichen Fußauflagen. Kabelzug, seitliches Anstoßen, blockierter Arm und harter Anschlag sind in dieser Abschätzung unberücksichtigt. Die drei Bodenbohrungen erlauben die feste Montage für den Schulbetrieb.

Bei Stromausfall bleibt die Fliege am Arm. Aus dem berechneten ersten Massenmoment ergibt sich bei einer Absenkung von 75° bis 6° eine konservative Grenze von etwa 0,071 J frei werdender Lageenergie. Während der Fahrt kommt Bewegungsenergie hinzu. Die gepolsterten Anschläge und die gekapselte Wurzel begrenzen den Weg. Wie schnell das reale Getriebe nachgibt oder ob der Servo beim Einschalten zuckt, muss am Exemplar geprüft werden. Ein Nachweis der Berührungssicherheit für unbeaufsichtigten Betrieb liegt nicht vor.

## STL-Prüfung

Die Binär-STL-Dateien wurden nach dem OpenSCAD-Export erneut eingelesen. Geprüft wurden Dateilänge, Dreieckszahl, zusammenfallende Eckpunkte, gerichtete Kantenpaare, degenerierte Dreiecke, Zusammenhang, Volumen und Außenmaße. Jede Kante gehört zu zwei entgegengesetzt orientierten Dreiecken, jeder Export enthält genau einen geschlossenen Körper mit positivem Volumen. Alle Dateien liegen in Drucklage. Maßstab im Slicer: **Millimeter, 100 %**.

| Datei | Außenmaß X × Y × Z in Drucklage (mm) | Dreiecke |
|---|---:|---:|
| 01_base_bottom.stl | 200,00 × 145,00 × 60,00 | 10196 |
| 02_base_lid.stl | 200,00 × 145,00 × 9,00 | 5140 |
| 03_servo_mount_mg996r.stl | 64,00 × 64,00 × 28,00 | 1360 |
| 04_swing_arm.stl | 174,90 × 33,00 × 6,00 | 2944 |
| 05_servo_horn_adapter.stl | 33,00 × 33,00 × 5,00 | 1232 |
| 06_fly_body.stl | 20,17 × 50,35 × 12,68 | 9732 |
| 08_fly_wing_left.stl | 32,10 × 38,40 × 1,45 | 868 |
| 09_fly_wing_right.stl | 32,10 × 38,40 × 1,45 | 868 |
| 10_fly_arm_connector.stl | 18,00 × 18,30 × 18,00 | 904 |
| 11_sensor_mount.stl | 68,00 × 28,00 × 6,00 | 2588 |
| 12_axis_support.stl | 83,35 × 89,00 × 30,00 | 1906 |
| 13_axis_pin_hub.stl | 10,00 × 30,60 × 8,00 | 988 |
| 14_guard_rear.stl | 96,00 × 96,00 × 10,00 | 2392 |
| 15_guard_spacer.stl | 96,00 × 96,00 × 16,00 | 1716 |
| 16_servo_cable_guide.stl | 18,00 × 38,00 × 31,00 | 1128 |
| 21_servo_flange_fit.stl | 64,00 × 32,00 × 3,00 | 968 |
| 22_horn_fit.stl | 33,00 × 33,00 × 5,00 | 1232 |
| 23_bearing_fit.stl | 23,00 × 23,00 × 6,00 | 576 |
| 24_fastener_fit.stl | 52,00 × 19,00 × 5,00 | 1016 |
