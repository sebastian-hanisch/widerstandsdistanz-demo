# Widerstand als Netzmaß – wann sagt er mehr als die zwei Grade?

Konzept-Demo der Reihe „Irrfahrten auf Netzen“ (Streamlit, Teil des Portfolios von Sebastian Hanisch).

Die Demo „Pendelzeit“ zeigt, dass ein Anhang abseits der Strecke die Pendelzeit verlängert und den **effektiven Widerstand R** unverändert lässt, prüft aber nicht, was R über zwei Orte vorhersagt. Diese Demo stellt R bei zufälligem **Kantenausfall** gegen kürzeste Distanz, **min cut** und die zwei Endgrade (die **Isolationsnäherung** kennt zusätzlich die Ausfallrate und ob die zwei Orte benachbart sind) und zeigt, auf welchen Netzen R Nichtnachbarn kaum anders ordnet als die Grade.

Zum Gradterm: Addiert man H(u,v) ≈ 2m/d_v und H(v,u) ≈ 2m/d_u und teilt durch 2m, steht der Gradterm 1/d_u + 1/d_v da: dieselbe Näherung wie in der Demo „Trefferzeit“.

## Warum dieses Problem

Ein Maß, das aus allen Wegen zwischen zwei Orten gerechnet wird, klingt nach der natürlichen Vorhersage dafür, ob die zwei Orte beim Ausfall von Leitungen verbunden bleiben. Es konkurriert aber mit sehr billigen Zahlen: der Distanz, der Zahl der getrennten Wege (min cut) und den zwei Nachbarzahlen. Auf dem Handnetz „zwei Hallen“ (zwei Dreiecke, eine Tür) haben die Paare (0,1) und (0,4) dieselben Grade (2, 2) und damit denselben Gradterm 1; R ist 2/3 gegen 7/3, und bei Ausfallrate 0,15 wird (0,1) in 4,2 % der Fälle getrennt, (0,4) in 21,9 % (exakt über alle 2⁷ Ausfallmuster).

## Modell und Methodik

* **Netz:** ungerichtet, ungewichtet, einfach; jede Kante hat den Widerstand 1 Ohm. R aus dem um J/n verschobenen Laplace (J = Matrix aus Einsen), nur auf zusammenhängenden Netzen (bei Netzen mit Zufall zählt die größte zusammenhängende Komponente).
* **Ausfall:** jede Kante fällt unabhängig mit derselben Wahrscheinlichkeit p aus; Zielgröße ist nur P(s und t getrennt).
* **Wahrheit:** zwei **unabhängige** Stichproben mit je 1 600 Ausfallmustern; die Muster kommen aus SplitMix64 (auf jeder Plattform dieselbe Folge). Auf dem Handnetz und bei „Leitung gegen drei Wege“ exakt.
* **Güte:** Rangkorrelation nach Spearman über 300 zufällige Knotenpaare (auf kleineren Netzen alle). Werte werden vorher auf 9 Stellen gerundet, die Isolationsnäherung vorher logarithmiert. Ist eine Seite konstant, gibt es keinen Wert. **Nicht messbar** ist eine Zelle, wenn in einer Stichprobe mindestens 95 % der Paare denselben Wert haben.
* **Klar** ist ein Abstand R − Gegner nur, wenn er in beiden Wahrheitsstichproben dasselbe Vorzeichen hat und mindestens 0,05 beträgt. Die Korrelation der geraden gegen die ungeraden Proben einer Stichprobe ist **keine Obergrenze**, nur ein Maß der Wiederholbarkeit.
* **Gegner:** kürzeste Distanz; min cut (Maximalfluss je Paar), auch mit der Distanz als Gleichstandsregel; Gradterm 1/d_s + 1/d_t; Isolationsnäherung p^d_s + p^d_t − p^(d_s+d_t−a_st) (a_st = 1 bei Nachbarn), die genaue Wahrscheinlichkeit, dass s oder t keine Kante mehr hat; eigene Ausfallstichproben mit 50 und 200 Proben (unabhängig von der Wahrheit). Keiner dieser Gegner hat eine abgestimmte Stellgröße.
* **Netze:** zwei Gitterhallen a×a (a = 6, 8, 10) mit 1, 2, 4 oder a verteilten Türen in den Zeilen floor((i + 0,5)·a/k) (eine Netzfamilie je k, keine Ergänzung der einen Tür) und ein Hallenverbund (2×2 mit a = 6, 3×3 mit a = 4 und 5); sechs Kontrastfamilien (straßenähnlich: ausgedünnte Delaunay-Triangulierung mit mittlerem Grad 2,8; Gitter mit Löchern; Punktnetz 2D mit Grad 6; Zufallsnetz mit Grad 4; Netz mit Knotenpunkten, Barabási-Albert mit 2 Anschlüssen; zwei Hälften mit 2 Querverbindungen) mit je 10 Netzen; vier dichte Familien (mittlerer Grad etwa 20: Zufallsnetz, Netz mit Knotenpunkten mit 10 Anschlüssen, Punktnetz 5D, zwei dichte Hälften mit 3 Querverbindungen) mit je 6 Netzen. Kontrast und dicht mit 150 Knoten vor der größten Komponente.

