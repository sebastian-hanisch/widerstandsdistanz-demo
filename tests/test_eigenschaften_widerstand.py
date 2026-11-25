"""Eigenschaften des effektiven Widerstands und der Maße auf Zufallsnetzen (je 30 Netze): Umnummerieren, Rayleigh, Dreiecksungleichung, Foster, Bäume,
die zwei unteren Schranken, R ≤ Distanz und R ≥ 1/min cut."""

import random

import numpy as np
import pytest

import wdn_ausfall as AF
import wdn_experimente as X
import wdn_masse as M
import wdn_netze as N
import wdn_widerstand as W
from conftest import zufallsnetz_klein

NETZE = [zufallsnetz_klein(6 + s % 9, 6 + s % 9 + s % 11, 700 + s) for s in range(30)]


def test_umnummerieren_aendert_nur_die_namen():
    for i, g in enumerate(NETZE):
        perm = list(range(g.n))
        random.Random(i).shuffle(perm)
        h = N.netz("perm", g.n, [(perm[u], perm[v]) for u, v in g.kanten])
        assert W.widerstand(h)[np.ix_(perm, perm)] == pytest.approx(W.widerstand(g), abs=1e-9)


def test_neue_kante_vergroessert_keinen_widerstand():
    for g in NETZE:
        fehlt = N.fehlende_kanten(g)
        if not fehlt:
            continue
        u, v = fehlt[len(fehlt) // 2]
        assert (W.widerstand(N.mit_kante(g, u, v)) <= W.widerstand(g) + 1e-9).all()


def test_dreiecksungleichung_und_foster():
    for g in NETZE:
        R = W.widerstand(g)
        assert (R[:, :, None] <= R[:, None, :] + R.T[None, :, :] + 1e-9).all()
        assert sum(R[u, v] for u, v in g.kanten) == pytest.approx(g.n - 1)


def test_baum_r_gleich_distanz():
    for s in range(30):
        g = zufallsnetz_klein(8, 7, 900 + s)
        assert W.widerstand(g) == pytest.approx(M.abstaende(N.adjazenz(g)).astype(float), abs=1e-9)


def test_schranken_und_mincut():
    for g in NETZE:
        R = W.widerstand(g)
        A = N.adjazenz(g)
        d = A.sum(1)
        gt = 1 / d[:, None] + 1 / d[None, :]
        anders = ~np.eye(g.n, dtype=bool)
        assert (R[anders] >= gt[anders] / 2 - 1e-9).all()
        frei = (A == 0) & anders
        assert (R[frei] >= gt[frei] - 1e-9).all()
        D = M.abstaende(A)
        assert (R <= D + 1e-9).all()
        paare = AF.alle_paare(g.n)
        mc = M.minschnitte(g, paare)
        assert all(R[s, t] >= 1 / c - 1e-9 for (s, t), c in zip(paare, mc))


def test_fuer_nachbarn_gilt_die_scharfe_schranke_nicht_allgemein(hand):
    R = W.widerstand(hand)
    d = N.grade(hand)
    assert R[0, 1] < 1 / d[0] + 1 / d[1]


def test_ausbausenkung_positiv_und_nie_groesser_als_der_index():
    for g in NETZE:
        if N.fehlende_kanten(g):
            erg = X.ausbau(g)
            assert (erg.senkung > 0).all() and (erg.senkung < erg.ki).all()


def test_ausfallstichprobe_monoton_in_p():
    g = NETZE[7]
    paare = AF.alle_paare(g.n)
    werte = [AF.exakt(g, paare, p) if len(g.kanten) <= AF.EXAKT_MAX_KANTEN else AF.stichprobe(g, paare, p, 3000, 4)[0] for p in (0.05, 0.2, 0.5)]
    assert (werte[0] <= werte[1] + 0.03).all() and (werte[1] <= werte[2] + 0.03).all()
