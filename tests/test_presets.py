"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Einrasten der Permalink-Werte."""

import wdn_constants as C
import wdn_experimente as X
import wdn_presets as P
import wdn_szenario as S


def test_jedes_preset_hat_hilfe_und_alle_schluessel():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS) == set(P.SETTING_SPECS), name
        assert C.PRESET_HELP[name]


def test_preset_werte_sind_gueltig():
    for name, preset in C.PRESETS.items():
        for key, spec in P.SETTING_SPECS.items():
            assert P.eingerastet(spec, preset[key]) == preset[key], (name, key)


def test_standard_ist_das_erste_preset():
    erstes = C.PRESETS[next(iter(C.PRESETS))]
    for key, spec in P.SETTING_SPECS.items():
        assert spec.default == erstes[key]


def test_die_plan_presets_sind_dabei():
    assert list(C.PRESETS) == ["Zwei Hallen, eine Tür", "Vier verteilte Türen: Grade vorn", "Straßenähnlich", "Netz mit Knotenpunkten", "Dichtes Netz",
                               "Besen"]
    assert C.PRESETS["Dichtes Netz"]["netz"] in S.DICHT and C.PRESETS["Besen"]["x_netz"] == S.X_BESEN


def test_einrasten_und_unbekannte_auswahl():
    spec = P.SETTING_SPECS["n"]
    assert P.eingerastet(spec, 156) == 160 and P.eingerastet(spec, 3) == C.N_MIN and P.eingerastet(spec, 999) == C.N_MAX
    assert P.eingerastet(P.SETTING_SPECS["netz"], "mond") is None and P.eingerastet(P.SETTING_SPECS["p"], 0.2) is None
    assert P.eingerastet(P.SETTING_SPECS["a"], 3) == C.A_MIN
    assert X.MAX_R in P.SETTING_SPECS["x_regel"].options
