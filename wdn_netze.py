"""Netze: einfach, ungerichtet, mit Knotennamen und Koordinaten für die Karte (ohne Streamlit; numpy, für das straßenähnliche Netz scipy).

Grundlage: Kopie des gemeinsamen Bausteins `pzt_netze` der Demo „Pendelzeit“ (kopieren, nicht importieren; Handnetz und Gitterhallen unverändert), ergänzt um die
Handbeispiele „Besen“ und „Leitung gegen drei Wege“, den Hallenverbund und die Netze mit Zufall (SplitMix64, `wdn_rng`).

Netze:
* Handnetz „zwei Hallen“: Dreiecke {0, 1, 2} und {3, 4, 5}, eine Tür 2–3, auf Wunsch eine zweite Tür 5–0.
* Besen: Weg 2–3–4, dazu die Blätter 0 und 1 an Knoten 2.
* Leitung (eine Kante) und drei sonst getrennte Wege der Länge 4.
* Gitterhallen a×a (Vierernachbarschaft). **Netzfamilie** `k_tueren`: k gleichmäßig verteilte Türen in den Zeilen floor((i + 0,5)·a / k), i = 0 … k−1.
* Hallenverbund p×q: p×q Hallen a×a im Raster, Nachbarhallen je durch eine Tür in der mittleren Zeile bzw. Spalte verbunden.
* Kontrastnetze mit Zufall: straßenähnlich (ausgedünnte Delaunay-Triangulierung), Gitter mit Löchern, Punktnetz in d Dimensionen (auf Wunsch auf dem Torus),
  Zufallsnetz (jedes Paar unabhängig), Netz mit Knotenpunkten (Anschluss nach dem Grad, Barabási-Albert), zwei Hälften mit Querverbindungen, gepflanzte Gruppen.
  Netze werden nie neu gezogen, bis sie zusammenhängen: es bleibt die größte Zusammenhangskomponente.
"""

from dataclasses import dataclass

import numpy as np

from wdn_rng import SplitMix64
from wdn_zufall import BlockZufall


@dataclass(frozen=True)
class Netz:
    name: str
    n: int
    kanten: tuple          # sortierte Paare (u, v) mit u < v
    knoten: tuple          # Name je Knoten
    pos: tuple             # (x, y) je Knoten, nur für die Karte


def netz(name: str, n: int, kanten, knoten=None, pos=None) -> Netz:
    """Netz aus einer Kantenliste; Schleifen, Doppelkanten und Knoten außerhalb 0 … n−1 werden abgewiesen."""
    paare = []
    for u, v in kanten:
        u, v = int(u), int(v)
        if u == v or not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"ungültige Kante ({u}, {v}) bei {n} Knoten")
        paare.append((min(u, v), max(u, v)))
    if len(set(paare)) != len(paare):
        raise ValueError("doppelte Kante")
    knoten = tuple(str(i) for i in range(n)) if knoten is None else tuple(knoten)
    if pos is None:
        winkel = 2 * np.pi * np.arange(n) / max(n, 1)
        pos = tuple((float(np.cos(w)), float(np.sin(w))) for w in winkel)
    return Netz(name, n, tuple(sorted(paare)), knoten, tuple(pos))


def kantenfeld(g: Netz) -> np.ndarray:
    """Kanten als m×2-Feld (auch bei m = 0)."""
    return np.array(g.kanten, dtype=np.int64).reshape(-1, 2)


def adjazenz(g: Netz) -> np.ndarray:
    A = np.zeros((g.n, g.n))
    k = kantenfeld(g)
    A[k[:, 0], k[:, 1]] = 1.0
    A[k[:, 1], k[:, 0]] = 1.0
    return A


def grade(g: Netz) -> np.ndarray:
    return np.bincount(kantenfeld(g).ravel(), minlength=g.n).astype(np.int64)


def nachbarn(g: Netz) -> list:
    nb = [[] for _ in range(g.n)]
    for u, v in g.kanten:
        nb[u].append(v)
        nb[v].append(u)
    return [sorted(x) for x in nb]


