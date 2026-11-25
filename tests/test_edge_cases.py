"""Randfälle: unzusammenhängende Netze, zwei Knoten, Nachbarpaare, p = 0 und 1, konstante Zielgröße („nicht messbar“, nie Korrelation 0), vollständiges Netz,
Worst Case an den Reglerrändern."""

import numpy as np
import pytest

import wdn_ausfall as AF
import wdn_experimente as X
import wdn_masse as M
import wdn_netze as N
import wdn_statistik as ST
import wdn_szenario as S
import wdn_widerstand as W


def test_unzusammenhaengend_gibt_fehler():
    g = N.netz("zwei Teile", 4, [(0, 1), (2, 3)])
    with pytest.raises(ValueError):
        W.widerstand(g)
    with pytest.raises(ValueError):
        X.ausbau(g)


def test_zwei_knoten():
    g = N.leitung()
    assert W.widerstand(g)[0, 1] == pytest.approx(1.0)
    assert M.minschnitte(g, np.array([[0, 1]])).tolist() == [1]
    with pytest.raises(ValueError):
        X.ausbau(g)


def test_konstante_zielgroesse_ist_nicht_messbar():
    g = N.k_tueren(6, 1)
    nm = X.netzmasse(g, 7000, S.FAMNR[S.HALLEN])
    z = X.ausfallzelle(g, nm, 1e-12, 0, 7000, S.FAMNR[S.HALLEN])
    assert not z.messbar and all(v is None for v in z.rho1.values()) and z.haelften is None


def test_nachbarpaare_in_der_isolationsnaeherung_ohne_doppelte_kante():
    d = np.array([1.0, 1.0])
    # ein Netz aus einer Kante: ein Ende ist genau dann ohne Kante, wenn sie ausfällt
    assert M.isolation(d, np.array([0]), np.array([1]), np.array([1]), 0.3)[0] == pytest.approx(0.3)


def test_entartung_ohne_nichtnachbarn():
    with pytest.raises(ValueError):
        X.entartung(N.vollstaendig(5))


@pytest.mark.parametrize("familie,a,tueren,verbund,n,p", [
    (S.HALLEN, 6, 1, "", 0, 0.05), (S.HALLEN, 10, 0, "", 0, 0.3), (S.VERBUND, 0, 0, "3x3x5", 0, 0.05), (S.STRASSE, 0, 0, "", 80, 0.05),
    (S.LOECHER, 0, 0, "", 80, 0.3), (S.ER20, 0, 0, "", 80, 0.15), (S.DHAELFTEN, 0, 0, "", 200, 0.85), (S.PUNKT5D, 0, 0, "", 200, 0.7),
    (S.HAELFTEN, 0, 0, "", 200, 0.15), (S.KNOTEN10, 0, 0, "", 80, 0.85),
])
def test_experiment_1_an_den_raendern(familie, a, tueren, verbund, n, p):
    g = S.baue(familie, n, a, tueren, verbund, 999_999)
    nm = X.netzmasse(g, 999_999, S.FAMNR[familie])
    ps = S.P_DICHT if S.ist_dicht(familie) else S.P_DUENN
    z = X.ausfallzelle(g, nm, p, ps.index(p), 999_999, S.FAMNR[familie])
    assert (0 <= z.y1).all() and (z.y1 <= 1).all()
    for v in list(z.rho1.values()) + list(z.rho2.values()):
        assert v is None or -1 - 1e-9 <= v <= 1 + 1e-9


def test_worst_case_groessen():
    g = S.baue_entartung(S.E_PUNKTWURZEL, 1000, 0)
    e = X.entartung(g)
    assert 0 < e.rho <= 1
    for netz in S.X_NETZE:
        X.ausbau(S.baue_ausbau(netz, 999_999))


def test_halbes_netz_komponente_bei_duennem_zufallsnetz():
    g = N.zufallsnetz(200, 1.2, 3)
    assert N.ist_zusammenhaengend(g) and g.n < 200


def test_stichprobe_mit_netz_ohne_ausfall_und_alle_ausfaellen(besen):
    paare = AF.alle_paare(besen.n)
    assert AF.stichprobe(besen, paare, 0.0, 10, 1)[0].tolist() == [0.0] * 10
    assert AF.stichprobe(besen, paare, 1.0, 10, 1)[0].tolist() == [1.0] * 10


def test_rangkorrelation_mit_einem_paar():
    assert ST.rangkorrelation([1.0], [2.0]) is None
