"""Die Maße, die verglichen werden: je eine kleine Funktion (ohne Streamlit; numpy, für den Maximalfluss scipy).

Für den Ausfallvergleich gilt überall dieselbe Richtung: **größerer Wert = „eher getrennt“** (weiter auseinander). Ähnlichkeiten (gemeinsame Nachbarn, L⁺, PageRank)
gehen darum mit negativem Vorzeichen ein.

Was jedes Maß weiß:
* Distanz: nur den kürzesten Weg (Breitensuche).
* min cut: die Zahl kantendisjunkter Wege zwischen s und t (ein Maximalfluss je Paar); „min cut, dann Distanz“ entscheidet Gleichstände nach der Distanz.
* Gradterm 1/d_s + 1/d_t: nur die zwei Endgrade.
* Isolationsnäherung: Wahrscheinlichkeit, dass s oder t keine Kante mehr hat, p^d_s + p^d_t − p^(d_s+d_t−a_st) (a_st = 1 bei Nachbarn); kennt p.
* effektiver Widerstand R: alle Wege und ihre Längen, aber nicht p.
"""

import numpy as np

import wdn_netze as N

R_TXT = "R"
DISTANZ, WIDERSTAND, MINCUT, MINCUT_DIST, GRADTERM, ISOLATION = "distanz", "r", "mincut", "mincut_dist", "gradterm", "isolation"
STICH50, STICH200 = "stich50", "stich200"
VERSTAERKT, MINUS_LPLUS, KOSINUS, PPR, ADAMIC, DIST_WEGE = "verstaerkt", "minus_lplus", "kosinus", "ppr", "adamic", "dist_wege"

# Voreinstellung der Sprungwahrscheinlichkeit beim zufälligen Neustart (PPR/Grad), wo nicht abgestimmt wird.
SPRUNG_VOREINSTELLUNG = 0.15


def abstaende(A: np.ndarray) -> np.ndarray:
    """Alle kürzesten Abstände (Kantenzahl) als ganzzahlige Matrix, −1 = nicht erreichbar. Breitensuche von allen Knoten zugleich über Matrixprodukte."""
    n = len(A)
    B = A.astype(np.float32)
    D = np.full((n, n), -1, dtype=np.int64)
    np.fill_diagonal(D, 0)
    front = np.eye(n, dtype=np.float32)
    stufe = 0
    while True:
        stufe += 1
        neu = (front @ B > 0) & (D < 0)
        if not neu.any():
            return D
        D[neu] = stufe
        front = neu.astype(np.float32)


def wegezahlen(A: np.ndarray, D: np.ndarray) -> np.ndarray:
    """Zahl der kürzesten Wege zwischen je zwei Knoten (als Gleitkommazahl, auf großen Gittern wächst sie schnell)."""
    n = len(A)
    Z = np.eye(n)
    Z[D == 1] = 1.0
    for k in range(2, int(D.max()) + 1):
        schritt = np.where(D == k - 1, Z, 0.0) @ A
        Z[D == k] = schritt[D == k]
    return Z


def minschnitte(g: N.Netz, paare: np.ndarray) -> np.ndarray:
    """Kleinste Zahl von Kanten, deren Wegnahme s und t trennt, je Paar (Maximalfluss mit Kapazität 1 je Richtung)."""
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import maximum_flow

    k = N.kantenfeld(g)
    zeilen = np.concatenate([k[:, 0], k[:, 1]])
    spalten = np.concatenate([k[:, 1], k[:, 0]])
    C = csr_matrix((np.ones(len(zeilen), dtype=np.int32), (zeilen, spalten)), shape=(g.n, g.n))
    return np.array([maximum_flow(C, int(s), int(t)).flow_value for s, t in paare], dtype=np.int64)


def gradterm(d: np.ndarray, S: np.ndarray, T: np.ndarray) -> np.ndarray:
    return 1.0 / d[S] + 1.0 / d[T]


