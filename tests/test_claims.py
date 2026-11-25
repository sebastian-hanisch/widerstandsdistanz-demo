"""Zahlen aus README und App-Texten: entweder direkt gerechnet (Handnetz, Leitung gegen drei Wege, Ausbau von Hand, Rangkorrelation innen und quer der dichten
Hälften; weitere Handbeispiele in test_masse.py und test_ausbau.py) oder aus der gespeicherten Tabelle `daten/vorgerechnet.json` gezählt. Die Datei wird zum
Teil neu gerechnet: Hallen-, Entartungs- und Ausbautabellen vollständig, jedes zehnte dichte Ausbaunetz, je Familie eine Stichprobe der übrigen Ausfallzellen
und ein Reparaturnetz. Neu-Rechnen als Band, nicht bitgleich (andere Plattformen runden in der letzten Stelle anders)."""

import re
from fractions import Fraction as Fr
from pathlib import Path

import numpy as np
import pytest

import wdn_ausfall as AF
import wdn_constants as C
import wdn_daten as D
import wdn_evaluation as E
import wdn_experimente as X
import wdn_masse as M
import wdn_netze as N
import wdn_statistik as ST
import wdn_szenario as S
import wdn_tabellen as T
import wdn_widerstand as W
from conftest import p_getrennt_brueche, widerstand_geerdet

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")
DATEN = D.laden()
DUENN = D.zellen(DATEN, block=("hallen", "kontrast"))
DICHT = D.zellen(DATEN, block="dicht")
z = E.zahl


def steht(*teile, text=README):
    glatt = " ".join(text.split())
    for t in teile:
        assert " ".join(t.split()) in glatt, t


# --- Handbeispiele ----------------------------------------------------------------------------------------------------------------------

def test_aufhaenger_am_handnetz(hand):
    assert widerstand_geerdet(6, hand.kanten, 0, 1) == Fr(2, 3) and widerstand_geerdet(6, hand.kanten, 0, 4) == Fr(7, 3)
    p01, p04 = p_getrennt_brueche(6, hand.kanten, Fr(3, 20), [(0, 1), (0, 4)])
    assert (E.prozent(float(p01)), E.prozent(float(p04))) == ("4,2 %", "21,9 %")
    assert N.grade(hand)[[0, 1, 4]].tolist() == [2, 2, 2]
    steht("(0,1) in 4,2 % der Fälle getrennt, (0,4) in 21,9 % (exakt über alle 2⁷ Ausfallmuster)", "R ist 2/3 gegen 7/3")
    assert Fr(7, 3) / Fr(2, 3) == Fr(7, 2)
    steht("R ist 3,5-mal so groß", text=APP)


def test_handnetz_ordnung_und_zweite_tuer(hand, hand2):
    steht("eine Tür: 78 richtig, 0 falsch; zwei Türen: 90 richtig, 0 falsch", "Distanz 72 / 0 / 6", "min cut 54 / 0 / 24", "Gradterm 40 / 14 / 24",
          "Isolationsnäherung 64 / 14 / 0", "mit zwei Türen sinkt P(0–4) auf 5,5 %", "der min cut bewertet 64 von 90 Vergleichen gleich")
    paare = AF.alle_paare(6)
    for g, soll_r, soll_mc, p04 in ((hand, (78, 0, 0), (54, 0, 24), "21,9 %"), (hand2, (90, 0, 0), (26, 0, 64), "5,5 %")):
        wahr = AF.exakt(g, paare, 0.15)
        nm = X.netzmasse(g, 0, 0, anzahl=15, extra=False)
        assert X.ordnungszaehlung(nm.werte[M.WIDERSTAND], wahr) == soll_r
        assert X.ordnungszaehlung(nm.werte[M.MINCUT], wahr) == soll_mc and E.prozent(wahr[3]) == p04


def test_leitung_gegen_drei_wege():
    for p, soll in ((Fr(3, 20), "10,92 %"), (Fr(3, 10), "43,88 %")):
        exakt = AF.exakt(N.drei_wege(), np.array([[0, 1]]), float(p))[0]
        assert E.prozent(exakt, 2) == soll
    assert widerstand_geerdet(11, N.drei_wege().kanten, 0, 1) == Fr(4, 3)
    steht("Bei p = 0,15 ist die Leitung mit 15,00 % getrennt, die drei Wege mit 10,92 %; bei p = 0,3 sind es 30,00 % gegen 43,88 %")


