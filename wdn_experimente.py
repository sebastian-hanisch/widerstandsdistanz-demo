"""Die Rechnungen der Experimente (ohne Streamlit): Ausfallvergleich, Entartung, Netzausbau, Reparaturversuche.

Dieselben Funktionen rechnen die Seite (live) und die vorgerechneten Tabellen (`tools/vorrechnen.py`).
"""

from dataclasses import dataclass

import numpy as np

import wdn_ausfall as AF
import wdn_masse as M
import wdn_netze as N
import wdn_statistik as ST
import wdn_widerstand as W
from wdn_zufall import ZWECK_KLEIN, ZWECK_PAARE, ZWECK_WAHR1, ZWECK_WAHR2, abgeleitet

PAARE = 300
PROBEN = 1600
PROBEN_KLEIN = (50, 200)

# Maße des Ausfallvergleichs in der Reihenfolge der Anzeige
AUSFALL_MASSE = (M.DISTANZ, M.WIDERSTAND, M.MINCUT, M.MINCUT_DIST, M.GRADTERM, M.ISOLATION, M.STICH50, M.STICH200)
# Zusätzliche Maße (Experiment 4: dieselben Reparaturmaße beim Ausfall)
REPARATUR_BEIM_AUSFALL = (M.VERSTAERKT, M.MINUS_LPLUS, M.KOSINUS, M.PPR, M.ADAMIC, M.DIST_WEGE)


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 1: Ausfall
# ----------------------------------------------------------------------------------------------------------------------------------

@dataclass
class Netzmasse:
    """Alles, was für ein Netz und seine Paare nicht von p abhängt."""
    paare: np.ndarray
    grad: np.ndarray
    a_st: np.ndarray
    werte: dict          # Maß → Werte je Paar (größer = „eher getrennt“)
    R: np.ndarray        # R je Paar
    D: np.ndarray        # Distanz je Paar


def netzmasse(g: N.Netz, seed: int, famnr: int, anzahl: int = PAARE, extra: bool = True) -> Netzmasse:
    paare = AF.zufallspaare(g.n, anzahl, abgeleitet(seed, ZWECK_PAARE, famnr))
    S, T = paare[:, 0], paare[:, 1]
    A = N.adjazenz(g)
    d = A.sum(axis=1)
    Lp = W.pseudoinverse(g)
    R = W.widerstand_aus(Lp)
    Dm = M.abstaende(A)
    mc = M.minschnitte(g, paare)
    D = Dm[S, T].astype(float)
    werte = {M.DISTANZ: D, M.WIDERSTAND: R[S, T], M.MINCUT: -mc.astype(float), M.MINCUT_DIST: -mc * 10_000.0 + D,
             M.GRADTERM: M.gradterm(d, S, T)}
    if extra:
        Z = M.wegezahlen(A, Dm)
        werte[M.VERSTAERKT] = M.verstaerkt_matrix(R, A)[S, T]
        werte[M.MINUS_LPLUS] = -Lp[S, T]
        werte[M.KOSINUS] = -M.kosinus_matrix(Lp)[S, T]
        werte[M.PPR] = -np.round(M.ppr_grad_matrix(A)[S, T], 12)
        werte[M.ADAMIC] = -M.adamic_adar_matrix(A)[S, T]
        werte[M.DIST_WEGE] = M.lexikografischer_rang(D, M.distanz_wege_zweitschluessel(A, Dm, Z)[S, T])
    return Netzmasse(paare, d, A[S, T], werte, R[S, T], D)


@dataclass
class Ausfallzelle:
    p: float
    y1: np.ndarray               # P(getrennt) je Paar, Wahrheitsstichprobe 1
    y2: np.ndarray
    haelften: object             # Rangkorrelation der geraden gegen die ungeraden Proben von Stichprobe 1 (oder None)
    messbar: bool
    isolation: np.ndarray        # Wert je Paar (nicht logarithmiert, nur zur Anzeige)
    klein: dict                  # 50 / 200 → Anteil getrennt je Paar (eigene, von der Wahrheit unabhängige Proben)
    rho1: dict                   # Maß → Rangkorrelation gegen Stichprobe 1
    rho2: dict


def ausfallzelle(g: N.Netz, nm: Netzmasse, p: float, p_nr: int, seed: int, famnr: int, proben: int = PROBEN) -> Ausfallzelle:
    S, T = nm.paare[:, 0], nm.paare[:, 1]
    nummer = famnr * 100 + p_nr
    y1, haelften = AF.stichprobe(g, nm.paare, p, proben, abgeleitet(seed, ZWECK_WAHR1, nummer))
    y2, _ = AF.stichprobe(g, nm.paare, p, proben, abgeleitet(seed, ZWECK_WAHR2, nummer))
    klein = {k: AF.stichprobe(g, nm.paare, p, k, abgeleitet(seed, ZWECK_KLEIN, nummer * 10 + i))[0] for i, k in enumerate(PROBEN_KLEIN)}
    ok = ST.messbar(y1) and ST.messbar(y2)
    werte = dict(nm.werte)
    werte[M.ISOLATION] = M.isolation_log(nm.grad, S, T, nm.a_st, p)
    werte[M.STICH50] = klein[PROBEN_KLEIN[0]]
    werte[M.STICH200] = klein[PROBEN_KLEIN[1]]
    rho1 = {m: ST.rangkorrelation(v, y1) if ok else None for m, v in werte.items()}
    rho2 = {m: ST.rangkorrelation(v, y2) if ok else None for m, v in werte.items()}
    return Ausfallzelle(p, y1, y2, ST.rangkorrelation(haelften[0], haelften[1]), ok, M.isolation(nm.grad, S, T, nm.a_st, p), klein, rho1, rho2)


