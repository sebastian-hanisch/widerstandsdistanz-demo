"""Orakel für die Gegner und die Ausfallziehung: min cut gegen Aufzählung aller Knotenmengen und networkx, Distanz und Wegezahlen gegen networkx, PPR gegen
Potenziteration, Adamic-Adar gegen networkx, Isolationsformel gegen Aufzählung, die gebündelte Komponentensuche gegen eine eigene Vereinigungssuche mit
denselben Ausfallmustern, die Rangkorrelation gegen scipy.stats.spearmanr."""

import itertools
from fractions import Fraction

import numpy as np
import pytest

import wdn_ausfall as AF
import wdn_masse as M
import wdn_netze as N
import wdn_statistik as ST
from conftest import min_cut_aufzaehlung, p_isoliert_brueche, wurzeln, zufallsnetz_klein
from wdn_zufall import BlockZufall

nx = pytest.importorskip("networkx")


def _nx(g):
    G = nx.Graph()
    G.add_nodes_from(range(g.n))
    G.add_edges_from(g.kanten)
    return G


@pytest.mark.parametrize("seed", range(20))
def test_mincut_distanz_wege(seed):
    n = 5 + seed % 5
    g = zufallsnetz_klein(n, n + seed % 7, 200 + seed)
    G = _nx(g)
    paare = AF.alle_paare(n)
    mc = M.minschnitte(g, paare)
    A = N.adjazenz(g)
    D = M.abstaende(A)
    Z = M.wegezahlen(A, D)
    for (s, t), c in zip(paare, mc):
        assert c == min_cut_aufzaehlung(n, g.kanten, int(s), int(t))
        assert c == len(list(nx.edge_disjoint_paths(G, int(s), int(t))))
        assert D[s, t] == nx.shortest_path_length(G, int(s), int(t))
        assert Z[s, t] == len(list(nx.all_shortest_paths(G, int(s), int(t))))


@pytest.mark.parametrize("seed", range(10))
def test_ppr_gegen_potenziteration_und_adamic_gegen_networkx(seed):
    g = zufallsnetz_klein(8, 12, 300 + seed)
    A = N.adjazenz(g)
    P = A / A.sum(1, keepdims=True)
    x = np.eye(8)
    for _ in range(400):
        x = 0.15 * np.eye(8) + 0.85 * x @ P
    assert M.ppr_matrix(A, 0.15) == pytest.approx(x, abs=1e-10)
    d = A.sum(1)
    G = M.ppr_grad_matrix(A, 0.15)
    assert G == pytest.approx(x / d[None, :] + (x / d[None, :]).T, abs=1e-10)
    nicht = N.fehlende_kanten(g)
    aa = M.adamic_adar_matrix(A)
    for s, t, wert in nx.adamic_adar_index(_nx(g), nicht):
        assert aa[s, t] == pytest.approx(wert, abs=1e-12)


@pytest.mark.parametrize("seed", range(8))
def test_isolationsformel_gegen_aufzaehlung(seed):
    n = 5 + seed % 3
    g = zufallsnetz_klein(n, n + 2, 400 + seed)
    paare = [tuple(q) for q in AF.alle_paare(n)]
    p = Fraction(3, 20)
    soll = p_isoliert_brueche(n, g.kanten, p, paare)
    d = N.grade(g).astype(float)
    A = N.adjazenz(g)
    S = np.array([q[0] for q in paare])
    T = np.array([q[1] for q in paare])
    assert M.isolation(d, S, T, A[S, T], 0.15) == pytest.approx([float(x) for x in soll], abs=1e-12)


@pytest.mark.parametrize("seed", range(6))
def test_gebuendelte_komponentensuche_gegen_vereinigungssuche(seed):
    g = zufallsnetz_klein(15, 22, 500 + seed)
    paare = AF.alle_paare(15)
    p, proben = 0.25, 130
    anteil, _ = AF.stichprobe(g, paare, p, proben, 123 + seed)
    rng = BlockZufall(123 + seed)
    m = len(g.kanten)
    zaehler = np.zeros(len(paare))
    for _ in range(proben):
        u = rng.random(m)
        da = [g.kanten[i] for i in range(m) if u[i] >= p]
        k = wurzeln(15, da)
        zaehler += [k[s] != k[t] for s, t in paare]
    assert anteil == pytest.approx(zaehler / proben, abs=1e-12)


@pytest.mark.parametrize("seed", range(10))
def test_exakt_gegen_stichprobe_im_band(seed):
    g = zufallsnetz_klein(7, 10, 600 + seed)
    paare = AF.alle_paare(7)
    ex = AF.exakt(g, paare, 0.3)
    anteil, _ = AF.stichprobe(g, paare, 0.3, 4000, seed)
    assert (np.abs(anteil - ex) <= 5 * np.sqrt(ex * (1 - ex) / 4000) + 1e-9).all()


def test_rangkorrelation_gegen_scipy():
    from scipy.stats import spearmanr

    rng = np.random.default_rng(5)
    for _ in range(60):
        x = rng.integers(0, 8, 40).astype(float)
        y = rng.integers(0, 8, 40).astype(float)
        assert ST.rangkorrelation(x, y) == pytest.approx(spearmanr(x, y).statistic, abs=1e-12)


def test_auc_gegen_paarzaehlung():
    rng = np.random.default_rng(6)
    for _ in range(40):
        werte = rng.integers(0, 5, 30).astype(float)
        positiv = rng.random(30) < 0.4
        if positiv.all() or not positiv.any():
            continue
        paare = list(itertools.product(werte[positiv], werte[~positiv]))
        soll = sum(1.0 if a < b else 0.5 if a == b else 0.0 for a, b in paare) / len(paare)
        assert ST.auc(werte, positiv) == pytest.approx(soll)
