"""Netzausbau an den Handrechnungen (Handnetz: KI 21; Besen: KI 18) und die Regeln."""

import numpy as np
import pytest

import wdn_experimente as X
import wdn_netze as N
import wdn_szenario as S
import wdn_widerstand as W


def _nach_kante(erg):
    return {(int(u), int(v)): i for i, (u, v) in enumerate(zip(erg.U, erg.V))}


def test_handnetz_senkungen(hand):
    erg = X.ausbau(hand)
    assert erg.ki == pytest.approx(21.0)
    idx = _nach_kante(erg)
    quer = [(0, 4), (0, 5), (1, 4), (1, 5)]
    for k in quer:
        assert erg.senkung[idx[k]] == pytest.approx(8.3) and erg.R[idx[k]] == pytest.approx(7 / 3)
    uebrige = [k for k in idx if k not in quer]
    assert len(uebrige) == 4 and all(erg.senkung[idx[k]] == pytest.approx(6.5) and erg.R[idx[k]] == pytest.approx(5 / 3) for k in uebrige)
    for regel in (X.MAX_R, X.MAX_GRADTERM, X.MAX_ZAEHLER):
        assert sorted((int(erg.U[i]), int(erg.V[i])) for i in erg.wahl[regel]) == quer
    assert erg.anteil[X.MAX_R] == pytest.approx(1.0) and erg.anteil[X.ZUFAELLIG] == pytest.approx((4 * 8.3 + 4 * 6.5) / 8 / 8.3)


def test_besen(besen):
    erg = X.ausbau(besen)
    assert erg.ki == pytest.approx(18.0)
    idx = _nach_kante(erg)
    blaetter = [(0, 1), (0, 4), (1, 4)]
    assert [erg.gradterm[idx[k]] for k in blaetter] == [2.0, 2.0, 2.0]
    assert [erg.R[idx[k]] for k in blaetter] == pytest.approx([2.0, 3.0, 3.0])
    assert erg.senkung[idx[(0, 4)]] == pytest.approx(6.5) and erg.senkung[idx[(0, 1)]] == pytest.approx(10 / 3)
    assert sorted((int(erg.U[i]), int(erg.V[i])) for i in erg.wahl[X.MAX_R]) == [(0, 4), (1, 4)]
    assert erg.anteil[X.MAX_R] == pytest.approx(1.0)
    assert erg.anteil[X.MAX_GRADTERM] == pytest.approx(98 / 117)


def test_zaehler_und_formel_gegen_neuberechnung(hand):
    erg = X.ausbau(hand)
    for i in range(len(erg.U)):
        h = N.mit_kante(hand, int(erg.U[i]), int(erg.V[i]))
        neu = W.kirchhoff_index(W.pseudoinverse(h))
        assert erg.ki - neu == pytest.approx(erg.senkung[i], abs=1e-9)


def test_fiedler_bei_doppeltem_eigenwert_nicht_bestimmbar():
    erg = X.ausbau(S.baue_ausbau(S.X_VERBUND, 7000))
    assert erg.wahl[X.FIEDLER] is None and erg.anteil[X.FIEDLER] is None
    erg = X.ausbau(N.k_tueren(6, 1))
    assert erg.anteil[X.FIEDLER] is not None


def test_vollstaendiges_netz_hat_keine_neue_kante():
    with pytest.raises(ValueError):
        X.ausbau(N.vollstaendig(4))


def test_gleichrangige_kanten_werden_gemittelt():
    erg = X.ausbau(N.netz("Stern", 4, [(0, 1), (0, 2), (0, 3)]))
    assert len(erg.wahl[X.MAX_R]) == 3 and erg.anteil[X.MAX_R] == pytest.approx(1.0)
    assert np.allclose(erg.senkung, erg.senkung[0])


def test_senkung_ist_positiv():
    for netz in S.X_NETZE:
        erg = X.ausbau(S.baue_ausbau(netz, 7003))
        assert (erg.senkung > 0).all()
