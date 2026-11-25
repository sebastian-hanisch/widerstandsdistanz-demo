"""Verdikte an von Hand gesetzten Werten: jede Schwelle der Art und jede Zahl im Text."""

import pytest

import wdn_evaluation as E
import wdn_experimente as X
import wdn_masse as M


def _zeile(r=(0.8, 0.8), dist=(0.5, 0.5), grad=(0.5, 0.5), mc=(0.8, 0.8), st=(0.8, 0.8), verst=0.6, messbar=True):
    werte = {M.WIDERSTAND: r, M.DISTANZ: dist, M.GRADTERM: grad, M.MINCUT: mc, M.STICH200: st, M.VERSTAERKT: (verst, verst)}
    return {"messbar": messbar, "rho1": {k: v[0] for k, v in werte.items()}, "rho2": {k: v[1] for k, v in werte.items()}}


def test_zahl_mit_komma_und_minus():
    assert E.zahl(0.8765) == "0,88" and E.zahl(-0.031, 2) == "−0,03" and E.zahl(-0.0001) == "0,00" and E.zahl(None) == "nicht bestimmbar"
    assert E.zahl(498501, 0) == "498 501" and E.prozent(0.1234) == "12,3 %" and E.prozent(None) == "nicht bestimmbar"


def test_ausfall_vor_distanz_und_gradterm():
    art, text = E.verdict_ausfall(_zeile())
    assert art == "success" and "R ist klar vor der Distanz und vor dem Gradterm" in text
    assert "gegen den min cut 0,80 (zweite Stichprobe 0,80): kein klarer Unterschied" in text


def test_ausfall_vor_distanz_gradterm_klar_vorn():
    art, text = E.verdict_ausfall(_zeile(grad=(0.9, 0.9)))
    assert art == "info" and "nicht vor den Graden:** der Gradterm ist klar vor R" in text
    assert "gegen den Gradterm 0,90 (zweite Stichprobe 0,90): der Gradterm klar vorn" in text


def test_ausfall_vor_distanz_kein_klarer_unterschied_zu_den_graden():
    art, text = E.verdict_ausfall(_zeile(grad=(0.76, 0.76)))
    assert art == "info" and "zum Gradterm gibt es keinen klaren Unterschied" in text


@pytest.mark.parametrize("grad", [(0.78, 0.78), (0.80, 0.80), (0.83, 0.83), (0.90, 0.78), (0.70, 0.82)],
                         ids=["R knapp vorn", "gleichauf", "Gradterm knapp vorn", "nur Stichprobe 1 klar", "Vorzeichen wechselt"])
def test_ausfall_ohne_klaren_unterschied_behauptet_nicht_hinter_den_graden(grad):
    """Der Zweig „kein klarer Unterschied zum Gradterm“ steht auch, wenn R vorn liegt: Er darf nur „nicht klar vor“ sagen, nie „nicht vor den Graden“."""
    art, text = E.verdict_ausfall(_zeile(grad=grad))
    assert art == "info" and "R ist klar vor der Distanz, nicht klar vor den Graden:** zum Gradterm gibt es keinen klaren Unterschied." in text
    assert "nicht vor den Graden" not in text


def test_ausfall_klar_hinter_der_distanz():
    art, text = E.verdict_ausfall(_zeile(dist=(0.9, 0.9)))
    assert art == "warning" and "R liegt klar hinter der kürzesten Distanz" in text


def test_ausfall_knapp_hinter_der_distanz_sagt_nicht_vor():
    art, text = E.verdict_ausfall(_zeile(r=(0.86, 0.86), dist=(0.89, 0.89)))
    assert art == "info" and "Kein klarer Unterschied zwischen R und der Distanz" in text and "R liegt in beiden Stichproben dahinter" in text
    assert "klar vor der Distanz" not in text


def test_ausfall_knapp_hinter_der_distanz_nur_in_einer_stichprobe_unter_005():
    """In einer Stichprobe 0,06 dahinter, in der anderen 0,02: nicht klar. „Um weniger als 0,05“ wäre für die erste Stichprobe falsch."""
    art, text = E.verdict_ausfall(_zeile(r=(0.80, 0.84), dist=(0.86, 0.86)))
    assert art == "info" and "R liegt in beiden Stichproben dahinter, aber nicht in beiden um mindestens 0,05." in text
    assert "um weniger als 0,05" not in text


def test_ausfall_schwelle_005_zaehlt_und_beide_stichproben_zaehlen():
    assert E.verdict_ausfall(_zeile(r=(0.55, 0.55)))[0] == "success"
    assert "Kein klarer Unterschied" in E.verdict_ausfall(_zeile(r=(0.80, 0.54)))[1]


