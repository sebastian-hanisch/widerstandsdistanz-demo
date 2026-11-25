"""Karte: Knotennummern in customdata, Beschriftungen als Annotationen, neue Leitungen als Bögen mit richtigen Enden, Achsen gesperrt."""

import pytest

import wdn_karte as K
import wdn_netze as N


def test_karte_knoten_beschriftung_und_achsen(hand):
    fig = K.karte(hand)
    punkte = [t for t in fig.data if t.mode == "markers" and t.customdata is not None]
    assert len(punkte) == 1 and list(punkte[0].customdata) == list(range(6))
    assert sorted(a.text for a in fig.layout.annotations) == [str(i) for i in range(6)]
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange and fig.layout.dragmode is False
    assert not K.karte(N.k_tueren(6, 1)).layout.annotations


def test_neue_leitungen_sind_boegen_von_ende_zu_ende():
    g = N.k_tueren(6, 1)
    fig = K.karte(g, neue_kanten=[((0, 5), "#111111", "dot", "a"), ((0, 5), "#222222", "dash", "b")])
    linien = [t for t in fig.data if t.mode == "lines" and t.showlegend]
    assert [t.name for t in linien] == ["a", "b"]
    for t in linien:
        assert (t.x[0], t.y[0]) == pytest.approx(g.pos[0]) and (t.x[-1], t.y[-1]) == pytest.approx(g.pos[5])
    mitte = len(linien[0].y) // 2
    # beide Bögen weichen von der geraden Reihe ab, und zwar nach verschiedenen Seiten
    assert (linien[0].y[mitte] - g.pos[0][1]) * (linien[1].y[mitte] - g.pos[0][1]) < 0