def zeile(zelle: Ausfallzelle) -> dict:
    """Kompakte Zeile (für die Tabellen und das Verdikt)."""
    return {"p": zelle.p, "messbar": zelle.messbar, "rho1": zelle.rho1, "rho2": zelle.rho2, "haelften": zelle.haelften}


def ordnungszaehlung(werte: np.ndarray, wahr: np.ndarray) -> tuple:
    """Über alle Paare von Knotenpaaren mit verschiedener wahrer Trennwahrscheinlichkeit: (richtig geordnet, falsch, vom Maß gleich bewertet)."""
    v = np.round(np.asarray(werte, dtype=float), 9)
    w = np.round(np.asarray(wahr, dtype=float), 12)
    I, J = np.triu_indices(len(v), 1)
    dw = np.sign(w[I] - w[J])
    dv = np.sign(v[I] - v[J])
    zaehlt = dw != 0
    return int(np.sum(zaehlt & (dv * dw > 0))), int(np.sum(zaehlt & (dv * dw < 0))), int(np.sum(zaehlt & (dv == 0)))


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 2: Entartung (R gegen den Gradterm auf allen Nichtnachbarpaaren)
# ----------------------------------------------------------------------------------------------------------------------------------

@dataclass
class Entartung:
    n: int
    m: int
    mittlerer_grad: float
    paare: int
    rho: float
    abweichung: float                     # Median |R − Gradterm| / R
    R: np.ndarray
    gt: np.ndarray
    quer: object                          # Wahr je Paar, wenn die Enden in verschiedenen Hälften liegen (nur bei zwei Hälften)
    abweichung_innen: object = None
    abweichung_quer: object = None


def entartung(g: N.Netz, haelften: bool = False) -> Entartung:
    A = N.adjazenz(g)
    d = A.sum(axis=1)
    R = W.widerstand(g)
    I, J = np.nonzero(np.triu(1 - A, 1))
    if len(I) == 0:
        raise ValueError("keine Nichtnachbarpaare")
    Rv = R[I, J]
    gt = M.gradterm(d, I, J)
    rel = np.abs(Rv - gt) / Rv
    rho = ST.rangkorrelation(Rv, gt)
    erg = Entartung(g.n, len(g.kanten), float(2 * len(g.kanten) / g.n), len(I), rho, float(np.median(rel)), Rv, gt, None)
    if haelften:
        seite = N.haelfte_von(g)
        quer = seite[I] != seite[J]
        erg.quer = quer
        erg.abweichung_innen = float(np.median(rel[~quer]))
        erg.abweichung_quer = float(np.median(rel[quer])) if quer.any() else None
    return erg


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 3: eine neue Kante, Ziel ist die kleinste Summe aller Paarwiderstände (Kirchhoff-Index)
# ----------------------------------------------------------------------------------------------------------------------------------

ZUFAELLIG, MAX_R, MAX_GRADTERM, MAX_DISTANZ, DIST_GRAD, FIEDLER, MAX_ZAEHLER = ("zufaellig", "max_r", "max_gradterm", "max_distanz", "distanz_grad",
                                                                              "fiedler", "max_zaehler")
REGELN = (ZUFAELLIG, MAX_R, MAX_GRADTERM, MAX_DISTANZ, DIST_GRAD, FIEDLER, MAX_ZAEHLER)
FIEDLER_LUECKE = 1e-8


@dataclass
class Ausbau:
    U: np.ndarray                 # Endpunkte aller fehlenden Kanten
    V: np.ndarray
    ki: float                     # Kirchhoff-Index vorher
    senkung: np.ndarray           # Senkung je neuer Kante
    R: np.ndarray                 # R je neuer Kante vor dem Einbau
    zaehler: np.ndarray           # |L⁺(e_u − e_v)|² je neuer Kante
    gradterm: np.ndarray
    distanz: np.ndarray
    wahl: dict                    # Regel → Indizes der gleichrangig besten Kanten (None, wenn die Regel nicht bestimmbar ist)
    anteil: dict                  # Regel → erreichte / beste Senkung (Mittel über die gleichrangigen)


