"""Gütemaße und das Kriterium für einen „klaren“ Abstand (ohne Streamlit; numpy und scipy.stats).

* `rangkorrelation`: Spearman; vorher werden die Werte auf 9 Nachkommastellen gerundet, damit rechnerisch gleiche Werte gleich bleiben. Ist eine Seite konstant,
  gibt es keinen Wert (`None`), nie 0.
* `messbar`: Die Zielgröße P(getrennt) ist nicht messbar, wenn mindestens 95 % der Paare denselben Wert haben.
* `klar`: Der Abstand R − Gegner ist klar, wenn er in zwei unabhängigen Ausfallstichproben dasselbe Vorzeichen hat und in beiden mindestens 0,05 beträgt.
"""

import numpy as np
from scipy.stats import rankdata

RUNDUNG = 9
SCHWELLE_KLAR = 0.05
ANTEIL_NICHT_MESSBAR = 0.95
TOL = 1e-12

R_VORN, GEGNER_VORN, UNKLAR = 1, -1, 0


def gerundet(x) -> np.ndarray:
    return np.round(np.asarray(x, dtype=float), RUNDUNG)


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    return float(a @ b / np.sqrt((a @ a) * (b @ b)))


def rangkorrelation(x, y):
    """Spearman-Rangkorrelation (Gleichstände mit mittlerem Rang) oder None, wenn eine Seite konstant ist."""
    x, y = gerundet(x), gerundet(y)
    if len(x) < 2 or x.min() == x.max() or y.min() == y.max():
        return None
    return _pearson(rankdata(x), rankdata(y))


def messbar(y) -> bool:
    _, anzahl = np.unique(np.asarray(y), return_counts=True)
    return bool(anzahl.max() < ANTEIL_NICHT_MESSBAR * len(y) - TOL)


def klar(r1, r2, g1, g2) -> int:
    """+1: R klar vorn; −1: Gegner klar vorn; 0: kein klarer Unterschied. Fehlt ein Wert, gibt es keinen klaren Unterschied."""
    if None in (r1, r2, g1, g2):
        return UNKLAR
    a, b = r1 - g1, r2 - g2
    if min(a, b) >= SCHWELLE_KLAR - TOL:
        return R_VORN
    if max(a, b) <= -SCHWELLE_KLAR + TOL:
        return GEGNER_VORN
    return UNKLAR


def anteil_unter_besten(werte: np.ndarray, wahr: np.ndarray, k: int = 10) -> float:
    """Anteil richtiger unter den k kleinsten Werten (kleiner = näher); bei Gleichstand an der Grenze die erwartete Quote einer zufälligen Reihenfolge."""
    grenze = np.partition(werte, k - 1)[k - 1]
    sicher = werte < grenze
    gleich = werte == grenze
    rest = k - sicher.sum()
    return float((wahr[sicher].sum() + wahr[gleich].sum() * rest / gleich.sum()) / k)


def auc(werte: np.ndarray, positiv: np.ndarray) -> float:
    """Fläche unter der ROC-Kurve (kleiner = näher): Wahrscheinlichkeit, dass ein positives Ziel näher steht als ein negatives, Gleichstand zählt ½."""
    r = rankdata(-werte)
    k = int(positiv.sum())
    if k == 0 or k == len(werte):
        raise ValueError("AUC braucht positive und negative Ziele")
    return float((r[positiv].sum() - k * (k + 1) / 2) / (k * (len(werte) - k)))