## Befunde (gemessen)

Die Tabellenzahlen und die Zählungen über Netz-p-Zellen und Ausbaunetze stehen in `daten/vorgerechnet.json` (erzeugt von `tools/vorrechnen.py`, Zufalls-Seeds in `wdn_tabellen.py`); `tests/test_claims.py` prüft sie gegen diese Datei und rechnet die Datei zum Teil neu (Umfang unter „Verifikation“). Die Handbeispiele (Trennwahrscheinlichkeiten und Ordnungszählungen am Handnetz, die Rechnungen unter „Von Hand“ zu Handnetz und Besen, „Leitung gegen drei Wege“) und die getrennten Rangkorrelationen innen und quer bei den dichten Hälften rechnen die Tests direkt nach. „R vorn“ heißt höhere Rangkorrelation in Wahrheitsstichprobe 1.

**In den 225 gemessenen Netz-p-Zellen der dünnen Netze** (zwei Hallen und Hallenverbund: 45; sechs Kontrastfamilien: 180) ordnet R die Paare **in jeder Zelle besser als die kürzeste Distanz** (klar in 224 von 225). Ob R mehr sagt als die zwei Endgrade, hängt am Netz.

### Zwei Hallen und Hallenverbund (je Zelle p = 0,05 / 0,15 / 0,3; Mittel über je 3 Netze)

| Netz | Distanz | R | min cut | min cut, dann Distanz | Gradterm | Isolation | Stichprobe 200 |
|---|---|---|---|---|---|---|---|
| zwei Hallen, 1 Tür | 0,73 / 0,77 / 0,83 | 0,87 / 0,91 / 0,95 | 0,92 / 0,92 / 0,92 | 0,87 / 0,90 / 0,94 | 0,27 / 0,45 / 0,44 | 0,28 / 0,46 / 0,45 | 0,91 / 0,93 / 0,97 |
| zwei Hallen, 2 verteilte Türen | 0,63 / 0,70 / 0,80 | 0,79 / 0,86 / 0,94 | 0,86 / 0,88 / 0,88 | 0,80 / 0,86 / 0,92 | 0,41 / 0,60 / 0,52 | 0,42 / 0,61 / 0,53 | 0,44 / 0,88 / 0,97 |
| zwei Hallen, 4 verteilte Türen | 0,18 / 0,36 / 0,68 | 0,28 / 0,49 / 0,82 | 0,56 / 0,86 / 0,74 | 0,52 / 0,83 / 0,90 | 0,56 / 0,90 / 0,78 | 0,56 / 0,90 / 0,79 | 0,40 / 0,64 / 0,91 |
| zwei Hallen, a verteilte Türen | 0,24 / 0,36 / 0,58 | 0,36 / 0,50 / 0,74 | 0,62 / 0,86 / 0,83 | 0,57 / 0,80 / 0,89 | 0,64 / 0,89 / 0,86 | 0,63 / 0,88 / 0,87 | 0,46 / 0,63 / 0,87 |
| Hallenverbund | 0,56 / 0,72 / 0,87 | 0,70 / 0,88 / 0,97 | 0,70 / 0,67 / 0,55 | 0,72 / 0,82 / 0,86 | 0,36 / 0,44 / 0,32 | 0,38 / 0,45 / 0,34 | 0,43 / 0,89 / 0,97 |

**Ehrlicher Gegenfall: viele verteilte Türen.** In der Familie „k gleichmäßig verteilte Türen“ ordnen zwei Gradzahlen den Ausfall bei k = 4 (p = 0,05 und 0,15) und bei k = a (alle drei p) im Familienmittel besser als R. Bei k = 4 war der Gradterm bei p = 0,05 und 0,15 in allen 6 Netz-p-Zellen (3 Netze × 2 Ausfallraten) klar vorn; bei p = 0,3 war R in einem der 3 Netze klar vorn, der Gradterm in einem. Bei k = a war der Gradterm in 8 von 9 Netz-p-Zellen klar vorn, in der neunten lag R knapp (nicht klar) vorn. R ist dort **nicht entartet**: seine Rangkorrelation mit dem Gradterm über die Nichtnachbarn ist bei a verteilten Türen 0,49 (a = 6), 0,46 (a = 8) und 0,44 (a = 10). „min cut, dann Distanz“ (ohne p) lag bei 4 und a Türen in 17 von 18 Zellen vor R.