def senkungen(Lp: np.ndarray, U: np.ndarray, V: np.ndarray):
    """(Senkung des Kirchhoff-Index, R_uv, |L⁺(e_u − e_v)|²) je neuer Kante nach Sherman-Morrison: n·Zähler / (1 + R)."""
    n = len(Lp)
    d = np.diag(Lp)
    R = d[U] + d[V] - 2 * Lp[U, V]
    Q = Lp @ Lp
    q = np.diag(Q)
    zaehler = q[U] + q[V] - 2 * Q[U, V]
    return n * zaehler / (1 + R), R, zaehler


def _fiedler(g: N.Netz):
    A = N.adjazenz(g)
    ew, ev = np.linalg.eigh(np.diag(A.sum(axis=1)) - A)
    if g.n < 3 or ew[2] - ew[1] < FIEDLER_LUECKE:
        return None
    return ev[:, 1]


def _beste(werte: np.ndarray) -> np.ndarray:
    w = ST.gerundet(werte)
    return np.flatnonzero(w >= w.max())


def ausbau(g: N.Netz) -> Ausbau:
    A = N.adjazenz(g)
    U, V = np.nonzero(np.triu(1 - A, 1))
    if len(U) == 0:
        raise ValueError("im vollständigen Netz fehlt keine Kante")
    Lp = W.pseudoinverse(g)
    senk, R, zaehler = senkungen(Lp, U, V)
    d = A.sum(axis=1)
    gt = M.gradterm(d, U, V)
    dist = M.abstaende(A)[U, V].astype(float)
    f = _fiedler(g)
    wahl = {ZUFAELLIG: np.arange(len(U)), MAX_R: _beste(R), MAX_GRADTERM: _beste(gt), MAX_DISTANZ: _beste(dist),
            DIST_GRAD: _beste(M.lexikografischer_rang(dist, gt)), FIEDLER: None if f is None else _beste((f[U] - f[V]) ** 2),
            MAX_ZAEHLER: _beste(zaehler)}
    best = senk.max()
    anteil = {r: None if w is None else float(senk[w].mean() / best) for r, w in wahl.items()}
    return Ausbau(U, V, W.kirchhoff_index(Lp), senk, R, zaehler, gt, dist, wahl, anteil)


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 4: Reparaturversuche (dichte Netze, „nah“ nach dem Maß gegen „nah“ nach der Konstruktion)
# ----------------------------------------------------------------------------------------------------------------------------------

REP_MASSE = (M.DISTANZ, M.WIDERSTAND, M.VERSTAERKT, M.MINUS_LPLUS, M.KOSINUS, M.PPR, M.ADAMIC, M.DIST_WEGE)


@dataclass
class Reparaturnetz:
    """Rangschlüssel je Maß als n×n-Matrizen bzw. Bausteine; kleiner = näher."""
    D: np.ndarray
    R: np.ndarray
    verst: np.ndarray
    Lp: np.ndarray
    kos: np.ndarray
    aa: np.ndarray
    zweit: np.ndarray
    A: np.ndarray
    gt: np.ndarray


def reparatur_bausteine(g: N.Netz) -> Reparaturnetz:
    A = N.adjazenz(g)
    d = A.sum(axis=1)
    Lp = W.pseudoinverse(g)
    R = W.widerstand_aus(Lp)
    Dm = M.abstaende(A)
    Z = M.wegezahlen(A, Dm)
    return Reparaturnetz(Dm, R, M.verstaerkt_matrix(R, A), Lp, M.kosinus_matrix(Lp), M.adamic_adar_matrix(A), M.distanz_wege_zweitschluessel(A, Dm, Z),
                         A, 1.0 / d[:, None] + 1.0 / d[None, :])


def zeilenschluessel(b: Reparaturnetz, ppr_grad: np.ndarray, i: int, andere: np.ndarray) -> dict:
    """Je Maß die Werte vom Anfrageknoten i zu allen anderen (kleiner = näher), Gleichstände auf 9 (PPR 13) Stellen gerundet."""
    return {M.DISTANZ: b.D[i, andere].astype(float), M.WIDERSTAND: ST.gerundet(b.R[i, andere]), M.VERSTAERKT: ST.gerundet(b.verst[i, andere]),
            M.MINUS_LPLUS: ST.gerundet(-b.Lp[i, andere]), M.KOSINUS: ST.gerundet(-b.kos[i, andere]), M.PPR: -np.round(ppr_grad[i, andere], 13),
            M.ADAMIC: ST.gerundet(-b.aa[i, andere]), M.DIST_WEGE: M.lexikografischer_rang(b.D[i, andere], b.zweit[i, andere])}


def bewerte(werte: np.ndarray, wahr: np.ndarray, mass: str) -> float:
    return ST.anteil_unter_besten(werte, wahr, 10) if mass == "p10" else ST.auc(werte, wahr)


def gradterm_bezug(b: Reparaturnetz, schluessel_matrix: np.ndarray, I: np.ndarray, J: np.ndarray) -> float:
    """Rangkorrelation eines Maßes mit dem Gradterm über die genannten (nicht benachbarten) Paare."""
    return ST.rangkorrelation(schluessel_matrix[I, J], b.gt[I, J])
