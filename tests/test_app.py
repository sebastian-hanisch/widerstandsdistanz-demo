"""End-to-end mit AppTest: Standard, jeder Button, jedes Preset mit seinen Verdikt-Zeilen, jede Option der Auswahlregler, Regler an den Rändern, alle vier
Experimente und Permalink. Plotly-Auswahlen gibt es in dieser Demo nicht; die Bedienung ist ohne Klick vollständig."""

import os
import re

import pytest
from streamlit.testing.v1 import AppTest

import wdn_constants as C
import wdn_presets as P
import wdn_szenario as S
import wdn_tabellen as T

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "180"))


def _fresh(**query) -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    for k, v in query.items():
        at.query_params[k] = str(v)
    at.run(timeout=TIMEOUT)
    _ok(at)
    return at


def _ok(at):
    assert not at.exception, [str(e) for e in at.exception]
    assert not at.error, [e.value for e in at.error]


def _preset(name) -> AppTest:
    at = _fresh()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    _ok(at)
    return at


def _texte(at, *arten) -> str:
    arten = arten or ("success", "info", "warning", "markdown", "caption")
    return " ".join(str(e.value) for kind in arten for e in getattr(at, kind))


def _experimente(at):
    return [s.value for s in at.subheader if s.value.startswith("🔬")]


def test_standard_zeigt_vier_experimente_und_vier_kernfragen():
    at = _fresh()
    assert len(_experimente(at)) == 4
    text = _texte(at)
    for frage in ("1. Sagt R mehr über das Zerreißen als die kürzeste Distanz?", "2. Und mehr als die zwei Grade an den Enden?",
                  "3. Ab wann ordnet R nur noch die Grade?", "4. Wählt R die bessere neue Leitung?"):
        assert frage in text
    # Aufhänger am Handnetz und Beispiel „Leitung gegen drei Wege“
    assert "| (0,1) | 2, 2 | 1 | 0,042 | 4,2 % | 2/3 |" in text and "| (0,4) | 2, 2 | 1 | 0,044 | 21,9 % | 7/3 |" in text
    assert "15,00 %" in text and "10,92 %" in text and "seltener getrennt" in text


def test_jeder_button_ohne_fehler():
    labels = [b.label for b in _fresh().button]
    for index in range(len(labels)):
        at = _fresh()
        at.button[index].click().run(timeout=TIMEOUT)
        _ok(at)


ERWARTET = {
    "Zwei Hallen, eine Tür": [
        "R erreicht die Rangkorrelation 0,93 (zweite Stichprobe 0,92). **R ist klar vor der Distanz und vor dem Gradterm.**",
        "„größtes R“ 86,1 % der besten Senkung, die Distanzregel 86,1 %, der Gradterm 45,2 %",
        "Auf diesem Netz erreicht die verstärkte Widerstandsdistanz P@10 0,82 (Distanz: 0,16",        # gespeichert: 0,824889
        "in 9 von 9 messbaren Netz-p-Zellen vor der Distanz"],
    "Vier verteilte Türen: Grade vorn": [
        "**R ist klar vor der Distanz, nicht vor den Graden:** der Gradterm ist klar vor R.", "gegen den Gradterm 0,92 (zweite Stichprobe 0,91)",
        "in 2 von 9 messbaren Netz-p-Zellen vor dem Gradterm", "die Distanzregel 85,8 %, der Gradterm 41,1 %"],
    "Straßenähnlich": [
        "**R ist klar vor der Distanz, nicht klar vor den Graden:** zum Gradterm gibt es keinen klaren Unterschied.", "der min cut klar vorn",
        "die 200er-Stichprobe klar vorn", "in 26 von 30 messbaren Netz-p-Zellen vor dem Gradterm"],
    "Netz mit Knotenpunkten": [
        "R erreicht die Rangkorrelation 0,87", "gegen den min cut 0,76 (zweite Stichprobe 0,76): R klar vorn", "in 4 von 30 messbaren Netz-p-Zellen vor dem Gradterm"],
    "Dichtes Netz": [
        "R erreicht die Rangkorrelation 0,86", "zum Gradterm gibt es keinen klaren Unterschied", "**R ordnet die Nichtnachbarn hier fast wie die zwei Endgrade**",
        "Auf diesem Netz erreicht die verstärkte Widerstandsdistanz AUC 0,62 (Distanz: 0,66", "sie liegt unter der Distanz"],
    "Besen": ["„größtes R“ 100,0 % der besten Senkung, die Distanzregel 100,0 %, der Gradterm 83,8 %", "trifft hier eine beste Kante"],
}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_preset_mit_seinen_verdikten(name):
    at = _preset(name)
    assert len(_experimente(at)) == 4
    verdikte = _texte(at, "success", "info", "warning")
    for teil in ERWARTET[name]:
        assert teil in verdikte, (name, teil, verdikte[:3000])