def test_besen_und_handnetz_ausbau(besen, hand):
    erg = X.ausbau(besen)
    assert erg.ki == pytest.approx(18) and erg.anteil[X.MAX_GRADTERM] == pytest.approx(98 / 117)
    erg = X.ausbau(hand)
    assert erg.ki == pytest.approx(21) and sorted(np.round(erg.senkung, 6).tolist()) == [6.5] * 4 + [8.3] * 4
    steht("vier fehlende Kanten mit R = 7/3 senken um 83/10, vier mit R = 5/3 um 13/2", "98/117", "senkt nur um 10/3")


# --- Ausfalltabelle: neu gerechnet ------------------------------------------------------------------------------------------------------

def _neu(gruppe, inst):
    return T.ausfall_zeilen(gruppe, inst)


def _vergleiche(neu, gruppe, seed, n_, a, variante):
    alt = [r for r in D.zellen(DATEN, gruppe=gruppe) if r["seed"] == seed and r["n"] == n_ and r["a"] == a and r["variante"] == variante]
    assert len(alt) == len(neu)
    for r_neu, r_alt in zip(neu, alt):
        assert r_neu["p"] == r_alt["p"] and r_neu["messbar"] == r_alt["messbar"] and r_neu["m"] == r_alt["m"]
        for schluessel in ("rho1", "rho2"):
            for mass, wert in r_alt[schluessel].items():
                if wert is None:
                    assert r_neu[schluessel][mass] is None
                else:
                    assert r_neu[schluessel][mass] == pytest.approx(wert, abs=3e-3), (gruppe, mass)


@pytest.mark.parametrize("gruppe", T.HALLEN_GRUPPEN)
def test_hallentabelle_neu_gerechnet(gruppe):
    for inst in T.instanzen(gruppe):
        neu = _neu(gruppe, inst)
        _vergleiche(neu, gruppe, inst[5], neu[0]["n"], inst[2], inst[4])


