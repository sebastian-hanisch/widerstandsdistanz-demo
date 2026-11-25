"""Effektiver Widerstand, Pseudoinverse und Kirchhoff-Index (ohne Streamlit, nur numpy).

Jede Kante hat den Widerstand 1 Ohm. Gerechnet wird über den um J/n verschobenen Laplace (J = Matrix aus lauter Einsen): L⁺ = (L + J/n)⁻¹ − J/n.
Das gilt nur für zusammenhängende Netze; für andere gibt es einen Fehler statt einer stillen Zahl (kein `pinv`).
Zweite Rechenwege (geerdeter Laplace, Trefferzeiten, Spannbaum-Zählung) stehen in den Tests.
"""

import numpy as np

import wdn_netze as N


def pseudoinverse(g: N.Netz) -> np.ndarray:
    """L⁺ eines zusammenhängenden Netzes."""
    if g.n < 2 or not N.ist_zusammenhaengend(g):
        raise ValueError("L⁺ und R nur für zusammenhängende Netze mit mindestens 2 Knoten")
    A = N.adjazenz(g)
    J = 1.0 / g.n
    return np.linalg.inv(np.diag(A.sum(axis=1)) - A + J) - J


def widerstand_aus(Lp: np.ndarray) -> np.ndarray:
    """R_st = L⁺_ss + L⁺_tt − 2·L⁺_st (Diagonale 0)."""
    d = np.diag(Lp)
    R = d[:, None] + d[None, :] - 2 * Lp
    np.fill_diagonal(R, 0.0)
    return R


def widerstand(g: N.Netz) -> np.ndarray:
    return widerstand_aus(pseudoinverse(g))


def kirchhoff_index(Lp: np.ndarray) -> float:
    """Summe der effektiven Widerstände über alle ungeordneten Paare: KI = n·Spur(L⁺)."""
    return float(len(Lp) * np.trace(Lp))