@pytest.mark.parametrize("familie", S.FAMILIEN)
def test_jede_netzfamilie_in_experiment_1(familie):
    at = _fresh()
    at.sidebar.selectbox(key="netz").set_value(familie).run(timeout=TIMEOUT)
    _ok(at)


def test_dichte_haelften_bei_015_sagen_nicht_vor_der_distanz():
    at = _fresh()
    at.sidebar.selectbox(key="netz").set_value(S.DHAELFTEN).run()
    at.sidebar.radio(key="pd").set_value(0.15).run()
    _ok(at)
    verdikte = _texte(at, "success", "info", "warning")
    assert "klar vor der Distanz" not in verdikte and "Kein klarer Unterschied zwischen R und der Distanz" in verdikte


def test_nicht_messbar_auf_dichtem_netz_bei_015():
    at = _fresh()
    at.sidebar.selectbox(key="netz").set_value(S.ER20).run()
    at.sidebar.radio(key="pd").set_value(0.15).run()
    _ok(at)
    assert "**Nicht messbar:**" in _texte(at, "warning")


@pytest.mark.parametrize("familie", S.ENTARTUNG)
def test_jede_familie_in_experiment_2(familie):
    at = _fresh()
    at.sidebar.selectbox(key="e_netz").set_value(familie).run(timeout=TIMEOUT)
    _ok(at)
    assert "ist die Rangkorrelation von R mit dem Gradterm" in _texte(at, "success", "info", "warning")


def test_entartungstabelle_median_und_spanne_mit_gleich_vielen_stellen():
    """Vorgerechnete Tabelle in Experiment 2: Median und Spanne mit derselben Stellenzahl, sonst liegt der angezeigte Median scheinbar außerhalb der Spanne
    (Zufallsnetz Grad 8: „0,997 (1,00 bis 1,00)“)."""
    at = _fresh()
    tabellen = [str(m.value) for m in at.markdown if "Rangkorrelation (Median, Spanne)" in str(m.value)]
    assert len(tabellen) == 1
    zellen = re.findall(r"\| (\d,\d+) \((\d,\d+) bis (\d,\d+)\) \|", tabellen[0])
    assert len(zellen) == 15                                             # fünf Zufallsfamilien × drei Größen
    for mitte, von, bis in zellen:
        assert len(mitte) == len(von) == len(bis), (mitte, von, bis)
        assert float(von.replace(",", ".")) <= float(mitte.replace(",", ".")) <= float(bis.replace(",", ".")), (mitte, von, bis)


@pytest.mark.parametrize("n", S.E_GROESSEN)
def test_groessen_in_experiment_2(n):
    at = _fresh()
    at.sidebar.selectbox(key="e_netz").set_value(S.E_PUNKTWURZEL).run()
    at.sidebar.radio(key="e_n").set_value(n).run(timeout=TIMEOUT)
    _ok(at)


@pytest.mark.parametrize("netz", S.X_NETZE)
def test_jedes_netz_in_experiment_3(netz):
    at = _fresh()
    at.sidebar.selectbox(key="x_netz").set_value(netz).run(timeout=TIMEOUT)
    _ok(at)
    assert "Hier erreicht „größtes R“" in _texte(at, "success", "info")


def test_jede_regel_in_experiment_3():
    for regel in ("zufaellig", "max_r", "max_gradterm", "max_distanz", "distanz_grad", "fiedler", "max_zaehler"):
        at = _fresh()
        at.sidebar.selectbox(key="x_regel").set_value(regel).run()
        _ok(at)