@pytest.mark.parametrize("gruppe", S.KONTRAST + S.DICHT)
def test_stichprobe_der_uebrigen_ausfalltabelle_neu_gerechnet(gruppe):
    alle = T.instanzen(gruppe)
    inst = alle[len(alle) // 2]
    neu = _neu(gruppe, inst)
    _vergleiche(neu, gruppe, inst[5], neu[0]["n"], 0, "")


def test_tabelle_hat_die_genannten_zellen():
    assert len(D.zellen(DATEN, block="hallen")) == 45 and len(D.zellen(DATEN, block="kontrast")) == 180 and len(DUENN) == 225
    assert len(DICHT) == 72 and D.nicht_messbar(DICHT) == (17, 72)
    assert all(r["messbar"] for r in DUENN)
    assert all(len(T.instanzen(g)) == 10 for g in S.KONTRAST) and all(len(T.instanzen(g)) == 6 for g in S.DICHT)
    ns = [r["n"] for r in DUENN]
    assert min(ns) >= 72 and max(ns) == 225


# --- Zahlen der README aus der Tabelle -------------------------------------------------------------------------------------------------

SPALTEN = (M.DISTANZ, M.WIDERSTAND, M.MINCUT, M.MINCUT_DIST, M.GRADTERM, M.ISOLATION, M.STICH200)


def test_hallentabelle_in_der_readme():
    for gruppe in T.HALLEN_GRUPPEN:
        felder = [" / ".join(z(D.mittel(D.zellen(DATEN, gruppe=gruppe, p=p), m)) for p in S.P_DUENN) for m in SPALTEN]
        steht(f"| {C.GRUPPEN_TEXT[gruppe]} | " + " | ".join(felder) + " |")


def test_kontrasttabelle_p015_in_der_readme():
    for gruppe in S.KONTRAST:
        zz = D.zellen(DATEN, gruppe=gruppe, p=0.15)
        steht(f"| {C.GRUPPEN_TEXT[gruppe]} | " + " | ".join(z(D.mittel(zz, m)) for m in SPALTEN) + " |")


ZAEHL_NAMEN = {**C.GRUPPEN_TEXT, S.ER20: "Zufallsnetz Grad 20 (dicht)", S.KNOTEN10: "Netz mit Knotenpunkten, 10 Anschlüsse (dicht)",
               S.PUNKT5D: "Punktnetz 5D (dicht)"}
ZAEHL_GEGNER = (M.DISTANZ, M.GRADTERM, M.ISOLATION, M.MINCUT, M.MINCUT_DIST, M.STICH200)


def test_r_vorn_tabelle_in_der_readme():
    for gruppe in T.HALLEN_GRUPPEN + S.KONTRAST + S.DICHT:
        zz = D.zellen(DATEN, gruppe=gruppe)
        felder = []
        for g in ZAEHL_GEGNER:
            c = D.zaehlung(zz, g)
            felder.append(f"{c['r_vorn']}/{c['messbar']}")
        steht(f"| {ZAEHL_NAMEN[gruppe]} | " + " | ".join(felder) + " |")
    felder = [f"{D.zaehlung(DUENN, g)['r_vorn']}/225" for g in ZAEHL_GEGNER]
    steht("| dünn zusammen | " + " | ".join(felder) + " |")


def test_gesamtzahlen_duenn():
    dist, gt, mc, st = (D.zaehlung(DUENN, g) for g in (M.DISTANZ, M.GRADTERM, M.MINCUT, M.STICH200))
    assert (dist["r_vorn"], dist["klar_r"]) == (225, 224)
    steht("in jeder Zelle besser als die kürzeste Distanz** (klar in 224 von 225)")
    assert (gt["klar_r"], gt["klar_gegner"], mc["klar_r"], mc["klar_gegner"], st["klar_r"], st["klar_gegner"]) == (118, 35, 59, 66, 38, 70)
    steht("gegen den Gradterm R 118-mal klar vorn, der Gradterm 35-mal; gegen den min cut R 59-mal, der min cut 66-mal; gegen die 200er-Stichprobe R 38-mal, "
          "die Stichprobe 70-mal")
    assert (mc["gegner_vorn"], st["gegner_vorn"]) == (129, 135)
    steht("Der min cut lag in 129 der 225 dünnen Zellen vor R, die eigene Stichprobe mit nur 200 Proben in 135.")
    assert D.ueber_wiederholbarkeit(D.zellen(DATEN, block="hallen"), M.MINCUT) == 14
    assert D.ueber_wiederholbarkeit(D.zellen(DATEN, block="kontrast"), M.MINCUT) == 46
    steht("der min cut lag in 14 der 45 Hallenzellen und in 46 der 180 Kontrastzellen darüber")


def test_gegenfall_viele_tueren():
    for gruppe, p_liste in (("hallen4", (0.05, 0.15)), ("hallen_a", S.P_DUENN)):
        for p in p_liste:
            zz = D.zellen(DATEN, gruppe=gruppe, p=p)
            assert D.mittel(zz, M.GRADTERM) > D.mittel(zz, M.WIDERSTAND), (gruppe, p)
    klein = [r for p in (0.05, 0.15) for r in D.zellen(DATEN, gruppe="hallen4", p=p)]
    assert D.zaehlung(klein, M.GRADTERM)["klar_gegner"] == 6 == len(klein)
    assert sorted((r["a"], r["p"]) for r in klein) == [(a, p) for a in (6, 8, 10) for p in (0.05, 0.15)]       # 3 Netze × 2 Ausfallraten, nicht 6 Netze
    c = D.zaehlung(D.zellen(DATEN, gruppe="hallen4", p=0.3), M.GRADTERM)
    assert (c["klar_r"], c["klar_gegner"]) == (1, 1)
    c = D.zaehlung(D.zellen(DATEN, gruppe="hallen_a"), M.GRADTERM)
    assert (c["klar_gegner"], c["r_vorn"], c["klar_r"], c["messbar"]) == (8, 1, 0, 9)
    steht("war der Gradterm bei p = 0,05 und 0,15 in allen 6 Netz-p-Zellen (3 Netze × 2 Ausfallraten) klar vorn", "in 8 von 9 Netz-p-Zellen klar vorn")
    assert sum(D.zaehlung(D.zellen(DATEN, gruppe=g), M.MINCUT_DIST)["gegner_vorn"] for g in ("hallen4", "hallen_a")) == 17
    steht("bei 4 und a Türen in 17 von 18 Zellen vor R")


def test_gitter_mit_loechern_zufallsnetz_und_knotenpunkte():
    soll = {0.05: (1, 6), 0.15: (4, 2), 0.3: (10, 0)}
    for p, (kr, kg) in soll.items():
        c = D.zaehlung(D.zellen(DATEN, gruppe=S.LOECHER, p=p), M.GRADTERM)
        assert (c["klar_r"], c["klar_gegner"]) == (kr, kg)
    zz = D.zellen(DATEN, gruppe=S.LOECHER, p=0.15)
    assert (z(D.mittel(zz, M.WIDERSTAND)), z(D.mittel(zz, M.GRADTERM))) == ("0,80", "0,76")
    for p in S.P_DUENN:
        zz = D.zellen(DATEN, gruppe=S.ZUFALL4, p=p)
        assert abs(D.mittel(zz, M.WIDERSTAND) - D.mittel(zz, M.GRADTERM)) <= 0.03
    c = D.zaehlung(D.zellen(DATEN, gruppe=S.ZUFALL4), M.GRADTERM)
    assert (c["klar_r"], c["klar_gegner"]) == (0, 0)
    c = D.zaehlung(D.zellen(DATEN, gruppe=S.KNOTEN), M.GRADTERM)
    assert c["gegner_vorn"] == 26
    steht("der Gradterm lag in 26 von 30 Zellen vor R")


def test_dichte_netze():
    ohne = (S.ER20, S.KNOTEN10, S.PUNKT5D)
    offen = sum(D.nicht_messbar(D.zellen(DATEN, gruppe=f, p=0.15))[0] for f in ohne)
    assert offen == 17
    steht("in 17 von 18 Netzen nicht messbar")
    gt_vor = []
    for fam in ohne:
        felder = [" / ".join(z(D.dicht_ohne_engpass(DATEN, fam, p)[m]) for p in (0.7, 0.85)) for m in (M.DISTANZ, M.WIDERSTAND, M.GRADTERM, M.ISOLATION)]
        name = {S.ER20: "Zufallsnetz Grad 20", S.KNOTEN10: "Netz mit Knotenpunkten (10)", S.PUNKT5D: "Punktnetz 5D"}[fam]
        steht(f"| {name} | " + " | ".join(felder) + " |")
        for p in (0.7, 0.85):
            w = D.dicht_ohne_engpass(DATEN, fam, p)
            assert w[M.ISOLATION] >= w[M.WIDERSTAND]
            gt_vor.append(w[M.GRADTERM] - w[M.WIDERSTAND])
    assert min(gt_vor) > 0 and max(gt_vor) <= 0.0085
    steht("liegt in allen sechs Mitteln knapp vor R (höchstens 0,008)")
    werte = {p: {m: D.mittel(D.zellen(DATEN, gruppe=S.DHAELFTEN, p=p), m) for m in (M.DISTANZ, M.WIDERSTAND, M.MINCUT, M.GRADTERM)} for p in S.P_DICHT}
    assert [z(werte[p][M.WIDERSTAND]) for p in (0.7, 0.85)] == ["0,95", "0,98"]
    assert [z(werte[p][M.GRADTERM]) for p in (0.7, 0.85)] == ["0,38", "0,44"]
    assert [z(werte[0.15][m]) for m in (M.WIDERSTAND, M.DISTANZ, M.MINCUT)] == ["0,86", "0,89", "0,93"]
    for r in D.zellen(DATEN, gruppe=S.DHAELFTEN, p=0.15):
        assert 0 < r["rho1"][M.DISTANZ] - r["rho1"][M.WIDERSTAND] < 0.05
    steht("p = 0,7 / 0,85: R 0,95 / 0,98 gegen Gradterm 0,38 / 0,44. Bei p = 0,15 liegt R (0,86) **hinter** Distanz (0,89) und min cut (0,93)")
    assert D.zaehlung(DICHT, M.DISTANZ)["r_vorn"] == 49


# --- Entartung: vollständig neu gerechnet ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("familie", S.ENTARTUNG)
def test_entartung_neu_gerechnet_und_in_der_readme(familie):
    zeilen = []
    for n_ in S.E_GROESSEN:
        alt = D.entartung_zeile(DATEN, familie, n_)
        neu = T.entartung_zeile(familie, n_)
        assert neu["n"] == alt["n"] and neu["netze"] == alt["netze"]
        for k in ("rho", "rho_min", "rho_max", "abweichung", "innen", "quer", "grad"):
            if alt[k] is None:
                assert neu[k] is None
            else:
                assert neu[k] == pytest.approx(alt[k], abs=2e-3), (familie, n_, k)
        zeilen.append(alt)
    name = {S.E_PUNKT10: "Punktnetz 2D, Grad 10 fest", S.E_ER8: "Zufallsnetz, Grad 8 fest", S.E_ERWURZEL: "Zufallsnetz, Grad √n",
            S.E_PUNKTWURZEL: "Punktnetz 2D, Grad 2√n", S.E_HAELFTEN: "dichte Hälften (Grad √n), 3 Querverbindungen"}.get(familie, S.E_TEXT[familie])
    steht(f"| {name} | " + " | ".join([" / ".join(("1 000" if n_ == 1000 else str(n_)) for n_ in ((200, 512, 968) if familie in S.E_HALLEN else
                                                                                                   (200, 500, 1000))),
                                       " / ".join(z(w["rho"], 3) for w in zeilen), " / ".join(E.prozent(w["abweichung"]) for w in zeilen)]) + " |")
    if familie == S.E_HAELFTEN:
        steht("innerhalb einer Hälfte klein (" + " / ".join(E.prozent(w["innen"]) for w in zeilen) + "), quer bleibt er groß ("
              + " / ".join(E.prozent(w["quer"]) for w in zeilen) + ")")
    if familie == S.E_PUNKT10:
        steht(f"zwischen {z(min(w['rho_min'] for w in zeilen))} und {z(max(w['rho_max'] for w in zeilen))}")


def test_dichte_haelften_rangfolge_innen_und_quer():
    """Der Wertfehler entartet nur innen, die Rangfolge für sich genommen auch quer: Rangkorrelation getrennt über Quer- und Innenpaare (Median der 5 Netze)."""
    mediane = {"quer": [], "innen": [], "alle": []}
    for n_ in S.E_GROESSEN:
        je_netz = {"quer": [], "innen": [], "alle": []}
        for i in range(T.NETZE_ENTARTUNG):
            e = X.entartung(S.baue_entartung(S.E_HAELFTEN, n_, T.TAB_SEED + i), haelften=True)
            je_netz["quer"].append(ST.rangkorrelation(e.R[e.quer], e.gt[e.quer]))
            je_netz["innen"].append(ST.rangkorrelation(e.R[~e.quer], e.gt[~e.quer]))
            je_netz["alle"].append(e.rho)
        for k, v in je_netz.items():
            mediane[k].append(float(np.median(v)))
    assert mediane["quer"] == pytest.approx([0.915, 0.963, 0.978], abs=2e-3)
    assert mediane["innen"] == pytest.approx([0.998, 1.000, 1.000], abs=1e-3)
    assert mediane["alle"] == pytest.approx([0.454, 0.479, 0.488], abs=2e-3)
    assert mediane["quer"][0] < E.ENTARTET_AB <= min(mediane["quer"][1:])
    steht("nur über die Querpaare 0,915 / 0,963 / 0,978 (bei 500 und 1 000 Knoten über der Schwelle 0,95 dieser Seite, bei 200 darunter)",
          "nur über die Paare innerhalb 0,998 / 1,000 / 1,000", "zusammen ist sie trotzdem nur 0,454 / 0,479 / 0,488")


def test_entartung_hallen_mit_a_tueren():
    werte = {e["a"]: e["rho"] for e in DATEN["entartung"]["hallen_a"]}
    neu = {e["a"]: e["rho"] for e in T.entartung_hallen_a()}
    for a in (6, 8, 10):
        assert neu[a] == pytest.approx(werte[a], abs=2e-3)
    steht(f"{z(werte[6])} (a = 6), {z(werte[8])} (a = 8) und {z(werte[10])} (a = 10)")


# --- Ausbau: vollständig neu gerechnet ---------------------------------------------------------------------------------------------------------

def test_ausbau_neu_gerechnet():
    for netz in S.X_NETZE:
        for alt in D.ausbau_zeilen(DATEN, netz):
            neu = T.ausbau_zeile(netz, alt["seed"])
            assert neu["n"] == alt["n"]
            for regel, wert in alt["anteil"].items():
                if wert is None:
                    assert neu["anteil"][regel] is None
                else:
                    assert neu["anteil"][regel] == pytest.approx(wert, abs=2e-3), (netz, alt["seed"], regel)
    assert DATEN["ausbau"]["pruefung_max_relativ"] < 1e-12


def test_ausbau_dicht_stichprobe():
    for alt in DATEN["ausbau"]["dicht"][::10]:
        neu = T.ausbau_dicht_zeile(alt["familie"], alt["seed"] - T.TAB_SEED)
        assert neu["rho"] == pytest.approx(alt["rho"], abs=2e-3)
        assert neu["beste_senkung_anteil"] == pytest.approx(alt["beste_senkung_anteil"], rel=1e-5)
        for regel in (X.MAX_R, X.MAX_GRADTERM):
            assert neu["anteil"][regel] == pytest.approx(alt["anteil"][regel], abs=2e-3)


REIHE = (X.ZUFAELLIG, X.MAX_R, X.MAX_GRADTERM, X.MAX_DISTANZ, X.DIST_GRAD, X.FIEDLER, X.MAX_ZAEHLER)
AUSBAU_NAMEN = {"xstrasse": "straßenähnlich", "xloecher": "Gitter mit Löchern", "xpunkt2d": "Punktnetz 2D, Grad 6", "xzufall4": "Zufallsnetz Grad 4",
                "xknoten": "Netz mit Knotenpunkten", "xhaelften": "zwei Hälften, 2 Querverbindungen"}


def test_ausbautabellen_in_der_readme():
    for netz in S.X_NETZE:
        zz = D.ausbau_zeilen(DATEN, netz)
        werte = [D.ausbau_median(zz, r) for r in REIHE]
        steht(f"| {AUSBAU_NAMEN.get(netz, S.X_TEXT[netz])} | {len(zz)} | " + " | ".join("–" if v is None else z(v) for v in werte) + " |")
    for netz in S.X_ZUFALL:
        name = "zwei Hälften" if netz == "xhaelften" else AUSBAU_NAMEN[netz]
        felder = ["{} / {} / {}".format(*D.ausbau_vergleich(D.ausbau_zeilen(DATEN, netz), g))
                  for g in (X.MAX_GRADTERM, X.MAX_DISTANZ, X.DIST_GRAD, X.FIEDLER)]
        steht(f"| {name} | " + " | ".join(felder) + " |")


def test_ausbau_gesamt_und_dicht():
    alle = [r for r in DATEN["ausbau"]["zeilen"] if r["netz"] in S.X_ZUFALL]
    assert len(alle) == 240 and D.ausbau_vergleich(alle, X.MAX_GRADTERM) == (212, 28, 0)
    steht("in den 240 Netzen der sechs Zufallsfamilien ist „größtes R“ in 212 besser, in 28 gleich und in keinem schlechter")
    med = {r: z(D.ausbau_median(alle, r)) for r in REIHE}
    steht(f"Fiedler {med[X.FIEDLER]}, größter Zähler {med[X.MAX_ZAEHLER]}, größtes R {med[X.MAX_R]}, Distanz {med[X.MAX_DISTANZ]}, Distanz dann Gradterm "
          f"{med[X.DIST_GRAD]}, Gradterm {med[X.MAX_GRADTERM]}, zufällig {med[X.ZUFAELLIG]}")
    d = D.dicht_ausbau(DATEN)
    assert [z(f(v["rho"] for v in d.values()), 3) for f in (min, max)] == ["0,997", "0,999"]
    assert [E.prozent(f(v["gradterm"] for v in d.values()), 0) for f in (min, max)] == ["96 %", "100 %"]
    assert [E.prozent(f(v["senkung"] for v in d.values()), 2) for f in (min, max)] == ["0,19 %", "1,38 %"]
    assert [f(v["besser"] for v in d.values()) for f in (min, max)] == [6, 19] and all(v["schlechter"] == 0 for v in d.values())
    assert all(v["netze"] == 20 for v in d.values())
    steht("Median 0,997 bis 0,999, der Gradterm erreicht im Median 96 bis 100 %", "nur um 0,19 bis 1,38 % (Median)", "in 6 bis 19 von 20 besser")


# --- Reparaturversuche -----------------------------------------------------------------------------------------------------------------------

def test_reparatur_ein_netz_neu_gerechnet():
    fall = "gruppen20"
    gesp = DATEN["reparatur"]["faelle"][fall]
    neu = T.rep_netzwerte(fall, T.REP_BEWERT_SEEDS[0], {"voreinstellung": 0.15, "abgestimmt": gesp["sprung_abgestimmt"]})
    for mass, wert in neu["guete"].items():
        lo, hi = gesp["spanne"][mass]
        assert lo - 5e-3 <= wert <= hi + 5e-3, mass


def test_reparatur_abstimmung_auf_eigenen_seeds_und_rand():
    assert not set(T.REP_ABSTIMM_SEEDS) & set(T.REP_BEWERT_SEEDS)
    faelle = DATEN["reparatur"]["faelle"]
    for name, f in faelle.items():
        assert f["netze"] == 3
        gitter = dict(zip(T.REP_SPRUNGGITTER, f["sprung_gitter"]))
        assert gitter[f["sprung_abgestimmt"]] == max(gitter.values())
        assert max(v for s, v in gitter.items() if s <= 0.01) - min(v for s, v in gitter.items() if s <= 0.01) <= 0.004
    assert sum(f["sprung_am_rand"] for f in faelle.values()) == 4
    steht("Bei vier der fünf Fälle", "um höchstens 0,004")


def test_reparaturtabelle_und_saetze_in_der_readme():
    namen = {"torus3d": ("Punktnetz-Torus 3D, Grad 63", "P@10"), "torus5d": ("Punktnetz-Torus 5D, Grad 28", "P@10"),
             "torus2d": ("Punktnetz-Torus 2D, Grad 63", "P@10"), "gruppen20": ("5 Gruppen, Grad 20", "AUC"), "gruppen80": ("5 Gruppen, Grad 80", "AUC")}
    reihe = (M.DISTANZ, M.WIDERSTAND, M.VERSTAERKT, M.MINUS_LPLUS, M.KOSINUS, "ppr_voreinstellung", "ppr_abgestimmt", M.ADAMIC, M.DIST_WEGE)
    faelle = DATEN["reparatur"]["faelle"]
    for name, (text, mass) in namen.items():
        f = faelle[name]
        steht(f"| {text} | {mass} | " + " | ".join(z(f["mittel"][m]) for m in reihe) + f" | {z(f['sprung_abgestimmt'], 3)} |")
    torus = [faelle[k]["mittel"] for k in ("torus3d", "torus5d", "torus2d")]
    vorsprung = [m[M.DIST_WEGE] - m[M.VERSTAERKT] for m in torus]
    assert (z(min(vorsprung)), z(max(vorsprung))) == ("0,01", "0,03")
    assert [z(f(m[M.VERSTAERKT] for m in torus)) for f in (min, max)] == ["0,67", "0,87"]
    assert [z(f(m[M.WIDERSTAND] for m in torus)) for f in (min, max)] == ["0,03", "0,10"]
    assert faelle["torus5d"]["mittel"][M.KOSINUS] > faelle["torus5d"]["mittel"][M.VERSTAERKT]
    g20, g80 = faelle["gruppen20"]["mittel"], faelle["gruppen80"]["mittel"]
    assert g20[M.VERSTAERKT] < g20[M.DISTANZ] < min(g20[M.MINUS_LPLUS], g20[M.KOSINUS], g20["ppr_voreinstellung"])
    assert g80[M.VERSTAERKT] == max(g80.values())


def test_reparaturmasse_beim_ausfall():
    v = D.zaehlung(DUENN, M.VERSTAERKT)
    assert (v["r_vorn"], v["klar_r"], v["messbar"]) == (225, 161, 225)
    d = D.zaehlung(DICHT, M.VERSTAERKT)
    assert (d["r_vorn"], d["gegner_vorn"], d["messbar"]) == (49, 0, 55)
    uebrige = [r for r in DICHT if r["messbar"] and not r["rho1"][M.WIDERSTAND] > r["rho1"][M.VERSTAERKT]]
    assert len(uebrige) == 6 and all(r["gruppe"] == S.DHAELFTEN and r["p"] == 0.15 and r["rho1"][M.WIDERSTAND] == r["rho1"][M.VERSTAERKT] for r in uebrige)
    for m in (M.KOSINUS, M.PPR, M.ADAMIC, M.DIST_WEGE):
        assert D.zaehlung(DUENN, m)["r_vorn"] == 225, m
    assert D.zaehlung(DUENN, M.MINUS_LPLUS)["r_vorn"] == 224
    steht("in allen 225 dünnen Zellen lag R vor der verstärkten Distanz (klar in 161), in den dichten in 49 von 55 messbaren Zellen",
          "−L⁺ in 224")


# --- Presets und App-Texte --------------------------------------------------------------------------------------------------------------------

def test_preset_aussagen_der_hilfen():
    def zelle(name):
        pr = C.PRESETS[name]
        fam = pr["netz"]
        g = S.baue(fam, pr["n"], pr["a"], pr["tueren"], pr["verbund"], pr["seed"])
        p = pr["pd"] if S.ist_dicht(fam) else pr["p"]
        ps = S.P_DICHT if S.ist_dicht(fam) else S.P_DUENN
        nm = X.netzmasse(g, pr["seed"], S.FAMNR[fam])
        return X.zeile(X.ausfallzelle(g, nm, p, ps.index(p), pr["seed"], S.FAMNR[fam]))

    u = lambda zl, m: E.urteil(zl, m)
    zl = zelle("Zwei Hallen, eine Tür")
    assert u(zl, M.DISTANZ) == u(zl, M.GRADTERM) == ST.R_VORN
    zl = zelle("Vier verteilte Türen: Grade vorn")
    assert u(zl, M.GRADTERM) == ST.GEGNER_VORN
    zl = zelle("Straßenähnlich")
    assert u(zl, M.DISTANZ) == ST.R_VORN and u(zl, M.MINCUT) == u(zl, M.STICH200) == ST.GEGNER_VORN
    zl = zelle("Netz mit Knotenpunkten")
    assert u(zl, M.DISTANZ) == u(zl, M.MINCUT) == ST.R_VORN and u(zl, M.GRADTERM) != ST.R_VORN
    zl = zelle("Dichtes Netz")
    assert u(zl, M.GRADTERM) == ST.UNKLAR


def test_default_ansicht_ist_die_tabellenzelle():
    """Die Voreinstellung der Seite ist dieselbe Instanz wie die vorgerechnete Zelle (zwei Hallen, a = 8, eine Tür, Zufalls-Seed 7000, p = 0,15)."""
    pr = C.PRESETS["Zwei Hallen, eine Tür"]
    g = S.baue(pr["netz"], pr["n"], pr["a"], pr["tueren"], pr["verbund"], pr["seed"])
    nm = X.netzmasse(g, pr["seed"], S.FAMNR[pr["netz"]])
    live = X.zeile(X.ausfallzelle(g, nm, 0.15, 1, pr["seed"], S.FAMNR[pr["netz"]]))
    gesp = next(r for r in D.zellen(DATEN, gruppe="hallen1", p=0.15) if r["a"] == 8)
    for m in (M.WIDERSTAND, M.DISTANZ, M.GRADTERM, M.MINCUT):
        assert live["rho1"][m] == pytest.approx(gesp["rho1"][m], abs=3e-3)


def test_kein_planbegriff_und_keine_stueck_nummer_in_app_und_readme():
    for text in (README, APP, "".join(C.PRESET_HELP.values())):
        for verboten in (r"Phase 0", r"Pilot", r"Prüfer", r"Korrekturrunde", r"Stück \d", r"\bträgt\b", r"\btragen\b", r"läuft lokal", r"Saatwert", r"\bW2\b"):
            assert not re.search(verboten, text), verboten


def test_readme_nennt_die_genannten_netze_und_zufalls_seeds():
    steht("zwei **unabhängige** Stichproben mit je 1 600 Ausfallmustern", "über 300 zufällige Knotenpaare", "mit je 10 Netzen",
          "mit je 6 Netzen")
    assert (X.PROBEN, X.PAARE, T.NETZE_KONTRAST, T.NETZE_DICHT, T.NETZE_AUSBAU, T.NETZE_AUSBAU_DICHT) == (1600, 300, 10, 6, 40, 20)


def test_widerstand_der_handnetz_paare_ueber_die_demo(hand):
    R = W.widerstand(hand)
    assert (R[0, 1], R[0, 4]) == pytest.approx((2 / 3, 7 / 3))
