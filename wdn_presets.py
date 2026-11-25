"""Permalink (Begrenzen, Einrasten), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).

Jeder Regler der Seitenleiste hat einen Eintrag in SETTING_SPECS. Regler, die nur bei bestimmten Netzfamilien gezeichnet werden, stehen in KEPT: Streamlit
löscht ihren Zustand, sobald sie nicht gezeichnet werden, darum bleibt der zuletzt gewählte Wert in einem eigenen Schlüssel erhalten (`seed_widget` unmittelbar
vor dem Regler, `merke` danach)."""

import random
from dataclasses import dataclass

import streamlit as st

import wdn_constants as C
import wdn_experimente as X
import wdn_szenario as S
import wdn_tabellen as T


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: object
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None
    step: int = 1


_STANDARD = C.PRESETS[next(iter(C.PRESETS))]


def _spec(state_key, url, caster, lo=None, hi=None, options=None, step=1):
    return state_key, SettingSpec(url, caster, _STANDARD[state_key], lo, hi, options, step)


SETTING_SPECS = dict([
    _spec("netz", "netz", str, options=S.FAMILIEN),
    _spec("a", "a", int, C.A_MIN, C.A_MAX),
    _spec("tueren", "tueren", int, options=S.TUEREN),
    _spec("verbund", "verbund", str, options=tuple(S.VERBUND_VARIANTEN)),
    _spec("n", "n", int, C.N_MIN, C.N_MAX, step=C.N_STEP),
    _spec("p", "p", float, options=S.P_DUENN),
    _spec("pd", "pd", float, options=S.P_DICHT),
    _spec("seed", "seed", int, 0, C.SEED_MAX),
    _spec("e_netz", "enetz", str, options=S.ENTARTUNG),
    _spec("e_n", "en", int, options=S.E_GROESSEN),
    _spec("x_netz", "xnetz", str, options=S.X_NETZE),
    _spec("x_regel", "regel", str, options=X.REGELN),
    _spec("r_netz", "rnetz", str, options=T.REP_FAELLE),
])
PRESET_KEYS = {key: key for key in SETTING_SPECS}
KEPT = {key: f"_kept_{key}" for key in ("a", "tueren", "verbund", "n", "p", "pd")}


def wert(state_key):
    """Aktueller Wert eines Reglers, auch wenn er gerade nicht gezeichnet wird."""
    spec = SETTING_SPECS[state_key]
    if state_key in KEPT:
        return st.session_state.get(state_key, st.session_state.get(KEPT[state_key], spec.default))
    return st.session_state.get(state_key, spec.default)


def init_session_state_defaults():
    """Standardwerte für Regler, die in jedem Lauf gezeichnet werden. Ausblendbare Regler (KEPT) bekommen ihren Wert erst unmittelbar vor dem Zeichnen."""
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in KEPT and state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def seed_widget(state_key):
    if state_key not in st.session_state:
        st.session_state[state_key] = st.session_state.get(KEPT[state_key], SETTING_SPECS[state_key].default)


def merke(state_key):
    st.session_state[KEPT[state_key]] = st.session_state[state_key]


def setze(state_key, neuer_wert):
    """Wert setzen, ohne den Zustand eines ausgeblendeten Reglers zu schreiben."""
    if state_key in KEPT:
        st.session_state[KEPT[state_key]] = neuer_wert
        st.session_state.pop(state_key, None)
    else:
        st.session_state[state_key] = neuer_wert


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def eingerastet(spec: SettingSpec, w):
    """Wert auf Grenzen begrenzt und auf die Schrittweite eingerastet; unbekannte Auswahl gibt None."""
    if spec.options is not None:
        return w if w in spec.options else None
    if spec.step > 1:
        w = spec.lo + round((w - spec.lo) / spec.step) * spec.step
    if spec.lo is not None:
        w = max(spec.lo, w)
    if spec.hi is not None:
        w = min(spec.hi, w)
    return w


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                w = eingerastet(spec, spec.caster(qp[spec.url_param]))
            except (ValueError, TypeError):
                continue
            if w is not None:
                setze(state_key, w)
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        setze(state_key, C.PRESETS[name][key])


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None (zustandslos, über alle Regler aus SETTING_SPECS)."""
    for name, preset in C.PRESETS.items():
        if all(wert(state_key) == preset.get(state_key, spec.default) for state_key, spec in SETTING_SPECS.items()):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["seed"] = random.randint(0, C.SEED_MAX)