def test_ausfall_nicht_messbar():
    art, text = E.verdict_ausfall(_zeile(messbar=False))
    assert art == "warning" and "Nicht messbar" in text and "95 %" in text


@pytest.mark.parametrize("rho,art,teil", [(0.95, "warning", "fast wie"), (0.9499, "info", "ähnlich"), (0.70, "info", "ähnlich"),
                                          (0.6999, "success", "anders als")])
def test_entartung_schwellen(rho, art, teil):
    a, text = E.verdict_entartung(500, 22.4, rho, 0.0448)
    assert a == art and teil in text and "500 Knoten, mittlerer Grad 22,4" in text and "um 4,5 %" in text


def test_entartung_ohne_wert():
    a, text = E.verdict_entartung(5, 4.0, None, 0.1)
    assert a == "warning" and "nicht bestimmbar" in text


def _anteile(r=0.86, dist=0.87, grad=0.45, fiedler=0.5, zaehler=0.86, dg=0.86):
    return {X.ZUFAELLIG: 0.4, X.MAX_R: r, X.MAX_DISTANZ: dist, X.MAX_GRADTERM: grad, X.DIST_GRAD: dg, X.FIEDLER: fiedler, X.MAX_ZAEHLER: zaehler}


def test_ausbau_zahlen_und_andere_regel_besser():
    art, text = E.verdict_ausbau(_anteile(), X.MAX_R, "größtes R")
    assert art == "info" and "„größtes R“ 86,0 % der besten Senkung, die Distanzregel 87,0 %, der Gradterm 45,0 %" in text
    assert "1 andere Regel ist hier besser" in text


def test_ausbau_beste_kante_und_gewaehlte_regel():
    art, text = E.verdict_ausbau(_anteile(r=1.0, dist=0.9), X.FIEDLER, "Fiedler")
    assert art == "success" and "trifft hier eine beste Kante" in text and "„Fiedler“ erreicht 50,0 %" in text


def test_ausbau_keine_andere_besser_und_fiedler_fehlt():
    art, text = E.verdict_ausbau(_anteile(dist=0.8, zaehler=0.86, dg=0.86, fiedler=None), X.MAX_DISTANZ, "Distanz")
    assert art == "success" and "Keine der anderen Regeln" in text and "gewählte Regel" not in text


def _fall(verst, dist=0.6, aa=0.65, dw=0.77):
    return {"guete": "auc", "mittel": {M.VERSTAERKT: verst, M.DISTANZ: dist, M.ADAMIC: aa, M.DIST_WEGE: dw, M.WIDERSTAND: 0.52}}


def test_reparatur_ueber_und_unter_der_distanz():
    art, text = E.verdict_reparatur(_fall(0.98))
    assert art == "success" and "AUC 0,98 (Distanz: 0,60, beste Zählregel „Distanz, dann Wegezahl“: 0,77)" in text and "über der Zählregel" in text
    art, text = E.verdict_reparatur(_fall(0.55))
    assert art == "warning" and "sie liegt unter der Distanz und unter der Zählregel" in text
    art, text = E.verdict_reparatur(_fall(0.6))
    assert art == "info" and "gleichauf mit der Distanz" in text


def test_reparatur_ausfall():
    art, text = E.verdict_reparatur_ausfall(_zeile(r=(0.93, 0.92), verst=0.91), "Netz X")
    assert art == "info" and "(Netz X)" in text and "0,91 gegen R mit 0,93" in text
    assert "nicht messbar" in E.verdict_reparatur_ausfall(_zeile(messbar=False), "Netz X")[1]


def test_leitung():
    art, text = E.verdict_leitung(0.15, 0.15, 0.1092)
    assert "15,00 %" in text and "10,92 %" in text and "seltener getrennt" in text
    assert "häufiger getrennt" in E.verdict_leitung(0.3, 0.3, 0.4388)[1]
    assert "gleich oft" in E.verdict_leitung(0.2, 0.2, 0.2)[1]


def test_kernfragen_nennen_zaehlung_und_urteil():
    zaehl = {"r_vorn": 7, "messbar": 9, "klar_r": 5, "klar_gegner": 2}
    art, text = E.kernfrage_distanz(_zeile(), zaehl, "zwei Hallen, 1 Tür")
    assert art == "success" and "R klar vorn (R 0,80, Distanz 0,50)" in text and "in 7 von 9 messbaren" in text
    art, text = E.kernfrage_grade(_zeile(grad=(0.9, 0.9)), zaehl, "x")
    assert art == "warning" and "Gradterm klar vorn" in text and "klar vorn war R in 5, der Gradterm in 2" in text
    assert E.kernfrage_grade(_zeile(grad=(0.78, 0.78)), zaehl, "x")[0] == "info"
    assert E.kernfrage_distanz(_zeile(messbar=False), zaehl, "x")[0] == "warning"