### Kontrastnetze, p = 0,15, je 10 Netze

| Netz | Distanz | R | min cut | min cut, dann Distanz | Gradterm | Isolation | Stichprobe 200 |
|---|---|---|---|---|---|---|---|
| straßenähnlich | 0,52 | 0,87 | 0,86 | 0,89 | 0,63 | 0,64 | 0,98 |
| Gitter mit Löchern | 0,45 | 0,80 | 0,86 | 0,89 | 0,76 | 0,76 | 0,96 |
| Punktnetz 2D | 0,59 | 0,83 | 0,93 | 0,93 | 0,54 | 0,54 | 0,91 |
| Zufallsnetz Grad 4 | 0,49 | 0,94 | 0,96 | 0,95 | 0,93 | 0,94 | 0,89 |
| Netz mit Knotenpunkten | 0,33 | 0,85 | 0,76 | 0,69 | 0,89 | 0,91 | 0,78 |
| zwei Hälften | 0,69 | 0,93 | 0,90 | 0,88 | 0,59 | 0,61 | 0,91 |

### R vorn, gezählt je Familie (alle p, messbare Zellen)

| Netz | gegen Distanz | gegen Gradterm | gegen Isolation | gegen min cut | gegen min cut, dann Distanz | gegen Stichprobe 200 |
|---|---|---|---|---|---|---|
| zwei Hallen, 1 Tür | 9/9 | 9/9 | 9/9 | 3/9 | 8/9 | 1/9 |
| zwei Hallen, 2 verteilte Türen | 9/9 | 9/9 | 9/9 | 3/9 | 5/9 | 4/9 |
| zwei Hallen, 4 verteilte Türen | 9/9 | 2/9 | 2/9 | 2/9 | 1/9 | 1/9 |
| zwei Hallen, a verteilte Türen | 9/9 | 1/9 | 1/9 | 1/9 | 0/9 | 1/9 |
| Hallenverbund | 9/9 | 9/9 | 9/9 | 7/9 | 7/9 | 6/9 |
| straßenähnlich | 30/30 | 26/30 | 26/30 | 16/30 | 15/30 | 1/30 |
| Gitter mit Löchern | 30/30 | 20/30 | 20/30 | 12/30 | 10/30 | 0/30 |
| Punktnetz 2D | 30/30 | 26/30 | 26/30 | 5/30 | 5/30 | 2/30 |
| Zufallsnetz Grad 4 | 30/30 | 22/30 | 17/30 | 7/30 | 12/30 | 24/30 |
| Netz mit Knotenpunkten | 30/30 | 4/30 | 0/30 | 22/30 | 29/30 | 30/30 |
| zwei Hälften | 30/30 | 30/30 | 30/30 | 18/30 | 29/30 | 20/30 |
| Zufallsnetz Grad 20 (dicht) | 12/12 | 0/12 | 0/12 | 8/12 | 7/12 | 12/12 |
| Netz mit Knotenpunkten, 10 Anschlüsse (dicht) | 12/12 | 2/12 | 0/12 | 6/12 | 6/12 | 12/12 |
| Punktnetz 5D (dicht) | 13/13 | 4/13 | 0/13 | 6/13 | 6/13 | 10/13 |
| dichte Hälften | 12/18 | 18/18 | 18/18 | 12/18 | 12/18 | 13/18 |
| dünn zusammen | 225/225 | 158/225 | 149/225 | 96/225 | 121/225 | 90/225 |

Nach dem Klar-Kriterium über die 225 dünnen Zellen: gegen den Gradterm R 118-mal klar vorn, der Gradterm 35-mal; gegen den min cut R 59-mal, der min cut 66-mal; gegen die 200er-Stichprobe R 38-mal, die Stichprobe 70-mal.

* **Keines der Maße ist durchgehend das beste.** Der min cut lag in 129 der 225 dünnen Zellen vor R, die eigene Stichprobe mit nur 200 Proben in 135.
* **Gitter mit Löchern hängt vom Netz ab.** In diesen 10 Netzen war der Gradterm bei p = 0,05 in 6 Netzen klar vorn und R in einem; bei p = 0,15 lag R im Mittel vorn (0,80 gegen 0,76; R in 4 Netzen klar vorn, der Gradterm in 2); bei p = 0,3 war R in allen 10 klar vorn. Für p ≤ 0,15 behauptet die Demo auf dieser Familie keine Richtung.
* **Zufallsnetz mit mittlerem Grad 4:** R und Gradterm liegen im Familienmittel bei jedem p höchstens 0,03 auseinander; R war in keiner der 30 Zellen klar vorn oder klar hinten.
* **Netz mit Knotenpunkten:** der Gradterm lag in 26 von 30 Zellen vor R.
* Die Wiederholbarkeit (Hälfte gegen Hälfte) ist **keine Obergrenze**: der min cut lag in 14 der 45 Hallenzellen und in 46 der 180 Kontrastzellen darüber.

