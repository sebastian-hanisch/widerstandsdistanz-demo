"""Netzfamilien der Experimente 1 bis 3 und wie aus Familie, Größe und Zufalls-Seed ein Netz wird (ohne Streamlit).

Jede Familie hat eine feste Nummer (nie umsortieren: sie geht in die abgeleiteten Zufalls-Seeds ein). Hallen sind fest gebaut; der Zufalls-Seed wählt dort nur
die Knotenpaare und die Ausfallproben.
"""

import wdn_netze as N
from wdn_zufall import ZWECK_NETZ, abgeleitet

# --- Familien von Experiment 1 --------------------------------------------------------------------------------------------------------
HALLEN, VERBUND = "hallen", "verbund"
STRASSE, LOECHER, PUNKT2D, ZUFALL4, KNOTEN, HAELFTEN = "strasse", "loecher", "punkt2d", "zufall4", "knoten", "haelften"
ER20, KNOTEN10, PUNKT5D, DHAELFTEN = "er20", "knoten10", "punkt5d", "dhaelften"
KONTRAST = (STRASSE, LOECHER, PUNKT2D, ZUFALL4, KNOTEN, HAELFTEN)
DICHT = (ER20, KNOTEN10, PUNKT5D, DHAELFTEN)
FAMILIEN = (HALLEN, VERBUND) + KONTRAST + DICHT

FAMNR = {HALLEN: 1, VERBUND: 2, STRASSE: 3, LOECHER: 4, PUNKT2D: 5, ZUFALL4: 6, KNOTEN: 7, HAELFTEN: 8, ER20: 9, KNOTEN10: 10, PUNKT5D: 11, DHAELFTEN: 12}

FAMILIE_TEXT = {
    HALLEN: "zwei Hallen mit k verteilten Türen",
    VERBUND: "Hallenverbund (eine Tür je Nachbarpaar)",
    STRASSE: "straßenähnlich (mittlerer Grad 2,8)",
    LOECHER: "Gitter mit Löchern",
    PUNKT2D: "Punktnetz 2D (mittlerer Grad 6)",
    ZUFALL4: "Zufallsnetz (mittlerer Grad 4)",
    KNOTEN: "Netz mit Knotenpunkten (2 Anschlüsse je neuem Knoten)",
    HAELFTEN: "zwei Hälften mit 2 Querverbindungen",
    ER20: "dicht: Zufallsnetz (mittlerer Grad 20)",
    KNOTEN10: "dicht: Netz mit Knotenpunkten (10 Anschlüsse)",
    PUNKT5D: "dicht: Punktnetz 5D (mittlerer Grad 20)",
    DHAELFTEN: "dichte Hälften mit 3 Querverbindungen",
}
FAMILIE_KURZ = {
    HALLEN: "zwei Hallen", VERBUND: "Hallenverbund", STRASSE: "straßenähnlich", LOECHER: "Gitter mit Löchern", PUNKT2D: "Punktnetz 2D",
    ZUFALL4: "Zufallsnetz Grad 4", KNOTEN: "Netz mit Knotenpunkten", HAELFTEN: "zwei Hälften", ER20: "Zufallsnetz Grad 20",
    KNOTEN10: "Netz mit Knotenpunkten (10)", PUNKT5D: "Punktnetz 5D", DHAELFTEN: "dichte Hälften",
}

# Türfamilie: Zahl der Türen, 0 = so viele wie Zeilen (a)
TUEREN = (1, 2, 4, 0)
TUEREN_TEXT = {1: "1 Tür", 2: "2 Türen", 4: "4 Türen", 0: "a Türen (jede Zeile)"}
VERBUND_VARIANTEN = {"2x2x6": (2, 2, 6), "3x3x4": (3, 3, 4), "3x3x5": (3, 3, 5)}
VERBUND_TEXT = {"2x2x6": "2×2 Hallen, a = 6", "3x3x4": "3×3 Hallen, a = 4", "3x3x5": "3×3 Hallen, a = 5"}
A_FAMILIE = (6, 8, 10)

P_DUENN = (0.05, 0.15, 0.3)
P_DICHT = (0.15, 0.7, 0.85)


def ist_dicht(familie: str) -> bool:
    return familie in DICHT


def anzahl_tueren(a: int, tueren: int) -> int:
    return a if tueren == 0 else tueren


def baue(familie: str, n: int, a: int, tueren: int, verbund: str, seed: int) -> N.Netz:
    """Netz der Experimente 1 und 2: Hallen aus a und der Türfamilie, der Verbund aus der Variante, alle anderen aus n und dem Zufalls-Seed."""
    if familie == HALLEN:
        return N.k_tueren(a, anzahl_tueren(a, tueren))
    if familie == VERBUND:
        return N.hallenverbund(*VERBUND_VARIANTEN[verbund])
    netzseed = abgeleitet(seed, ZWECK_NETZ, FAMNR[familie])
    if familie == STRASSE:
        return N.strassennetz(n, 2.8, netzseed)
    if familie == LOECHER:
        spalten = max(2, round(n / 10))
        kanten = 10 * (spalten - 1) + 9 * spalten
        return N.gitter_mit_loechern(10, spalten, round(60 * kanten / 275), netzseed)
    if familie == PUNKT2D:
        return N.punktnetz(n, 6, 2, netzseed)
    if familie == ZUFALL4:
        return N.zufallsnetz(n, 4, netzseed)
    if familie == KNOTEN:
        return N.knotenpunktnetz(n, 2, netzseed)
    if familie == HAELFTEN:
        return N.zwei_haelften(n, 5, 2, netzseed)
    if familie == ER20:
        return N.zufallsnetz(n, 20, netzseed)
    if familie == KNOTEN10:
        return N.knotenpunktnetz(n, 10, netzseed)
    if familie == PUNKT5D:
        return N.punktnetz(n, 20, 5, netzseed)
    if familie == DHAELFTEN:
        return N.zwei_haelften(n, 20, 3, netzseed)
    raise ValueError(f"unbekannte Familie {familie}")


