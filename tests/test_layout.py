"""Layout (DEMO-PLAYBOOK §2): fester Kopf, Schnellstart oben in der Seitenleiste, aktives Preset hervorgehoben; jeder Regler der Seitenleiste steht in
SETTING_SPECS, und jede Änderung hebt die Markierung auf (auch bei Reglern, die erst nach einem Familienwechsel erscheinen)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import wdn_constants as C
import wdn_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")
REGLER_ARTEN = ("slider", "number_input", "select_slider", "selectbox", "radio", "toggle", "checkbox", "text_input")
# Regler, die erst bei einer bestimmten Netzfamilie erscheinen: erst dorthin wechseln
VORBEREITUNG = {"verbund": "verbund", "n": "strasse", "pd": "er20"}
ANDERS = {"netz": "verbund", "a": 6, "tueren": 2, "verbund": "2x2x6", "n": 90, "p": 0.3, "pd": 0.85, "seed": 7001, "e_netz": "er8", "e_n": 200,
          "x_netz": "xhallen2", "x_regel": "max_gradterm", "r_netz": "gruppen80"}


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _typen(at) -> dict:
    return {b.label: b.proto.type for b in at.sidebar.button if b.label in C.PRESETS}


def _regler(at, key):
    for art in REGLER_ARTEN:
        try:
            return getattr(at.sidebar, art)(key=key)
        except KeyError:
            continue
    raise AssertionError(f"Regler {key} steht nicht in der Seitenleiste")


def test_presets_stehen_in_der_seitenleiste_und_nicht_im_hauptbereich():
    at = _app()
    assert [b.label for b in at.sidebar.button][: len(C.PRESETS)] == list(C.PRESETS)
    assert not [b for b in at.main.button if b.label in C.PRESETS]


def test_titel_steht_im_festen_kopf():
    at = _app()
    assert "st-key-kopf" in " ".join(h.proto.body for h in at.get("html"))
    assert at.title[0].value


def test_beim_start_ist_genau_das_standard_preset_hervorgehoben():
    typen = _typen(_app())
    assert [name for name, typ in typen.items() if typ == "primary"] == [next(iter(C.PRESETS))]


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_angeklicktes_preset_ist_hervorgehoben_und_bleibt_es_im_naechsten_lauf(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert [n for n, typ in _typen(at).items() if typ == "primary"] == [name]
    at.run()
    assert [n for n, typ in _typen(at).items() if typ == "primary"] == [name]


def test_jeder_regler_der_seitenleiste_steht_in_setting_specs():
    for familie in ("hallen", "verbund", "er20"):
        at = _app()
        at.sidebar.selectbox(key="netz").set_value(familie).run()
        schluessel = {w.key for art in REGLER_ARTEN for w in getattr(at.sidebar, art) if w.key}
        assert not (schluessel - set(P.SETTING_SPECS)), schluessel - set(P.SETTING_SPECS)


@pytest.mark.parametrize("state_key", list(P.SETTING_SPECS))
def test_jede_aenderung_eines_reglers_hebt_die_hervorhebung_auf(state_key):
    at = _app()
    if state_key in VORBEREITUNG:
        at.sidebar.selectbox(key="netz").set_value(VORBEREITUNG[state_key]).run()
    _regler(at, state_key).set_value(ANDERS[state_key]).run()
    assert not at.exception
    assert "primary" not in _typen(at).values()
    name = next(iter(C.PRESETS))
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert _typen(at)[name] == "primary"
