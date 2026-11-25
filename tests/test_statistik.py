"""Rangkorrelation, „nicht messbar“, Klar-Kriterium, P@10 und AUC an Handwerten."""

import numpy as np
import pytest

import wdn_statistik as ST


def test_rangkorrelation_von_hand():
    assert ST.rangkorrelation([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert ST.rangkorrelation([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    # Ränge x: 1,2,3,4; y: 1,3,2,4 -> 1 - 6*2/(4*15) = 0,8
    assert ST.rangkorrelation([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(0.8)


def test_rangkorrelation_konstant_ist_none_nie_null():
    assert ST.rangkorrelation([1, 1, 1], [1, 2, 3]) is None
    assert ST.rangkorrelation([1, 2, 3], [0.5, 0.5, 0.5]) is None


def test_rundung_macht_rechenrauschen_zu_gleichstand():
    assert ST.rangkorrelation([0.1 + 0.2, 0.3, 1.0], [1, 2, 3]) == pytest.approx(ST.rangkorrelation([0.3, 0.3, 1.0], [1, 2, 3]))


def test_messbar_schwelle_95_prozent():
    assert ST.messbar([0] * 94 + list(range(1, 7)))
    assert not ST.messbar([0] * 95 + [1, 2, 3, 4, 5])           # genau 95 %: nicht messbar


def test_klar_braucht_beide_stichproben():
    assert ST.klar(0.80, 0.81, 0.70, 0.70) == ST.R_VORN
    assert ST.klar(0.75, 0.75, 0.70, 0.70) == ST.R_VORN                  # genau 0,05 zählt
    assert ST.klar(0.80, 0.74, 0.70, 0.70) == ST.UNKLAR                  # in einer Stichprobe zu knapp
    assert ST.klar(0.60, 0.60, 0.70, 0.65) == ST.GEGNER_VORN
    assert ST.klar(0.80, 0.60, 0.70, 0.70) == ST.UNKLAR                  # Vorzeichen verschieden
    assert ST.klar(None, 0.8, 0.5, 0.5) == ST.UNKLAR


def test_anteil_unter_besten_mit_gleichstand():
    werte = np.array([0.0] * 5 + [1.0] * 10 + [2.0] * 5)
    wahr = np.zeros(20, bool)
    wahr[:5] = True
    wahr[5:10] = True                     # fünf der zehn Gleichrangigen sind richtig
    assert ST.anteil_unter_besten(werte, wahr, 10) == pytest.approx((5 + 5 * 0.5) / 10)


def test_auc_von_hand():
    werte = np.array([1.0, 2.0, 3.0, 4.0])
    assert ST.auc(werte, np.array([True, True, False, False])) == pytest.approx(1.0)
    assert ST.auc(werte, np.array([False, False, True, True])) == pytest.approx(0.0)
    assert ST.auc(np.array([1.0, 1.0]), np.array([True, False])) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        ST.auc(werte, np.ones(4, bool))
