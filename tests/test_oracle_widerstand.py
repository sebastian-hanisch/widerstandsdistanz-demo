"""Orakel: effektiver Widerstand und Kirchhoff-Index gegen zwei andere Rechenwege in Brüchen (geerdeter Laplace, Spannbaum-Zählung) und gegen die
Zählung aufspannender 2-Wälder. `networkx.resistance_distance` dient bewusst nicht als Orakel (rechnete in einer anderen Demo der Reihe auf einem Netz falsch).
Dazu die Neuberechnung nach jeder neuen Kante gegen die Sherman-Morrison-Formel."""

import itertools
from fractions import Fraction

import numpy as np
import pytest

import wdn_experimente as X
import wdn_netze as N
import wdn_widerstand as W
from conftest import widerstand_geerdet, widerstand_spannbaeume, wurzeln, zufallsnetz_klein


@pytest.mark.parametrize("seed", range(25))
def test_widerstand_gegen_brueche(seed):
    n = 4 + seed % 6
    g = zufallsnetz_klein(n, n - 1 + seed % 5, seed)
    R = W.widerstand(g)
    for s, t in itertools.combinations(range(n), 2):
        soll = widerstand_geerdet(n, g.kanten, s, t)
        assert R[s, t] == pytest.approx(float(soll), abs=1e-9)
        if (s + t) % 3 == 0:
            assert widerstand_spannbaeume(n, g.kanten, s, t) == soll


def _ki_zweiwaelder(n, kanten):
    """KI = (Zahl der aufspannenden 2-Wälder, je mit |Teil 1|·|Teil 2| gewichtet) / (Zahl der Spannbäume)."""
    def waelder(anzahl):
        for T in itertools.combinations(kanten, anzahl):
            k = wurzeln(n, T)
            if len(set(k)) == n - anzahl:
                yield k

    baeume = sum(1 for _ in waelder(n - 1))
    trennend = 0
    for k in waelder(n - 2):
        gr = [k.count(x) for x in set(k)]
        trennend += gr[0] * gr[1]
    return Fraction(trennend, baeume)


@pytest.mark.parametrize("seed", range(20))
def test_kirchhoff_index_gegen_zweiwaelder_und_neuberechnung(seed):
    n = 4 + seed % 3
    g = zufallsnetz_klein(n, n + seed % 3, 100 + seed)
    assert W.kirchhoff_index(W.pseudoinverse(g)) == pytest.approx(float(_ki_zweiwaelder(n, g.kanten)), abs=1e-9)
    if not N.fehlende_kanten(g):
        return
    erg = X.ausbau(g)
    for i in range(len(erg.U)):
        h = N.mit_kante(g, int(erg.U[i]), int(erg.V[i]))
        assert erg.ki - float(_ki_zweiwaelder(n, h.kanten)) == pytest.approx(erg.senkung[i], abs=1e-8)


def test_kirchhoff_index_gegen_eigenwerte():
    g = zufallsnetz_klein(30, 60, 9)
    A = N.adjazenz(g)
    ew = np.linalg.eigvalsh(np.diag(A.sum(1)) - A)
    assert W.kirchhoff_index(W.pseudoinverse(g)) == pytest.approx(30 * sum(1 / x for x in ew[1:]))