def isolation(d: np.ndarray, S, T, a_st, p: float) -> np.ndarray:
    """P(s oder t hat keine Kante mehr): p^d_s + p^d_t − p^(d_s + d_t − a_st); die gemeinsame Kante zweier Nachbarn zählt nur einmal."""
    ds, dt = d[S].astype(float), d[T].astype(float)
    return p ** ds + p ** dt - p ** (ds + dt - np.asarray(a_st, dtype=float))


def isolation_log(d: np.ndarray, S, T, a_st, p: float) -> np.ndarray:
    """Logarithmus der Isolationsnäherung, ohne Unterlauf bei großen Graden (sonst würden sehr kleine Werte zu Gleichständen). Nur für 0 < p < 1."""
    if not 0 < p < 1:
        raise ValueError("p zwischen 0 und 1")
    ds, dt = d[S].astype(float), d[T].astype(float)
    m = np.minimum(ds, dt)
    rest = p ** (ds - m) + p ** (dt - m) - p ** (ds + dt - np.asarray(a_st, dtype=float) - m)
    return m * np.log(p) + np.log(rest)


def verstaerkt_matrix(R: np.ndarray, A: np.ndarray) -> np.ndarray:
    """Verstärkte Widerstandsdistanz (amplified commute distance) auf der R-Skala: R − 1/d_s − 1/d_t + 2·a_st / (d_s·d_t), Diagonale 0."""
    d = A.sum(axis=1)
    V = R - 1.0 / d[:, None] - 1.0 / d[None, :] + 2.0 * A / np.outer(d, d)
    np.fill_diagonal(V, 0.0)
    return V


def kosinus_matrix(Lp: np.ndarray) -> np.ndarray:
    """Kosinusform von L⁺ (zentriert und normiert): L⁺_st / sqrt(L⁺_ss · L⁺_tt). Groß heißt „nah“."""
    w = np.sqrt(np.diag(Lp))
    return Lp / np.outer(w, w)


def ppr_matrix(A: np.ndarray, sprung: float) -> np.ndarray:
    """Zeile s: Aufenthaltsanteile der Irrfahrt ab s, die in jedem Schritt mit `sprung` nach s zurückspringt (personalisiertes PageRank)."""
    n = len(A)
    P = A / A.sum(axis=1, keepdims=True)
    return sprung * np.linalg.inv(np.eye(n) - (1.0 - sprung) * P)


def ppr_grad_matrix(A: np.ndarray, sprung: float = SPRUNG_VOREINSTELLUNG) -> np.ndarray:
    """PPR/Grad: Aufenthaltsanteil am Ziel durch dessen Grad, über beide Richtungen addiert (symmetrisch). Groß heißt „nah“."""
    d = A.sum(axis=1)
    X = ppr_matrix(A, sprung) / d[None, :]
    return X + X.T


def adamic_adar_matrix(A: np.ndarray) -> np.ndarray:
    """Adamic-Adar: Summe über gemeinsame Nachbarn w von 1 / ln(Grad von w). Ein gemeinsamer Nachbar zweier Knoten hat mindestens Grad 2."""
    d = A.sum(axis=1)
    return (A / np.log(np.maximum(d, 2.0))) @ A


def distanz_wege_zweitschluessel(A: np.ndarray, D: np.ndarray, Z: np.ndarray) -> np.ndarray:
    """Gleichstandsschlüssel von „Distanz, dann Wegezahl“ (kleiner = näher): bei Nachbarn die halbe Zahl der nicht gemeinsamen Nachbarn
    ((d_s + d_t)/2 − gemeinsame), sonst minus die Zahl der kürzesten Wege."""
    d = A.sum(axis=1)
    gemeinsam = A @ A
    return np.where(A > 0, (d[:, None] + d[None, :]) / 2.0 - gemeinsam, -Z)


def lexikografischer_rang(*spalten) -> np.ndarray:
    """Rang nach mehreren Spalten nacheinander (auf 9 Stellen gerundet), Gleichstände bleiben Gleichstände."""
    M = np.stack([np.round(np.asarray(s, dtype=float), 9) for s in spalten], axis=1)
    _, umkehr = np.unique(M, axis=0, return_inverse=True)
    return umkehr.ravel().astype(float)
