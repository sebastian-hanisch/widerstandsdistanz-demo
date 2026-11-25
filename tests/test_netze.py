"""Netzbau: Handnetze, Hallen, Hallenverbund und die Netze mit Zufall (Struktur, Zusammenhang, Reproduzierbarkeit)."""

import numpy as np
import pytest

import wdn_netze as N
import wdn_szenario as S


def test_handnetz_und_zweite_tuer(hand, hand2):
    assert (hand.n, len(hand.kanten), N.grade(hand).tolist()) == (6, 7, [2, 2, 3, 3, 2, 2])
    assert len(hand2.kanten) == 8 and (0, 5) in hand2.kanten


def test_besen_leitung_drei_wege(besen):
    assert besen.n == 5 and len(besen.kanten) == 4 and N.grade(besen).tolist() == [1, 1, 3, 2, 1]
    assert N.leitung().kanten == ((0, 1),)
    g = N.drei_wege()
    assert (g.n, len(g.kanten), N.grade(g)[0], N.grade(g)[1]) == (11, 12, 3, 3)


def test_tuerzeilen_sind_eine_familie_und_eine_tuer_liegt_in_der_mitte():
    for a in range(2, 12):
        assert N.tuerzeilen(a, 1) == [a // 2]
        assert N.tuerzeilen(a, a) == list(range(a))
        for k in range(1, a + 1):
            zeilen = N.tuerzeilen(a, k)
            assert zeilen == [int((i + 0.5) * a / k) for i in range(k)] and len(set(zeilen)) == k
    assert N.tuerzeilen(8, 4) == [1, 3, 5, 7] and N.tuerzeilen(8, 2) == [2, 6]


@pytest.mark.parametrize("a,k", [(6, 1), (8, 4), (10, 10)])
def test_zwei_hallen_zaehlen(a, k):
    g = N.k_tueren(a, k)
    assert g.n == 2 * a * a and len(g.kanten) == 4 * a * (a - 1) + k and N.ist_zusammenhaengend(g)


@pytest.mark.parametrize("p,q,a", [(2, 2, 6), (3, 3, 4), (3, 3, 5), (3, 3, 3)])
def test_hallenverbund_je_nachbarpaar_eine_tuer(p, q, a):
    g = N.hallenverbund(p, q, a)
    tueren = p * (q - 1) + q * (p - 1)
    assert g.n == p * q * a * a and len(g.kanten) == p * q * 2 * a * (a - 1) + tueren and N.ist_zusammenhaengend(g)
    halle = lambda x: x // (a * a)
    quer = [(halle(u), halle(v)) for u, v in g.kanten if halle(u) != halle(v)]
    assert len(quer) == tueren and len(set(quer)) == tueren


@pytest.mark.parametrize("familie", S.KONTRAST + S.DICHT)
def test_zufallsnetze_reproduzierbar_zusammenhaengend_und_im_grad(familie):
    g = S.baue(familie, 150, 0, 0, "", 7000)
    h = S.baue(familie, 150, 0, 0, "", 7000)
    i = S.baue(familie, 150, 0, 0, "", 7001)
    assert g.kanten == h.kanten and g.kanten != i.kanten
    assert N.ist_zusammenhaengend(g) and 100 <= g.n <= 150
    soll = {S.STRASSE: 2.8, S.PUNKT2D: 6, S.ZUFALL4: 4, S.KNOTEN: 4, S.HAELFTEN: 5, S.ER20: 20, S.KNOTEN10: 18.7, S.PUNKT5D: 20, S.DHAELFTEN: 20,
            S.LOECHER: 2.87}[familie]
    assert abs(2 * len(g.kanten) / g.n - soll) < 1.2


def test_strassennetz_ist_eben_ausgeduennt_und_hat_genau_die_kantenzahl():
    g = S.baue(S.STRASSE, 150, 0, 0, "", 7003)
    assert g.n == 150 and len(g.kanten) == 210


def test_haelften_haben_genau_die_querverbindungen():
    for familie, quer in ((S.HAELFTEN, 2), (S.DHAELFTEN, 3)):
        g = S.baue(familie, 150, 0, 0, "", 7000)
        seite = N.haelfte_von(g)
        assert sum(seite[u] != seite[v] for u, v in g.kanten) == quer


def test_groesste_komponente_und_fehler_bei_ungueltigen_kanten():
    g = N.netz("zwei Teile", 7, [(0, 1), (1, 2), (3, 4), (4, 5), (5, 6)])
    k = N.groesste_komponente(g)
    assert k.n == 4 and k.kanten == ((0, 1), (1, 2), (2, 3)) and k.knoten == ("3", "4", "5", "6")
    for kanten in ([(0, 0)], [(0, 1), (1, 0)], [(0, 9)]):
        with pytest.raises(ValueError):
            N.netz("kaputt", 3, kanten)


def test_gruppennetz_hat_gleich_grosse_gruppen_und_den_anteil_innen():
    g, gruppe = N.gruppennetz(500, 5, 20, 0.6, 4)
    assert np.bincount(gruppe).tolist() == [100] * 5
    innen = np.mean([gruppe[u] == gruppe[v] for u, v in g.kanten])
    assert abs(innen - 0.6) < 0.03 and abs(2 * len(g.kanten) / g.n - 20) < 1


def test_punktnetz_nimmt_die_kuerzesten_paare():
    g, D = N.punktnetz_mit_abstaenden(60, 6, 2, 11)
    in_netz = [D[u, v] for u, v in g.kanten]
    draussen = [D[u, v] for u, v in N.fehlende_kanten(g)]
    assert len(g.kanten) == 180 and max(in_netz) <= min(draussen)


def test_ausbaunetze_sind_klein_und_zusammenhaengend():
    for netz in S.X_NETZE:
        g = S.baue_ausbau(netz, 7000)
        assert g.n <= 81 and N.ist_zusammenhaengend(g)
