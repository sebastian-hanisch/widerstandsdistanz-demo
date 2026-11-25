"""Kantenausfall: exakte Werte am Handnetz und am Beispiel „Leitung gegen drei Wege“; die Stichprobe gegen die exakten Werte."""

from fractions import Fraction as Fr

import numpy as np
import pytest

import wdn_ausfall as AF
import wdn_netze as N
from conftest import p_getrennt_brueche


def test_handnetz_exakt(hand, hand2):
    paare = AF.alle_paare(6)
    y = AF.exakt(hand, paare, 0.15)
    i01, i04 = 0, 3
    assert tuple(paare[i04]) == (0, 4)
    p = Fr(3, 20)
    assert y[i01] == pytest.approx(float(2 * p**2 - p**3))                  # im Dreieck: beide Wege kaputt
    assert round(float(y[i04]), 4) == 0.2193
    assert round(float(AF.exakt(hand2, paare, 0.15)[i04]), 4) == 0.0550
    brueche = p_getrennt_brueche(6, hand.kanten, p, [tuple(q) for q in paare])
    assert y == pytest.approx([float(b) for b in brueche], abs=1e-12)


@pytest.mark.parametrize("p,soll", [(0.15, 0.1092), (0.3, 0.4388)])
def test_leitung_gegen_drei_wege(p, soll):
    g = N.drei_wege()
    ex = AF.exakt(g, np.array([[0, 1]]), p)[0]
    assert ex == pytest.approx(AF.p_drei_wege(p), abs=1e-12) and round(ex, 4) == soll
    assert AF.exakt(N.leitung(), np.array([[0, 1]]), p)[0] == pytest.approx(AF.p_leitung(p))


def test_stichprobe_im_band_um_den_exakten_wert(hand):
    paare = AF.alle_paare(6)
    exakt = AF.exakt(hand, paare, 0.15)
    for seed in (1, 2, 3):
        anteil, haelften = AF.stichprobe(hand, paare, 0.15, 20000, seed)
        sd = np.sqrt(exakt * (1 - exakt) / 20000)
        assert (np.abs(anteil - exakt) <= 4.5 * sd + 1e-12).all()
        assert anteil == pytest.approx(haelften.mean(axis=0))


def test_stichprobe_haelften_zaehlen_jede_probe_einmal(hand):
    paare = AF.alle_paare(6)
    for proben in (50, 199, 200, 1601):
        anteil, haelften = AF.stichprobe(hand, paare, 0.3, proben, 5)
        gerade, ungerade = (proben + 1) // 2, proben // 2
        assert anteil * proben == pytest.approx(haelften[0] * gerade + haelften[1] * ungerade)


def test_stichprobe_blockgroesse_aendert_nichts(hand, monkeypatch):
    paare = AF.alle_paare(6)
    erst = AF.stichprobe(hand, paare, 0.3, 450, 9)[0]
    monkeypatch.setattr(AF, "BLOCK", 7)
    assert AF.stichprobe(hand, paare, 0.3, 450, 9)[0] == pytest.approx(erst)


def test_p_null_und_eins(hand):
    paare = AF.alle_paare(6)
    assert AF.stichprobe(hand, paare, 0.0, 40, 1)[0].max() == 0.0
    assert AF.stichprobe(hand, paare, 1.0, 40, 1)[0].min() == 1.0
    assert AF.exakt(hand, paare, 0.0).max() == 0.0 and AF.exakt(hand, paare, 1.0).min() == pytest.approx(1.0)


def test_zufallspaare_verschieden_und_vollstaendig_auf_kleinen_netzen():
    paare = AF.zufallspaare(100, 300, 4)
    assert len({tuple(q) for q in paare}) == 300 and (paare[:, 0] < paare[:, 1]).all()
    assert len(AF.zufallspaare(6, 300, 4)) == 15
    with pytest.raises(ValueError):
        AF.exakt(N.k_tueren(4, 1), np.array([[0, 1]]), 0.2)
    with pytest.raises(ValueError):
        AF.stichprobe(N.handnetz(1), np.array([[0, 1]]), 0.2, 1, 1)
