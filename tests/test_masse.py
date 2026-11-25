"""Die Maße an Handrechnungen (Handnetz, Besen): jede Einheit für sich."""

from fractions import Fraction as Fr

import numpy as np
import pytest

import wdn_ausfall as AF
import wdn_experimente as X
import wdn_masse as M
import wdn_netze as N
import wdn_widerstand as W


def test_widerstand_handnetz_von_hand(hand):
    R = W.widerstand(hand)
    # im Dreieck: 1 Ohm parallel zu 2 Ohm = 2/3; über die Tür: 2/3 + 1 + 2/3 = 7/3
    assert R[0, 1] == pytest.approx(2 / 3) and R[0, 4] == pytest.approx(7 / 3) and R[2, 3] == pytest.approx(1.0)
    assert sum(R[u, v] for u, v in hand.kanten) == pytest.approx(5.0)          # Foster: n − 1


def test_isolation_formel_von_hand(hand):
    d = N.grade(hand).astype(float)
    p = 0.15
    nachbar = M.isolation(d, np.array([0]), np.array([1]), np.array([1]), p)[0]
    fern = M.isolation(d, np.array([0]), np.array([4]), np.array([0]), p)[0]
    assert nachbar == pytest.approx(float(Fr(333, 8000))) == pytest.approx(0.041625)
    assert fern == pytest.approx(2 * p**2 - p**4) == pytest.approx(0.04449375)
    assert np.exp(M.isolation_log(d, np.array([0]), np.array([4]), np.array([0]), p))[0] == pytest.approx(fern)


def test_isolation_log_ohne_unterlauf():
    d = np.array([400.0, 500.0, 600.0])
    logs = M.isolation_log(d, np.array([0, 0]), np.array([1, 2]), np.array([0, 0]), 0.05)
    assert np.isfinite(logs).all()
    assert logs[0] == pytest.approx(400 * np.log(0.05)) and logs[1] == pytest.approx(logs[0])      # beide Male bestimmt der kleinste Grad 400
    assert M.isolation(d, np.array([0]), np.array([1]), np.array([0]), 0.05)[0] == 0.0     # ohne Logarithmus läuft der Wert unter
    with pytest.raises(ValueError):
        M.isolation_log(d, np.array([0]), np.array([1]), np.array([0]), 1.0)


def test_gradterm_und_verstaerkt_von_hand(hand):
    d = N.grade(hand).astype(float)
    assert M.gradterm(d, np.array([0]), np.array([4]))[0] == pytest.approx(1.0)
    V = M.verstaerkt_matrix(W.widerstand(hand), N.adjazenz(hand))
    assert [V[0, 1], V[2, 3], V[0, 4]] == pytest.approx([1 / 6, 5 / 9, 4 / 3])
    assert (W.widerstand(hand)[0, 1] - 1.0) == pytest.approx(-1 / 3)           # ohne den Nachbarterm negativ
    assert np.allclose(np.diag(V), 0)


def test_abstaende_und_wegezahlen_von_hand():
    kreis = N.netz("4-Kreis", 4, [(0, 1), (1, 2), (2, 3), (0, 3)])
    A = N.adjazenz(kreis)
    D = M.abstaende(A)
    assert D[0, 2] == 2 and D[0, 1] == 1 and D[0, 0] == 0
    Z = M.wegezahlen(A, D)
    assert Z[0, 2] == 2 and Z[0, 1] == 1
    getrennt = N.netz("zwei", 3, [(0, 1)])
    assert M.abstaende(N.adjazenz(getrennt))[0, 2] == -1


def test_minschnitte_von_hand(hand, hand2, besen):
    assert M.minschnitte(hand, np.array([[0, 1], [0, 4]])).tolist() == [2, 1]
    assert M.minschnitte(hand2, np.array([[0, 4]])).tolist() == [2]
    assert M.minschnitte(besen, np.array([[0, 4]])).tolist() == [1]


def test_distanz_wege_schluessel(hand):
    A = N.adjazenz(hand)
    D = M.abstaende(A)
    zweit = M.distanz_wege_zweitschluessel(A, D, M.wegezahlen(A, D))
    assert zweit[0, 1] == (2 + 2) / 2 - 1 and zweit[0, 3] == -1          # (0,1): ein gemeinsamer Nachbar; (0,3): ein kürzester Weg
    rang = M.lexikografischer_rang(np.array([2, 1, 1]), np.array([0.0, 3.0, -1.0]))
    assert rang.tolist() == [2.0, 1.0, 0.0]


def test_adamic_adar_und_ppr(hand):
    A = N.adjazenz(hand)
    assert M.adamic_adar_matrix(A)[0, 1] == pytest.approx(1 / np.log(3))        # gemeinsamer Nachbar 2 mit Grad 3
    P = M.ppr_matrix(A, 0.15)
    assert P.sum(axis=1) == pytest.approx(np.ones(6))
    G = M.ppr_grad_matrix(A, 0.15)
    assert np.allclose(G, G.T)


def test_kosinus_diagonale_eins(hand):
    K = M.kosinus_matrix(W.pseudoinverse(hand))
    assert np.allclose(np.diag(K), 1.0) and (np.abs(K) <= 1 + 1e-12).all()


def test_ordnungszaehlung_handnetz_ein_und_zwei_tueren(hand, hand2):
    soll = {1: {M.WIDERSTAND: (78, 0, 0), M.DISTANZ: (72, 0, 6), M.MINCUT: (54, 0, 24), M.MINCUT_DIST: (78, 0, 0), M.GRADTERM: (40, 14, 24),
                M.ISOLATION: (64, 14, 0)},
            2: {M.WIDERSTAND: (90, 0, 0), M.DISTANZ: (62, 0, 28), M.MINCUT: (26, 0, 64), M.MINCUT_DIST: (74, 0, 16), M.GRADTERM: (46, 16, 28),
                M.ISOLATION: (70, 16, 4)}}
    for tueren, g in ((1, hand), (2, hand2)):
        paare = AF.alle_paare(6)
        wahr = AF.exakt(g, paare, 0.15)
        nm = X.netzmasse(g, 0, 0, anzahl=15, extra=False)
        A = N.adjazenz(g)
        werte = dict(nm.werte)
        werte[M.ISOLATION] = M.isolation(A.sum(axis=1), paare[:, 0], paare[:, 1], A[paare[:, 0], paare[:, 1]], 0.15)
        for mass, erwartet in soll[tueren].items():
            assert X.ordnungszaehlung(werte[mass], wahr) == erwartet, (tueren, mass)