### Leitung gegen drei Wege: R kennt die Ausfallrate nicht

Eine Leitung (R = 1) gegen drei sonst getrennte Wege der Länge 4 (R = 4/3). Bei p = 0,15 ist die Leitung mit 15,00 % getrennt, die drei Wege mit 10,92 %; bei p = 0,3 sind es 30,00 % gegen 43,88 % (exakt, Formel (1 − (1−p)⁴)³ gleich der Aufzählung aller 2¹² Muster). Kein Maß, das p nicht kennt, kann diese zwei Paare bei beiden Ausfallraten richtig ordnen.

Auf dem Handnetz ordnet R jeden Vergleich zweier Paare richtig (eine Tür: 78 richtig, 0 falsch; zwei Türen: 90 richtig, 0 falsch); mit einer Tür tut das auch „min cut, dann Distanz“. Das ist eine Eigenschaft dieses Netzes, kein Satz. Bei einer Tür: Distanz 72 / 0 / 6 (richtig / falsch / gleich bewertet), min cut 54 / 0 / 24, Gradterm 40 / 14 / 24, Isolationsnäherung 64 / 14 / 0; mit zwei Türen sinkt P(0–4) auf 5,5 %, der min cut bewertet 64 von 90 Vergleichen gleich.

### Dichte Netze (150 Knoten, mittlerer Grad etwa 20)

* Bei p = 0,15 war die Trennung auf den drei Familien ohne Engpass in 17 von 18 Netzen nicht messbar.
* p = 0,7 / 0,85, Familienmittel über 6 Netze:

| Netz ohne Engpass | Distanz | R | Gradterm | Isolation |
|---|---|---|---|---|
| Zufallsnetz Grad 20 | 0,15 / 0,18 | 0,85 / 0,97 | 0,86 / 0,98 | 0,88 / 0,98 |
| Netz mit Knotenpunkten (10) | 0,35 / 0,40 | 0,90 / 0,98 | 0,90 / 0,98 | 0,98 / 0,99 |
| Punktnetz 5D | 0,42 / 0,45 | 0,96 / 0,99 | 0,96 / 0,99 | 0,99 / 0,99 |

  Die Isolationsnäherung (kennt p) liegt in allen sechs Mitteln mindestens so hoch wie R; der Gradterm ohne p liegt in allen sechs Mitteln knapp vor R (höchstens 0,008). „R schlägt die Distanz“ heißt dort vor allem: die Grade schlagen die Distanz.
* **Dichte Hälften mit 3 Querverbindungen:** p = 0,7 / 0,85: R 0,95 / 0,98 gegen Gradterm 0,38 / 0,44. Bei p = 0,15 liegt R (0,86) **hinter** Distanz (0,89) und min cut (0,93); gegen die Distanz ist der Abstand in jedem Netz kleiner als 0,05. „R vor der Distanz“ gilt also nur für die gemessenen dünnen Zellen und die übrigen dichten Zellen.

### Entartung: ordnet R nur noch die zwei Grade?

Über **alle Nichtnachbarpaare**: Rangkorrelation von R mit dem Gradterm und Median von |R − Gradterm| / R. Hallen je ein festes Netz (a = 10, 16, 22), Zufallsfamilien je 5 Netze (Median).

| Netz | Knoten | Rangkorrelation | Wertfehler |
|---|---|---|---|
| zwei Hallen, 1 Tür | 200 / 512 / 968 | 0,273 / 0,246 / 0,228 | 78,6 % / 80,6 % / 81,7 % |
| zwei Hallen, a verteilte Türen | 200 / 512 / 968 | 0,440 / 0,400 / 0,373 | 64,8 % / 69,0 % / 71,3 % |
| Punktnetz 2D, Grad 10 fest | 200 / 500 / 1 000 | 0,665 / 0,535 / 0,497 | 54,9 % / 62,7 % / 66,6 % |
| Zufallsnetz, Grad 8 fest | 200 / 500 / 1 000 | 0,997 / 0,997 / 0,997 | 13,5 % / 13,9 % / 14,1 % |
| Zufallsnetz, Grad √n | 200 / 500 / 1 000 | 0,999 / 1,000 / 1,000 | 7,1 % / 4,5 % / 3,2 % |
| Punktnetz 2D, Grad 2√n | 200 / 500 / 1 000 | 0,967 / 0,958 / 0,975 | 16,4 % / 13,8 % / 11,4 % |
| dichte Hälften (Grad √n), 3 Querverbindungen | 200 / 500 / 1 000 | 0,454 / 0,479 / 0,488 | 67,1 % / 75,6 % / 81,1 % |