def test_fiedler_wird_bei_doppeltem_eigenwert_ausgeblendet():
    at = _fresh()
    at.sidebar.selectbox(key="x_regel").set_value("fiedler").run()
    at.sidebar.selectbox(key="x_netz").set_value(S.X_VERBUND).run()
    _ok(at)
    assert at.session_state["x_regel"] == "max_r"
    assert not any("Fiedler" in o for o in at.sidebar.selectbox(key="x_regel").options)
    assert "nicht bestimmbar (zweiter Eigenwert doppelt)" in _texte(at, "markdown")


@pytest.mark.parametrize("fall", T.REP_FAELLE)
def test_jeder_fall_in_experiment_4(fall):
    at = _fresh()
    at.sidebar.selectbox(key="r_netz").set_value(fall).run(timeout=TIMEOUT)
    _ok(at)
    assert "Auf diesem Netz erreicht die verstärkte Widerstandsdistanz" in _texte(at, "success", "info", "warning")


@pytest.mark.parametrize("mass", C.STREU_MASSE)
def test_jeder_vorhersager_im_streubild(mass):
    at = _fresh()
    at.radio(key="streu_mass").set_value(mass).run()
    _ok(at)


@pytest.mark.parametrize("wert,teil", [(C.P_LEITUNG_MIN, "seltener getrennt"), (C.P_LEITUNG_MAX, "häufiger getrennt"), (0.3, "häufiger getrennt")])
def test_leitung_regler(wert, teil):
    at = _fresh()
    at.slider(key="p_leitung").set_value(wert).run()
    _ok(at)
    assert teil in _texte(at, "info")


def test_regler_an_den_grenzen():
    for netz, key in (("hallen", "a"), ("strasse", "n"), ("dhaelften", "n")):
        for rand in ("min", "max"):
            at = _fresh()
            at.sidebar.selectbox(key="netz").set_value(netz).run()
            regler = at.sidebar.slider(key=key)
            regler.set_value(int(getattr(regler, rand))).run(timeout=TIMEOUT)
            _ok(at)
    for seed in (0, C.SEED_MAX):
        at = _fresh()
        at.sidebar.number_input(key="seed").set_value(seed).run(timeout=TIMEOUT)
        _ok(at)


def test_worst_case_alle_maxima():
    _ok(_fresh(netz="dhaelften", n=C.N_MAX, pd=0.85, seed=C.SEED_MAX, enetz="punktwurzel", en=1000, xnetz="xverbund", rnetz="torus2d"))
    _ok(_fresh(netz="hallen", a=C.A_MAX, tueren=0, p=0.05, enetz="ehaelften", en=1000))


def test_permalink_laedt_und_begrenzt():
    at = _fresh(netz="strasse", n=94, p=0.3, seed=-5, enetz="er8", en=1000, xnetz="besen", regel="max_gradterm")
    assert (at.session_state["netz"], at.session_state["seed"], at.session_state["e_n"], at.session_state["x_netz"]) == ("strasse", 0, 1000, "besen")
    assert at.sidebar.slider(key="n").value == 90 and at.sidebar.radio(key="p").value == 0.3
    at = _fresh(netz="mond", p=0.4, tueren=3, a=99)
    assert at.session_state["netz"] == "hallen" and at.sidebar.slider(key="a").value == C.A_MAX and at.sidebar.radio(key="p").value == 0.15


def test_adresszeile_spiegelt_die_regler():
    at = _fresh()
    at.sidebar.number_input(key="seed").set_value(42).run()
    assert str(at.query_params["seed"]).strip("[]'") == "42"
    for key in P.SETTING_SPECS:
        assert P.SETTING_SPECS[key].url_param in at.query_params


def test_ausgeblendeter_regler_behaelt_seinen_wert():
    at = _fresh()
    at.sidebar.slider(key="a").set_value(10).run()
    at.sidebar.selectbox(key="netz").set_value("strasse").run()
    at.sidebar.selectbox(key="netz").set_value("hallen").run()
    _ok(at)
    assert at.sidebar.slider(key="a").value == 10
