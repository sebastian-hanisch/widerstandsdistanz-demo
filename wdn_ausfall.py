"""Kantenausfall: jede Kante fällt unabhängig mit Wahrscheinlichkeit p aus; gesucht ist P(s und t sind danach getrennt) (ohne Streamlit; numpy und scipy).

`stichprobe` zählt in Zufallsproben, wie oft jedes Paar getrennt ist (eine Komponentensuche je Probe liefert alle Paare zugleich; hier werden viele Proben als ein
großes Netz aus lauter getrennten Kopien auf einmal gelöst). `exakt` zählt auf kleinen Netzen alle 2^m Ausfallmuster.
"""

import numpy as np

import wdn_netze as N
from wdn_zufall import BlockZufall

EXAKT_MAX_KANTEN = 16
BLOCK = 200                       # Proben je gemeinsamer Komponentensuche


def _labels(n: int, kanten: np.ndarray, da: np.ndarray) -> np.ndarray:
    """Komponentennummern für B Proben zugleich. `da` ist B×m (wahr = Kante ist noch da); Rückgabe B×n."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    B = len(da)
    probe, kante = np.nonzero(da)
    u = kanten[kante, 0] + probe * n
    v = kanten[kante, 1] + probe * n
    M = coo_matrix((np.ones(len(u), dtype=np.int8), (u, v)), shape=(B * n, B * n))
    _, lab = connected_components(M, directed=False)
    return lab.reshape(B, n)


def ausfallmuster(m: int, p: float, proben: int, rng: BlockZufall):
    """Erzeugt die Muster blockweise: je Probe m Werte der Folge; die Kante ist da, wenn der Wert mindestens p ist."""
    fertig = 0
    while fertig < proben:
        B = min(BLOCK, proben - fertig)
        yield rng.random(B * m).reshape(B, m) >= p
        fertig += B


def stichprobe(g: N.Netz, paare: np.ndarray, p: float, proben: int, seed: int):
    """(Anteil getrennt je Paar, 2×Paare mit den Anteilen der geraden und ungeraden Proben)."""
    if proben < 2:
        raise ValueError("mindestens 2 Proben")
    kanten = N.kantenfeld(g)
    S, T = paare[:, 0], paare[:, 1]
    treffer = np.zeros((2, len(paare)))
    anzahl = np.zeros(2)
    erste = 0
    for da in ausfallmuster(len(kanten), p, proben, BlockZufall(seed)):
        lab = _labels(g.n, kanten, da)
        getrennt = lab[:, S] != lab[:, T]
        gerade = (np.arange(len(da)) + erste) % 2 == 0
        treffer[0] += getrennt[gerade].sum(axis=0)
        treffer[1] += getrennt[~gerade].sum(axis=0)
        anzahl += [gerade.sum(), (~gerade).sum()]
        erste += len(da)
    return treffer.sum(axis=0) / proben, treffer / anzahl[:, None]


def exakt(g: N.Netz, paare: np.ndarray, p: float) -> np.ndarray:
    """P(getrennt) je Paar durch Aufzählung aller 2^m Ausfallmuster (nur für kleine Netze)."""
    kanten = N.kantenfeld(g)
    m = len(kanten)
    if m > EXAKT_MAX_KANTEN:
        raise ValueError(f"exakt nur bis {EXAKT_MAX_KANTEN} Kanten")
    muster = ((np.arange(1 << m)[:, None] >> np.arange(m)[None, :]) & 1).astype(bool)      # wahr = Kante da
    gewicht = np.prod(np.where(muster, 1.0 - p, p), axis=1)
    summe = np.zeros(len(paare))
    for start in range(0, len(muster), 2048):
        teil = muster[start:start + 2048]
        lab = _labels(g.n, kanten, teil)
        summe += gewicht[start:start + 2048] @ (lab[:, paare[:, 0]] != lab[:, paare[:, 1]])
    return summe


def p_leitung(p: float) -> float:
    """Eine Leitung: getrennt genau dann, wenn sie ausfällt."""
    return p


def p_drei_wege(p: float, k: int = 3, laenge: int = 4) -> float:
    """k getrennte Wege der gegebenen Länge: getrennt, wenn jeder Weg mindestens eine Kante verliert."""
    return (1.0 - (1.0 - p) ** laenge) ** k


def alle_paare(n: int) -> np.ndarray:
    I, J = np.triu_indices(n, 1)
    return np.stack([I, J], axis=1)


def zufallspaare(n: int, anzahl: int, seed: int) -> np.ndarray:
    """`anzahl` verschiedene ungeordnete Paare (alle, wenn es nicht mehr gibt), sortiert."""
    from wdn_rng import SplitMix64

    if anzahl >= n * (n - 1) // 2:
        return alle_paare(n)
    rng = SplitMix64(seed)
    wahl = set()
    while len(wahl) < anzahl:
        a, b = rng.below(n), rng.below(n)
        if a != b:
            wahl.add((min(a, b), max(a, b)))
    return np.array(sorted(wahl), dtype=np.int64)