Bei den dichten Hälften ist der **Wertfehler** nur bei den Paaren innerhalb einer Hälfte klein (6,3 % / 4,3 % / 3,1 %), quer bleibt er groß (73,6 % / 80,2 % / 84,8 %). Nach der **Rangfolge** liegen für sich genommen auch die Querpaare nah am Gradterm: Rangkorrelation nur über die Querpaare 0,915 / 0,963 / 0,978 (bei 500 und 1 000 Knoten über der Schwelle 0,95 dieser Seite, bei 200 darunter), nur über die Paare innerhalb 0,998 / 1,000 / 1,000 (je Median der 5 Netze). Über alle Nichtnachbarpaare zusammen ist sie trotzdem nur 0,454 / 0,479 / 0,488 (Tabelle). Die Rangfolge kann entarten, während der Wertfehler bleibt (Zufallsnetz Grad 8). Beim Punktnetz mit Grad 10 streuen die einzelnen Netze stark (zwischen 0,42 und 0,72). Die größte Komponente der Punktnetze hat etwas weniger Knoten.

**Fehlende Kanten suchen:** Entartet R, heißt „nahe in R“ vor allem: kleine Summe der Kehrgrade. Wer dort fehlende Kanten sucht, nimmt R nicht roh (Vorhersage fehlender Kanten: Demo [Link-Vorhersage](https://sebastianhanisch-link-prediction-demo.streamlit.app/)).

### Welche Leitung bauen?

Ziel: die kleinste Summe aller Paarwiderstände (Kirchhoff-Index KI). Die Senkung durch eine neue Kante u–v ist exakt **ΔKI = n · |L⁺(e_u − e_v)|² / (1 + R_uv)** (gegen die Neuberechnung geprüft, größte relative Abweichung unter 10⁻¹²). R steht im **Nenner**; „größtes R“ ist eine Daumenregel. Zahl = erreichte / beste Senkung; Zufallsfamilien: Median über 40 Netze mit 60 Knoten (größte Komponente), Hallen je ein Netz. Wählt eine Regel mehrere gleichrangige Kanten, zählt ihr Mittel; „zufällig“ ist der Mittelwert über alle fehlenden Kanten.

| Netz | Netze | zufällig | größtes R | größter Gradterm | Distanz | Distanz, dann Gradterm | Fiedler | größter Zähler |
|---|---|---|---|---|---|---|---|---|
| Besen (5 Knoten) | 1 | 0,79 | 1,00 | 0,84 | 1,00 | 1,00 | 1,00 | 1,00 |
| Handnetz zwei Hallen | 1 | 0,89 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 |
| zwei Hallen 6×6, 1 Tür | 1 | 0,47 | 0,86 | 0,45 | 0,86 | 0,86 | 0,86 | 0,86 |
| zwei Hallen 6×6, 2 Türen | 1 | 0,43 | 0,86 | 0,41 | 0,86 | 0,86 | 0,91 | 0,86 |
| Hallenverbund 3×3, a = 3 | 1 | 0,51 | 0,94 | 0,48 | 0,94 | 0,94 | – | 0,94 |
| straßenähnlich | 40 | 0,41 | 0,85 | 0,46 | 0,87 | 0,85 | 0,88 | 0,88 |
| Gitter mit Löchern | 40 | 0,42 | 0,82 | 0,48 | 0,86 | 0,86 | 0,89 | 0,87 |
| Punktnetz 2D, Grad 6 | 40 | 0,44 | 0,83 | 0,57 | 0,90 | 0,90 | 0,93 | 0,92 |
| Zufallsnetz Grad 4 | 40 | 0,26 | 1,00 | 0,89 | 0,90 | 0,95 | 1,00 | 1,00 |
| Netz mit Knotenpunkten | 40 | 0,54 | 1,00 | 0,65 | 0,85 | 0,88 | 0,98 | 1,00 |
| zwei Hälften, 2 Querverbindungen | 40 | 0,49 | 0,76 | 0,44 | 0,86 | 0,80 | 0,81 | 0,78 |

„Größtes R“ besser / gleich / schlechter, je Netz:

| Netz | gegen Gradterm | gegen Distanz | gegen Distanz, dann Gradterm | gegen Fiedler |
|---|---|---|---|---|
| straßenähnlich | 40 / 0 / 0 | 11 / 8 / 21 | 14 / 12 / 14 | 0 / 18 / 22 |
| Gitter mit Löchern | 40 / 0 / 0 | 7 / 11 / 22 | 7 / 14 / 19 | 0 / 18 / 22 |
| Punktnetz 2D, Grad 6 | 26 / 14 / 0 | 8 / 2 / 30 | 9 / 9 / 22 | 0 / 13 / 27 |
| Zufallsnetz Grad 4 | 33 / 7 / 0 | 32 / 4 / 4 | 24 / 12 / 4 | 12 / 19 / 9 |
| Netz mit Knotenpunkten | 40 / 0 / 0 | 38 / 1 / 1 | 39 / 1 / 0 | 24 / 9 / 7 |
| zwei Hälften | 33 / 7 / 0 | 0 / 2 / 38 | 7 / 6 / 27 | 0 / 11 / 29 |

* **Gegen den Gradterm:** in den 240 Netzen der sechs Zufallsfamilien ist „größtes R“ in 212 besser, in 28 gleich und in keinem schlechter. Das ist eine Aussage über diesen Netzsatz, kein Satz.
* **Keine Regel gewinnt überall.** Median über die 240 Netze: Fiedler 0,91, größter Zähler 0,91, größtes R 0,87, Distanz 0,87, Distanz dann Gradterm 0,86, Gradterm 0,55, zufällig 0,44.
* Auf dem Hallenverbund ist der zweite Eigenwert doppelt; die Fiedler-Regel ist dort nicht bestimmbar (Netze mit Eigenwertabstand unter 10⁻⁸ werden ausgelassen).
* **Dicht** (150 Knoten, Grad etwa 20, je 20 Netze der drei Familien ohne Engpass): Die Rangkorrelation von R und Gradterm über die fehlenden Kanten ist im Median 0,997 bis 0,999, der Gradterm erreicht im Median 96 bis 100 % der besten Senkung, und die beste Kante senkt den KI nur um 0,19 bis 1,38 % (Median). „Größtes R“ ist je Netz in 6 bis 19 von 20 besser als der Gradterm, sonst gleich.
* **Von Hand:** Handnetz mit einer Tür (KI = 21): vier fehlende Kanten mit R = 7/3 senken um 83/10, vier mit R = 5/3 um 13/2; größtes R, Gradterm und Zähler wählen dieselben vier. Das Handnetz trennt die Regeln nicht. **Besen** (Weg 2–3–4, Blätter 0 und 1 an Knoten 2, KI = 18): die drei Blattpaare haben denselben Gradterm 2; R trennt sie (2, 3, 3) und wählt die besten, (0,4) und (1,4), mit Senkung 13/2; (0,1) senkt nur um 10/3. Die Gradterm-Regel erreicht im Mittel ihrer Gleichstände 98/117.

### Reparaturversuche (1 000 Knoten, 150 Anfrageknoten, Mittel über 3 Netze)

Torus: P@10 = Anteil richtiger unter den 10 nächsten Knoten, richtig sind die 10 räumlich nächsten. Gruppen: AUC „gleiche Gruppe“ (5 gleich große Gruppen, 60 % der Kanten eines Knotens innen). Die Sprungwahrscheinlichkeit von PPR/Grad ist je Fall auf **eigenen** Netzen gewählt (Gitter 0,001 bis 0,9); sonst ist nichts abgestimmt.

| Netz | Maß | Distanz | R | verstärkt | −L⁺ | Kosinus L⁺ | PPR 0,15 | PPR abgestimmt | Adamic-Adar | Distanz, Wegezahl | abgestimmter Sprung |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Punktnetz-Torus 3D, Grad 63 | P@10 | 0,16 | 0,03 | 0,82 | 0,72 | 0,80 | 0,66 | 0,71 | 0,82 | 0,84 | 0,001 |
| Punktnetz-Torus 5D, Grad 28 | P@10 | 0,37 | 0,07 | 0,67 | 0,61 | 0,70 | 0,57 | 0,61 | 0,68 | 0,70 | 0,002 |
| Punktnetz-Torus 2D, Grad 63 | P@10 | 0,16 | 0,10 | 0,87 | 0,77 | 0,82 | 0,71 | 0,77 | 0,85 | 0,88 | 0,001 |
| 5 Gruppen, Grad 20 | AUC | 0,66 | 0,52 | 0,62 | 0,84 | 0,85 | 0,83 | 0,85 | 0,66 | 0,77 | 0,001 |
| 5 Gruppen, Grad 80 | AUC | 0,60 | 0,53 | 0,98 | 0,97 | 0,97 | 0,97 | 0,97 | 0,98 | 0,95 | 0,001 |

* Bei vier der fünf Fälle liegt die abgestimmte Sprungwahrscheinlichkeit **am Rand** des Gitters (0,001); die Güte ändert sich unter 0,01 nur noch um höchstens 0,004.
* In den drei dichten Punktnetzen holt die **verstärkte Widerstandsdistanz** die nahen Knoten zurück (P@10 0,67 bis 0,87 gegen 0,03 bis 0,10 mit R); die Zählregel „Distanz, dann Wegezahl“ liegt dort 0,01 bis 0,03 davor. Auf dem 5D-Torus liegt auch die Kosinusform vor ihr.
* **Bei den 5 Gruppen mit mittlerem Grad 20 holt die verstärkte Distanz nichts zurück** (0,62 unter der Distanz 0,66); −L⁺, Kosinusform und PPR/Grad sind dort besser. Bei Grad 80 liegt sie vorn.
* **Beim Ausfall verliert die Reparatur Information:** in allen 225 dünnen Zellen lag R vor der verstärkten Distanz (klar in 161), in den dichten in 49 von 55 messbaren Zellen; in den 6 übrigen (dichte Hälften, p = 0,15) liegen beide gleichauf. Auch Kosinusform, PPR/Grad (Sprung 0,15), Adamic-Adar und „Distanz, dann Wegezahl“ lagen beim Ausfall in allen 225 dünnen Zellen hinter R, −L⁺ in 224.

## Ehrliche Grenzen

* Nur Modellnetze. Keine Aussage über echte Straßen-, Strom- oder Datennetze, keine Neuheitsaussage.
* Nur die Trennung eines Paars; Umwege, längere Wege oder Durchsatz sind nicht gemessen. Abhängige Ausfälle und Gewichte sind nicht gemessen.
* Die Wahrheit ist außer auf dem Handnetz und bei „Leitung gegen drei Wege“ eine Stichprobe.
* Ausfall nur mit 72 bis 225 Knoten, dicht nur mit 150; je Hallengröße ein festes Netz; Entartung bei Hallen je ein Netz.
* Stärkere Schätzer, die kantendisjunkte kürzeste Wege mit p verrechnen, sind nicht als Gegner dabei. Wald-Distanz, biharmonische Distanz und p-Widerstand sind nicht gemessen.
* Die Karte hat keine Klickbedienung; jede Einstellung geht über die Seitenleiste.
* Literatur teilweise nur in Teilen gelesen (siehe „Quellen“); ein Literaturwert-Test fehlt (offen).

## Verifikation

* **Handrechnungen:** Handnetz (R = 2/3, 7/3, Ordnungszählungen, Ausbau 83/10 und 13/2), Besen (98/117), Entartung am vollständigen Netz (relative Abweichung 1/(n−1)) und an zwei Cliquen mit Brücke, verstärkte Distanz (1/6, 5/9, 4/3), „Leitung gegen drei Wege“.
* **Orakel** (anderer Rechenweg): R gegen geerdeten Laplace in Brüchen und Spannbaum-Zählung; KI gegen die Zählung aufspannender 2-Wälder, Eigenwerte und Neuberechnung jeder neuen Kante; min cut gegen Aufzählung aller Knotenmengen und `networkx.edge_disjoint_paths`; Distanz und Wegezahlen gegen networkx; PPR gegen Potenziteration; Adamic-Adar gegen networkx; Isolationsformel gegen Aufzählung aller Ausfallmuster; die gebündelte Komponentensuche gegen eine eigene Vereinigungssuche mit denselben Mustern; Rangkorrelation gegen `scipy.stats.spearmanr`; AUC gegen Paarzählung. `networkx.resistance_distance` wird nicht benutzt.
* **Eigenschaften** (je 30 Netze): Umnummerieren, neue Kante vergrößert kein R, Dreiecksungleichung, Foster, Bäume R = Distanz, untere Schranken, R ≥ 1/min cut, R ≤ Distanz.
* **Zahlen:** `tests/test_claims.py` rechnet die Hallen-, Entartungs- und Ausbautabellen vollständig neu, von den dichten Ausbaunetzen jedes zehnte, von den übrigen Ausfallzellen je Familie eine Stichprobe und ein Reparaturnetz, und prüft die Zahlen dieser README gegen die gespeicherte Datei (Neu-Rechnen als Band).
* **Oberfläche:** AppTest (Standard, jeder Button, jedes Preset mit seinen Verdikt-Zeilen, jede Option, Regler an den Rändern, Permalink, alle vier Experimente), Layout-, Footer- und Laufzeit-Import-Test.
* Gesamt: **381 Tests** (`python -m pytest tests -q`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App |
| `wdn_netze.py` | Handnetze, Gitterhallen, Hallenverbund, Netze mit Zufall |
| `wdn_zufall.py`, `wdn_rng.py` | SplitMix64 (blockweise) und abgeleitete Zufalls-Seeds |
| `wdn_widerstand.py` | L⁺, effektiver Widerstand, Kirchhoff-Index |
| `wdn_masse.py` | die Gegner und Reparaturmaße, je eine Funktion |
| `wdn_ausfall.py` | Ausfallstichprobe (gebündelt) und exakte Aufzählung |
| `wdn_statistik.py` | Rangkorrelation, Klar-Kriterium, P@10, AUC |
| `wdn_szenario.py` | Netzfamilien der Experimente |
| `wdn_experimente.py` | die Rechnungen der vier Experimente |
| `wdn_tabellen.py` | die festgeschriebene Instanzmenge der Tabellen |
| `wdn_daten.py` | Laden und Zählen der vorgerechneten Zahlen |
| `wdn_evaluation.py` | Verdikte (reine Funktionen) und Zahlformate |
| `wdn_karte.py`, `wdn_visualization.py` | Plotly-Figuren, Achsen gesperrt |
| `wdn_constants.py`, `wdn_presets.py`, `wdn_layout.py` | Regler, Presets, Permalink, fester Kopf |
| `tools/vorrechnen.py` | rechnet `daten/vorgerechnet.json` neu |
| `tests/` | Handrechnungen, Orakel, Eigenschaften, Randfälle, Verdikte, Claims, Oberfläche |

## Bewusst nicht umgesetzt

* Zuverlässigkeit des ganzen Netzes und R je vorhandener Kante: Demo [Zufällige Spannbäume](https://sebastianhanisch-random-spanning-tree-demo.streamlit.app/). min cut als Verfahren: [Gomory-Hu-Baum](https://sebastianhanisch-gomory-hu-demo.streamlit.app/) und [Satz von Menger](https://sebastianhanisch-menger-demo.streamlit.app/). Seltene Trennungen richtig schätzen: [Importance Sampling](https://sebastianhanisch-importance-sampling-demo.streamlit.app/).
* Garantierter Zusammenhang durch neue Kanten: [Zusammenhang verstärken](https://sebastianhanisch-zusammenhang-verstaerken-demo.streamlit.app/). In der Demo [Netzhärtung](https://sebastianhanisch-haertung-demo.streamlit.app/) ist R ein anderes Maß (Robustheitsindex). [Zentralität](https://sebastianhanisch-centrality-demo.streamlit.app/) bewertet einzelne Knoten, nicht Paare.
* Suche nach mehreren neuen Kanten, Umwege als Zielgröße, abgestimmte Varianten der Reparaturmaße außer der Sprungwahrscheinlichkeit.

## Quellen

* von Luxburg, Radl, Hein: *Hitting and Commute Times in Large Random Neighborhood Graphs*, Journal of Machine Learning Research 15 (2014), 1751–1798 (gelesen: Abschnitte 1 bis 5 und 6.1): R nähert sich dem Gradterm, wenn der Mindestgrad mit der Netzgröße wächst und kein starker Engpass besteht; Gitter und Netze mit konstantem Mindestgrad sind nicht abgedeckt.
* Dieselben: *Getting lost in space* (NIPS 2010), Abschnitt 4: verstärkte Widerstandsdistanz (dort für die Pendeldistanz) und die Korrektur nach Brand (L⁺ zentriert und normiert).
* L. Lovász: *Random Walks on Graphs: A Survey* (1993; in Teilen gelesen), Korollar 3.3: R ≥ (1/d_s + 1/d_t)/2.
* D. Levin, Y. Peres, E. Wilmer: *Markov Chains and Mixing Times*, 2. Auflage, Proposition 10.7: Pendelzeit = 2m·R.
* Dickson u. a.: Übersicht zu Circuitscape, *Conservation Biology* 33 (2019); gelesen: Zusammenfassung und Schlussteil. Die Autoren nennen selbst Fälle, in denen einfachere Modelle besser sein können.
* Cianfanelli, Como, Ozdaglar, Parise: Ergebnis über effektive Widerstände zum besten Eingriff in Verkehrsnetze (nur die Zusammenfassung gelesen: affine Latenzen, unveränderter Träger des Gleichgewichts).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Irrfahrten auf Netzen: Trefferzeit bis Schnitt](https://sebastianhanisch.net/konzepte-irrfahrten.html).