def komponenten(g: Netz) -> np.ndarray:
    """Nummer der Zusammenhangskomponente je Knoten (Breitensuche in Python-Listen)."""
    nb = nachbarn(g)
    nummer = np.full(g.n, -1, dtype=np.int64)
    k = 0
    for start in range(g.n):
        if nummer[start] >= 0:
            continue
        nummer[start] = k
        front = [start]
        while front:
            x = front.pop()
            for w in nb[x]:
                if nummer[w] < 0:
                    nummer[w] = k
                    front.append(w)
        k += 1
    return nummer


def ist_zusammenhaengend(g: Netz) -> bool:
    return g.n > 0 and int(komponenten(g).max()) == 0


def hat_kante(g: Netz, u: int, v: int) -> bool:
    return (min(u, v), max(u, v)) in set(g.kanten)


def mit_kante(g: Netz, u: int, v: int) -> Netz:
    """Dasselbe Netz mit der neuen Kante u–v (nur zwischen zwei verschiedenen, noch nicht verbundenen Knoten)."""
    if u == v or hat_kante(g, u, v):
        raise ValueError("neue Kante nur zwischen zwei verschiedenen, bisher nicht verbundenen Knoten")
    return netz(g.name, g.n, list(g.kanten) + [(u, v)], g.knoten, g.pos)


def fehlende_kanten(g: Netz) -> list:
    vorhanden = set(g.kanten)
    return [(u, v) for u in range(g.n) for v in range(u + 1, g.n) if (u, v) not in vorhanden]


def groesste_komponente(g: Netz) -> Netz:
    """Das Teilnetz auf der größten Zusammenhangskomponente (bei Gleichstand die mit der kleinsten Knotennummer); Knoten werden neu nummeriert."""
    nummer = komponenten(g)
    gross = int(np.bincount(nummer).argmax())
    alt = np.flatnonzero(nummer == gross)
    if len(alt) == g.n:
        return g
    neu = np.full(g.n, -1, dtype=np.int64)
    neu[alt] = np.arange(len(alt))
    kanten = [(neu[u], neu[v]) for u, v in g.kanten if neu[u] >= 0]
    return netz(g.name, len(alt), kanten, [g.knoten[i] for i in alt], [g.pos[i] for i in alt])


# ----------------------------------------------------------------------------------------------------------------------------------
# Handbeispiele
# ----------------------------------------------------------------------------------------------------------------------------------

HANDNETZ_POS = ((0.0, 1.4), (0.0, 0.0), (1.2, 0.7), (2.8, 0.7), (4.0, 0.0), (4.0, 1.4))
ZWEITE_TUER = (0, 5)
BESEN_KANTEN = ((0, 2), (1, 2), (2, 3), (3, 4))


def handnetz(tueren: int = 1) -> Netz:
    """Dreiecke {0,1,2} und {3,4,5}; Tür 2–3, bei zwei Türen zusätzlich 5–0."""
    if tueren not in (1, 2):
        raise ValueError("Handnetz mit einer oder zwei Türen")
    kanten = [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (2, 3)]
    if tueren == 2:
        kanten.append(ZWEITE_TUER)
    return netz("Handnetz zwei Hallen", 6, kanten, pos=HANDNETZ_POS)


def besen() -> Netz:
    """Besen: Blätter 0 und 1 an Knoten 2, dazu der Weg 2–3–4. Ein Baum."""
    return netz("Besen", 5, BESEN_KANTEN, pos=((0.0, 1.6), (0.0, 0.0), (1.0, 0.8), (2.0, 0.8), (3.0, 0.8)))


def leitung() -> Netz:
    return netz("eine Leitung", 2, [(0, 1)], pos=((0.0, 0.0), (4.0, 0.0)))


def drei_wege(k: int = 3, laenge: int = 4) -> Netz:
    """Endknoten 0 und 1, dazwischen k sonst getrennte Wege der gegebenen Länge."""
    kanten, pos = [], [(0.0, 0.0), (float(laenge), 0.0)]
    naechster = 2
    for i in range(k):
        kette = [0] + list(range(naechster, naechster + laenge - 1)) + [1]
        naechster += laenge - 1
        kanten += list(zip(kette, kette[1:]))
        pos += [(float(j), (i - (k - 1) / 2) * 1.0) for j in range(1, laenge)]
    return netz(f"{k} Wege der Länge {laenge}", naechster, kanten, pos=pos)


