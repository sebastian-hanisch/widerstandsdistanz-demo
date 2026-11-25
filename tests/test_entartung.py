"""Entartung an den Handformeln: vollständiges Netz und zwei vollständige Hälften mit einer Brücke."""

import itertools

import numpy as np
import pytest

import wdn_experimente as X
import wdn_netze as N
import wdn_widerstand as W


@pytest.mark.parametrize("n", [4, 6, 10])
def test_vollstaendiges_netz(n):
    g = N.vollstaendig(n)
    R = W.widerstand(g)
    d = N.grade(g)
    for s, t in itertools.combinations(range(n), 2):
        assert R[s, t] == pytest.approx(2 / n)
        assert (1 / d[s] + 1 / d[t] - R[s, t]) / R[s, t] == pytest.approx(1 / (n - 1))
    with pytest.raises(ValueError):
        X.entartung(g)


@pytest.mark.parametrize("k", [4, 6])
def test_zwei_cliquen_mit_einer_bruecke(k):
    kanten = list(itertools.combinations(range(k), 2)) + [(i + k, j + k) for i, j in itertools.combinations(range(k), 2)] + [(0, k)]
    g = N.netz("Brücke", 2 * k, kanten)
    R = W.widerstand(g)
    d = N.grade(g)
    assert R[0, k] == pytest.approx(1.0) and 1 / d[0] + 1 / d[k] == pytest.approx(2 / k)
    assert R[1, 2] == pytest.approx(2 / k) and 1 / d[1] + 1 / d[2] == pytest.approx(2 / (k - 1))
    assert R[1, k + 1] == pytest.approx(1 + 4 / k)
    e = X.entartung(g)
    assert e.paare == 2 * k * (2 * k - 1) // 2 - len(kanten)


def test_entartung_zaehlt_nur_nichtnachbarn(hand):
    e = X.entartung(hand)
    assert e.paare == 15 - 7 and e.n == 6 and e.mittlerer_grad == pytest.approx(14 / 6)
    assert (e.R >= e.gt - 1e-9).all()                                    # untere Schranke für Nichtnachbarn
    assert e.quer is None


def test_haelften_getrennt_ausgewertet():
    g = N.zwei_haelften(100, 12, 2, 5)
    e = X.entartung(g, haelften=True)
    assert e.quer.any() and (~e.quer).any()
    rel = np.abs(e.R - e.gt) / e.R
    assert e.abweichung_quer == pytest.approx(np.median(rel[e.quer])) and e.abweichung_innen < e.abweichung_quer