# --- Familien von Experiment 2 (Entartung) -------------------------------------------------------------------------------------------
E_HALLEN1, E_HALLENA, E_PUNKT10, E_ER8, E_ERWURZEL, E_PUNKTWURZEL, E_HAELFTEN = ("hallen1", "hallena", "punkt10", "er8", "erwurzel", "punktwurzel",
                                                                               "ehaelften")
ENTARTUNG = (E_HALLEN1, E_HALLENA, E_PUNKT10, E_ER8, E_ERWURZEL, E_PUNKTWURZEL, E_HAELFTEN)
E_NR = {E_HALLEN1: 21, E_HALLENA: 22, E_PUNKT10: 23, E_ER8: 24, E_ERWURZEL: 25, E_PUNKTWURZEL: 26, E_HAELFTEN: 27}
E_TEXT = {
    E_HALLEN1: "zwei Hallen, 1 Tür",
    E_HALLENA: "zwei Hallen, a verteilte Türen",
    E_PUNKT10: "Punktnetz 2D, mittlerer Grad 10 fest",
    E_ER8: "Zufallsnetz, mittlerer Grad 8 fest",
    E_ERWURZEL: "Zufallsnetz, mittlerer Grad √n",
    E_PUNKTWURZEL: "Punktnetz 2D, mittlerer Grad 2√n",
    E_HAELFTEN: "dichte Hälften (Grad √n) mit 3 Querverbindungen",
}
E_GROESSEN = (200, 500, 1000)
E_HALLENSEITE = {200: 10, 500: 16, 1000: 22}
E_HALLEN = (E_HALLEN1, E_HALLENA)


def baue_entartung(familie: str, n: int, seed: int) -> N.Netz:
    """Netz von Experiment 2. Bei den Hallen gehört zu n die Seite a = 10, 16 oder 22 (200, 512, 968 Knoten)."""
    if familie in E_HALLEN:
        a = E_HALLENSEITE[n]
        return N.k_tueren(a, 1 if familie == E_HALLEN1 else a)
    netzseed = abgeleitet(seed, ZWECK_NETZ, E_NR[familie])
    if familie == E_PUNKT10:
        return N.punktnetz(n, 10, 2, netzseed)
    if familie == E_ER8:
        return N.zufallsnetz(n, 8, netzseed)
    if familie == E_ERWURZEL:
        return N.zufallsnetz(n, n ** 0.5, netzseed)
    if familie == E_PUNKTWURZEL:
        return N.punktnetz(n, 2 * n ** 0.5, 2, netzseed)
    if familie == E_HAELFTEN:
        return N.zwei_haelften(n, n ** 0.5, 3, netzseed)
    raise ValueError(f"unbekannte Familie {familie}")


# --- Netze von Experiment 3 (Netzausbau, n ≤ 81) -----------------------------------------------------------------------------------------
X_BESEN, X_HAND, X_HALLEN1, X_HALLEN2, X_VERBUND = "besen", "hand", "xhallen1", "xhallen2", "xverbund"
X_ZUFALL = ("xstrasse", "xloecher", "xpunkt2d", "xzufall4", "xknoten", "xhaelften")
X_NETZE = (X_BESEN, X_HAND, X_HALLEN1, X_HALLEN2, X_VERBUND) + X_ZUFALL
X_NR = {f: 41 + i for i, f in enumerate(X_ZUFALL)}
X_TEXT = {
    X_BESEN: "Besen (5 Knoten)", X_HAND: "Handnetz zwei Hallen", X_HALLEN1: "zwei Hallen 6×6, 1 Tür", X_HALLEN2: "zwei Hallen 6×6, 2 Türen",
    X_VERBUND: "Hallenverbund 3×3, a = 3", "xstrasse": "straßenähnlich (60 Knoten)", "xloecher": "Gitter mit Löchern 6×10",
    "xpunkt2d": "Punktnetz 2D, Grad 6 (60)", "xzufall4": "Zufallsnetz Grad 4 (60)", "xknoten": "Netz mit Knotenpunkten (60)",
    "xhaelften": "zwei Hälften, 2 Querverbindungen (60)",
}


def baue_ausbau(netz: str, seed: int) -> N.Netz:
    if netz == X_BESEN:
        return N.besen()
    if netz == X_HAND:
        return N.handnetz(1)
    if netz == X_HALLEN1:
        return N.k_tueren(6, 1)
    if netz == X_HALLEN2:
        return N.k_tueren(6, 2)
    if netz == X_VERBUND:
        return N.hallenverbund(3, 3, 3)
    netzseed = abgeleitet(seed, ZWECK_NETZ, X_NR[netz])
    if netz == "xstrasse":
        return N.strassennetz(60, 2.8, netzseed)
    if netz == "xloecher":
        return N.gitter_mit_loechern(6, 10, 25, netzseed)
    if netz == "xpunkt2d":
        return N.punktnetz(60, 6, 2, netzseed)
    if netz == "xzufall4":
        return N.zufallsnetz(60, 4, netzseed)
    if netz == "xknoten":
        return N.knotenpunktnetz(60, 2, netzseed)
    if netz == "xhaelften":
        return N.zwei_haelften(60, 5, 2, netzseed)
    raise ValueError(f"unbekanntes Netz {netz}")