def vollstaendig(n: int) -> Netz:
    return netz(f"vollständiges Netz mit {n} Knoten", n, [(u, v) for u in range(n) for v in range(u + 1, n)])


# ----------------------------------------------------------------------------------------------------------------------------------
# Gitterhallen
# ----------------------------------------------------------------------------------------------------------------------------------

def hallenknoten(a: int, halle: int, zeile: int, spalte: int) -> int:
    """Knotennummer in den Gitterhallen: erst die linke Halle zeilenweise, dann die rechte."""
    if not (halle in (0, 1) and 0 <= zeile < a and 0 <= spalte < a):
        raise ValueError("Platz außerhalb der Halle")
    return halle * a * a + zeile * a + spalte


def tuerzeilen(a: int, k: int) -> list:
    """Zeilen der k gleichmäßig verteilten Türen: floor((i + 0,5)·a / k), in ganzen Zahlen gerechnet. Eine Tür liegt so in Zeile a // 2."""
    if not 1 <= k <= a:
        raise ValueError("1 bis a Türen")
    return [((2 * i + 1) * a) // (2 * k) for i in range(k)]


def _gitterkanten(a: int, versatz: int) -> list:
    kanten = []
    for z in range(a):
        for s in range(a):
            u = versatz + z * a + s
            if s + 1 < a:
                kanten.append((u, u + 1))
            if z + 1 < a:
                kanten.append((u, u + a))
    return kanten


def gitterhallen(a: int, zeilen) -> Netz:
    """Zwei Gitter a×a, je eine Tür in jeder Zeile aus `zeilen`."""
    if a < 2:
        raise ValueError("a mindestens 2")
    zeilen = list(zeilen)
    if len(set(zeilen)) != len(zeilen) or not zeilen:
        raise ValueError("mindestens eine Tür, jede Zeile höchstens einmal")
    kanten = _gitterkanten(a, 0) + _gitterkanten(a, a * a)
    kanten += [(hallenknoten(a, 0, z, a - 1), hallenknoten(a, 1, z, 0)) for z in zeilen]
    namen = [f"{b}({z},{s})" for b in "LR" for z in range(a) for s in range(a)]
    pos = [(float(s + h * (a + 1)), float(a - 1 - z)) for h in range(2) for z in range(a) for s in range(a)]
    return netz(f"Zwei Hallen {a}×{a}", 2 * a * a, kanten, namen, pos)


def zwei_hallen(a: int) -> Netz:
    """Zwei Hallen mit einer Tür in Zeile a // 2."""
    return gitterhallen(a, [a // 2])


def k_tueren(a: int, k: int) -> Netz:
    """Netzfamilie mit k gleichmäßig verteilten Türen (keine Ergänzung der einen Tür)."""
    return gitterhallen(a, tuerzeilen(a, k))


def hallenverbund(p: int, q: int, a: int) -> Netz:
    """p×q Hallen a×a im Raster; waagrechte Nachbarn durch eine Tür in der mittleren Zeile, senkrechte durch eine in der mittleren Spalte."""
    if p < 1 or q < 1 or a < 2:
        raise ValueError("mindestens eine Halle, a mindestens 2")
    start = lambda i, j: (i * q + j) * a * a
    m = a // 2
    kanten, pos, namen = [], [], []
    for i in range(p):
        for j in range(q):
            kanten += _gitterkanten(a, start(i, j))
            pos += [(float(j * (a + 1) + s), float(-i * (a + 1) - z)) for z in range(a) for s in range(a)]
            namen += [f"H{i + 1}{j + 1}({z},{s})" for z in range(a) for s in range(a)]
            if j + 1 < q:
                kanten.append((start(i, j) + m * a + a - 1, start(i, j + 1) + m * a))
            if i + 1 < p:
                kanten.append((start(i, j) + (a - 1) * a + m, start(i + 1, j) + m))
    return netz(f"Hallenverbund {p}×{q}, a = {a}", p * q * a * a, kanten, namen, pos)


# ----------------------------------------------------------------------------------------------------------------------------------
# Netze mit Zufall
# ----------------------------------------------------------------------------------------------------------------------------------

def _finde(eltern, x):
    while eltern[x] != x:
        eltern[x] = eltern[eltern[x]]
        x = eltern[x]
    return x


def _ausduennen(n: int, kanten: list, ziel_m: int, rng: SplitMix64) -> list:
    """Erst ein Spannwald in zufälliger Reihenfolge (so bleibt der Zusammenhang), dann weitere Kanten bis `ziel_m`."""
    reihe = list(range(len(kanten)))
    rng.shuffle(reihe)
    eltern = list(range(n))
    wald, rest = [], []
    for i in reihe:
        a, b = kanten[i]
        ra, rb = _finde(eltern, a), _finde(eltern, b)
        if ra != rb:
            eltern[ra] = rb
            wald.append((a, b))
        else:
            rest.append((a, b))
    return wald + rest[: max(0, ziel_m - len(wald))]


def strassennetz(n: int, grad: float, seed: int) -> Netz:
    """Zufallspunkte im Quadrat, Delaunay-Triangulierung, zufällig ausgedünnt bis zum mittleren Grad."""
    from scipy.spatial import Delaunay

    P = BlockZufall(seed).random(2 * n).reshape(n, 2)
    kanten = set()
    for s in Delaunay(P).simplices:
        for i, j in ((0, 1), (1, 2), (0, 2)):
            a, b = int(s[i]), int(s[j])
            kanten.add((min(a, b), max(a, b)))
    duenn = _ausduennen(n, sorted(kanten), int(round(grad * n / 2)), SplitMix64(seed + 1))
    return groesste_komponente(netz("straßenähnliches Netz", n, duenn, pos=[(float(x), float(y)) for x, y in P]))


def gitter_mit_loechern(zeilen: int, spalten: int, fehlend: int, seed: int) -> Netz:
    """Gitter, aus dem `fehlend` Kanten entfernt sind, ohne den Zusammenhang zu verlieren."""
    kanten = []
    for i in range(zeilen):
        for j in range(spalten):
            u = i * spalten + j
            if j + 1 < spalten:
                kanten.append((u, u + 1))
            if i + 1 < zeilen:
                kanten.append((u, u + spalten))
    duenn = _ausduennen(zeilen * spalten, kanten, len(kanten) - fehlend, SplitMix64(seed))
    pos = [(float(j), float(zeilen - 1 - i)) for i in range(zeilen) for j in range(spalten)]
    return groesste_komponente(netz("Gitter mit Löchern", zeilen * spalten, duenn, pos=pos))


def punktabstaende(n: int, dim: int, seed: int, torus: bool = False):
    """(Punkte, Abstandsmatrix) von n gleichverteilten Punkten im Einheitswürfel (Torus: Abstand je Achse über den Rand)."""
    P = BlockZufall(seed).random(n * dim).reshape(n, dim)
    D2 = np.zeros((n, n))
    for k in range(dim):
        diff = np.abs(P[:, k][:, None] - P[:, k][None, :])
        if torus:
            diff = np.minimum(diff, 1 - diff)
        D2 += diff * diff
    return P, np.sqrt(D2)


def _kuerzeste_paare(n: int, D: np.ndarray, m: int):
    """Die m kürzesten Paare (bei gleichem Abstand nach der Reihenfolge der Paare)."""
    I, J = np.triu_indices(n, 1)
    wahl = np.argsort(D[I, J], kind="stable")[:m]
    return list(zip(I[wahl].tolist(), J[wahl].tolist()))


def punktnetz_mit_abstaenden(n: int, grad: float, dim: int, seed: int, torus: bool = False):
    """(Netz, Abstände der Punkte): verbunden sind die kürzesten Paare, bis der mittlere Grad erreicht ist; hier ohne Beschränkung auf eine Komponente."""
    P, D = punktabstaende(n, dim, seed, torus)
    m = min(int(round(grad * n / 2)), n * (n - 1) // 2)
    pos = [(float(p[0]), float(p[1])) for p in P] if dim >= 2 else None
    return netz(f"Punktnetz {dim}D", n, _kuerzeste_paare(n, D, m), pos=pos), D


def punktnetz(n: int, grad: float, dim: int, seed: int, torus: bool = False) -> Netz:
    return groesste_komponente(punktnetz_mit_abstaenden(n, grad, dim, seed, torus)[0])


def _zufallspaare_unabhaengig(n: int, wahrscheinlichkeit, rng: BlockZufall):
    I, J = np.triu_indices(n, 1)
    wahl = rng.random(len(I)) < wahrscheinlichkeit
    return list(zip(I[wahl].tolist(), J[wahl].tolist()))


def zufallsnetz(n: int, grad: float, seed: int) -> Netz:
    """Jedes Knotenpaar ist unabhängig mit Wahrscheinlichkeit grad/(n−1) verbunden (Erdős-Rényi), dann die größte Komponente."""
    return groesste_komponente(netz("Zufallsnetz", n, _zufallspaare_unabhaengig(n, grad / (n - 1), BlockZufall(seed))))


def knotenpunktnetz(n: int, m: int, seed: int) -> Netz:
    """Anschluss nach dem Grad (Barabási-Albert): jeder neue Knoten verbindet sich mit m vorhandenen, die ersten m Ziele sind die Knoten 0 … m−1."""
    if not 1 <= m < n:
        raise ValueError("1 ≤ m < n")
    rng = SplitMix64(seed)
    ziele = list(range(m))
    liste, kanten = [], []
    for v in range(m, n):
        kanten += [(u, v) for u in ziele]
        liste += ziele + [v] * m
        wahl = set()
        while len(wahl) < m:
            wahl.add(liste[rng.below(len(liste))])
        ziele = sorted(wahl)
    return groesste_komponente(netz("Netz mit Knotenpunkten", n, kanten))


def zwei_haelften(n: int, grad: float, quer: int, seed: int) -> Netz:
    """Zwei Zufallsnetze mit je n // 2 Knoten und `quer` verschiedenen zufälligen Querverbindungen; dann die größte Komponente."""
    h = n // 2
    kanten = []
    for halb, teil in enumerate((0, h)):
        kanten += [(a + teil, b + teil) for a, b in _zufallspaare_unabhaengig(h, grad / (h - 1), BlockZufall(seed + halb))]
    rng = SplitMix64(seed + 2)
    vorhanden = set()
    while len(vorhanden) < quer:
        vorhanden.add((rng.below(h), h + rng.below(h)))
    winkel = 2 * np.pi * np.arange(h) / h
    pos = [(float(np.cos(w)), float(np.sin(w))) for w in winkel] + [(float(np.cos(w) + 2.6), float(np.sin(w))) for w in winkel]
    return groesste_komponente(netz("zwei Hälften", 2 * h, kanten + sorted(vorhanden), pos=pos))


def haelfte_von(g: Netz) -> np.ndarray:
    """Für Netze aus `zwei_haelften`: 0 (linke) oder 1 (rechte Hälfte) je Knoten, an der Lage in der Karte abgelesen."""
    return np.array([1 if x > 1.3 else 0 for x, _ in g.pos], dtype=np.int64)


def gruppennetz(n: int, k: int, grad: float, anteil_innen: float, seed: int):
    """k gleich große gepflanzte Gruppen; `anteil_innen` = erwarteter Anteil der Kanten eines Knotens in der eigenen Gruppe. Rückgabe (Netz, Gruppe je Knoten)."""
    gruppe = np.arange(n) * k // n
    I, J = np.triu_indices(n, 1)
    p = np.where(gruppe[I] == gruppe[J], grad * anteil_innen / (n / k - 1), grad * (1 - anteil_innen) / (n - n / k))
    wahl = BlockZufall(seed).random(len(I)) < p
    return netz("gepflanzte Gruppen", n, list(zip(I[wahl].tolist(), J[wahl].tolist()))), gruppe
